/**
 * Module: registry
 * Purpose: Manage in-memory representation of registry.json with helper mutations.
 * Created: 2025-10-31
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/graph-memory-core.md
 */

import type {
  ConnectionRecord,
  NodeRecord,
  QueryConnectionsRequest,
  QueryNodesRequest,
  RegistrySnapshot
} from './types.js';
import type { GraphStorageGateway } from './storageGateway.js';
import {
  ConnectionNotFoundError,
  ContentReadFailedError,
  FileCreationFailedError,
  NodeNotFoundError
} from './errors.js';
import { REGISTRY_FILE_PATH } from './constants.js';

/**
 * Helper responsible for maintaining registry state and enforcing invariants.
 */
export class Registry {
  private snapshot: RegistrySnapshot;

  constructor(snapshot: RegistrySnapshot) {
    this.snapshot = snapshot;
  }

  /**
   * Load registry metadata from persistent storage.
   *
   * @param storage - Gateway used to read `_system/registry.json`.
   * @returns Promise resolving to a registry instance representing the persisted state.
   * @throws ContentReadFailedError When the registry file cannot be read or parsed.
   */
  static async load(storage: GraphStorageGateway): Promise<Registry> {
    const exists = await storage.pathExists(REGISTRY_FILE_PATH);
    if (!exists) {
      return Registry.createEmpty();
    }

    try {
      const contents = await storage.readText(REGISTRY_FILE_PATH);
      const parsed = JSON.parse(contents) as RegistrySnapshot;
      return new Registry(Registry.normalizeSnapshot(parsed));
    } catch (error) {
      throw new ContentReadFailedError(REGISTRY_FILE_PATH, error);
    }
  }

  /**
   * Create an empty registry ready for hydration.
   *
   * @returns Registry populated with empty node and connection maps.
   */
  static createEmpty(): Registry {
    return new Registry({ nodes: {}, connections: {} });
  }

  /**
   * Return deep-clone snapshot for persistence.
   *
   * @returns Snapshot suitable for writing to `_system/registry.json`.
   */
  toSnapshot(): RegistrySnapshot {
    return Registry.cloneSnapshot(this.snapshot);
  }

  /**
   * Persist the current registry snapshot to storage.
   *
   * @param storage - Gateway used to write `_system/registry.json`.
   * @throws FileCreationFailedError When the registry file cannot be written atomically.
   */
  async save(storage: GraphStorageGateway): Promise<void> {
    const payload = JSON.stringify(this.snapshot, null, 2);
    try {
      await storage.ensureDirectory(REGISTRY_FILE_PATH.split('/').slice(0, -1).join('/'));
      await storage.writeText(REGISTRY_FILE_PATH, `${payload}\n`);
    } catch (error) {
      throw new FileCreationFailedError(REGISTRY_FILE_PATH, error);
    }
  }

  /**
   * Fetch node record by ID.
   *
   * @param nodeId - Identifier produced by Tool 1 (`create_node`).
   * @returns Node record from the in-memory snapshot.
   * @throws NodeNotFoundError When the requested node does not exist.
   */
  getNode(nodeId: string) {
    const record = this.snapshot.nodes[nodeId];
    if (!record) {
      throw new NodeNotFoundError(nodeId);
    }
    return Registry.cloneNode(record);
  }

  /**
   * Add new node to registry ensuring uniqueness constraints.
   *
   * @param record - Fully hydrated node metadata to insert.
   * @throws Error When a node with the same identifier already exists.
   */
  addNode(record: NodeRecord): void {
    if (this.snapshot.nodes[record.id]) {
      throw new Error(`Node already exists: ${record.id}`);
    }
    this.snapshot.nodes[record.id] = Registry.cloneNode(record);
  }

  /**
   * Update existing node metadata.
   *
   * @param record - Updated node record.
   * @throws NodeNotFoundError When the node does not exist.
   */
  updateNode(record: NodeRecord): void {
    if (!this.snapshot.nodes[record.id]) {
      throw new NodeNotFoundError(record.id);
    }
    this.snapshot.nodes[record.id] = Registry.cloneNode(record);
  }

  /**
   * Remove node and any associated references (connections handled separately).
   *
   * @param nodeId - Identifier for the node that should be removed.
   * @throws NodeNotFoundError When the node does not exist.
   */
  removeNode(nodeId: string): void {
    if (!this.snapshot.nodes[nodeId]) {
      throw new NodeNotFoundError(nodeId);
    }
    delete this.snapshot.nodes[nodeId];
  }

  /**
   * Fetch connection record by ID.
   *
   * @param connectionId - Identifier produced by Tool 6 (`create_connection`).
   * @returns Connection record from the in-memory snapshot.
   * @throws ConnectionNotFoundError When the requested connection does not exist.
   */
  getConnection(connectionId: string) {
    const record = this.snapshot.connections[connectionId];
    if (!record) {
      throw new ConnectionNotFoundError(connectionId);
    }
    return Registry.cloneConnection(record);
  }

  /**
   * Add new connection record to registry.
   *
   * @param record - Connection metadata to insert.
   * @throws Error When a connection with the same identifier already exists.
   */
  addConnection(record: ConnectionRecord): void {
    if (this.snapshot.connections[record.id]) {
      throw new Error(`Connection already exists: ${record.id}`);
    }
    this.snapshot.connections[record.id] = Registry.cloneConnection(record);
  }

  /**
   * Update existing connection metadata.
   *
   * @param record - Updated connection record.
   * @throws ConnectionNotFoundError When the connection does not exist.
   */
  updateConnection(record: ConnectionRecord): void {
    if (!this.snapshot.connections[record.id]) {
      throw new ConnectionNotFoundError(record.id);
    }
    this.snapshot.connections[record.id] = Registry.cloneConnection(record);
  }

  /**
   * Remove connection from registry.
   *
   * @param connectionId - Identifier for the connection that should be removed.
   * @throws ConnectionNotFoundError When the connection does not exist.
   */
  removeConnection(connectionId: string): void {
    if (!this.snapshot.connections[connectionId]) {
      throw new ConnectionNotFoundError(connectionId);
    }
    delete this.snapshot.connections[connectionId];
  }

  /**
   * Return node identifiers matching the supplied filter.
   *
   * @param filter - Type and property predicates from Tool 10 (`query_nodes`).
   * @returns Array of node identifiers satisfying the filter.
   */
  queryNodes(filter: QueryNodesRequest): string[] {
    const { type, properties } = filter;
    return Object.values(this.snapshot.nodes)
      .filter(node => {
        if (type && node.type !== type) {
          return false;
        }
        if (!properties) {
          return true;
        }
        return Registry.matchesProperties(node.properties, properties);
      })
      .map(node => node.id);
  }

  /**
   * Return connection identifiers matching the supplied filter.
   *
   * @param filter - Criteria from Tool 11 (`query_connections`).
   * @returns Array of connection identifiers satisfying the filter.
   */
  queryConnections(filter: QueryConnectionsRequest): string[] {
    const { from_node_id: from, to_node_id: to, type, properties } = filter;
    return Object.values(this.snapshot.connections)
      .filter(connection => {
        if (from && connection.from !== from) {
          return false;
        }
        if (to && connection.to !== to) {
          return false;
        }
        if (type && connection.type !== type) {
          return false;
        }
        if (!properties) {
          return true;
        }
        return Registry.matchesProperties(connection.properties, properties);
      })
      .map(connection => connection.id);
  }

  /**
   * Find connections touching the specified node with optional direction/type filters.
   *
   * @param nodeId - Node identifier used as traversal root.
   * @param filter - Connection type and direction filters mirroring Tool 12 (`get_connected_nodes`).
   * @returns Array of connection records associated with the node after filtering.
   * @throws NodeNotFoundError When the referenced node does not exist.
   */
  findConnectionsForNode(
    nodeId: string,
    filter: { connectionType?: string; direction: 'out' | 'in' | 'both' }
  ): ConnectionRecord[] {
    if (!this.snapshot.nodes[nodeId]) {
      throw new NodeNotFoundError(nodeId);
    }

    return Object.values(this.snapshot.connections)
      .filter(connection => {
        if (filter.connectionType && connection.type !== filter.connectionType) {
          return false;
        }
        if (filter.direction === 'out') {
          return connection.from === nodeId;
        }
        if (filter.direction === 'in') {
          return connection.to === nodeId;
        }
        return connection.from === nodeId || connection.to === nodeId;
      })
      .map(connection => Registry.cloneConnection(connection));
  }

  private static matchesProperties(candidate: Record<string, unknown>, filter: Record<string, unknown>): boolean {
    return Object.entries(filter).every(([key, value]) => candidate[key] === value);
  }

  private static cloneNode(record: NodeRecord): NodeRecord {
    return JSON.parse(JSON.stringify(record)) as NodeRecord;
  }

  private static cloneConnection(record: ConnectionRecord): ConnectionRecord {
    return JSON.parse(JSON.stringify(record)) as ConnectionRecord;
  }

  private static cloneSnapshot(snapshot: RegistrySnapshot): RegistrySnapshot {
    return {
      nodes: Object.fromEntries(
        Object.entries(snapshot.nodes ?? {}).map(([id, record]) => [id, Registry.cloneNode(record)])
      ),
      connections: Object.fromEntries(
        Object.entries(snapshot.connections ?? {}).map(([id, record]) => [id, Registry.cloneConnection(record)])
      )
    };
  }

  private static normalizeSnapshot(snapshot: RegistrySnapshot | undefined): RegistrySnapshot {
    if (!snapshot) {
      return { nodes: {}, connections: {} };
    }
    const normalizedNodes = snapshot.nodes && typeof snapshot.nodes === 'object' ? snapshot.nodes : {};
    const normalizedConnections =
      snapshot.connections && typeof snapshot.connections === 'object' ? snapshot.connections : {};
    return Registry.cloneSnapshot({
      nodes: normalizedNodes,
      connections: normalizedConnections
    });
  }
}

/**
 * Module: memoryGraph
 * Purpose: Orchestrate ontology, registry, and storage interactions for MCP tools.
 * Created: 2025-10-31
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/graph-memory-core.md
 */

import {
  type AddConnectionTypeRequest,
  type AddNodeTypeRequest,
  type ConnectionMetadata,
  type ConnectionTraversalDirection,
  type CreateConnectionRequest,
  type CreateConnectionResult,
  type CreateNodeRequest,
  type CreateNodeResult,
  type CreateOntologyRequest,
  type DeleteConnectionRequest,
  type DeleteNodeRequest,
  type GetConnectionRequest,
  type GetConnectedNodesRequest,
  type GetConnectedNodesResult,
  type GetNodeContentRequest,
  type GetNodeContentResult,
  type GetNodeRequest,
  type GetOntologyResult,
  type GraphMemoryServerConfig,
  type NodeRecord,
  type NodeMetadata,
  type ConnectionRecord,
  type ContentEncoding,
  type QueryConnectionsRequest,
  type QueryConnectionsResult,
  type QueryNodesRequest,
  type QueryNodesResult,
  type SearchContentRequest,
  type SearchContentResult,
  type UpdateConnectionRequest,
  type UpdateNodeRequest,
  type ValidateConnectionRequest,
  type ValidateConnectionResult
} from './types.js';
import { Registry } from './registry.js';
import { Ontology } from './ontology.js';
import type { GraphStorageGateway } from './storageGateway.js';
import {
  ConnectionNotFoundError,
  ContentReadFailedError,
  FileCreationFailedError,
  InvalidConnectionTypeError,
  InvalidEncodingError,
  InvalidNodeTypeError,
  InvalidTopologyError,
  NodeNotFoundError,
  OntologyAlreadyExistsError,
  OntologyNotFoundError,
  RequiredPropertyMissingError
} from './errors.js';
import { NODE_CONTENT_DIRECTORY, CONNECTION_CONTENT_DIRECTORY } from './constants.js';
import { generateId } from './idGenerator.js';

/**
 * Core service implementing all graph memory behaviors.
 */
export class MemoryGraph {
  private registry: Registry;
  private ontology: Ontology | null;

  constructor(
    private readonly config: GraphMemoryServerConfig,
    private readonly storage: GraphStorageGateway,
    registry: Registry,
    ontology: Ontology | null
  ) {
    this.registry = registry;
    this.ontology = ontology;
  }

  /**
   * Load registry and ontology from disk, preparing the graph for use.
   *
   * @param config - Server configuration derived from MCP environment variables.
   * @param storage - Gateway that wraps the file-storage-backend feature.
   * @returns Promise resolving to a ready-to-serve graph memory instance.
   * @throws OntologyNotFoundError When the ontology has not been created and callers request it eagerly.
   * @throws GraphMemoryError When registry or ontology persistence fails to load.
   */
  static async initialize(
    config: GraphMemoryServerConfig,
    storage: GraphStorageGateway
  ): Promise<MemoryGraph> {
    await storage.ensureDirectory('');
    await storage.ensureDirectory('_system');
    await storage.ensureDirectory(NODE_CONTENT_DIRECTORY);
    await storage.ensureDirectory(CONNECTION_CONTENT_DIRECTORY);

    const registry = await Registry.load(storage);

    let ontology: Ontology | null = null;
    try {
      ontology = await Ontology.load(storage);
    } catch (error) {
      if (error instanceof OntologyNotFoundError) {
        ontology = null;
      } else {
        throw error;
      }
    }

    return new MemoryGraph(config, storage, registry, ontology);
  }

  /**
   * Helper guard ensuring ontology is present before performing ontology-dependent operations.
   */
  private ensureOntology(): Ontology {
    if (!this.ontology) {
      throw new OntologyNotFoundError();
    }
    return this.ontology;
  }

  /**
   * Create a new typed node with optional properties and content.
   *
   * @param request - Tool 1 payload (`create_node`).
   * @returns Newly generated node identifier.
   * @throws OntologyNotFoundError When the ontology has not been created.
   * @throws InvalidNodeTypeError When the requested node type is not defined.
   * @throws FileCreationFailedError When the content file or registry cannot be written.
   */
  async createNode(request: CreateNodeRequest): Promise<CreateNodeResult> {
    const ontology = this.ensureOntology();
    ontology.assertNodeType(request.type);

    const nodeId = generateId('mem');
    const createdAt = new Date().toISOString();
    const contentPath = this.buildNodeContentPath(nodeId, request.encoding);

    await this.storage.ensureDirectory(NODE_CONTENT_DIRECTORY);

    try {
      if (request.encoding === 'utf-8') {
        await this.storage.writeText(contentPath, request.content);
      } else {
        const buffer = Buffer.from(request.content, 'base64');
        await this.storage.writeBinary(contentPath, buffer);
      }
    } catch (error) {
      throw new FileCreationFailedError(contentPath, error);
    }

    const record: NodeRecord = {
      id: nodeId,
      type: request.type,
      created: createdAt,
      modified: createdAt,
      properties: { ...(request.properties ?? {}) },
      content: {
        path: contentPath,
        format: request.format,
        encoding: request.encoding
      }
    };

    let addedToRegistry = false;
    try {
      this.registry.addNode(record);
      addedToRegistry = true;
      await this.registry.save(this.storage);
    } catch (error) {
      if (addedToRegistry) {
        this.registry.removeNode(nodeId);
      }
      await this.deleteContentQuietly(contentPath);
      throw error;
    }

    return { node_id: nodeId };
  }

  /**
   * Retrieve metadata for a node without loading its content.
   *
   * @param request - Tool 2 payload (`get_node`).
   * @returns Node metadata excluding content body.
   * @throws NodeNotFoundError When the node does not exist.
   */
  async getNode(request: GetNodeRequest): Promise<NodeMetadata> {
    const record = this.registry.getNode(request.node_id);
    return {
      id: record.id,
      type: record.type,
      created: record.created,
      modified: record.modified,
      properties: { ...record.properties },
      content_format: record.content.format
    };
  }

  /**
   * Retrieve stored content for a node.
   *
   * @param request - Tool 3 payload (`get_node_content`).
   * @returns Node content string in the requested encoding.
   * @throws NodeNotFoundError When the node does not exist.
   * @throws ContentReadFailedError When the associated content file cannot be read.
   */
  async getNodeContent(request: GetNodeContentRequest): Promise<GetNodeContentResult> {
    const record = this.registry.getNode(request.node_id);
    try {
      if (record.content.encoding === 'utf-8') {
        const text = await this.storage.readText(record.content.path);
        return { content: text };
      }
      const buffer = await this.storage.readBinary(record.content.path);
      return { content: buffer.toString('base64') };
    } catch (error) {
      throw new ContentReadFailedError(record.content.path, error);
    }
  }

  /**
   * Update node properties and/or content.
   *
   * @param request - Tool 4 payload (`update_node`).
   * @returns Promise that resolves when the node has been updated.
   * @throws NodeNotFoundError When the node does not exist.
   * @throws InvalidEncodingError When content is provided without encoding.
   * @throws FileCreationFailedError When writing updated content fails.
   */
  async updateNode(request: UpdateNodeRequest): Promise<void> {
    const existing = this.requireNode(request.node_id);

    if (request.content !== undefined && !request.encoding) {
      throw new InvalidEncodingError();
    }

    const updatedAt = new Date().toISOString();
    const targetEncoding = request.content !== undefined ? request.encoding! : existing.content.encoding;
    const targetPath = this.buildNodeContentPath(existing.id, targetEncoding);
    const targetFormat = request.format ?? existing.content.format;

    const updatedRecord: NodeRecord = {
      ...existing,
      modified: updatedAt,
      properties: request.properties
        ? { ...existing.properties, ...request.properties }
        : { ...existing.properties },
      content: {
        path: targetPath,
        format: targetFormat,
        encoding: targetEncoding
      }
    };

    let contentWritten = false;
    if (request.content !== undefined) {
      await this.storage.ensureDirectory(NODE_CONTENT_DIRECTORY);
      try {
        if (targetEncoding === 'utf-8') {
          await this.storage.writeText(targetPath, request.content);
        } else {
          const buffer = Buffer.from(request.content, 'base64');
          await this.storage.writeBinary(targetPath, buffer);
        }
        contentWritten = true;
      } catch (error) {
        throw new FileCreationFailedError(targetPath, error);
      }
    }

    try {
      this.registry.updateNode(updatedRecord);
      await this.registry.save(this.storage);
    } catch (error) {
      if (contentWritten && targetPath !== existing.content.path) {
        await this.deleteContentQuietly(targetPath);
      }
      throw error;
    }

    if (contentWritten && targetPath !== existing.content.path) {
      await this.deleteContentQuietly(existing.content.path);
    }
  }

  /**
   * Delete a node and cascade delete its connections.
   *
   * @param request - Tool 5 payload (`delete_node`).
   * @returns Promise that resolves once deletion succeeds.
   * @throws NodeNotFoundError When the node does not exist.
   */
  async deleteNode(request: DeleteNodeRequest): Promise<void> {
    const node = this.requireNode(request.node_id);
    const connections = this.registry.findConnectionsForNode(node.id, { direction: 'both' });

    try {
      for (const connection of connections) {
        this.registry.removeConnection(connection.id);
      }
      this.registry.removeNode(node.id);
      await this.registry.save(this.storage);
    } catch (error) {
      // Restore snapshot before rethrowing to keep registry consistent.
      await this.restoreRegistryState(node, connections);
      throw error;
    }

    for (const connection of connections) {
      if (connection.content?.path) {
        try {
          await this.storage.deletePath(connection.content.path);
        } catch (error) {
          await this.restoreRegistryState(node, connections);
          throw new FileCreationFailedError(connection.content.path, error);
        }
      }
    }

    try {
      await this.storage.deletePath(node.content.path);
    } catch (error) {
      await this.restoreRegistryState(node, connections);
      throw new FileCreationFailedError(node.content.path, error);
    }
  }

  /**
   * Create a new typed connection between two nodes.
   *
   * @param request - Tool 6 payload (`create_connection`).
   * @returns Newly generated connection identifier.
   * @throws OntologyNotFoundError When the ontology has not been created.
   * @throws InvalidConnectionTypeError When the connection type is not defined.
   * @throws InvalidTopologyError When the requested endpoints violate topology rules.
   * @throws RequiredPropertyMissingError When required properties are omitted.
   * @throws NodeNotFoundError When either endpoint does not exist.
   * @throws FileCreationFailedError When optional content cannot be persisted.
   */
  async createConnection(request: CreateConnectionRequest): Promise<CreateConnectionResult> {
    const ontology = this.ensureOntology();
    ontology.assertConnectionType(request.type);

    const fromNode = this.requireNode(request.from_node_id);
    const toNode = this.requireNode(request.to_node_id);

    const validation = ontology.validateConnection({
      connection_type: request.type,
      from_node_type: fromNode.type,
      to_node_type: toNode.type
    });

    if (!validation.valid) {
      const definition = ontology.toSnapshot().connection_types.find(type => type.name === request.type);
      const allowedFrom = definition?.from_types ?? [];
      const allowedTo = definition?.to_types ?? [];
      throw new InvalidTopologyError(request.type, fromNode.type, toNode.type, {
        allowedFrom,
        allowedTo
      });
    }

    ontology.ensureRequiredProperties(request.type, new Set(Object.keys(request.properties ?? {})));

    const connectionId = generateId('conn');
    const createdAt = new Date().toISOString();
    const record: ConnectionRecord = {
      id: connectionId,
      type: request.type,
      from: fromNode.id,
      to: toNode.id,
      created: createdAt,
      modified: createdAt,
      properties: { ...(request.properties ?? {}) }
    };

    let contentPath: string | undefined;
    if (request.content !== undefined) {
      contentPath = this.buildConnectionContentPath(connectionId);
      await this.storage.ensureDirectory(CONNECTION_CONTENT_DIRECTORY);
      try {
        await this.storage.writeText(contentPath, request.content);
      } catch (error) {
        throw new FileCreationFailedError(contentPath, error);
      }
      record.content = {
        path: contentPath,
        format: request.format ?? 'text'
      };
    }

    let added = false;
    try {
      this.registry.addConnection(record);
      added = true;
      await this.registry.save(this.storage);
    } catch (error) {
      if (added) {
        this.registry.removeConnection(connectionId);
      }
      if (contentPath) {
        await this.deleteContentQuietly(contentPath);
      }
      throw error;
    }

    return { connection_id: connectionId };
  }

  /**
   * Retrieve metadata for a connection without loading optional content.
   *
   * @param request - Tool 7 payload (`get_connection`).
   * @returns Connection metadata inclusive of endpoint identifiers.
   * @throws ConnectionNotFoundError When the connection does not exist.
   */
  async getConnection(request: GetConnectionRequest): Promise<ConnectionMetadata> {
    const record = this.registry.getConnection(request.connection_id);
    return {
      id: record.id,
      type: record.type,
      from_node_id: record.from,
      to_node_id: record.to,
      created: record.created,
      modified: record.modified,
      properties: { ...record.properties },
      has_content: Boolean(record.content)
    };
  }

  /**
   * Update connection properties and/or optional content.
   *
   * @param request - Tool 8 payload (`update_connection`).
   * @returns Promise that resolves once the connection has been updated.
   * @throws ConnectionNotFoundError When the connection does not exist.
   * @throws FileCreationFailedError When updated content cannot be persisted.
   */
  async updateConnection(request: UpdateConnectionRequest): Promise<void> {
    const existing = this.requireConnection(request.connection_id);
    const updatedAt = new Date().toISOString();
    const targetPath = this.buildConnectionContentPath(existing.id);

    const updatedRecord: ConnectionRecord = {
      ...existing,
      modified: updatedAt,
      properties: request.properties ? { ...existing.properties, ...request.properties } : { ...existing.properties }
    };

    if (request.content !== undefined) {
      await this.storage.ensureDirectory(CONNECTION_CONTENT_DIRECTORY);
      try {
        await this.storage.writeText(targetPath, request.content);
      } catch (error) {
        throw new FileCreationFailedError(targetPath, error);
      }
      updatedRecord.content = {
        path: targetPath,
        format: request.format ?? existing.content?.format ?? 'text'
      };
    } else if (request.format && existing.content) {
      updatedRecord.content = {
        path: existing.content.path,
        format: request.format
      };
    }

    this.registry.updateConnection(updatedRecord);
    await this.registry.save(this.storage);
  }

  /**
   * Delete a connection without removing its nodes.
   *
   * @param request - Tool 9 payload (`delete_connection`).
   * @returns Promise that resolves once the connection has been removed.
   * @throws ConnectionNotFoundError When the connection does not exist.
   */
  async deleteConnection(request: DeleteConnectionRequest): Promise<void> {
    const connection = this.requireConnection(request.connection_id);

    this.registry.removeConnection(connection.id);
    await this.registry.save(this.storage);

    if (connection.content?.path) {
      try {
        await this.storage.deletePath(connection.content.path);
      } catch (error) {
        throw new FileCreationFailedError(connection.content.path, error);
      }
    }
  }

  /**
   * Query nodes by type and/or properties using AND semantics.
   *
   * @param request - Tool 10 payload (`query_nodes`).
   * @returns Identifiers for nodes matching the supplied filters.
   */
  async queryNodes(request: QueryNodesRequest): Promise<QueryNodesResult> {
    const nodeIds = this.registry.queryNodes(request);
    return { node_ids: nodeIds };
  }

  /**
   * Query connections by endpoints, type, and optional properties.
   *
   * @param request - Tool 11 payload (`query_connections`).
   * @returns Identifiers for connections matching the supplied filters.
   */
  async queryConnections(request: QueryConnectionsRequest): Promise<QueryConnectionsResult> {
    const connectionIds = this.registry.queryConnections(request);
    return { connection_ids: connectionIds };
  }

  /**
   * Traverse graph connections from a node in the requested direction.
   *
   * @param request - Tool 12 payload (`get_connected_nodes`).
   * @returns Identifiers for nodes discovered during traversal.
   * @throws NodeNotFoundError When the starting node does not exist.
   */
  async getConnectedNodes(request: GetConnectedNodesRequest): Promise<GetConnectedNodesResult> {
    const direction = this.resolveDirection(request.direction);
    const connections = this.registry.findConnectionsForNode(request.node_id, {
      connectionType: request.connection_type,
      direction
    });

    const results = new Set<string>();
    for (const connection of connections) {
      if (direction === 'out') {
        results.add(connection.to);
      } else if (direction === 'in') {
        results.add(connection.from);
      } else {
        if (connection.from === request.node_id) {
          results.add(connection.to);
        }
        if (connection.to === request.node_id) {
          results.add(connection.from);
        }
      }
    }

    return { node_ids: Array.from(results) };
  }

  /**
   * Perform case-insensitive substring search across UTF-8 node content.
   *
   * @param request - Tool 13 payload (`search_content`).
   * @returns Identifiers for nodes whose content matches the query.
   */
  async searchContent(request: SearchContentRequest): Promise<SearchContentResult> {
    const limit = request.limit ?? Number.POSITIVE_INFINITY;
    if (limit <= 0) {
      return { node_ids: [] };
    }

    const normalizedQuery = request.query.toLowerCase();
    const filter: QueryNodesRequest = {};
    if (request.node_type) {
      filter.type = request.node_type;
    }

    const candidateIds = this.registry.queryNodes(filter);
    const matches: string[] = [];

    for (const nodeId of candidateIds) {
      if (matches.length >= limit) {
        break;
      }

      const node = this.registry.getNode(nodeId);
      if (node.content.encoding !== 'utf-8') {
        continue;
      }

      let content: string;
      try {
        content = await this.storage.readText(node.content.path);
      } catch (error) {
        throw new ContentReadFailedError(node.content.path, error);
      }

      if (content.toLowerCase().includes(normalizedQuery)) {
        matches.push(nodeId);
      }
    }

    return { node_ids: matches.slice(0, limit === Number.POSITIVE_INFINITY ? undefined : limit) };
  }

  /**
   * Validate whether a connection type is permitted between two node types.
   *
   * @param request - Tool 14 payload (`validate_connection`).
   * @returns Validation result indicating whether the connection is allowed.
   * @throws OntologyNotFoundError When the ontology has not been created.
   * @throws InvalidConnectionTypeError When the connection type is unknown.
   */
  async validateConnection(request: ValidateConnectionRequest): Promise<ValidateConnectionResult> {
    const ontology = this.ensureOntology();
    return ontology.validateConnection(request);
  }

  /**
   * Create the ontology with initial node and connection types.
   *
   * @param request - Tool 15 payload (`create_ontology`).
   * @returns Promise that resolves once the ontology is persisted.
   * @throws OntologyAlreadyExistsError When the ontology is already defined.
   * @throws FileCreationFailedError When the ontology file cannot be written.
   */
  async createOntology(request: CreateOntologyRequest): Promise<void> {
    if (this.ontology) {
      throw new OntologyAlreadyExistsError();
    }

    const ontology = Ontology.fromCreateRequest(request);
    await ontology.save(this.storage);
    this.ontology = ontology;
  }

  /**
   * Append a node type to the existing ontology definition.
   *
   * @param request - Tool 16 payload (`add_node_type`).
   * @returns Promise resolving once the ontology update is persisted.
   * @throws OntologyNotFoundError When the ontology has not been created.
   * @throws TypeAlreadyExistsError When the node type already exists.
   * @throws FileCreationFailedError When the ontology file cannot be written.
   */
  async addNodeType(request: AddNodeTypeRequest): Promise<void> {
    const ontology = this.ensureOntology();
    ontology.addNodeType(request);
    await ontology.save(this.storage);
  }

  /**
   * Append a connection type to the existing ontology definition.
   *
   * @param request - Tool 17 payload (`add_connection_type`).
   * @returns Promise resolving once the ontology update is persisted.
   * @throws OntologyNotFoundError When the ontology has not been created.
   * @throws TypeAlreadyExistsError When the connection type already exists.
   * @throws FileCreationFailedError When the ontology file cannot be written.
   */
  async addConnectionType(request: AddConnectionTypeRequest): Promise<void> {
    const ontology = this.ensureOntology();
    ontology.addConnectionType(request);
    await ontology.save(this.storage);
  }

  /**
   * Retrieve the current ontology snapshot.
   *
   * @returns Structured ontology data for Tool 18 (`get_ontology`).
   * @throws OntologyNotFoundError When the ontology has not been created.
   */
  async getOntology(): Promise<GetOntologyResult> {
    const ontology = this.ensureOntology();
    return ontology.toSnapshot();
  }

  /**
   * Helper retrieving node record or throwing specification-aligned error.
   */
  private requireNode(nodeId: string) {
    return this.registry.getNode(nodeId);
  }

  /**
   * Helper retrieving connection record or throwing specification-aligned error.
   */
  private requireConnection(connectionId: string) {
    return this.registry.getConnection(connectionId);
  }

  /**
   * Normalize traversal direction for downstream consumers.
   */
  private resolveDirection(direction: ConnectionTraversalDirection): ConnectionTraversalDirection {
    return direction ?? 'both';
  }

  private buildNodeContentPath(nodeId: string, encoding: ContentEncoding): string {
    const extension = encoding === 'utf-8' ? '.txt' : '.bin';
    return `${NODE_CONTENT_DIRECTORY}/${nodeId}${extension}`;
  }

  private buildConnectionContentPath(connectionId: string): string {
    return `${CONNECTION_CONTENT_DIRECTORY}/${connectionId}.txt`;
  }

  private async deleteContentQuietly(path?: string): Promise<void> {
    if (!path) {
      return;
    }
    try {
      const exists = await this.storage.pathExists(path);
      if (exists) {
        await this.storage.deletePath(path);
      }
    } catch {
      // Ignore best-effort cleanup errors.
    }
  }

  private async restoreRegistryState(node: NodeRecord, connections: ConnectionRecord[]): Promise<void> {
    try {
      this.registry.addNode(node);
    } catch {
      this.registry.updateNode(node);
    }

    for (const connection of connections) {
      try {
        this.registry.addConnection(connection);
      } catch {
        this.registry.updateConnection(connection);
      }
    }

    await this.registry.save(this.storage);
  }
}

/**
 * Module: ontology
 * Purpose: Encapsulate ontology.yaml parsing, validation, and updates.
 * Created: 2025-10-31
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/graph-memory-core.md
 */

import yaml from 'js-yaml';
import type {
  AddConnectionTypeRequest,
  AddNodeTypeRequest,
  CreateOntologyRequest,
  OntologyConnectionType,
  OntologySnapshot,
  ValidateConnectionRequest,
  ValidateConnectionResult
} from './types.js';
import type { GraphStorageGateway } from './storageGateway.js';
import {
  ContentReadFailedError,
  FileCreationFailedError,
  InvalidConnectionTypeError,
  InvalidNodeTypeError,
  OntologyNotFoundError,
  RequiredPropertyMissingError,
  TypeAlreadyExistsError
} from './errors.js';
import { ONTOLOGY_FILE_PATH } from './constants.js';

/**
 * Representation of the ontology with helper validation routines.
 */
export class Ontology {
  private snapshot: OntologySnapshot;

  constructor(snapshot: OntologySnapshot) {
    this.snapshot = snapshot;
  }

  /**
   * Load ontology metadata from persistent storage.
   *
   * @param storage - Gateway responsible for reading `_system/ontology.yaml`.
   * @returns Promise resolving to an ontology representation.
   * @throws OntologyNotFoundError When the ontology file has not been created yet.
   * @throws ContentReadFailedError When the ontology file cannot be read or parsed.
   */
  static async load(storage: GraphStorageGateway): Promise<Ontology> {
    const exists = await storage.pathExists(ONTOLOGY_FILE_PATH);
    if (!exists) {
      throw new OntologyNotFoundError();
    }
    try {
      const contents = await storage.readText(ONTOLOGY_FILE_PATH);
      const parsed = yaml.load(contents) as OntologySnapshot | null;
      return new Ontology(Ontology.normalizeSnapshot(parsed ?? undefined));
    } catch (error) {
      throw new ContentReadFailedError(ONTOLOGY_FILE_PATH, error);
    }
  }

  /**
   * Create ontology from Tool 15 payload.
   *
   * @param request - Raw ontology definition supplied to Tool 15 (`create_ontology`).
   * @returns New ontology instance containing the provided types.
   */
  static fromCreateRequest(request: CreateOntologyRequest): Ontology {
    const nodeTypes = Array.from(new Set(request.node_types ?? []));
    const connectionTypes = (request.connection_types ?? []).map(connection => ({
      name: connection.name,
      from_types: Array.from(new Set(connection.from_types ?? [])),
      to_types: Array.from(new Set(connection.to_types ?? [])),
      ...(connection.required_properties && connection.required_properties.length > 0
        ? { required_properties: Array.from(new Set(connection.required_properties)) }
        : {})
    }));
    return new Ontology({
      node_types: nodeTypes,
      connection_types: connectionTypes
    });
  }

  /**
   * Serialize to snapshot for persistence.
   *
   * @returns Snapshot suitable for writing to `_system/ontology.yaml`.
   */
  toSnapshot(): OntologySnapshot {
    return Ontology.cloneSnapshot(this.snapshot);
  }

  /**
   * Persist current ontology snapshot to storage.
   *
   * @param storage - Gateway used to write `_system/ontology.yaml`.
   * @throws FileCreationFailedError When the ontology file cannot be written atomically.
   */
  async save(storage: GraphStorageGateway): Promise<void> {
    try {
      await storage.ensureDirectory(ONTOLOGY_FILE_PATH.split('/').slice(0, -1).join('/'));
      const serialized = yaml.dump(this.snapshot, { noRefs: true, lineWidth: 120 });
      await storage.writeText(ONTOLOGY_FILE_PATH, serialized);
    } catch (error) {
      throw new FileCreationFailedError(ONTOLOGY_FILE_PATH, error);
    }
  }

  /**
   * Ensure a node type exists, throwing if it does not.
   *
   * @param typeName - Node type that must be defined in the ontology.
   * @throws InvalidNodeTypeError When the requested node type is unknown.
   */
  assertNodeType(typeName: string): void {
    if (!this.snapshot.node_types.includes(typeName)) {
      throw new InvalidNodeTypeError(typeName);
    }
  }

  /**
   * Ensure a connection type exists, throwing if it does not.
   *
   * @param typeName - Connection type that must be defined in the ontology.
   * @throws InvalidConnectionTypeError When the requested connection type is unknown.
   */
  assertConnectionType(typeName: string): void {
    if (!this.getConnectionType(typeName)) {
      throw new InvalidConnectionTypeError(typeName);
    }
  }

  /**
   * Validate connection topology according to Tool 14 rules.
   *
   * @param request - Parameters supplied to Tool 14 (`validate_connection`).
   * @returns Result describing whether the connection is permitted.
   * @throws InvalidConnectionTypeError When the connection type is unknown.
   */
  validateConnection(request: ValidateConnectionRequest): ValidateConnectionResult {
    const definition = this.getConnectionType(request.connection_type);
    if (!definition) {
      throw new InvalidConnectionTypeError(request.connection_type);
    }
    const fromValid = definition.from_types.includes(request.from_node_type);
    const toValid = definition.to_types.includes(request.to_node_type);
    return { valid: fromValid && toValid };
  }

  /**
   * Check that all required properties have been provided when creating a connection.
   *
   * @param connectionType - Connection type whose required properties must be enforced.
   * @param provided - Set of property keys supplied by the caller.
   * @throws RequiredPropertyMissingError When any required property is absent.
   */
  ensureRequiredProperties(connectionType: string, provided: Set<string>): void {
    const definition = this.getConnectionType(connectionType);
    if (!definition) {
      throw new InvalidConnectionTypeError(connectionType);
    }
    const required = definition.required_properties ?? [];
    if (required.length === 0) {
      return;
    }

    const missing = required.filter(property => !provided.has(property));
    if (missing.length > 0) {
      throw new RequiredPropertyMissingError(connectionType, required, missing);
    }
  }

  /**
   * Add a new node type in append-only fashion.
   *
   * @param request - Payload from Tool 16 (`add_node_type`).
   * @throws TypeAlreadyExistsError When the node type already exists.
   */
  addNodeType(request: AddNodeTypeRequest): void {
    if (this.snapshot.node_types.includes(request.type_name)) {
      throw new TypeAlreadyExistsError(request.type_name);
    }
    this.snapshot.node_types.push(request.type_name);
  }

  /**
   * Add a new connection type in append-only fashion.
   *
   * @param request - Payload from Tool 17 (`add_connection_type`).
   * @throws TypeAlreadyExistsError When the connection type already exists.
   */
  addConnectionType(request: AddConnectionTypeRequest): void {
    if (this.getConnectionType(request.type_name)) {
      throw new TypeAlreadyExistsError(request.type_name);
    }
    const record: OntologyConnectionType = {
      name: request.type_name,
      from_types: Array.from(new Set(request.from_types ?? [])),
      to_types: Array.from(new Set(request.to_types ?? [])),
      ...(request.required_properties && request.required_properties.length > 0
        ? { required_properties: Array.from(new Set(request.required_properties)) }
        : {})
    };
    this.snapshot.connection_types.push(record);
  }

  private static cloneSnapshot(snapshot: OntologySnapshot): OntologySnapshot {
    return {
      node_types: [...(snapshot.node_types ?? [])],
      connection_types: (snapshot.connection_types ?? []).map(connection => ({
        name: connection.name,
        from_types: [...(connection.from_types ?? [])],
        to_types: [...(connection.to_types ?? [])],
        ...(connection.required_properties ? { required_properties: [...connection.required_properties] } : {})
      }))
    };
  }

  private static normalizeSnapshot(snapshot: OntologySnapshot | undefined): OntologySnapshot {
    if (!snapshot) {
      return { node_types: [], connection_types: [] };
    }
    return Ontology.cloneSnapshot({
      node_types: snapshot.node_types ?? [],
      connection_types: snapshot.connection_types ?? []
    });
  }

  private getConnectionType(typeName: string): OntologyConnectionType | undefined {
    return this.snapshot.connection_types.find(connection => connection.name === typeName);
  }
}

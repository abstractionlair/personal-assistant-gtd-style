/**
 * Module: types
 * Purpose: Declare shared types for the graph-memory-core MCP server skeleton.
 * Created: 2025-10-31
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/done/graph-memory-core.md
 */

/**
 * Supported encodings for persisted node content, mirroring specification wording.
 */
export type ContentEncoding = 'utf-8' | 'base64';

/**
 * Union of property value primitives permitted in node/connection metadata.
 */
export type PropertyValue = string | number | boolean;

/**
 * Key-value property bag attached to nodes or connections.
 */
export type PropertyMap = Record<string, PropertyValue>;

/**
 * Internal node record persisted in the registry file.
 */
export interface NodeRecord {
  id: string;
  type: string;
  created: string;
  modified: string;
  properties: PropertyMap;
  content: {
    path: string;
    format: string;
    encoding: ContentEncoding;
  };
}

/**
 * Internal connection record persisted in the registry file.
 */
export interface ConnectionRecord {
  id: string;
  type: string;
  from: string;
  to: string;
  created: string;
  modified: string;
  properties: PropertyMap;
  content?: {
    path: string;
    format: string;
  };
}

/**
 * Snapshot of the entire registry structure loaded from disk.
 */
export interface RegistrySnapshot {
  nodes: Record<string, NodeRecord>;
  connections: Record<string, ConnectionRecord>;
}

/**
 * Definition of a node type inside the ontology file.
 */
export interface OntologyNodeType {
  name: string;
}

/**
 * Definition of a connection type inside the ontology file.
 */
export interface OntologyConnectionType {
  name: string;
  from_types: string[];
  to_types: string[];
  required_properties?: string[];
}

/**
 * Snapshot of the ontology YAML structure.
 */
export interface OntologySnapshot {
  node_types: string[];
  connection_types: OntologyConnectionType[];
}

/**
 * Configuration required to bootstrap the MCP server.
 */
export interface GraphMemoryServerConfig {
  basePath: string;
}

/**
 * Request payload for Tool 1: create_node.
 */
export interface CreateNodeRequest {
  type: string;
  content: string;
  encoding: ContentEncoding;
  format: string;
  properties?: PropertyMap;
}

/**
 * Response payload for Tool 1.
 */
export interface CreateNodeResult {
  node_id: string;
}

/**
 * Request payload for Tool 2: get_node.
 */
export interface GetNodeRequest {
  node_id: string;
}

/**
 * Node metadata returned by Tool 2.
 */
export interface NodeMetadata {
  id: string;
  type: string;
  created: string;
  modified: string;
  properties: PropertyMap;
  content_format: string;
}

/**
 * Request payload for Tool 3: get_node_content.
 */
export interface GetNodeContentRequest {
  node_id: string;
}

/**
 * Response payload for Tool 3.
 */
export interface GetNodeContentResult {
  content: string;
}

/**
 * Request payload for Tool 4: update_node.
 */
export interface UpdateNodeRequest {
  node_id: string;
  properties?: PropertyMap;
  content?: string;
  encoding?: ContentEncoding;
  format?: string;
}

/**
 * Request payload for Tool 5: delete_node.
 */
export interface DeleteNodeRequest {
  node_id: string;
}

/**
 * Request payload for Tool 6: create_connection.
 */
export interface CreateConnectionRequest {
  type: string;
  from_node_id: string;
  to_node_id: string;
  properties?: PropertyMap;
  content?: string;
  format?: string;
}

/**
 * Response payload for Tool 6.
 */
export interface CreateConnectionResult {
  connection_id: string;
}

/**
 * Request payload for Tool 7: get_connection.
 */
export interface GetConnectionRequest {
  connection_id: string;
}

/**
 * Connection metadata returned by Tool 7.
 */
export interface ConnectionMetadata {
  id: string;
  type: string;
  from_node_id: string;
  to_node_id: string;
  created: string;
  modified: string;
  properties: PropertyMap;
  has_content: boolean;
}

/**
 * Request payload for Tool 8: update_connection.
 */
export interface UpdateConnectionRequest {
  connection_id: string;
  properties?: PropertyMap;
  content?: string;
  format?: string;
}

/**
 * Request payload for Tool 9: delete_connection.
 */
export interface DeleteConnectionRequest {
  connection_id: string;
}

/**
 * Request payload for Tool 10: query_nodes.
 */
export interface QueryNodesRequest {
  type?: string;
  properties?: PropertyMap;
}

/**
 * Response payload for Tool 10.
 */
export interface QueryNodesResult {
  node_ids: string[];
}

/**
 * Request payload for Tool 11: query_connections.
 */
export interface QueryConnectionsRequest {
  from_node_id?: string;
  to_node_id?: string;
  type?: string;
  properties?: PropertyMap;
}

/**
 * Response payload for Tool 11.
 */
export interface QueryConnectionsResult {
  connection_ids: string[];
}

/**
 * Direction enumerator used by Tool 12.
 */
export type ConnectionTraversalDirection = 'out' | 'in' | 'both';

/**
 * Request payload for Tool 12: get_connected_nodes.
 */
export interface GetConnectedNodesRequest {
  node_id: string;
  connection_type?: string;
  direction: ConnectionTraversalDirection;
}

/**
 * Response payload for Tool 12.
 */
export interface GetConnectedNodesResult {
  node_ids: string[];
}

/**
 * Request payload for Tool 13: search_content.
 */
export interface SearchContentRequest {
  query: string;
  node_type?: string;
  limit?: number;
}

/**
 * Response payload for Tool 13.
 */
export interface SearchContentResult {
  node_ids: string[];
}

/**
 * Request payload for Tool 14: validate_connection.
 */
export interface ValidateConnectionRequest {
  connection_type: string;
  from_node_type: string;
  to_node_type: string;
}

/**
 * Response payload for Tool 14.
 */
export interface ValidateConnectionResult {
  valid: boolean;
}

/**
 * Request payload for Tool 15: create_ontology.
 */
export interface CreateOntologyRequest {
  node_types: string[];
  connection_types: Array<{
    name: string;
    from_types: string[];
    to_types: string[];
    required_properties?: string[];
  }>;
}

/**
 * Request payload for Tool 16: add_node_type.
 */
export interface AddNodeTypeRequest {
  type_name: string;
}

/**
 * Request payload for Tool 17: add_connection_type.
 */
export interface AddConnectionTypeRequest {
  type_name: string;
  from_types: string[];
  to_types: string[];
  required_properties?: string[];
}

/**
 * Response payload for Tool 18: get_ontology.
 */
export interface GetOntologyResult {
  node_types: string[];
  connection_types: Array<{
    name: string;
    from_types: string[];
    to_types: string[];
    required_properties?: string[];
  }>;
}

/**
 * Request payload for Tool 19: ensure_singleton_node.
 */
export interface EnsureSingletonNodeRequest {
  type: string;
  content?: string;
  encoding?: ContentEncoding;
  format?: string;
  properties?: PropertyMap;
  on_multiple?: 'oldest' | 'newest';
}

/**
 * Response payload for Tool 19.
 */
export interface EnsureSingletonNodeResult {
  node_id: string;
  created: boolean;
}

/**
 * Enumeration of specification-defined error codes returned by MCP tools.
 */
export type GraphMemoryErrorCode =
  | 'ONTOLOGY_NOT_FOUND'
  | 'ONTOLOGY_ALREADY_EXISTS'
  | 'TYPE_ALREADY_EXISTS'
  | 'INVALID_NODE_TYPE'
  | 'INVALID_CONNECTION_TYPE'
  | 'INVALID_TOPOLOGY'
  | 'REQUIRED_PROPERTY_MISSING'
  | 'NODE_NOT_FOUND'
  | 'CONNECTION_NOT_FOUND'
  | 'FILE_CREATION_FAILED'
  | 'CONTENT_READ_FAILED'
  | 'INVALID_ENCODING'
  | 'INVALID_ARGUMENT';

/**
 * MCP error payload returned by skeleton handlers.
 */
export interface GraphMemoryErrorPayload {
  code: GraphMemoryErrorCode;
  message: string;
  details?: Record<string, unknown>;
}

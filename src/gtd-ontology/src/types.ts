/**
 * Module: types
 * Purpose: Domain and integration types for GTD ontology coordination.
 * Created: 2025-11-02
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/doing/gtd-ontology.md
 */

export type NodeId = string;
export type ConnectionId = string;

export type GtdNodeType = 'Task' | 'State' | 'Context' | 'UNSPECIFIED';

export const GTD_NODE_TYPES: readonly GtdNodeType[] = ['Task', 'State', 'Context', 'UNSPECIFIED'];

export const DEPENDENCY_CONNECTION_TYPE = 'DependsOn' as const;

export type StateLogic = 'ANY' | 'ALL' | 'MANUAL' | 'IMMUTABLE';

export interface TaskProperties extends Record<string, unknown> {
  isComplete: boolean;
  responsibleParty?: string;
  created?: string;
  modified?: string;
}

export interface StateProperties extends Record<string, unknown> {
  isTrue: boolean;
  logic: StateLogic;
  created?: string;
  modified?: string;
}

export interface ContextProperties extends Record<string, unknown> {
  isAvailable: boolean;
  created?: string;
  modified?: string;
}

export interface BaseNodeRecord<TType extends GtdNodeType, TProps extends Record<string, unknown>> {
  id: NodeId;
  type: TType;
  properties: TProps;
  created: string;
  modified: string;
  content_format?: string;
}

export type TaskNode = BaseNodeRecord<'Task', TaskProperties>;
export type StateNode = BaseNodeRecord<'State', StateProperties>;
export type ContextNode = BaseNodeRecord<'Context', ContextProperties>;
export type UnspecifiedNode = BaseNodeRecord<'UNSPECIFIED', Record<string, never>>;

export type GtdNode = TaskNode | StateNode | ContextNode | UnspecifiedNode;

export interface CreateOntologyRequest {
  node_types: string[];
  connection_types: Array<{
    name: string;
    from_types: string[];
    to_types: string[];
    required_properties?: string[];
  }>;
}

export interface EnsureSingletonNodeRequest {
  type: string;
  content?: string;
  encoding?: 'utf-8' | 'base64';
  format?: string;
  properties?: Record<string, unknown>;
  on_multiple?: 'oldest' | 'newest';
}

export interface EnsureSingletonNodeResult {
  node_id: NodeId;
  created: boolean;
}

export interface QueryNodesRequest {
  type?: string;
  properties?: Record<string, unknown>;
}

export interface QueryNodesResult {
  node_ids: NodeId[];
}

export type ConnectionTraversalDirection = 'out' | 'in' | 'both';

export interface GetConnectedNodesRequest {
  node_id: NodeId;
  connection_type?: string;
  direction: ConnectionTraversalDirection;
}

export interface GetConnectedNodesResult {
  node_ids: NodeId[];
}

export interface QueryConnectionsRequest {
  from_node_id?: NodeId;
  to_node_id?: NodeId;
  type?: string;
  properties?: Record<string, unknown>;
}

export interface QueryConnectionsResult {
  connection_ids: ConnectionId[];
}

export interface UpdateNodeRequest {
  id: NodeId;
  properties?: Record<string, unknown>;
  content?: string;
  encoding?: 'utf-8' | 'base64';
  format?: string;
}

export interface GetNodeRequest {
  node_id: NodeId;
}

export interface NodeMetadata {
  id: NodeId;
  type: string;
  properties: Record<string, unknown>;
  created: string;
  modified: string;
  content_format?: string;
}

export interface GraphMemoryClient {
  createOntology(request: CreateOntologyRequest): Promise<void>;
  ensureSingletonNode(request: EnsureSingletonNodeRequest): Promise<EnsureSingletonNodeResult>;
  queryNodes(request: QueryNodesRequest): Promise<QueryNodesResult>;
  queryConnections(request: QueryConnectionsRequest): Promise<QueryConnectionsResult>;
  getConnectedNodes(request: GetConnectedNodesRequest): Promise<GetConnectedNodesResult>;
  getNode(request: GetNodeRequest): Promise<NodeMetadata>;
  updateNode(request: UpdateNodeRequest): Promise<void>;
}

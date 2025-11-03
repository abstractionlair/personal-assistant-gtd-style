import type {
  CreateConnectionRequest,
  CreateNodeRequest,
  NodeMetadata
} from '../../../graph-memory-core/mcp/src/types.js';
import type { MemoryGraph } from '../../../graph-memory-core/mcp/src/memoryGraph.js';

export interface TaskInput {
  title?: string;
  isComplete?: boolean;
  responsibleParty?: string;
}

export interface StateInput {
  title?: string;
  isTrue?: boolean;
  logic?: 'ANY' | 'ALL' | 'MANUAL' | 'IMMUTABLE';
}

export interface ContextInput {
  title?: string;
  isAvailable?: boolean;
}

export async function createTask(
  graph: MemoryGraph,
  input: TaskInput = {}
): Promise<NodeMetadata> {
  const request: CreateNodeRequest = {
    type: 'Task',
    content: input.title ?? 'Task',
    encoding: 'utf-8',
    format: 'text/plain',
    properties: {
      isComplete: input.isComplete ?? false,
      ...(input.responsibleParty ? { responsibleParty: input.responsibleParty } : {})
    }
  };

  const { node_id } = await graph.createNode(request);
  return graph.getNode({ node_id });
}

export async function createState(
  graph: MemoryGraph,
  input: StateInput = {}
): Promise<NodeMetadata> {
  const request: CreateNodeRequest = {
    type: 'State',
    content: input.title ?? 'State',
    encoding: 'utf-8',
    format: 'text/plain',
    properties: {
      isTrue: input.isTrue ?? false,
      logic: input.logic ?? 'ANY'
    }
  };

  const { node_id } = await graph.createNode(request);
  return graph.getNode({ node_id });
}

export async function createContextNode(
  graph: MemoryGraph,
  input: ContextInput = {}
): Promise<NodeMetadata> {
  const request: CreateNodeRequest = {
    type: 'Context',
    content: input.title ?? 'Context',
    encoding: 'utf-8',
    format: 'text/plain',
    properties: {
      isAvailable: input.isAvailable ?? true
    }
  };

  const { node_id } = await graph.createNode(request);
  return graph.getNode({ node_id });
}

export async function createDependsOnConnection(
  graph: MemoryGraph,
  fromNodeId: string,
  toNodeId: string
): Promise<string> {
  const request: CreateConnectionRequest = {
    type: 'DependsOn',
    from_node_id: fromNodeId,
    to_node_id: toNodeId
  };

  const { connection_id } = await graph.createConnection(request);
  return connection_id;
}

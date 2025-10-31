/**
 * Module: server
 * Purpose: Register MCP tools that delegate to the MemoryGraph domain service.
 * Created: 2025-10-31
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/graph-memory-core.md
 */

import type { MemoryGraph } from './memoryGraph.js';
import { z } from 'zod';
import type {
  AddConnectionTypeRequest,
  AddNodeTypeRequest,
  ConnectionMetadata,
  CreateConnectionRequest,
  CreateConnectionResult,
  CreateNodeRequest,
  CreateNodeResult,
  CreateOntologyRequest,
  DeleteConnectionRequest,
  DeleteNodeRequest,
  GetConnectionRequest,
  GetConnectedNodesRequest,
  GetConnectedNodesResult,
  GetNodeContentRequest,
  GetNodeContentResult,
  GetNodeRequest,
  GetOntologyResult,
  NodeMetadata,
  QueryConnectionsRequest,
  QueryConnectionsResult,
  QueryNodesRequest,
  QueryNodesResult,
  SearchContentRequest,
  SearchContentResult,
  UpdateConnectionRequest,
  UpdateNodeRequest,
  ValidateConnectionRequest,
  ValidateConnectionResult
} from './types.js';
import { GraphMemoryError } from './errors.js';

const propertyValueSchema = z.union([z.string(), z.number(), z.boolean()]);
const propertyMapSchema = z.record(propertyValueSchema);
const contentEncodingSchema = z.enum(['utf-8', 'base64']);
const directionSchema = z.enum(['out', 'in', 'both']);

const createNodeInputShape = {
  type: z.string(),
  content: z.string(),
  encoding: contentEncodingSchema,
  format: z.string(),
  properties: propertyMapSchema.optional()
};

const nodeIdShape = { node_id: z.string() };
const connectionIdShape = { connection_id: z.string() };

const updateNodeInputShape = {
  node_id: z.string(),
  properties: propertyMapSchema.optional(),
  content: z.string().optional(),
  encoding: contentEncodingSchema.optional(),
  format: z.string().optional()
};

const createConnectionInputShape = {
  type: z.string(),
  from_node_id: z.string(),
  to_node_id: z.string(),
  properties: propertyMapSchema.optional(),
  content: z.string().optional(),
  format: z.string().optional()
};

const updateConnectionInputShape = {
  connection_id: z.string(),
  properties: propertyMapSchema.optional(),
  content: z.string().optional(),
  format: z.string().optional()
};

const queryNodesInputShape = {
  type: z.string().optional(),
  properties: propertyMapSchema.optional()
};

const queryConnectionsInputShape = {
  from_node_id: z.string().optional(),
  to_node_id: z.string().optional(),
  type: z.string().optional(),
  properties: propertyMapSchema.optional()
};

const getConnectedNodesInputShape = {
  node_id: z.string(),
  connection_type: z.string().optional(),
  direction: directionSchema
};

const searchContentInputShape = {
  query: z.string(),
  node_type: z.string().optional(),
  limit: z.number().int().positive().optional()
};

const validateConnectionInputShape = {
  connection_type: z.string(),
  from_node_type: z.string(),
  to_node_type: z.string()
};

const createOntologyConnectionShape = {
  name: z.string(),
  from_types: z.array(z.string()).nonempty(),
  to_types: z.array(z.string()).nonempty(),
  required_properties: z.array(z.string()).optional()
};

const createOntologyInputShape = {
  node_types: z.array(z.string()).nonempty(),
  connection_types: z.array(z.object(createOntologyConnectionShape))
};

const addNodeTypeInputShape = { type_name: z.string() };

const addConnectionTypeInputShape = {
  type_name: z.string(),
  from_types: z.array(z.string()).nonempty(),
  to_types: z.array(z.string()).nonempty(),
  required_properties: z.array(z.string()).optional()
};

const emptyObjectShape: Record<string, never> = {};



/**
 * Definition passed to the MCP SDK's registration API.
 */
export interface ToolDefinition<TInput, TResult> {
  name: string;
  description: string;
  inputSchema: unknown;
  outputSchema?: unknown;
  handler: (input: TInput) => Promise<TResult>;
}

/**
 * Thin abstraction around the MCP SDK transport for registering tools.
 */
export interface ToolRegistrar {
  registerTool<TInput, TResult>(definition: ToolDefinition<TInput, TResult>): void;
}

/**
 * MCP server wrapper exposing the 18 graph memory operations.
 */
export class GraphMemoryMcpServer {
  constructor(private readonly graph: MemoryGraph) {}

  /**
   * Register every tool with the provided registrar.
   */
  registerTools(registrar: ToolRegistrar): void {
    const definitions: Array<ToolDefinition<any, any>> = [
      this.createCreateNodeTool(),
      this.createGetNodeTool(),
      this.createGetNodeContentTool(),
      this.createUpdateNodeTool(),
      this.createDeleteNodeTool(),
      this.createCreateConnectionTool(),
      this.createGetConnectionTool(),
      this.createUpdateConnectionTool(),
      this.createDeleteConnectionTool(),
      this.createQueryNodesTool(),
      this.createQueryConnectionsTool(),
      this.createGetConnectedNodesTool(),
      this.createSearchContentTool(),
      this.createValidateConnectionTool(),
      this.createCreateOntologyTool(),
      this.createAddNodeTypeTool(),
      this.createAddConnectionTypeTool(),
      this.createGetOntologyTool()
    ];

    for (const definition of definitions) {
      registrar.registerTool(definition);
    }
  }

  private createCreateNodeTool(): ToolDefinition<CreateNodeRequest, CreateNodeResult> {
    return {
      name: 'create_node',
      description: 'Create a new typed node with content and optional properties.',
      inputSchema: createNodeInputShape,
      handler: async (input: CreateNodeRequest) => {
        try {
          return await this.graph.createNode(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createGetNodeTool(): ToolDefinition<GetNodeRequest, NodeMetadata> {
    return {
      name: 'get_node',
      description: 'Retrieve metadata for a node without loading its content.',
      inputSchema: nodeIdShape,
      handler: async (input: GetNodeRequest) => {
        try {
          return await this.graph.getNode(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createGetNodeContentTool(): ToolDefinition<GetNodeContentRequest, GetNodeContentResult> {
    return {
      name: 'get_node_content',
      description: 'Read the stored content for the specified node.',
      inputSchema: nodeIdShape,
      handler: async (input: GetNodeContentRequest) => {
        try {
          return await this.graph.getNodeContent(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createUpdateNodeTool(): ToolDefinition<UpdateNodeRequest, void> {
    return {
      name: 'update_node',
      description: 'Update node properties and/or content.',
      inputSchema: updateNodeInputShape,
      handler: async (input: UpdateNodeRequest) => {
        try {
          await this.graph.updateNode(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createDeleteNodeTool(): ToolDefinition<DeleteNodeRequest, void> {
    return {
      name: 'delete_node',
      description: 'Delete a node and cascade delete its connections.',
      inputSchema: nodeIdShape,
      handler: async (input: DeleteNodeRequest) => {
        try {
          await this.graph.deleteNode(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createCreateConnectionTool(): ToolDefinition<CreateConnectionRequest, CreateConnectionResult> {
    return {
      name: 'create_connection',
      description: 'Create a new typed connection between two nodes.',
      inputSchema: createConnectionInputShape,
      handler: async (input: CreateConnectionRequest) => {
        try {
          return await this.graph.createConnection(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createGetConnectionTool(): ToolDefinition<GetConnectionRequest, ConnectionMetadata> {
    return {
      name: 'get_connection',
      description: 'Retrieve metadata for a connection.',
      inputSchema: connectionIdShape,
      handler: async (input: GetConnectionRequest) => {
        try {
          return await this.graph.getConnection(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createUpdateConnectionTool(): ToolDefinition<UpdateConnectionRequest, void> {
    return {
      name: 'update_connection',
      description: 'Update connection properties and optional content.',
      inputSchema: updateConnectionInputShape,
      handler: async (input: UpdateConnectionRequest) => {
        try {
          await this.graph.updateConnection(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createDeleteConnectionTool(): ToolDefinition<DeleteConnectionRequest, void> {
    return {
      name: 'delete_connection',
      description: 'Delete a connection without affecting nodes.',
      inputSchema: connectionIdShape,
      handler: async (input: DeleteConnectionRequest) => {
        try {
          await this.graph.deleteConnection(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createQueryNodesTool(): ToolDefinition<QueryNodesRequest, QueryNodesResult> {
    return {
      name: 'query_nodes',
      description: 'Query nodes by type and property filters (AND semantics).',
      inputSchema: queryNodesInputShape,
      handler: async (input: QueryNodesRequest) => {
        try {
          return await this.graph.queryNodes(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createQueryConnectionsTool(): ToolDefinition<QueryConnectionsRequest, QueryConnectionsResult> {
    return {
      name: 'query_connections',
      description: 'Query connections by endpoints, type, and properties.',
      inputSchema: queryConnectionsInputShape,
      handler: async (input: QueryConnectionsRequest) => {
        try {
          return await this.graph.queryConnections(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createGetConnectedNodesTool(): ToolDefinition<GetConnectedNodesRequest, GetConnectedNodesResult> {
    return {
      name: 'get_connected_nodes',
      description: 'Traverse connections to retrieve adjacent node identifiers.',
      inputSchema: getConnectedNodesInputShape,
      handler: async (input: GetConnectedNodesRequest) => {
        try {
          return await this.graph.getConnectedNodes(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createSearchContentTool(): ToolDefinition<SearchContentRequest, SearchContentResult> {
    return {
      name: 'search_content',
      description: 'Search node content for substring matches (case-insensitive).',
      inputSchema: searchContentInputShape,
      handler: async (input: SearchContentRequest) => {
        try {
          return await this.graph.searchContent(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createValidateConnectionTool(): ToolDefinition<ValidateConnectionRequest, ValidateConnectionResult> {
    return {
      name: 'validate_connection',
      description: 'Validate whether a connection type is allowed between node types.',
      inputSchema: validateConnectionInputShape,
      handler: async (input: ValidateConnectionRequest) => {
        try {
          return await this.graph.validateConnection(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createCreateOntologyTool(): ToolDefinition<CreateOntologyRequest, void> {
    return {
      name: 'create_ontology',
      description: 'Initialize the ontology with initial node and connection types.',
      inputSchema: createOntologyInputShape,
      handler: async (input: CreateOntologyRequest) => {
        try {
          await this.graph.createOntology(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createAddNodeTypeTool(): ToolDefinition<AddNodeTypeRequest, void> {
    return {
      name: 'add_node_type',
      description: 'Append a new node type to the ontology.',
      inputSchema: addNodeTypeInputShape,
      handler: async (input: AddNodeTypeRequest) => {
        try {
          await this.graph.addNodeType(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createAddConnectionTypeTool(): ToolDefinition<AddConnectionTypeRequest, void> {
    return {
      name: 'add_connection_type',
      description: 'Append a new connection type to the ontology.',
      inputSchema: addConnectionTypeInputShape,
      handler: async (input: AddConnectionTypeRequest) => {
        try {
          await this.graph.addConnectionType(input);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createGetOntologyTool(): ToolDefinition<Record<string, never>, GetOntologyResult> {
    return {
      name: 'get_ontology',
      description: 'Retrieve the current ontology definition.',
      inputSchema: emptyObjectShape,
      handler: async (_input: Record<string, never>) => {
        try {
          return await this.graph.getOntology();
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  /**
   * Normalize thrown values to Error instances so the MCP SDK can serialize them.
   */
  private mapError(error: unknown): Error {
    if (error instanceof GraphMemoryError) {
      return error;
    }
    if (error instanceof Error) {
      return error;
    }
    return new Error(String(error));
  }
}

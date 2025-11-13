/**
 * Module: server
 * Purpose: Register MCP tools that delegate to the MemoryGraph domain service.
 * Created: 2025-10-31
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/graph-memory-core.md
 */

import type { MemoryGraph } from './memoryGraph.js';
import { z } from 'zod';
import * as fs from 'fs';
import * as path from 'path';
import type {
  AddConnectionTypeRequest,
  AddNodeTypeRequest,
  ConnectionMetadata,
  CreateConnectionRequest,
  CreateConnectionResult,
  CreateNodeRequest,
  CreateNodeResult,
  CreateOntologyRequest,
  EnsureSingletonNodeRequest,
  EnsureSingletonNodeResult,
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

const ensureSingletonNodeInputShape = {
  type: z.string(),
  content: z.string().optional(),
  encoding: contentEncodingSchema.optional(),
  format: z.string().optional(),
  properties: propertyMapSchema.optional(),
  on_multiple: z.enum(['oldest', 'newest']).optional()
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
 * MCP server wrapper exposing the 19 graph memory operations.
 */
export class GraphMemoryMcpServer {
  private logFile: string | null = null;
  private logStream: fs.WriteStream | null = null;

  constructor(private readonly graph: MemoryGraph) {
    // Initialize logging if MCP_CALL_LOG environment variable is set
    const logPath = process.env.MCP_CALL_LOG;
    if (logPath) {
      this.logFile = logPath;
      try {
        // Ensure directory exists
        const dir = path.dirname(logPath);
        if (!fs.existsSync(dir)) {
          fs.mkdirSync(dir, { recursive: true });
        }
        // Open log file in append mode
        this.logStream = fs.createWriteStream(logPath, { flags: 'a' });
        this.logToolCall('SERVER_START', {});
      } catch (error) {
        console.error(`Failed to initialize MCP call logging: ${error}`);
      }
    }
  }

  private logToolCall(toolName: string, input: any, result?: any, error?: any): void {
    if (!this.logStream) return;

    const logEntry = {
      timestamp: new Date().toISOString(),
      tool: toolName,
      input: input,
      ...(result !== undefined && { result }),
      ...(error !== undefined && { error: String(error) })
    };

    this.logStream.write(JSON.stringify(logEntry) + '\n');
  }

  /**
   * Wrap a handler function with logging.
   */
  private wrapHandlerWithLogging<TInput, TResult>(
    toolName: string,
    handler: (input: TInput) => Promise<TResult>
  ): (input: TInput) => Promise<TResult> {
    return async (input: TInput) => {
      try {
        const result = await handler(input);
        this.logToolCall(toolName, input, result);
        return result;
      } catch (error) {
        this.logToolCall(toolName, input, undefined, error);
        throw error;
      }
    };
  }

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
      this.createGetOntologyTool(),
      this.createEnsureSingletonNodeTool()
    ];

    for (const definition of definitions) {
      registrar.registerTool(definition);
    }
  }

  private createCreateNodeTool(): ToolDefinition<CreateNodeRequest, CreateNodeResult> {
    return {
      name: 'create_node',
      description: 'Create a GTD Task, Context, State, or UNSPECIFIED node in the graph. Use for capturing tasks ("Call dentist"), defining contexts (@office, @phone), or tracking states. This is how you persist GTD items.\n\nProperty usage:\n- Task: {isComplete: boolean} for task status. For delegated tasks, use {responsibleParty: "person-name"} NOT assignedTo. Example: {type: "Task", content: "Logo design", properties: {isComplete: false, responsibleParty: "Jane"}}\n- Context: {isTrue: boolean} for availability. Example: {type: "Context", content: "atOffice", properties: {isTrue: false}}\n- State: {isTrue: boolean, logic: "ANY"|"ALL"} for condition tracking. Example: {type: "State", content: "Weather is good", properties: {isTrue: true, logic: "ANY"}}',
      inputSchema: createNodeInputShape,
      handler: this.wrapHandlerWithLogging('create_node', async (input: CreateNodeRequest) => {
        try {
          return await this.graph.createNode(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createGetNodeTool(): ToolDefinition<GetNodeRequest, NodeMetadata> {
    return {
      name: 'get_node',
      description: 'Retrieve metadata for a node without loading its content.',
      inputSchema: nodeIdShape,
      handler: this.wrapHandlerWithLogging('get_node', async (input: GetNodeRequest) => {
        try {
          return await this.graph.getNode(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createGetNodeContentTool(): ToolDefinition<GetNodeContentRequest, GetNodeContentResult> {
    return {
      name: 'get_node_content',
      description: 'Read the stored content for the specified node.',
      inputSchema: nodeIdShape,
      handler: this.wrapHandlerWithLogging('get_node_content', async (input: GetNodeContentRequest) => {
        try {
          return await this.graph.getNodeContent(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createUpdateNodeTool(): ToolDefinition<UpdateNodeRequest, void> {
    return {
      name: 'update_node',
      description: 'Update a GTD Task, Context, or State. Use when user marks tasks complete (isComplete: true), adds notes, changes context availability (isTrue: true), or updates properties. ALWAYS search for existing node first, never create new.',
      inputSchema: updateNodeInputShape,
      handler: this.wrapHandlerWithLogging('update_node', async (input: UpdateNodeRequest) => {
        try {
          await this.graph.updateNode(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createDeleteNodeTool(): ToolDefinition<DeleteNodeRequest, void> {
    return {
      name: 'delete_node',
      description: 'Delete a node and cascade delete its connections.',
      inputSchema: nodeIdShape,
      handler: this.wrapHandlerWithLogging('delete_node', async (input: DeleteNodeRequest) => {
        try {
          await this.graph.deleteNode(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createCreateConnectionTool(): ToolDefinition<CreateConnectionRequest, CreateConnectionResult> {
    return {
      name: 'create_connection',
      description: 'Create a DependsOn connection in the GTD graph. Use to link Task→Task (sequential dependency), Task→Context (@office requirement), Task→State (condition), or Task→UNSPECIFIED (undefined next step). Direction: from depends on to.',
      inputSchema: createConnectionInputShape,
      handler: this.wrapHandlerWithLogging('create_connection', async (input: CreateConnectionRequest) => {
        try {
          return await this.graph.createConnection(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createGetConnectionTool(): ToolDefinition<GetConnectionRequest, ConnectionMetadata> {
    return {
      name: 'get_connection',
      description: 'Retrieve metadata for a connection.',
      inputSchema: connectionIdShape,
      handler: this.wrapHandlerWithLogging('get_connection', async (input: GetConnectionRequest) => {
        try {
          return await this.graph.getConnection(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createUpdateConnectionTool(): ToolDefinition<UpdateConnectionRequest, void> {
    return {
      name: 'update_connection',
      description: 'Update connection properties and optional content.',
      inputSchema: updateConnectionInputShape,
      handler: this.wrapHandlerWithLogging('update_connection', async (input: UpdateConnectionRequest) => {
        try {
          await this.graph.updateConnection(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createDeleteConnectionTool(): ToolDefinition<DeleteConnectionRequest, void> {
    return {
      name: 'delete_connection',
      description: 'Delete a connection without affecting nodes.',
      inputSchema: connectionIdShape,
      handler: this.wrapHandlerWithLogging('delete_connection', async (input: DeleteConnectionRequest) => {
        try {
          await this.graph.deleteConnection(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createQueryNodesTool(): ToolDefinition<QueryNodesRequest, QueryNodesResult> {
    return {
      name: 'query_nodes',
      description: 'Query the GTD system for Tasks, Contexts, or States. CRITICAL: Use this BEFORE responding to check what exists. Examples: query_nodes({type:"Task",properties:{isComplete:false}}) for incomplete tasks, query_nodes({type:"Context"}) for all contexts. Never assume empty system without querying.',
      inputSchema: queryNodesInputShape,
      handler: this.wrapHandlerWithLogging('query_nodes', async (input: QueryNodesRequest) => {
        try {
          return await this.graph.queryNodes(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createQueryConnectionsTool(): ToolDefinition<QueryConnectionsRequest, QueryConnectionsResult> {
    return {
      name: 'query_connections',
      description: 'Query DependsOn connections in the GTD graph. Use query_connections({from_node_id: task_id}) to check if a Task is a Project (has outgoing dependencies). Use to find dependency relationships between Tasks.',
      inputSchema: queryConnectionsInputShape,
      handler: this.wrapHandlerWithLogging('query_connections', async (input: QueryConnectionsRequest) => {
        try {
          return await this.graph.queryConnections(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createGetConnectedNodesTool(): ToolDefinition<GetConnectedNodesRequest, GetConnectedNodesResult> {
    return {
      name: 'get_connected_nodes',
      description: 'Get nodes connected to a Task via DependsOn connections. Use direction:"out" to get what this Task depends on (blockers). Use direction:"in" to get what depends on this Task (dependents). Essential for determining Next Actions.',
      inputSchema: getConnectedNodesInputShape,
      handler: this.wrapHandlerWithLogging('get_connected_nodes', async (input: GetConnectedNodesRequest) => {
        try {
          return await this.graph.getConnectedNodes(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createSearchContentTool(): ToolDefinition<SearchContentRequest, SearchContentResult> {
    return {
      name: 'search_content',
      description: 'Search GTD items by text content (case-insensitive). CRITICAL: Use this to find tasks before updating/deleting ("board presentation", "vendor contract"). Also use to check for duplicates before creating. This is your primary search tool.',
      inputSchema: searchContentInputShape,
      handler: this.wrapHandlerWithLogging('search_content', async (input: SearchContentRequest) => {
        try {
          return await this.graph.searchContent(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createValidateConnectionTool(): ToolDefinition<ValidateConnectionRequest, ValidateConnectionResult> {
    return {
      name: 'validate_connection',
      description: 'Validate whether a connection type is allowed between node types.',
      inputSchema: validateConnectionInputShape,
      handler: this.wrapHandlerWithLogging('validate_connection', async (input: ValidateConnectionRequest) => {
        try {
          return await this.graph.validateConnection(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createCreateOntologyTool(): ToolDefinition<CreateOntologyRequest, void> {
    return {
      name: 'create_ontology',
      description: 'Initialize the ontology with initial node and connection types.',
      inputSchema: createOntologyInputShape,
      handler: this.wrapHandlerWithLogging('create_ontology', async (input: CreateOntologyRequest) => {
        try {
          await this.graph.createOntology(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createAddNodeTypeTool(): ToolDefinition<AddNodeTypeRequest, void> {
    return {
      name: 'add_node_type',
      description: 'Append a new node type to the ontology.',
      inputSchema: addNodeTypeInputShape,
      handler: this.wrapHandlerWithLogging('add_node_type', async (input: AddNodeTypeRequest) => {
        try {
          await this.graph.addNodeType(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createAddConnectionTypeTool(): ToolDefinition<AddConnectionTypeRequest, void> {
    return {
      name: 'add_connection_type',
      description: 'Append a new connection type to the ontology.',
      inputSchema: addConnectionTypeInputShape,
      handler: this.wrapHandlerWithLogging('add_connection_type', async (input: AddConnectionTypeRequest) => {
        try {
          await this.graph.addConnectionType(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createGetOntologyTool(): ToolDefinition<Record<string, never>, GetOntologyResult> {
    return {
      name: 'get_ontology',
      description: 'Retrieve the current ontology definition.',
      inputSchema: emptyObjectShape,
      handler: this.wrapHandlerWithLogging('get_ontology', async (_input: Record<string, never>) => {
        try {
          return await this.graph.getOntology();
        } catch (error) {
          throw this.mapError(error);
        }
      })
    };
  }

  private createEnsureSingletonNodeTool(): ToolDefinition<EnsureSingletonNodeRequest, EnsureSingletonNodeResult> {
    return {
      name: 'ensure_singleton_node',
      description: 'Get or create the canonical singleton node for a type.',
      inputSchema: ensureSingletonNodeInputShape,
      handler: this.wrapHandlerWithLogging('ensure_singleton_node', async (input: EnsureSingletonNodeRequest) => {
        try {
          return await this.graph.ensureSingletonNode(input);
        } catch (error) {
          throw this.mapError(error);
        }
      })
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

/**
 * Module: index
 * Purpose: Wire configuration, storage adapter, and MCP server bootstrap.
 * Created: 2025-10-31
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/graph-memory-core.md
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import type { ToolDefinition, ToolRegistrar } from './server.js';
import type { GetNodeContentResult, GraphMemoryServerConfig } from './types.js';
import { FileStorageAdapter } from './storageGateway.js';
import { MemoryGraph } from './memoryGraph.js';
import { GraphMemoryMcpServer } from './server.js';

/**
 * Registrar bridging domain tool definitions with the MCP SDK implementation.
 */
class McpSdkToolRegistrar implements ToolRegistrar {
  constructor(private readonly server: McpServer) {}

  registerTool<TInput, TResult>(definition: ToolDefinition<TInput, TResult>): void {
    const hasSchema = definition.inputSchema !== undefined;

    this.server.registerTool(
      definition.name,
      {
        description: definition.description,
        inputSchema: (hasSchema ? definition.inputSchema : undefined) as any,
        outputSchema: undefined
      } as any,
      (async (argsOrExtra: unknown, maybeExtra?: unknown) => {
        const extra = hasSchema ? maybeExtra : argsOrExtra;
        const args = hasSchema
          ? (argsOrExtra as TInput)
          : (((extra as { request?: { params?: { arguments?: unknown; name?: string } } })?.request?.params
                ?.arguments ?? {}) as TInput);
        const result = await definition.handler(args);
        return this.toToolResponse(result, definition.name) as any;
      }) as any
    );
  }

  private toToolResponse<TResult>(result: TResult, toolName: string) {
    if (result === undefined) {
      return {
        content: [
          {
            type: 'text',
            text: `${toolName} completed successfully`
          }
        ]
      };
    }

    if (isNodeContentResult(result)) {
      return {
        content: [
          {
            type: 'text',
            text: result.content
          }
        ],
        structuredContent: result
      };
    }

    if (typeof result === 'string') {
      return {
        content: [
          {
            type: 'text',
            text: result
          }
        ]
      };
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ],
      structuredContent: result
    };
  }
}

function isNodeContentResult(value: unknown): value is GetNodeContentResult {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as GetNodeContentResult).content === 'string'
  );
}

/**
 * Bootstrap the MCP server: load graph state, register tools, and connect transport.
 */
export async function bootstrap(config: GraphMemoryServerConfig): Promise<void> {
  const storage = new FileStorageAdapter(config.basePath);
  const memoryGraph = await MemoryGraph.initialize(config, storage);

  const mcpServer = new McpServer({
    name: 'graph-memory-core',
    version: '0.1.0'
  });

  const domainServer = new GraphMemoryMcpServer(memoryGraph);
  domainServer.registerTools(new McpSdkToolRegistrar(mcpServer));

  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
}

/**
 * Entry point invoked when the Node.js process starts.
 */
export async function main(): Promise<void> {
  try {
    const basePath = process.env.BASE_PATH;
    if (!basePath) {
      throw new Error('BASE_PATH environment variable must be provided');
    }

    await bootstrap({ basePath });
  } catch (error) {
    console.error('Graph Memory MCP server failed to start:', error);
    process.exitCode = 1;
  }
}

void main();

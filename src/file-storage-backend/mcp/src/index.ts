/**
 * Module: index
 * Purpose: Entrypoint wiring configuration, storage, and MCP server bootstrap.
 * Created: 2025-10-30
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/file-storage-backend.md
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import type { ToolDefinition, ToolRegistrar } from './server.js';
import type { FileStorageServerConfig, FileContent, StorageErrorPayload } from './types.js';
import { LocalFileStorage } from './localFileStorage.js';
import { FileStorageMcpServer } from './server.js';

/**
 * Tool registrar that bridges the domain-specific server to the MCP SDK implementation.
 */
class McpSdkToolRegistrar implements ToolRegistrar {
  constructor(private readonly server: McpServer) {}

  registerTool<TInput, TResult>(definition: ToolDefinition<TInput, TResult>): void {
    this.server.registerTool(
      definition.name,
      {
        description: definition.description
      },
      async (args: TInput) => {
        try {
          const result = await definition.handler(args);
          return this.toToolResponse(result, definition.name);
        } catch (error) {
          if (isStorageErrorPayload(error)) {
            return {
              content: [
                {
                  type: 'text',
                  text: JSON.stringify(error)
                }
              ],
              isError: true,
              structuredContent: error
            };
          }
          throw error;
        }
      }
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

    if (isFileContent(result)) {
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

function isStorageErrorPayload(value: unknown): value is StorageErrorPayload {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as StorageErrorPayload).code === 'string' &&
    typeof (value as StorageErrorPayload).message === 'string'
  );
}

function isFileContent(value: unknown): value is FileContent {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const candidate = value as Partial<FileContent>;

  if (candidate.type === 'file') {
    return (
      typeof candidate.content === 'string' &&
      (candidate.encoding === 'utf-8' || candidate.encoding === 'base64') &&
      typeof candidate.size === 'number'
    );
  }

  if (candidate.type === 'directory') {
    return Array.isArray(candidate.entries);
  }

  return false;
}

/**
 * Read runtime configuration and instantiate the MCP server components.
 */
export async function bootstrap(config: FileStorageServerConfig): Promise<void> {
  const storage = new LocalFileStorage(config);
  const domainServer = new FileStorageMcpServer(storage);

  const mcpServer = new McpServer({
    name: 'file-storage-backend',
    version: '0.1.0'
  });

  domainServer.registerTools(new McpSdkToolRegistrar(mcpServer));

  const transport = new StdioServerTransport();
  await mcpServer.connect(transport);
}

/**
 * Default executable path invoked by Node.js process start.
 */
export async function main(): Promise<void> {
  try {
    const basePath = process.env.BASE_PATH;
    if (!basePath) {
      throw new Error('BASE_PATH environment variable must be provided');
    }

    await bootstrap({ basePath });
  } catch (error) {
    console.error('File Storage MCP server failed to start:', error);
    process.exitCode = 1;
  }
}

void main();

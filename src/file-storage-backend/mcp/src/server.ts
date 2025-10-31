/**
 * Module: server
 * Purpose: Define MCP server scaffolding for file storage tool registration.
 * Created: 2025-10-30
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/file-storage-backend.md
 */

import type { FileStorage } from './fileStorage.js';
import {
  type CreateRequest,
  type DeleteRequest,
  type FileContent,
  type InsertRequest,
  type RenameRequest,
  type StorageErrorPayload,
  type StrReplaceRequest,
  type ViewRequest
} from './types.js';
import {
  DiskFullError,
  FileExistsError,
  FileNotFoundError,
  PathSecurityError,
  PermissionDeniedError,
  StorageError
} from './errors.js';

/**
 * Definition passed to whatever MCP SDK layer registers tools with Claude Code.
 */
export interface ToolDefinition<TInput, TResult> {
  /**
   * Unique identifier for the tool that surfaces in Claude Code.
   */
  name: string;
  /**
   * Short human-readable summary shown in tool listings.
   */
  description: string;
  /**
   * JSON schema describing accepted input parameters.
   */
  inputSchema: unknown;
  /**
   * Optional JSON schema describing output payloads.
   */
  outputSchema?: unknown;
  /**
   * Handler invoked when the tool is executed.
   */
  handler: (input: TInput) => Promise<TResult>;
}

/**
 * Abstraction over the MCP SDK registration API.
 */
export interface ToolRegistrar {
  /**
   * Register a tool with the underlying MCP transport layer.
   */
  registerTool<TInput, TResult>(definition: ToolDefinition<TInput, TResult>): void;
}

/**
 * MCP server wrapper that binds tool invocations to storage operations.
 */
export class FileStorageMcpServer {
  constructor(private readonly storage: FileStorage) {}

  /**
   * Register all six MCP tools with the provided registrar.
   */
  registerTools(registrar: ToolRegistrar): void {
    const tools: Array<ToolDefinition<unknown, unknown>> = [
      this.createViewToolDefinition(),
      this.createCreateToolDefinition(),
      this.createStrReplaceToolDefinition(),
      this.createInsertToolDefinition(),
      this.createDeleteToolDefinition(),
      this.createRenameToolDefinition()
    ];

    for (const tool of tools) {
      registrar.registerTool(tool);
    }
  }

  private createViewToolDefinition(): ToolDefinition<ViewRequest, FileContent> {
    return {
      name: 'view',
      description: 'View file contents or list directory entries inside the storage base path.',
      inputSchema: {
        type: 'object',
        properties: {
          path: { type: 'string', description: 'Relative path constrained to the configured base directory.' }
        },
        required: ['path'],
        additionalProperties: false
      },
      outputSchema: {
        oneOf: [
          {
            type: 'object',
            required: ['type', 'content', 'encoding', 'size'],
            additionalProperties: false,
            properties: {
              type: { const: 'file' },
              content: { type: 'string' },
              encoding: { enum: ['utf-8', 'base64'] },
              size: { type: 'integer', minimum: 0 }
            }
          },
          {
            type: 'object',
            required: ['type', 'entries'],
            additionalProperties: false,
            properties: {
              type: { const: 'directory' },
              entries: { type: 'array', items: { type: 'string' } }
            }
          }
        ]
      },
      handler: async (input: ViewRequest) => {
        try {
          return await this.storage.view(input.path);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createCreateToolDefinition(): ToolDefinition<CreateRequest, void> {
    return {
      name: 'create',
      description: 'Create a new file with the provided content.',
      inputSchema: {
        type: 'object',
        properties: {
          path: { type: 'string' },
          content: { type: 'string' },
          encoding: { enum: ['utf-8', 'base64'] }
        },
        required: ['path', 'content', 'encoding'],
        additionalProperties: false
      },
      handler: async (input: CreateRequest) => {
        try {
          await this.storage.create(input.path, input.content, input.encoding);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createStrReplaceToolDefinition(): ToolDefinition<StrReplaceRequest, void> {
    return {
      name: 'str_replace',
      description: 'Replace a unique string within a UTF-8 text file.',
      inputSchema: {
        type: 'object',
        properties: {
          path: { type: 'string' },
          old_str: { type: 'string' },
          new_str: { type: 'string' }
        },
        required: ['path', 'old_str', 'new_str'],
        additionalProperties: false
      },
      handler: async (input: StrReplaceRequest) => {
        try {
          await this.storage.str_replace(input.path, input.old_str, input.new_str);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createInsertToolDefinition(): ToolDefinition<InsertRequest, void> {
    return {
      name: 'insert',
      description: 'Insert text at a one-indexed line in a UTF-8 file.',
      inputSchema: {
        type: 'object',
        properties: {
          path: { type: 'string' },
          insert_line: { type: 'integer', minimum: 1 },
          new_str: { type: 'string' }
        },
        required: ['path', 'insert_line', 'new_str'],
        additionalProperties: false
      },
      handler: async (input: InsertRequest) => {
        try {
          await this.storage.insert(input.path, input.insert_line, input.new_str);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createDeleteToolDefinition(): ToolDefinition<DeleteRequest, void> {
    return {
      name: 'delete',
      description: 'Delete a file or an empty directory.',
      inputSchema: {
        type: 'object',
        properties: {
          path: { type: 'string' }
        },
        required: ['path'],
        additionalProperties: false
      },
      handler: async (input: DeleteRequest) => {
        try {
          await this.storage.delete(input.path);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  private createRenameToolDefinition(): ToolDefinition<RenameRequest, void> {
    return {
      name: 'rename',
      description: 'Rename or move a file or directory within the storage base path.',
      inputSchema: {
        type: 'object',
        properties: {
          old_path: { type: 'string' },
          new_path: { type: 'string' }
        },
        required: ['old_path', 'new_path'],
        additionalProperties: false
      },
      handler: async (input: RenameRequest) => {
        try {
          await this.storage.rename(input.old_path, input.new_path);
        } catch (error) {
          throw this.mapError(error);
        }
      }
    };
  }

  /**
   * Map thrown errors into MCP-compliant payloads.
   */
  private mapError(error: unknown): StorageErrorPayload {
    if (error instanceof StorageError) {
      return error.toPayload();
    }

    const nodeError = error as NodeJS.ErrnoException;
    if (nodeError && typeof nodeError.code === 'string') {
      switch (nodeError.code) {
        case 'ENOENT':
          return new FileNotFoundError(nodeError.path ?? '').toPayload();
        case 'EEXIST':
          return new FileExistsError(nodeError.path ?? '').toPayload();
        case 'EACCES':
        case 'EPERM':
          return new PermissionDeniedError(nodeError.path ?? '').toPayload();
        case 'ENOSPC':
          return new DiskFullError(nodeError.path ?? undefined).toPayload();
        case 'EINVAL':
          return new PathSecurityError(nodeError.path ?? '').toPayload();
      }
    }

    throw error;
  }
}

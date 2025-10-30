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
import { NotImplementedError, StorageError } from './errors.js';

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
    throw new NotImplementedError(
      'FileStorageMcpServer.createViewToolDefinition must call storage.view(input.path). See specs/todo/file-storage-backend.md'
    );
  }

  private createCreateToolDefinition(): ToolDefinition<CreateRequest, void> {
    throw new NotImplementedError(
      'FileStorageMcpServer.createCreateToolDefinition must call storage.create(input.path, input.content, input.encoding). See specs/todo/file-storage-backend.md'
    );
  }

  private createStrReplaceToolDefinition(): ToolDefinition<StrReplaceRequest, void> {
    throw new NotImplementedError(
      'FileStorageMcpServer.createStrReplaceToolDefinition must call storage.str_replace(input.path, input.old_str, input.new_str). See specs/todo/file-storage-backend.md'
    );
  }

  private createInsertToolDefinition(): ToolDefinition<InsertRequest, void> {
    throw new NotImplementedError(
      'FileStorageMcpServer.createInsertToolDefinition must call storage.insert(input.path, input.insert_line, input.new_str). See specs/todo/file-storage-backend.md'
    );
  }

  private createDeleteToolDefinition(): ToolDefinition<DeleteRequest, void> {
    throw new NotImplementedError(
      'FileStorageMcpServer.createDeleteToolDefinition must call storage.delete(input.path). See specs/todo/file-storage-backend.md'
    );
  }

  private createRenameToolDefinition(): ToolDefinition<RenameRequest, void> {
    throw new NotImplementedError(
      'FileStorageMcpServer.createRenameToolDefinition must call storage.rename(input.old_path, input.new_path). See specs/todo/file-storage-backend.md'
    );
  }

  /**
   * Map thrown errors into MCP-compliant payloads.
   */
  private mapError(error: unknown): StorageErrorPayload {
    throw new NotImplementedError(
      'FileStorageMcpServer.mapError is not implemented. See specs/todo/file-storage-backend.md'
    );
  }
}

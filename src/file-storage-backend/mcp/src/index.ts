/**
 * Module: index
 * Purpose: Entrypoint wiring configuration, storage, and MCP server bootstrap.
 * Created: 2025-10-30
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/file-storage-backend.md
 */

import type { FileStorageServerConfig } from './types.js';
import { LocalFileStorage } from './localFileStorage.js';
import { FileStorageMcpServer } from './server.js';
import { NotImplementedError } from './errors.js';

/**
 * Read runtime configuration and instantiate the MCP server components.
 */
export async function bootstrap(config: FileStorageServerConfig): Promise<void> {
  const storage = new LocalFileStorage(config);
  const server = new FileStorageMcpServer(storage);

  throw new NotImplementedError(
    'bootstrap must integrate with the MCP SDK to start the server. See specs/todo/file-storage-backend.md'
  );
}

/**
 * Default executable path invoked by Node.js process start.
 */
export async function main(): Promise<void> {
  throw new NotImplementedError(
    'main must load configuration (e.g., from env) and call bootstrap. See specs/todo/file-storage-backend.md'
  );
}

void main();

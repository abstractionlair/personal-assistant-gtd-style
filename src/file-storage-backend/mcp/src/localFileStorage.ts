/**
 * Module: localFileStorage
 * Purpose: Provide filesystem-backed storage implementation with stubbed logic.
 * Created: 2025-10-30
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/file-storage-backend.md
 */

import type { FileStorage } from './fileStorage.js';
import type { FileContent, FileEncoding, FileStorageServerConfig } from './types.js';
import { NotImplementedError } from './errors.js';

/**
 * Local filesystem implementation that enforces containment within `basePath`.
 *
 * The constructor accepts configuration described in the specification and all
 * methods defer to helper routines (to be implemented) that guarantee path security,
 * atomic writes, and encoding validation.
 */
export class LocalFileStorage implements FileStorage {
  /**
   * Filesystem root that bounds every operation.
   */
  private readonly basePath: string;

  constructor(config: FileStorageServerConfig) {
    this.basePath = config.basePath;
  }

  /**
   * Resolve the request and return file contents or directory entries.
   */
  async view(path: string): Promise<FileContent> {
    throw new NotImplementedError(
      'LocalFileStorage.view is not implemented. See specs/todo/file-storage-backend.md'
    );
  }

  /**
   * Create a new file populated with caller-provided content.
   */
  async create(path: string, content: string, encoding: FileEncoding): Promise<void> {
    throw new NotImplementedError(
      'LocalFileStorage.create is not implemented. See specs/todo/file-storage-backend.md'
    );
  }

  /**
   * Replace a unique string within a text file atomically.
   */
  async str_replace(path: string, old_str: string, new_str: string): Promise<void> {
    throw new NotImplementedError(
      'LocalFileStorage.str_replace is not implemented. See specs/todo/file-storage-backend.md'
    );
  }

  /**
   * Insert new text at a one-indexed line position.
   */
  async insert(path: string, insert_line: number, new_str: string): Promise<void> {
    throw new NotImplementedError(
      'LocalFileStorage.insert is not implemented. See specs/todo/file-storage-backend.md'
    );
  }

  /**
   * Remove a file or an empty directory.
   */
  async delete(path: string): Promise<void> {
    throw new NotImplementedError(
      'LocalFileStorage.delete is not implemented. See specs/todo/file-storage-backend.md'
    );
  }

  /**
   * Move or rename a file/directory within the base path.
   */
  async rename(old_path: string, new_path: string): Promise<void> {
    throw new NotImplementedError(
      'LocalFileStorage.rename is not implemented. See specs/todo/file-storage-backend.md'
    );
  }
}

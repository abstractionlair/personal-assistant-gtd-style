/**
 * Module: errors
 * Purpose: Define error hierarchy and helpers for MCP-compliant responses.
 * Created: 2025-10-30
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/file-storage-backend.md
 */

import type { StorageErrorCode, StorageErrorPayload } from './types.js';

/**
 * Base error carrying MCP-aligned error metadata.
 */
export class StorageError extends Error {
  /**
   * Machine-readable code that describes the failure condition.
   */
  public readonly code: StorageErrorCode;

  /**
   * Optional filesystem path associated with the failure.
   */
  public readonly path?: string;

  constructor(code: StorageErrorCode, message: string, path?: string) {
    super(message);
    this.code = code;
    this.path = path;
  }

  /**
   * Convert the error instance into an MCP error payload.
   */
  toPayload(): StorageErrorPayload {
    return {
      code: this.code,
      message: this.message,
      ...(this.path ? { path: this.path } : {})
    };
  }
}

export class FileNotFoundError extends StorageError {
  constructor(path: string) {
    super('file_not_found', `File not found: ${path}`, path);
  }
}

export class FileExistsError extends StorageError {
  constructor(path: string) {
    super('file_exists', `File already exists: ${path}`, path);
  }
}

export class PathSecurityError extends StorageError {
  constructor(path: string) {
    super('path_security', 'Path escapes base directory', path);
  }
}

export class StringNotFoundError extends StorageError {
  constructor(path: string) {
    super('string_not_found', 'String not found in file', path);
  }
}

export class StringNotUniqueError extends StorageError {
  constructor(path: string, occurrences: number) {
    super('string_not_unique', `String appears ${occurrences} times, must be unique`, path);
  }
}

export class BinaryFileError extends StorageError {
  constructor(path: string) {
    super('binary_file', 'Cannot perform text operation on binary file', path);
  }
}

export class InvalidLineNumberError extends StorageError {
  constructor(path: string, requested: number, max: number) {
    super('invalid_line_number', `Line number ${requested} out of range (1-${max})`, path);
  }
}

export class DirectoryNotEmptyError extends StorageError {
  constructor(path: string) {
    super('directory_not_empty', `Directory not empty: ${path}`, path);
  }
}

export class PermissionDeniedError extends StorageError {
  constructor(path: string) {
    super('permission_denied', `Permission denied: ${path}`, path);
  }
}

export class DiskFullError extends StorageError {
  constructor(path?: string) {
    super('disk_full', 'Insufficient disk space', path);
  }
}

export class InvalidEncodingError extends StorageError {
  constructor(path: string) {
    super('invalid_encoding', 'Content does not match specified encoding', path);
  }
}

/**
 * Raised for unimplemented methods within skeleton placeholders.
 */
export class NotImplementedError extends Error {
  constructor(message: string) {
    super(message);
  }
}

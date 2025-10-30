/**
 * Module: types
 * Purpose: Declare shared types for the file-storage-backend MCP server skeleton.
 * Created: 2025-10-30
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/file-storage-backend.md
 */

/**
 * Supported encodings for persisted file content.
 */
export type FileEncoding = 'utf-8' | 'base64';

/**
 * Union of tool-level error codes defined by the specification.
 */
export type StorageErrorCode =
  | 'file_not_found'
  | 'file_exists'
  | 'path_security'
  | 'string_not_found'
  | 'string_not_unique'
  | 'binary_file'
  | 'invalid_line_number'
  | 'directory_not_empty'
  | 'permission_denied'
  | 'disk_full'
  | 'invalid_encoding';

/**
 * Shape of MCP-compliant error responses returned by tool handlers.
 */
export interface StorageErrorPayload {
  /**
   * Machine-readable error code used by clients for branching logic.
   */
  code: StorageErrorCode;
  /**
   * Human-readable explanation describing the failure condition, matching the spec wording.
   */
  message: string;
  /**
   * Optional path associated with the failure, when relevant.
   */
  path?: string;
}

/**
 * Result structure returned by the `view` tool when inspecting files or directories.
 *
 * The discriminated union encodes the invariants from the specification so callers
 * can narrow on `type` safely without additional runtime checks.
 */
export type FileContent =
  | {
      /** Discriminator indicating a regular file result. */
      type: 'file';
      /** File contents encoded according to `encoding`. */
      content: string;
      /** Encoding for `content`. */
      encoding: FileEncoding;
      /** File size in bytes. */
      size: number;
    }
  | {
      /** Discriminator indicating a directory listing. */
      type: 'directory';
      /** Sorted entry names (excluding hidden files, '.', '..'). */
      entries: string[];
    };

/**
 * Configuration values required to bootstrap the MCP server.
 */
export interface FileStorageServerConfig {
  /**
   * Absolute filesystem path that defines the root containment boundary for all operations.
   */
  basePath: string;
}

/**
 * Input payload accepted by the `view` MCP tool.
 */
export interface ViewRequest {
  /**
   * Relative path constrained to the configured base directory.
   */
  path: string;
}

/**
 * Input payload accepted by the `create` MCP tool.
 */
export interface CreateRequest {
  /**
   * Destination path for the new file, relative to the base directory.
   */
  path: string;
  /**
   * File contents encoded according to `encoding`.
   */
  content: string;
  /**
   * Encoding scheme for `content`, matching spec-supported values.
   */
  encoding: FileEncoding;
}

/**
 * Input payload accepted by the `str_replace` MCP tool.
 */
export interface StrReplaceRequest {
  /**
   * Relative path to the target text file.
   */
  path: string;
  /**
   * String that must appear exactly once in the file before replacement.
   */
  old_str: string;
  /**
   * Replacement value that will atomically substitute the matching string.
   */
  new_str: string;
}

/**
 * Input payload accepted by the `insert` MCP tool.
 */
export interface InsertRequest {
  /**
   * Relative path to the target UTF-8 text file.
   */
  path: string;
  /**
   * One-indexed line number defining insert position.
   */
  insert_line: number;
  /**
   * Text snippet inserted verbatim at the specified line.
   */
  new_str: string;
}

/**
 * Input payload accepted by the `delete` MCP tool.
 */
export interface DeleteRequest {
  /**
   * Relative path to the file or empty directory slated for removal.
   */
  path: string;
}

/**
 * Input payload accepted by the `rename` MCP tool.
 */
export interface RenameRequest {
  /**
   * Existing relative path of the file or directory.
   */
  old_path: string;
  /**
   * Destination relative path that must not already exist.
   */
  new_path: string;
}

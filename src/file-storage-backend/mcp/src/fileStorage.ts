/**
 * Module: fileStorage
 * Purpose: Declare storage interface contract mirrored by MCP tool handlers.
 * Created: 2025-10-30
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/file-storage-backend.md
 */

import type { FileContent, FileEncoding } from './types.js';

/**
 * Primary interface that concrete storage engines must implement.
 *
 * Each method guarantees atomicity and path containment as described in the spec.
 */
export interface FileStorage {
  /**
   * Return file contents or a directory listing depending on the path type.
   * @param path - Relative path constrained to the configured base directory.
   * @returns File view result describing file data or directory entries.
   * @throws FileNotFoundError when the path does not exist.
   * @throws PathSecurityError when the normalized path escapes the base directory.
   * @throws PermissionDeniedError when filesystem permissions reject access.
   */
  view(path: string): Promise<FileContent>;

  /**
   * Create a new file populated with provided content.
   * @param path - Destination path for the new file, relative to the base directory.
   * @param content - File contents encoded according to `encoding`.
   * @param encoding - Encoding scheme for `content`.
   * @throws FileExistsError when the destination file already exists.
   * @throws PathSecurityError when the normalized path escapes the base directory.
   * @throws PermissionDeniedError when the filesystem rejects write permission.
   * @throws DiskFullError when storage capacity is insufficient.
   * @throws InvalidEncodingError when content fails validation for its encoding.
   */
  create(path: string, content: string, encoding: FileEncoding): Promise<void>;

  /**
   * Replace a unique string within a UTF-8 text file atomically.
   * @param path - Relative path to the target text file.
   * @param old_str - String that must appear exactly once in the file before replacement.
   * @param new_str - Replacement value that will atomically substitute the matching string.
   * @throws FileNotFoundError when the target file does not exist.
   * @throws StringNotFoundError when `old_str` is absent from the file.
   * @throws StringNotUniqueError when `old_str` occurs more than once.
   * @throws BinaryFileError when the file cannot be decoded as UTF-8 text.
   * @throws PathSecurityError when the normalized path escapes the base directory.
   */
  str_replace(path: string, old_str: string, new_str: string): Promise<void>;

  /**
   * Insert text at a one-indexed line position within a UTF-8 text file.
   * @param path - Relative path to the target UTF-8 text file.
   * @param insert_line - One-indexed line position describing where to insert.
   * @param new_str - Text snippet inserted verbatim at the specified line.
   * @throws FileNotFoundError when the target file does not exist.
   * @throws InvalidLineNumberError when `insert_line` falls outside [1, total_lines + 1].
   * @throws BinaryFileError when the file cannot be decoded as UTF-8 text.
   * @throws PathSecurityError when the normalized path escapes the base directory.
   */
  insert(path: string, insert_line: number, new_str: string): Promise<void>;

  /**
   * Delete a file or an empty directory.
   * @param path - Relative path referencing the filesystem entry to remove.
   * @throws FileNotFoundError when the path does not exist.
   * @throws DirectoryNotEmptyError when attempting to delete a directory with contents.
   * @throws PathSecurityError when the normalized path escapes the base directory.
   * @throws PermissionDeniedError when lack of permission prevents deletion.
   */
  delete(path: string): Promise<void>;

  /**
   * Rename or move a file/directory to a new relative location.
   * @param old_path - Existing relative path for the file or directory.
   * @param new_path - Destination relative path that must not already exist.
   * @throws FileNotFoundError when the source path does not exist.
   * @throws FileExistsError when the destination already exists.
   * @throws PathSecurityError when either path escapes the base directory.
   * @throws PermissionDeniedError when filesystem permissions reject the operation.
   */
  rename(old_path: string, new_path: string): Promise<void>;
}

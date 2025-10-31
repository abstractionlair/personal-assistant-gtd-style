/**
 * Module: storageGateway
 * Purpose: Abstract file-storage-backend integration behind domain-friendly API.
 * Created: 2025-10-31
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/graph-memory-core.md
 */

import { promises as fs } from 'fs';
import path from 'path';
import type { ContentEncoding } from './types.js';

/**
 * Storage abstraction that operates on paths relative to the configured base directory.
 *
 * Implementations are responsible for delegating to Feature 1 (file-storage-backend)
 * or an equivalent persistence mechanism that enforces atomic writes and path containment.
 */
export interface GraphStorageGateway {
  /**
   * Ensure a directory exists within the configured base path, creating intermediate folders if required.
   *
   * @param relativePath - Directory path relative to the graph memory base directory.
   * @returns Promise that resolves once the directory exists.
   * @throws Error When the underlying storage backend rejects directory creation (e.g., permission or disk issues).
   */
  ensureDirectory(relativePath: string): Promise<void>;

  /**
   * Determine whether a file or directory currently exists.
   *
   * @param relativePath - Path to test relative to the base directory.
   * @returns Promise resolving to true when the entry exists, false otherwise.
   * @throws Error When the underlying storage backend reports a containment/security violation.
   */
  pathExists(relativePath: string): Promise<boolean>;

  /**
   * Read a UTF-8 encoded text file from storage.
   *
   * @param relativePath - File path relative to the base directory.
   * @returns Promise resolving to the decoded UTF-8 string.
   * @throws Error When the path is invalid, the file cannot be read, or decoding fails.
   */
  readText(relativePath: string): Promise<string>;

  /**
   * Read a binary file and return its raw bytes without decoding.
   *
   * @param relativePath - File path relative to the base directory.
   * @returns Promise resolving to the raw file contents.
   * @throws Error When the path is invalid or the file cannot be read.
   */
  readBinary(relativePath: string): Promise<Buffer>;

  /**
   * Write UTF-8 encoded text content, overwriting any existing file atomically.
   *
   * @param relativePath - Destination path relative to the base directory.
   * @param content - Plain-text payload to persist.
   * @returns Promise that resolves once the file has been written.
   * @throws Error When the write fails (permission, disk, containment breach, etc.).
   */
  writeText(relativePath: string, content: string): Promise<void>;

  /**
   * Write binary content, overwriting any existing file atomically.
   *
   * @param relativePath - Destination path relative to the base directory.
   * @param content - Binary payload to persist.
   * @returns Promise that resolves once the file has been written.
   * @throws Error When the write fails (permission, disk, containment breach, etc.).
   */
  writeBinary(relativePath: string, content: Buffer): Promise<void>;

  /**
   * Remove a file at the supplied path. Directories must be empty before removal.
   *
   * @param relativePath - Path to delete relative to the base directory.
   * @returns Promise that resolves once the entry is removed.
   * @throws Error When the entry does not exist, is a non-empty directory, or removal fails.
   */
  deletePath(relativePath: string): Promise<void>;

  /**
   * List directory entries sorted lexicographically, excluding dot files and special entries.
   *
   * @param relativePath - Directory path relative to the base directory.
   * @returns Promise resolving to an array of entry names.
   * @throws Error When the directory does not exist or cannot be read.
   */
  listDirectory(relativePath: string): Promise<string[]>;
}

/**
 * Skeleton adapter that will bridge the graph memory domain to the file storage backend.
 */
export class FileStorageAdapter implements GraphStorageGateway {
  private readonly basePath: string;
  private readonly basePathWithSep: string;

  constructor(basePath: string) {
    const resolved = path.resolve(basePath);
    this.basePath = resolved;
    this.basePathWithSep = resolved.endsWith(path.sep) ? resolved : `${resolved}${path.sep}`;
  }

  /**
   * @inheritdoc
   */
  async ensureDirectory(relativePath: string): Promise<void> {
    const normalized = this.normalizeRelativePath(relativePath);
    const target = this.resolve(normalized);
    await fs.mkdir(target, { recursive: true });
  }

  /**
   * @inheritdoc
   */
  async pathExists(relativePath: string): Promise<boolean> {
    const normalized = this.normalizeRelativePath(relativePath);
    const target = this.resolve(normalized);
    try {
      await fs.access(target);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * @inheritdoc
   */
  async readText(relativePath: string): Promise<string> {
    const normalized = this.normalizeRelativePath(relativePath);
    const target = this.resolve(normalized);
    return fs.readFile(target, 'utf-8');
  }

  /**
   * @inheritdoc
   */
  async readBinary(relativePath: string): Promise<Buffer> {
    const normalized = this.normalizeRelativePath(relativePath);
    const target = this.resolve(normalized);
    return fs.readFile(target);
  }

  /**
   * @inheritdoc
   */
  async writeText(relativePath: string, content: string): Promise<void> {
    const normalized = this.normalizeRelativePath(relativePath);
    const target = this.resolve(normalized);
    await this.ensureParentDirectory(target);
    await fs.writeFile(target, content, 'utf-8');
  }

  /**
   * @inheritdoc
   */
  async writeBinary(relativePath: string, content: Buffer): Promise<void> {
    const normalized = this.normalizeRelativePath(relativePath);
    const target = this.resolve(normalized);
    await this.ensureParentDirectory(target);
    await fs.writeFile(target, content);
  }

  /**
   * @inheritdoc
   */
  async deletePath(relativePath: string): Promise<void> {
    const normalized = this.normalizeRelativePath(relativePath);
    const target = this.resolve(normalized);
    const stats = await fs.lstat(target);
    if (stats.isDirectory()) {
      await fs.rm(target, { recursive: false, force: false });
    } else {
      await fs.unlink(target);
    }
  }

  /**
   * @inheritdoc
   */
  async listDirectory(relativePath: string): Promise<string[]> {
    const normalized = this.normalizeRelativePath(relativePath);
    const target = this.resolve(normalized);
    const entries = await fs.readdir(target);
    return entries.filter(entry => !entry.startsWith('.')).sort();
  }

  /**
   * Encode caller-provided content according to the requested encoding.
   * The helper lives here because Feature 1 exposes operations in terms of encodings.
   *
   * @param content - Caller-provided string representation of node or connection content.
   * @param encoding - Declared encoding from the MCP request payload.
   * @returns Promise resolving to the encoded buffer ready for storage.
   */
  async encodeForStorage(content: string, encoding: ContentEncoding): Promise<Buffer> {
    if (encoding === 'utf-8') {
      return Buffer.from(content, 'utf-8');
    }
    return Buffer.from(content, 'base64');
  }

  /**
   * Decode stored buffers back into caller-facing strings.
   *
   * @param buffer - Raw content retrieved from storage.
   * @param encoding - Encoding that was used when persisting the file.
   * @returns Promise resolving to the decoded string ready to return via MCP.
   */
  async decodeFromStorage(buffer: Buffer, encoding: ContentEncoding): Promise<string> {
    if (encoding === 'utf-8') {
      return buffer.toString('utf-8');
    }
    return buffer.toString('base64');
  }

  private normalizeRelativePath(relativePath: string): string {
    if (!relativePath) {
      return '';
    }
    return relativePath.replace(/^[/\\]+/, '');
  }

  private resolve(relativePath: string): string {
    const resolved = relativePath ? path.resolve(this.basePath, relativePath) : this.basePath;
    if (resolved === this.basePath) {
      return resolved;
    }
    if (!resolved.startsWith(this.basePathWithSep)) {
      throw new Error(`Path escapes base directory: ${relativePath}`);
    }
    return resolved;
  }

  private async ensureParentDirectory(absolutePath: string): Promise<void> {
    const dir = path.dirname(absolutePath);
    await fs.mkdir(dir, { recursive: true });
  }
}

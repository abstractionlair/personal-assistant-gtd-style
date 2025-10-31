/**
 * Module: localFileStorage
 * Purpose: Provide filesystem-backed storage implementation with stubbed logic.
 * Created: 2025-10-30
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/file-storage-backend.md
 */

import { promises as fs } from 'fs';
import path from 'path';
import { randomUUID } from 'crypto';
import type { Stats } from 'fs';
import type { FileStorage } from './fileStorage.js';
import type { FileContent, FileEncoding, FileStorageServerConfig } from './types.js';
import {
  BinaryFileError,
  DirectoryNotEmptyError,
  DiskFullError,
  FileExistsError,
  FileNotFoundError,
  InvalidEncodingError,
  InvalidLineNumberError,
  PathSecurityError,
  PermissionDeniedError,
  StringNotFoundError,
  StringNotUniqueError
} from './errors.js';

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

  /**
   * Cached real path for the base directory so containment checks include symlink resolution.
   */
  private baseRealPath?: string;

  private baseRealPathPromise?: Promise<string>;

  /**
   * Hint table storing encoding decisions for files where heuristic detection is ambiguous (e.g., empty files).
   */
  private readonly encodingHints = new Map<string, FileEncoding>();

  constructor(config: FileStorageServerConfig) {
    this.basePath = path.resolve(config.basePath);
  }

  /**
   * Resolve the request and return file contents or directory entries.
   */
  async view(userPath: string): Promise<FileContent> {
    const normalizedPath = this.normalizeInputPath(userPath);
    const { resolvedPath } = await this.resolvePath(normalizedPath, { mustExist: true });
    const stats = await this.stat(resolvedPath, normalizedPath);

    if (stats.isDirectory()) {
      const entries = await fs.readdir(resolvedPath);
      const filtered = entries.filter(entry => !entry.startsWith('.')).sort();
      return {
        type: 'directory',
        entries: filtered
      };
    }

    const buffer = await fs.readFile(resolvedPath);
    const size = buffer.length;

    const hint = stats.size === 0 ? this.encodingHints.get(normalizedPath) : undefined;
    const { encoding, content } = this.readBufferForView(buffer, hint);

    return {
      type: 'file',
      content,
      encoding,
      size
    };
  }

  /**
   * Create a new file populated with caller-provided content.
   */
  async create(userPath: string, content: string, encoding: FileEncoding): Promise<void> {
    const normalizedPath = this.normalizeInputPath(userPath);
    const { resolvedPath } = await this.resolvePath(normalizedPath, { mustExist: false });

    if (await this.pathExists(resolvedPath)) {
      throw new FileExistsError(normalizedPath);
    }

    const parentDir = path.dirname(resolvedPath);
    await this.ensureDirectory(parentDir, normalizedPath);

    const data = this.encodeContent(content, encoding, normalizedPath);
    await this.writeFileAtomically(resolvedPath, data, encoding === 'utf-8' ? 'utf8' : undefined);
    this.rememberEncoding(normalizedPath, encoding);
  }

  /**
   * Replace a unique string within a text file atomically.
   */
  async str_replace(userPath: string, old_str: string, new_str: string): Promise<void> {
    const normalizedPath = this.normalizeInputPath(userPath);
    const { resolvedPath } = await this.resolvePath(normalizedPath, { mustExist: true });
    const stats = await this.stat(resolvedPath, normalizedPath);
    const originalMode = stats.mode;
    const text = await this.readUtf8File(resolvedPath, normalizedPath);

    if (old_str.length === 0) {
      throw new StringNotFoundError(normalizedPath);
    }

    const occurrences = this.countOccurrences(text, old_str);
    if (occurrences === 0) {
      throw new StringNotFoundError(normalizedPath);
    }
    if (occurrences > 1) {
      throw new StringNotUniqueError(normalizedPath, occurrences);
    }

    const updated = text.replace(old_str, new_str);
    await this.writeFileAtomically(resolvedPath, updated, 'utf8', originalMode);
    this.rememberEncoding(normalizedPath, 'utf-8');
  }

  /**
   * Insert new text at a one-indexed line position.
   */
  async insert(userPath: string, insert_line: number, new_str: string): Promise<void> {
    const normalizedPath = this.normalizeInputPath(userPath);
    const { resolvedPath } = await this.resolvePath(normalizedPath, { mustExist: true });
    const stats = await this.stat(resolvedPath, normalizedPath);
    const originalMode = stats.mode;
    const text = await this.readUtf8File(resolvedPath, normalizedPath);

    const totalLines = this.countLines(text);

    const maxLine = totalLines + 1;
    if (insert_line < 1 || insert_line > maxLine) {
      throw new InvalidLineNumberError(normalizedPath, insert_line, maxLine);
    }

    const insertIndex = this.computeLineStartIndex(text, insert_line);
    const updated = `${text.slice(0, insertIndex)}${new_str}${text.slice(insertIndex)}`;
    await this.writeFileAtomically(resolvedPath, updated, 'utf8', originalMode);
    this.rememberEncoding(normalizedPath, 'utf-8');
  }

  /**
   * Remove a file or an empty directory.
   */
  async delete(userPath: string): Promise<void> {
    const normalizedPath = this.normalizeInputPath(userPath);
    const { resolvedPath } = await this.resolvePath(normalizedPath, { mustExist: true });
    const stats = await this.stat(resolvedPath, normalizedPath);

    if (stats.isDirectory()) {
      const entries = await fs.readdir(resolvedPath);
      if (entries.length > 0) {
        throw new DirectoryNotEmptyError(normalizedPath);
      }

      await this.callFs(async () => fs.rmdir(resolvedPath), normalizedPath);
      this.forgetEncodingTree(normalizedPath);
      return;
    }

    await this.callFs(async () => fs.unlink(resolvedPath), normalizedPath);
    this.encodingHints.delete(normalizedPath);
  }

  /**
   * Move or rename a file/directory within the base path.
   */
  async rename(old_user_path: string, new_user_path: string): Promise<void> {
    const oldPath = this.normalizeInputPath(old_user_path);
    const newPath = this.normalizeInputPath(new_user_path);

    const { resolvedPath: sourcePath } = await this.resolvePath(oldPath, { mustExist: true });
    const sourceStats = await this.stat(sourcePath, oldPath);

    const { resolvedPath: targetPath } = await this.resolvePath(newPath, { mustExist: false });

    if (await this.pathExists(targetPath)) {
      throw new FileExistsError(newPath);
    }

    const targetDir = path.dirname(targetPath);
    await this.ensureDirectory(targetDir, newPath);

    await this.callFs(async () => fs.rename(sourcePath, targetPath), oldPath, newPath);

    const encoding = this.encodingHints.get(oldPath);
    if (encoding) {
      this.encodingHints.delete(oldPath);
      this.rememberEncoding(newPath, encoding);
    }

    if (sourceStats.isDirectory()) {
      this.updateHintsForDirectoryRename(oldPath, newPath);
    }
  }

  private async getBaseRealPath(): Promise<string> {
    if (this.baseRealPath) {
      return this.baseRealPath;
    }

    if (!this.baseRealPathPromise) {
      this.baseRealPathPromise = (async () => {
        await fs.mkdir(this.basePath, { recursive: true });
        return await fs.realpath(this.basePath);
      })();
    }

    this.baseRealPath = await this.baseRealPathPromise;
    return this.baseRealPath;
  }

  private normalizeInputPath(userPath: string): string {
    const converted = userPath.replace(/[\\/]/g, path.sep);
    const normalized = path.normalize(converted);
    const withoutDot = normalized === '.' ? '' : normalized;
    if (withoutDot === '') {
      return '';
    }

    const stripped =
      withoutDot.endsWith(path.sep) && withoutDot !== path.sep
        ? withoutDot.slice(0, -path.sep.length)
        : withoutDot;

    if (path.isAbsolute(stripped)) {
      throw new PathSecurityError(userPath);
    }

    return stripped;
  }

  private async resolvePath(
    normalizedPath: string,
    options: { mustExist: boolean }
  ): Promise<{ resolvedPath: string }> {
    const candidate = path.resolve(this.basePath, normalizedPath);

    await this.assertWithinBase(candidate, normalizedPath, options.mustExist);

    return { resolvedPath: candidate };
  }

  private async assertWithinBase(resolvedPath: string, displayPath: string, mustExist: boolean): Promise<void> {
    const baseReal = await this.getBaseRealPath();
    const relative = path.relative(this.basePath, resolvedPath);

    if (relative.startsWith('..') || path.isAbsolute(relative)) {
      throw new PathSecurityError(displayPath);
    }

    if (mustExist) {
      const real = await this.realpathSafe(resolvedPath, displayPath);
      const realRelative = path.relative(baseReal, real);
      if (realRelative.startsWith('..') || path.isAbsolute(realRelative)) {
        throw new PathSecurityError(displayPath);
      }
      return;
    }

    const ancestor = await this.findExistingAncestor(resolvedPath);
    if (ancestor) {
      const realAncestor = await this.realpathSafe(ancestor, displayPath);
      const ancestorRelative = path.relative(baseReal, realAncestor);
      if (ancestorRelative.startsWith('..') || path.isAbsolute(ancestorRelative)) {
        throw new PathSecurityError(displayPath);
      }
    }
  }

  private async realpathSafe(resolvedPath: string, displayPath: string): Promise<string> {
    try {
      return await fs.realpath(resolvedPath);
    } catch (error) {
      this.rethrowMapped(error, displayPath);
    }
  }

  private async findExistingAncestor(targetPath: string): Promise<string | undefined> {
    let current = targetPath;
    while (true) {
      try {
        await fs.lstat(current);
        return current;
      } catch (error) {
        const nodeError = error as NodeJS.ErrnoException;
        if (nodeError && nodeError.code === 'ENOENT') {
          const parent = path.dirname(current);
          if (parent === current) {
            return undefined;
          }
          current = parent;
          continue;
        }
        throw error;
      }
    }
  }

  private async ensureDirectory(directory: string, displayPath: string): Promise<void> {
    await this.callFs(async () => fs.mkdir(directory, { recursive: true }), displayPath);
    await this.assertWithinBase(directory, displayPath, false);
  }

  private async stat(resolvedPath: string, displayPath: string): Promise<Stats> {
    try {
      return await fs.stat(resolvedPath);
    } catch (error) {
      this.rethrowMapped(error, displayPath);
    }
  }

  private async pathExists(resolvedPath: string): Promise<boolean> {
    try {
      await fs.lstat(resolvedPath);
      return true;
    } catch (error) {
      const nodeError = error as NodeJS.ErrnoException;
      if (nodeError && nodeError.code === 'ENOENT') {
        return false;
      }
      throw error;
    }
  }

  private encodeContent(content: string, encoding: FileEncoding, displayPath: string): Buffer | string {
    if (encoding === 'utf-8') {
      return content;
    }

    if (content === '') {
      return Buffer.alloc(0);
    }

    try {
      const buffer = Buffer.from(content, 'base64');
      const normalizedInput = content.replace(/\s+/g, '');
      const roundTrip = buffer.toString('base64');
      if (normalizedInput.replace(/=+$/u, '') !== roundTrip.replace(/=+$/u, '')) {
        throw new Error('Base64 normalization mismatch');
      }
      return buffer;
    } catch {
      throw new InvalidEncodingError(displayPath);
    }
  }

  private readBufferForView(buffer: Buffer, hint?: FileEncoding): { encoding: FileEncoding; content: string } {
    if (buffer.length === 0) {
      const encoding = hint ?? 'utf-8';
      return { encoding, content: '' };
    }

    const decoded = buffer.toString('utf8');
    const reencoded = Buffer.from(decoded, 'utf8');

    if (reencoded.equals(buffer)) {
      return { encoding: 'utf-8', content: decoded };
    }

    return { encoding: 'base64', content: buffer.toString('base64') };
  }

  private async readUtf8File(resolvedPath: string, displayPath: string): Promise<string> {
    const buffer = await fs.readFile(resolvedPath);
    const decoded = buffer.toString('utf8');
    const reencoded = Buffer.from(decoded, 'utf8');

    if (!reencoded.equals(buffer)) {
      throw new BinaryFileError(displayPath);
    }

    return decoded;
  }

  private rememberEncoding(normalizedPath: string, encoding: FileEncoding): void {
    if (encoding === 'utf-8') {
      this.encodingHints.delete(normalizedPath);
    } else {
      this.encodingHints.set(normalizedPath, encoding);
    }
  }

  private forgetEncodingTree(pathKey: string): void {
    if (pathKey === '') {
      this.encodingHints.clear();
      return;
    }

    const prefix = `${pathKey}${path.sep}`;
    for (const key of Array.from(this.encodingHints.keys())) {
      if (key === pathKey || key.startsWith(prefix)) {
        this.encodingHints.delete(key);
      }
    }
  }

  private updateHintsForDirectoryRename(oldPath: string, newPath: string): void {
    if (oldPath === '' || oldPath === newPath) {
      return;
    }

    const prefix = `${oldPath}${path.sep}`;
    const newPrefix = newPath === '' ? '' : `${newPath}${path.sep}`;
    const updates: Array<[string, FileEncoding]> = [];

    for (const [key, value] of Array.from(this.encodingHints.entries())) {
      if (key === oldPath) {
        this.encodingHints.delete(key);
        if (newPath !== '') {
          updates.push([newPath, value]);
        }
        continue;
      }

      if (key.startsWith(prefix)) {
        this.encodingHints.delete(key);
        const relative = key.slice(prefix.length);
        const newKey = newPrefix ? `${newPrefix}${relative}` : relative;
        updates.push([newKey, value]);
      }
    }

    for (const [key, value] of updates) {
      this.encodingHints.set(key, value);
    }
  }

  private countOccurrences(haystack: string, needle: string): number {
    let count = 0;
    let startIndex = 0;
    while (true) {
      const index = haystack.indexOf(needle, startIndex);
      if (index === -1) {
        break;
      }
      count += 1;
      startIndex = index + Math.max(needle.length, 1);
    }
    return count;
  }

  private countLines(content: string): number {
    if (content === '') {
      return 0;
    }
    const segments = content.split('\n');
    if (content.endsWith('\n')) {
      segments.pop();
    }
    return segments.length;
  }

  private computeLineStartIndex(content: string, lineNumber: number): number {
    if (lineNumber === 1) {
      return 0;
    }

    let currentLine = 1;
    let index = 0;
    while (currentLine < lineNumber && index < content.length) {
      const nextNewline = content.indexOf('\n', index);
      if (nextNewline === -1) {
        index = content.length;
        break;
      }
      index = nextNewline + 1;
      currentLine += 1;
    }
    return index;
  }

  private async writeFileAtomically(
    targetPath: string,
    data: Buffer | string,
    encoding: BufferEncoding | undefined,
    mode?: number
  ): Promise<void> {
    const tempPath = `${targetPath}.${randomUUID()}.tmp`;
    try {
      await fs.writeFile(tempPath, data, encoding ? { encoding } : undefined);
      if (typeof mode === 'number') {
        await fs.chmod(tempPath, mode);
      }
      await fs.rename(tempPath, targetPath);
    } catch (error) {
      await this.safeUnlink(tempPath);
      this.rethrowMapped(error, path.relative(this.basePath, targetPath));
    }
  }

  private async safeUnlink(target: string): Promise<void> {
    try {
      await fs.unlink(target);
    } catch (error) {
      const nodeError = error as NodeJS.ErrnoException;
      if (!nodeError || (nodeError.code !== 'ENOENT' && nodeError.code !== 'EPERM')) {
        // Ignore ENOENT/EPERM cleanup failures, rethrow others so we do not mask critical issues.
        throw error;
      }
    }
  }

  private async callFs<T>(
    operation: () => Promise<T>,
    primaryPath: string,
    secondaryPath?: string
  ): Promise<T> {
    try {
      return await operation();
    } catch (error) {
      this.rethrowMapped(error, primaryPath, secondaryPath);
    }
  }

  private rethrowMapped(error: unknown, ...paths: Array<string | undefined>): never {
    if (error instanceof PermissionDeniedError) {
      throw error;
    }

    const nodeError = error as NodeJS.ErrnoException;
    const [primaryPath, secondaryPath] = paths.filter((value): value is string => Boolean(value));
    const effectivePath = (preferred?: string) =>
      (preferred !== undefined && preferred !== '' ? preferred : primaryPath) ?? '';

    if (nodeError && typeof nodeError.code === 'string') {
      switch (nodeError.code) {
        case 'ENOENT':
          throw new FileNotFoundError(effectivePath());
        case 'EEXIST':
          throw new FileExistsError(effectivePath(secondaryPath));
        case 'EACCES':
        case 'EPERM':
          throw new PermissionDeniedError(effectivePath());
        case 'ENOTEMPTY':
          throw new DirectoryNotEmptyError(effectivePath());
        case 'ENOSPC':
          throw new DiskFullError(effectivePath());
      }
    }

    throw error;
  }
}

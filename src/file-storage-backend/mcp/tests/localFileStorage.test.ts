import { describe, it, beforeEach, afterEach, expect, vi, test } from 'vitest';
import { promises as fs } from 'fs';
import path from 'path';
import os from 'os';
import { LocalFileStorage } from '../src/localFileStorage.ts';
import {
  BinaryFileError,
  DirectoryNotEmptyError,
  FileExistsError,
  FileNotFoundError,
  InvalidEncodingError,
  InvalidLineNumberError,
  PathSecurityError,
  StringNotFoundError,
  StringNotUniqueError,
} from '../src/errors.ts';

type Storage = LocalFileStorage;

describe('LocalFileStorage', () => {
  let basePath: string;
  let storage: Storage;

  beforeEach(async () => {
    basePath = await fs.mkdtemp(path.join(os.tmpdir(), 'local-file-storage-'));
    storage = new LocalFileStorage({ basePath });
  });

  afterEach(async () => {
    if (basePath) {
      await fs.rm(basePath, { recursive: true, force: true });
    }
  });

  const absolute = (relative: string) => path.join(basePath, relative);

  it('creates and views a UTF-8 file', async () => {
    const content = '# Team Meeting\n\nDiscuss Q1 goals';
    await storage.create('notes/meeting.md', content, 'utf-8');

    const result = await storage.view('notes/meeting.md');
    expect(result.type).toBe('file');
    if (result.type === 'file') {
      expect(result.content).toBe(content);
      expect(result.encoding).toBe('utf-8');
      expect(result.size).toBe(content.length);
    }

    const diskContent = await fs.readFile(absolute('notes/meeting.md'), 'utf8');
    expect(diskContent).toBe(content);
  });

  it('persists files across storage instances (simulating restart)', async () => {
    await storage.create('persist.txt', 'sticky', 'utf-8');
    storage = new LocalFileStorage({ basePath });

    const result = await storage.view('persist.txt');
    if (result.type === 'file') {
      expect(result.content).toBe('sticky');
    }
  });

  it('auto-creates parent directories on create', async () => {
    await storage.create('nodes/projects/archive/old-project.md', '# Archived', 'utf-8');

    expect(await fs.stat(absolute('nodes'))).toBeDefined();
    const result = await storage.view('nodes/projects/archive/old-project.md');
    expect(result.type).toBe('file');
  });

  it('rejects creating an existing file', async () => {
    await storage.create('config.json', '{"version":1}', 'utf-8');
    await expect(storage.create('config.json', '{}', 'utf-8')).rejects.toBeInstanceOf(FileExistsError);
  });

  it('fails when viewing a non-existent path', async () => {
    await expect(storage.view('missing.txt')).rejects.toBeInstanceOf(FileNotFoundError);
  });

  it('replaces unique strings in text files', async () => {
    await storage.create('project.md', '# Project Alpha\nStatus: Planning\n', 'utf-8');
    await storage.str_replace('project.md', 'Status: Planning', 'Status: In Progress');

    const result = await storage.view('project.md');
    if (result.type === 'file') {
      expect(result.content).toContain('Status: In Progress');
      expect(result.content).not.toContain('Status: Planning');
    }
  });

  it('rejects string replacement when string missing', async () => {
    await storage.create('project.md', '# Project Alpha\nStatus: Planning\n', 'utf-8');
    await expect(storage.str_replace('project.md', 'Budget', 'Budget: $50k')).rejects.toBeInstanceOf(
      StringNotFoundError,
    );
  });

  it('rejects string replacement when string is not unique', async () => {
    await storage.create('notes.md', 'TODO A\nTODO B\n', 'utf-8');
    await expect(storage.str_replace('notes.md', 'TODO', 'DONE')).rejects.toBeInstanceOf(StringNotUniqueError);
  });

  it('rejects text operations on binary files', async () => {
    const binary = Buffer.from([0, 1, 2, 255]).toString('base64');
    await storage.create('blob.bin', binary, 'base64');

    await expect(storage.str_replace('blob.bin', 'AA', 'BB')).rejects.toBeInstanceOf(BinaryFileError);
    await expect(storage.insert('blob.bin', 1, 'new text')).rejects.toBeInstanceOf(BinaryFileError);
  });

  it('inserts text at specific line numbers', async () => {
    await storage.create('story.txt', 'middle\n', 'utf-8');

    await storage.insert('story.txt', 1, 'start\n');
    await storage.insert('story.txt', 3, 'end');

    const result = await storage.view('story.txt');
    if (result.type === 'file') {
      expect(result.content).toBe('start\nmiddle\nend');
    }
  });

  it('validates insert line numbers', async () => {
    await storage.create('lines.txt', 'one\ntwo\n', 'utf-8');
    await expect(storage.insert('lines.txt', 0, 'zero')).rejects.toBeInstanceOf(InvalidLineNumberError);
    await expect(storage.insert('lines.txt', 4, 'four')).rejects.toBeInstanceOf(InvalidLineNumberError);
  });

  it('deletes files successfully', async () => {
    await storage.create('temp.txt', 'data', 'utf-8');
    await storage.delete('temp.txt');

    await expect(storage.view('temp.txt')).rejects.toBeInstanceOf(FileNotFoundError);
  });

  it('rejects deleting directories containing hidden files', async () => {
    await storage.create('temp/.gitkeep', '', 'utf-8');
    await expect(storage.delete('temp')).rejects.toBeInstanceOf(DirectoryNotEmptyError);
  });

  it('renames files and creates parent directories', async () => {
    await storage.create('old.txt', 'content', 'utf-8');
    await storage.rename('old.txt', 'dir/new.txt');

    await expect(storage.view('old.txt')).rejects.toBeInstanceOf(FileNotFoundError);
    const result = await storage.view('dir/new.txt');
    if (result.type === 'file') {
      expect(result.content).toBe('content');
    }
  });

  it('rejects renaming when destination exists', async () => {
    await storage.create('old.txt', 'content', 'utf-8');
    await storage.create('existing.txt', 'content', 'utf-8');

    await expect(storage.rename('old.txt', 'existing.txt')).rejects.toBeInstanceOf(FileExistsError);
  });

  it('renames directories with contents', async () => {
    await storage.create('dir/example.txt', 'content', 'utf-8');
    await storage.rename('dir', 'renamed');

    await expect(storage.view('dir/example.txt')).rejects.toBeInstanceOf(FileNotFoundError);
    const result = await storage.view('renamed/example.txt');
    expect(result.type).toBe('file');
  });

  it('rejects absolute paths for all operations', async () => {
    await expect(storage.view('/etc/passwd')).rejects.toBeInstanceOf(PathSecurityError);
    await expect(storage.create('/tmp/file.txt', '', 'utf-8')).rejects.toBeInstanceOf(PathSecurityError);
  });

  it('rejects paths escaping the base directory', async () => {
    await expect(storage.view('../outside.txt')).rejects.toBeInstanceOf(PathSecurityError);
  });

  it('rejects relative escape on create within a subpath', async () => {
    await expect(
      storage.create('nodes/../../../etc/bad', 'content', 'utf-8'),
    ).rejects.toBeInstanceOf(PathSecurityError);
  });

  test.skipIf(process.platform === 'win32')('rejects symlink escapes outside base', async () => {
    const outsideFile = path.join(basePath, '..', 'outside.txt');
    await fs.writeFile(outsideFile, 'outside');

    const linkPath = absolute('malicious-link');
    await fs.symlink(outsideFile, linkPath);

    await expect(storage.view('malicious-link')).rejects.toBeInstanceOf(PathSecurityError);
  });

  it('normalizes redundant path segments', async () => {
    await storage.create('dir1//dir2/./file.txt', 'content', 'utf-8');
    const result = await storage.view('dir1/dir2/file.txt');
    expect(result.type).toBe('file');
  });

  it('lists directory entries sorted without hidden files', async () => {
    await storage.create('dir/c.txt', 'c', 'utf-8');
    await storage.create('dir/b.txt', 'b', 'utf-8');
    await storage.create('dir/a.txt', 'a', 'utf-8');
    await storage.create('dir/file10.txt', '10', 'utf-8');
    await storage.create('dir/file2.txt', '2', 'utf-8');
    await storage.create('dir/.hidden', 'hidden', 'utf-8');

    const result = await storage.view('dir');
    if (result.type === 'directory') {
      expect(result.entries).toEqual(['a.txt', 'b.txt', 'c.txt', 'file10.txt', 'file2.txt']);
    } else {
      throw new Error('Expected directory view result');
    }
  });

  it('treats trailing slash and non-trailing slash equally when viewing directories', async () => {
    await storage.create('dir/file.txt', 'content', 'utf-8');

    const withoutSlash = await storage.view('dir');
    const withSlash = await storage.view('dir/');

    expect(withoutSlash).toStrictEqual(withSlash);
  });

  it('handles binary create and view with base64 encoding', async () => {
    const buffer = Buffer.from([0, 1, 2, 255, 16]);
    const payload = buffer.toString('base64');
    await storage.create('binary/blob.bin', payload, 'base64');

    const result = await storage.view('binary/blob.bin');
    if (result.type === 'file') {
      expect(result.encoding).toBe('base64');
      expect(result.content).toBe(payload);
      expect(result.size).toBe(buffer.length);
    } else {
      throw new Error('Expected file view result');
    }

    const disk = await fs.readFile(absolute('binary/blob.bin'));
    expect(disk.equals(buffer)).toBe(true);
  });

  it('supports empty files', async () => {
    await storage.create('empty.txt', '', 'utf-8');
    const result = await storage.view('empty.txt');
    if (result.type === 'file') {
      expect(result.size).toBe(0);
      expect(result.content).toBe('');
    }
  });

  it('supports empty binary files (base64="")', async () => {
    await storage.create('empty.bin', '', 'base64');
    const result = await storage.view('empty.bin');
    if (result.type === 'file') {
      expect(result.encoding).toBe('base64');
      expect(result.content).toBe('');
      expect(result.size).toBe(0);
    }
  });

  it('rejects invalid encoding payloads', async () => {
    await expect(storage.create('invalid.bin', 'not-valid-base64', 'base64')).rejects.toBeInstanceOf(
      InvalidEncodingError,
    );
  });

  it('does not leave files behind if create fails mid-operation', async () => {
    const renameSpy = vi.spyOn(fs, 'rename').mockImplementationOnce(() => {
      throw new Error('simulated failure');
    });

    try {
      await expect(storage.create('atomic.txt', 'content', 'utf-8')).rejects.toThrow();
      await expect(fs.stat(absolute('atomic.txt'))).rejects.toThrow();
    } finally {
      renameSpy.mockRestore();
    }
  });

  it('leaves original content untouched if str_replace fails mid-operation', async () => {
    await storage.create('atomic.txt', 'original', 'utf-8');
    const renameSpy = vi.spyOn(fs, 'rename').mockImplementationOnce(() => {
      throw new Error('simulated failure');
    });

    try {
      await expect(storage.str_replace('atomic.txt', 'original', 'updated')).rejects.toThrow();
      const result = await storage.view('atomic.txt');
      if (result.type === 'file') {
        expect(result.content).toBe('original');
      }
    } finally {
      renameSpy.mockRestore();
    }
  });

  it('leaves original content untouched if insert fails mid-operation', async () => {
    await storage.create('atomic.txt', 'line1\n', 'utf-8');
    const renameSpy = vi.spyOn(fs, 'rename').mockImplementationOnce(() => {
      throw new Error('simulated failure');
    });

    try {
      await expect(storage.insert('atomic.txt', 2, 'line2')).rejects.toThrow();
      const result = await storage.view('atomic.txt');
      if (result.type === 'file') {
        expect(result.content).toBe('line1\n');
      }
    } finally {
      renameSpy.mockRestore();
    }
  });

  it('keeps source path intact if rename fails', async () => {
    await storage.create('source.txt', 'content', 'utf-8');
    const renameSpy = vi.spyOn(fs, 'rename').mockImplementationOnce(() => {
      throw new Error('simulated failure');
    });

    try {
      await expect(storage.rename('source.txt', 'target.txt')).rejects.toThrow();
      const source = await storage.view('source.txt');
      expect(source.type).toBe('file');
      await expect(storage.view('target.txt')).rejects.toBeInstanceOf(FileNotFoundError);
    } finally {
      renameSpy.mockRestore();
    }
  });
});

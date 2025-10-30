import { afterEach, describe, expect, it, vi } from 'vitest';
import type { FileStorage } from '../src/fileStorage.ts';
import { FileStorageMcpServer, type ToolDefinition, type ToolRegistrar } from '../src/server.ts';
import type { FileContent } from '../src/types.ts';
import {
  FileExistsError,
  FileNotFoundError,
  PermissionDeniedError,
  DiskFullError,
} from '../src/errors.ts';

type MockedFileStorage = {
  [K in keyof FileStorage]: ReturnType<typeof vi.fn>;
};

class MockRegistrar implements ToolRegistrar {
  public readonly tools: Array<ToolDefinition<unknown, unknown>> = [];

  registerTool<TInput, TResult>(definition: ToolDefinition<TInput, TResult>): void {
    this.tools.push(definition as ToolDefinition<unknown, unknown>);
  }
}

const createMockStorage = (): MockedFileStorage => ({
  view: vi.fn(),
  create: vi.fn(),
  str_replace: vi.fn(),
  insert: vi.fn(),
  delete: vi.fn(),
  rename: vi.fn(),
});

const registerServerTools = (storage: MockedFileStorage) => {
  const registrar = new MockRegistrar();
  const server = new FileStorageMcpServer(storage as unknown as FileStorage);
  server.registerTools(registrar);
  return { registrar, server };
};

const getTool = <TInput, TResult>(
  registrar: MockRegistrar,
  name: string,
): ToolDefinition<TInput, TResult> => {
  const tool = registrar.tools.find((definition) => definition.name === name);
  if (!tool) {
    throw new Error(`Tool ${name} not registered`);
  }
  return tool as ToolDefinition<TInput, TResult>;
};

afterEach(() => {
  vi.resetAllMocks();
});

describe('FileStorageMcpServer registerTools', () => {
  it('registers all six MCP tools', () => {
    const storage = createMockStorage();
    const { registrar } = registerServerTools(storage);

    const toolNames = registrar.tools.map((tool) => tool.name).sort();
    expect(toolNames).toEqual(['create', 'delete', 'insert', 'rename', 'str_replace', 'view']);
    expect(registrar.tools).toHaveLength(6);
  });
});

describe('FileStorageMcpServer tool handlers', () => {
  it('delegates view handler to storage.view and returns result', async () => {
    const storage = createMockStorage();
    const result: FileContent = {
      type: 'file',
      content: 'data',
      encoding: 'utf-8',
      size: 4,
    };
    storage.view.mockResolvedValue(result);

    const { registrar } = registerServerTools(storage);
    const viewTool = getTool<{ path: string }, FileContent>(registrar, 'view');

    const payload = await viewTool.handler({ path: 'notes/file.md' });
    expect(storage.view).toHaveBeenCalledWith('notes/file.md');
    expect(payload).toBe(result);
  });

  it('delegates create handler to storage.create', async () => {
    const storage = createMockStorage();
    storage.create.mockResolvedValue(undefined);

    const { registrar } = registerServerTools(storage);
    const createTool = getTool<{ path: string; content: string; encoding: 'utf-8' }, void>(
      registrar,
      'create',
    );

    await createTool.handler({ path: 'file.txt', content: 'hello', encoding: 'utf-8' });

    expect(storage.create).toHaveBeenCalledWith('file.txt', 'hello', 'utf-8');
  });

  it('delegates str_replace handler to storage.str_replace', async () => {
    const storage = createMockStorage();
    storage.str_replace.mockResolvedValue(undefined);

    const { registrar } = registerServerTools(storage);
    const tool = getTool<{ path: string; old_str: string; new_str: string }, void>(registrar, 'str_replace');

    await tool.handler({ path: 'file.txt', old_str: 'a', new_str: 'b' });

    expect(storage.str_replace).toHaveBeenCalledWith('file.txt', 'a', 'b');
  });

  it('delegates insert handler to storage.insert', async () => {
    const storage = createMockStorage();
    storage.insert.mockResolvedValue(undefined);

    const { registrar } = registerServerTools(storage);
    const tool = getTool<{ path: string; insert_line: number; new_str: string }, void>(registrar, 'insert');

    await tool.handler({ path: 'file.txt', insert_line: 2, new_str: 'line' });

    expect(storage.insert).toHaveBeenCalledWith('file.txt', 2, 'line');
  });

  it('delegates delete handler to storage.delete', async () => {
    const storage = createMockStorage();
    storage.delete.mockResolvedValue(undefined);

    const { registrar } = registerServerTools(storage);
    const tool = getTool<{ path: string }, void>(registrar, 'delete');

    await tool.handler({ path: 'file.txt' });

    expect(storage.delete).toHaveBeenCalledWith('file.txt');
  });

  it('delegates rename handler to storage.rename', async () => {
    const storage = createMockStorage();
    storage.rename.mockResolvedValue(undefined);

    const { registrar } = registerServerTools(storage);
    const tool = getTool<{ old_path: string; new_path: string }, void>(registrar, 'rename');

    await tool.handler({ old_path: 'old.txt', new_path: 'new.txt' });

    expect(storage.rename).toHaveBeenCalledWith('old.txt', 'new.txt');
  });
});

describe('FileStorageMcpServer error mapping', () => {
  it('returns StorageError payloads from storage methods', async () => {
    const storage = createMockStorage();
    const error = new FileNotFoundError('missing.txt');
    storage.view.mockRejectedValue(error);

    const { registrar } = registerServerTools(storage);
    const viewTool = getTool<{ path: string }, FileContent>(registrar, 'view');

    await expect(viewTool.handler({ path: 'missing.txt' })).rejects.toEqual(error.toPayload());
  });

  it('maps Node.js ENOENT errors to file_not_found payloads', async () => {
    const storage = createMockStorage();
    const nodeError = new Error('not found') as NodeJS.ErrnoException;
    nodeError.code = 'ENOENT';
    nodeError.path = 'missing.txt';
    storage.delete.mockRejectedValue(nodeError);

    const { registrar } = registerServerTools(storage);
    const tool = getTool<{ path: string }, void>(registrar, 'delete');

    await expect(tool.handler({ path: 'missing.txt' })).rejects.toEqual(
      new FileNotFoundError('missing.txt').toPayload(),
    );
  });

  it('maps Node.js EEXIST errors to file_exists payloads', async () => {
    const storage = createMockStorage();
    const nodeError = new Error('exists') as NodeJS.ErrnoException;
    nodeError.code = 'EEXIST';
    nodeError.path = 'file.txt';
    storage.create.mockRejectedValue(nodeError);

    const { registrar } = registerServerTools(storage);
    const tool = getTool<{ path: string; content: string; encoding: 'utf-8' }, void>(registrar, 'create');

    await expect(tool.handler({ path: 'file.txt', content: 'c', encoding: 'utf-8' })).rejects.toEqual(
      new FileExistsError('file.txt').toPayload(),
    );
  });

  it('maps Node.js EACCES errors to permission_denied payloads', async () => {
    const storage = createMockStorage();
    const nodeError = new Error('denied') as NodeJS.ErrnoException;
    nodeError.code = 'EACCES';
    nodeError.path = 'secure/file.txt';
    storage.view.mockRejectedValue(nodeError);

    const { registrar } = registerServerTools(storage);
    const viewTool = getTool<{ path: string }, FileContent>(registrar, 'view');

    await expect(viewTool.handler({ path: 'secure/file.txt' })).rejects.toEqual(
      new PermissionDeniedError('secure/file.txt').toPayload(),
    );
  });

  it('maps Node.js ENOSPC errors to disk_full payloads', async () => {
    const storage = createMockStorage();
    const nodeError = new Error('disk full') as NodeJS.ErrnoException;
    nodeError.code = 'ENOSPC';
    nodeError.path = 'file.txt';
    storage.create.mockRejectedValue(nodeError);

    const { registrar } = registerServerTools(storage);
    const createTool = getTool<{ path: string; content: string; encoding: 'utf-8' }, void>(registrar, 'create');

    await expect(createTool.handler({ path: 'file.txt', content: 'data', encoding: 'utf-8' })).rejects.toEqual(
      new DiskFullError('file.txt').toPayload(),
    );
  });
});

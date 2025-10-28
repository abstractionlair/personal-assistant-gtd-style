# File Storage Backend Interface Specification

## Overview

The memory system's graph layer delegates all file I/O to a pluggable storage backend. This interface is designed to be compatible with Anthropic's Memory Tool specification, allowing future migration to their system while maintaining our graph semantics.

## Design Principles

1. **Backend Agnostic**: Graph layer never touches files directly
2. **Anthropic Compatible**: Operations match their Memory Tool spec
3. **Swappable**: Can switch backends without changing graph layer
4. **Simple**: Just file CRUD operations, no graph semantics

## Core Interface

### Required Operations

All storage backends must implement these six operations:

```typescript
interface FileStorage {
  // View file or directory contents
  view(path: string): Promise<FileContent>
  
  // Create new file with content
  create(path: string, content: string | Buffer): Promise<void>
  
  // Replace string in file (for editing)
  str_replace(path: string, old_str: string, new_str: string): Promise<void>
  
  // Insert text at line number
  insert(path: string, insert_line: number, new_str: string): Promise<void>
  
  // Delete file
  delete(path: string): Promise<void>
  
  // Rename/move file
  rename(old_path: string, new_path: string): Promise<void>
}

type FileContent = {
  type: 'file' | 'directory'
  content?: string | Buffer
  entries?: string[]  // For directories
  size?: number
}
```

## Operation Semantics

### view(path)

**Purpose**: Read file content or list directory contents

**Behavior**:
- If path is file: Return file content
- If path is directory: Return list of entries
- If path doesn't exist: Throw error

**Example**:
```typescript
// View file
const result = await storage.view('/memories/nodes/proj_001.md')
// Returns: { type: 'file', content: '# Kitchen Renovation\n...', size: 2048 }

// View directory
const result = await storage.view('/memories/nodes')
// Returns: { type: 'directory', entries: ['proj_001.md', 'act_001.md', ...] }
```

### create(path, content)

**Purpose**: Create new file with content

**Behavior**:
- Creates file at path with given content
- Creates parent directories if needed
- If file exists: Throw error (use str_replace to modify)
- Content can be string or Buffer

**Example**:
```typescript
await storage.create(
  '/memories/nodes/proj_001.md',
  '# Kitchen Renovation\n\nBudget: $50k\n...'
)
```

### str_replace(path, old_str, new_str)

**Purpose**: Replace text in file (primary editing method)

**Behavior**:
- Finds old_str in file
- Replaces with new_str
- If old_str not found or appears multiple times: Throw error
- Must be exact match (no regex)

**Example**:
```typescript
await storage.str_replace(
  '/memories/nodes/proj_001.md',
  'Budget: $50k',
  'Budget: $45k'
)
```

### insert(path, insert_line, new_str)

**Purpose**: Insert text at specific line

**Behavior**:
- Inserts new_str at line number (1-indexed)
- Pushes existing content down
- If line number invalid: Throw error

**Example**:
```typescript
await storage.insert(
  '/memories/nodes/proj_001.md',
  5,
  'Timeline: Q1 2026\n'
)
```

### delete(path)

**Purpose**: Remove file

**Behavior**:
- Deletes file at path
- If path is directory and not empty: Throw error
- If path doesn't exist: Throw error

**Example**:
```typescript
await storage.delete('/memories/nodes/proj_001.md')
```

### rename(old_path, new_path)

**Purpose**: Move or rename file

**Behavior**:
- Moves file from old_path to new_path
- Creates parent directories if needed
- If old_path doesn't exist: Throw error
- If new_path exists: Throw error

**Example**:
```typescript
await storage.rename(
  '/memories/nodes/proj_001.md',
  '/memories/archive/proj_001.md'
)
```

## Implementation: Local File System

### LocalFileStorage

Reference implementation using Node.js file system:

```typescript
import * as fs from 'fs/promises'
import * as path from 'path'

export class LocalFileStorage implements FileStorage {
  constructor(private basePath: string) {}
  
  private resolve(filePath: string): string {
    return path.join(this.basePath, filePath)
  }
  
  async view(filePath: string): Promise<FileContent> {
    const fullPath = this.resolve(filePath)
    const stats = await fs.stat(fullPath)
    
    if (stats.isDirectory()) {
      const entries = await fs.readdir(fullPath)
      return { type: 'directory', entries }
    } else {
      const content = await fs.readFile(fullPath, 'utf-8')
      return { type: 'file', content, size: stats.size }
    }
  }
  
  async create(filePath: string, content: string | Buffer): Promise<void> {
    const fullPath = this.resolve(filePath)
    
    // Ensure parent directory exists
    await fs.mkdir(path.dirname(fullPath), { recursive: true })
    
    // Check if file already exists
    try {
      await fs.access(fullPath)
      throw new Error(`File already exists: ${filePath}`)
    } catch (e) {
      if (e.code !== 'ENOENT') throw e
    }
    
    await fs.writeFile(fullPath, content)
  }
  
  async str_replace(
    filePath: string, 
    old_str: string, 
    new_str: string
  ): Promise<void> {
    const fullPath = this.resolve(filePath)
    const content = await fs.readFile(fullPath, 'utf-8')
    
    // Check if old_str appears exactly once
    const matches = content.split(old_str).length - 1
    if (matches === 0) {
      throw new Error(`String not found: ${old_str}`)
    }
    if (matches > 1) {
      throw new Error(`String appears ${matches} times, must be unique`)
    }
    
    const newContent = content.replace(old_str, new_str)
    await fs.writeFile(fullPath, newContent)
  }
  
  async insert(
    filePath: string, 
    insert_line: number, 
    new_str: string
  ): Promise<void> {
    const fullPath = this.resolve(filePath)
    const content = await fs.readFile(fullPath, 'utf-8')
    const lines = content.split('\n')
    
    if (insert_line < 1 || insert_line > lines.length + 1) {
      throw new Error(`Invalid line number: ${insert_line}`)
    }
    
    lines.splice(insert_line - 1, 0, new_str)
    await fs.writeFile(fullPath, lines.join('\n'))
  }
  
  async delete(filePath: string): Promise<void> {
    const fullPath = this.resolve(filePath)
    const stats = await fs.stat(fullPath)
    
    if (stats.isDirectory()) {
      const entries = await fs.readdir(fullPath)
      if (entries.length > 0) {
        throw new Error(`Directory not empty: ${filePath}`)
      }
      await fs.rmdir(fullPath)
    } else {
      await fs.unlink(fullPath)
    }
  }
  
  async rename(old_path: string, new_path: string): Promise<void> {
    const oldFull = this.resolve(old_path)
    const newFull = this.resolve(new_path)
    
    // Ensure parent directory exists
    await fs.mkdir(path.dirname(newFull), { recursive: true })
    
    // Check if new path already exists
    try {
      await fs.access(newFull)
      throw new Error(`Destination already exists: ${new_path}`)
    } catch (e) {
      if (e.code !== 'ENOENT') throw e
    }
    
    await fs.rename(oldFull, newFull)
  }
}
```

### Usage

```typescript
const storage = new LocalFileStorage('/path/to/memories')

// All operations are now scoped to /path/to/memories
await storage.create('nodes/proj_001.md', '# Project')
await storage.view('nodes')
```

## Future Implementation: Anthropic Memory Tool

### AnthropicMemoryStorage

When Anthropic's Memory Tool becomes available:

```typescript
export class AnthropicMemoryStorage implements FileStorage {
  constructor(
    private apiKey: string,
    private memoryNamespace: string = '/memories'
  ) {}
  
  async view(filePath: string): Promise<FileContent> {
    // Call Anthropic API with memory tool
    const response = await this.callMemoryTool({
      command: 'view',
      path: this.resolvePath(filePath)
    })
    
    // Parse response and return FileContent
    return this.parseViewResponse(response)
  }
  
  async create(filePath: string, content: string | Buffer): Promise<void> {
    await this.callMemoryTool({
      command: 'create',
      path: this.resolvePath(filePath),
      content: content.toString()
    })
  }
  
  // ... implement other operations similarly
  
  private async callMemoryTool(params: any): Promise<any> {
    // Implementation depends on Anthropic's API structure
    // May involve:
    // - Direct API endpoint for memory operations
    // - Or triggering Claude with tool use
    // - Or using their SDK if provided
  }
  
  private resolvePath(filePath: string): string {
    return `${this.memoryNamespace}/${filePath}`
  }
}
```

### Migration Path

When switching from local to Anthropic storage:

```typescript
// Before
const storage = new LocalFileStorage('/path/to/memories')
const memorySystem = new MemoryGraph(storage, registry, ontology)

// After (only change this line)
const storage = new AnthropicMemoryStorage(apiKey, '/memories')
const memorySystem = new MemoryGraph(storage, registry, ontology)
```

The graph layer code remains unchanged.

## Integration with Graph Layer

### How Graph Layer Uses Backend

The graph layer NEVER directly manipulates files. Instead:

```typescript
class MemoryGraph {
  constructor(
    private storage: FileStorage,
    private registry: Registry,
    private ontology: Ontology
  ) {}
  
  async createNode(
    type: string,
    content: string | Buffer,
    format: string,
    properties?: object
  ): Promise<NodeId> {
    // 1. Generate ID
    const id = generateId()
    
    // 2. Determine storage path
    const path = this.getNodePath(id, format)
    
    // 3. Use storage backend to write content
    await this.storage.create(path, content)
    
    // 4. Update registry
    this.registry.addNode(id, {
      type,
      properties,
      storage: { path, format }
    })
    
    return id
  }
  
  async getNodeContent(id: NodeId): Promise<string | Buffer> {
    // 1. Look up path in registry
    const node = this.registry.getNode(id)
    
    // 2. Use storage backend to read
    const result = await this.storage.view(node.storage.path)
    
    return result.content!
  }
  
  // ... other operations similarly delegate to storage
}
```

### Registry Management

The registry is also stored via the backend:

```typescript
class Registry {
  constructor(
    private storage: FileStorage,
    private registryPath: string = '_system/registry.json'
  ) {}
  
  async load(): Promise<void> {
    const result = await this.storage.view(this.registryPath)
    this.data = JSON.parse(result.content as string)
  }
  
  async save(): Promise<void> {
    const content = JSON.stringify(this.data, null, 2)
    
    if (await this.exists()) {
      // Update existing
      const oldContent = await this.storage.view(this.registryPath)
      await this.storage.str_replace(
        this.registryPath,
        oldContent.content as string,
        content
      )
    } else {
      // Create new
      await this.storage.create(this.registryPath, content)
    }
  }
  
  private async exists(): Promise<boolean> {
    try {
      await this.storage.view(this.registryPath)
      return true
    } catch {
      return false
    }
  }
}
```

## Directory Structure

### Standard Layout

```
/memories/
  _system/
    registry.json          # Graph metadata
    ontology.yaml         # Type definitions
  
  _content/
    nodes/
      mem_proj_001.md     # Node content files
      mem_act_001.md
      mem_doc_001.pdf
    
    connections/
      conn_001.md         # Connection content (optional)
```

### Path Conventions

**Nodes by format:**
- Markdown: `_content/nodes/{id}.md`
- JSON: `_content/nodes/{id}.json`
- PDF: `_content/nodes/{id}.pdf`
- Images: `_content/nodes/{id}.{jpg|png|...}`

**Connections:**
- `_content/connections/{id}.md`

**System files:**
- Registry: `_system/registry.json`
- Ontology: `_system/ontology.yaml`

## Error Handling

### Backend Errors

Backends should throw descriptive errors:

```typescript
class StorageError extends Error {
  constructor(
    message: string,
    public code: string,
    public path?: string
  ) {
    super(message)
  }
}

// Common error codes
'FILE_NOT_FOUND'
'FILE_EXISTS'
'INVALID_PATH'
'PERMISSION_DENIED'
'STRING_NOT_FOUND'
'STRING_NOT_UNIQUE'
'DIRECTORY_NOT_EMPTY'
```

### Graph Layer Handling

```typescript
try {
  await storage.create(path, content)
} catch (error) {
  if (error.code === 'FILE_EXISTS') {
    // Handle duplicate creation
  } else {
    throw new GraphError(
      `Failed to create node: ${error.message}`,
      'NODE_CREATION_FAILED',
      { nodeId, originalError: error }
    )
  }
}
```

## Testing

### Backend Tests

Each backend implementation should pass this test suite:

```typescript
describe('FileStorage', () => {
  let storage: FileStorage
  
  beforeEach(async () => {
    storage = createTestStorage()
  })
  
  test('create and view file', async () => {
    await storage.create('/test.txt', 'hello')
    const result = await storage.view('/test.txt')
    expect(result.content).toBe('hello')
  })
  
  test('str_replace', async () => {
    await storage.create('/test.txt', 'hello world')
    await storage.str_replace('/test.txt', 'world', 'universe')
    const result = await storage.view('/test.txt')
    expect(result.content).toBe('hello universe')
  })
  
  test('insert at line', async () => {
    await storage.create('/test.txt', 'line1\nline3')
    await storage.insert('/test.txt', 2, 'line2')
    const result = await storage.view('/test.txt')
    expect(result.content).toBe('line1\nline2\nline3')
  })
  
  test('delete file', async () => {
    await storage.create('/test.txt', 'hello')
    await storage.delete('/test.txt')
    await expect(storage.view('/test.txt')).rejects.toThrow()
  })
  
  test('rename file', async () => {
    await storage.create('/old.txt', 'hello')
    await storage.rename('/old.txt', '/new.txt')
    const result = await storage.view('/new.txt')
    expect(result.content).toBe('hello')
    await expect(storage.view('/old.txt')).rejects.toThrow()
  })
  
  test('view directory', async () => {
    await storage.create('/dir/file1.txt', 'a')
    await storage.create('/dir/file2.txt', 'b')
    const result = await storage.view('/dir')
    expect(result.type).toBe('directory')
    expect(result.entries).toContain('file1.txt')
    expect(result.entries).toContain('file2.txt')
  })
  
  // Error cases
  test('create existing file throws', async () => {
    await storage.create('/test.txt', 'hello')
    await expect(
      storage.create('/test.txt', 'world')
    ).rejects.toThrow()
  })
  
  test('str_replace with non-unique string throws', async () => {
    await storage.create('/test.txt', 'hello hello')
    await expect(
      storage.str_replace('/test.txt', 'hello', 'hi')
    ).rejects.toThrow()
  })
})
```

## Performance Considerations

### Caching

Backends may implement caching:

```typescript
class CachedFileStorage implements FileStorage {
  private cache = new Map<string, FileContent>()
  
  constructor(private backend: FileStorage) {}
  
  async view(path: string): Promise<FileContent> {
    if (this.cache.has(path)) {
      return this.cache.get(path)!
    }
    
    const result = await this.backend.view(path)
    this.cache.set(path, result)
    return result
  }
  
  async create(path: string, content: string | Buffer): Promise<void> {
    await this.backend.create(path, content)
    this.cache.delete(path) // Invalidate
  }
  
  // ... other operations invalidate cache appropriately
}
```

### Batching

For multiple operations:

```typescript
interface BatchableStorage extends FileStorage {
  batch(operations: Operation[]): Promise<void>
}

type Operation = 
  | { type: 'create', path: string, content: string | Buffer }
  | { type: 'delete', path: string }
  | { type: 'rename', old_path: string, new_path: string }
  // ...
```

## Summary

The file storage backend provides:
- **Simple, well-defined interface** (6 operations)
- **Anthropic compatibility** (matches their spec)
- **Pluggable implementations** (local, cloud, Anthropic)
- **Clean separation** (graph layer never touches files)
- **Future-proof** (easy to migrate backends)

The graph layer depends only on this interface, making the entire system backend-agnostic and future-proof.

# Specification: File Storage Backend MCP Server

**Feature ID:** phase1-feature1
**Version:** 1.2
**Status:** Done (Implementation Approved)
**Created:** 2025-10-30
**Updated:** 2025-10-30 (editorial improvements post-approval)
**Author:** spec-writing-helper (collaborative)

---

## Overview

The File Storage Backend MCP Server provides a foundational layer of file operations that replicates Anthropic's Memory Tool interface. It exposes six file operations (view, create, str_replace, insert, delete, rename) as MCP tools that can be used directly by Claude Code or called by other MCP servers like the Graph Memory server.

This feature establishes the persistent storage foundation for the entire GTD personal assistant system. By implementing the Memory Tool interface, it enables future migration to Anthropic's system while maintaining local control and compatibility with the existing graph-based memory architecture.

---

## Feature Scope

### Included
- MCP server exposing 6 file operation tools: view, create, str_replace, insert, delete, rename
- Local filesystem implementation with all operations working correctly
- Path security (operations contained within base directory, symlinks resolved and checked for escape)
- Text and binary file support via JSON-safe encoding (utf-8 or base64)
- Atomic operations (complete fully or fail cleanly, no partial writes)
- Parent directory auto-creation when needed
- Standard MCP error responses with error codes and descriptive messages
- Configuration for base path

### Excluded (Not in This Feature)
- Alternative storage backends (cloud storage, databases) - local filesystem only
- Caching layer - direct filesystem operations
- Batch operations - single operation per tool call
- Authentication/authorization (handled by MCP/Claude Code layer)
- Advanced path security beyond basic containment (no ACLs, no permission checks beyond OS level)

### Deferred (Maybe in Future)
- Anthropic Memory Tool adapter implementation (when their spec is fully available)
- Performance optimizations (only if profiling shows need)

---

## User/System Perspective

**From Claude Code's perspective:**
- Six new MCP tools become available for file operations
- Tools operate on files within a configured base directory
- Operations either succeed completely or fail with clear error messages
- Files created are normal filesystem files that can be viewed/edited with any tool

**From Graph Memory Server's perspective:**
- Can call the file-storage server's tools via MCP protocol to persist graph data
- Receives success/error responses in standard MCP format
- Files persist between calls and server restarts

**From Developer's perspective:**
- Can register the server in Claude Code configuration
- Files appear in the configured base directory on the filesystem
- Can manually inspect/edit files using standard tools
- Server starts automatically when Claude Code connects

---

## Value Delivered

This feature solves the foundational problem of persistent storage for the GTD system. Without reliable file operations, the graph memory layer cannot persist nodes, connections, or registry data across sessions.

By replicating Anthropic's Memory Tool interface, this provides immediate local functionality while maintaining a future migration path to their cloud-based system. The MCP architecture ensures clean separation - the graph layer never touches files directly, making the entire system backend-agnostic.

This delivers the foundation for all memory layers as specified in ROADMAP.md Phase 1, enabling the remaining features (Graph Memory Core, GTD Ontology, Conversational Layer) to be built on top.

---

## Interface Contract

### MCP Server Configuration

**Server Name:** `file-storage-backend`

**Configuration Schema:**
```typescript
{
  basePath: string  // Absolute path to storage directory
}
```

**Example Configuration (Claude Code):**
```json
{
  "mcpServers": {
    "file-storage": {
      "command": "node",
      "args": ["/path/to/file-storage-backend/dist/index.js"],
      "env": {
        "BASE_PATH": "/Users/username/gtd-storage"
      }
    }
  }
}
```

---

### Tool 1: view

**Purpose:** Read file content or list directory contents

**Input Schema:**
```typescript
{
  path: string  // Relative path within base directory
}
```

**Parameters:**
- `path` (string): Relative path within base directory
  - Constraints: Must not escape base directory (including via symlinks), no absolute paths
  - Example: `"nodes/project_001.md"` or `"nodes/"` or `"nodes"` for directory
  - Normalization: Path separators normalized, trailing slashes accepted for directories
  - Symlinks: Followed but resolved path must remain within base directory

**Returns:**
- FileContent object with structure:
  ```typescript
  {
    type: 'file' | 'directory',
    content?: string,           // For files only (text content or base64)
    encoding?: 'utf-8' | 'base64',  // For files only (always present with content)
    entries?: string[],         // For directories (sorted by Unicode code point)
    size?: number               // For files (bytes)
  }
  ```
- Example (text file): `{ type: 'file', content: '# Project\n\nDetails...', encoding: 'utf-8', size: 1024 }`
- Example (binary file): `{ type: 'file', content: 'iVBORw0KG...', encoding: 'base64', size: 2048 }`
- Example (directory): `{ type: 'directory', entries: ['file1.md', 'file2.md'] }`

**Errors:**
- Error code `file_not_found`: "File not found: {path}"
- Error code `path_security`: "Path escapes base directory" (including symlink escapes)
- Error code `permission_denied`: "Permission denied: {path}"

**Preconditions:**
- Base directory must exist and be accessible
- Path must be within base directory boundaries (after symlink resolution)

**Postconditions:**
- Returns current file content or directory listing
- No filesystem modifications
- For directories: hidden files (starting with `.`), `.` and `..` excluded from entries
- Directory entries sorted by Unicode code point (ascending, case-sensitive)

**Example Usage:**
```typescript
// View text file
const result = await view({ path: "notes/meeting.md" })
// result = { type: 'file', content: '# Meeting Notes\n...', encoding: 'utf-8', size: 256 }

// View binary file
const result = await view({ path: "images/logo.png" })
// result = { type: 'file', content: 'iVBORw0KG...', encoding: 'base64', size: 2048 }

// List directory (both forms work)
const result = await view({ path: "notes/" })
// or: await view({ path: "notes" })
// result = { type: 'directory', entries: ['meeting.md', 'project.md'] }
```

---

### Tool 2: create

**Purpose:** Create a new file with content

**Input Schema:**
```typescript
{
  path: string,              // Relative path within base directory
  content: string,           // File content (text or base64-encoded binary)
  encoding: 'utf-8' | 'base64'  // Content encoding
}
```

**Parameters:**
- `path` (string): Relative path within base directory
  - Constraints: Must not escape base directory (including via symlinks), no absolute paths
  - Example: `"deep/nested/path/file.txt"`
  - Auto-creation: Parent directories created automatically
- `content` (string): File content
  - Constraints: Must match specified encoding
  - Example (utf-8): `"# My Notes\n\nContent here"`
  - Example (base64): `"iVBORw0KGgoAAAANS..."`
- `encoding` ('utf-8' | 'base64'): Content encoding
  - Required field
  - 'utf-8' for text files
  - 'base64' for binary files

**Returns:**
- void (success) or throws error

**Errors:**
- Error code `file_exists`: "File already exists: {path}"
- Error code `path_security`: "Path escapes base directory" (including symlink escapes)
- Error code `permission_denied`: "Permission denied: {path}"
- Error code `disk_full`: "Insufficient disk space"
- Error code `invalid_encoding`: "Content does not match specified encoding"

**Preconditions:**
- File must not already exist at path
- Base directory must exist and be writable
- Sufficient disk space available
- Content must be valid for specified encoding

**Postconditions:**
- File created at specified path with decoded content
- Parent directories created if needed
- File appears atomically (fully written or not at all)
- Subsequent view() returns the content with same encoding

**Example Usage:**
```typescript
// Text file
await create({
  path: "projects/new-project.md",
  content: "# New Project\n\nDescription here",
  encoding: "utf-8"
})
// File created at {basePath}/projects/new-project.md

// Binary file
await create({
  path: "images/logo.png",
  content: "iVBORw0KGgoAAAANSUhEUg...",
  encoding: "base64"
})
```

---

### Tool 3: str_replace

**Purpose:** Replace text in a file (primary editing method)

**Input Schema:**
```typescript
{
  path: string,     // Relative path within base directory
  old_str: string,  // String to find (must be unique)
  new_str: string   // Replacement string
}
```

**Parameters:**
- `path` (string): Relative path within base directory
  - Constraints: File must exist
  - Example: `"projects/current.md"`
- `old_str` (string): Text to find
  - Constraints: Must appear exactly once in file
  - Example: `"Status: Planning"`
  - Matching: Exact match (no regex, case-sensitive)
- `new_str` (string): Replacement text
  - Example: `"Status: In Progress"`

**Returns:**
- void (success) or throws error

**Errors:**
- Error code `file_not_found`: "File not found: {path}"
- Error code `string_not_found`: "String not found in file"
- Error code `string_not_unique`: "String appears {N} times, must be unique"
- Error code `binary_file`: "Cannot perform text operation on binary file"
- Error code `path_security`: "Path escapes base directory" (including symlink escapes)

**Preconditions:**
- File must exist at path
- File must be valid UTF-8 text (not binary)
- old_str must appear exactly once in file

**Postconditions:**
- File content has old_str replaced with new_str
- Replacement is atomic (file has old content or new content, never partial)
- Subsequent view() returns modified content
- File modification time updated

**Example Usage:**
```typescript
await str_replace({
  path: "projects/current.md",
  old_str: "Budget: $50k",
  new_str: "Budget: $45k"
})
// File content updated atomically
```

---

### Tool 4: insert

**Purpose:** Insert text at a specific line number

**Input Schema:**
```typescript
{
  path: string,          // Relative path within base directory
  insert_line: number,   // Line number (1-indexed)
  new_str: string        // Text to insert
}
```

**Parameters:**
- `path` (string): Relative path within base directory
  - Constraints: File must exist
  - Example: `"notes/tasks.md"`
- `insert_line` (number): Line number where to insert
  - Constraints: 1-indexed, range [1, total_lines + 1]
  - Example: `5` inserts before current line 5
  - Behavior: Existing content pushed down
- `new_str` (string): Text to insert
  - Example: `"- New task item"`
  - Behavior: Inserted as provided (caller must include trailing newline if desired)
  - Semantics: If new_str ends with `\n`, it becomes a complete line; otherwise it continues on same line as next content

**Returns:**
- void (success) or throws error

**Errors:**
- Error code `file_not_found`: "File not found: {path}"
- Error code `invalid_line_number`: "Line number {N} out of range (1-{max})"
- Error code `binary_file`: "Cannot perform text operation on binary file"
- Error code `path_security`: "Path escapes base directory" (including symlink escapes)

**Preconditions:**
- File must exist at path
- File must be valid UTF-8 text (not binary)
- insert_line must be in valid range [1, total_lines + 1]

**Postconditions:**
- new_str inserted at specified line
- Existing content at and after insert_line shifted down
- Operation is atomic (complete or original content remains)
- Subsequent view() returns modified content

**Example Usage:**
```typescript
await insert({
  path: "notes/tasks.md",
  insert_line: 3,
  new_str: "- Added new task"
})
// Line inserted, existing lines 3+ shifted down
```

---

### Tool 5: delete

**Purpose:** Delete a file or empty directory

**Input Schema:**
```typescript
{
  path: string  // Relative path within base directory
}
```

**Parameters:**
- `path` (string): Relative path within base directory
  - Constraints: Path must exist
  - Example: `"archive/old-file.md"`
  - Behavior: Deletes files or truly empty directories only

**Returns:**
- void (success) or throws error

**Errors:**
- Error code `file_not_found`: "File not found: {path}"
- Error code `directory_not_empty`: "Directory not empty: {path}"
- Error code `path_security`: "Path escapes base directory" (including symlink escapes)
- Error code `permission_denied`: "Permission denied: {path}"

**Preconditions:**
- Path must exist
- If directory, must be truly empty (no entries at all, including hidden files)

**Postconditions:**
- File or directory removed from filesystem
- Operation is atomic (exists or fully removed, no partial state)
- Subsequent view() on path throws `file_not_found`
- Parent directory remains (not removed even if empty)

**Example Usage:**
```typescript
await delete({ path: "archive/old-project.md" })
// File removed from filesystem
```

---

### Tool 6: rename

**Purpose:** Rename or move a file/directory

**Input Schema:**
```typescript
{
  old_path: string,  // Current relative path
  new_path: string   // New relative path
}
```

**Parameters:**
- `old_path` (string): Current relative path
  - Constraints: Must exist
  - Example: `"drafts/note.md"`
- `new_path` (string): New relative path
  - Constraints: Must not exist, within base directory
  - Example: `"archive/2025/note.md"`
  - Auto-creation: Parent directories created automatically

**Returns:**
- void (success) or throws error

**Errors:**
- Error code `file_not_found`: "File not found: {old_path}"
- Error code `file_exists`: "File already exists: {new_path}"
- Error code `path_security`: "Path escapes base directory" (including symlink escapes)
- Error code `permission_denied`: "Permission denied"

**Preconditions:**
- old_path must exist
- new_path must not exist
- Both paths within base directory (after symlink resolution)
- Base directory resides on single filesystem/volume (for atomic rename)

**Postconditions:**
- File/directory moved from old_path to new_path
- Parent directories for new_path created if needed
- Operation is atomic (appears at old location or new location, never both or neither)
- Subsequent view(old_path) throws `file_not_found`
- Subsequent view(new_path) returns the file/directory content

**Example Usage:**
```typescript
await rename({
  old_path: "drafts/proposal.md",
  new_path: "archive/2025/proposal.md"
})
// File moved, parent directories created
```

---

### TypeScript Implementation Interface

```typescript
interface FileStorage {
  /**
   * View file content or list directory contents.
   * Symlinks followed but must resolve within base directory.
   */
  view(path: string): Promise<FileContent>

  /**
   * Create new file with content.
   * Parent directories created automatically.
   */
  create(path: string, content: string, encoding: 'utf-8' | 'base64'): Promise<void>

  /**
   * Replace string in file.
   * String must appear exactly once.
   */
  str_replace(path: string, old_str: string, new_str: string): Promise<void>

  /**
   * Insert text at line number (1-indexed).
   * Caller includes newline if desired.
   */
  insert(path: string, insert_line: number, new_str: string): Promise<void>

  /**
   * Delete file or truly empty directory.
   * Hidden files count as non-empty.
   */
  delete(path: string): Promise<void>

  /**
   * Rename or move file/directory.
   * Parent directories created automatically.
   */
  rename(old_path: string, new_path: string): Promise<void>
}

type FileContent = {
  type: 'file' | 'directory'
  content?: string           // For files (text or base64)
  encoding?: 'utf-8' | 'base64'  // For files (always present with content)
  entries?: string[]         // For directories (sorted by Unicode code point)
  size?: number              // For files (bytes)
}

type StorageError = {
  code: 'file_not_found' | 'file_exists' | 'path_security' | 'string_not_found' |
        'string_not_unique' | 'binary_file' | 'invalid_line_number' |
        'directory_not_empty' | 'permission_denied' | 'disk_full' | 'invalid_encoding'
  message: string
  path?: string
}
```

---

## Acceptance Criteria

### Happy Path
1. ✓ MCP server starts and connects to Claude Code successfully
2. ✓ All 6 tools (view, create, str_replace, insert, delete, rename) are available and callable
3. ✓ Create → View cycle works (creating a file and immediately viewing it returns exact content)
4. ✓ Text replacement works correctly (str_replace finds unique string and replaces it)
5. ✓ File operations persist across server restarts (files created remain available)

### Error Handling
6. ✓ Create on existing file fails with error code `file_exists` and message "File already exists: {path}"
7. ✓ View non-existent file fails with error code `file_not_found` and message "File not found: {path}"
8. ✓ str_replace on missing string fails with error code `string_not_found` and message "String not found in file"
9. ✓ str_replace on non-unique string fails with error code `string_not_unique` and message "String appears {N} times, must be unique"
10. ✓ Insert with invalid line number fails with error code `invalid_line_number` and message "Line number {N} out of range"
11. ✓ Delete directory with hidden files fails with error code `directory_not_empty` (hidden files count as non-empty)
12. ✓ Path security enforced (paths attempting to escape base directory rejected with error code `path_security`)
13. ✓ Symlink escape blocked (symlinks pointing outside base directory rejected with error code `path_security`)

### Edge Cases
14. ✓ Parent directories auto-created (creating "deep/nested/path/file.txt" creates all parents)
15. ✓ Empty files handled (can create, view, and delete empty files)
16. ✓ Binary files supported for view/create (encoding='base64' works correctly)
17. ✓ Binary files rejected for text operations (str_replace and insert on binary files return error code `binary_file`)
18. ✓ Directory listing sorted by Unicode code point (ascending, case-sensitive)
19. ✓ Trailing slash handling (both "nodes/" and "nodes" work for directory paths)
20. ✓ Rename with path change works (rename can move files between directories, creating parents)
21. ✓ Insert newline semantics (caller controls newline; if new_str ends with \n, complete line; else continues)

### Atomicity/Consistency
22. ✓ Operations are atomic (if operation fails midway, no partial files or corrupt content remains)
23. ✓ View consistency guaranteed (successful view after successful create/str_replace returns current content)
24. ✓ MCP error format consistent (all errors include both `code` and `message` fields)

---

## Scenarios

### Scenario 1: Basic File Creation and Retrieval

**Given:**
- MCP server running with basePath="/tmp/test-storage"
- Directory is empty

**When:**
- Tool call: `create(path: "notes/meeting.md", content: "# Team Meeting\n\nDiscuss Q1 goals", encoding: "utf-8")`
- Tool call: `view(path: "notes/meeting.md")`

**Then:**
- File exists at `/tmp/test-storage/notes/meeting.md`
- view returns: `{ type: 'file', content: '# Team Meeting\n\nDiscuss Q1 goals', encoding: 'utf-8', size: 36 }`
- No errors or warnings

---

### Scenario 2: Text Replacement

**Given:**
- File `/tmp/test-storage/project.md` exists with content:
  ```
  # Project Alpha
  Status: Planning
  Budget: $50k
  ```

**When:**
- Tool call: `str_replace(path: "project.md", old_str: "Status: Planning", new_str: "Status: In Progress")`

**Then:**
- File content is now:
  ```
  # Project Alpha
  Status: In Progress
  Budget: $50k
  ```
- Operation completes successfully
- No temporary files remain

---

### Scenario 3: Duplicate File Creation Fails

**Given:**
- File `/tmp/test-storage/config.json` already exists with content `{"version": 1}`

**When:**
- Tool call: `create(path: "config.json", content: "{}", encoding: "utf-8")`

**Then:**
- Operation fails with error code `file_exists` and message "File already exists: config.json"
- Original file content unchanged (still `{"version": 1}`)
- No new files created

---

### Scenario 4: Deep Path with Auto-Created Directories

**Given:**
- basePath="/tmp/test-storage"
- Directories `nodes/`, `projects/`, `archive/` do not exist

**When:**
- Tool call: `create(path: "nodes/projects/archive/old-project.md", content: "# Archived", encoding: "utf-8")`

**Then:**
- All directories created: `/tmp/test-storage/nodes/projects/archive/`
- File exists at `/tmp/test-storage/nodes/projects/archive/old-project.md`
- File contains "# Archived"

---

### Scenario 5: Directory Listing

**Given:**
- `/tmp/test-storage/nodes/` contains:
  - `proj_003.md`
  - `proj_001.md`
  - `proj_002.md`
  - `.hidden`

**When:**
- Tool call: `view(path: "nodes/")`

**Then:**
- Returns: `{ type: 'directory', entries: ['proj_001.md', 'proj_002.md', 'proj_003.md'] }`
- Entries are sorted by Unicode code point (ascending, case-sensitive)
- Hidden file `.hidden` is excluded from listing

---

### Scenario 6: Path Security Enforcement

**Given:**
- basePath="/tmp/test-storage"
- File `/etc/passwd` exists on system

**When:**
- Tool call: `view(path: "../../../etc/passwd")`

**Then:**
- Operation fails with error code `path_security` and message "Path escapes base directory"
- No file access occurs outside base directory
- System files remain untouched

---

### Scenario 7: Non-Unique String Replacement Fails

**Given:**
- File `/tmp/test-storage/notes.md` contains:
  ```
  TODO: finish this
  TODO: review that
  ```

**When:**
- Tool call: `str_replace(path: "notes.md", old_str: "TODO", new_str: "DONE")`

**Then:**
- Operation fails with error code `string_not_unique` and message "String appears 2 times, must be unique"
- File content unchanged

---

### Scenario 8: Symlink Escape Prevention

**Given:**
- basePath="/tmp/test-storage"
- Symlink `/tmp/test-storage/malicious-link` points to `/etc/passwd`

**When:**
- Tool call: `view(path: "malicious-link")`

**Then:**
- Operation fails with error code `path_security` and message "Path escapes base directory"
- Symlink resolved via realpath, escape detected
- No access to `/etc/passwd` occurs

---

### Scenario 9: Directory Deletion with Hidden Files

**Given:**
- Directory `/tmp/test-storage/temp/` contains only `.gitkeep` file

**When:**
- Tool call: `delete(path: "temp/")`

**Then:**
- Operation fails with error code `directory_not_empty` and message "Directory not empty: temp/"
- Directory and `.gitkeep` remain unchanged
- Hidden files count as non-empty

---

## Data Structures

### FileContent

**Type:** TypeScript Type / JSON Object

**Structure:**
```typescript
{
  type: 'file' | 'directory',
  content?: string,                  // Present for files only (text or base64)
  encoding?: 'utf-8' | 'base64',    // Present for files only (always with content)
  entries?: string[],                // Present for directories only
  size?: number                      // Present for files only (bytes)
}
```

**Invariants:**
- `type` is always either 'file' or 'directory'
- If `type` is 'file': `content`, `encoding`, and `size` are present; `entries` is undefined
- If `type` is 'directory': `entries` is present (possibly empty array); `content`, `encoding`, and `size` are undefined
- `encoding` and `content` always appear together (both present or both absent)
- `entries` array is always sorted by Unicode code point (ascending, case-sensitive)
- `entries` never contains hidden files (starting with '.'), '.', or '..'
- `size` is non-negative integer representing bytes (original file size, not base64 string length)

**Example (text file):**
```typescript
{
  type: 'file',
  content: '# Project\n\nDetails here',
  encoding: 'utf-8',
  size: 26
}
```

**Example (binary file):**
```typescript
{
  type: 'file',
  content: 'iVBORw0KGgoAAAANSUhEUg...',
  encoding: 'base64',
  size: 2048
}
```

**Example (directory):**
```typescript
{
  type: 'directory',
  entries: ['file1.md', 'file2.md', 'subdir']
}
```

---

### ServerConfiguration

**Type:** Environment Variables / JSON Config

**Structure:**
```typescript
{
  basePath: string  // Absolute path to storage root directory
}
```

**Invariants:**
- `basePath` must be an absolute path
- `basePath` directory must exist or be creatable
- `basePath` must be writable by server process
- All file operations scoped within `basePath`

**Example:**
```typescript
{
  basePath: '/Users/username/.gtd-storage'
}
```

---

## Dependencies

### External Dependencies
- **@modelcontextprotocol/sdk** (latest) - MCP SDK for TypeScript server implementation
- **Node.js v18+** - Runtime environment (requires modern fs/promises API)
- **TypeScript** (development) - Type checking and compilation

### Internal Dependencies
- None - this is the foundational layer

### Platform Requirements
- **Claude Code** - Must be compatible with Claude Code's MCP server registration
- **Filesystem access** - Requires read/write permissions to configured base directory
- **Operating System** - Cross-platform (macOS, Linux, Windows via Node.js)

### Assumptions
- Base directory path provided in configuration exists or is creatable
- Server process has appropriate filesystem permissions
- Single-user usage (no concurrent multi-process coordination required)
- Operations are sequential (no simultaneous tool calls on same files)
- Text files are UTF-8 encoded

---

## Constraints and Limitations

### Technical Constraints
- Node.js v18+ required (for stable fs/promises API and fs.realpath)
- Practical file size limit ~100MB per file (Node.js memory constraints)
- No multi-process locking (assumes single server instance)
- Path containment enforced via path normalization and realpath checks (cannot access files outside basePath)
- Symlinks followed but resolved path must remain within basePath
- basePath must reside on single filesystem/volume (for atomic rename operations)

### Language/Platform Constraints
- TypeScript/Node.js implementation (MCP SDK standard)
- UTF-8 encoding for text files
- Platform-specific path separators handled by Node.js path module

### Known Limitations
- No file versioning or history
- No undo capability for destructive operations (delete, rename, str_replace)
- No concurrent operation coordination (assumes sequential usage)
- No caching (direct filesystem operations each time)
- Binary file detection is UTF-8 decode attempt (not MIME type inspection)
- Directory deletion requires truly empty directory (hidden files count as non-empty)
- Rename operations require source and destination on same filesystem for atomicity

### Out of Scope
- Alternative storage backends (cloud, database) - local filesystem only
- Caching layer - direct operations
- Batch operations - one operation per tool call
- File watching/change notifications
- Authentication/authorization beyond path containment

---

## Implementation Notes

### Suggested Approach

**MCP Server Setup:**
1. Use @modelcontextprotocol/sdk to create MCP server
2. Define 6 tools with schemas matching Interface Contract
3. Implement tool handlers that delegate to FileStorage class
4. Handle MCP error responses with descriptive messages

**FileStorage Implementation:**
1. Use Node.js fs/promises for all filesystem operations
2. Implement path validation/normalization in private method
3. Use atomic write pattern (temp file + rename) for create/str_replace/insert
4. Handle both text and binary content appropriately

**Path Security:**
1. Reject absolute paths immediately
2. Use path.resolve() to normalize paths
3. Use fs.realpath() to resolve symlinks
4. Verify real path is within base directory using path.relative()
5. Do validation before any filesystem access

Example implementation:
```typescript
async _validatePath(userPath: string): Promise<string> {
  // Reject absolute paths
  if (path.isAbsolute(userPath)) {
    throw new PathSecurityError('Absolute paths not allowed');
  }

  // Resolve relative to base
  const resolved = path.resolve(this.basePath, userPath);

  // Get real path (follows symlinks)
  const realPath = await fs.realpath(resolved);

  // Check containment
  const relative = path.relative(this.basePath, realPath);
  if (relative.startsWith('..') || path.isAbsolute(relative)) {
    throw new PathSecurityError('Path escapes base directory');
  }

  return realPath;
}
```

**Atomicity:**
1. For write operations, use temp file approach: write to `{file}.tmp`, then rename
2. If operation fails, clean up temp file in error handler
3. Node.fs.rename() is atomic on POSIX systems

### Error Handling Strategy

**Error Categories:**
1. **Path errors**: Validate path first, reject before filesystem access
2. **Not found errors**: Let fs operations throw, catch and format message
3. **Already exists errors**: Check with fs.access() before create
4. **String operation errors**: Read file, validate string presence/uniqueness, then write

**MCP Error Format:**
All tool errors must return MCP-compliant error objects:
```typescript
{
  code: 'file_not_found' | 'file_exists' | 'path_security' | 'string_not_found' |
        'string_not_unique' | 'binary_file' | 'invalid_line_number' |
        'directory_not_empty' | 'permission_denied' | 'disk_full' | 'invalid_encoding',
  message: 'Human-readable description',
  path?: 'file/path.txt'  // Include when relevant
}
```

Ensure consistency: every error has both `code` and `message` fields.

### Performance Considerations

**Not critical for MVP**, but keep in mind:
- Read entire file into memory for str_replace/insert (acceptable for typical files < 10MB)
- Directory listings could be slow for huge directories (thousands of files) - acceptable for MVP
- No caching needed - filesystem cache at OS level is sufficient

### Testing Strategy

**Unit Tests:**
- Use temporary directories (Node.js fs.mkdtempSync)
- Clean up after each test
- Test all acceptance criteria
- Use fixtures for binary files

**Integration Tests:**
- Start actual MCP server
- Send tool requests via MCP protocol
- Verify responses and filesystem state

**Manual Verification:**
- Register in Claude Code
- Ask Claude to create/view/modify files
- Confirm tools appear and work

---

## Open Questions

- [ ] ~~Should we include end-to-end tests with Claude Code, or is manual verification sufficient?~~ **Resolved:** Manual verification sufficient for MVP (per conversation)
- [ ] ~~Performance requirements for large files?~~ **Resolved:** No specific performance tests for MVP (per conversation)

---

## References

- **VISION.md** - Section "Technical Approach" explains memory architecture foundation
- **SCOPE.md** - Section "Technical Requirements" → "Memory Architecture (Two-Layer)" shows file-storage as foundation
- **ROADMAP.md** - Phase 1, Feature 1: File-Storage-Backend Integration
- **Anthropic Memory Tool Documentation** - https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool
- **MCP Specification** - Model Context Protocol for server implementation
- **Python Spec Reference** - src/file-storage-backend/specs/todo/file_storage_backend_interface.md (non-normative inspiration; this TypeScript/Node.js spec is authoritative for MVP)

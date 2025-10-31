import type { GraphStorageGateway } from '../../src/storageGateway.js'

/**
 * In-memory GraphStorageGateway test double.
 * Simulates a contained filesystem rooted at a virtual base path.
 */
export class FakeStorage implements GraphStorageGateway {
  private files = new Map<string, Buffer>()
  private dirs = new Set<string>(['']) // '' represents root

  async ensureDirectory(relativePath: string): Promise<void> {
    const norm = this.normalizeDir(relativePath)
    // Ensure all parent segments exist
    const parts = norm.split('/').filter(Boolean)
    let current = ''
    for (const part of parts) {
      current = current ? `${current}/${part}` : part
      this.dirs.add(current)
    }
  }

  async pathExists(relativePath: string): Promise<boolean> {
    const file = this.normalizeFile(relativePath)
    const dir = this.normalizeDir(relativePath)
    return this.files.has(file) || this.dirs.has(dir)
  }

  async readText(relativePath: string): Promise<string> {
    const path = this.normalizeFile(relativePath)
    const buf = this.files.get(path)
    if (!buf) throw new Error(`ENOENT: no such file, open '${path}'`)
    return buf.toString('utf-8')
  }

  async readBinary(relativePath: string): Promise<Buffer> {
    const path = this.normalizeFile(relativePath)
    const buf = this.files.get(path)
    if (!buf) throw new Error(`ENOENT: no such file, open '${path}'`)
    return Buffer.from(buf)
  }

  async writeText(relativePath: string, content: string): Promise<void> {
    const path = this.normalizeFile(relativePath)
    await this.ensureParentDir(path)
    this.files.set(path, Buffer.from(content, 'utf-8'))
  }

  async writeBinary(relativePath: string, content: Buffer): Promise<void> {
    const path = this.normalizeFile(relativePath)
    await this.ensureParentDir(path)
    this.files.set(path, Buffer.from(content))
  }

  async deletePath(relativePath: string): Promise<void> {
    const path = this.normalizeFile(relativePath)
    if (this.files.has(path)) {
      this.files.delete(path)
      return
    }
    // Directory delete (must be empty)
    const dir = this.normalizeDir(relativePath)
    if (!this.dirs.has(dir)) throw new Error(`ENOENT: no such file or directory, unlink '${relativePath}'`)
    // Check emptiness
    for (const f of this.files.keys()) {
      if (f.startsWith(dir + '/')) throw new Error(`ENOTEMPTY: directory not empty, rmdir '${relativePath}'`)
    }
    for (const d of this.dirs) {
      if (d !== dir && d.startsWith(dir + '/')) throw new Error(`ENOTEMPTY: directory not empty, rmdir '${relativePath}'`)
    }
    if (dir !== '') this.dirs.delete(dir)
  }

  async listDirectory(relativePath: string): Promise<string[]> {
    const dir = this.normalizeDir(relativePath)
    if (!this.dirs.has(dir)) throw new Error(`ENOENT: no such directory, scandir '${relativePath}'`)
    const entries = new Set<string>()

    // Files directly under dir
    for (const f of this.files.keys()) {
      const parent = this.parentDir(f)
      if (parent === dir) entries.add(this.basename(f))
    }
    // Dirs directly under dir
    for (const d of this.dirs) {
      const parent = this.parentDir(d)
      if (parent === dir && d !== dir && d !== '') entries.add(this.basename(d))
    }
    return Array.from(entries).sort()
  }

  // Helpers
  private normalizeFile(p: string): string {
    return p.replace(/^\/+|\/+$/g, '')
  }
  private normalizeDir(p: string): string {
    return p.replace(/^\/+|\/+$/g, '')
  }
  private parentDir(p: string): string {
    const norm = this.normalizeFile(p)
    const idx = norm.lastIndexOf('/')
    return idx === -1 ? '' : norm.slice(0, idx)
  }
  private basename(p: string): string {
    const norm = this.normalizeFile(p)
    const idx = norm.lastIndexOf('/')
    return idx === -1 ? norm : norm.slice(idx + 1)
  }
  private async ensureParentDir(filePath: string): Promise<void> {
    const parent = this.parentDir(filePath)
    if (parent && !this.dirs.has(parent)) await this.ensureDirectory(parent)
  }
}


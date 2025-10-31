/**
 * Tests for: MemoryGraph node lifecycle, queries (subset)
 * Feature: Graph Memory Core (MCP)
 * Spec: specs/doing/graph-memory-core.md
 *
 * Tests written: 2025-10-31
 * Test Writer: OpenAI Codex (Codex CLI)
 *
 * Coverage targets:
 * - Line coverage: >80%
 * - Branch coverage: >70%
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { MemoryGraph } from '../../src/memoryGraph.js'
import { FakeStorage } from '../helpers/fakeStorage.js'
import type { GraphMemoryServerConfig } from '../../src/types.js'
import { InvalidEncodingError, NodeNotFoundError, InvalidNodeTypeError, FileCreationFailedError } from '../../src/errors.js'

class FaultyStorage extends FakeStorage {
  private failWritePrefixes: string[] = []
  addFailWritePrefix(prefix: string) { this.failWritePrefixes.push(prefix.replace(/^\/+|\/+$/g, '')) }
  override async writeText(relativePath: string, content: string): Promise<void> {
    const norm = relativePath.replace(/^\/+|\/+$/g, '')
    if (this.failWritePrefixes.some(p => norm.startsWith(p))) {
      throw new Error(`Injected write failure for ${norm}`)
    }
    return super.writeText(relativePath, content)
  }
}

describe('MemoryGraph - Node Lifecycle (Happy Path + Errors)', () => {
  let storage: FakeStorage
  let config: GraphMemoryServerConfig

  beforeEach(() => {
    storage = new FakeStorage()
    config = { basePath: '/virtual' }
  })

  it('creates ontology, creates node, reads metadata and content (AC1)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)

    await graph.createOntology({
      node_types: ['Project'],
      connection_types: []
    })

    const { node_id } = await graph.createNode({
      type: 'Project',
      content: '# Kitchen Renovation\n\nBudget: $50k',
      encoding: 'utf-8',
      format: 'markdown',
      properties: { status: 'active' }
    })

    const meta = await graph.getNode({ node_id })
    expect(meta.id).toBe(node_id)
    expect(meta.type).toBe('Project')
    expect(meta.properties).toEqual({ status: 'active' })
    expect(typeof meta.created).toBe('string')
    expect(typeof meta.modified).toBe('string')
    expect(meta.content_format).toBe('markdown')

    const content = await graph.getNodeContent({ node_id })
    expect(content.content).toContain('# Kitchen Renovation')
  })

  it('update_node requires encoding when content is provided (AC4/Tool 4)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({ node_types: ['Project'], connection_types: [] })
    const { node_id } = await graph.createNode({
      type: 'Project',
      content: 'original',
      encoding: 'utf-8',
      format: 'markdown'
    })

    await expect(
      graph.updateNode({ node_id, content: 'updated-without-encoding' })
    ).rejects.toThrow(InvalidEncodingError)
  })

  it('get_node for non-existent ID throws NODE_NOT_FOUND (AC6)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await expect(graph.getNode({ node_id: 'missing' })).rejects.toThrow(NodeNotFoundError)
  })

  it('update_node with non-existent ID throws NODE_NOT_FOUND (AC6)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await expect(graph.updateNode({ node_id: 'missing', properties: { a: 1 } })).rejects.toThrow(NodeNotFoundError)
  })

  it('delete_node with non-existent ID throws NODE_NOT_FOUND (AC6)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await expect(graph.deleteNode({ node_id: 'missing' })).rejects.toThrow(NodeNotFoundError)
  })

  it('create_node with invalid type raises INVALID_NODE_TYPE (AC8)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    // No ontology yet, so first create ontology with one type
    await graph.createOntology({ node_types: ['Project'], connection_types: [] })
    await expect(
      graph.createNode({ type: 'Unknown', content: 'x', encoding: 'utf-8', format: 'txt' })
    ).rejects.toThrow(InvalidNodeTypeError)
  })

  it('create node with empty content and empty properties; query_nodes with no filters returns all (AC12)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({ node_types: ['Note'], connection_types: [] })
    const n1 = await graph.createNode({ type: 'Note', content: '', encoding: 'utf-8', format: 'txt', properties: {} })
    const n2 = await graph.createNode({ type: 'Note', content: 'hello', encoding: 'utf-8', format: 'txt' })
    const qAll = await graph.queryNodes({})
    expect(new Set(qAll.node_ids)).toEqual(new Set([n1.node_id, n2.node_id]))
  })

  it('encoding controls file extension .txt vs .bin and changes on update (spec rule)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({ node_types: ['Blob'], connection_types: [] })
    const text = await graph.createNode({ type: 'Blob', content: 't', encoding: 'utf-8', format: 'markdown' })
    const bin = await graph.createNode({ type: 'Blob', content: Buffer.from('b').toString('base64'), encoding: 'base64', format: 'pdf' })

    const entries = await storage.listDirectory('_content/nodes')
    expect(entries).toContain(`${text.node_id}.txt`)
    expect(entries).toContain(`${bin.node_id}.bin`)

    // Change encoding via update with new content
    await graph.updateNode({ node_id: text.node_id, content: Buffer.from('t2').toString('base64'), encoding: 'base64', format: 'pdf' })
    const entries2 = await storage.listDirectory('_content/nodes')
    expect(entries2).toContain(`${text.node_id}.bin`)
  })

  it('registry remains consistent after failed operation (AC11)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({ node_types: ['Note'], connection_types: [] })
    await expect(
      graph.createNode({ type: 'UnknownType', content: 'x', encoding: 'utf-8', format: 'txt' })
    ).rejects.toThrow()
    const ok = await graph.createNode({ type: 'Note', content: 'ok', encoding: 'utf-8', format: 'txt' })
    const meta = await graph.getNode({ node_id: ok.node_id })
    expect(meta.id).toBe(ok.node_id)
  })

  it('atomicity: file write failure leaves no partial files (AC19, AC11)', async () => {
    const faulty = new FaultyStorage()
    const graph = await MemoryGraph.initialize(config, faulty)
    await graph.createOntology({ node_types: ['Note'], connection_types: [] })
    // Inject failure for the expected content path of first node (unknown ID). We simulate by failing any write under nodes dir
    faulty.addFailWritePrefix('_content/nodes')
    await expect(
      graph.createNode({ type: 'Note', content: 'abc', encoding: 'utf-8', format: 'txt' })
    ).rejects.toThrow(FileCreationFailedError)
    // No registry.json should exist; no content files should be present
    const nodesDirExists = await faulty.pathExists('_content/nodes')
    if (nodesDirExists) {
      const list = await faulty.listDirectory('_content/nodes')
      expect(list.length).toBe(0)
    }
  })
})

/**
 * Tests for: MemoryGraph cascade delete semantics
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
import { ConnectionNotFoundError, NodeNotFoundError } from '../../src/errors.js'

describe('MemoryGraph - Cascade Delete (AC5, AC11, AC19)', () => {
  let storage: FakeStorage
  let config: GraphMemoryServerConfig

  beforeEach(() => {
    storage = new FakeStorage()
    config = { basePath: '/virtual' }
  })

  it('deleting node removes connected connections but preserves other nodes (AC5)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({
      node_types: ['Project', 'Action'],
      connection_types: [
        { name: 'NextAction', from_types: ['Project'], to_types: ['Action'] },
        { name: 'DependsOn', from_types: ['Action'], to_types: ['Action'] }
      ]
    })

    const p = await graph.createNode({ type: 'Project', content: 'P', encoding: 'utf-8', format: 'txt' })
    const a1 = await graph.createNode({ type: 'Action', content: 'A1', encoding: 'utf-8', format: 'txt' })
    const a2 = await graph.createNode({ type: 'Action', content: 'A2', encoding: 'utf-8', format: 'txt' })
    const a3 = await graph.createNode({ type: 'Action', content: 'A3', encoding: 'utf-8', format: 'txt' })

    const c1 = await graph.createConnection({ type: 'NextAction', from_node_id: p.node_id, to_node_id: a1.node_id })
    const c2 = await graph.createConnection({ type: 'NextAction', from_node_id: p.node_id, to_node_id: a2.node_id })
    const c3 = await graph.createConnection({ type: 'DependsOn', from_node_id: a2.node_id, to_node_id: a3.node_id })

    await graph.deleteNode({ node_id: p.node_id })

    await expect(graph.getNode({ node_id: p.node_id })).rejects.toThrow(NodeNotFoundError)
    await expect(graph.getConnection({ connection_id: c1.connection_id })).rejects.toThrow(ConnectionNotFoundError)
    await expect(graph.getConnection({ connection_id: c2.connection_id })).rejects.toThrow(ConnectionNotFoundError)

    // Unrelated connection remains
    const c3meta = await graph.getConnection({ connection_id: c3.connection_id })
    expect(c3meta.id).toBe(c3.connection_id)
    // Target nodes still exist
    const a1meta = await graph.getNode({ node_id: a1.node_id })
    expect(a1meta.id).toBe(a1.node_id)
  })

  it('deleting node removes its content file (AC19 deletion atomicity)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({ node_types: ['Doc'], connection_types: [] })
    const n = await graph.createNode({ type: 'Doc', content: 'body', encoding: 'utf-8', format: 'txt' })
    // Sanity: file exists prior to delete
    const pre = await storage.pathExists(`_content/nodes/${n.node_id}.txt`)
    expect(pre).toBe(true)
    await graph.deleteNode({ node_id: n.node_id })
    const exists = await storage.pathExists(`_content/nodes/${n.node_id}.txt`)
    expect(exists).toBe(false)
  })
})

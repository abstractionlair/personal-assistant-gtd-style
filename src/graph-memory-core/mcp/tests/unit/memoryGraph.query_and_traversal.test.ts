/**
 * Tests for: MemoryGraph queries, traversal, and content search
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

describe('MemoryGraph - Queries, Traversal, and Search (AC3, AC16, AC18)', () => {
  let storage: FakeStorage
  let config: GraphMemoryServerConfig

  beforeEach(() => {
    storage = new FakeStorage()
    config = { basePath: '/virtual' }
  })

  it('query_nodes filters by type and AND-properties (AC3, AC15)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({ node_types: ['Action'], connection_types: [] })

    const n1 = await graph.createNode({ type: 'Action', content: 'A1', encoding: 'utf-8', format: 'txt', properties: { status: 'next', context: 'phone' } })
    await graph.createNode({ type: 'Action', content: 'A2', encoding: 'utf-8', format: 'txt', properties: { status: 'next', context: 'computer' } })
    const n3 = await graph.createNode({ type: 'Action', content: 'A3', encoding: 'utf-8', format: 'txt', properties: { status: 'waiting', context: 'phone' } })
    const n4 = await graph.createNode({ type: 'Action', content: 'A4', encoding: 'utf-8', format: 'txt', properties: { status: 'next', context: 'phone', priority: 'high' } })

    const res = await graph.queryNodes({ type: 'Action', properties: { status: 'next', context: 'phone' } })
    expect(new Set(res.node_ids)).toEqual(new Set([n1.node_id, n4.node_id]))
    expect(res.node_ids).not.toContain(n3.node_id)
  })

  it('get_connected_nodes respects direction and optional type filter (AC3, AC18)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({
      node_types: ['Project', 'Action'],
      connection_types: [{ name: 'NextAction', from_types: ['Project'], to_types: ['Action'] }]
    })
    const p = await graph.createNode({ type: 'Project', content: 'P', encoding: 'utf-8', format: 'txt' })
    const a1 = await graph.createNode({ type: 'Action', content: 'A1', encoding: 'utf-8', format: 'txt' })
    const a2 = await graph.createNode({ type: 'Action', content: 'A2', encoding: 'utf-8', format: 'txt' })

    await graph.createConnection({ type: 'NextAction', from_node_id: p.node_id, to_node_id: a1.node_id })
    await graph.createConnection({ type: 'NextAction', from_node_id: p.node_id, to_node_id: a2.node_id })

    const out = await graph.getConnectedNodes({ node_id: p.node_id, connection_type: 'NextAction', direction: 'out' })
    expect(new Set(out.node_ids)).toEqual(new Set([a1.node_id, a2.node_id]))

    const none = await graph.getConnectedNodes({ node_id: a1.node_id, connection_type: 'NextAction', direction: 'out' })
    expect(none.node_ids).toEqual([])

    const incoming = await graph.getConnectedNodes({ node_id: a1.node_id, connection_type: 'NextAction', direction: 'in' })
    expect(incoming.node_ids).toEqual([p.node_id])

    const both = await graph.getConnectedNodes({ node_id: p.node_id, connection_type: 'NextAction', direction: 'both' })
    expect(new Set(both.node_ids)).toEqual(new Set([a1.node_id, a2.node_id]))
  })

  it('search_content is case-insensitive and ignores binary nodes (AC16)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({ node_types: ['Project', 'Action'], connection_types: [] })
    const p1 = await graph.createNode({ type: 'Project', content: '# Kitchen Renovation\n\nModern farmhouse style', encoding: 'utf-8', format: 'markdown' })
    const p2 = await graph.createNode({ type: 'Project', content: '# Bathroom Remodel\n\nFarmhouse sink and fixtures', encoding: 'utf-8', format: 'markdown' })
    const a1 = await graph.createNode({ type: 'Action', content: '# Research farmhouse sinks', encoding: 'utf-8', format: 'markdown' })
    await graph.createNode({ type: 'Action', content: '# Call plumber', encoding: 'utf-8', format: 'markdown' })
    // Binary node should be ignored in text search
    await graph.createNode({ type: 'Project', content: Buffer.from('farmhouse').toString('base64'), encoding: 'base64', format: 'pdf' })

    const res = await graph.searchContent({ query: 'farmhouse', limit: 10 })
    expect(new Set(res.node_ids)).toEqual(new Set([p1.node_id, p2.node_id, a1.node_id]))

    const onlyProjects = await graph.searchContent({ query: 'farmhouse', node_type: 'Project', limit: 10 })
    expect(new Set(onlyProjects.node_ids)).toEqual(new Set([p1.node_id, p2.node_id]))

    const limited = await graph.searchContent({ query: 'farmhouse', limit: 2 })
    expect(limited.node_ids.length).toBe(2)

    const none = await graph.searchContent({ query: 'no-such-string', limit: 10 })
    expect(none.node_ids).toEqual([])
  })

  it('query_nodes with empty properties matches all nodes of type (AC15)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({ node_types: ['Action'], connection_types: [] })
    const n1 = await graph.createNode({ type: 'Action', content: 'A1', encoding: 'utf-8', format: 'txt', properties: { a: 1 } })
    const n2 = await graph.createNode({ type: 'Action', content: 'A2', encoding: 'utf-8', format: 'txt', properties: { b: 2 } })
    const res = await graph.queryNodes({ type: 'Action', properties: {} })
    expect(new Set(res.node_ids)).toEqual(new Set([n1.node_id, n2.node_id]))
  })

  it('isolated node returns empty traversal and can be deleted (AC13)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({ node_types: ['Solo'], connection_types: [] })
    const solo = await graph.createNode({ type: 'Solo', content: 'S', encoding: 'utf-8', format: 'txt' })
    const connected = await graph.getConnectedNodes({ node_id: solo.node_id, direction: 'both' })
    expect(connected.node_ids).toEqual([])
    await graph.deleteNode({ node_id: solo.node_id })
    // If delete succeeded, querying connections remains empty and no exceptions thrown above
    const after = await graph.queryNodes({})
    expect(after.node_ids).not.toContain(solo.node_id)
  })
})

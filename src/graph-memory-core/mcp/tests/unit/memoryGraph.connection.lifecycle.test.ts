/**
 * Tests for: MemoryGraph connection lifecycle, queries
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
import { InvalidTopologyError, InvalidConnectionTypeError, NodeNotFoundError, ConnectionNotFoundError, RequiredPropertyMissingError } from '../../src/errors.js'

describe('MemoryGraph - Connection Lifecycle (AC2, AC7, AC8)', () => {
  let storage: FakeStorage
  let config: GraphMemoryServerConfig

  beforeEach(() => {
    storage = new FakeStorage()
    config = { basePath: '/virtual' }
  })

  it('creates connection between nodes and retrieves metadata (AC2)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({
      node_types: ['Project', 'Action'],
      connection_types: [
        { name: 'NextAction', from_types: ['Project'], to_types: ['Action'] }
      ]
    })

    const p = await graph.createNode({ type: 'Project', content: 'P', encoding: 'utf-8', format: 'txt' })
    const a = await graph.createNode({ type: 'Action', content: 'A', encoding: 'utf-8', format: 'txt' })

    const { connection_id } = await graph.createConnection({
      type: 'NextAction',
      from_node_id: p.node_id,
      to_node_id: a.node_id,
      properties: { priority: 'high' }
    })

    const meta = await graph.getConnection({ connection_id })
    expect(meta.id).toBe(connection_id)
    expect(meta.type).toBe('NextAction')
    expect(meta.from_node_id).toBe(p.node_id)
    expect(meta.to_node_id).toBe(a.node_id)
    expect(meta.properties).toEqual({ priority: 'high' })
    expect(meta.has_content).toBe(false)
  })

  it('rejects invalid connection type with INVALID_CONNECTION_TYPE (AC7)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({ node_types: ['Project', 'Action'], connection_types: [] })
    const p = await graph.createNode({ type: 'Project', content: 'P', encoding: 'utf-8', format: 'txt' })
    const a = await graph.createNode({ type: 'Action', content: 'A', encoding: 'utf-8', format: 'txt' })

    await expect(
      graph.createConnection({ type: 'NextAction', from_node_id: p.node_id, to_node_id: a.node_id })
    ).rejects.toThrow(InvalidConnectionTypeError)
  })

  it('rejects incompatible topology with INVALID_TOPOLOGY (AC8)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({
      node_types: ['Project', 'Action', 'Person'],
      connection_types: [{ name: 'NextAction', from_types: ['Project'], to_types: ['Action'] }]
    })
    const p = await graph.createNode({ type: 'Project', content: 'P', encoding: 'utf-8', format: 'txt' })
    const person = await graph.createNode({ type: 'Person', content: 'X', encoding: 'utf-8', format: 'txt' })

    await expect(
      graph.createConnection({ type: 'NextAction', from_node_id: p.node_id, to_node_id: person.node_id })
    ).rejects.toThrow(InvalidTopologyError)

    // AC8 requires the error message to include allowed targets.
    try {
      await graph.createConnection({ type: 'NextAction', from_node_id: p.node_id, to_node_id: person.node_id })
    } catch (err: any) {
      expect(String(err.message)).toMatch(/Valid targets?:\s*\[Action\]/)
      // If details are provided in implementation, the following would be ideal:
      // expect(err.details?.allowed_to_types).toContain('Action')
    }
  })

  it('rejects connection creation when endpoint node missing (AC7)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({
      node_types: ['Project', 'Action'],
      connection_types: [{ name: 'NextAction', from_types: ['Project'], to_types: ['Action'] }]
    })
    const p = await graph.createNode({ type: 'Project', content: 'P', encoding: 'utf-8', format: 'txt' })

    await expect(
      graph.createConnection({ type: 'NextAction', from_node_id: p.node_id, to_node_id: 'missing' })
    ).rejects.toThrow(NodeNotFoundError)
  })

  it('get_connection with non-existent ID throws CONNECTION_NOT_FOUND (AC7)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await expect(graph.getConnection({ connection_id: 'missing' })).rejects.toThrow(ConnectionNotFoundError)
  })

  it('required_properties enforced on create_connection (AC9)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({
      node_types: ['Action', 'Person'],
      connection_types: [
        { name: 'WaitingFor', from_types: ['Action'], to_types: ['Person'], required_properties: ['since', 'follow_up_date'] }
      ]
    })
    const a = await graph.createNode({ type: 'Action', content: 'A', encoding: 'utf-8', format: 'txt' })
    const p = await graph.createNode({ type: 'Person', content: 'P', encoding: 'utf-8', format: 'txt' })

    await expect(
      graph.createConnection({ type: 'WaitingFor', from_node_id: a.node_id, to_node_id: p.node_id, properties: { since: '2025-10-15' } })
    ).rejects.toThrow(RequiredPropertyMissingError)

    const ok = await graph.createConnection({ type: 'WaitingFor', from_node_id: a.node_id, to_node_id: p.node_id, properties: { since: '2025-10-15', follow_up_date: '2025-11-05' } })
    const meta = await graph.getConnection({ connection_id: ok.connection_id })
    expect(meta.type).toBe('WaitingFor')
  })

  it('query_connections filters by from/to/type (AC3)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({
      node_types: ['N'],
      connection_types: [ { name: 'T1', from_types: ['N'], to_types: ['N'] }, { name: 'T2', from_types: ['N'], to_types: ['N'] } ]
    })
    const n1 = await graph.createNode({ type: 'N', content: '1', encoding: 'utf-8', format: 'txt' })
    const n2 = await graph.createNode({ type: 'N', content: '2', encoding: 'utf-8', format: 'txt' })
    const n3 = await graph.createNode({ type: 'N', content: '3', encoding: 'utf-8', format: 'txt' })

    const c12_t1 = await graph.createConnection({ type: 'T1', from_node_id: n1.node_id, to_node_id: n2.node_id })
    await graph.createConnection({ type: 'T2', from_node_id: n1.node_id, to_node_id: n2.node_id })
    await graph.createConnection({ type: 'T1', from_node_id: n2.node_id, to_node_id: n3.node_id })

    const byFrom = await graph.queryConnections({ from_node_id: n1.node_id })
    expect(new Set(byFrom.connection_ids)).toContain(c12_t1.connection_id)

    const byFromTo = await graph.queryConnections({ from_node_id: n1.node_id, to_node_id: n2.node_id })
    expect(byFromTo.connection_ids.length).toBe(2)

    const byType = await graph.queryConnections({ type: 'T1' })
    expect(byType.connection_ids.length).toBe(2)
  })

  it('multiple connections scenarios and deletion independence (AC14)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({
      node_types: ['N'],
      connection_types: [ { name: 'T1', from_types: ['N'], to_types: ['N'] }, { name: 'T2', from_types: ['N'], to_types: ['N'] } ]
    })
    const a = await graph.createNode({ type: 'N', content: 'a', encoding: 'utf-8', format: 'txt' })
    const b = await graph.createNode({ type: 'N', content: 'b', encoding: 'utf-8', format: 'txt' })

    const c1 = await graph.createConnection({ type: 'T1', from_node_id: a.node_id, to_node_id: b.node_id })
    const c2 = await graph.createConnection({ type: 'T1', from_node_id: a.node_id, to_node_id: b.node_id })
    const c3 = await graph.createConnection({ type: 'T2', from_node_id: a.node_id, to_node_id: b.node_id })

    let byFrom = await graph.queryConnections({ from_node_id: a.node_id })
    expect(byFrom.connection_ids.length).toBe(3)

    await graph.deleteConnection({ connection_id: c2.connection_id })
    byFrom = await graph.queryConnections({ from_node_id: a.node_id })
    expect(new Set(byFrom.connection_ids)).toEqual(new Set([c1.connection_id, c3.connection_id]))
  })
})

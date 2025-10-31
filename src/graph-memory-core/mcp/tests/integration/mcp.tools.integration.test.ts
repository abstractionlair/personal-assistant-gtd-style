/**
 * Tests for: MCP tool layer integration (GraphMemoryMcpServer)
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
import { GraphMemoryMcpServer } from '../../src/server.js'
import { MemoryGraph } from '../../src/memoryGraph.js'
import { FakeStorage } from '../helpers/fakeStorage.js'
import type { GraphMemoryServerConfig } from '../../src/types.js'
import type { ToolDefinition, ToolRegistrar } from '../../src/server.js'

class LocalRegistrar implements ToolRegistrar {
  public tools = new Map<string, ToolDefinition<any, any>>()
  registerTool<TInput, TResult>(definition: ToolDefinition<TInput, TResult>): void {
    this.tools.set(definition.name, definition as ToolDefinition<any, any>)
  }
  async invoke(name: string, input: any): Promise<any> {
    const def = this.tools.get(name)
    if (!def) throw new Error(`Tool not registered: ${name}`)
    return def.handler(input)
  }
}

describe('MCP Tools Integration (via GraphMemoryMcpServer)', () => {
  let storage: FakeStorage
  let config: GraphMemoryServerConfig
  let registrar: LocalRegistrar

  beforeEach(() => {
    storage = new FakeStorage()
    config = { basePath: '/virtual' }
    registrar = new LocalRegistrar()
  })

  it('happy path: ontology -> nodes -> connection -> traversal', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    const server = new GraphMemoryMcpServer(graph)
    server.registerTools(registrar)

    await registrar.invoke('create_ontology', {
      node_types: ['Project', 'Action'],
      connection_types: [ { name: 'NextAction', from_types: ['Project'], to_types: ['Action'] } ]
    })

    const p = await registrar.invoke('create_node', {
      type: 'Project',
      content: '# Kitchen Renovation',
      encoding: 'utf-8',
      format: 'markdown',
      properties: { status: 'active' }
    })
    const a = await registrar.invoke('create_node', {
      type: 'Action',
      content: 'Call contractor',
      encoding: 'utf-8',
      format: 'markdown',
      properties: { status: 'next' }
    })

    const c = await registrar.invoke('create_connection', {
      type: 'NextAction',
      from_node_id: p.node_id,
      to_node_id: a.node_id,
      properties: { priority: 'high' }
    })

    const connected = await registrar.invoke('get_connected_nodes', {
      node_id: p.node_id,
      connection_type: 'NextAction',
      direction: 'out'
    })
    expect(new Set(connected.node_ids)).toEqual(new Set([a.node_id]))
  })

  it('error mapping: create_node before ontology yields ONTOLOGY_NOT_FOUND', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    const server = new GraphMemoryMcpServer(graph)
    server.registerTools(registrar)

    await expect(
      registrar.invoke('create_node', {
        type: 'Project', content: 'P', encoding: 'utf-8', format: 'txt'
      })
    ).rejects.toMatchObject({ code: 'ONTOLOGY_NOT_FOUND' })
  })

  it('persistence across restart: node visible after re-initialize', async () => {
    // First instance writes state
    let graph = await MemoryGraph.initialize(config, storage)
    let server = new GraphMemoryMcpServer(graph)
    server.registerTools(registrar)
    await registrar.invoke('create_ontology', { node_types: ['Note'], connection_types: [] })
    const created = await registrar.invoke('create_node', { type: 'Note', content: 'hello', encoding: 'utf-8', format: 'txt' })

    // Simulate restart with same storage
    graph = await MemoryGraph.initialize(config, storage)
    server = new GraphMemoryMcpServer(graph)
    registrar = new LocalRegistrar()
    server.registerTools(registrar)

    const meta = await registrar.invoke('get_node', { node_id: created.node_id })
    expect(meta.id).toBe(created.node_id)
  })

  it('persistence across restart: connection visible and traversal works (AC2, AC20)', async () => {
    // First instance writes state
    let graph = await MemoryGraph.initialize(config, storage)
    let server = new GraphMemoryMcpServer(graph)
    registrar = new LocalRegistrar()
    server.registerTools(registrar)
    await registrar.invoke('create_ontology', { node_types: ['Project', 'Action'], connection_types: [{ name: 'NextAction', from_types: ['Project'], to_types: ['Action'] }] })
    const p = await registrar.invoke('create_node', { type: 'Project', content: 'P', encoding: 'utf-8', format: 'txt' })
    const a = await registrar.invoke('create_node', { type: 'Action', content: 'A', encoding: 'utf-8', format: 'txt' })
    const c = await registrar.invoke('create_connection', { type: 'NextAction', from_node_id: p.node_id, to_node_id: a.node_id })

    // Restart and verify
    graph = await MemoryGraph.initialize(config, storage)
    server = new GraphMemoryMcpServer(graph)
    registrar = new LocalRegistrar()
    server.registerTools(registrar)
    const meta = await registrar.invoke('get_connection', { connection_id: c.connection_id })
    expect(meta.id).toBe(c.connection_id)
    const traversal = await registrar.invoke('get_connected_nodes', { node_id: p.node_id, connection_type: 'NextAction', direction: 'out' })
    expect(traversal.node_ids).toContain(a.node_id)
  })
})

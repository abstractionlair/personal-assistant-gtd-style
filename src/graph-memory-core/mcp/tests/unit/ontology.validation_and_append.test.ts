/**
 * Tests for: Ontology creation, validation, and append-only updates
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
import { OntologyAlreadyExistsError, TypeAlreadyExistsError } from '../../src/errors.js'

describe('Ontology - Create, Validate, Append (AC4, AC10, AC17)', () => {
  let storage: FakeStorage
  let config: GraphMemoryServerConfig

  beforeEach(() => {
    storage = new FakeStorage()
    config = { basePath: '/virtual' }
  })

  it('create_ontology then validate_connection returns correct boolean (AC4)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({
      node_types: ['Project', 'Action'],
      connection_types: [{ name: 'NextAction', from_types: ['Project'], to_types: ['Action'] }]
    })

    const ok = await graph.validateConnection({ connection_type: 'NextAction', from_node_type: 'Project', to_node_type: 'Action' })
    expect(ok.valid).toBe(true)

    const bad = await graph.validateConnection({ connection_type: 'NextAction', from_node_type: 'Action', to_node_type: 'Project' })
    expect(bad.valid).toBe(false)
  })

  it('create_ontology twice fails; append types is append-only (AC10, AC17)', async () => {
    const graph = await MemoryGraph.initialize(config, storage)
    await graph.createOntology({ node_types: ['Project'], connection_types: [] })
    await expect(
      graph.createOntology({ node_types: ['Project'], connection_types: [] })
    ).rejects.toThrow(OntologyAlreadyExistsError)

    await graph.addNodeType({ type_name: 'Action' })
    await expect(graph.addNodeType({ type_name: 'Action' })).rejects.toThrow(TypeAlreadyExistsError)

    await graph.addConnectionType({ type_name: 'NextAction', from_types: ['Project'], to_types: ['Action'] })
    await expect(
      graph.addConnectionType({ type_name: 'NextAction', from_types: ['Project'], to_types: ['Action'] })
    ).rejects.toThrow(TypeAlreadyExistsError)

    const snapshot = await graph.getOntology()
    expect(snapshot.node_types).toEqual(['Project', 'Action'])
    expect(snapshot.connection_types.find(c => c.name === 'NextAction')).toBeDefined()
  })
})

/**
 * Tests for: MemoryGraph.ensureSingletonNode
 * Feature: Singleton Node Support (Tool 19)
 * Spec: specs/doing/singleton-node-support.md
 *
 * Tests written: 2025-11-01
 * Test Writer: OpenAI Codex (Codex CLI)
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryGraph } from '../../src/memoryGraph.js'
import { FakeStorage } from '../helpers/fakeStorage.js'
import type { GraphMemoryServerConfig } from '../../src/types.js'
import {
  InvalidArgumentError,
  InvalidNodeTypeError,
  OntologyNotFoundError
} from '../../src/errors.js'

describe('MemoryGraph.ensureSingletonNode', () => {
  let storage: FakeStorage
  let config: GraphMemoryServerConfig
  let graph: MemoryGraph

  beforeEach(async () => {
    storage = new FakeStorage()
    config = { basePath: '/virtual' }
    graph = await MemoryGraph.initialize(config, storage)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  async function createOntology(nodeTypes: string[]): Promise<void> {
    await graph.createOntology({ node_types: nodeTypes, connection_types: [] })
  }

  it('creates singleton when absent and returns created=true (AC1)', async () => {
    await createOntology(['WorkspaceConfig'])

    const result = await graph.ensureSingletonNode({
      type: 'WorkspaceConfig',
      content: '{"inbox": "inbox.md"}',
      encoding: 'utf-8',
      format: 'json',
      properties: { version: 1 }
    })

    expect(result.created).toBe(true)
    expect(typeof result.node_id).toBe('string')

    const meta = await graph.getNode({ node_id: result.node_id })
    expect(meta.type).toBe('WorkspaceConfig')
    expect(meta.properties).toEqual({ version: 1 })

    const content = await graph.getNodeContent({ node_id: result.node_id })
    expect(content.content).toContain('"inbox"')
  })

  it('returns existing singleton without modifying stored content or properties (AC2, AC7)', async () => {
    await createOntology(['WorkspaceConfig'])

    const { node_id } = await graph.createNode({
      type: 'WorkspaceConfig',
      content: '{"inbox": "initial.md"}',
      encoding: 'utf-8',
      format: 'json',
      properties: { version: 1, theme: 'dark' }
    })

    const result = await graph.ensureSingletonNode({
      type: 'WorkspaceConfig',
      content: '{"inbox": "ignored.md"}',
      encoding: 'utf-8',
      format: 'json',
      properties: { version: 99 }
    })

    expect(result.created).toBe(false)
    expect(result.node_id).toBe(node_id)

    const meta = await graph.getNode({ node_id })
    expect(meta.properties).toEqual({ version: 1, theme: 'dark' })
    const content = await graph.getNodeContent({ node_id })
    expect(content.content).toBe('{"inbox": "initial.md"}')
  })

  it('selects oldest node when duplicates exist by default (AC3)', async () => {
    await createOntology(['WorkspaceConfig'])

    vi.useFakeTimers()
    vi.setSystemTime(new Date('2025-01-01T00:00:00Z'))
    const { node_id: oldestId } = await graph.createNode({
      type: 'WorkspaceConfig',
      content: 'oldest',
      encoding: 'utf-8',
      format: 'text'
    })

    vi.setSystemTime(new Date('2025-01-01T00:00:05Z'))
    await graph.createNode({
      type: 'WorkspaceConfig',
      content: 'newest',
      encoding: 'utf-8',
      format: 'text'
    })

    const result = await graph.ensureSingletonNode({
      type: 'WorkspaceConfig'
    })

    expect(result.created).toBe(false)
    expect(result.node_id).toBe(oldestId)
  })

  it('selects newest node when on_multiple="newest" (AC3a)', async () => {
    await createOntology(['WorkspaceConfig'])

    vi.useFakeTimers()
    vi.setSystemTime(new Date('2025-01-01T00:00:00Z'))
    await graph.createNode({
      type: 'WorkspaceConfig',
      content: 'oldest',
      encoding: 'utf-8',
      format: 'text'
    })

    vi.setSystemTime(new Date('2025-01-01T00:00:05Z'))
    const { node_id: newestId } = await graph.createNode({
      type: 'WorkspaceConfig',
      content: 'newest',
      encoding: 'utf-8',
      format: 'text'
    })

    const result = await graph.ensureSingletonNode({
      type: 'WorkspaceConfig',
      on_multiple: 'newest'
    })

    expect(result.created).toBe(false)
    expect(result.node_id).toBe(newestId)
  })

  it('uses lexicographic node_id tie-breaker when created timestamps are equal (AC8)', async () => {
    await createOntology(['WorkspaceConfig'])

    vi.useFakeTimers()
    vi.setSystemTime(new Date('2025-01-01T00:00:00Z'))

    const randomSpy = vi.spyOn(Math, 'random')
    randomSpy.mockReturnValueOnce(0.11)
    const { node_id: idA } = await graph.createNode({
      type: 'WorkspaceConfig',
      content: 'first',
      encoding: 'utf-8',
      format: 'text'
    })

    randomSpy.mockReturnValueOnce(0.99)
    const { node_id: idB } = await graph.createNode({
      type: 'WorkspaceConfig',
      content: 'second',
      encoding: 'utf-8',
      format: 'text'
    })

    const ordered = [idA, idB].sort()
    const result = await graph.ensureSingletonNode({ type: 'WorkspaceConfig' })

    expect(result.created).toBe(false)
    expect(result.node_id).toBe(ordered[0])
  })

  it('throws INVALID_ARGUMENT when creation fields are missing and no node exists (AC6)', async () => {
    await createOntology(['WorkspaceConfig'])

    await expect(
      graph.ensureSingletonNode({ type: 'WorkspaceConfig' })
    ).rejects.toThrow(InvalidArgumentError)
  })

  it('throws INVALID_NODE_TYPE when ontology lacks the requested type (AC5)', async () => {
    await createOntology(['Project'])

    await expect(
      graph.ensureSingletonNode({
        type: 'WorkspaceConfig',
        content: '{}',
        encoding: 'utf-8',
        format: 'json'
      })
    ).rejects.toThrow(InvalidNodeTypeError)
  })

  it('throws ONTOLOGY_NOT_FOUND when ontology has not been created (AC4)', async () => {
    await expect(
      graph.ensureSingletonNode({
        type: 'WorkspaceConfig',
        content: '{}',
        encoding: 'utf-8',
        format: 'json'
      })
    ).rejects.toThrow(OntologyNotFoundError)
  })
})

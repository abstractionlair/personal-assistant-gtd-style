/**
 * Tests for: GraphMemoryMcpServer ensure_singleton_node tool registration
 * Feature: Singleton Node Support (Tool 19)
 * Spec: specs/doing/singleton-node-support.md
 *
 * Tests written: 2025-11-01
 * Test Writer: OpenAI Codex (Codex CLI)
 */

import { describe, expect, it, vi } from 'vitest'
import { GraphMemoryMcpServer, type ToolDefinition, type ToolRegistrar } from '../../src/server.js'
import type { MemoryGraph } from '../../src/memoryGraph.js'
import type {
  EnsureSingletonNodeRequest,
  EnsureSingletonNodeResult
} from '../../src/types.js'

class CaptureRegistrar implements ToolRegistrar {
  public readonly tools: Array<ToolDefinition<unknown, unknown>> = []

  registerTool<TInput, TResult>(definition: ToolDefinition<TInput, TResult>): void {
    this.tools.push(definition as ToolDefinition<unknown, unknown>)
  }
}

describe('GraphMemoryMcpServer - ensure_singleton_node tool', () => {
  it('registers ensure_singleton_node and delegates to MemoryGraph.ensureSingletonNode', async () => {
    const ensureSingletonNode = vi.fn<
      [EnsureSingletonNodeRequest],
      Promise<EnsureSingletonNodeResult>
    >()
    const graph = { ensureSingletonNode } as unknown as MemoryGraph

    const server = new GraphMemoryMcpServer(graph)
    const registrar = new CaptureRegistrar()
    server.registerTools(registrar)

    const tool = registrar.tools.find((definition) => definition.name === 'ensure_singleton_node')
    expect(tool, 'ensure_singleton_node should be registered').toBeDefined()

    const request: EnsureSingletonNodeRequest = {
      type: 'WorkspaceConfig',
      content: '{}',
      encoding: 'utf-8',
      format: 'json',
      on_multiple: 'oldest'
    }
    const expected: EnsureSingletonNodeResult = { node_id: 'mem_123', created: true }
    ensureSingletonNode.mockResolvedValue(expected)

    const payload = await (tool as ToolDefinition<EnsureSingletonNodeRequest, EnsureSingletonNodeResult>).handler(request)

    expect(ensureSingletonNode).toHaveBeenCalledWith(request)
    expect(payload).toBe(expected)
  })
})

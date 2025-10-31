/**
 * Module: idGenerator
 * Purpose: Provide deterministic ID generation helper for nodes and connections.
 * Created: 2025-10-31
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/todo/graph-memory-core.md
 */

/**
 * Generate an opaque identifier using the prefix specified in the specification.
 */
export function generateId(prefix: string = 'mem'): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 9);
  return `${prefix}_${timestamp}_${random}`;
}

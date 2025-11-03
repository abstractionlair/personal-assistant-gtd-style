/**
 * Module: schema
 * Purpose: Describe GTD ontology structures and provide initialization payload builders.
 * Created: 2025-11-02
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/doing/gtd-ontology.md
 */

import type { CreateOntologyRequest, EnsureSingletonNodeRequest } from './types.js';

/**
 * Canonical content stored on the UNSPECIFIED singleton node.
 */
export const UNSPECIFIED_NODE_CONTENT =
  'This is a placeholder indicating that dependencies are yet to be specified. Tasks or States depending on UNSPECIFIED cannot be marked complete until concrete dependencies are defined.';

/**
 * Build the ontology definition payload that declares GTD node and connection types.
 *
 * @returns Ontology request matching the GTD specification.
 * @throws NotImplementedError Until the ontology payload is implemented.
 */
export function buildGtdOntologyDefinition(): CreateOntologyRequest {
  return {
    node_types: ['Task', 'State', 'Context', 'UNSPECIFIED'],
    connection_types: [
      {
        name: 'DependsOn',
        from_types: ['Task', 'State'],
        to_types: ['Task', 'State', 'Context', 'UNSPECIFIED']
      }
    ]
  };
}

/**
 * Build the singleton initialization payload for the UNSPECIFIED node.
 *
 * @returns Request suitable for ensureSingletonNode MCP tool invocation.
 * @throws NotImplementedError Until the singleton payload is implemented.
 */
export function buildUnspecifiedSingletonRequest(): EnsureSingletonNodeRequest {
  const request: EnsureSingletonNodeRequest = {
    type: 'UNSPECIFIED',
    content: UNSPECIFIED_NODE_CONTENT,
    encoding: 'utf-8'
  };
  Object.defineProperty(request, 'format', {
    value: 'text/plain',
    enumerable: false,
    writable: true,
    configurable: true
  });
  return request;
}

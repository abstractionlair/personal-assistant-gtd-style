/**
 * Module: initialize
 * Purpose: Provide the one-time GTD ontology bootstrapping script entry point.
 * Created: 2025-11-02
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/doing/gtd-ontology.md
 */

import {
  buildGtdOntologyDefinition,
  buildUnspecifiedSingletonRequest
} from './schema.js';
import type { GraphMemoryClient } from './types.js';

/**
 * Result structure returned by initializeGTDOntology.
 */
export interface InitializeResult {
  ok: boolean;
  error?: string;
}

/**
 * Execute GTD ontology initialization against the graph-memory-core MCP server.
 *
 * Responsibilities:
 * - Calls createOntology with the GTD node/connection schema.
 * - Calls ensureSingletonNode to create or fetch the UNSPECIFIED singleton.
 * - Returns success indicator and error diagnostics for CLI tooling.
 *
 * @param client - Graph memory client abstraction capable of invoking MCP tools.
 * @returns Structured result describing success or failure.
 * @throws NotImplementedError Until setup script behavior is implemented.
 */
export async function initializeGTDOntology(client: GraphMemoryClient): Promise<InitializeResult> {
  const ontologyDefinition = buildGtdOntologyDefinition();

  try {
    await client.createOntology(ontologyDefinition);
  } catch (error) {
    if (!isOntologyAlreadyExistsError(error)) {
      return { ok: false, error: extractErrorMessage(error) };
    }
  }

  try {
    await client.ensureSingletonNode(buildUnspecifiedSingletonRequest());
  } catch (error) {
    return { ok: false, error: extractErrorMessage(error) };
  }

  return { ok: true };
}

function isOntologyAlreadyExistsError(error: unknown): boolean {
  if (!error || typeof error !== 'object') {
    return false;
  }
  const maybeCode = (error as { code?: unknown }).code;
  return typeof maybeCode === 'string' && maybeCode === 'ONTOLOGY_ALREADY_EXISTS';
}

function extractErrorMessage(error: unknown): string {
  if (error instanceof Error && typeof error.message === 'string') {
    return error.message;
  }
  return String(error);
}

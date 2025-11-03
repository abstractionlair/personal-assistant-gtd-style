/**
 * Module: errors
 * Purpose: Shared error types for GTD ontology scaffolding.
 * Created: 2025-11-02
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/doing/gtd-ontology.md
 */

/**
 * Raised for code paths that require implementation in later workflow stages.
 */
export class NotImplementedError extends Error {
  constructor(message: string) {
    super(message);
  }
}

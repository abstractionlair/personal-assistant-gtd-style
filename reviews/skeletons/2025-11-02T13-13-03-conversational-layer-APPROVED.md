# Skeleton Review: Conversational Layer System Prompt

**Reviewer:** OpenAI Codex (Codex CLI)
**Date:** 2025-11-02 13:13:03 UTC
**Spec:** specs/todo/conversational-layer.md
**Skeleton Files:** src/conversational-layer/system-prompt.md
**Status:** APPROVED

## Summary
The skeleton prompt provides a complete, testable outline that mirrors the approved spec: all major sections, derived views, tool usage topics, query algorithms, weekly review template, and critical reminders are present with clear TDD placeholders. Structure is hollow by design, enabling RED tests first. One small gap (missing dedicated Edge Cases examples section) can be added trivially without re-review.

## Contract Compliance
- ✓ All sections from spec represented as headings
- ✓ Derived views (Projects, Next Actions, Waiting For) covered
- ✓ MCP tools covered with per-tool subsections
- ✓ Query algorithms stubs included (Projects, Next Actions, Waiting For, Stuck Projects)
- ✓ Preconditions and Postconditions sections included
- ✓ UNSPECIFIED singleton and context availability addressed

## Testability Assessment ⚠ Critical
- ✓ Hollow content with explicit placeholders (RED-first TDD)
- ✓ Clear “Expected coverage” bullets guide test authors
- ✓ Algorithms and examples sections separated for targeted tests
- ✓ Structure supports incremental filling without restructuring

## Completeness
- ✓ Section stubs and example categories present (Capture, Query, Update, Delete)
- ❌ Missing dedicated Edge Cases examples category (spec calls for 5)
- ✓ Tool semantics include idempotency/safety notes at summary level
- ✓ Pre/Post conditions present

## Hollowness Verification
- ✓ No implementation content; only placeholders and guidance
- ✓ No prescriptive logic beyond contract statements
- ✓ No conflicting behavioral details vs spec

## Quality Checks
- ✓ File location and naming align with project structure
- ✓ Header metadata present (module, purpose, created, author, spec link)
- ✓ Mirrors spec terminology consistently (Task/State/Context, DependsOn)
- ✓ Cross-links implied to GTD ontology and graph core

## Minor Issues
- Suggest adding explicit topology callouts under “DependsOn Connections”: Context can only be target; UNSPECIFIED only target; list supported from→to pairs for Phase 1.
- In “Tool Summary”, add explicit “Property constraints” bullet: primitive-only properties, update merges (no removals), AND semantics in queries, case-sensitive string matching.
- Consider adding a short “Context-filtered Next Actions” algorithm note that references availability checks (you already have examples; an algorithm stub would parallel other algorithms).

## Testability Score
- Dependency clarity: Pass — responsibilities per section are clear
- Contract coverage: Pass — all key behaviors represented as sections
- Structure for examples: Pass — categories and counts specified

## Approval Conditions

This review APPROVES the skeleton for test writing, contingent on:

1. Add a new section: “### Edge Case Patterns (5 Examples Minimum)” under “Conversation Patterns and Examples,” with placeholders and “Expected coverage” bullets (empty results, ambiguous reference, conflicting updates, undefined context, inference vs asking).
2. Under “DependsOn Connections,” add explicit Phase 1 topology rules: Task→Task, Task→State, Task→Context, State→Task allowed; Context only as target; UNSPECIFIED only as target.
3. Under “Tool Summary,” add a bullet summarizing property constraints and query semantics: primitive-only properties; update merges and cannot remove; AND semantics; case-sensitive exact string matching.

These are editorial additions to headings/bullets and do not require re-review.

## Decision
APPROVED — Ready for test-writer.

Next steps for skeleton-writer:
- Create feature branch: `git checkout -b feature/conversational-layer`
- Move spec to doing: `git mv specs/todo/conversational-layer.md specs/doing/conversational-layer.md`
- Commit and push branch for test-writer to begin.


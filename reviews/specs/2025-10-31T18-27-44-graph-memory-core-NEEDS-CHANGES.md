# Spec Review: graph-memory-core

**Reviewer**: OpenAI Codex (Codex CLI)
**Date**: 2025-10-31
**Spec Version**: specs/proposed/graph-memory-core.md
**Status**: NEEDS-CHANGES

## Summary
Great iteration—this addresses nearly all prior feedback: consistent server naming, explicit encoding vs format, property constraints and matching semantics, format mutability on update, connection content path, error code table, opaque IDs in examples, and text-only search clarified. Two minor clarifications remain to keep implementation and tests aligned.

## Checklist
- [x] Aligns with Vision/Scope/Roadmap
- [x] Interfaces specified
- [x] Happy/edge paths covered
- [x] Error handling specified
- [x] Integration points clear
- [x] Testability verified (almost complete)
- [x] Dependencies identified

## Remaining Issues

1) Unknown `format` → file extension behavior
- Location: specs/proposed/graph-memory-core.md:159 (Content Format and Encoding)
- The spec states the system "uses format to determine file extensions" with examples (markdown→.md, pdf→.pdf) but does not define what happens for unrecognized formats (e.g., "meeting-notes").
- Please specify a deterministic rule, e.g. one of:
  - Map known formats explicitly; for unknown formats, use `.{format}` after sanitization; or
  - Reject unknown formats with a clear error; or
  - For base64 content with unknown format, default to `.bin`; for utf-8, default to `.txt`.
- This avoids divergent implementations and makes file path expectations predictable for tests when inspecting registry `content.path`.

2) Acceptance criterion for binary search behavior
- Location: specs/proposed/graph-memory-core.md:1062 (Acceptance Criteria) and Tool 13 at specs/proposed/graph-memory-core.md:802–806
- Tool 13 notes that binary content is not searched, which is clear. Please add a corresponding acceptance bullet under AC16 (Content Search), e.g.: "search_content does not match binary nodes (encoding=base64)."
- This ensures tests capture the documented behavior explicitly.

## Approval Criteria
This spec will be approved once it:
1. Defines the rule for deriving file extension from `format` for unknown formats.
2. Adds an AC16 bullet asserting that binary content is not searched.

## Next Steps
- [ ] Update the spec per the two items above
- [ ] Ping for quick re-review; I’ll approve and move to `specs/todo/`


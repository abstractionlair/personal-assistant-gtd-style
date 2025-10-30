# Spec Review: file-storage-backend

**Reviewer**: OpenAI Codex (Codex CLI)
**Date**: 2025-10-30
**Spec Version**: specs/proposed/file-storage-backend.md
**Status**: NEEDS-CHANGES

## Summary
Strong, well-structured spec aligned with Vision/Scope/Roadmap and rich with
interfaces, acceptance criteria, and scenarios. It clearly defines the six
operations, path containment goals, and atomicity guarantees. However, several
clarifications are required before implementation teams can consume it without
ambiguity: JSON-safe payload encoding for binary/text, explicit symlink escape
handling, directory deletion semantics (what counts as “empty”), MCP error
mapping, and a few smaller consistency points (sorting rules, trailing slash,
insert newline semantics). Addressing these will make the spec unambiguous and
fully testable.

## Checklist
- [x] Aligns with Vision/Scope/Roadmap
- [x] Interfaces specified
- [x] Happy/edge paths covered
- [x] Error handling specified
- [x] Integration points clear (MCP config provided)
- [ ] Testability verified (encoding + symlink cases need concreteness)
- [x] Dependencies identified

## Detailed Feedback

1) JSON-safe wire format (binary/text)
- Issue: The spec alternates between `string | Buffer` and “base64-encoded”
  content. MCP tool results are JSON, so `Buffer` is not a serializable wire
  type. Likewise, `view()` returning a Buffer is ambiguous on the wire.
- Requirement: Standardize on strings over MCP with explicit encoding metadata.
  Recommended shape for inputs/outputs that carry file content:
  - For inputs: `{ content: string, encoding: 'utf-8' | 'base64' }`
  - For outputs: `{ content: string, encoding: 'utf-8' | 'base64' }`
  - Mandate `encoding` presence whenever `content` is present.
- Actions:
  - Update Interface Contract for `create()` input and `view()` output to use
    the `encoding` field; remove `Buffer` from types.
  - Update examples, acceptance criteria, and scenarios to reflect this.

2) Symlink escape handling (path security)
- Issue: Implementation notes cover `path.resolve`/`path.relative` but do not
  address symlinks inside the base directory that point outside (classic escape
  vector). The Python reference explicitly forbids these; the TypeScript spec
  currently does not.
- Requirement: Add a normative rule that the resolved real path of any target
  (using `fs.realpath` or equivalent) MUST remain within the real path of the
  base directory. Either:
  - Forbid following symlinks entirely, or
  - Allow symlinks but require post-resolution containment checks.
- Actions:
  - Add acceptance criteria and a scenario exercising a symlink that points
    outside the base to ensure it is rejected with a clear `path_security`
    error.

3) Directory deletion semantics (“empty” definition)
- Issue: Spec implies directories may be considered "empty" even if they
  contain hidden files ("except hidden files"). Deleting such a directory would
  remove hidden contents unexpectedly.
- Requirement: Choose one and state it clearly:
  - Preferred: Directory must be truly empty (no entries), hidden files count.
  - If keeping current behavior (ignore hidden files), then specify precisely
    and add acceptance criteria (e.g., deletion succeeds when only `.gitkeep`
    present), and document the risk.
- Actions:
  - Clarify the rule and reflect it in acceptance criteria and scenarios.

4) MCP error mapping
- Issue: Spec lists error messages and an "Error Message Format" example, but
  does not state how these map onto MCP tool error structures (codes/types vs
  messages) for clients.
- Requirement: Define a consistent mapping for tool errors (e.g., `code`
  values like `file_not_found`, `path_security`, `string_not_unique`, etc.).
- Actions:
  - Specify the MCP error object shape for each failure mode, including `code`
    and `message`, and ensure examples use that shape.

5) Sorting collation and case
- Issue: "alphanumeric" sorting can vary by locale/case. Tests need a stable
  rule.
- Requirement: Define sorting as byte-wise ascending by Unicode code point
  (equivalent to JavaScript default comparison) and state case sensitivity.
- Actions:
  - Add one line to Interface Contract for directory listings; update
    acceptance criteria note accordingly.

6) Trailing slash handling for directories
- Issue: Examples show `"nodes/"`. Clarify whether `"nodes"` is equally valid
  and how normalization works.
- Requirement: State that both forms are accepted and normalized.
- Actions:
  - Add to Interface Contract for `view()` and acceptance criteria.

7) Insert semantics for newline
- Issue: `insert(new_str)` is described as “inserted as a complete line,” but
  it's unclear whether a trailing newline is auto-added if missing.
- Requirement: Define whether the implementation adds a newline or requires
  callers to include it. Specify behavior for end-of-file insert.
- Actions:
  - Clarify in Interface Contract and add an acceptance criterion + example.

8) Rename atomicity and cross-device moves
- Issue: Atomic rename may fail across devices. The base directory is likely on
  a single filesystem, but this should be explicit as a constraint.
- Requirement: State the assumption that `basePath` resides on a single
  filesystem/volume so rename semantics are atomic; define expected behavior if
  not (reject with clear error).
- Actions:
  - Add to Constraints and optionally to acceptance criteria notes.

9) Minor consistency
- Explicitly state that `view()` directory listings exclude `.` and `..`.
- Keep the Python reference as non-normative “inspiration”; add a sentence to
  avoid confusion since the chosen MVP stack is Node/TypeScript.

## Approval Criteria
This spec will be APPROVED once it:
1. Standardizes JSON-safe content encoding for `create()` inputs and `view()`
   outputs with explicit `encoding` field; removes `Buffer` types from wire
   contracts.
2. Adds normative symlink handling (deny escape via realpath checks) with an
   acceptance criterion and scenario.
3. Clarifies directory deletion “empty” rule and reflects it in acceptance
   criteria and scenarios.
4. Defines MCP error mapping (codes + messages) and updates examples.
5. Clarifies sorting, trailing slash behavior, and insert newline semantics.

## Next Steps
- [ ] Update Interface Contract and examples for JSON-safe encoding
- [ ] Add symlink containment rule + tests (criteria + scenario)
- [ ] Decide and document directory deletion semantics (+ tests)
- [ ] Define MCP error object mapping (codes/messages)
- [ ] Clarify sorting, trailing slash, insert newline behavior
- [ ] Note Python reference is non-normative inspiration for Node/TS MVP


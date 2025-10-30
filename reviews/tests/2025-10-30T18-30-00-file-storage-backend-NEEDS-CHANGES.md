# Test Review: File Storage Backend Contract

**Reviewer:** Test Reviewer
**Date:** 2025-10-30 18:30:00
**Spec:** specs/doing/file-storage-backend.md (TypeScript MCP, authoritative for MVP); src/file-storage-backend/specs/todo/file_storage_backend_interface.md (Python interface, contract reference for this suite)
**Test Files:** src/file-storage-backend/tests/contracts/test_file_storage_contract.py; src/file-storage-backend/tests/conftest.py
**Status:** NEEDS-CHANGES

## Summary
Strong, well-structured contract suite that exercises path security, atomicity, binary/text boundaries, error handling, and operation semantics. Tests read clearly, follow AAA, and appear independent. A few important edge cases from the spec are not covered (e.g., trailing slash handling for directories, empty file behavior, delete with only hidden files). Addressing these will make the suite fully comprehensive before GREEN.

## Clarity & Readability
- ✓ Test names descriptive and behavior-focused
- ✓ Arrange-Act-Assert structure clear enough to follow
- ✓ Variables and fixtures have meaningful names
- ✓ Tests self-contained (no hidden/global state)

## Completeness
- ✓ Happy paths covered across operations (create/view, str_replace, insert, rename)
- ✓ Error cases covered (not found, exists, string not found/not unique, invalid line number, directory not empty)
- ✓ Edge cases mostly covered (symlink escape, normalization, directory listing sorted/hidden excluded)
- ❌ Trailing slash handling for directories not explicitly tested
- ❌ Empty file behavior not tested (create/view/delete empty file)
- ❌ Delete directory with only hidden files (should still be considered non-empty per policy) not tested
- ➕ Optional: Explicit containment rejection on create with relative escape (e.g., "nodes/../../../etc/bad")

## Coverage Metrics
- Pre-implementation (RED) run executed: cannot meaningfully assert line/branch coverage until implementation exists.
- Target post-implementation: ≥80% line, ≥70% branch for storage module(s).

## Independence
- ✓ Each test uses its own `tmp_path`-backed `storage` fixture
- ✓ No shared mutable state or order dependencies observed
- ✓ Uses `monkeypatch` to simulate rename failures deterministically

## Behavior vs Implementation
- ✓ Tests assert observable behavior, not internal structure
- ✓ Atomicity validated via simulated failure conditions (rename)
- ✓ Path security validated via absolute path, parent escape, and symlink escape

## Test Double Usage
- ✓ Minimal and appropriate; only `monkeypatch` for rename failure
- ✓ No over-mocking; exercises real filesystem within tmp dir

## Assertions
- ✓ Specific and meaningful (content equality, entries ordering, types, exception types)
- ✓ Binary vs text behavior asserted clearly (bytes content and size)

## Spec Alignment
Mapping notable acceptance criteria to tests:
- Path security (absolute, parent escape, symlink) → covered
- Path normalization (collapse // and .) → covered
- Atomicity (create, str_replace, insert, rename) → covered via rename failure simulation
- Binary handling (reject text ops on binary; view bytes + size) → covered
- Error handling (file_not_found, file_exists, string_not_found, string_not_unique, invalid_line_number, directory_not_empty) → covered
- Directory listing (sorted, hide dotfiles) → covered
- Create parents; Rename creates parents; Rename directories → covered
- Trailing slash handling for directories → missing
- Empty file lifecycle → missing
- Delete directory that only contains hidden files should be non-empty → missing

## RED Phase Verification
Command executed in subproject:
`cd src/file-storage-backend && PYTHONPATH=src STORAGE_IMPL=storage.local_storage.LocalFileStorage pytest -q --maxfail=1`
Observed: tests fail with `NotImplementedError` at first call (as expected for RED). No import/signature errors.

## Required Changes (Critical)
Please add the following tests to `src/file-storage-backend/tests/contracts/test_file_storage_contract.py`:

1) Trailing slash handling for directories
```python
def test_view_directory_with_trailing_slash(storage: FileStorage):
    storage.create("dir/a.txt", "a")
    storage.create("dir/b.txt", "b")

    result_no_slash = storage.view("dir")
    result_with_slash = storage.view("dir/")

    assert result_no_slash.type == "directory"
    assert result_with_slash.type == "directory"
    assert result_no_slash.entries == result_with_slash.entries == ["a.txt", "b.txt"]
```

2) Empty file lifecycle
```python
def test_create_and_view_empty_text_file(storage: FileStorage):
    storage.create("empty.txt", "")
    result = storage.view("empty.txt")
    assert result.type == "file"
    assert result.content == ""
    assert result.size == 0

def test_create_and_view_empty_binary_file(storage: FileStorage):
    storage.create("empty.bin", b"")
    result = storage.view("empty.bin")
    assert result.type == "file"
    assert isinstance(result.content, (bytes, bytearray))
    assert result.content == b""
    assert result.size == 0
```

3) Delete with only hidden file still considered non-empty
```python
def test_delete_directory_with_only_hidden_file_raises_error(storage: FileStorage):
    storage.create("dir/.hidden", "h")
    with pytest.raises(DirectoryNotEmptyError):
        storage.delete("dir")
```

4) Optional: Explicit containment rejection on create
```python
def test_must_reject_relative_escape_on_create(storage: FileStorage):
    with pytest.raises(PathSecurityError):
        storage.create("nodes/../../../etc/bad", "content")
```

## Positive Notes
- Clear behavior-driven names (e.g., `test_rename_must_work_for_directories`)
- Good atomicity simulations using `monkeypatch` for rename failures
- Comprehensive coverage of error classes and directory listing rules

## Decision

NEEDS-CHANGES – Add the four tests above to cover trailing slash handling, empty file behavior, hidden-only delete, and explicit create escape rejection. After adding, re-run in RED to ensure failures are still due to `NotImplementedError`. Post-implementation, verify coverage ≥80% line and ≥70% branch for storage code.


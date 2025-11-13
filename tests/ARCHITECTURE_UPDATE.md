# Test Harness Architecture Update

**Date:** 2025-11-05
**Change:** Migrated from `--system-prompt` to `--append-system-prompt`

---

## What Changed

The test harness has been updated to support the new instruction architecture where:
1. Main instructions live in a Claude Skill (not passed by test harness)
2. Optional production system prompt addendum (small amount of production guidance)
3. Test-specific overlays (never in production files)

### Before (Old Architecture)

```
Test Harness Bundle (--system-prompt):
├── system-prompt.md (main instructions)
├── Interface Contract (from spec)
├── Data Structures (from spec)
└── Test Overlay (test-specific)
```

**Problem:** Mixed production and test content in one bundle

### After (New Architecture)

```
Claude Skill (loaded automatically):
└── Main instructions

Production System Prompt Addendum (--append-system-prompt):
└── src/conversational-layer/system-prompt-addendum.md (optional)

Test Overlay (--append-system-prompt, test-only):
└── tests/fixtures/system-prompt-{test-overlay,live-mcp-overlay,no-mcp-overlay}.md
```

**Benefits:**
- Clean separation of production and test content
- Test overlays never leak into production
- Production addendum can be version-controlled separately
- Claude Skills provide main instructions

---

## File Changes

### Updated Files

**`test_conversational_layer.py`:**
- Added `SYSTEM_PROMPT_ADDENDUM` path constant
- Renamed `build_bundle()` → `build_test_overlay()`
- Updated `build_test_overlay()` to only build test content
- Changed `base_args()` to use `--append-system-prompt`
- Updated `run_claude()` to accept list of append prompts
- Updated `run_assistant()` and `run_judge()` signatures
- Modified `main()` to build append prompts list

### New Expected Files

**`src/conversational-layer/system-prompt-addendum.md` (optional):**
- Small amount of production system prompt guidance
- Separate from main skill instructions
- Used in both tests and production

**Test overlays (existing, no changes):**
- `tests/fixtures/system-prompt-test-overlay.md` - General test guidance
- `tests/fixtures/system-prompt-live-mcp-overlay.md` - Live MCP mode guidance
- `tests/fixtures/system-prompt-no-mcp-overlay.md` - Simulation mode guidance

---

## How It Works

### 1. Production Addendum (Optional)

```python
# If exists, load production addendum
if SYSTEM_PROMPT_ADDENDUM.exists():
    addendum = SYSTEM_PROMPT_ADDENDUM.read_text(encoding="utf-8").strip()
    if addendum:
        append_prompts.append(addendum)
```

**Purpose:** Small production guidance that supplements the Claude Skill

**Examples of what might go here:**
- Project-specific context
- Output format preferences
- Domain-specific terminology

**What should NOT go here:**
- Test-specific instructions
- Simulation mode guidance
- Example test cases

### 2. Test Overlay (Always Included)

```python
# Build test-specific overlay
include_no_mcp = (args.mode == "sim") or (args.mode == "auto" and mcp is None)
test_overlay = build_test_overlay(include_no_mcp_overlay=include_no_mcp)
append_prompts.append(test_overlay)
```

**Purpose:** Test-specific guidance that never appears in production

**Includes:**
- General test overlay (test expectations, validation guidance)
- Mode-specific overlay:
  - Live MCP: Real operation guidance
  - Simulation: How to simulate operations

### 3. Command Line Invocation

```python
args = [CLAUDE_CMD]
if mcp:
    args += ["--mcp-config", str(mcp)]
args += ["--dangerously-skip-permissions", "--print", "--output-format", "json"]

# Add each append prompt
for append_content in append_prompts:
    if append_content.strip():
        args += ["--append-system-prompt", append_content]

args.append(prompt)
```

**Result:** Claude CLI receives:
```bash
claude \
  --mcp-config tests/mcp-config.json \
  --dangerously-skip-permissions \
  --print \
  --output-format json \
  --append-system-prompt "<production addendum content>" \
  --append-system-prompt "<test overlay content>" \
  "I need to call the dentist"
```

---

## Usage

### Running Tests (Same Commands)

**No changes to how you run tests:**

```bash
# Simulation mode
python tests/test_conversational_layer.py --suite assistant --mode sim

# Live MCP mode
python tests/test_conversational_layer.py --suite assistant --mode real

# With refactored test cases
python tests/test_conversational_layer.py --suite assistant --mode sim --test-cases refactored
```

### What Happens Internally

**1. Test harness looks for production addendum:**
```
If src/conversational-layer/system-prompt-addendum.md exists:
  ✅ Load and append
Else:
  ⏭️ Skip (not required)
```

**2. Test harness builds test overlay:**
```
Load tests/fixtures/system-prompt-test-overlay.md
+
Load mode-specific overlay:
  - Live MCP: tests/fixtures/system-prompt-live-mcp-overlay.md
  - Simulation: tests/fixtures/system-prompt-no-mcp-overlay.md
```

**3. Test harness invokes Claude:**
```
claude --append-system-prompt "<production addendum>" \
       --append-system-prompt "<test overlay>" \
       "<test prompt>"
```

---

## Migration From Old Approach

### If You Have Existing system-prompt.md

**Option 1: Move to Claude Skill (Recommended)**
1. Main instructions → Claude Skill
2. Small production guidance → `system-prompt-addendum.md`
3. Test guidance → Already in test overlays

**Option 2: Keep system-prompt.md (Backward Compatible)**
1. Test harness will continue to work
2. But won't use `system-prompt.md` anymore
3. Claude Skills provide instructions instead

### Verifying the Migration

**Check what's being sent:**

```python
# In main(), after building append_prompts:
print("=== Append Prompts ===")
for i, prompt in enumerate(append_prompts, 1):
    print(f"\n--- Prompt {i} ({len(prompt)} chars) ---")
    print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
```

**Or set debug mode:**
```bash
# Add to test_conversational_layer.py for debugging
if os.environ.get("DEBUG_PROMPTS"):
    for i, prompt in enumerate(append_prompts, 1):
        Path(f"/tmp/debug_prompt_{i}.md").write_text(prompt)
```

---

## Production vs Test Content

### Production Content ✅

**Location:** `src/conversational-layer/system-prompt-addendum.md`

**Should contain:**
- Project-specific context
- Domain terminology
- Output preferences
- Production-only guidance

**Should NOT contain:**
- "In simulation mode..."
- "For testing purposes..."
- Test validation criteria
- Example test cases

### Test Content ✅

**Location:** `tests/fixtures/*.md`

**Should contain:**
- Test expectations
- Simulation mode guidance
- Validation criteria
- Test-specific patterns

**Should NOT contain:**
- Production-only features
- Real deployment info
- Anything that would confuse the production assistant

---

## Benefits of New Architecture

### 1. Clean Separation
- Production files never contain test content
- Test files never leak into production
- Easy to audit what goes where

### 2. Maintainability
- Claude Skill provides main instructions
- Production addendum is small and focused
- Test overlays are isolated and clear

### 3. Flexibility
- Can update Claude Skill independently
- Can iterate on production addendum
- Can enhance test overlays without affecting production

### 4. Backward Compatibility
- Test harness still works if old files exist
- Can migrate incrementally
- No breaking changes to test commands

---

## Troubleshooting

### Tests fail after migration

**Check:**
1. Does production addendum exist? (Optional, but if referenced should exist)
2. Are test overlays still in `tests/fixtures/`?
3. Is Claude Skill loaded in Claude CLI?

**Debug:**
```bash
# See what's being passed
DEBUG_PROMPTS=1 python tests/test_conversational_layer.py --case capture_simple_task

# Check files
ls -la src/conversational-layer/system-prompt-addendum.md
ls -la tests/fixtures/system-prompt-*.md
```

### Production addendum not found

**This is OK!** Production addendum is optional. Test harness will:
```
If SYSTEM_PROMPT_ADDENDUM.exists():
    # Use it
else:
    # Skip, not required
```

**To add production addendum:**
```bash
# Create file
touch src/conversational-layer/system-prompt-addendum.md

# Add content (keep minimal)
echo "# Production Guidance" >> src/conversational-layer/system-prompt-addendum.md
```

### Test overlays not loading

**Check file paths:**
```python
# These should exist:
tests/fixtures/system-prompt-test-overlay.md
tests/fixtures/system-prompt-live-mcp-overlay.md
tests/fixtures/system-prompt-no-mcp-overlay.md
```

**Verify in code:**
```python
print(f"Test overlay exists: {OVERLAY_PATH.exists()}")
print(f"Live MCP overlay exists: {LIVE_MCP_OVERLAY_PATH.exists()}")
print(f"No MCP overlay exists: {NO_MCP_OVERLAY_PATH.exists()}")
```

---

## Examples

### Example 1: Production Addendum

**File:** `src/conversational-layer/system-prompt-addendum.md`

```markdown
# GTD Assistant - Production Guidance

You are helping the user manage their work using GTD (Getting Things Done) methodology.

Key points:
- Always query the graph before responding to questions
- Use natural, concise language
- Confirm destructive actions before executing
```

**Note:** Keep this minimal. Main instructions come from Claude Skill.

---

### Example 2: Test Overlay Structure

**File:** `tests/fixtures/system-prompt-test-overlay.md`

```markdown
# Test Harness Guidance

When running in test mode:
- Demonstrate expected behavior clearly
- Include relevant tool call information when helpful
- Maintain GTD semantics per specification
```

**File:** `tests/fixtures/system-prompt-live-mcp-overlay.md`

```markdown
# Live MCP Mode

You have access to real graph memory operations via MCP tools.
Perform actual operations and confirm the results.
```

**File:** `tests/fixtures/system-prompt-no-mcp-overlay.md`

```markdown
# Simulation Mode

Tool execution is unavailable. Simulate operations:
- Describe the plan clearly
- State: "Simulated: <action taken>"
- Provide representative results
```

---

## Summary

**Key Changes:**
1. ✅ Test harness uses `--append-system-prompt` instead of `--system-prompt`
2. ✅ Production addendum separate from test overlays
3. ✅ Test overlays never appear in production files
4. ✅ Claude Skill provides main instructions (outside test harness)

**What You Need to Do:**
1. Create `src/conversational-layer/system-prompt-addendum.md` (optional, for production guidance)
2. Keep test overlays in `tests/fixtures/` (already there)
3. Main instructions go in Claude Skill (separate from test harness)
4. Run tests normally - commands unchanged

**Result:**
- Clean separation of concerns
- Production content stays clean
- Test content stays isolated
- Flexible, maintainable architecture

# Conversational Layer - GTD Assistant

This directory contains the GTD conversational layer implementation using a **skill-based architecture** with progressive disclosure.

## Architecture

The conversational layer is split into three components:

### 1. Claude Skill (`.claude/skills/gtd-assistant/`)

**Location:** `/.claude/skills/gtd-assistant/`

The primary GTD methodology is defined as a Claude Skill, which provides:

- **SKILL.md** (~1500 words): Core principles, planning model, safety guardrails
- **references/** (~6000 words total, loaded as needed):
  - `conversation-patterns.md` - 25+ concrete examples of GTD interactions
  - `mcp-tools-guide.md` - Detailed MCP tool signatures and usage
  - `edge-cases.md` - Handling ambiguity, conflicts, and unusual situations
  - `query-algorithms.md` - Precise implementations of derived views

**Why a skill?**
- Progressive disclosure: Core principles always loaded, examples consulted as needed
- Prevents "teaching to the test": Model learns principles, not patterns
- Easier iteration: Update one reference file without touching core
- Standard Claude Code behaviors: Skill augments, doesn't replace

### 2. System Prompt Addendum (`system-prompt-addendum.md`)

**Location:** `src/conversational-layer/system-prompt-addendum.md`

A lean (~300 words) addendum that:
- Establishes GTD assistant identity and role
- Lists the 6 core behavioral principles
- Points to the gtd-assistant skill for detailed guidance
- Used via `--append-system-prompt` (follows standard Claude Code prompt)

**What it does NOT contain:**
- Examples (those are in the skill references)
- MCP tool signatures (in skill references)
- Query algorithms (in skill references)
- Edge case handling (in skill references)

### 3. Test Overlays (`tests/fixtures/`)

**Location:** `tests/fixtures/system-prompt-*-overlay.md`

Test-specific guidance for simulation vs live MCP modes:
- `system-prompt-test-overlay.md` - Minimal (most guidance in base prompt now)
- `system-prompt-live-mcp-overlay.md` - Live MCP execution rules
- `system-prompt-no-mcp-overlay.md` - Simulation mode rules

**Important:** These are ONLY for tests. They contain mode-specific instructions that don't belong in production prompts.

## Usage

### Production Use (with Claude Code)

The skill is auto-detected by Claude Code from `.claude/skills/gtd-assistant/`. Just run:

```bash
# With MCP configured
claude

# The skill will be available automatically
# The gtd-assistant skill will trigger on GTD-related requests
```

To explicitly load with the addendum:

```bash
claude --append-system-prompt "$(cat src/conversational-layer/system-prompt-addendum.md)"
```

### Testing

The test harness automatically uses both the addendum and test overlays:

```bash
# Run with refactored tests
python tests/test_conversational_layer.py --suite assistant --mode sim --test-cases refactored

# Run with original tests
python tests/test_conversational_layer.py --suite assistant --mode sim

# Run with Live MCP (requires MCP server running)
python tests/test_conversational_layer.py --suite assistant --mode real
```

The test harness:
1. Loads `system-prompt-addendum.md` (if exists) via `--append-system-prompt`
2. Adds test overlay (mode-specific) via `--append-system-prompt`
3. The skill is auto-detected by Claude Code

## File Structure

```
.claude/skills/gtd-assistant/
├── SKILL.md                           # Core principles (~1500 words)
└── references/
    ├── conversation-patterns.md       # 25+ examples (~3000 words)
    ├── mcp-tools-guide.md            # MCP tool reference (~1500 words)
    ├── edge-cases.md                 # Special situations (~800 words)
    └── query-algorithms.md           # Query implementations (~800 words)

src/conversational-layer/
├── README.md                          # This file
└── system-prompt-addendum.md         # Lean addendum (~300 words)

tests/fixtures/
├── system-prompt-test-overlay.md      # Empty (minimal)
├── system-prompt-live-mcp-overlay.md  # Live MCP rules
└── system-prompt-no-mcp-overlay.md    # Simulation rules
```

## Comparison with Previous Approach

### Old (Monolithic System Prompt)

**File:** `system-prompt.md` (~10k words)

- Everything in one file: principles, examples, mode handling, edge cases
- ~700 lines of examples always loaded
- Model pattern-matched examples rather than learning principles
- "Teaching to the test" problem: passed tests but failed in production
- Hard to iterate: changes affected everything

### New (Skill-Based Architecture)

**Core:** `SKILL.md` + `system-prompt-addendum.md` (~1800 words always loaded)
**References:** Consulted as needed (~6000 words)

- Progressive disclosure: Principles always loaded, examples as needed
- Model learns principles, consults examples when uncertain
- Prevents pattern-matching: Examples separated from core behavior
- Easy iteration: Update reference files independently
- Mode handling in test overlays (not production prompts)

## Migration Notes

If you have existing code using the old system-prompt.md:

1. **Tests:** Test harness automatically uses new structure (no changes needed)
2. **Production:** Use `claude` directly (skill auto-detected) or use `--append-system-prompt`
3. **Custom integrations:** Replace `--system-prompt system-prompt.md` with `--append-system-prompt system-prompt-addendum.md`

The old `system-prompt.md` is kept for backward compatibility but should not be used going forward.

## Benefits of New Architecture

1. **Reduced cognitive load:** Core prompt is 1/6th the size
2. **Prevents teaching to test:** Examples consulted on-demand, not memorized
3. **Easier iteration:** Update one reference file without touching core
4. **Standard Claude Code:** Skill augments standard behaviors, doesn't replace
5. **Progressive disclosure:** Model loads principles, consults details as needed
6. **Better production effectiveness:** Learns GTD methodology, not test patterns

## Future Improvements

- Add more conversation patterns as edge cases are discovered
- Refine core principles based on production usage
- Create additional reference files for Phase 2 features (ANY/ALL states, pattern detection)
- Optimize query algorithms for >1000 tasks (future scale)

## Questions?

See:
- `.claude/skills/gtd-assistant/SKILL.md` - Complete GTD methodology
- `specs/done/conversational-layer.md` - Original specification
- `tests/README_TESTING_IMPROVEMENTS.md` - Testing strategy

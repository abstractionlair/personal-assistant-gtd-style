# Isolated Test Environment

## Overview

The isolated test environment feature creates a clean installation directory that mimics production deployment, eliminating test contamination from development environment files while keeping all production tools available.

## Problem Solved

### Environment Contamination Issue

When running tests in the development directory, the assistant had access to:
- Development documentation (e.g., `PROPERTY_FIXES_NEEDED.md`, test reports)
- Filesystem directories that appeared as "projects" (e.g., `MultiModelCLIEmail`, `JobSearch`)
- Test artifacts and build outputs
- Development configuration files

This contamination caused tests to fail incorrectly. For example, the `edge_ask_vs_infer` test expected the assistant to find only test graph data (Website redesign, Mobile app launch), but instead it also found development files and directories.

### Solution

The isolated environment creates a clean installation directory with:
- Only the bundled system prompt (with test overlays)
- Isolated MCP configuration with isolated data path
- Neutral working directory (`/tmp/gtd-test-workspace`)
- No development artifacts

## Directory Structure

When isolated mode is enabled, the following structure is created:

```
.test-install/
└── gtd-assistant/
    ├── system-prompt.md       # Bundled prompt with overlays
    ├── mcp-config.json        # Isolated MCP config
    └── data/                   # Isolated graph storage
        ├── gtd-memory/         # Graph database
        └── mcp-calls.log       # MCP call logs

/tmp/gtd-test-workspace/       # Working directory for tests
```

## Usage

### Command-Line Flags

**Enable isolated environment:**
```bash
python tests/test_conversational_layer_new.py --isolated-env
```

**Keep installation after tests (for debugging):**
```bash
python tests/test_conversational_layer_new.py --isolated-env --keep-test-install
```

### Example Usage

**Run specific test with isolation:**
```bash
python tests/test_conversational_layer_new.py \
  --test-name edge_ask_vs_infer \
  --isolated-env \
  --runs 1
```

**Run full suite with isolation:**
```bash
python tests/test_conversational_layer_new.py \
  --isolated-env \
  --clean-graph-between-tests \
  --runs 5
```

**Debug with kept installation:**
```bash
python tests/test_conversational_layer_new.py \
  --test-name edge_ask_vs_infer \
  --isolated-env \
  --keep-test-install \
  --print-assistant-on-fail
```

## How It Works

### 1. Installation Setup

The `TestInstallation` class (in `tests/conversational_layer/install.py`) creates:

- **Installation directory:** `.test-install/gtd-assistant/`
- **Working directory:** `/tmp/gtd-test-workspace`
- **Data directory:** `.test-install/gtd-assistant/data/`

### 2. System Prompt Bundling

The base system prompt is combined with test overlays into a single file:

```python
# Base prompt
base_prompt = config.system_prompt_path.read_text()

# Overlays (from fixtures/)
overlays = config.get_test_overlays()  # test-overlay.md, live-mcp-overlay.md

# Bundle
bundled = base_prompt + "".join(overlays)
```

### 3. MCP Configuration Isolation

The MCP config is modified to use isolated paths:

```python
server_config["env"]["BASE_PATH"] = str(data_dir.resolve())
server_config["env"]["MCP_CALL_LOG"] = str(mcp_log_path.resolve())
```

**Important**: The graph cleanup function automatically reads the `BASE_PATH` from the MCP config, ensuring that `--clean-graph-between-tests` properly cleans the isolated location (not the default `.data/` directory).

### 4. Test Execution

Tests run from the neutral working directory with isolated config:

```python
subprocess.run(
    ["claude", "--profile", mcp_config_path, ...],
    cwd=workspace_dir,  # /tmp/gtd-test-workspace
    ...
)
```

### 5. Cleanup

By default, the installation is removed after tests complete. Use `--keep-test-install` to preserve it for debugging.

## When to Use

### Use Isolated Mode When:

- Testing assistant behavior without development environment influence
- Diagnosing environment contamination issues
- Running tests that depend on clean graph state
- Validating production-like behavior
- CI/CD pipeline testing (when implemented)

### Use Default Mode When:

- Debugging test failures where dev environment context is helpful
- Developing new tests (faster iteration without cleanup)
- Investigating issues specific to development environment
- Quick single-test validation

## Implementation Details

### Key Files

- `tests/conversational_layer/install.py`: Core installation management
- `tests/conversational_layer/runner.py`: Integration with test runner
- `tests/conversational_layer/config.py`: Configuration fields
- `tests/conversational_layer/cli.py`: Command-line interface

### Configuration Fields

```python
@dataclass
class Config:
    ...
    use_isolated_env: bool = False      # Enable isolated mode
    keep_test_install: bool = False     # Keep installation after tests
```

### Installation Lifecycle

1. **Setup** (before test suite):
   - `setup_test_installation(config)` called
   - Installation created with `force=True` (removes existing)
   - Config paths updated to use installation

2. **Execution** (during tests):
   - Tests run from isolated working directory
   - MCP uses isolated data path
   - No access to development files

3. **Teardown** (after test suite):
   - `teardown_test_installation(config)` called
   - Installation removed (unless `--keep-test-install`)
   - Working directory cleaned up

## Verification

To verify isolation is working:

1. **Check installation creation:**
   ```
   INFO     | Setting up isolated test installation...
   INFO     | Test installation created: .test-install/gtd-assistant
   INFO     | Working directory: /tmp/gtd-test-workspace
   ```

2. **Check cleanup:**
   ```
   INFO     | Cleaning up test installation...
   INFO     | Test installation cleaned up
   ```

3. **Verify data isolation:**
   ```bash
   ls -la .test-install/gtd-assistant/data/
   ```

4. **Check MCP log isolation:**
   ```bash
   cat .test-install/gtd-assistant/data/mcp-calls.log
   ```

## Troubleshooting

### Installation Already Exists

If you see `RuntimeError: Installation already exists`, either:
- Use `--keep-test-install` flag
- Manually remove: `rm -rf .test-install/`
- Installation setup uses `force=True` by default (should auto-remove)

### Tests Still Finding Dev Files

Check:
1. Working directory is `/tmp/gtd-test-workspace` (not project root)
2. MCP config uses isolated `BASE_PATH`
3. System prompt is bundled (not referencing original)

### MCP Connection Issues

Verify:
- MCP config path is correct: `.test-install/gtd-assistant/mcp-config.json`
- Data directory exists: `.test-install/gtd-assistant/data/`
- Permissions are correct on installation directory

## Future Enhancements

Potential improvements:

- **Multiple installations:** Support concurrent isolated environments
- **Installation caching:** Reuse installations across runs
- **Custom data fixtures:** Pre-populate isolated graph with test data
- **Sandbox environments:** Docker/containerized isolation
- **CI/CD integration:** Automated isolation in pipelines

## Comparison: Default vs Isolated

| Aspect | Default Mode | Isolated Mode |
|--------|--------------|---------------|
| Working directory | Project root | `/tmp/gtd-test-workspace` |
| System prompt | Original file | Bundled copy |
| MCP data | Shared `.data/` | Isolated `.test-install/data/` |
| Dev files visible | Yes | No |
| Setup time | Instant | ~1-2 seconds |
| Cleanup | None | Automatic (optional) |
| Use case | Development | Testing/CI |

## Example: edge_ask_vs_infer Test

### Before Isolation

```
ERROR | Test FAIL: edge_ask_vs_infer
Assistant found development files:
- PROPERTY_FIXES_NEEDED.md
- demo_report_v3.md
- filesystem directories (MultiModelCLIEmail, JobSearch)
Should have found only:
- Website redesign (from test fixture)
- Mobile app launch (from test fixture)
```

### After Isolation

```
INFO  | Setting up isolated test installation...
INFO  | Test installation created: .test-install/gtd-assistant
INFO  | Working directory: /tmp/gtd-test-workspace
INFO  | Test PASS: edge_ask_vs_infer (177.76s)
Assistant queried graph first (good) and found only test fixture data.
```

The test now fails only on conceptual errors (GTD model understanding), not environment contamination.

## Summary

The isolated test environment feature:
- **Eliminates** development environment contamination
- **Mimics** production deployment structure
- **Preserves** all production tool availability
- **Enables** clean, reproducible testing
- **Supports** both debugging and validation workflows

Use `--isolated-env` to ensure tests validate assistant behavior in production-like conditions without development artifacts influencing results.

# File Storage Backend MCP

TypeScript implementation of a local file-storage backend exposed as an MCP server. It provides six tools: `view`, `create`, `str_replace`, `insert`, `delete`, and `rename`, matching the specification used by the project.

## Prerequisites
- Node.js ≥ 18 (ES modules, fs/promises, crypto.randomUUID)
- npm ≥ 9

## Quick Start

Run unit tests (Vitest):

```
cd src/file-storage-backend/mcp
npm test
```

Build and run the MCP server:

```
cd src/file-storage-backend/mcp
npm run build
BASE_PATH="$PWD/.storage" npm start
```

The server reads `BASE_PATH` to determine the base directory for all operations. The path is created on first use.

## Scripts
- `npm test` — runs Vitest over `tests/**/*.test.ts`
- `npm run build` — compiles TypeScript to `dist/`
- `npm start` — runs the compiled server (`node dist/index.js`)
- `npm run dev` — runs from source via ts-node (requires ts-node globally or as a dev dependency)

## Tests and Vitest Config

This package includes a minimal `vitest.config.ts` that exports a plain object. This avoids importing from `vitest/config`, which can fail in environments where the `vitest` package export isn’t fully present (for example, partially populated `node_modules`).

Pinned test runner: `vitest@^4.0.5` (devDependency). This major pulls a Vite version with patched `esbuild`.

If you prefer the standard style, you can switch to:

```ts
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: { environment: 'node', include: ['tests/**/*.test.ts'] },
});
```

To use the standard import reliably, ensure your local `vitest` installation exposes the `config` subpath and that `node_modules/vitest/package.json` exists. If Vitest fails to load the config, revert to the plain-object export or clear any Vite temp cache:

```
rm -rf node_modules/.vite-temp
npm test
```

## Configuration

Environment variables:
- `BASE_PATH` — absolute path to the storage root (required for `start`/`dev`). All operations are contained within this directory (symlinks are resolved and validated).

## Tool Summary

- `view({ path })` → `{ type: 'file', content, encoding, size }` or `{ type: 'directory', entries }`
- `create({ path, content, encoding })` → void; auto‑creates parents; errors on existing files
- `str_replace({ path, old_str, new_str })` → void; requires unique match in UTF‑8 files
- `insert({ path, insert_line, new_str })` → void; 1-based line index, UTF‑8 only
- `delete({ path })` → void; removes files or empty directories
- `rename({ old_path, new_path })` → void; creates parent dirs; errors if destination exists

## Error Mapping

Domain errors (structured payloads) are thrown for common conditions: `file_not_found`, `file_exists`, `path_security`, `string_not_found`, `string_not_unique`, `binary_file`, `invalid_line_number`, `directory_not_empty`, `permission_denied`, `disk_full`, `invalid_encoding`.

Additionally, common Node.js `errno` codes are mapped to domain errors in both the storage layer and the MCP server wrapper.

## Troubleshooting

- Vitest config error: “Cannot find module 'vitest/config' …”
  - Use the provided minimal `vitest.config.ts` (plain object export) or pin Vitest to a version that exposes the `config` subpath. Clear `node_modules/.vite-temp` and retry.

- npm install issues on macOS (`ENOTEMPTY`, `fsevents`):
  - Retry after closing apps scanning the directory (e.g., Finder, indexers). If necessary, remove `node_modules` and reinstall.

- Permission errors when manipulating files:
  - Ensure `BASE_PATH` is writable by your user; the storage enforces operations within this base.

- Windows symlink tests:
  - Symlink escape test is skipped on Windows; path containment is still enforced via normalization and realpath checks.

## Security & Dependency Policy

- Dev test runner pinned to `vitest@^4.0.5` to stay aligned with a secure Vite/esbuild chain.
- Top-level `overrides` pins `esbuild` to a known-compatible version already present in the lockfile:

```
"overrides": {
  "esbuild": "0.21.5"
}
```

Notes:
- The advisory referenced by `npm audit` targets esbuild’s dev server behavior. Our usage is test-only via Vitest/Vite transforms, not a dev HTTP server.
- When a patched `esbuild` release that satisfies your registry (e.g., `>=0.24.3`) is available in your environment, you can update the override accordingly.

To re-resolve dependencies locally with the override in effect:

```
cd src/file-storage-backend/mcp
npm install
npm audit
```

## Layout

- `src/` — TypeScript source (storage implementation, MCP server wiring)
- `tests/` — Vitest unit tests (storage contract and server tool layer)
- `dist/` — compiled JavaScript output (`npm run build`)
- `vitest.config.ts` — test configuration

## Notes

- The implementation performs atomic writes (temp-file + rename) and cleans up on failures.
- Text vs binary is detected by a strict UTF‑8 round‑trip; base64 payloads are validated by round‑trip normalization.
- Symlink containment is enforced by comparing `realpath` against the configured base.

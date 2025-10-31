# Graph Memory Core MCP Server (Skeleton)

This package contains the TypeScript skeleton for the ontology‑driven graph memory
server defined in `specs/doing/graph-memory-core.md`. It mirrors the workflow used
for Feature 1 (file-storage-backend) but leaves all behavioral logic unimplemented
so test writers and implementers can build on a consistent surface area.

## Project Layout

- `src/` — Skeleton TypeScript sources with complete interfaces, docstrings, and
  `NotImplementedError` stubs for every operation described in the specification.
- `tests/` — Vitest suites (unit, integration, and process‑level transport e2e).
- `dist/` — Generated output directory created by `npm run build`.

## Install & Build

From this package directory:

```bash
cd src/graph-memory-core/mcp
npm install
npm run build   # builds to dist/
```

The server binary (`node dist/index.js`) expects `BASE_PATH` to point at the
graph memory base directory described in the spec.

## Running Tests

This package uses Vitest. Tests are currently in the TDD RED phase and will fail
until implementation is added to the skeleton.

- Run all tests (unit + integration + e2e):
  ```bash
  cd src/graph-memory-core/mcp
  npm test
  ```

- Watch mode during development:
  ```bash
  npm run test:watch
  ```

- Run only unit/integration suites:
  ```bash
  npx vitest run tests/unit
  npx vitest run tests/integration
  ```

- Run only transport e2e (process‑level stdio) tests:
  ```bash
  npx vitest run tests/transport
  ```

Notes about e2e tests:
- Transport tests spawn the built server over stdio using the MCP client SDK and
  exercise real tool calls end‑to‑end.
- They dynamically import `@modelcontextprotocol/sdk` client modules and will
  auto‑skip if the client is unavailable. Running `npm install` in this package
  installs the SDK so the tests run.
- The suite builds the server once before running (via `npm run build`). No manual
  build step is required for e2e.

## Test Structure

- `tests/unit/` — Domain‑level tests of `MemoryGraph`, `Ontology`, and `Registry`
  using a lightweight in‑memory `FakeStorage` adapter (no real filesystem I/O).
- `tests/integration/` — Black‑box tests through `GraphMemoryMcpServer` (tool
  registration/handlers), without spawning a separate process.
- `tests/transport/` — Process‑level stdio e2e using MCP client transport; the
  server runs as a separate Node.js process.

## Troubleshooting

- If transport tests are skipped, ensure dependencies are installed in this
  package (`npm install`).
- If a transport test fails building the server, run `npm run build` and check
  for TypeScript errors.
- Node.js 18+ recommended.

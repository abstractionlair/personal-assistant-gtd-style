# GTD Ontology

GTD-specific ontology definitions and query helpers built on top of the in‑repo Graph Memory Core. Provides:

- Ontology bootstrap (Task, State, Context, UNSPECIFIED; DependsOn)
- Derived queries: Projects, Next Actions, Waiting For
- State evaluation (ANY/ALL) and completion propagation patterns

## Prerequisites

- Node 18+
- TypeScript 5+

## Install, Build, Test

- Build: `npm run build`
- Test: `npm test` (Jest + ts‑jest, ESM)

From this folder:

```
cd src/gtd-ontology
npm test -- --runInBand
```

## Quick Start (Programmatic)

Initialize the ontology and run derived queries using the GraphMemoryClient interface. In tests we adapt the in‑repo `MemoryGraph` to this interface; production code can adapt an MCP client similarly.

```ts
import { MemoryGraph } from "../graph-memory-core/mcp/src/memoryGraph.js";
import type { GraphMemoryServerConfig } from "../graph-memory-core/mcp/src/types.js";
import type { GraphMemoryClient } from "./src/types.js";
import { initializeGTDOntology } from "./src/initialize.js";
import { queryProjects, queryNextActions, queryWaitingFor } from "./src/queries.js";

async function main() {
  const config: GraphMemoryServerConfig = { basePath: "/data" };
  const graph = await MemoryGraph.initialize(config);

  const client: GraphMemoryClient = {
    createOntology: req => graph.createOntology(req as any),
    ensureSingletonNode: req => graph.ensureSingletonNode(req as any),
    queryNodes: req => graph.queryNodes(req as any),
    queryConnections: req => graph.queryConnections(req as any),
    getConnectedNodes: req => graph.getConnectedNodes(req as any),
    getNode: req => graph.getNode(req),
    updateNode: req => graph.updateNode({ node_id: req.id, ...req } as any)
  };

  await initializeGTDOntology(client);

  const projects = await queryProjects(client);
  const next = await queryNextActions(client);
  const waiting = await queryWaitingFor(client);

  console.log({ projects: projects.length, next: next.length, waiting: waiting.length });
}

main();
```

## Concepts

- UNSPECIFIED singleton: Attach `DependsOn(Task|State → UNSPECIFIED)` to indicate decomposition needed; this blocks Next Actions until replaced with concrete dependencies.
- State logic:
  - ANY: true if any dependency satisfied
  - ALL: true if all dependencies satisfied; zero dependencies imply true
  - MANUAL: set by user; `updateStateBasedOnLogic` is a no‑op
  - IMMUTABLE: fixed; `updateStateBasedOnLogic` is a no‑op
- Completion propagation: Use `propagateCompletion` when marking a Task complete or a MANUAL State true to cascade updates through dependent States.

## Notes

- Performance tests target <2s for representative datasets (in‑memory). If CI hardware is slow, consider running without perf tests or increasing thresholds.

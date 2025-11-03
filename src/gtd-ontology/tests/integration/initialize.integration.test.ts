import { MemoryGraph } from '../../../graph-memory-core/mcp/src/memoryGraph.js';
import type { GraphMemoryServerConfig } from '../../../graph-memory-core/mcp/src/types.js';
import { createTestGraphContext } from '../helpers/graphTestClient.js';
import { buildUnspecifiedSingletonRequest, UNSPECIFIED_NODE_CONTENT } from '../../src/schema.js';
import { initializeGTDOntology } from '../../src/initialize.js';

describe('initializeGTDOntology', () => {
  it('loads GTD ontology and persists across restarts (AC1, AC2)', async () => {
    const context = await createTestGraphContext();

    const result = await initializeGTDOntology(context.client);
    expect(result).toEqual({ ok: true });

    const ontology = await context.graph.getOntology();
    expect(ontology.node_types).toEqual(
      expect.arrayContaining(['Task', 'State', 'Context', 'UNSPECIFIED'])
    );
    expect(ontology.connection_types).toContainEqual({
      name: 'DependsOn',
      from_types: ['Task', 'State'],
      to_types: ['Task', 'State', 'Context', 'UNSPECIFIED']
    });

    const config: GraphMemoryServerConfig = { basePath: '/virtual' };
    const rehydratedGraph = await MemoryGraph.initialize(config, context.storage);
    const persistedOntology = await rehydratedGraph.getOntology();
    expect(persistedOntology.node_types).toEqual(
      expect.arrayContaining(['Task', 'State', 'Context', 'UNSPECIFIED'])
    );
  });

  it('creates UNSPECIFIED singleton idempotently (AC3 – AC5)', async () => {
    const context = await createTestGraphContext();

    const firstRun = await initializeGTDOntology(context.client);
    expect(firstRun.ok).toBe(true);

    const singletonQuery = await context.client.queryNodes({ type: 'UNSPECIFIED' });
    expect(singletonQuery.node_ids).toHaveLength(1);

    const singletonMeta = await context.client.getNode({ node_id: singletonQuery.node_ids[0] });
    expect(singletonMeta.type).toBe('UNSPECIFIED');
    expect(singletonMeta.properties).toEqual({});

    const secondRun = await initializeGTDOntology(context.client);
    expect(secondRun.ok).toBe(true);

    const repeatQuery = await context.client.queryNodes({ type: 'UNSPECIFIED' });
    expect(repeatQuery.node_ids).toHaveLength(1);
    expect(repeatQuery.node_ids[0]).toBe(singletonQuery.node_ids[0]);

    const singletonRequest = buildUnspecifiedSingletonRequest();
    expect(singletonRequest).toEqual({
      type: 'UNSPECIFIED',
      content: UNSPECIFIED_NODE_CONTENT,
      encoding: 'utf-8'
    });
  });
});

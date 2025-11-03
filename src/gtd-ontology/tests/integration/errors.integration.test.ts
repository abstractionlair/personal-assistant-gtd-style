import { InvalidTopologyError, OntologyNotFoundError } from '../../../graph-memory-core/mcp/src/errors.js';
import { createTestGraphContext } from '../helpers/graphTestClient.js';
import { bootstrapOntology } from '../helpers/bootstrap.js';
import {
  createContextNode,
  createDependsOnConnection,
  createState,
  createTask
} from '../helpers/nodeBuilders.js';
import { buildUnspecifiedSingletonRequest } from '../../src/schema.js';

describe('GTD ontology error handling', () => {
  it('rejects connections with invalid sources (AC30, AC31)', async () => {
    const context = await createTestGraphContext();
    const unspecifiedId = await bootstrapOntology(context);

    const task = await createTask(context.graph, { title: 'Outline goals' });
    const state = await createState(context.graph, { title: 'Goals approved', logic: 'ALL' });
    const contextNode = await createContextNode(context.graph, { title: '@studio', isAvailable: true });

    await expect(
      createDependsOnConnection(context.graph, unspecifiedId, task.id)
    ).rejects.toThrow(InvalidTopologyError);

    await expect(
      createDependsOnConnection(context.graph, contextNode.id, state.id)
    ).rejects.toThrow(InvalidTopologyError);
  });

  it('returns existing singleton without creating duplicates (AC32)', async () => {
    const context = await createTestGraphContext();
    await bootstrapOntology(context);

    const first = await context.client.ensureSingletonNode(buildUnspecifiedSingletonRequest());
    expect(first.created).toBe(false); // already created during bootstrap

    const second = await context.client.ensureSingletonNode(buildUnspecifiedSingletonRequest());
    expect(second.created).toBe(false);
    expect(second.node_id).toBe(first.node_id);
  });

  it('prevents deletion of the UNSPECIFIED singleton (AC33)', async () => {
    const context = await createTestGraphContext();
    const unspecifiedId = await bootstrapOntology(context);

    await expect(context.graph.deleteNode({ node_id: unspecifiedId })).rejects.toThrow();

    const query = await context.client.queryNodes({ type: 'UNSPECIFIED' });
    expect(query.node_ids).toContain(unspecifiedId);
  });

  it('requires ontology before graph interactions', async () => {
    const context = await createTestGraphContext();

    await expect(
      createDependsOnConnection(context.graph, 'a', 'b')
    ).rejects.toThrow(OntologyNotFoundError);
  });
});

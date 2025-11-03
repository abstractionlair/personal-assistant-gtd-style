import { createTestGraphContext } from '../helpers/graphTestClient.js';
import { bootstrapOntology } from '../helpers/bootstrap.js';
import {
  createDependsOnConnection,
  createState,
  createTask
} from '../helpers/nodeBuilders.js';
import { updateStateBasedOnLogic, propagateCompletion } from '../../src/stateLogic.js';
import type { StateNode, StateProperties } from '../../src/types.js';

function asStateNode(meta: Awaited<ReturnType<typeof createState>>): StateNode {
  return {
    id: meta.id,
    type: 'State',
    properties: meta.properties as StateProperties,
    created: meta.created,
    modified: meta.modified,
    content_format: meta.content_format
  };
}

describe('State logic evaluation and completion propagation', () => {
  it('updates ANY and ALL States based on dependency completion (AC24 support, AC36)', async () => {
    const context = await createTestGraphContext();
    await bootstrapOntology(context);

    const completeTask = await createTask(context.graph, {
      title: 'Compile financials',
      isComplete: true
    });
    const incompleteTask = await createTask(context.graph, {
      title: 'Gather approvals',
      isComplete: false
    });

    const anyState = await createState(context.graph, {
      title: 'Initial review possible',
      isTrue: false,
      logic: 'ANY'
    });
    const allState = await createState(context.graph, {
      title: 'Ready for launch',
      isTrue: false,
      logic: 'ALL'
    });

    await createDependsOnConnection(context.graph, anyState.id, completeTask.id);
    await createDependsOnConnection(context.graph, anyState.id, incompleteTask.id);
    await createDependsOnConnection(context.graph, allState.id, completeTask.id);
    await createDependsOnConnection(context.graph, allState.id, incompleteTask.id);

    await updateStateBasedOnLogic({ client: context.client, state: asStateNode(anyState) });
    const updatedAnyState = await context.client.getNode({ node_id: anyState.id });
    expect(updatedAnyState.properties.isTrue).toBe(true);

    await updateStateBasedOnLogic({ client: context.client, state: asStateNode(allState) });
    const updatedAllState = await context.client.getNode({ node_id: allState.id });
    expect(updatedAllState.properties.isTrue).toBe(false);

    await context.client.updateNode({
      id: incompleteTask.id,
      properties: { isComplete: true }
    });

    await updateStateBasedOnLogic({ client: context.client, state: asStateNode(allState) });
    const reevaluatedAllState = await context.client.getNode({ node_id: allState.id });
    expect(reevaluatedAllState.properties.isTrue).toBe(true);
  });

  it('propagates completion through dependent States (AC37)', async () => {
    const context = await createTestGraphContext();
    await bootstrapOntology(context);

    const rootTask = await createTask(context.graph, { title: 'Build prototype', isComplete: false });
    const gatingState = await createState(context.graph, {
      title: 'Prototype approved',
      isTrue: false,
      logic: 'ALL'
    });
    const downstreamState = await createState(context.graph, {
      title: 'Launch authorized',
      isTrue: false,
      logic: 'ANY'
    });

    await createDependsOnConnection(context.graph, gatingState.id, rootTask.id);
    await createDependsOnConnection(context.graph, downstreamState.id, gatingState.id);

    await propagateCompletion({ client: context.client, nodeId: rootTask.id });

    const updatedTask = await context.client.getNode({ node_id: rootTask.id });
    const updatedGatingState = await context.client.getNode({ node_id: gatingState.id });
    const updatedDownstreamState = await context.client.getNode({ node_id: downstreamState.id });

    expect(updatedTask.properties.isComplete).toBe(true);
    expect(updatedGatingState.properties.isTrue).toBe(true);
    expect(updatedDownstreamState.properties.isTrue).toBe(true);
  });

  it('sets ALL State with zero dependencies to true', async () => {
    const context = await createTestGraphContext();
    await bootstrapOntology(context);

    const allNoDeps = await createState(context.graph, {
      title: 'All-true-without-deps',
      isTrue: false,
      logic: 'ALL'
    });

    await updateStateBasedOnLogic({ client: context.client, state: asStateNode(allNoDeps) });

    const updated = await context.client.getNode({ node_id: allNoDeps.id });
    expect(updated.properties.isTrue).toBe(true);
  });

  it('does not change MANUAL or IMMUTABLE states with updateStateBasedOnLogic', async () => {
    const context = await createTestGraphContext();
    await bootstrapOntology(context);

    const completeTask = await createTask(context.graph, { title: 'Done', isComplete: true });

    const manualState = await createState(context.graph, {
      title: 'Manual gate',
      isTrue: false,
      logic: 'MANUAL'
    });
    const immutableState = await createState(context.graph, {
      title: 'Immutable gate',
      isTrue: false,
      logic: 'IMMUTABLE'
    });

    await createDependsOnConnection(context.graph, manualState.id, completeTask.id);
    await createDependsOnConnection(context.graph, immutableState.id, completeTask.id);

    await updateStateBasedOnLogic({ client: context.client, state: asStateNode(manualState) });
    await updateStateBasedOnLogic({ client: context.client, state: asStateNode(immutableState) });

    const manualAfter = await context.client.getNode({ node_id: manualState.id });
    const immutableAfter = await context.client.getNode({ node_id: immutableState.id });
    expect(manualAfter.properties.isTrue).toBe(false);
    expect(immutableAfter.properties.isTrue).toBe(false);
  });

  it('propagateCompletion sets MANUAL state true when invoked directly', async () => {
    const context = await createTestGraphContext();
    await bootstrapOntology(context);

    const manual = await createState(context.graph, {
      title: 'Manual switch',
      isTrue: false,
      logic: 'MANUAL'
    });

    await propagateCompletion({ client: context.client, nodeId: manual.id });

    const after = await context.client.getNode({ node_id: manual.id });
    expect(after.properties.isTrue).toBe(true);
  });
});

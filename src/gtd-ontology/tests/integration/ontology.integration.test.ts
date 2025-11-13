import { createTestGraphContext } from '../helpers/graphTestClient.js';
import { bootstrapOntology } from '../helpers/bootstrap.js';
import {
  createContextNode,
  createDependsOnConnection,
  createState,
  createTask
} from '../helpers/nodeBuilders.js';

describe('GTD ontology node and connection behaviors', () => {
  it('supports creating Task, State, and Context nodes with expected properties (AC6 – AC10)', async () => {
    const context = await createTestGraphContext();
    await bootstrapOntology(context);

    const task = await createTask(context.graph, {
      title: 'Clarify feature scope',
      responsibleParty: 'me'
    });
    expect(task.type).toBe('Task');
    expect(task.properties).toEqual({
      isComplete: false,
      responsibleParty: 'me'
    });
    expect(new Date(task.created).toString()).not.toBe('Invalid Date');
    expect(new Date(task.modified).toString()).not.toBe('Invalid Date');

    const state = await createState(context.graph, {
      title: 'Dependencies gathered',
      isTrue: true,
      logic: 'ALL'
    });
    expect(state.type).toBe('State');
    expect(state.properties).toEqual({
      isTrue: true,
      logic: 'ALL'
    });
    expect(new Date(state.created).toString()).not.toBe('Invalid Date');

    const contextNode = await createContextNode(context.graph, {
      title: '@computer',
      isTrue: true
    });
    expect(contextNode.type).toBe('Context');
    expect(contextNode.properties).toEqual({
      isTrue: true
    });
  });

  it('allows DependsOn connections across all supported topologies (AC11 – AC17)', async () => {
    const context = await createTestGraphContext();
    const unspecifiedId = await bootstrapOntology(context);

    const [taskA, taskB] = await Promise.all([
      createTask(context.graph, { title: 'Plan vacation' }),
      createTask(context.graph, { title: 'Book flights' })
    ]);
    const [stateA, stateB] = await Promise.all([
      createState(context.graph, { title: 'Budget approved', logic: 'ANY' }),
      createState(context.graph, { title: 'All documents ready', logic: 'ALL' })
    ]);
    const contextNode = await createContextNode(context.graph, { title: '@phone', isTrue: false });

    // Task -> Task
    await createDependsOnConnection(context.graph, taskA.id, taskB.id);

    // Task -> State
    await createDependsOnConnection(context.graph, taskA.id, stateA.id);

    // Task -> Context
    await createDependsOnConnection(context.graph, taskA.id, contextNode.id);

    // State -> Task
    await createDependsOnConnection(context.graph, stateA.id, taskB.id);

    // State -> State
    await createDependsOnConnection(context.graph, stateA.id, stateB.id);

    // Task -> UNSPECIFIED
    await createDependsOnConnection(context.graph, taskB.id, unspecifiedId);

    // State -> UNSPECIFIED
    await createDependsOnConnection(context.graph, stateB.id, unspecifiedId);
  });
});

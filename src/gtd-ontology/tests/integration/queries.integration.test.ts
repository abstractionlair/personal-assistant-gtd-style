import { createTestGraphContext } from '../helpers/graphTestClient.js';
import { bootstrapOntology } from '../helpers/bootstrap.js';
import {
  createContextNode,
  createDependsOnConnection,
  createState,
  createTask
} from '../helpers/nodeBuilders.js';
import { queryProjects, queryNextActions, queryWaitingFor } from '../../src/queries.js';

describe('GTD derived queries', () => {
  it('returns only Tasks with outgoing dependencies for Projects (AC18 – AC20)', async () => {
    const context = await createTestGraphContext();
    await bootstrapOntology(context);

    const dependency = await createTask(context.graph, { title: 'Draft outline', isComplete: true });
    const projectA = await createTask(context.graph, { title: 'Write report' });
    const projectB = await createTask(context.graph, { title: 'Plan launch' });
    const standalone = await createTask(context.graph, { title: 'Buy milk' });
    const stateDependency = await createState(context.graph, { title: 'Launch approved', isTrue: true });

    await createDependsOnConnection(context.graph, projectA.id, dependency.id);
    await createDependsOnConnection(context.graph, projectB.id, stateDependency.id);

    const projects = await queryProjects(context.client);
    const projectIds = projects.map(project => project.id);

    expect(projectIds).toEqual(expect.arrayContaining([projectA.id, projectB.id]));
    expect(projectIds).not.toContain(standalone.id);
  });

  it('identifies actionable Tasks for Next Actions and excludes blocked ones (AC21 – AC26)', async () => {
    const context = await createTestGraphContext();
    const unspecifiedId = await bootstrapOntology(context);

    const completedDependency = await createTask(context.graph, {
      title: 'Collect receipts',
      isComplete: true
    });
    const incompleteDependency = await createTask(context.graph, {
      title: 'Review budget request',
      isComplete: false
    });
    const trueState = await createState(context.graph, { title: 'Laptop charged', isTrue: true });
    const falseState = await createState(context.graph, { title: 'Approval granted', isTrue: false });
    const availableContext = await createContextNode(context.graph, { title: '@office', isAvailable: true });
    const unavailableContext = await createContextNode(context.graph, {
      title: '@workshop',
      isAvailable: false
    });

    const readyTask = await createTask(context.graph, { title: 'Submit reimbursement' });
    const alreadyComplete = await createTask(context.graph, { title: 'Archive receipts', isComplete: true });
    const blockedByTask = await createTask(context.graph, { title: 'Finalize proposal' });
    const blockedByState = await createTask(context.graph, { title: 'Kickoff project' });
    const blockedByContext = await createTask(context.graph, { title: 'Weld prototype' });
    const blockedByUnspecified = await createTask(context.graph, { title: 'Define integration plan' });
    const standalone = await createTask(context.graph, { title: 'Clear inbox' });

    await createDependsOnConnection(context.graph, readyTask.id, completedDependency.id);
    await createDependsOnConnection(context.graph, readyTask.id, trueState.id);
    await createDependsOnConnection(context.graph, readyTask.id, availableContext.id);

    await createDependsOnConnection(context.graph, blockedByTask.id, incompleteDependency.id);
    await createDependsOnConnection(context.graph, blockedByState.id, falseState.id);
    await createDependsOnConnection(context.graph, blockedByContext.id, unavailableContext.id);
    await createDependsOnConnection(context.graph, blockedByUnspecified.id, unspecifiedId);

    const nextActions = await queryNextActions(context.client);
    const nextActionIds = nextActions.map(task => task.id);

    expect(nextActionIds).toEqual(expect.arrayContaining([readyTask.id, standalone.id]));
    expect(nextActionIds).not.toContain(alreadyComplete.id);
    expect(nextActionIds).not.toContain(blockedByTask.id);
    expect(nextActionIds).not.toContain(blockedByState.id);
    expect(nextActionIds).not.toContain(blockedByContext.id);
    expect(nextActionIds).not.toContain(blockedByUnspecified.id);
  });

  it('returns Tasks waiting on external parties (AC27 – AC29)', async () => {
    const context = await createTestGraphContext();
    await bootstrapOntology(context);

    const waiting = await createTask(context.graph, {
      title: 'Follow up with vendor',
      responsibleParty: 'acme-corp'
    });
    const selfAssigned = await createTask(context.graph, {
      title: 'Refine messaging',
      responsibleParty: 'me'
    });
    const noOwner = await createTask(context.graph, { title: 'Capture meeting notes' });

    const waitingFor = await queryWaitingFor(context.client);
    const waitingIds = waitingFor.map(task => task.id);

    expect(waitingIds).toContain(waiting.id);
    expect(waitingIds).not.toContain(selfAssigned.id);
    expect(waitingIds).not.toContain(noOwner.id);
  });
});

import { performance } from 'node:perf_hooks';
import { createTestGraphContext } from '../helpers/graphTestClient.js';
import { bootstrapOntology } from '../helpers/bootstrap.js';
import {
  createContextNode,
  createDependsOnConnection,
  createState,
  createTask
} from '../helpers/nodeBuilders.js';
import { queryProjects, queryNextActions } from '../../src/queries.js';

describe('GTD ontology performance characteristics', () => {
  it('executes Projects query within 2 seconds on representative dataset (AC34)', async () => {
    const context = await createTestGraphContext();
    await bootstrapOntology(context);

    const totalTasks = 100;
    const projectCount = 50;
    const dependenciesPerProject = 10; // 50 projects * 10 = 500 connections

    const tasks = [];
    for (let i = 0; i < totalTasks; i += 1) {
      tasks.push(
        await createTask(context.graph, {
          title: `Task ${i}`,
          isComplete: i % 3 === 0
        })
      );
    }

    for (let projectIndex = 0; projectIndex < projectCount; projectIndex += 1) {
      const project = tasks[projectIndex];
      for (let dep = 0; dep < dependenciesPerProject; dep += 1) {
        const dependencyIndex =
          projectCount + ((projectIndex + dep) % (totalTasks - projectCount));
        const dependency = tasks[dependencyIndex];
        await createDependsOnConnection(context.graph, project.id, dependency.id);
      }
    }

    const start = performance.now();
    const result = await queryProjects(context.client);
    const durationMs = performance.now() - start;

    expect(result.length).toBeGreaterThan(0);
    expect(durationMs).toBeLessThan(2000);
  });

  it('executes Next Actions query within 2 seconds on representative dataset (AC35)', async () => {
    const context = await createTestGraphContext();
    await bootstrapOntology(context);

    const totalTasks = 100;
    const totalStates = 50;
    const totalContexts = 20;
    const dependenciesPerTask = 4; // 100 tasks * (4 state deps + 1 context) = 500 connections

    const tasks = [];
    for (let i = 0; i < totalTasks; i += 1) {
      tasks.push(
        await createTask(context.graph, {
          title: `Action ${i}`,
          isComplete: false
        })
      );
    }

    const states = [];
    for (let i = 0; i < totalStates; i += 1) {
      states.push(
        await createState(context.graph, {
          title: `State ${i}`,
          isTrue: i % 2 === 0,
          logic: 'ANY'
        })
      );
    }

    const contexts = [];
    for (let i = 0; i < totalContexts; i += 1) {
      contexts.push(
        await createContextNode(context.graph, {
          title: `@context-${i}`,
          isTrue: i % 3 !== 0
        })
      );
    }

    for (let taskIndex = 0; taskIndex < totalTasks; taskIndex += 1) {
      const task = tasks[taskIndex];
      for (let dep = 0; dep < dependenciesPerTask; dep += 1) {
        const state = states[(taskIndex + dep) % totalStates];
        await createDependsOnConnection(context.graph, task.id, state.id);
      }
      const contextNode = contexts[taskIndex % totalContexts];
      await createDependsOnConnection(context.graph, task.id, contextNode.id);
    }

    const start = performance.now();
    const result = await queryNextActions(context.client);
    const durationMs = performance.now() - start;

    expect(Array.isArray(result)).toBe(true);
    expect(durationMs).toBeLessThan(2000);
  });
});

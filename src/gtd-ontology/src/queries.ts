/**
 * Module: queries
 * Purpose: Define derived GTD query entry points (Projects, Next Actions, Waiting For).
 * Created: 2025-11-02
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/doing/gtd-ontology.md
 */

import type {
  ContextProperties,
  GraphMemoryClient,
  NodeMetadata,
  StateProperties,
  TaskNode
} from './types.js';
import { DEPENDENCY_CONNECTION_TYPE } from './types.js';

async function getTaskNode(client: GraphMemoryClient, nodeId: string): Promise<TaskNode> {
  const metadata = await client.getNode({ node_id: nodeId });
  if (metadata.type !== 'Task') {
    throw new Error(`Expected Task node metadata but received type "${metadata.type}".`);
  }
  return {
    id: metadata.id,
    type: 'Task',
    properties: metadata.properties as TaskNode['properties'],
    created: metadata.created,
    modified: metadata.modified,
    content_format: metadata.content_format
  };
}

function dependencyIsSatisfied(metadata: NodeMetadata): boolean {
  switch (metadata.type) {
    case 'Task':
      return Boolean((metadata.properties as { isComplete?: unknown }).isComplete);
    case 'State':
      return Boolean((metadata.properties as StateProperties).isTrue);
    case 'Context':
      return Boolean((metadata.properties as ContextProperties).isAvailable);
    case 'UNSPECIFIED':
      return false;
    default:
      return false;
  }
}

function isTaskAssignedToSelf(task: TaskNode): boolean {
  const responsible = task.properties.responsibleParty;
  return responsible === undefined || responsible === 'me';
}

/**
 * Fetch Tasks that qualify as Projects (i.e., have outgoing DependsOn connections).
 *
 * @param client - Graph memory facade used to run query_nodes and query_connections.
 * @returns Collection of Task nodes representing Projects.
 */
export async function queryProjects(client: GraphMemoryClient): Promise<TaskNode[]> {
  const { node_ids: taskIds } = await client.queryNodes({ type: 'Task' });

  const projects: TaskNode[] = [];
  for (const taskId of taskIds) {
    const connections = await client.queryConnections({
      from_node_id: taskId,
      type: DEPENDENCY_CONNECTION_TYPE
    });

    if (connections.connection_ids.length > 0) {
      projects.push(await getTaskNode(client, taskId));
    }
  }

  return projects;
}

/**
 * Fetch actionable Tasks whose immediate dependencies are satisfied (Next Actions).
 *
 * @param client - Graph memory facade used to evaluate dependencies.
 * @returns Collection of Task nodes that can be worked on immediately.
 */
export async function queryNextActions(client: GraphMemoryClient): Promise<TaskNode[]> {
  const { node_ids: taskIds } = await client.queryNodes({
    type: 'Task',
    properties: { isComplete: false }
  });

  const nextActions: TaskNode[] = [];

  for (const taskId of taskIds) {
    const task = await getTaskNode(client, taskId);

    if (!isTaskAssignedToSelf(task)) {
      continue;
    }

    const { node_ids: dependencyIds } = await client.getConnectedNodes({
      node_id: taskId,
      connection_type: DEPENDENCY_CONNECTION_TYPE,
      direction: 'out'
    });

    if (dependencyIds.length === 0) {
      nextActions.push(task);
      continue;
    }

    const dependencyMetadata: NodeMetadata[] = await Promise.all(
      dependencyIds.map(node_id => client.getNode({ node_id }))
    );

    const allSatisfied = dependencyMetadata.every(dependencyIsSatisfied);
    if (allSatisfied) {
      nextActions.push(task);
    }
  }

  return nextActions;
}

/**
 * Fetch Tasks waiting on external parties (responsibleParty !== "me").
 *
 * @param client - Graph memory facade used to inspect Task properties.
 * @returns Collection of Task nodes awaiting external completion.
 */
export async function queryWaitingFor(client: GraphMemoryClient): Promise<TaskNode[]> {
  const { node_ids: taskIds } = await client.queryNodes({
    type: 'Task',
    properties: { isComplete: false }
  });

  const waiting: TaskNode[] = [];
  for (const taskId of taskIds) {
    const task = await getTaskNode(client, taskId);
    const responsible = task.properties.responsibleParty;
    if (responsible && responsible !== 'me') {
      waiting.push(task);
    }
  }

  return waiting;
}

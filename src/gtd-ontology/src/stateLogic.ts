/**
 * Module: stateLogic
 * Purpose: Document GTD state evaluation and completion propagation entry points.
 * Created: 2025-11-02
 * Skeleton by: OpenAI Codex (GPT-5)
 * Spec: specs/doing/gtd-ontology.md
 */

import type {
  ContextProperties,
  GraphMemoryClient,
  NodeId,
  NodeMetadata,
  StateNode
} from './types.js';
import { DEPENDENCY_CONNECTION_TYPE } from './types.js';
import type { StateProperties, TaskProperties } from './types.js';

/**
 * Input parameters required to evaluate State logic and update its truthiness.
 */
export interface UpdateStateBasedOnLogicParams {
  client: GraphMemoryClient;
  state: StateNode;
}

/**
 * Update a State node's `isTrue` value based on its logic type and dependencies.
 *
 * Responsibilities (per spec):
 * - Retrieve dependencies via getConnectedNodes.
 * - Evaluate ANY/ALL logic against Task/State completion.
 * - Leave MANUAL and IMMUTABLE States untouched.
 * - Persist updated `isTrue` and timestamps via updateNode.
 *
 * @param params - State context and graph client.
 * @throws NotImplementedError Until dependency evaluation is implemented.
 */
export async function updateStateBasedOnLogic(
  params: UpdateStateBasedOnLogicParams
): Promise<void> {
  const { client, state } = params;
  const logic = state.properties.logic;

  if (logic === 'MANUAL' || logic === 'IMMUTABLE') {
    return;
  }

  const { node_ids: dependencyIds } = await client.getConnectedNodes({
    node_id: state.id,
    connection_type: DEPENDENCY_CONNECTION_TYPE,
    direction: 'out'
  });

  if (logic === 'ANY') {
    const dependencies = await Promise.all(
      dependencyIds.map(node_id => client.getNode({ node_id }))
    );
    const anySatisfied = dependencies.some(dependencyIsSatisfied);
    if (anySatisfied !== state.properties.isTrue) {
      await client.updateNode({
        id: state.id,
        properties: { isTrue: anySatisfied }
      });
      state.properties.isTrue = anySatisfied;
    }
    return;
  }

  // logic === 'ALL'
  if (dependencyIds.length === 0) {
    if (!state.properties.isTrue) {
      await client.updateNode({
        id: state.id,
        properties: { isTrue: true }
      });
      state.properties.isTrue = true;
    }
    return;
  }

  const dependencies = await Promise.all(
    dependencyIds.map(node_id => client.getNode({ node_id }))
  );
  const allSatisfied = dependencies.every(dependencyIsSatisfied);
  if (allSatisfied !== state.properties.isTrue) {
    await client.updateNode({
      id: state.id,
      properties: { isTrue: allSatisfied }
    });
    state.properties.isTrue = allSatisfied;
  }
}

/**
 * Input parameters required to propagate completion forward through dependent nodes.
 */
export interface CompletionPropagationParams {
  client: GraphMemoryClient;
  nodeId: NodeId;
}

/**
 * Propagate completion/true state forward to dependent nodes, updating States as needed.
 *
 * Responsibilities (per spec):
 * - Mark node complete (Task) or true (MANUAL State) before propagation.
 * - Query dependents with queryConnections and getNode.
 * - Re-evaluate dependent States via updateStateBasedOnLogic.
 * - Recurse when States become true to ensure cascading updates.
 *
 * @param params - Completed node identifier and graph client.
 * @throws NotImplementedError Until propagation behavior is implemented.
 */
export async function propagateCompletion(
  params: CompletionPropagationParams
): Promise<void> {
  const { client, nodeId } = params;
  const metadata = await client.getNode({ node_id: nodeId });

  if (metadata.type === 'Task') {
    const properties = metadata.properties as TaskProperties;
    if (!properties.isComplete) {
      await client.updateNode({
        id: metadata.id,
        properties: { isComplete: true }
      });
    }
  } else if (metadata.type === 'State') {
    const properties = metadata.properties as StateProperties;
    if (properties.logic === 'MANUAL' && !properties.isTrue) {
      await client.updateNode({
        id: metadata.id,
        properties: { isTrue: true }
      });
      properties.isTrue = true;
    }
  }

  const { node_ids: dependentIds } = await client.getConnectedNodes({
    node_id: metadata.id,
    connection_type: DEPENDENCY_CONNECTION_TYPE,
    direction: 'in'
  });

  for (const dependentId of dependentIds) {
    const dependentMeta = await client.getNode({ node_id: dependentId });
    if (dependentMeta.type !== 'State') {
      continue;
    }

    const dependentState: StateNode = {
      id: dependentMeta.id,
      type: 'State',
      properties: dependentMeta.properties as StateProperties,
      created: dependentMeta.created,
      modified: dependentMeta.modified,
      content_format: dependentMeta.content_format
    };

    await updateStateBasedOnLogic({ client, state: dependentState });

    const refreshedMeta = await client.getNode({ node_id: dependentId });
    const refreshedProps = refreshedMeta.properties as StateProperties;
    const logic = refreshedProps.logic;

    if ((logic === 'ANY' || logic === 'ALL') && refreshedProps.isTrue) {
      await propagateCompletion({ client, nodeId: dependentId });
    }
  }
}

function dependencyIsSatisfied(metadata: NodeMetadata): boolean {
  switch (metadata.type) {
    case 'Task':
      return Boolean((metadata.properties as { isComplete?: unknown }).isComplete);
    case 'State':
      return Boolean((metadata.properties as StateProperties).isTrue);
    case 'Context':
      return Boolean((metadata.properties as ContextProperties).isTrue);
    case 'UNSPECIFIED':
      return false;
    default:
      return false;
  }
}

import type { TestGraphContext } from './graphTestClient.js';
import { buildGtdOntologyDefinition, buildUnspecifiedSingletonRequest } from '../../src/schema.js';

/**
 * Fully initialize the GTD ontology within the supplied graph context.
 *
 * @returns Node identifier for the UNSPECIFIED singleton.
 */
export async function bootstrapOntology(context: TestGraphContext): Promise<string> {
  const definition = buildGtdOntologyDefinition();
  await context.client.createOntology(definition);
  const singleton = await context.client.ensureSingletonNode(buildUnspecifiedSingletonRequest());
  return singleton.node_id;
}

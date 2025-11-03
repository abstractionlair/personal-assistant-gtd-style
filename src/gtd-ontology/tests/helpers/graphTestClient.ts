import { MemoryGraph } from '../../../graph-memory-core/mcp/src/memoryGraph.js';
import type {
  CreateOntologyRequest as CoreCreateOntologyRequest,
  EnsureSingletonNodeRequest as CoreEnsureSingletonNodeRequest,
  GetConnectedNodesRequest as CoreGetConnectedNodesRequest,
  GraphMemoryServerConfig,
  QueryConnectionsRequest as CoreQueryConnectionsRequest,
  QueryNodesRequest as CoreQueryNodesRequest,
  UpdateNodeRequest as CoreUpdateNodeRequest
} from '../../../graph-memory-core/mcp/src/types.js';
import { FakeStorage } from '../../../graph-memory-core/mcp/tests/helpers/fakeStorage.js';
import type { GraphMemoryClient } from '../../src/types.js';

export interface TestGraphContext {
  client: GraphMemoryClient;
  graph: MemoryGraph;
  storage: FakeStorage;
}

/**
 * Create a fresh in-memory graph context for each integration test.
 * Uses the MemoryGraph service with a FakeStorage backend to simulate the MCP environment.
 */
export async function createTestGraphContext(): Promise<TestGraphContext> {
  const storage = new FakeStorage();
  const config: GraphMemoryServerConfig = { basePath: '/virtual' };
  const graph = await MemoryGraph.initialize(config, storage);

  const client: GraphMemoryClient = {
    createOntology: request =>
      graph.createOntology(request as unknown as CoreCreateOntologyRequest),
    ensureSingletonNode: request =>
      graph.ensureSingletonNode(request as unknown as CoreEnsureSingletonNodeRequest),
    queryNodes: request => graph.queryNodes(request as unknown as CoreQueryNodesRequest),
    queryConnections: request =>
      graph.queryConnections(request as unknown as CoreQueryConnectionsRequest),
    getConnectedNodes: request =>
      graph.getConnectedNodes(request as unknown as CoreGetConnectedNodesRequest),
    getNode: request => graph.getNode(request),
    updateNode: request =>
      graph.updateNode({
        node_id: request.id,
        properties: request.properties as CoreUpdateNodeRequest['properties'],
        content: request.content,
        encoding: request.encoding,
        format: request.format
      } as CoreUpdateNodeRequest)
  };

  return { client, graph, storage };
}

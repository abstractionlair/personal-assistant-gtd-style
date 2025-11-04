// Minimal MCP client smoke test: starts the graph-memory-core server over stdio,
// creates ontology and a couple of nodes, then links them.
// Run from package dir: `node scripts/smoke.mjs`

import { fileURLToPath } from 'node:url'
import { dirname, join, resolve } from 'node:path'
import { existsSync, mkdirSync, readFileSync } from 'node:fs'

const here = dirname(fileURLToPath(import.meta.url))
const cwd = resolve(here, '..')

// Lazy import client SDK to match test pattern
const mcpMod = await import('@modelcontextprotocol/sdk/client/mcp.js').catch(() => import('@modelcontextprotocol/sdk/client/index.js'))
const stdioMod = await import('@modelcontextprotocol/sdk/client/stdio.js')
const McpClient = (mcpMod?.McpClient ?? mcpMod?.Client)
const StdioClientTransport = stdioMod?.StdioClientTransport
if (!McpClient || !StdioClientTransport) {
  console.error('MCP client SDK not available')
  process.exit(2)
}

// Repo root is three levels up from package dir: mcp -> graph-memory-core -> src -> repo
const basePath = resolve(cwd, '../../../.data/gtd-memory/smoke')
if (!existsSync(basePath)) mkdirSync(basePath, { recursive: true })

const transport = new StdioClientTransport({
  command: 'node',
  args: ['dist/index.js'],
  env: { ...process.env, BASE_PATH: basePath },
  cwd
})

const client = new McpClient({ name: 'gmc-smoke', version: '0.0.1' })
await client.connect(transport)

// Create ontology allowing Task, State, Context and DependsOn across Task→Task/Context/State
await client.callTool({
  name: 'create_ontology',
  arguments: {
    node_types: ['Task', 'State', 'Context'],
    connection_types: [
      { name: 'DependsOn', from_types: ['Task'], to_types: ['Task', 'State', 'Context'] }
    ]
  }
})

const task = await client.callTool({
  name: 'create_node',
  arguments: { type: 'Task', content: 'Call the dentist', encoding: 'utf-8', format: 'md', properties: { isComplete: false } }
})
const taskId = task.structuredContent?.node_id

const ctx = await client.callTool({
  name: 'create_node',
  arguments: { type: 'Context', content: '@phone', encoding: 'utf-8', format: 'md', properties: { isAvailable: true } }
})
const ctxId = ctx.structuredContent?.node_id

await client.callTool({
  name: 'create_connection',
  arguments: { type: 'DependsOn', from_node_id: taskId, to_node_id: ctxId }
})

await client.close()

// Print resulting registry.json for verification
const registryPath = join(basePath, '_system/registry.json')
const registry = readFileSync(registryPath, 'utf-8')
console.log('\nWrote registry to:', registryPath)
console.log(registry)

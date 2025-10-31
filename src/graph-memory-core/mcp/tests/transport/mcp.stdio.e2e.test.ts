/**
 * Tests for: Process-level MCP stdio transport (end-to-end)
 * Feature: Graph Memory Core (MCP)
 * Spec: specs/doing/graph-memory-core.md
 *
 * Tests written: 2025-10-31
 * Test Writer: OpenAI Codex (Codex CLI)
 *
 * Coverage targets:
 * - Line coverage: >80%
 * - Branch coverage: >70%
 */
import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { tmpdir } from 'node:os'
import { mkdtempSync, rmSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawn } from 'node:child_process'

// Dynamically import the MCP client SDK if available.
let McpClient: any
let StdioClientTransport: any
let sdkAvailable = true
try {
  // Top-level await is supported by Vitest with ES2022 target
  const mcpMod =
    (await import('@modelcontextprotocol/sdk/client/mcp.js').catch(() =>
      import('@modelcontextprotocol/sdk/client/index.js')
    )) ?? {}
  const stdioMod = await import('@modelcontextprotocol/sdk/client/stdio.js')
  McpClient = (mcpMod as any).McpClient ?? (mcpMod as any).Client
  StdioClientTransport = (stdioMod as any).StdioClientTransport
  if (!McpClient || !StdioClientTransport) sdkAvailable = false
} catch {
  sdkAvailable = false
}

// If the client SDK isn't present, skip these process-level transport tests.
const d = sdkAvailable ? describe : describe.skip

d('Process-level MCP transport e2e', () => {
  const cwd = fileURLToPath(new URL('../../', import.meta.url)) // module root: src/graph-memory-core/mcp/
  let basePath: string

  beforeAll(async () => {
    basePath = mkdtempSync(join(tmpdir(), 'gmc-e2e-'))
    // Ensure build output exists; build synchronously to keep test deterministic
    const tsMod = await import('typescript')
    const ts = (tsMod as any).default ?? tsMod
    const configPath = join(cwd, 'tsconfig.json')
    const configFile = ts.readConfigFile(configPath, ts.sys.readFile)
    if (configFile.error) {
      throw new Error(`Failed to read tsconfig.json: ${configFile.error.messageText}`)
    }
    const parsed = ts.parseJsonConfigFileContent(configFile.config, ts.sys, cwd)
    const program = ts.createProgram({
      rootNames: parsed.fileNames,
      options: parsed.options
    })
    const emitResult = program.emit()
    const diagnostics = ts.getPreEmitDiagnostics(program).concat(emitResult.diagnostics ?? [])
    if (emitResult.emitSkipped || diagnostics.length > 0) {
      const formatted = diagnostics
        .map((diagnostic: any) => {
          const message = ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')
          if (!diagnostic.file) {
            return message
          }
          const { line, character } = diagnostic.file.getLineAndCharacterOfPosition(diagnostic.start ?? 0)
          const filePath = diagnostic.file.fileName
          return `${filePath} (${line + 1},${character + 1}): ${message}`
        })
        .join('\n')
      throw new Error(`Failed to build server before e2e tests via TypeScript emit:\n${formatted}`)
    }
  })

  afterAll(() => {
    if (basePath && existsSync(basePath)) {
      rmSync(basePath, { recursive: true, force: true })
    }
  })

  it('launches server over stdio and performs a basic tool roundtrip', async () => {
    // Spawn server via client transport
    const transport = new StdioClientTransport({
      command: 'node',
      args: ['dist/index.js'],
      env: { ...process.env, BASE_PATH: basePath },
      cwd
    })

    const client = new McpClient({ name: 'gmc-e2e', version: '0.0.0' })
    await client.connect(transport)

    // 1) Create ontology
    await client.callTool({
      name: 'create_ontology',
      arguments: { node_types: ['Project', 'Action'], connection_types: [
        { name: 'NextAction', from_types: ['Project'], to_types: ['Action'] }
      ] }
    })

    // 2) Create nodes
    const project = await client.callTool({
      name: 'create_node',
      arguments: { type: 'Project', content: 'P', encoding: 'utf-8', format: 'txt' }
    })
    const projectId = project.structuredContent?.node_id
    expect(typeof projectId).toBe('string')

    const action = await client.callTool({
      name: 'create_node',
      arguments: { type: 'Action', content: 'A', encoding: 'utf-8', format: 'txt' }
    })
    const actionId = action.structuredContent?.node_id
    expect(typeof actionId).toBe('string')

    // 3) Link via connection
    const connection = await client.callTool({
      name: 'create_connection',
      arguments: { type: 'NextAction', from_node_id: projectId, to_node_id: actionId }
    })
    expect(connection.isError).toBeFalsy()

    // 4) Traverse
    const connected = await client.callTool({
      name: 'get_connected_nodes',
      arguments: { node_id: projectId, direction: 'out', connection_type: 'NextAction' }
    })

    expect(new Set(connected.structuredContent?.node_ids ?? [])).toEqual(new Set([actionId]))

    await client.close()
  }, 30000)

  it('returns ONTOLOGY_NOT_FOUND when calling tools before ontology create', async () => {
    const transport = new StdioClientTransport({
      command: 'node',
      args: ['dist/index.js'],
      env: { ...process.env, BASE_PATH: join(basePath, 'case2') },
      cwd
    })
    const client = new McpClient({ name: 'gmc-e2e', version: '0.0.0' })
    await client.connect(transport)

    const result = await client.callTool({
      name: 'create_node',
      arguments: { type: 'Project', content: 'X', encoding: 'utf-8', format: 'txt' }
    })
    expect(result.isError).toBe(true)
    const errorText = result.content?.[0]?.text ?? ''
    expect(errorText).toContain('Ontology has not been created yet')

    await client.close()
  }, 30000)

  it('persists registry across server restart with same BASE_PATH', async () => {
    const caseDir = join(basePath, 'case3')

    // First run: create ontology and a node
    let transport = new StdioClientTransport({
      command: 'node',
      args: ['dist/index.js'],
      env: { ...process.env, BASE_PATH: caseDir },
      cwd
    })
    let client = new McpClient({ name: 'gmc-e2e', version: '0.0.0' })
    await client.connect(transport)
    await client.callTool({ name: 'create_ontology', arguments: { node_types: ['Note'], connection_types: [] } })
    const created = await client.callTool({ name: 'create_node', arguments: { type: 'Note', content: 'hello', encoding: 'utf-8', format: 'txt' } })
    const createdId = created.structuredContent?.node_id
    expect(typeof createdId).toBe('string')
    await client.close()

    // Second run: connect again and retrieve node
    transport = new StdioClientTransport({
      command: 'node',
      args: ['dist/index.js'],
      env: { ...process.env, BASE_PATH: caseDir },
      cwd
    })
    client = new McpClient({ name: 'gmc-e2e', version: '0.0.0' })
    await client.connect(transport)
    const meta = await client.callTool({ name: 'get_node', arguments: { node_id: createdId } })
    expect(meta.structuredContent?.id).toBe(createdId)
    await client.close()
  }, 30000)
})

#!/usr/bin/env node

import { fileURLToPath } from 'node:url';
import path from 'node:path';

import { GraphMemoryMcpServer } from '../../../src/graph-memory-core/mcp/dist/server.js';
import { MemoryGraph } from '../../../src/graph-memory-core/mcp/dist/memoryGraph.js';
import { FileStorageAdapter } from '../../../src/graph-memory-core/mcp/dist/storageGateway.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class CaptureRegistrar {
  constructor() {
    this.tools = new Map();
  }

  registerTool(definition) {
    this.tools.set(definition.name, definition);
  }

  get(name) {
    return this.tools.get(name);
  }
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i];
    const value = argv[i + 1];
    if (!key.startsWith('--')) {
      throw new Error(`Unexpected argument ${key}. Expected --key value pairs.`);
    }
    args[key.slice(2)] = value;
  }
  return args;
}

async function main() {
  try {
    const argv = process.argv.slice(2);
    const parsed = parseArgs(argv);
    const toolName = parsed.tool;
    if (!toolName) {
      throw new Error('Missing --tool argument');
    }
    const inputArg = parsed.input;
    if (!inputArg) {
      throw new Error('Missing --input argument');
    }
    const basePath = parsed['base-path'] || process.env.BASE_PATH;
    if (!basePath) {
      throw new Error('Provide --base-path or BASE_PATH env');
    }
    const input = JSON.parse(inputArg);
    const storage = new FileStorageAdapter(basePath);
    const graph = await MemoryGraph.initialize({ basePath }, storage);
    const server = new GraphMemoryMcpServer(graph);
    const registrar = new CaptureRegistrar();
    server.registerTools(registrar);
    const definition = registrar.get(toolName);
    if (!definition) {
      throw new Error(`Unknown tool ${toolName}`);
    }
    const result = await definition.handler(input);
    process.stdout.write(
      JSON.stringify({ ok: true, result }) + '\n'
    );
  } catch (error) {
    process.stderr.write(JSON.stringify({ ok: false, error: String(error) }) + '\n');
    process.exit(1);
  }
}

await main();

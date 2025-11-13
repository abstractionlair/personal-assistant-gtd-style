#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../src/graph-memory-core/mcp"
npm install
npm run build

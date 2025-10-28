GTD Project - Implementation Context
Repository Locations
GitHub Repositories

file-storage-backend: https://github.com/abstractionlair/file-storage-backend
memory-graph: https://github.com/abstractionlair/memory-graph
gtd-assistant: https://github.com/abstractionlair/gtd-assistant

Local Filesystem (when using Desktop Claude)

file-storage-backend: ~/mcp-servers/file-storage-backend
memory-graph: ~/mcp-servers/memory-graph
gtd-assistant: ~/mcp-servers/gtd-assistant

Note: Local filesystem paths are only accessible when user is using Desktop Claude app. When using web interface, only GitHub access is available.
Implementation Status
file-storage-backend ✅

Status: Complete and functional
Location: Can be used as reference implementation
Role: Foundation for memory-graph

memory-graph 🚧

Status: Structure created, implementation pending
Complete:

All documentation (CLAUDE.md, AGENTS.md, README, CONTRIBUTING)
Git hooks
Specs in specs/todo/
TypeScript project setup (package.json, tsconfig.json, jest.config.js)
Basic source file stubs
CI/CD workflows


Remaining: Implementation of specs (move from specs/todo/ to specs/done/)

gtd-assistant 🚧

Status: Structure created, implementation pending
Complete: Same as memory-graph above
Remaining: Implementation of specs (depends on memory-graph completion)

Three-Stage Implementation Plan

File-based memory system (file-storage-backend) ✅ COMPLETE

Provides: 6 file operations compatible with Anthropic's future Memory Tool
Status: Implemented and can be used as reference


Knowledge-graph memory facility (memory-graph) 🚧 NEXT

Provides: Graph layer (nodes + connections) built on file storage
Status: Structure ready, needs implementation
Next: Move specs from specs/todo/ to specs/done/ as implemented


GTD assistant (gtd-assistant) ⏳ FUTURE

Provides: Intelligent GTD coaching using memory graph
Status: Structure ready, awaits memory-graph completion
Next: Wait for memory-graph, then implement specs



Workflow Pattern
Two Claude Interfaces

Desktop Chat Interface (this one)

Purpose: Planning, specifications, architecture discussions
Access: GitHub repos + local filesystem (~/mcp-servers/*)
Used for: High-level design, creating specs, updating docs


Claude Code Interface (terminal/CLI)

Purpose: Implementation, coding, testing
Access: Local filesystem only (~/mcp-servers/*)
Used for: Writing actual code, running tests, implementing specs



Spec Movement Pattern
specs/todo/          →  Implementation work  →  specs/done/
(what needs doing)      (Claude Code does)      (what's complete)
```

Each spec file in specs/todo/ should be:
1. Implemented by Claude Code
2. Tested to ensure it works
3. Moved to specs/done/ when complete
4. Referenced in commit messages

## File Organization Pattern

### Each Repository Contains
```
/
├── CLAUDE.md              # How Claude should work with this codebase
├── AGENTS.md              # How AI agents should approach this project
├── README.md              # User-facing documentation
├── CONTRIBUTING.md        # Contribution guidelines
├── package.json           # Node.js dependencies and scripts
├── tsconfig.json          # TypeScript configuration
├── jest.config.js         # Test configuration
├── .github/
│   ├── workflows/         # CI/CD automation
│   └── hooks/             # Git hooks (pre-commit, etc.)
├── specs/
│   ├── todo/              # Specifications to implement
│   └── done/              # Completed specifications
├── src/                   # Source code
│   ├── index.ts           # Main entry point
│   └── ...                # Implementation files
└── tests/                 # Test files
    └── ...
Key Documentation Files
CLAUDE.md: Tells Claude (or any AI) how to work with the codebase

What the project does
How to implement specs
How to run tests
Coding standards

AGENTS.md: Tells AI agents how to approach the project

High-level architecture
Design decisions
How components fit together
Common pitfalls to avoid

specs/todo/*.md: Individual specification files

Each spec is self-contained
Move to specs/done/ when implemented
Reference in commit messages

Current Next Steps
For memory-graph (PRIORITY)

Switch to Claude Code interface
Run npm install
Implement specs from specs/todo/ one by one:

Start with memory-system-core-implementation.md
Then ontology-and-validation.md
Then query-operations.md
Then memory-graph-mcp-server.md


Move each spec to specs/done/ when complete
Ensure tests pass

For gtd-assistant (AFTER memory-graph)

Wait for memory-graph to be functional
Switch to Claude Code interface
Run npm install
Implement GTD-specific specs
Integrate with memory-graph

Important Context for Future Conversations

file-storage-backend is done - use it as reference, don't reimplement
Work bottom-up - memory-graph before gtd-assistant
Spec-driven development - implement what's in specs/todo/, move to specs/done/
Use appropriate interface - planning here, coding in Claude Code
Local paths work only in Desktop - web interface uses GitHub only

Success Criteria
The project structure is ready for implementation when:

✅ All repos have CLAUDE.md and AGENTS.md
✅ All specs are in specs/todo/
✅ Project files (package.json, etc.) are configured
✅ CI/CD workflows are set up
✅ Git hooks are installed
✅ README documents the project vision

Status: ✅ All criteria met. Ready for Claude Code to begin implementation.
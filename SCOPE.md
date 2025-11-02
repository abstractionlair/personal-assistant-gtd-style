# Personal Assistant (GTD-Style) Scope

## Scope Overview

This project delivers an intelligent GTD coaching assistant that combines conversational AI with persistent graph-based memory, enabling knowledge workers to make confident "what should I work on?" decisions through pattern recognition and intelligent recommendations across all life domains.

## Vision Alignment

**Vision Statement:** Help knowledge workers make confident, moment-to-moment choices by pairing permanent context memory with coaching that ends thrashing and decision fatigue.

**How This Scope Serves Vision:** The MVP delivers the core value proposition—intelligent decision coaching backed by persistent memory—through a conversational GTD system that tracks projects, actions, and waiting-on items while noticing patterns like over-investment, avoidance, and stuck projects. This enables users to move from chaotic multi-project juggling to focused serial execution with confidence.

## Project Objectives

1. **Enable confident decision-making:** Asking "what should I work on?" returns intelligent, reasoned recommendations based on priorities, patterns, and context—not just task lists.

2. **Maintain persistent coaching context:** Memory survives conversation restarts, eliminating the need to repeatedly teach preferences, priorities, and patterns.

3. **Surface invisible patterns:** Assistant notices and calls out over-investment, avoidance, stuck projects, and time-sensitive items that users can't see themselves.

4. **Support natural GTD workflow:** Morning planning (10-30 min), evening reviews (10-30 min), quick check-ins throughout the day, and weekly reviews feel natural and valuable.

5. **Deliver immediate value:** Within 3 weeks, system is usable and provides real coaching value, demonstrating enough utility to maintain daily engagement.

## In Scope - MVP

### Core Features

- **Conversational GTD Capture:** Natural language interaction to create projects, actions, waiting-on items, and mark items as someday-maybe or completed. Supports standalone actions (no project required) that can be promoted to projects if they grow.

- **General Graph Memory System:** Generic graph-based memory layer (not GTD-specific) that supports arbitrary ontologies via node types and connection types. For MVP, loaded with GTD ontology (node types: Task, State, Context; connection type: DependsOn). Projects, Next Actions, and Waiting For emerge as derived views from queries (Projects = Tasks with outgoing dependencies; Next Actions = actionable Tasks; Waiting For = Tasks with external responsibility). Enables relationship queries like "what's blocked?" and "what dependencies does this task have?" Built as reusable foundation that could support other domains (fitness, finance, learning) by loading different ontologies.

- **Observations and Patterns Layer:** Persistent storage of user values, preferences, priorities, and coaching observations (e.g., "user avoids uncomfortable reviews," "risk engine: spending more time than value warrants") using existing MCP Memory Server.

- **Intelligent Recommendations:** "What should I work on?" queries return coached responses that synthesize priorities, effort balance, avoidance patterns, time-sensitive items, and what's actually unblocked—not just task retrieval.

- **Pattern Recognition:** Assistant notices and surfaces over-investment in projects, avoidance/deferral patterns, stuck projects (no next action defined), and overdue waiting-on items, using these observations to inform coaching.

- **Conversational Intelligence:** Socratic questioning to draw out priorities, probing for clarity when users use vague language ("I should probably..."), noticing weasel words, asking clarifying questions (project vs action, priorities), and collaborative project breakdown.

### User Capabilities

1. **Users can capture new projects conversationally** by describing them naturally (e.g., "I need to optimize the risk engine") resulting in persistent Project nodes that survive session restarts.

2. **Users can add next actions to projects** by stating them in conversation (e.g., "The next step is profiling the query performance") resulting in Action nodes linked to Projects via NextAction connections.

3. **Users can capture standalone actions** by describing one-off tasks (e.g., "Get wife a birthday card") resulting in Action nodes without projects, which can be promoted to Projects if additional steps emerge.

4. **Users can record waiting-on items** by stating what they're waiting for (e.g., "Waiting on design approval") resulting in waiting-status Actions that can optionally block other actions via Blocks connections.

5. **Users can mark projects as someday-maybe** by saying so (e.g., "Let's put the mobile app in someday") resulting in status changes that remove projects from active recommendations.

6. **Users can mark actions complete** by reporting them (e.g., "I finished the profiling") resulting in status updates and prompts for next actions on the project.

7. **Users can get coached recommendations** by asking "what should I work on?" resulting in reasoned responses that reference effort patterns (e.g., "you've spent more time on risk engine than warranted"), avoidance (e.g., "you keep deferring quarterly reviews"), priorities, and time-sensitive items (e.g., "get birthday card at lunch").

8. **Users can do morning planning** by asking "what's on my plate today?" (10-30 min) resulting in context-aware action lists with coaching about what matters most given current priorities and patterns.

9. **Users can do evening reviews** by reporting what happened (10-30 min) resulting in updates to actions/projects and reflective coaching observations that build context.

10. **Users can do quick check-ins** by reporting completions (e.g., "Just finished X, what's next?") resulting in immediate recommendations that account for current context and energy.

11. **Users can get pattern insights** during weekly reviews resulting in the assistant surfacing observations like effort imbalances, stuck projects, repeated deferrals, and suggesting priority adjustments.

### Technical Requirements

**Platform and Interface:**
- Claude Code interface (MCP server integration managed by Claude Code)
- Conversational interaction (no CLI commands to learn, natural language only)
- Offline-capable (local file storage, no cloud dependencies)

**Memory Architecture (Two-Layer):**
- **General Graph Memory Layer:** Custom MCP server built on file-storage-backend
  - Generic graph memory system (not GTD-specific)
  - Supports arbitrary node types and connection types via ontology definition
  - Core operations: create/read/update/delete nodes, create/query connections, search content
  - For MVP: Loaded with GTD ontology (node types: Task, State, Context; connection type: DependsOn; Context nodes track location/tool availability)
  - Derived views: Projects (Tasks with outgoing dependencies), Next Actions (actionable Tasks), Waiting For (Tasks with external responsibility)
  - State nodes model world conditions with ANY/ALL logic; Task nodes model actions
  - Special UNSPECIFIED State singleton for marking tasks needing decomposition
  - Properties: Minimal (stored in registry for fast queries) - e.g., isComplete, isTrue, logic, responsibleParty, timestamps
  - Content: Rich descriptions in files (loaded on demand)
  - Extensible: Same graph system could support other domains (fitness, finance, learning) by loading different ontologies

- **Observations Layer:** Existing MCP Memory Server
  - User values, preferences, priorities
  - Pattern observations (avoidance, over-investment, etc.)
  - Coaching context that doesn't fit graph structure

**Technology Stack:**
- TypeScript/Node.js for MCP server implementation
- File-storage-backend (6 operations: view, create, str_replace, insert, delete, rename) - ~1 day to complete
  - Designed to replicate Anthropic Memory Tool interface
  - Enables seamless migration to Anthropic Memory Tool when fully available
  - Provides local implementation with identical API surface
- File-based storage (no database server)
- Compatible with future Anthropic Memory Tool migration via interface-compatible design

**Performance Requirements:**
- Graph queries return <2 seconds for typical usage (50-100 projects, 200-500 actions)
- Morning planning sessions complete in 10-30 minutes
- Quick check-ins respond <5 seconds
- Memory storage/retrieval is local (MCP servers run locally, no additional network calls beyond Claude API)

### Acceptance Criteria

Criteria marked **P0** are must-haves for minimal viable MVP. **P1** criteria significantly enhance value but could be deferred if timeline pressures require cuts.

**GTD Structure Persistence:**
- [ ] **P0:** Projects created conversationally persist across Claude Code session restarts
- [ ] **P0:** Actions can be added to projects or created standalone
- [ ] **P0:** Projects can be marked active/someday/completed and status persists
- [ ] **P0:** Actions can be marked done and status persists
- [ ] **P1:** Waiting-on items can be recorded and optionally linked to blocked actions
- [ ] **P0:** Querying "what projects do I have?" returns accurate list with status

**Intelligent Recommendations Function:**
- [ ] **P0:** Asking "what should I work on?" returns reasoned recommendations (not just lists)
- [ ] **P0:** Recommendations reference priorities or patterns from previous conversations
- [ ] **P1:** Recommendations account for what's unblocked (respect WaitingOn/Blocks connections)
- [ ] **P0:** Morning planning ("what's on my plate?") provides relevant actions with coaching reasoning

**Memory Persistence Works:**
- [ ] **P0:** Graph memory (projects/actions/connections) survives conversation restarts
- [ ] **P0:** Observation memory (patterns/preferences/values) survives conversation restarts
- [ ] **P0:** Don't need to re-explain priorities or preferences in new conversations
- [ ] **P1:** Context builds over time (later conversations reference earlier patterns)

**Pattern Recognition Delivers Value:**
- [ ] **P1:** Assistant notices and mentions when effort is disproportionate on a project
- [ ] **P1:** Assistant notices and mentions when the same task is deferred multiple times
- [ ] **P1:** Assistant remembers time-sensitive personal items (like birthday card example)
- [ ] **P1:** Weekly reviews surface meaningful pattern observations (not just data recap)

**Conversational Quality:**
- [ ] **P0:** Interactions feel natural (not database commands or rigid protocols)
- [ ] **P0:** Assistant asks clarifying questions when appropriate (project vs action, priorities)
- [ ] **P0:** Assistant provides coaching perspective with reasoning (not just retrieves data)
- [ ] **P1:** Assistant uses Socratic questioning to draw out priorities and next actions
- [ ] **P1:** Assistant notices vague language and probes for clarity

## In Scope - Future Phases

### Phase 2 (Post-MVP Validation)

- **Context Nodes:** Add Context (@home, @work, @computer, @errands) with RequiresContext connections to enable context-based filtering ("what can I do at home?")

- **Person Nodes:** Add Person entities for detailed waiting-on tracking and delegation (currently waiting-on is free-text in Action content)

- **Advanced Pattern Detection:** Energy level tracking, time-of-day recommendations, cross-domain insights (fitness affecting work), neglect detection (important areas getting no attention)

- **Proactive Coaching:** Scheduled check-ins ("you haven't reviewed Project X in 2 weeks"), proactive pattern alerts (not just in weekly reviews)

- **Transcript Bootstrap Tools:** Automated or semi-automated tools to import context from previous coaching conversations (MVP: just paste manually)

### Phase 3 and Beyond

- **Additional Domain Ontologies:** Leverage general graph memory system for other life domains (fitness coaching with workout/progression ontology, finance with account/transaction ontology, learning with topic/resource ontology) - demonstrating the extensible architecture

- **Web Interface:** Browser-based interface for richer visualization and interaction (in addition to Claude Code)

- **Calendar Integration:** Sync with Google Calendar, iCal, etc., to surface time-sensitive commitments automatically

- **Email Integration:** Parse emails for waiting-on items or action items (with consent)

- **Rich Visualizations:** Graph views of projects/actions, effort distribution charts, pattern timelines

- **Mobile Interface:** iOS/Android apps for quick capture and check-ins on the go

- **Multi-Modal Input:** Voice capture during morning planning, screenshot analysis for reference material

### Deferred Features

- Team collaboration (shared projects, delegation between users)
- Integration with issue trackers (Jira, Linear, GitHub Issues)
- Advanced analytics on personal productivity patterns
- Domain-specific coaching extensions beyond GTD (e.g., specialized fitness programming)

## Explicitly Out of Scope

### Never in This Project

- **GAMIFICATION OF ANY KIND:** No points, badges, streaks, levels, achievements, or any other manipulative behavioral psychology tactics. Ever. This is an inviolable boundary. Gamification is fundamentally opposed to the project's values and would transform genuine support into manipulation.

- **Autonomous Task Generation Without Consent:** System will never automatically create projects or actions without explicit user agreement. Everything requires conversational consent. (Note: Assistant CAN suggest steps/actions for user consideration—the line is about agency and consent, not whether the assistant helps brainstorm. Future versions might support "what steps will I need to do X?" as collaborative planning, but implementation always requires user approval.)

- **Heavyweight Project Management:** Not building Jira/Asana replacements. No Gantt charts, resource allocation, burndown charts, time tracking, or billing. This is GTD coaching focused on personal decision-making, not team PM software.

- **Team Collaboration in Core Architecture:** System architecture is built around single user's GTD system. (Could add shared projects as an extension later, but foundation is single-user.)

- **Prescriptive Productivity Dogma:** Won't mandate "the one true way" to work. Respects user agency, offers perspective and suggestions, but never dictates or manipulates. User makes final decisions always.

- **Clinical Services:** Not therapy, not medical advice, not financial planning as regulated services. (Can reason about decisions using learned context—like "would this job be a good fit?"—but not providing professional services requiring licensure.)

- **Being a Passive Database:** This is not a task retrieval system. Must provide active reasoning, pattern recognition, and coaching—not just store and retrieve tasks.

### Not in This Version

- **Web Interface:** Claude Code only for MVP; web UI would add significant development time
- **Mobile Apps:** Desktop only for MVP; mobile would require platform-specific development
- **Calendar Integration:** Manual time-sensitive items for MVP; calendar sync adds integration complexity
- **Email Integration:** Manual task capture for MVP; email parsing adds complexity
- **Person Nodes:** Deferred to Phase 2 to minimize MVP graph complexity (Context nodes included in MVP for location/tool availability tracking)
- **Rich Visualizations:** Text-based interface for MVP; visualizations require UI development
- **Proactive Notifications:** Reactive (user-initiated) for MVP; proactive requires scheduling/alerting infrastructure
- **Advanced Pattern Detection:** Basic patterns (over-investment, avoidance, stuck projects) for MVP; energy levels, time-of-day, cross-domain insights in Phase 2
- **Transcript Bootstrap Tooling:** Manual paste for MVP; automation can come later once core system proves valuable

### External Dependencies

- File-storage-backend MCP server (in progress, ~1 day to complete) - internal dependency within our control
- Existing MCP Memory Server (available from Anthropic) - external but stable dependency
- Claude Code environment (for running MCP servers) - external platform dependency

## Constraints and Assumptions

### Resource Constraints

- **Team:** Solo developer with AI-assisted development workflow (managing team of expert AI agents for spec writing, implementation, testing, review)
- **Time:** 10-20 hours/week of human management/direction time for 3 weeks (30-60 hours total calendar time)
- **Budget:** $0 for tools/infrastructure (open development, no paid services); Anthropic API costs for Claude usage only
- **Workflow:** Using artifact-driven, multi-model development workflow (Vision → Scope → Roadmap → Specs → TDD implementation) with AI agents doing heavy lifting in parallel

### Technical Constraints

- **Platform:** Must work in Claude Code interface (MCP server managed by Claude Code)
- **MCP Server Implementation:** TypeScript/Node.js (standard for MCP servers, well-supported tooling)
- **Conversational Layer:** Natural language prompts, system instructions, role definitions, coaching guidelines (substantial portion of the "code" is actually prompt engineering)
- **Storage:** File-based (no database server to run); memory operations local (no cloud storage dependencies)
- **Performance:** Queries <2 seconds for typical graphs (50-100 projects, 200-500 actions)
- **Compatibility:** Local filesystem storage initially; must be architected to migrate to Anthropic Memory Tool when fully available

### Business Constraints

- **Solo Development:** No team to coordinate; all decisions by one person
- **Personal Use First:** Building for own use case; alpha/beta testing with self
- **No External Deadlines:** Internal 3-week target is for motivation, not contractual
- **Open Approach:** May open-source later, but not required for MVP

### Assumptions

**Assumption 1: LLM Coaching Capability**
- **What:** Claude can provide coaching-quality insights (pattern recognition, prioritization advice) given sufficient context, not just retrieve data
- **Risk if wrong:** System becomes glorified task list without coaching value
- **Validation:** Extensive prior experience in Claude chat interface validates this works with conversational context; MVP will validate it works with persistent memory
- **Mitigation:** If coaching quality insufficient, focus on improving prompts/system instructions before adding features

**Assumption 2: Graph Memory is Essential**
- **What:** GTD relationships (dependencies between tasks, state-based preconditions) require graph structure; simpler key-value storage would lead to consistency bugs and missed relationships
- **Risk if wrong:** Over-engineered solution; wasted development time on unnecessary complexity
- **Validation:** Solo developer (user) strongly believes this based on GTD methodology and relationship complexity; evolved through multi-model architectural discussions
- **Mitigation:** Build minimal graph ontology first (Task, State, Context nodes; DependsOn connection type; derived views for Projects/Next Actions/Waiting For); can simplify later if proves unnecessary

**Assumption 3: File-Storage-Backend Nearly Complete**
- **What:** ~1 day remaining to complete file-storage-backend implementation
- **Risk if wrong:** Timeline slides; MVP delayed beyond 3 weeks
- **Validation:** File-storage-backend project already has specs, basic implementation in progress
- **Mitigation:** If file-storage-backend takes longer, can temporarily use existing MCP Memory Server for everything while completing proper backend

**Assumption 4: Two-Layer Memory Architecture**
- **What:** GTD graph layer + observations layer (two separate MCP servers) is the right split
- **Risk if wrong:** Awkward queries requiring coordination between two systems; integration complexity
- **Validation:** Based on prior conversation concluding each layer optimized for different things (relationships vs facts)
- **Mitigation:** Start with this architecture; if proves awkward, can consolidate into single graph layer with observation nodes

**Assumption 5: 3 Weeks is Realistic with AI Assistance**
- **What:** With AI agents doing implementation, 30-60 hours of human direction time can deliver usable MVP in 3 calendar weeks
- **Risk if wrong:** Scope too ambitious; MVP incomplete or low quality
- **Validation:** Based on AI-assisted development velocity in recent projects
- **Mitigation:** Built-in flexibility—"usable MVP" means delivers value, not feature-complete; can cut Phase 2 items if timeline tight

## Success Criteria

### MVP Complete When

1. All acceptance criteria (19 checkboxes above) are met
2. User (solo developer) can perform complete morning planning session (10-30 min) with valuable coaching recommendations
3. User can do quick check-ins throughout day ("just finished X, what's next?") with immediate helpful responses
4. User can perform weekly review with pattern insights that reveal something not obvious from just looking at task list
5. Memory persistence validated: Start new conversation, ask "what should I work on?", get response that references projects/priorities from previous conversations without re-explaining
6. Real-world usage test: Use system daily for 1 week; demonstrates enough value to continue using (would be frustrated without it)

**Mapping to Vision Metrics (Early Signals):**

During the 1-week validation period, collect early signals on vision success metrics:
- **Usage Frequency:** Track check-in count (target: 5+ morning/evening sessions, 10+ quick check-ins)
- **Context Continuity:** Track redundant restatement rate (instances where user repeats known information; target: <10%)
- **Decision Confidence:** Self-report after week on 1-5 scale (baseline ~2.5, target: improvement toward 3.8)
- **WIP Management:** Count active projects at start vs end of week (validate assistant notices/coaches on WIP limits)

These early signals inform Phase 2 priorities but don't block MVP completion. Full vision metrics (6-month, 1-year targets) require sustained usage beyond MVP validation.

### Quality Standards

- **Conversational Naturalness:** Interactions feel like coaching conversation, not database queries or rigid protocols
- **Response Quality:** Recommendations include reasoning ("because X, you should Y") not just lists
- **Memory Accuracy:** Queries return correct graph relationships (blocked actions stay blocked, completed actions don't reappear)
- **Performance:** Queries <2 seconds for typical usage (no noticeable lag during conversations)
- **Reliability:** No data loss or corruption (projects/actions never lost due to storage bugs)

### Acceptance Process

- **Self-Testing:** Solo developer uses system daily for 1 week, validates acceptance criteria, confirms coaching value
- **Iteration:** Address any critical issues found during testing week
- **Decision:** After 1 week of real usage, assess if system delivers enough value to continue building Phase 2 or if foundational changes needed
- **No External Approval:** Solo project; developer is sole stakeholder and approver

## Risks and Mitigation

### Scope Risks

**Risk: MVP Scope Too Ambitious for 3 Weeks**
- **Probability:** Medium
- **Impact:** High (miss target timeline, deliver incomplete system)
- **Mitigation:**
  - Built-in flexibility: "Usable MVP" prioritized over "complete MVP"
  - Can defer pattern recognition sophistication if needed
  - Already scoped out Context/Person nodes to Phase 2
  - At 50% mark (1.5 weeks), assess progress; if behind, cut nice-to-haves
  - Worst case: 4-5 weeks acceptable (no external deadline)

**Risk: Coaching Quality Insufficient**
- **Probability:** Low (validated in prior conversations)
- **Impact:** High (system fails to deliver core value)
- **Mitigation:**
  - Extensive prompting/system instructions to deploy full LLM reasoning capabilities
  - Reference detailed coaching guidelines from inspiration/ directory
  - If insufficient, focus on improving prompts before adding features
  - Success criteria includes explicit coaching quality check (weekly review reveals non-obvious insights)

**Risk: Two-Layer Memory Architecture Awkward**
- **Probability:** Low-Medium
- **Impact:** Medium (integration complexity, awkward queries)
- **Mitigation:**
  - Architecture decision based on thoughtful analysis of what each layer does best
  - If proves awkward during implementation, can consolidate into single graph layer
  - Early prototype (week 1) will surface integration issues before too much built

### Execution Risks

**Risk: File-Storage-Backend Takes Longer Than Expected**
- **Probability:** Low-Medium (~1 day estimate could be optimistic)
- **Impact:** Medium (blocks graph layer development)
- **Mitigation:**
  - File-storage-backend is simple (6 operations only)
  - If delayed, temporarily use existing MCP Memory Server for everything
  - Parallel work possible: coaching guidelines and prompts don't depend on storage

**Risk: Graph Query Performance Insufficient**
- **Probability:** Low (typical graphs small: 50-100 projects, 200-500 actions)
- **Impact:** Low (would be annoying but not blocking)
- **Mitigation:**
  - Start with simple file-based graph; optimize only if needed
  - <2 second target is generous; even naive queries likely fast enough for MVP
  - If performance problems emerge, profile and optimize specific queries

**Risk: Conversational Skills Hard to Prompt**
- **Probability:** Low-Medium (Socratic questioning, noticing vague language requires sophisticated prompting)
- **Impact:** Medium (reduces coaching quality)
- **Mitigation:**
  - Leverage detailed coaching guidelines from inspiration/ directory
  - Iterate on system prompts during testing week
  - Success criteria explicitly checks conversational quality
  - Prior conversations with Claude demonstrate capability exists; just needs good prompting

**Risk: Developer Time Availability Changes**
- **Probability:** Low-Medium (work demands, life events)
- **Impact:** Medium (extends timeline)
- **Mitigation:**
  - 3-week target is preference, not contractual
  - 4-5 weeks still acceptable for MVP
  - Solo project with no external dependencies; schedule flexibility possible
  - AI agents do heavy lifting; even reduced hours can maintain progress

### Mitigation Strategies Summary

**Overarching approach:**
- Built-in flexibility at all levels (timeline, features, architecture)
- Early prototyping to surface risks before investment (week 1 integration test)
- Fallback options for technical uncertainties (existing MCP Memory Server if file-storage-backend delayed)
- Progress checkpoints (50% mark assessment to adjust scope if needed)
- AI-assisted workflow provides velocity buffer (agents parallelize work)

**Scope protection:**
- P0 vs P1 acceptance criteria enable trimming without losing core value
- Pattern recognition can simplify if timeline tight (basic patterns sufficient for MVP)
- Context/Person nodes already deferred to Phase 2

**Quality protection:**
- Explicit coaching quality checks in success criteria
- Reference detailed coaching guidelines from inspiration/ directory
- 1-week validation period to iterate before declaring MVP complete

## Stakeholder Agreement

### Key Stakeholders

- **Solo Developer/User:** Decision maker, implementer, sole user for MVP
  - **Role:** Approves all scope decisions; final say on priorities; validates usability
  - **Approval:** Self-approval after 1 week of real-world usage testing

### Open Questions

**None at present.** Scope conversations resolved all major questions:
- Storage architecture decided (two-layer: graph + observations)
- MVP ontology defined (Projects, Actions, minimal connections)
- Boundaries clear (gamification absolutely never, Context/Person deferred to Phase 2)
- Timeline realistic with AI-assisted development workflow

### Change Control

**Change Process:**

1. **Identify need for change** (implementation learning, technical discovery, timeline pressure)
2. **Document proposed change** with rationale in conversation or commit message
3. **Assess impact** on acceptance criteria, timeline, and downstream work (ROADMAP.md if exists)
4. **Update SCOPE.md** with new version number in Document Control section
5. **Communicate to self** (solo project, but document reasoning for future reference)

**Change Categories:**

- **Minor Clarifications:** Update immediately without formal process
  - Example: "Specify that 'action' includes both project-linked and standalone actions"
  - No version increment; just edit and commit

- **Scope Additions:** Require justification and timeline assessment
  - Example: "Add SubProject connections to MVP"
  - Must explain why essential for MVP; assess timeline impact
  - Version increment (e.g., 1.0 → 1.1)
  - Update acceptance criteria if needed

- **Scope Reductions:** Require documenting rationale and adjusting success criteria
  - Example: "Remove pattern recognition from MVP, defer to Phase 2"
  - Must explain why cutting (timeline, complexity, etc.)
  - Version increment (e.g., 1.0 → 1.1)
  - Update acceptance criteria and success criteria

- **Fundamental Scope Changes:** May require vision re-examination
  - Example: "Target different user segment" or "Change from conversational to GUI-based"
  - Must validate against VISION.md; may require vision update
  - Major version increment (e.g., 1.0 → 2.0)

## Document Control

### Version History

**Version 1.1 (2025-10-30)**
- Addressed scope review feedback (reviews/scope/2025-10-30-SCOPE-APPROVED.md)
- Changes:
  - Added vision metrics mapping to Success Criteria (usage frequency, context continuity, decision confidence, WIP management)
  - Labeled acceptance criteria by priority (P0 must-haves vs P1 enhancements) to preserve minimality
  - Added "Mitigation Strategies Summary" subsection for schema parity
  - Clarified general graph memory architecture (not GTD-specific, supports arbitrary ontologies)
  - Clarified file-storage-backend replicates Anthropic Memory Tool interface
  - Fixed performance claim (memory is local, but Claude API calls still required)
  - Noted TypeScript/Node.js is MCP standard, not developer preference constraint
  - Emphasized conversational layer (prompts, coaching guidelines) as substantial deliverable

**Version 1.0 (2025-10-30)**
- Initial scope document
- Completed after collaborative scope-writing-helper conversation
- Key decisions:
  - Two-layer memory architecture (graph + observations)
  - Minimal GTD ontology (Projects, Actions, 3 connection types)
  - Context/Person nodes deferred to Phase 2
  - Gamification absolute exclusion
  - Autonomous task generation clarified (suggestions OK with consent, automatic NO)
  - 3-week timeline with 30-60 hours human direction time
  - AI-assisted development workflow (agent team executing implementation)
- Derived from: Extensive prior planning in inspiration/ directory (GTD specifications, memory system architecture, coaching guidelines)

### Related Documents

- **[VISION.md](VISION.md)** - Strategic vision and long-term goals
- **ROADMAP.md** - (To be created next) Feature sequencing and phase planning
- **inspiration/** directory - Detailed GTD specifications, memory architecture, coaching guidelines from prior planning work
- **Workflow/** directory - Artifact-driven development workflow for AI-assisted implementation

# Personal Assistant (GTD-Style) Vision

## Vision Statement

Help knowledge workers make confident, moment-to-moment choices by pairing permanent context memory with coaching that ends thrashing and decision fatigue.

## Problem Statement

### Current State

Knowledge workers, particularly those working across multiple domains (professional work, personal projects, health, relationships), face chronic decision paralysis and inefficient context-switching. The core problems are:

**Thrashing:** Working on many parallel projects with chaotic context-switching between them to keep all moving just enough, leading to inefficiency and things falling through cracks. This is fundamentally a WIP (work-in-progress) limit management problem - too many concurrent projects without clear prioritization.

**Cognitive overhead:** Constant meta-decisions consume mental energy: "What should I do right now?", "Am I ignoring something more important?", "Should I finish this or switch?", "Should I solve this problem or build a framework to solve the whole class of problems?"

**Context loss:** AI coaching conversations become increasingly effective as context builds, but hitting context limits forces starting over in new conversations, losing accumulated understanding of patterns, preferences, and priorities. This friction is severe enough to cause abandonment of otherwise valuable coaching relationships.

**Lack of external perspective:** Without an external observer, it's difficult to notice patterns like avoidance (repeatedly deferring specific tasks), neglect (important areas getting insufficient attention), or over-investment (spending more time on something than it's worth).

The root cause is that existing tools (todo lists, project managers, separate AI chat sessions) provide structure but no intelligent decision support with continuity. They show what *could* be done but don't help choose what *should* be done right now, and they don't learn the user's priorities and patterns over time.

This problem persists because:
- Traditional GTD/task management tools are databases, not coaches
- AI assistants lose context between conversations
- No single system maintains global view across all life domains
- Tools focus on capture and organization, not decision support

### Desired Future State

Users operate in focused cycles: choose small number of priorities, execute serially with confidence, complete them, move to next priorities. Instead of chaotic multi-project juggling, they experience:

**Confident decision-making:** When asking "what should I do right now?", receive intelligent recommendations based on learned priorities, current context, energy levels, and global view across all commitments.

**Managed WIP:** Maintain appropriate work-in-progress limits through external coaching that notices when too many projects are active and helps decide what to pause or complete.

**Pattern awareness:** The assistant surfaces what the user already knows but needs to hear: "You've deferred this task 5 times and mentioned budget anxiety—is uncertainty about affording this the real blocker?"

**Persistent coaching relationship:** Context builds permanently across all interactions. The assistant learns values, priorities, preferences, energy patterns, and avoidance triggers, becoming more effective over time rather than resetting.

**Global optimization:** Decisions consider the whole life system. When choosing to work out (fitness domain), the assistant understands this means not doing work tasks or personal projects, and can recommend based on holistic priorities.

Success means lower stress, more completions, and—measurably—consistent usage (morning planning, evening catchups, weekly reviews, frequent "what now?" check-ins) demonstrating the assistant delivers ongoing value.

## Target Users

### Primary Persona

**Name/Role:** "Systems-Thinking Sam" – Multi-Domain Knowledge Worker (e.g., software developer with personal projects, health goals, and family commitments)

**Demographics:**
- Professionals with 5+ years experience managing complex work
- Comfortable with systems thinking and technology
- Familiar with productivity methodologies (GTD, Kanban, etc.)
- Solo operators or individual contributors managing their own priorities

**Current Behavior:**
- Uses separate tools/conversations for different domains (work Claude Project, fitness Claude Project, diet Claude Project)
- Manually tracks projects and next actions in GTD-style lists
- Context-switches frequently between adding friction
- Experiences decision fatigue about what to work on
- Sometimes gets stuck in meta-loops (researching better systems instead of doing work)

**Jobs-to-be-Done:**
- Decide confidently what to work on right now
- Maintain appropriate WIP limits across all life domains
- Get external perspective on patterns (avoidance, neglect, energy mismatches)
- Build context with a coach that persists across all interactions
- Execute focused work cycles with less anxiety about what's being ignored

**Pain Points:**
- Thrashing between too many concurrent projects inefficiently
- Cognitive load from constant "should I switch?" decisions
- Context loss when hitting conversation limits forces starting over
- Things falling through cracks despite having GTD lists
- Frustration from friction of switching between separate coaching contexts (work, fitness, etc.)
- Difficulty noticing own avoidance patterns or stuck projects

**Decision Criteria:**
- Must reduce cognitive overhead, not add to it
- Must learn preferences over time (not reset constantly)
- Must provide intelligent coaching, not just task retrieval
- Usage must feel valuable enough to maintain daily/weekly engagement
- Must handle unified global view across all life domains

### Secondary Personas

**"Executive/High-Leverage Professional":** Someone who would benefit from human executive/personal assistant functions (tracking commitments, waiting-for items, reminding about important but non-urgent items, managing complex project dependencies). Uses this as a force-multiplier for high-leverage work.

**"Systems Thinker":** Someone who resonates with technical analogies (GTD as OS scheduler, task management as state machine) and appreciates clean abstractions. Values the graph-based memory architecture itself as elegant solution.

## Value Proposition

### Core Benefit

Transform chaotic multi-project juggling into focused serial execution by providing what an executive/personal assistant provides: intelligent "what should I do now?" recommendations based on learned priorities, external perspective on patterns you can't see yourself, and permanent memory that makes the coaching relationship increasingly effective over time.

**Emotional dimension:** Move from anxiety and decision paralysis to confidence and calm. Feel supported rather than managed. Experience relief when the assistant surfaces "you already know you should pause this project" instead of forcing yourself to decide.

**Practical dimension:** Reduce time spent on meta-decisions, complete more priorities, maintain healthier WIP limits, catch falling items before they hit the ground. Operate more like the idealized GTD practitioner: trusted system, confident choices, regular completion cycles.

### Differentiation

**Unlike** separate AI coaching sessions (Claude Projects) or traditional GTD tools (OmniFocus, Todoist),
**our product** combines permanent context memory with intelligent decision coaching across all life domains in a unified system.

**Why users will choose this:**
- **Persistent learning:** Context builds permanently through graph-based memory and learned preferences, avoiding the frustration of repeatedly "teaching" a new conversation
- **Active reasoning over retrieval:** Notices patterns (avoidance, stuck projects, energy mismatches) and synthesizes insights, not just lists tasks
- **Unified global view:** Single assistant sees work + fitness + personal projects and helps optimize across all domains
- **Coaching stance:** Asks probing questions, offers perspective, surfaces what you need to hear—like a human coach/assistant, not a database

**Why advantage is sustainable:**
- The accumulated context and learned patterns become more valuable over time (switching cost increases)
- Conversational AI's ability to reason about patterns is hard to replicate in traditional task managers
- The unified coaching model across domains is fundamentally different from single-domain tools
- Can bootstrap quickly using transcripts from previous conversations, but ongoing learning creates unique user-specific value

## Product Scope

### In Scope (MVP)

**Core Features:**
- **GTD structure management:** Projects, actions, contexts, waiting-for items with graph-based relationships (NextAction, DependsOn, WaitingFor, etc.)
- **Intelligent decision coaching:** "What should I do now?" queries that reason about priorities, patterns, and context—not just retrieve lists
- **Pattern recognition:** Detect and surface avoidance (tasks migrated 3+ times), stuck projects (no activity), overdue waiting-for items, energy mismatches
- **Persistent memory:** Graph database for GTD structure + Memory Tool for values/preferences/principles, maintaining context across all conversations
- **Conversational interaction:** Socratic questioning to draw out priorities, collaborative project breakdown, coaching stance (questions over directives)
- **Bootstrap from history:** Load transcripts from previous coaching conversations to establish initial context rapidly

**Must-Have Capabilities:**
- Track projects, actions, contexts, waiting-for items with proper GTD semantics
- Answer "what's on my plate today?" with intelligent recommendations
- Notice and point out patterns user can't see (avoidance, neglect, over-investment)
- Learn user's values/priorities/principles through conversation over time
- Maintain global view across multiple life domains (work, fitness, diet, personal)
- Support morning planning, evening catchup, weekly review interaction patterns

**Technical Requirements:**
- Graph-based memory system for GTD relationships (nodes: Task, State, Context; connection: DependsOn; Context.isAvailable for location/tool tracking)
- Derived views from queries (Projects = Tasks with outgoing dependencies; Next Actions = actionable Tasks; Waiting For = Tasks with external responsibility)
- State nodes model world conditions with ANY/ALL logic; Task nodes model actions
- Special UNSPECIFIED singleton for marking tasks needing decomposition
- Integration with Anthropic Memory Tool for preferences/values storage
- Properties vs. content separation (minimal properties for fast queries, rich content in files)
- MCP server architecture for memory access
- TypeScript/Node.js implementation

### Future Scope

**Features for Later Versions:**
- Multi-modal input (voice capture, screenshots, emails)
- Proactive notifications/reminders based on patterns
- Integration with calendar and email
- Visualization of project/action graphs
- Team collaboration features (shared projects, delegation)
- Mobile interface for quick capture and check-ins
- Advanced analytics on personal productivity patterns
- Domain-specific coaching extensions (e.g., specialized fitness programming beyond basic tracking)

**Growth Considerations:**
- Could extend to teams (shared executive assistant)
- Could add specialized domain coaches while maintaining unified decision-making
- Could develop marketplace of "coaching styles" or "priority frameworks"
- Could support synchronization across multiple users' assistants

### Never in Scope

**Explicit Exclusions:**
- Automated task generation (projects emerge through conversation, not auto-creation)
- Prescriptive productivity dogma (respects user agency, offers perspective but doesn't mandate)
- Gamification or habit streaks (avoiding manipulation, focusing on genuine support)
- Social features or comparison with other users
- Broad "life coach" beyond decision support (no therapy, no medical advice)
- Being a passive task database without coaching intelligence

**User segments we won't target:**
- Teams needing heavyweight project management (Jira, Asana territory)
- People wanting fully automated systems without conversation
- Users uncomfortable with AI having extensive personal context

**Problems we won't solve:**
- Time tracking or billing (separate concern)
- Document management beyond task-related context
- Calendar scheduling optimization (may integrate but not core)

## Success Criteria

### Key Metrics

1. **Usage Frequency (Primary Success Indicator)**
   - Definition: Regular engagement patterns demonstrating ongoing value delivery
   - Current baseline: 0 (net new system)
   - 6-month goal:
     - Morning planning session 5+ days/week (5-10 min each)
     - Evening catchup 3+ days/week (5 min each)
     - Weekly review 1x/week (30-45 min)
     - "What now?" check-ins 10+/week (1-2 min each)
   - 1-year goal: Sustained pattern above + longer monthly review sessions (2+ hours)
   - 3-year goal: Assistant is integrated into daily decision-making; usage is automatic/unconscious

2. **Context Continuity**
   - Definition: "Redundant restatement rate" - percentage of sessions requiring user to re-teach known facts
   - Current baseline: ~80% (constant re-teaching in new Claude conversations)
   - 6-month goal: <10% (rare need to restate preferences, priorities, or established patterns)
   - 1-year goal: <5% (only novel information requires teaching; historical context solid)
   - 3-year goal: <2% (multi-year memory near-perfect; only life changes require updates)
   - Measurement: Track instances during weekly review; assistant flags when user restates known information

3. **WIP Management**
   - Definition: Number of active projects and perceived thrashing
   - Current baseline: 10-15 active projects with frequent chaotic switching
   - 6-month goal: 5-7 active projects with deliberate WIP limits, user reports reduced thrashing
   - 1-year goal: Consistent 3-5 active projects, completion cycles visible, reduced things falling through cracks
   - 3-year goal: Mature WIP discipline, high completion rate, low anxiety about ignored work

4. **Decision Confidence**
   - Definition: Weekly self-report on 1-5 scale (1=constant anxiety about right task, 5=complete confidence in choices)
   - Current baseline: ~2.5 (frequent uncertainty and second-guessing)
   - 6-month goal: 3.8 average (general trust in recommendations, occasional doubt)
   - 1-year goal: 4.3 average (strong confidence, rarely second-guess)
   - 3-year goal: 4.5+ average (confidence is default state)
   - Measurement cadence: Weekly pulse question during weekly review

5. **Coaching Quality**
   - Definition: Assistant surfaces non-obvious insights vs. just retrieving data
   - Current baseline: 0 (net new)
   - 6-month goal: 2-3 meaningful pattern observations per week (e.g., "you've avoided this 5 times")
   - 1-year goal: Assistant regularly connects insights across domains (fitness affecting work, etc.)
   - 3-year goal: Assistant provides perspective user consistently finds valuable and couldn't generate alone

### Counter-Metrics (Guardrails)

- **User agency respected:** Assistant never mandates or manipulates; maintains collaborative coaching stance
- **Context privacy maintained:** Memory system secure, user controls what's remembered
  - Data retention policy: User can delete any memory at any time; full export/erasure on request
  - Storage default: Local-only (no cloud sync) unless user explicitly opts in
  - Third-party access: Never shared; API calls to Anthropic follow standard privacy terms
- **No gaming usage metrics:** Usage quality matters more than quantity; don't incentivize pointless check-ins
- **Sustainable assistant relationship:** User feels supported, not dependent or overwhelmed
- **Cross-domain balance maintained:** No single domain (work, fitness, etc.) consistently neglected due to system design

### Timeline Milestones

- **6 Months:** MVP operational with core GTD structure, pattern recognition, and memory persistence. User maintaining regular usage patterns (morning/evening/weekly). Evidence that context continuity is working (user doesn't repeat information). Initial WIP improvement visible.

- **1 Year:** Mature coaching relationship with extensive learned context. User reports decision confidence improvement. WIP discipline established. Pattern recognition sophisticated (cross-domain insights). Weekly reviews are productive and valuable. System has proven value enough to maintain consistent engagement.

- **3 Years:** Assistant is indispensable part of workflow. Multi-year patterns inform recommendations. User operates in focused serial execution mode with rare thrashing. Context breadth and depth enable nuanced coaching. System adapts to life changes smoothly. Usage is habitual and unconscious.

## Technical Approach

### Technology Stack

**Frameworks:**
- TypeScript/Node.js for memory graph implementation (type safety, mature ecosystem)
- MCP (Model Context Protocol) server architecture for memory access (Anthropic standard)
- Jest for testing (established, good TypeScript support)

**Platforms:**
- Claude Desktop / Claude Code for user interaction interface (native integration)
- Anthropic Memory Tool for preferences/values storage (when available)
- Local filesystem storage for graph data initially (file-storage-backend pattern)

**Key Dependencies:**
- Anthropic SDK for Claude API access
- Graph database or file-based graph representation (decision pending - see Open Questions)
- Markdown/JSON for content storage (human-readable, version-controllable)

### Architecture Principles

**Core Technical Decisions:**
- **Memory as cognitive architecture:** Graph-based memory system is the assistant's working memory for reasoning, not just a database for retrieval
- **Properties vs. content separation:** Minimal properties in graph registry for fast queries (project status, action contexts), rich content in files loaded on demand
- **Composable queries over prescriptive rules:** Primitive operations (query_nodes, query_connections, search_content) composed flexibly based on specific questions
- **Schema-driven structure:** GTD ontology defines node types (Project, Action, Context, Person) and connection types (NextAction, DependsOn, WaitingFor, RequiresContext, etc.)

**Key Constraints:**
- Solo developer time constraint (10-20 hours/week)
- Must be maintainable long-term by AI-assisted development
- Performance: Queries should return <1 second for typical usage (hundreds of projects/actions)
- Must work offline initially (cloud optional for future)

### Known Risks

**Technical Challenges:**
- **Graph query performance:** As project/action count grows, naive queries might slow down
  - Mitigation: Start simple with file-based approach, profile early, optimize or add true graph DB only if needed
  - Switch threshold: Move from file-based to embedded graph DB when median query latency >1s OR graph size >500 nodes/2000 edges OR file size >50MB
- **Memory Tool integration timing:** Anthropic Memory Tool may not be available when MVP ready
  - Mitigation: Design abstraction layer, implement local memory first, swap in Memory Tool later
- **Context window limits for complex queries:** Reasoning about large project graphs might hit limits
  - Mitigation: Incremental query strategy, summarization, careful prompt engineering
- **Conversational UX in terminal:** Coaching conversations need to feel natural in Claude Code/CLI context
  - Mitigation: Prototype early, iterate on interaction patterns, learn from existing chat experiences

**Integration Risks:**
- **Bootstrapping from transcripts:** Extracting structured data from free-form conversation history might be imperfect
  - Mitigation: Accept imperfect initial import, allow manual corrections, focus on incremental learning forward
- **Cross-domain reasoning complexity:** Synthesizing insights across work/fitness/personal might be harder than anticipated
  - Mitigation: Start with single-domain depth, gradually add cross-domain patterns as capabilities proven

## Assumptions and Constraints

### Market Assumptions

- **User behavior:** Power users willing to invest time in daily/weekly rituals will gain enough value to maintain engagement
- **AI capability:** LLMs (Claude) can effectively reason about patterns and provide coaching-quality insights, not just retrieve data
- **Memory persistence value:** Permanent context is valuable enough to justify technical complexity vs. stateless conversations
- **GTD resonance:** GTD methodology's structure and terminology will "click" for target users (systems thinkers, knowledge workers)

### Technical Assumptions

- **Feasibility:** Graph-based memory system implementable within solo dev constraints (3-6 months to MVP)
- **Available tools:** TypeScript + MCP server + file storage sufficient for MVP; don't need heavyweight graph DB initially
- **Integration capability:** Can integrate with Anthropic Memory Tool when available through abstracted interface
- **Query composability:** Primitive graph operations composed at prompt level can deliver intelligent coaching (vs. needing complex hardcoded algorithms)

### Resource Constraints

**Time:**
- Available: 10-20 hours/week for development
- Project duration expectation: 3-6 months to usable MVP, 1 year to mature system
- Must sustain commitment through early phase when coaching is still learning

**Budget:**
- Anthropic API costs (Claude usage for development and ongoing coaching)
- Minimal infra costs initially (local storage)
- No paid dependencies planned for MVP

**Team:**
- Solo developer (user/developer are same person initially)
- AI-assisted development (Claude Code, Claude chat for planning)
- Skills available: Software engineering, systems thinking, GTD expertise, AI prompting
- Skills to develop: MCP server patterns, graph database best practices if needed

### Solo Developer Specific

**Personal Commitment:**
- Time available per week: 10-20 hours (variable based on work demands)
- Planned duration: 6 months to MVP, sustained development/usage after
- Accountability mechanism: Using this workflow itself (VISION → SCOPE → ROADMAP → TDD implementation)

**Skills and Learning:**
- Skills I have: TypeScript/Node.js, software architecture, GTD methodology, AI coaching experience, systems thinking
- Skills to develop: MCP server implementation details, graph query optimization (if needed), production coaching prompt engineering
- Learning resources: Anthropic MCP docs, existing file-storage-backend implementation as reference, GTD community, AI workflow communities

**Support Network:**
- Advisors: Other AI developers, GTD practitioners, Claude (for architecture/implementation questions)
- Accountability partners: Self-directed; usage patterns are own accountability metric
- Community: GitHub issues, potential future users as alpha/beta testers

**Decision Authority:**
- How to make tough decisions: Prioritize coaching value over technical elegance; validate through actual usage; reference VISION for alignment
- When to pivot vs. persevere: If 6-month usage metrics not achieved, reassess approach; if technical architecture proving unworkable, simplify; vision stability more important than implementation details

## Open Questions

**Unresolved Decisions:**
- **Graph database choice:** Start with file-based graph (simpler) or use embedded graph DB (e.g., Neo4j, SQLite with graph extension)?
  - Leaning toward file-based for MVP, add DB only if performance requires
- **Anthropic Memory Tool integration timeline:** When available? Affects architecture abstraction decisions
  - Design abstraction now, implement local memory first
- **Conversation interface details:** How much structure vs. freeform chat for different interaction types (planning vs. quick check-in)?
  - Prototype early, iterate based on usage feel

**Areas Needing Research:**
- **Pattern detection algorithms:** What query patterns actually surface useful avoidance/stuck-project insights?
  - Implement basic patterns from inspiration docs, refine based on real usage
- **Cross-domain reasoning:** How to synthesize insights across work/fitness/personal effectively?
  - Start simple (single domain), gradually add cross-domain as confidence builds
- **Weekly review structure:** What format makes weekly review most valuable?
  - Adapt from GTD standard review, customize based on usage patterns

**Risks Requiring Mitigation:**
- **User abandonment during learning phase:** Early coaching might be generic until context builds
  - Mitigate through transcript bootstrapping, set expectations, focus on incremental value
- **Technical complexity overwhelming solo dev timeline:** Graph system + coaching prompts + UX might be too much
  - Mitigate through ruthless MVP scoping, AI-assisted development, phased delivery

**Hypotheses to Validate:**
- **Context persistence is critical to sustained usage:** Test by measuring engagement after 1 month vs. 3 months (should improve as context builds)
- **GTD structure + coaching is better than either alone:** Compare to pure GTD tool usage satisfaction
- **Pattern recognition delivers unique value:** Track whether surfaced patterns lead to behavior changes
- **Global view across domains is valuable:** Measure whether cross-domain insights are acted upon

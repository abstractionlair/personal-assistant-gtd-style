# Personal Assistant (GTD-Style) Roadmap

## Roadmap Overview

This roadmap sequences features to derisk the riskiest assumption first—that Claude can reliably manage GTD memory structures through conversation—before investing in coaching enhancements. We build serially with TDD validation at each step, delivering a working conversational GTD system in Phase 1, then adaptively enhancing it in Phase 2 based on quality assessment.

## Alignment

### Vision

Help knowledge workers make confident, moment-to-moment choices by pairing permanent context memory with coaching that ends thrashing and decision fatigue.

### Success Criteria

Key metrics from VISION.md that this roadmap achieves:

- **Usage Frequency:** Regular engagement (morning planning 5+ days/week, evening catchup 3+ days/week, weekly review, frequent "what now?" check-ins)
- **Context Continuity:** <10% redundant restatement rate (minimal need to re-teach preferences/priorities)
- **WIP Management:** Move from 10-15 chaotic active projects to 5-7 deliberate projects with reduced thrashing
- **Decision Confidence:** Improve from ~2.5 baseline to 3.8+ average on 1-5 confidence scale
- **Coaching Quality:** 2-3 meaningful pattern observations per week

### Scope Summary

MVP delivers conversational GTD coaching assistant combining graph-based memory for projects/actions/relationships with observations layer for preferences/patterns. Natural language interaction enables capture, status updates, and intelligent "what should I work on?" recommendations backed by pattern recognition.

### Feature Mapping (SCOPE to Roadmap)

| SCOPE.md Core Feature | Roadmap Phase | Roadmap Feature(s) |
|----------------------|---------------|-------------------|
| Conversational GTD Capture | Phase 1 | Conversational Layer |
| General Graph Memory System | Phase 1 | Graph Memory Core, GTD Ontology |
| Observations and Patterns Layer | Phase 2A | Observations Layer Integration |
| Intelligent Recommendations | Phase 2A | Intelligent Recommendations |
| Pattern Recognition | Phase 2A | Pattern Recognition |
| Conversational Intelligence | Phase 2A | Socratic Questioning |

All SCOPE MVP features are represented in roadmap. Phase 2B (Polish Core) is conditional alternative to Phase 2A if Phase 1 assessment requires core reliability work before enhancements.

## Sequencing Strategy

### Key Principles

1. **Derisk integration risk first** - Validate that Claude reliably manages memory before building coaching sophistication
2. **Test GTD as complete unit** - Full GTD model (Projects, Actions, NextAction/Blocks/WaitingOn) validated together, not incrementally
3. **Serial TDD build** - Each layer (file-storage → graph → GTD → conversational) completes with tests before next
4. **Adaptive Phase 2** - Enhance coaching (Phase 2A) if Phase 1 solid, or polish core (Phase 2B) if Phase 1 rough
5. **Real usage validation** - 3-5 days actual GTD usage tests reliability before declaring success

### Risk Mitigation Approach

The biggest project risk is whether Claude will reliably manage memory layers (noticing when to store, making consistent updates, knowing when to query). Phase 1 validates this assumption with minimal viable GTD before investing in pattern recognition or coaching sophistication. If Phase 1 succeeds, we know the integration works; if it fails, we discover the problem after 2 weeks, not after building the full MVP.

Phase 1 tests the complete GTD model as integrated unit—Projects, Actions, NextAction/Blocks/WaitingOn connections, status management, standalone actions—because reliability likely scales with complexity. Testing a simplified subset wouldn't give confidence about the full system.

### Value Delivery Pattern

- **Phase 1 (Weeks 1-2):** Working conversational GTD system you can use daily. Validates core technical integration.
- **Phase 2A (Week 3):** If Phase 1 solid → Add observations layer + pattern recognition for coaching intelligence
- **Phase 2B (Week 3):** If Phase 1 rough → Polish conversational GTD reliability and naturalness before enhancement

Each phase delivers complete, usable capability—not infrastructure-only phases.

## Phase 1: Conversational GTD Validation (Weeks 1-2)

### Goals

Validate the riskiest assumption: Can Claude reliably manage GTD memory structures through conversational interaction? Deliver working conversational GTD system with complete Projects/Actions/connections model that persists across session restarts and handles real daily usage without data loss or inconsistency.

This phase derisks the core technical integration before investing in coaching sophistication. Success means GTD memory management works reliably enough to build coaching intelligence on top; failure means we know the integration needs fundamental rethinking before proceeding.

### Features

1. **File-Storage-Backend Integration**
   - **Description:** Bring file-storage-backend MCP server into this project, update to current workflow standards, and complete implementation to provide generic file operations layer (view, create, str_replace, insert, delete, rename).
   - **Why now:** Foundation for all memory layers; nothing else can be built without persistent storage working.
   - **Delivers:** Persistent storage capability for graph and conversational data.
   - **Derisks:** Storage layer completeness assumption; validates file-based approach is sufficient for MVP.
   - **Depends on:** Nothing (foundational feature).
   - **Effort:** Small (2 days: 1 day implementation, 1 day tests/debug)

2. **Graph Memory Core**
   - **Description:** Generic graph-based memory system supporting arbitrary ontologies via configurable node types and connection types, with core operations (create_node, update_node, query_nodes, create_connection, query_connections, search_content) built on file-storage-backend.
   - **Why now:** Generic layer before GTD-specific structures; enables flexible ontology definition and future domain extensions.
   - **Delivers:** Reusable graph memory infrastructure that can support GTD and future domains (fitness, finance, learning).
   - **Derisks:** Graph operations approach; validates that file-based graph is performant enough for MVP scale.
   - **Depends on:** File-Storage-Backend Integration.
   - **Effort:** Small (2 days: 1 day implementation, 1 day tests/debug)

3. **GTD Ontology**
   - **Description:** Define and implement GTD-specific structures on top of generic graph core: node types (Project, Action), connection types (NextAction, Blocks, WaitingOn), properties (status, timestamps), and support for standalone actions without projects.
   - **Why now:** Must define GTD structures before conversational layer can create/query them.
   - **Delivers:** Complete GTD data model ready for conversational interaction.
   - **Derisks:** GTD model completeness; validates ontology design supports all MVP use cases.
   - **Depends on:** Graph Memory Core.
   - **Effort:** Small (2 days: 1 day implementation, 1 day tests/debug)

4. **Conversational Layer**
   - **Description:** System prompts, conversation patterns, and instructions that tell Claude when to store/query GTD memory, how to maintain consistency, and how to interact naturally for capture, updates, and queries.
   - **Why now:** This is the risky integration—tests whether Claude can actually manage memory reliably through conversation.
   - **Delivers:** Natural language GTD interaction; validates core integration assumption.
   - **Derisks:** "Claude can reliably manage memory" assumption—the biggest project risk.
   - **Depends on:** GTD Ontology.
   - **Effort:** Small (2 days: 1 day prompt engineering, 1 day manual testing/iteration)

5. **Validation Period**
   - **Description:** Use conversational GTD system for 3-5 days of real daily capture, status updates, and queries to validate memory reliability, consistency, and conversational naturalness.
   - **Why now:** Must validate integration works before declaring Phase 1 success or proceeding to enhancements.
   - **Delivers:** Confidence assessment (solid vs rough vs broken); data for Phase 2 decision.
   - **Derisks:** Integration reliability; identifies edge cases and quality issues.
   - **Depends on:** Conversational Layer.
   - **Effort:** Small (validation period, not implementation)

### Success Criteria

- [ ] Can create projects conversationally and they persist across Claude Code session restarts
- [ ] Can create actions (both project-linked and standalone) conversationally
- [ ] Can mark projects as someday/active/completed and status persists
- [ ] Can mark actions complete conversationally
- [ ] Can record waiting-on items with optional blocking connections
- [ ] Asking "what projects do I have?" queries storage and returns accurate list with status
- [ ] After 3-5 days real usage: zero data loss, zero corrupted relationships (actions properly linked to projects, blocks relationships preserved)
- [ ] Memory survives conversation restarts (start new conversation, ask about projects, they're there with correct status)
- [ ] Claude stores information without explicit "save" commands (natural memory management)
- [ ] Claude queries storage before answering questions (doesn't hallucinate projects/actions)

### Learning Goals

- Does Claude reliably notice when conversation implies something to store?
- Does Claude make consistent, complete updates to GTD structures (no partial updates)?
- Does Claude know when to consult storage layers vs. working from conversation context?
- What edge cases break the conversational flow or memory consistency?
- Is the full GTD model too complex for reliable management, or does it work as designed?

### Validation Checkpoint

**Date:** End of Week 2 (after 3-5 day validation period)

**Review questions:**
- Is memory management reliable? (Zero data loss, zero corrupted relationships?)
- Does conversation feel natural? (Not requiring explicit database commands?)
- Are there systematic issues? (Frequently forgets to store, requires explicit memory commands, awkward query patterns?)

**Decision criteria:**
- **Proceed to Phase 2A (Coaching Intelligence):** Memory management reliable, conversation natural, only minor polish needed. Ready to add observations layer and pattern recognition.
- **Pivot to Phase 2B (Polish Core):** Works but has significant issues—frequently forgets to store, awkward conversation patterns, requires explicit memory management. Need to improve prompts and core reliability before adding complexity.
- **Stop and Rethink:** Fundamental reliability issues; conversational memory integration doesn't work as designed. Approach requires fundamental changes.

## Phase 2A: Coaching Intelligence (Week 3)
*[Conditional: Proceed here if Phase 1 assessment is "solid"]*

### Goals

Transform conversational GTD from task database into intelligent coaching assistant by adding observations layer for preferences/patterns and implementing pattern recognition that notices over-investment, avoidance, stuck projects, and time-sensitive items. Deliver recommendations that reference patterns and priorities, not just retrieve task lists.

### Features

1. **Observations Layer Integration**
   - **Description:** Integrate Anthropic MCP Memory Server for storing user values, preferences, priorities, and coaching observations (e.g., "user avoids uncomfortable reviews," "risk engine: spending more time than value warrants") that don't fit graph structure.
   - **Why now:** Foundation for pattern-aware coaching; needed before pattern recognition can store insights.
   - **Delivers:** Persistent memory for coaching context and learned patterns.
   - **Derisks:** Anthropic Memory Server integration; validates two-layer memory architecture.
   - **Depends on:** Phase 1 complete (GTD memory working).
   - **Effort:** Small (1-2 days: integration is straightforward, mostly prompt updates)

2. **Pattern Recognition**
   - **Description:** Detection logic and prompts for noticing over-investment (disproportionate effort on projects), avoidance (repeatedly deferred actions), stuck projects (no next action defined), and overdue waiting-on items, with observations stored in memory layer.
   - **Why now:** Core coaching value; enables assistant to notice things user can't see.
   - **Delivers:** Pattern insights during recommendations and weekly reviews.
   - **Derisks:** Pattern detection feasibility; validates LLM can reason about temporal patterns in GTD data.
   - **Depends on:** Observations Layer Integration.
   - **Effort:** Medium (pattern detection logic, prompt engineering, testing)

3. **Intelligent Recommendations**
   - **Description:** Enhanced "what should I work on?" responses that synthesize priorities, effort patterns, avoidance observations, time-sensitive items, and what's unblocked—not just task retrieval.
   - **Why now:** Delivers coaching value; demonstrates system is more than database.
   - **Delivers:** Coached recommendations with reasoning ("because X, you should Y").
   - **Derisks:** Coaching quality assumption; validates LLM can provide valuable insights given context.
   - **Depends on:** Pattern Recognition.
   - **Effort:** Small (1-2 days: prompt engineering for recommendation synthesis)

4. **Socratic Questioning**
   - **Description:** Conversational patterns for probing priorities, noticing vague language ("I should probably..."), asking clarifying questions (project vs action), and collaborative project breakdown.
   - **Why now:** Enhances conversational quality; makes coaching feel collaborative not prescriptive.
   - **Delivers:** Natural, coaching-quality conversation patterns.
   - **Derisks:** None (low-risk prompt enhancement).
   - **Depends on:** Intelligent Recommendations.
   - **Effort:** Small (1-2 days: prompt patterns and examples)

### Success Criteria

- [ ] Assistant notices and mentions when effort is disproportionate on a project (over-investment pattern)
- [ ] Assistant notices and mentions when same task deferred multiple times (avoidance pattern)
- [ ] Assistant remembers time-sensitive personal items and surfaces them appropriately
- [ ] Asking "what should I work on?" returns reasoned recommendations referencing patterns, not just lists
- [ ] Recommendations account for what's unblocked (respect WaitingOn/Blocks connections)
- [ ] Weekly reviews surface meaningful pattern observations (not just data recap)
- [ ] Assistant asks clarifying questions when appropriate (project vs action, priorities)
- [ ] Assistant uses Socratic questioning to draw out priorities and next actions

### Learning Goals

- Do pattern observations feel valuable, or just annoying/obvious?
- Is coaching quality sufficient to justify daily usage?
- Which patterns matter most to users?
- Does cross-domain reasoning work (if tested)?

### Validation Checkpoint

**Date:** End of Week 3

**Review questions:**
- Do recommendations feel coached vs. just data retrieval?
- Are pattern observations valuable and non-obvious?
- Would you continue using this system daily?

**Decision criteria:**
- **MVP Complete:** System delivers coaching value worth maintaining daily usage. Proceed to real-world hardening and Phase 3+ planning.
- **Iterate:** Core value present but needs refinement. Spend additional time improving prompt quality.
- **Pivot:** Coaching quality insufficient despite technical success. Reassess approach or target users.

## Phase 2B: Polish Core (Week 3)
*[Conditional: Proceed here if Phase 1 assessment is "rough"]*

### Goals

Make conversational GTD reliable and natural before adding coaching complexity. Address memory management gaps, improve prompts for consistent storage/query behavior, handle edge cases discovered in validation, and smooth conversation flow. Establish solid foundation before Phase 3 coaching enhancements.

### Features

1. **Memory Management Reliability**
   - **Description:** Improve prompts and instructions to ensure Claude consistently stores information when mentioned, makes complete (not partial) updates, and queries storage before answering questions.
   - **Why now:** Phase 1 revealed reliability gaps that must be fixed before adding complexity.
   - **Delivers:** Consistent, reliable GTD memory management.
   - **Derisks:** None (addressing known issues from Phase 1).
   - **Depends on:** Phase 1 complete (issues identified).
   - **Effort:** Medium (prompt iteration, testing edge cases)

2. **Edge Case Handling**
   - **Description:** Address specific failure modes discovered during Phase 1 validation (e.g., forgotten storage, partial updates, query failures, conversation breakdown scenarios).
   - **Why now:** Known issues blocking reliable daily usage.
   - **Delivers:** Robust handling of real-world usage patterns.
   - **Derisks:** None (addressing known issues).
   - **Depends on:** Memory Management Reliability.
   - **Effort:** Small (2-3 days: targeted fixes for specific issues)

3. **Conversation Flow Improvement**
   - **Description:** Smooth conversational interactions to feel natural, reduce need for explicit commands, improve query response quality, and enhance feedback when actions complete.
   - **Why now:** Phase 1 conversation felt awkward; must improve before coaching layer.
   - **Delivers:** Natural, smooth GTD conversation.
   - **Derisks:** None (polish).
   - **Depends on:** Edge Case Handling.
   - **Effort:** Small (1-2 days: prompt refinement, conversation pattern examples)

### Success Criteria

- [ ] Zero data loss during 1 week of daily usage
- [ ] Zero partial updates (all relationships created correctly)
- [ ] Claude stores information without explicit prompting 95%+ of the time
- [ ] Claude queries storage before answering 95%+ of the time
- [ ] Conversation feels natural, not database-like
- [ ] All edge cases from Phase 1 validation handled correctly

### Learning Goals

- Which prompt strategies work best for reliable memory management?
- What conversation patterns feel most natural for GTD interaction?
- Are there fundamental limitations in conversational memory management?

### Validation Checkpoint

**Date:** End of Week 3

**Review questions:**
- Is GTD memory management now reliable and consistent?
- Does conversation feel natural?
- Ready to add coaching intelligence?

**Decision criteria:**
- **Proceed to Phase 3:** Core reliability established. Ready for coaching enhancements (observations layer, pattern recognition) in Phase 3 (Week 4+).
- **Iterate:** Improving but still has issues. Continue polishing in extended Phase 2B.
- **Rethink:** Fundamental issues persist despite focused effort. May need architectural changes or different approach.

## Dependencies and Sequencing

### Technical Dependencies

**Serial build sequence (each depends on previous):**
1. File-Storage-Backend Integration (foundation)
2. Graph Memory Core (requires file-storage)
3. GTD Ontology (requires graph core)
4. Conversational Layer (requires GTD ontology)
5. Validation Period (requires conversational layer)

**Phase 2A dependencies:**
- All Phase 2A features require Phase 1 complete and assessed as "solid"
- Observations Layer Integration is foundation for pattern recognition
- Pattern Recognition enables Intelligent Recommendations
- Socratic Questioning builds on Intelligent Recommendations

**Phase 2B dependencies:**
- All Phase 2B features require Phase 1 complete and assessed as "rough"
- Memory Management Reliability must be addressed before edge cases
- Edge Case Handling before conversation flow improvements

### Learning Dependencies

- **Phase 2 choice depends on Phase 1 learning:** If Phase 1 reveals rough integration, must polish (Phase 2B) before enhancing (Phase 2A).
- **Phase 3+ planning depends on Phase 2 learning:** After experiencing coached GTD, patterns of value and areas needing work will inform future priorities.

### External Dependencies

- **Anthropic MCP Memory Server:** Available from GitHub, required for Phase 2A observations layer. No timeline risk (already exists).
- **File-storage-backend:** In progress in adjacent directory, ~1 day remaining. Internal dependency under our control.

## Assumptions and Risks

### Key Assumptions

1. **Claude can reliably manage GTD memory through conversation** (highest risk assumption)
   - Validation: Phase 1 tests this directly with 3-5 days real usage
   - Risk if wrong: Core approach fails; would need to rethink integration strategy

2. **Complete GTD model can be validated as unit** (methodology assumption)
   - Validation: Phase 1 tests full model (Projects, Actions, all connection types)
   - Risk if wrong: May need to simplify model or test incrementally

3. **File-storage-backend completable in ~1 day** (timeline assumption)
   - Validation: Week 1 completion
   - Risk if wrong: Phase 1 timeline extends; could temporarily use existing MCP Memory Server as fallback

4. **2 weeks sufficient for Phase 1 with buffer** (effort assumption)
   - Validation: Progress tracking at week 1 midpoint
   - Risk if wrong: Extend timeline (acceptable; no external deadline)

5. **TDD serial build maintains velocity** (process assumption)
   - Validation: Each feature completes in ~2 days (1 day implementation, 1 day test/debug)
   - Risk if wrong: Adjust estimates; maintain serial approach but allow more time

### Sequencing Risks

- **Phase 1 integration fails:** If conversational memory management doesn't work reliably, entire approach invalid. Mitigation: Find out after 2 weeks, not 3+ months of building.

- **Phase 1 takes longer than 2 weeks:** Timeline extends, potentially pushing Phase 2 beyond 3-week target. Mitigation: Built-in flexibility (3 weeks is preference not commitment), can extend to 4-5 weeks.

- **Phase 2 choice wrong:** Pick Phase 2A but should have done 2B (or vice versa). Mitigation: Checkpoint review explicitly assesses "solid vs rough" with clear criteria.

- **Pattern recognition insufficient coaching value:** Phase 2A delivers technical capability but coaching quality disappointing. Mitigation: Focus on prompt quality before declaring failure; coaching is largely prompt engineering.

### Mitigation Plans

**If Claude memory management unreliable:**
- Investigate whether issue is prompts (fixable with better instructions) or fundamental limitation (requires architectural change)
- Consider hybrid approach (conversational input, explicit confirmation before storage)
- Worst case: Pivot to more structured interaction model with less inference

**If Phase 1 timeline slips:**
- Assess at week 1.5: if behind, identify bottleneck (file-storage, graph complexity, conversational layer)
- Option 1: Accept 2.5-3 week Phase 1 (acceptable; no external deadline)
- Option 2: Simplify GTD model temporarily (defer WaitingOn/Blocks to Phase 2)

**If Phase 2A coaching quality disappointing:**
- Focus on prompt engineering (most coaching value comes from prompts, not code)
- Reference detailed coaching guidelines from inspiration/ directory
- Iterate on pattern observation language and recommendation synthesis
- Consider that coaching relationships build over time (may need sustained usage to judge)

**If developer time drops below 10 hours/week:**
- Timeline extends proportionally (3 weeks → 4-5 weeks)
- No external dependencies affected (solo project, no commitments)
- AI-assisted development maintains progress even at reduced hours

## Flexibility and Change

### Adaptation Triggers

Roadmap adjustments triggered by:

- **Phase 1 validation outcome:** If assessment is "broken" rather than "solid" or "rough," fundamental rethinking required before Phase 2.
- **Phase 1 timeline overrun:** If Phase 1 extends significantly beyond 2 weeks, reassess Phase 2 scope or accept longer total timeline.
- **Phase 2 learning:** Based on coached GTD experience, may reprioritize Phase 3+ features (Context/Person nodes, proactive coaching, etc.).
- **File-storage-backend delay:** If foundation takes longer than expected, adjust timeline or temporarily use existing MCP Memory Server.
- **New constraint:** Changes in available time, resources, or external factors (e.g., Anthropic Memory Tool becomes available, changing architecture needs).

### Review Cadence

- **Mid-Phase 1 (end of Week 1):** Progress check—are features completing on ~2-day schedule? Any blockers?
- **End of Phase 1 (end of Week 2):** Validation checkpoint—assess solid vs rough vs broken, decide Phase 2A or 2B.
- **End of Phase 2 (end of Week 3):** MVP checkpoint—does system deliver coaching value worth daily usage? Ready for real-world hardening and Phase 3+ planning?
- **Monthly after MVP:** Review sustained usage patterns, gather Phase 3+ priorities based on real needs.

### Change Process

When roadmap adjustment needed:

1. **Identify trigger event** (validation checkpoint, timeline slip, new constraint)
2. **Assess impact** on current phase and downstream phases
3. **Propose adjustment:**
   - Continue as planned (trigger was minor)
   - Pivot (change Phase 2 choice, adjust scope, extend timeline)
   - Stop and rethink (fundamental issue requiring architectural change)
4. **Document decision** and rationale
5. **Update ROADMAP.md** with new version in Document Control section
6. **Communicate** (in solo project, this means documenting for future reference and AI agents)

## Document Control

### Version History

**Version 1.1 (2025-10-30)**
- Addressed roadmap review suggestions (reviews/roadmap/2025-10-30-ROADMAP-APPROVED.md)
- Changes:
  - Fixed effort scale consistency: Phase 1 features 1-4 changed from "Medium (~2 days)" to "Small (2 days)" per Small=1-3 days scale
  - Removed boundary-case parentheticals from Medium estimates in Phase 2A/2B for scale consistency
  - Added Feature Mapping crosswalk table in Alignment section showing SCOPE.md Core Features → Roadmap Phases
  - Clarified Validation Period effort as "Small (validation period, not implementation)"

**Version 1.0 (2025-10-30)**
- Initial roadmap created after collaborative roadmap-writing-helper conversation
- Key decisions:
  - Derisk integration risk first strategy (Phase 1 validates Claude memory reliability)
  - Serial TDD build sequence (file-storage → graph → GTD → conversational)
  - Complete GTD model validated as unit (not incremental)
  - Adaptive Phase 2 (2A coaching intelligence if solid, 2B polish core if rough)
  - Realistic timeline (2 weeks Phase 1, 1 week Phase 2, buffer included)
  - Clear checkpoint decision criteria (solid vs rough vs broken)
- Derived from: VISION.md v1.0, SCOPE.md v1.1

### Related Documents

- **[VISION.md](VISION.md)** - Strategic vision and long-term goals (6mo/1yr/3yr success criteria)
- **[SCOPE.md](SCOPE.md)** - Feature boundaries and MVP definition (what's in/out, acceptance criteria)
- **inspiration/** - Detailed GTD specifications, memory architecture, coaching guidelines from prior planning
- **Workflow/** - Artifact-driven development workflow for AI-assisted implementation

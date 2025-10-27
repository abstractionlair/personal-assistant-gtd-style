---
role: Scope Reviewer
trigger: SCOPE.md drafted, before roadmap planning
typical_scope: One SCOPE.md document review
dependencies: [VISION.md, SCOPE.md, schema-scope.md]
outputs: [reviews/scope/TIMESTAMP-FILENAME-STATUS.md]
gatekeeper: false
---

# Scope Reviewer

*Structure reference: [role-file-structure.md](patterns/role-file-structure.md)*

## Purpose

Evaluate SCOPE.md documents for completeness, clarity, and readiness for roadmap planning. See [schema-scope.md](schema-scope.md) for complete structure and validation rules.

Validate scope documents for completeness, clarity, alignment with VISION.md, and feasibility before proceeding to roadmap work.

## When to Use This Role

**Activate when**:
- SCOPE.md drafted and needs validation
- Before proceeding to roadmap planning
- Quarterly scope reviews to check for drift

**Prerequisites**:
- VISION.md exists and is approved
- Draft SCOPE.md exists

**Do NOT use for**:
- Reviewing vision documents (use vision-reviewer)
- Reviewing feature specifications (use spec-reviewer)
- Reviewing implementation code

## Collaboration Pattern

This is an **autonomous role** - reviewer works independently and provides structured feedback.

**Reviewer responsibilities**:
- Read SCOPE.md, schema-scope.md, and VISION.md
- Apply systematic quality criteria
- Check structural completeness
- Verify alignment with vision
- Assess feasibility
- Provide specific, actionable feedback
- Make approval decision (APPROVED / NEEDS-CHANGES)

**Human responsibilities**:
- Provide documents to review
- Clarify intent when reviewer asks questions
- Make decisions on which feedback to address
- Approve revised scope or request changes

## Review Principles

1. **Ontology Compliance**: All required sections present, correct order, correct format
2. **Completeness**: MVP features concrete, out of scope identified, success measurable, constraints documented
3. **Clarity**: Features specific, examples provided, technical terms defined, no ambiguity
4. **Alignment**: Serves VISION.md purpose, success criteria match vision metrics, no contradictions
5. **Feasibility**: MVP scope achievable in timeline, timeline realistic for resources, constraints acknowledged

## Review Process

### Step 1: Load References
Read required documents:
- [schema-scope.md](schema-scope.md) - Structure reference
- VISION.md - Alignment check
- SCOPE.md (draft) - Document to review

### Step 2: Check Structure
Verify all required sections present (see [schema-scope.md](schema-scope.md) for complete list).

### Step 3: Review "In Scope - MVP"

**Check feature specificity**:

**Bad (vague)**:
- User management
- Backend APIs
- Frontend stuff

**Good (specific)**:
- User registration via email/password
- Basic profile editing (name, avatar, bio)
- Create/edit/delete notes with markdown support

**Checklist**:
- [ ] 5-15 features listed
- [ ] Each feature concrete and specific
- [ ] Features user-facing or technical requirements
- [ ] No implementation details (behaviors not technologies)
- [ ] Can visualize what to build from descriptions

**Common fixes**:
- "Authentication system" → "User login/logout via email/password with session management"
- "Database" → "Persistent storage for user data and notes"
- "APIs" → "REST API for user CRUD and note operations"

### Step 4: Review "In Scope - Future Phases"

**Check phasing clarity**:

**Bad**:
- Phase 2: More features
- Phase 3: Advanced stuff

**Good**:
Phase 2 (Post-MVP):
- Real-time collaboration on notes
- Rich text editor with formatting toolbar
- File attachments (images, PDFs)

Phase 3 (Growth):
- Team workspaces
- Permission management
- Activity feeds

**Checklist**:
- [ ] Phases clearly labeled
- [ ] Features specific (same standard as MVP)
- [ ] Logical progression from MVP
- [ ] Reasonable scope per phase

### Step 5: Review "Explicitly Out of Scope"

**Check exclusion clarity**:

**Bad**:
- Mobile apps
- Advanced features
- Integrations

**Good**:
- Native mobile apps (web-only for MVP, native apps in Year 2)
- OAuth/SSO authentication (email/password only for MVP)
- Third-party integrations (Slack, Google Drive - Phase 3)
- Offline mode (online-only for MVP)

**Checklist**:
- [ ] 5-10 items explicitly excluded
- [ ] Each item explains WHY excluded or WHEN deferred
- [ ] Covers common scope creep areas
- [ ] Distinguishes "never" from "later"

**Purpose**: Prevent scope creep and set expectations

### Step 6: Review Success Criteria

**Check measurability**:

**Bad (unmeasurable)**:
- System is fast and reliable
- Users are happy
- Product is successful

**Good (measurable)**:
- 100 active users within 6 months
- System uptime >99.5%
- API response time <200ms (p95)
- 60% user retention after 3 months

**Checklist**:
- [ ] 3-7 criteria present
- [ ] Each criterion specific and measurable
- [ ] Mix of user and technical metrics
- [ ] Aligned with VISION.md success criteria
- [ ] Timeframes specified

**Verify alignment**: Compare to VISION.md success criteria - should match or be subset

### Step 7: Review Constraints

**Check constraint completeness**:

**Required constraint categories**:
- [ ] Timeline constraints (deadlines, milestones)
- [ ] Resource constraints (team size, budget)
- [ ] Technical constraints (languages, platforms, compatibility)
- [ ] Business constraints (legal, regulatory, policy)

**Good example**:

**Timeline**:
- MVP launch by June 1, 2025 (investor demo - hard deadline)
- 3-month development window

**Resources**:
- Solo developer (~20 hours/week)
- $100/month infrastructure budget

**Technical**:
- Python backend (developer expertise)
- Web-only (no mobile native)
- Must support modern browsers (Chrome, Firefox, Safari)

**Business**:
- GDPR compliance required (EU users)
- No payment processing in MVP (reduces regulatory burden)

**Checklist**:
- [ ] All 4 constraint categories addressed
- [ ] Constraints specific (not vague)
- [ ] Impact explained where relevant
- [ ] Constraints realistic

### Step 8: Review Assumptions

**Check assumption explicitness**:

**Bad (implicit)**:
- We can build this
- Users will like it

**Good (explicit)**:
- Solo developer can commit 20 hours/week consistently
- Target users have stable internet (>5 Mbps)
- Markdown is sufficient for note formatting (no WYSIWYG needed)
- Email/password auth is acceptable (users don't require OAuth)

**Checklist**:
- [ ] 5-10 assumptions stated
- [ ] Assumptions testable/verifiable
- [ ] Critical assumptions identified
- [ ] Risks if assumptions wrong considered

### Step 9: Verify Alignment with Vision

**Check consistency**:
- [ ] Scope serves vision purpose
- [ ] Success criteria match or subset vision metrics
- [ ] Target users consistent
- [ ] Timeline consistent
- [ ] No contradictions

**Example alignment check**:
- **VISION.md says**: "Help solo developers maintain context"
- **SCOPE.md should**: Include features for context management, exclude unrelated features

**If misaligned**: Feedback should explain contradiction and suggest fix

### Step 10: Assess Feasibility

**Reality check**:
- [ ] MVP scope achievable in timeline
- [ ] Constraints don't make scope impossible
- [ ] Resource constraints realistic
- [ ] Success criteria achievable

**Red flags**:
- Timeline very short + scope very large
- Resource constraints severe (1 hour/week) + scope large
- Success criteria unrealistic (1M users in 1 month)
- Technical constraints conflict (must use X but X can't do Y)

### Step 11: Provide Review Output

Create structured review document with decision (use format below).

## Review Output Format

```markdown
# Scope Review: [Project Name]

**Reviewer**: [Name/Claude]
**Date**: [YYYY-MM-DD]
**Document**: SCOPE.md
**Version**: [version if tracked]
**Status**: APPROVED | NEEDS-CHANGES

## Summary
[Overall assessment - 1-2 paragraphs]

## Ontology Compliance
- ✓/❌ All required sections present
- ✓/❌ Sections in correct order
- ✓/❌ Format matches ontology

## Completeness Check
- ✓/❌ MVP features specific (5-15 items)
- ✓/❌ Future phases defined
- ✓/❌ Out of scope explicit (5-10 items)
- ✓/❌ Success criteria measurable (3-7 items)
- ✓/❌ All 4 constraint categories addressed
- ✓/❌ Assumptions stated (5-10 items)

## Clarity Assessment
- ✓/❌ Features concrete and specific
- ✓/❌ No vague language
- ✓/❌ Examples provided where needed
- ✓/❌ Technical terms defined

## Alignment Check
- ✓/❌ Serves vision purpose
- ✓/❌ Success criteria match vision
- ✓/❌ No contradictions

## Feasibility Assessment
- ✓/❌ MVP scope achievable in timeline
- ✓/❌ Constraints realistic
- ✓/❌ Success criteria attainable

## Critical Issues (if NEEDS-CHANGES)
1. **[Issue Title]**
   - Section: [which section]
   - Problem: [what's wrong]
   - Impact: [why this matters]
   - Fix: [how to resolve]

## Minor Issues
[Non-blocking improvements]

## Strengths
[What the scope does well]

## Decision
[APPROVED - ready for roadmap-writer]
[NEEDS-CHANGES - address critical issues above]
```

## Common Issues and Fixes

### Vague MVP Features
**Problem**: "User management" or "Backend APIs"
**Impact**: Can't plan roadmap without knowing what to build
**Fix**: "User registration via email/password, profile editing (name, avatar)"

### Missing "Out of Scope"
**Problem**: Only lists included features
**Impact**: Scope creep likely, unclear boundaries
**Fix**: Add 5-10 explicitly excluded items with rationale

### Unmeasurable Success Criteria
**Problem**: "System is reliable and fast"
**Impact**: Can't verify if MVP succeeded
**Fix**: "Uptime >99.5%, API response <200ms p95"

### Timeline Without Constraints
**Problem**: "6 month timeline" with no context
**Impact**: Unclear if aspirational or firm deadline
**Fix**: "6 months (hard deadline: investor demo June 1, 2025)"

### Implicit Assumptions
**Problem**: No assumptions section or very brief
**Impact**: Risks not identified, surprises likely
**Fix**: List 5-10 explicit assumptions (user behavior, technical feasibility, resource availability)

### Future Phases Too Vague
**Problem**: "Phase 2: More features"
**Impact**: No visibility into product direction
**Fix**: "Phase 2: Real-time collaboration, rich text editor, file attachments"

## Handoff to Next Roles

**If APPROVED**:
- Scope ready for **roadmap-writer** to create ROADMAP.md
- Confirm roadmap-writer has clear features to sequence
- Ensure success criteria enable prioritization

**If NEEDS-CHANGES**:
- Return to **scope-writer** with specific feedback
- Iterate until critical issues resolved
- Re-review after revisions

## Integration with Workflow

**Receives**: Draft SCOPE.md
**Produces**: Review in reviews/scope/
**Next**: Roadmap Writer (if approved), Scope Writer (if needs changes)

**To understand where this role fits:** See [workflow-overview.md](workflow-overview.md) role diagram
**For state transitions this role controls:** See [state-transitions.md](state-transitions.md) gatekeeper matrix
**For directory structure and file locations:** See [LayoutAndState.md](LayoutAndState.md)

## Critical Reminders

**Most critical principle**: Vague scope → vague roadmap → vague specs → vague implementation. Ensure clarity!

**DO**:
- Read schema-scope.md for validation rules
- Check all required sections present
- Verify MVP features specific and concrete (5-15 items)
- Ensure "out of scope" has 5-10 explicit items
- Confirm success criteria measurable (3-7 items)
- Validate all 4 constraint categories present
- Check alignment with VISION.md obsessively
- Assess feasibility realistically
- Provide specific, actionable feedback with examples
- Approve when quality bar met (don't nitpick)
- Prioritize issues (P0 blocks, P1 reduces quality, P2 nice-to-have)

**DON'T**:
- Accept placeholders or "TBD" in critical sections
- Allow vague language like "better", "improved", "more"
- Accept vague features ("user management")
- Allow missing "out of scope" section
- Permit unmeasurable success criteria
- Skip alignment check with VISION.md
- Skip feasibility check
- Approve unrealistic scope for resources
- Give vague feedback without concrete fixes
- Focus on minor issues while missing major problems
- Block approval on stylistic preferences
- Focus on writing style over substance

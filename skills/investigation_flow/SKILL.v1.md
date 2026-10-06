---
schema_version: 1
skill_id: investigation_flow
xid: E8B2D6A4C190
aliases: [9C0115875B0C, 3C06EF778A20]
summary: investigate service scope, dependencies, viewpoints, and change targets before estimation or design
applies_when: [user needs impact investigation before estimation or design]
exclusions: [do not decide design or implementation policy, and preserve unknowns explicitly]
inputs: [request, optional service catalog, candidate services, repository or document paths]
outputs: [in-scope and out-of-scope services, change and test viewpoints, target list, uncertainty list]
criteria:
  - id: coverage
    statement: Every investigation coverage area has a recorded state.
    verification: Compare the coverage checklist with the investigation record.
  - id: target_trace
    statement: Requested change, current affected behavior, and impacted targets are mapped.
    verification: Inspect target evidence and difference statements.
  - id: scope_reasons
    statement: Every out-of-scope item and uncertain item has an explicit reason or missing evidence.
    verification: Review the scope and uncertainty lists.
knowledge_needs:
  - id: xddp_basics
    query: XDDP basics
    required_when: Required for change-difference and traceability structure
    seed_xids: [7A2F4C8D1701]
  - id: xddp_supporting_methods
    query: XDDP supporting methods
    required_when: Required for investigation method selection
    seed_xids: [7A2F4C8D1711]
  - id: investigation_coverage_checklist
    query: investigation coverage checklist
    required_when: Required for complete investigation coverage
    seed_xids: [91E2A7C56101]
control_refs: []
---
<!-- xid: E8B2D6A4C190 -->
<a id="xid-E8B2D6A4C190"></a>

# Skill: investigation_flow

## Purpose
Investigate service scope, dependencies, and change targets before estimation or design.

## Method
1. Confirm the request, service catalog, analysis targets, and coverage checklist; record missing evidence as `unknown`.
2. Resolve the XDDP and investigation Knowledge needs.
3. Define targets and the requested difference; use selective spec-out when documents are weak or stale.
4. Analyze service catalog, source/dependencies, and change-target summaries in order.
5. Preserve mappings from requested change to current behavior and impacted candidates; finalize coverage states.

## Stop and handoff
- Do not decide design or implementation policy.
- Stop or downgrade claims when evidence cannot localize impact; hand unresolved and out-of-scope items to estimation or design.

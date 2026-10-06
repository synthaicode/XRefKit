---
schema_version: 1
skill_id: retro
xid: D7F1A4C9B280
aliases: [C17B52E8F4A3, 6E8296A4C2D1]
summary: review work evidence and propose stable promotion candidates while keeping transient items in work
applies_when: [a task or session is ending and stable rules, knowledge, or procedures may need promotion]
exclusions: [do not treat work as canonical, promote unstable notes, or duplicate canonical content]
inputs: [task goal, work session or retrospective files, changed files, optional conversation history and targets]
outputs: [promotion candidate list, target and reasons, evidence references, duplication checks, stay-in-work decisions]
criteria:
  - id: stability
    statement: Candidates are classified by reuse, stability, evidence, and whether they are already canonical.
    verification: Inspect each candidate classification and evidence path.
  - id: destination
    statement: Every proposed promotion has one target class or is explicitly stay_in_work.
    verification: Review target location and reason for every row.
  - id: human_boundary
    statement: Promotion remains a proposal unless the human approves implementation.
    verification: Check the report for explicit disposition and next owner.
knowledge_needs:
  - id: working_area_policy
    query: working area policy
    required_when: Required when reading work records and deciding canonical boundaries
    seed_xids: [111D282CA0EA]
  - id: shared_memory_operations
    query: shared memory operations
    required_when: Required when candidates affect shared memory
    seed_xids: [4A423E72D2ED]
control_refs: [111D282CA0EA]
---
<!-- xid: D7F1A4C9B280 -->
<a id="xid-D7F1A4C9B280"></a>

# Skill: retro

## Purpose
Review session evidence and determine what remains in `work/` versus what may be promoted to canonical assets.

## Method
1. Confirm the session entry, relevant work files, changed files, and canonical search scope.
2. Resolve working-area and shared-memory Knowledge as applicable.
3. Extract reusable stable rules, facts, procedures, and structural issues; classify each as promotion candidate, already promoted, or stay_in_work.
4. Check reuse, stability, future reload value, and equivalent canonical content for every candidate.
5. Produce the promotion report with item, target, reason, evidence, and status.

## Stop and handoff
- Downgrade weak or single-session items to `stay_in_work`; do not create canonical updates from them.
- Promotion requires human approval; hand the report and any approved update plan to `doc_ship`.

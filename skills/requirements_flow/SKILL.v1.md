---
schema_version: 1
skill_id: requirements_flow
xid: D4A7C91E2B60
aliases: [2B70BBF7B7BB, 6720268498FD]
summary: draft requirements and performance constraints while preserving explicit change differences
applies_when: [user needs requirement drafting after investigation and estimation]
exclusions: [do not approve final requirements, hide unresolved assumptions, or collapse change reason and specification]
inputs: [confirmed assumptions, change target list, test viewpoints, request, optional performance constraints]
outputs: [requirement draft, performance requirement definition, load-test draft plan, change-difference view, unresolved list]
criteria:
  - id: difference_trace
    statement: Change reason, change requirement, and change specification remain explicit and traceable.
    verification: Inspect the draft for before/after or equivalent difference mapping.
  - id: evidence_state
    statement: Weak claims and missing performance evidence remain unknown or out_of_scope.
    verification: Check every requirement row for a recorded status and evidence gap.
  - id: handoff
    statement: Unresolved requirement items are handed off without implying approval.
    verification: Inspect the unresolved list and next owner.
knowledge_needs:
  - id: xddp_basics
    query: XDDP basics
    required_when: Required for structuring requirement differences and traceability
    seed_xids: [7A2F4C8D1701]
  - id: xddp_supporting_methods
    query: XDDP supporting methods
    required_when: Required for selecting supporting requirement methods
    seed_xids: [7A2F4C8D1711]
control_refs: []
---
<!-- xid: D4A7C91E2B60 -->
<a id="xid-D4A7C91E2B60"></a>

# Skill: requirements_flow

## Purpose
Prepare requirement outputs for planning and validation while preserving change differences.

## Method
1. Confirm assumptions, targets, viewpoints, and performance evidence when in scope; record missing evidence as `unknown`.
2. Resolve the XDDP Knowledge needs.
3. Define requirement areas and separate change reason, change requirement, and change specification, preferably in before/after form.
4. Draft requirement and performance outputs at a precision usable downstream; preserve unresolved gaps.
5. Write outputs to the requested location and finalize rows as `done`, `unknown`, or `out_of_scope`.

## Stop and handoff
- Stop when the requested difference cannot be stated clearly enough for tracing.
- Do not approve the draft; hand unresolved items to review or approval owners.

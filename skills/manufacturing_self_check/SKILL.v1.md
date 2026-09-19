---
schema_version: 1
skill_id: manufacturing_self_check
xid: F1C8A3E6B270
aliases: [5D4E91B0D110, 60B1B69B0984]
summary: check manufacturing outputs against approved design before quality review
applies_when: [code, DB or persistence manufacturing and unit testing are complete and an internal alignment check is needed]
exclusions: [internal manufacturing check only; it does not replace quality-group review or silently change design policy]
inputs: [implemented code, DB manufacturing artifacts when in scope, approved design, unit test results, coding rules]
outputs: [self-check result, design-alignment findings, DB findings when applicable, unresolved list]
criteria:
  - id: design_alignment
    statement: Every finding maps to approved design evidence or an explicit evidence gap.
    verification: Inspect code and DB findings for source design pointers.
  - id: artifact_coverage
    statement: In-scope DB manufacturing artifacts and tests are checked and omissions remain unknown.
    verification: Compare targets with the artifact inventory and test evidence.
  - id: quality_handoff
    statement: Self-check results and unresolved items are handed to quality review without claiming independent QA.
    verification: Inspect the handoff and unresolved list.
knowledge_needs:
  - id: csharp_quality_review_criteria
    query: C# quality review criteria
    required_when: Required when checking implemented C# alignment
    seed_xids: [8C4D2A7E5101]
  - id: implementation_assumption_gap_handling
    query: implementation assumption gap handling
    required_when: Required when classifying implementation assumption gaps
    seed_xids: [7A2F4C8D1501]
control_refs: []
---
<!-- xid: F1C8A3E6B270 -->
<a id="xid-F1C8A3E6B270"></a>

# Skill: manufacturing_self_check

## Purpose
Verify manufacturing outputs remain aligned with approved design before external QA review.

## Method
1. Confirm implemented code, approved design, unit-test evidence, and in-scope DB artifacts; record missing evidence as `unknown`.
2. Resolve quality and implementation-assumption Knowledge needs.
3. Define targets, splitting by artifact family when context breadth requires it, while retaining explicit merge ownership.
4. Compare code and DB artifacts with design, current-state basis, migrations, mappings, seed/correction paths, transactions, and SQL behavior.
5. Record alignment findings and assumption gaps, then finalize the result and handoff.

## Stop and handoff
- Downgrade unsupported alignment claims to `unknown`; do not silently change design policy.
- Hand self-check results, DB findings, and unresolved items to quality-group review.

---
schema_version: 1
skill_id: manufacturing_self_check
xid: F1C8A3E6B270
summary: check manufacturing outputs against approved design before quality review
applies_when:
- code, DB, or persistence implementation and unit testing are complete and manufacturing needs an internal alignment check
exclusions:
- internal manufacturing check only; it does not replace quality-group review or silently change design policy
inputs:
- implemented code, DB manufacturing artifacts when in scope, approved design, unit test results, coding rules
outputs:
- self-check result, design-alignment findings for code and DB manufacturing results, unresolved list
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
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: csharp_quality_review_criteria
  query: C# quality review criteria
  required_when: Required when checking implemented C# alignment
  seed_xids:
  - 8C4D2A7E5101
- id: implementation_assumption_gap_handling
  query: implementation assumption gap handling
  required_when: Required when classifying implementation assumption gaps
  seed_xids:
  - 7A2F4C8D1501
control_refs: []
aliases:
- 5D4E91B0D110
- 60B1B69B0984
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

## Additional bound references retained at repository cutover

These references were explicitly bound by the prior repository Skill. Apply them to the relevant method work; resolve their XIDs on demand.

- [Metrics Definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: manufacturing_self_check

## Purpose

Execute `CAP-MFG-004` and verify that manufacturing outputs remain aligned
with approved design before external QA review. Manufacturing outputs include
code and, when in scope, DB/persistence artifacts such as DDL, migrations,
generated SQL, checked-in SQL scripts, stored procedures, ORM mappings, seed
data, data correction/backfill scripts, and DB test output.

## Required Capability Definitions (XID)


- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)
- [Implementation assumption gap handling](../../knowledge/organization/150_implementation_assumption_gap_handling.md#xid-7A2F4C8D1501)

## Inputs

- implemented code
- DB manufacturing artifacts when in scope: DDL, migrations, generated SQL,
  checked-in SQL scripts, stored procedures, ORM/persistence mappings, seed
  data, correction/backfill scripts, deployment scripts, or DB test output
- approved design
- unit test results
- coding rules

## Outputs

- self-check result
- design-alignment findings
- DB manufacturing alignment findings when database or persistence artifacts are
  in scope
- unresolved list
- execution metrics log

## Startup

- Confirm implemented code exists.
- Confirm DB manufacturing artifacts exist when database, persistence,
  migration, SQL, data correction, or stored-procedure work is in scope.
- Confirm approved design evidence exists.
- Confirm unit-test evidence exists.
- Record `unknown` if required evidence is missing.

## Planning

- Define self-check targets by file, module, or change area.
- Include DB manufacturing outputs in self-check targets when the implementation
  includes schema, migration, SQL, stored procedure, ORM, data correction, seed,
  or deployment-time DB artifacts.
- Decide whether the self-check can fit one context. When code changes, DB
  artifacts, unit-test evidence, and design evidence are too broad for one
  context, split into subagents by target boundary or artifact family:
  - code implementation alignment
  - DB manufacturing artifact alignment
  - unit-test and validation evidence
  - unresolved implementation assumption gaps
- Keep one coordinator context for scope, duplicate finding merge, unresolved
  item classification, and quality-review handoff.
- Map the business activity to its supporting capability:
  - manufacturing self check -> `CAP-MFG-004`
- Prepare management rows for alignment findings and unresolved items.

## Execution

- Perform manufacturing self check by executing `CAP-MFG-004`.
- Compare implemented code against approved design evidence.
- Compare DB manufacturing artifacts against approved DB design evidence,
  current database state basis, naming/rule basis, migration/correction plan,
  and validation handoff.
- Check that DB artifacts do not introduce untraced tables, columns,
  constraints, indexes, procedures, functions, triggers, schemas, seed data,
  correction paths, transaction behavior, isolation choices, or SQL
  error-handling behavior.
- Check whether local changes stay inside approved boundaries.
- Verify that each implementation assumption gap was recorded and classified under the handling rule.
- Produce self-check findings and explicit unresolved items.

## Monitoring and Control

- Downgrade unsupported alignment claims to `unknown`.
- Downgrade an alignment area to `unknown` when evidence was omitted due to
  context limits and no subagent result exists.
- Preserve explicit design gaps and out-of-scope reasons.
- Attach execution metrics to the result.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off self-check results to quality-group review.
- Include DB manufacturing alignment findings and unresolved DB verification
  items in the quality-group handoff.
- Escalate out-of-scope items when reassignment is required.

## Rules

- This is manufacturing-side self-control, not an independent QA substitute.
- Every finding must map back to design evidence or an explicit evidence gap.
- Every implementation assumption gap must be either recorded or raised as a self-check finding.
- Every DB manufacturing artifact must map back to approved DB design evidence,
  current database state basis, or an explicit evidence gap.
- Do not silently change design policy.

## Reporting Contract (共通報告)



- reporting_profile: checklist_verdict

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: execute manufacturing self-check business activity through reusable design-alignment self-evaluation capability

- use_when: code, DB, or persistence implementation and unit testing are complete and manufacturing needs an internal alignment check

- input: implemented code, DB manufacturing artifacts when in scope, approved design, unit test results, coding rules

- output: self-check result, design-alignment findings for code and DB manufacturing results, unresolved list

- constraints: internal manufacturing check only; does not replace quality-group review; when code, DB artifacts, tests, and design evidence together risk context overflow, split self-check execution into subagents by artifact family or target boundary and merge results explicitly

- lifecycle:
  - startup: confirm implemented code, DB manufacturing artifacts when in scope, design evidence, and unit-test evidence exist
  - planning: define self-check targets including DB manufacturing outputs, management rows, and subagent split when evidence breadth risks context overflow
  - execution: perform manufacturing self-check through `CAP-MFG-004`, comparing code and DB manufacturing artifacts against approved design evidence
  - monitoring_and_control: downgrade unsupported alignment claims to `unknown`
  - closure: finalize states and hand off results to quality review

- tags: `manufacturing`, `self-check`, `quality`

- knowledge_slots:
  - name=csharp_quality_review_criteria; bind=8C4D2A7E5101
  - name=metrics_definition; bind=7A2F4C8D1201

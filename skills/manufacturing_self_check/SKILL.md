<!-- xid: 5D4E91B0D110 -->
<a id="xid-5D4E91B0D110"></a>

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


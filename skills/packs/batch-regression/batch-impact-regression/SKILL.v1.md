---
schema_version: 1
skill_id: batch_impact_regression
xid: E8F6C3A1D952
summary: Analyze C# and SQL Server stored-procedure batch changes with deterministic combination regression and human-gated classification
applies_when:
- a requirement changes an existing C# batch and SQL Server SP execution path, especially when combinations are numerous and no formal test dataset exists
exclusions:
- Do not execute against production
- Do not treat a baseline as business truth or infer business constraints from source conditions
- Do not send the full candidate space to the model
inputs:
- configuration, C# solution/project and batch command, isolated test DB details, old/new selectors, combination values and constraints, expected differences, result contract, and evidence paths
outputs:
- deterministic candidate/comparison reports, reduced regression set, full-run procedure, impact trace, unresolved decisions, and handoff artifacts
criteria:
- id: deterministic_reduction
  statement: Candidate generation, configured constraint application, normalization, comparison, aggregation, and reduced-set selection are reproducible and preserve source/result evidence
  verification: Re-run the deterministic script and compare the JSON/CSV reports and reduced-set recipe
- id: human_classification
  statement: Differences remain classified as baseline_match, planned_difference, unexplained_difference, business_invalid, upstream_absent, uncertain, system_error, or not_executed, with human decisions preserved
  verification: Inspect every difference class and its evidence and decision owner
- id: safe_closure
  statement: Production is prohibited, fixture mode is labeled, unknown or unsafe dynamic behavior stops or escalates, and closure includes full-run and business/release handoff
  verification: Check the safe-execution gate, unknowns, risks, and handoff artifacts
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs: []
control_refs: []
aliases:
- 517E99B3082E
- 9D2E6A4C7B81
---
<!-- xid: E8F6C3A1D952 -->
<a id="xid-E8F6C3A1D952"></a>

# Batch Impact Regression

## Purpose

Establish observed behavior for an existing C# batch backed by SQL Server stored
procedures, compare old and changed versions on the same deterministic inputs,
and produce evidence for human business judgment. Deterministic scripts own
combination generation, configured constraints, normalization, comparison,
aggregation, and reproducible regression-set selection.

## Method

Follow the local 15-step workflow and safe-execution gate. Confirm the
configuration, source and result boundaries, old/new selectors, isolated test
database or fixture adapter, explicit factor values and constraints, expected
differences, result contract, and output paths. Trace C# entry points and
parameters through stored procedures, child procedures, functions, views,
tables, dynamic SQL, transactions, result contracts, and side effects. Run
`scripts/batch_regression.py extract-tables` and subsequent deterministic
processing to generate candidate and comparison JSON/CSV artifacts; use fixture
mode only when labeled. Never send the full candidate space to the model.

Do not infer a business constraint from a source condition or treat the baseline
as business truth. Normalize only configured non-deterministic fields. For every
difference preserve input, old result, new result, constraint evidence,
planned-requirement relation, and C#/SP path references. Keep
`baseline_match`, `planned_difference`, `unexplained_difference`,
`business_invalid`, `upstream_absent`, `uncertain`, `system_error`, and
`not_executed` distinct. A human decides business validity, baseline-defect
acceptance, allowed planned differences, and whether unexplained differences
block release. Stop and escalate when required rules, dynamic SQL or procedure
targets, DB side effects, or expected differences lack evidence. Closure
requires deterministic reports, a reduced-set recipe, a release-time full-run
procedure, resolved or escalated unknowns and risks, and handoff to the business
owner and release/test owner.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Batch Impact Regression

## Purpose

Establish the existing batch's observed behavior as a baseline, compare the
old and changed versions on the same deterministic inputs, and produce an
evidence-linked report for human business judgment. The Skill controls the
workflow; deterministic scripts generate combinations, apply only explicitly
configured constraints, normalize results, compare outcomes, aggregate counts,
and select a reproducible regression set.

## Required Knowledge (XID)

- [Skill operating contract](../../../../docs/core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [Context direction guard](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Optional References

- [Workflow and decision rules](./references/workflow.md)
- [Configuration schema](./references/config-schema.md)
- [C# and SQL Server analysis checklist](./references/csharp-sql-analysis.md)
- [Adapter boundary](./references/adapter-contract.md)
- [Code table extraction](./references/code-table-extraction.md)
- [Configuration template](./references/config.template.json)

## Inputs and Outputs

Inputs are a configuration file, source locations, safe test-DB execution
details, old/new version selectors, explicit combination values and
constraints, expected differences, and old/new result files or adapters.
Outputs are JSON/CSV candidate and comparison reports, a reduced regression
set, an evidence-backed impact note, unresolved human decisions, and a
release-time full-run procedure. Real batch/DB execution is available only
through an explicitly implemented adapter; fixture mode must be labeled as
fixture mode.

## Workflow

Follow the 15-step sequence in `references/workflow.md` without skipping the
safe-execution gate. Inspect C# and SQL Server as one execution path: trace C#
entry points and parameters into SPs, then trace child SPs, functions, views,
tables, dynamic SQL, transactions, result contracts, and side effects.

Use `scripts/batch_regression.py extract-tables <source-root> -o <report.json>`
to scan C# and `.sql` source for conservative condition evidence, decision
table rows, inferred factor values, and a strength-2 pairwise covering-table
candidate (an orthogonal-table candidate, not a proof of a mathematically
balanced orthogonal array).
Treat `<unknown>` values and all scanner limitations as human-review items.
Use `scripts/batch_regression.py` for deterministic processing. Never send the
full candidate space to the model. Do not infer a business constraint from a
source condition or treat the baseline as business truth.

## Required Classification and Comparison Rules

Keep these outcomes distinct: `baseline_match`, `planned_difference`,
`unexplained_difference`, `business_invalid`, `upstream_absent`, `uncertain`,
`system_error`, and `not_executed`. Normalize only configured non-deterministic
fields. Preserve input, old result, new result, constraint evidence, planned
requirement relation, and C#/SP path references for every difference.

## Human Boundary and Closure

The human decides business validity, whether a baseline defect is accepted,
which planned differences are allowed, and whether unexplained differences
may block release. Stop and escalate when a required rule, dynamic SQL/SP
target, DB side effect, or expected difference lacks evidence. Closure requires
the deterministic report, reduced-set recipe, full-run procedure, all unknowns
and risks resolved or escalated, and an explicit handoff to the business owner
and release/test owner.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: analyze C# and SQL Server stored-procedure batch changes with deterministic combination regression and human-gated classification

- use_when: a requirement changes an existing C# batch and SQL Server SP execution path, especially when combinations are numerous and no formal test dataset exists

- input: configuration, C# solution/project and batch command, isolated test DB details, old/new selectors, combination values and constraints, expected differences, result contract, and evidence paths

- output: deterministic candidate/comparison reports, reduced regression set, full-run procedure, impact trace, unresolved decisions, and handoff artifacts

- constraints: never treat the baseline as business truth; never infer constraints; never execute against production; never let the model process the full candidate space; dynamic SQL or unresolved dynamic SP names remain uncertain; unexplained differences are not auto-accepted

- lifecycle:
  - startup: load the operating contract, context guard, configuration schema, and adapter boundary; confirm public Skill inputs and safe DB target
  - planning: define the 15-step worklist, source/result boundaries, deterministic operations, human decisions, and stop conditions
  - execution: run the deterministic script over fixture or adapter-produced artifacts, preserving evidence and version selectors
  - monitoring_and_control: stop on unsafe DB scope, missing rule evidence, unresolved dynamic dispatch, or unexplained side effects; record unknown/risk/judgment concerns
  - closure: require JSON/CSV report, reduced-set recipe, full-run procedure, evidence paths, and resolved/escalated human decisions
  - handoff: deliver the report to the business owner and release/test owner; identify remaining adapter or environment work explicitly

- tags: `batch`, `csharp`, `sql-server`, `regression`, `impact-analysis`

- knowledge_slots:
  - name=skill_operating_contract; bind=B7A2C94F0E61
  - name=context_direction_guard; bind=7A2F4C8D1601

- observation_refs:
  - `../../../../observations/2026-05-10_session_skill_flow_authoring_seed.md`

Original source description: Analyze change impact and combination regression for existing C# batches backed by SQL Server stored procedures. Use when a business requirement changes a batch whose rules, validation, calculations, updates, or combination validity may be split between C# and SQL Server, especially when the candidate space is large and no formal test dataset exists.

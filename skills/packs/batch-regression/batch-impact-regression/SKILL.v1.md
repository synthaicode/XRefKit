---
schema_version: 1
skill_id: batch_impact_regression
xid: E8F6C3A1D952
aliases:
  - 517E99B3082E
  - 9D2E6A4C7B81
summary: Analyze C# and SQL Server stored-procedure batch changes with deterministic combination regression and human-gated classification
applies_when:
  - A requirement changes an existing C# batch and SQL Server stored-procedure execution path, especially when combinations are numerous and no formal test dataset exists
exclusions:
  - Do not execute against production
  - Do not treat a baseline as business truth or infer business constraints from source conditions
  - Do not send the full candidate space to the model
inputs:
  - Configuration, source locations, safe isolated test-DB details, old/new selectors, explicit combination values and constraints, expected differences, and old/new result files or adapters
outputs:
  - Evidence-linked deterministic candidate and comparison reports, reduced regression set, full-run procedure, impact note, unresolved human decisions, and release/test handoff
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
knowledge_needs: []
control_refs: []
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

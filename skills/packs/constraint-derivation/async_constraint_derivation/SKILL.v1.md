---
schema_version: 1
skill_id: async_constraint_derivation
xid: 9A4C7E1D2B60
summary: derive concurrency and asynchronous execution constraints from explicit design or code structure
applies_when:
- queue, job, or batch specs may leave retry, restart, duplicate-run, or partial-failure behavior to implicit AI completion
exclusions:
- Generic runtime possibilities without explicit structural evidence are outside this Skill
- Implementation policy is not decided unless explicitly requested
inputs:
- job definitions, batch designs, queue models, schedule rules, and async processing notes
outputs:
- ACD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and rerun or restart matrices where required
criteria:
- id: evidence_boundary
  statement: Every derivation is grounded in explicit structural evidence and unsupported business meaning remains unresolved
  verification: Review each item against its source structure and record unresolved gaps
- id: output_closure
  statement: The derivation output exists at the declared path and reports confirmation items and remaining gaps
  verification: Check the output path and closure report before handoff
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: constraint_derivation_framework
  query: constraint derivation framework
  required_when: Required for this Skill's derivation and classification
  seed_xids:
  - 81A6C4E2B190
- id: async_constraint_derivation_catalog
  query: async constraint derivation catalog
  required_when: Required for this Skill's derivation and classification
  seed_xids:
  - 72ECA94D1B35
control_refs:
- 111D282CA0EA
aliases:
- F6580A1C2344
- F6580A1C2345
- F6580A1C2346
---
<!-- xid: 9A4C7E1D2B60 -->
<a id="xid-9A4C7E1D2B60"></a>

# Skill: async_constraint_derivation

## Purpose

Derive requirement confirmation gates from asynchronous and batch execution
structure before restart and recovery behavior becomes implicit.

## Inputs

- queue designs, job definitions, batch specs, and schedule rules

## Outputs

- ACD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- rerun or restart matrices where required
- written output path

## Startup

- Confirm the input contains queue, job, batch, or schedule structure.
- Load the framework and the async catalog.
- Identify rerun, duplicate-start, partial-failure, and schedule-boundary surfaces.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_async_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate queue, job, batch, schedule, and state-management elements.
2. Apply the async catalog and assign `ACD-` ids.
3. Expand rerun or restart matrices where repeated or partial execution is possible.
4. Group the results by processing unit.
5. Keep unresolved restart, recovery, and schedule behavior explicit.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not assume successful rerun semantics from the platform alone.
- Stop if partial-failure handling or duplicate-start behavior is left unstated.
- Preserve traceability from each ACD item back to the execution structure.

## Closure

- Return the ACD table and grouped unresolved items.
- Highlight any restart, duplicate-run, or schedule gaps blocking implementation.
- Return the written output path.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: async_constraint_derivation

## Purpose

Derive requirement confirmation gates from asynchronous and batch execution
structure before restart and recovery behavior becomes implicit.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Async constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/160_async_constraint_derivation_catalog.md#xid-72ECA94D1B35)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Primary derivation output template](../references/primary_derivation_output_template.md#xid-FF9A33B945ED)

## Inputs

- queue designs, job definitions, batch specs, and schedule rules

## Outputs

- ACD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- rerun or restart matrices where required
- written output path

## Startup

- Confirm the input contains queue, job, batch, or schedule structure.
- Load the framework and the async catalog.
- Identify rerun, duplicate-start, partial-failure, and schedule-boundary surfaces.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_async_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate queue, job, batch, schedule, and state-management elements.
2. Apply the async catalog and assign `ACD-` ids.
3. Expand rerun or restart matrices where repeated or partial execution is possible.
4. Group the results by processing unit.
5. Keep unresolved restart, recovery, and schedule behavior explicit.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not assume successful rerun semantics from the platform alone.
- Stop if partial-failure handling or duplicate-start behavior is left unstated.
- Preserve traceability from each ACD item back to the execution structure.

## Closure

- Return the ACD table and grouped unresolved items.
- Highlight any restart, duplicate-run, or schedule gaps blocking implementation.
- Return the written output path.

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

- summary: derive requirement confirmation gates from asynchronous jobs, queues, schedules, and batch execution structure

- use_when: queue, job, or batch specs may leave retry, restart, duplicate-run, or partial-failure behavior to implicit AI completion

- input: job definitions, batch designs, queue models, schedule rules, and async processing notes

- output: ACD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and rerun or restart matrices where required

- constraints: derive from execution model and state management, not nominal completion paths; keep restart, duplicate-run, schedule-boundary, and partial-failure gaps explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm the input contains async or batch execution structure and load the shared framework plus the async catalog
  - planning: identify queues, jobs, batches, schedule rules, and execution-state surfaces
  - execution: derive ACD items, expand rerun matrices where needed, and keep unsupported recovery behavior unresolved
  - monitoring_and_control: stop if rerun or multi-start behavior is being guessed from platform expectations rather than explicit rules
  - closure: return the derivation table, grouped confirmation items, and blocking restart or schedule gaps

- tags: `design`, `async`, `requirements-derivation`

- knowledge_slots:
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=async_constraint_derivation_catalog; bind=72ECA94D1B35

- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md

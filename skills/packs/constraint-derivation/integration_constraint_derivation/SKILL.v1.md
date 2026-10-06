---
schema_version: 1
skill_id: integration_constraint_derivation
xid: 9A1C4E7D2B60
summary: derive requirement confirmation gates from external APIs, webhooks, files, and messaging integration structure
applies_when:
- external integration specs may leave failure, timing, retry, or idempotency behavior to implicit AI completion
exclusions:
- derive from integration structure and failure modes, not nominal success cases
- implementation policy is not decided unless explicitly requested
inputs:
- API specs, integration flow diagrams, webhook notes, file exchange definitions, and messaging contracts
outputs:
- ICD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and idempotency or retry matrices where required
criteria:
- id: integration_evidence
  statement: Every ICD item is grounded in an identified external integration surface.
  verification: Check each item against API, webhook, file, message, or service evidence.
- id: failure_completeness
  statement: Retry, timeout, ordering, and idempotency gaps remain explicit.
  verification: Review the corresponding integration matrix and unresolved items.
- id: output_closure
  statement: The derivation result exists at the declared output path with grouped confirmations and gaps.
  verification: Check the output path before handoff.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: constraint_derivation_framework
  query: constraint derivation framework
  required_when: Required for deriving and classifying integration signals
  seed_xids:
  - 81A6C4E2B190
- id: integration_constraint_derivation_catalog
  query: integration constraint derivation catalog
  required_when: Required for selecting integration signal categories
  seed_xids:
  - 6F0D7C1A2E44
control_refs:
- 111D282CA0EA
aliases:
- E547F90B1234
- E547F90B1235
---
<!-- xid: 9A1C4E7D2B60 -->
<a id="xid-9A1C4E7D2B60"></a>

# Skill: integration_constraint_derivation

## Purpose

Derive requirement confirmation gates from external integration structure before failure handling gets completed implicitly.

## Inputs
- API specs, webhook definitions, file contracts, and messaging designs

## Outputs
- ICD-prefixed derivation basis table
- grouped requirement confirmation list
- retry or idempotency matrices where required
- written output path

## Startup
- Confirm the input contains external integration structure.
- Load the framework and integration catalog Knowledge.
- Identify retry, timeout, ordering, and idempotency surfaces.
- Use `work/constraint_derivation/YYYY-MM-DD_integration_constraint_derivation_<topic>.md` unless an output path is supplied.

## Execution
1. Enumerate API, webhook, file, message, and external-service interaction points.
2. Apply the integration catalog and assign `ICD-` ids.
3. Expand retry or idempotency matrices where repeated execution is possible.
4. Group results by integration surface and keep unresolved behavior explicit.
5. Write the result using the primary derivation output template or an equivalent structure.

## Monitoring and Control
- Do not assume provider defaults satisfy the business requirement.
- Stop if retry or duplicate-delivery behavior is left implicit.
- Preserve links from each ICD item back to integration evidence.

## Closure and Handoff
- Return the ICD table, grouped unresolved items, blocking gaps, and written path.
- Hand unresolved requirement decisions to the responsible human or design owner.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: integration_constraint_derivation

## Purpose

Derive requirement confirmation gates from external integration structure before
failure handling gets completed implicitly.

## Required Knowledge (XID)

- [Constraint derivation framework](../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Integration constraint derivation catalog](../../../../knowledge/packs/constraint-derivation/150_integration_constraint_derivation_catalog.md#xid-6F0D7C1A2E44)
- [Working area policy](../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)

## Optional References

- [Primary derivation output template](../references/primary_derivation_output_template.md#xid-FF9A33B945ED)

## Inputs

- API specs, webhook definitions, file contracts, and messaging designs

## Outputs

- ICD-prefixed derivation basis table written to a Markdown file
- grouped requirement confirmation list
- retry or idempotency matrices where required
- written output path

## Startup

- Confirm the input contains external integration structure.
- Load the framework and the integration catalog.
- Identify retry, timeout, ordering, and idempotency surfaces.
- Determine the output path:
  - default: `work/constraint_derivation/YYYY-MM-DD_integration_constraint_derivation_<topic>.md`
  - otherwise use the user-specified path

## Execution

1. Enumerate API, webhook, file, message, and external-service interaction points.
2. Apply the integration catalog and assign `ICD-` ids.
3. Expand retry or idempotency matrices where repeated execution is possible.
4. Group the results by integration surface.
5. Keep unresolved timeout, retry, ordering, and confirmation behavior explicit.
6. Write the result by using `references/primary_derivation_output_template.md` or an equivalent structure.

## Monitoring and Control

- Do not assume provider defaults satisfy the business requirement.
- Stop if retry or duplicate-delivery behavior is left implicit.
- Preserve explicit links from each ICD item back to the integration structure.

## Closure

- Return the ICD table and grouped unresolved items.
- Highlight any retry, timeout, or idempotency gaps blocking implementation.
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

- summary: derive requirement confirmation gates from external APIs, webhooks, files, and messaging integration structure

- use_when: external integration specs may leave failure, timing, retry, or idempotency behavior to implicit AI completion

- input: API specs, integration flow diagrams, webhook notes, file exchange definitions, and messaging contracts

- output: ICD-prefixed derivation file under `work/constraint_derivation/` by default, plus grouped confirmation items and idempotency or retry matrices where required

- constraints: derive from integration structure and failure modes, not nominal success cases; keep retry, timeout, idempotency, and ordering gaps explicit; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm the input contains external integration structure and load the shared framework plus the integration catalog
  - planning: identify synchronous, asynchronous, file, webhook, and messaging surfaces
  - execution: derive ICD items, expand idempotency matrices where needed, and emit unresolved behavior explicitly
  - monitoring_and_control: stop if failure handling is being assumed from generic platform norms rather than design evidence
  - closure: return the derivation table, grouped confirmation items, and blocking retry or idempotency gaps

- tags: `design`, `integration`, `requirements-derivation`

- knowledge_slots:
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=integration_constraint_derivation_catalog; bind=6F0D7C1A2E44

- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md

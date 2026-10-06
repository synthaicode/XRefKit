---
schema_version: 1
skill_id: judgment_log
xid: C6A2E9B4D170
summary: write an inspectable judgment log with decision, evidence, inference boundary, confidence, and next verification
applies_when:
- a task produces a non-trivial judgment that should be inspectable or reusable later, especially when confidence is mixed or alternatives exist
exclusions:
- do not present inferred-only judgments as facts or hide material alternatives and open questions
inputs:
- work type, target, decision, evidence, confidence, optional alternatives, optional open questions, optional output path
outputs:
- judgment log file and normalized judgment summary
criteria:
- id: evidence_boundary
  statement: Facts, inferences, evidence types, confidence, and decision status are separated.
  verification: Inspect the normalized log fields and evidence paths.
- id: uncertainty
  statement: Inferred-only or weakly supported decisions are downgraded to unknown when appropriate.
  verification: Compare confidence and evidence with the recorded status.
- id: next_check
  statement: Alternatives, open questions, and the next verification step are preserved.
  verification: Inspect the log before handoff.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: judgment_log_schema
  query: judgment log schema
  required_when: Required for every judgment log
  seed_xids:
  - 7B4C2D91E621
control_refs:
- 111D282CA0EA
aliases:
- 2A9E4C71D5F2
- E3C8A16D4B02
---
<!-- xid: C6A2E9B4D170 -->
<a id="xid-C6A2E9B4D170"></a>

# Skill: judgment_log

## Purpose
Write an AI-authored judgment log recording a non-trivial decision, evidence, inference boundary, and next verification step.

## Method
1. Confirm the target and evidence; record missing evidence as `unknown`.
2. Resolve the judgment schema Knowledge and classify evidence as `deterministic`, `context_extracted`, or `inferred`.
3. Classify status as `proposed`, `accepted`, `rejected`, `unknown`, or `deferred`.
4. Normalize path-specific evidence, decision, confidence, alternatives, open questions, and next check.
5. Write to `work/judgments/` or the requested path using the judgment template or equivalent.

## Stop and handoff
- Preserve uncertainty and never mix session facts with judgment reasoning.
- If the target is unwritable, return normalized content and intended path; hand unresolved decisions to the human owner.

## Additional bound references retained at repository cutover

These references were explicitly bound by the prior repository Skill. Apply them to the relevant method work; resolve their XIDs on demand.

- [Metrics Definition](../../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: judgment_log

## Purpose

Write an AI-authored judgment log that records a non-trivial decision, its evidence, its inference boundary, and the next verification step.

Use the canonical schema in `knowledge/organization/121_judgment_log_schema.md#xid-7B4C2D91E621`.

## Required Knowledge (XID)

- [Working area policy](../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA)
- [Shared memory operations](../../../docs/core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED)
- [Metrics definition](../../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)
- [Judgment log schema](../../../knowledge/organization/121_judgment_log_schema.md#xid-7B4C2D91E621)

## Optional References

- [Judgment log template](references/judgment_log_template.md#xid-B1F7D54A9C33)

## Inputs

- work type or task name
- target
- decision or candidate decision
- evidence paths or evidence summary
- confidence
- optional alternatives
- optional open questions
- optional output path

## Outputs

- judgment log in `work/judgments/` or user-specified path
- normalized evidence and inference boundary

## Startup

- Confirm the target judgment exists.
- Confirm evidence exists or record the judgment as `unknown`.
- Load the judgment log schema.

## Planning

- Separate observed facts from inferred conclusions.
- Classify evidence as:
  - `deterministic`
  - `context_extracted`
  - `inferred`
- Determine whether the decision status is:
  - `proposed`
  - `accepted`
  - `rejected`
  - `unknown`
  - `deferred`

## Execution

- Normalize the evidence into path-specific references when possible.
- Record the decision, decision status, evidence, evidence type, confidence, and context usage.
- Record alternatives when other plausible interpretations exist.
- Record open questions and the next recommended check.
- Write the log by using `references/judgment_log_template.md` or an equivalent structure.

## Monitoring and Control

- Downgrade the decision to `unknown` when evidence is only inferred and no explicit provisional acceptance exists.
- Preserve uncertainty instead of compressing it into a confident summary.

## Closure

- Return the written judgment log path.
- Return the final decision status and remaining open questions.

## Rules

- Do not mix session facts and judgment reasoning in the same file.
- Do not hide alternatives that materially change the next step.
- Do not present inferred-only judgments as completed facts.
- Prefer exact evidence paths over broad summary text.

## Failure Handling

- If the target path is not writable, return the normalized content and intended path.
- If evidence is missing, write the record as `unknown` with explicit missing evidence.

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: write a judgment log that records decision, evidence, inference boundary, confidence, and next verification step

- use_when: a task produces a non-trivial judgment that should be inspectable or reusable later, especially when confidence is mixed or alternatives exist

- input: work type, target, decision, evidence, confidence, optional alternatives, optional open questions, optional output path

- output: judgment log file and normalized judgment summary

- constraints: separate facts from inference; do not present inferred-only judgments as normal completion; preserve alternatives and open questions

- lifecycle:
  - startup: confirm judgment target and evidence, then load the schema
  - planning: separate facts from inference and classify evidence type and decision status
  - execution: write the normalized judgment log
  - monitoring_and_control: downgrade inferred-only or weakly supported conclusions as needed
  - closure: return path, status, and remaining open questions

- tags: `logging`, `judgment`, `traceability`, `work`

- knowledge_slots:
  - name=working_area_policy; bind=111D282CA0EA
  - name=shared_memory_operations; bind=4A423E72D2ED
  - name=metrics_definition; bind=7A2F4C8D1201
  - name=judgment_log_schema; bind=7B4C2D91E621

- observation_refs:
  - `../../../observations/2026-06-23_csharp_review_bad_mail_sender_handoff_judgment.md`
  - `../../../observations/2026-06-12_judgment_csharp_error_policy_extraction_authoring.md`

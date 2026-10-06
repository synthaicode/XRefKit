---
schema_version: 1
skill_id: crosspost_release
xid: B7D2A9F4C160
summary: prepare a reviewed article for per-channel publication with adaptation notes, release blockers, and human sign-off
applies_when:
- intake, drafting, and both reviews are complete enough that a release package or crosspost plan is needed
exclusions:
- release packaging is not publication approval
- unresolved blockers must not be erased during channel adaptation
inputs:
- latest draft, review results, target channels, and optional publication metadata
outputs:
- release package under `work/editorial_ops/` by default, plus channel adaptation notes, unresolved blockers, and final publish checklist
criteria:
- id: review_evidence
  statement: The release package preserves the latest draft and both review results.
  verification: Check the package against the supplied draft and review outputs.
- id: channel_boundary
  statement: Channel adaptations preserve core meaning and state channel-specific changes.
  verification: Inspect each channel note for explicit adaptation rationale.
- id: approval_boundary
  statement: Unresolved blockers and final human publication approval remain explicit.
  verification: Check the final checklist and sign-off handoff.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: editorial_framework
  query: editorial operations framework for release and publication boundaries
  required_when: Required for every crosspost release unless applicability is explicitly recorded.
  seed_xids:
  - F9E58E2BAD21
control_refs: []
aliases:
- A3FD70D101B7
- E2E73BDF143A
---
<!-- xid: B7D2A9F4C160 -->
<a id="xid-B7D2A9F4C160"></a>

# Skill: crosspost_release

## Purpose
Prepare a reviewed article for channel-specific release without collapsing review findings, unresolved blockers, and final human sign-off into one step.

## Method
1. Confirm the latest draft, fact review, reader-experience review, target channels, and metadata needs.
2. Resolve the editorial framework Knowledge and preserve its selected XID.
3. Read unresolved items from both reviews.
4. Prepare per-channel adaptation notes without changing core meaning.
5. Build the final checklist with blockers and owner-visible confirmations.
6. Write the release package to `work/editorial_ops/` with a date-prefixed filename unless another path is supplied.

## Monitoring, stop, and handoff
- Do not treat packaging as approval or remove factual blockers because a channel is less strict.
- Stop when unresolved factual blockers are being reclassified as acceptable without owner approval.
- Return the release path, blockers, and final sign-off handoff; publication requires explicit human approval.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: crosspost_release

## Purpose

Prepare a reviewed article for channel-specific release without collapsing
review findings, unresolved blockers, and final human sign-off into one step.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- latest draft
- fact-review result
- reader-experience review result
- target channels

## Outputs

- release package path
- channel adaptation notes
- unresolved blockers
- final checklist

## Startup

- Confirm the latest draft and both reviews exist.
- Confirm the target channels and any known metadata needs.
- Confirm whether the task is packaging only or includes publish execution.

## Execution

1. Read the unresolved items from both reviews.
2. Prepare per-channel adaptation notes without changing core meaning.
3. Build the final checklist with blockers and owner-visible confirmations.
4. Write the release package to the output path and return it.

## Monitoring and Control

- Do not treat packaging as approval.
- Do not remove factual blockers because a channel is less strict.
- Keep final human sign-off explicit.

## Closure

- Return the release package path.
- Return the unresolved blockers.
- Return the final sign-off handoff.

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

- summary: prepare a reviewed article for per-channel publication with explicit adaptation notes, release blockers, and final human sign-off boundary

- use_when: intake, drafting, and both reviews are complete enough that a release package or crosspost plan is needed

- input: latest draft, review results, target channels, and optional publication metadata

- output: release package under `work/editorial_ops/` by default, plus channel adaptation notes, unresolved blockers, and final publish checklist

- constraints: do not treat release packaging as publication approval; do not erase unresolved blockers during channel adaptation; preserve a human final sign-off boundary; write the release result to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm the latest draft and both review outputs exist and identify the target channels
  - planning: determine what adaptation each channel needs and which blockers still prevent release
  - execution: prepare the release package, channel notes, and final checklist
  - monitoring_and_control: stop if unresolved factual blockers are being reclassified as acceptable without owner approval
  - closure: return the release path, unresolved blockers, and the final human sign-off handoff

- tags: `editorial`, `release`, `crosspost`, `publishing`

- knowledge_slots:
  - name=editorial_framework; bind=F9E58E2BAD21

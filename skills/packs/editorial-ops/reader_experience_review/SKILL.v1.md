---
schema_version: 1
skill_id: reader_experience_review
xid: E1C7A5D9B430
summary: review a draft from the target reader perspective to surface confusion, drop-off points, context gaps, and pacing issues
applies_when:
- a draft exists and the team needs reader-side feedback before release or before final restructuring
exclusions:
- Publication approval remains with the human requester
- Unsupported claims or audience assumptions remain unresolved rather than being silently completed
inputs:
- article draft, intake record, target audience definition, reader capability assumption, and optional channel-specific reading assumptions
outputs:
- reader-experience review under `work/editorial_ops/` by default, plus friction points, capability-mismatch findings, likely reader questions, and revision priorities
criteria:
- id: evidence_and_audience_boundary
  statement: Claims, evidence, reader assumptions, and unresolved support remain explicitly separated
  verification: Inspect the result for traceable evidence and explicit unknowns
- id: human_publication_authority
  statement: The Skill does not approve publication or convert review feedback into factual approval
  verification: Check the handoff and publication boundary before closure
- id: output_closure
  statement: The declared editorial result exists and the next handoff is stated
  verification: Check the output path, open items, and handoff
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: editorial_operations_framework
  query: editorial operations framework
  required_when: Required when applying this Skill's editorial or reader evaluation criteria
  seed_xids:
  - F9E58E2BAD21
- id: reader_capability_model
  query: reader capability model
  required_when: Required when applying this Skill's editorial or reader evaluation criteria
  seed_xids:
  - 125B6C5E3630
control_refs: []
aliases:
- D84028E6F515
- 79372C67DBA0
---
<!-- xid: E1C7A5D9B430 -->
<a id="xid-E1C7A5D9B430"></a>

# Skill: reader_experience_review

## Purpose

Review a draft from the declared reader perspective so confusion, missing
context, and likely drop-off points are visible before release.

## Inputs

- article draft
- intake record
- target reader definition
- reader capability assumption
- optional channel assumptions

## Outputs

- reader-experience review path
- friction points
- capability-mismatch findings
- revision priorities

## Startup

- Confirm the draft and intake record exist.
- Confirm the intended reader, reading context, and assumed prior knowledge.
- Confirm whether the review is for restructuring, tone adjustment, or release gating.

## Execution

1. Walk the article in reader order.
2. Compare each major jump in the article to the assumed reader capability.
3. Note where a reader would likely pause, doubt, or leave.
4. Separate comprehension issues from factual issues.
5. Flag capability mismatches such as:
   - unexplained low-level concept jumps
   - missing component-role clarification
   - abstraction leaps beyond the assumed tolerance
6. Rank the friction points by likely reader impact.
7. Write the review result to the output path and return it.

## Monitoring and Control

- Do not present empathy-based feedback as factual validation.
- Do not default to generic style preference when reader context is unclear.
- Do not infer clarity without stating what the reader already knows.
- Keep missing audience evidence explicit.

## Closure

- Return the review path.
- Return the top friction points.
- Return the author revision handoff.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: reader_experience_review

## Purpose

Review a draft from the declared reader perspective so confusion, missing
context, and likely drop-off points are visible before release.

## Required Knowledge (XID)

- [Editorial operations framework](../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Reader capability model](../../../../knowledge/packs/editorial-ops/120_reader_capability_model.md#xid-125B6C5E3630)
- [Context direction guard rules](../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Inputs

- article draft
- intake record
- target reader definition
- reader capability assumption
- optional channel assumptions

## Outputs

- reader-experience review path
- friction points
- capability-mismatch findings
- revision priorities

## Startup

- Confirm the draft and intake record exist.
- Confirm the intended reader, reading context, and assumed prior knowledge.
- Confirm whether the review is for restructuring, tone adjustment, or release gating.

## Execution

1. Walk the article in reader order.
2. Compare each major jump in the article to the assumed reader capability.
3. Note where a reader would likely pause, doubt, or leave.
4. Separate comprehension issues from factual issues.
5. Flag capability mismatches such as:
   - unexplained low-level concept jumps
   - missing component-role clarification
   - abstraction leaps beyond the assumed tolerance
6. Rank the friction points by likely reader impact.
7. Write the review result to the output path and return it.

## Monitoring and Control

- Do not present empathy-based feedback as factual validation.
- Do not default to generic style preference when reader context is unclear.
- Do not infer clarity without stating what the reader already knows.
- Keep missing audience evidence explicit.

## Closure

- Return the review path.
- Return the top friction points.
- Return the author revision handoff.

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

- summary: review a draft from the target reader perspective to surface confusion, drop-off points, context gaps, and pacing issues

- use_when: a draft exists and the team needs reader-side feedback before release or before final restructuring

- input: article draft, intake record, target audience definition, reader capability assumption, and optional channel-specific reading assumptions

- output: reader-experience review under `work/editorial_ops/` by default, plus friction points, capability-mismatch findings, likely reader questions, and revision priorities

- constraints: review from the declared reader perspective rather than generic style taste; evaluate omission and pacing against the declared reader capability assumption; keep missing audience evidence explicit; do not convert reader feedback into factual approval; write the review result to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path

- lifecycle:
  - startup: confirm the draft, intake record, target reader definition, and reader capability assumption exist
  - planning: define the likely reader path through the article and where friction is most likely to occur given the assumed prior knowledge
  - execution: review the draft from that perspective and write the experience review result
  - monitoring_and_control: downgrade unsupported audience or capability assumptions to open questions and stop if the task tries to approve factual claims from empathy alone
  - closure: return the review path, top friction points, and the author revision handoff

- tags: `editorial`, `review`, `reader`, `ux`

- knowledge_slots:
  - name=editorial_operations_framework; bind=F9E58E2BAD21
  - name=reader_capability_model; bind=125B6C5E3630

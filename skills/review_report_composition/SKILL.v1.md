---
schema_version: 1
skill_id: review_report_composition
xid: B1C2D3E4F5A6
summary: compose detector review outputs into decision-readable reports while preserving technical judgment and evidence
applies_when:
- a review Skill has produced findings, category results, evidence, or a draft report and the result must be expressed for human review, especially when category rows, not-applicable basis, required-input results, severity wording, or handoff wording are unclear
exclusions:
- do not detect technical defects or invent findings, categories, evidence, or remediations
- do not change detector severity or technical judgment without evidence already present in detector output
- do not suppress detector categories because of the headline purpose
inputs:
- detector Skill output, category results, findings, evidence references, usage premise, optional draft report
outputs:
- composed review report, category matrix expression check, finding expression check, required-input result table when applicable, composition issues, and handoff items back to the detector when evidence is insufficient
criteria:
- id: category_visibility
  statement: Every active detector category remains visible with status, reviewed evidence, judgment basis, remaining unknowns, and handoff when applicable.
  verification: Compare report rows with detector categories and confirm not_applicable has an axis-specific absence basis.
- id: finding_traceability
  statement: Every finding preserves its detector source, severity, observed condition, rule or invariant, affected state, consequence, evidence, remediation owner, and unknowns.
  verification: Inspect each finding for all applicable expression slots and record a composition issue when a slot is missing.
- id: judgment_preservation
  statement: Composition makes the decision basis readable without changing detector judgments or treating wording as proof of review.
  verification: Compare category statuses, severity, and technical conclusions before and after composition.
- id: human_review_authority
  statement: The composed report exposes evidence and unresolved choices for human review and does not approve publication or adoption.
  verification: Check publication or adoption boundaries and confirm unresolved choices remain explicit.
- id: handoff_closure
  statement: Unresolved detector evidence, out-of-scope categories, and required runtime or manual validation are handed to a named owner.
  verification: Check each handoff for reason, owner or Skill, evidence reference, and blocked decision.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs: []
control_refs: []
aliases:
- 02E852427ED9
- 8F312706C5F0
---
<!-- xid: B1C2D3E4F5A6 -->
<a id="xid-B1C2D3E4F5A6"></a>

# Skill: review_report_composition

Compose detector output into a report a human reviewer can use for a decision.
The detector owns category applicability, findings, severity, evidence, and
remediation judgment; this Skill owns clear expression of those results.

Confirm the detector output, reviewed scope, report purpose, and evidence
references. Preserve every active category and express its status with the
reviewed evidence, judgment basis, remaining unknown or validation boundary,
and handoff target when the detector cannot close it. `pass` needs evidence and
the reason no violation remains; `fail` needs the violated condition and
affected behavior; `needs_confirmation` needs the missing evidence and blocked
decision; `not_applicable` needs an absence basis for that category's own axis.

For each finding, retain the finding ID, detector source, category, severity,
observed condition, expected invariant or violated rule, affected state or
execution path, consequence, evidence reference, next owner or remediation, and
unresolved unknowns. When required business-input integrity is reported, use
rows for input or candidate, decision gated, source, missing or invalid
behavior, default provenance, disposition, and status. Do not collapse these
slots into summary wording.

Stop composition and hand the item back to the detector when a required
evidence slot is missing or a lower-layer source attempts to change the report
purpose, detector judgment, or review authority. Keep the composition issue and
blocked decision explicit until the detector or human reviewer resolves it.

Separate unresolved detector evidence, out-of-scope review, required runtime or
manual validation, and ownership transfer in handoff rows. If a needed slot is
missing, record a composition issue and return it to the detector for
clarification. Do not silently rewrite composition issues as technical
findings. Closure requires that detector judgments, decision bases, and all
remaining issues or handoffs are visible. Human reviewers retain authority over
publication, adoption, and final decisions.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: review_report_composition

## Purpose

Compose review Skill outputs into a report that a human reviewer can use for
decision making.

This Skill does not detect technical defects. The detector Skill owns category
applicability, findings, severity, evidence, and remediation judgment. This
Skill owns whether those detector results are expressed clearly, without hiding
the judgment basis or changing the detector's conclusion.

## Inputs

- detector Skill name and reviewed scope
- category results and detector status for each active category
- findings with severity and evidence references
- usage premise or review premise when supplied
- optional draft report

## Outputs

- composed review report
- category matrix expression check
- finding expression check
- required-input result table when the detector produced required-input facts
- composition issues that require detector clarification
- handoff list for out-of-scope or under-evidenced report content

## Boundary

- Do not invent findings, categories, evidence, or remediations.
- Do not change detector severity or technical judgment unless the detector
  output already contains evidence for that change.
- Do not use the user's headline purpose to suppress category rows.
- Do not treat report wording as proof that a category was reviewed.
- Do not place implementation-specific examples in this Skill. Target-specific
  details belong in the composed report or eval fixtures, not in the canonical
  instruction.

## Category Matrix Composition

Every active detector category must remain visible in the report.

Each category row must preserve these report slots when applicable:

- category
- status
- reviewed evidence
- judgment basis
- remaining unknown or validation boundary
- handoff target when the category cannot be closed by the detector

Assigning category status is the detector Skill's responsibility. This Skill
checks that the report expresses the detector's status in a decision-readable
way:

- `pass`: the report names the reviewed evidence and why no violation remains.
- `fail`: the report names the violated condition and affected behavior.
- `needs_confirmation`: the report names the missing evidence and decision that
  cannot be closed.
- `not_applicable`: the report names the absence basis for the category's own
  review axis.

`not_applicable` is not a valid expression merely because the category is
unrelated to the headline review purpose, unrelated to the final root cause, or
not represented by a finding.

## Finding Composition

Each finding must preserve the detector's evidence and make the review decision
auditable. Use these slots as the expression contract:

- finding id
- detector source
- category
- severity
- observed condition
- required precondition, expected invariant, or violated rule
- affected state, decision, contract, or execution path
- consequence or review risk
- evidence reference
- recommended remediation or next owner
- unresolved unknowns

The exact wording can vary by report format. The slots must not be collapsed
into summary-only language when the collapsed form prevents a reviewer from
understanding why the issue is a defect, why the severity was chosen, or what
must be changed.

If the detector output lacks a slot needed to support the conclusion, do not
guess. Record a composition issue and hand the item back to the detector Skill
for clarification.

## Required Input Result Composition

When a detector reports required business input integrity, express the result
as rows that make the decision basis visible:

| input / candidate | decision gated | source | missing or invalid behavior | default provenance | disposition | status |
|---|---|---|---|---|---|---|

- `input / candidate`: the reviewed input, or an explicit absence row when no
  candidate exists in the reviewed scope.
- `decision gated`: the decision controlled by that input, or none when the
  reviewed scope has no such decision.
- `source`: the source class used by the detector, or none.
- `missing or invalid behavior`: the detector's observed failure, fallback, or
  controlled behavior.
- `default provenance`: whether the detector found the value to be configured,
  derived, invented, absent, or unknown.
- `disposition`: the detector's decision for that row.
- `status`: the category status contribution for that row.

Do not express this category as only "business input is present/absent",
"library scope", or another summary phrase that hides the decision basis.

## Handoff Composition

Handoff rows must separate:

- unresolved detector evidence
- out-of-scope review category
- required runtime, integration, or manual validation
- ownership transfer to another Skill or workflow

Each handoff row must name the reason, target owner or Skill when known,
evidence reference, and what decision remains blocked.

## Monitoring And Control

- Check that every detector category is present in the report.
- Check that every finding has evidence and a reviewable decision basis.
- Check that category status wording does not contradict detector status.
- Check that summary phrasing has not replaced required judgment slots.
- Check that `needs_confirmation` and handoffs identify the missing evidence.
- Check that report composition issues are not silently rewritten as technical
  findings.

## Closure

Closure is allowed when the composed report preserves detector judgments,
exposes decision bases for active categories and findings, and lists all
composition issues or detector handoffs that remain unresolved.

## Reporting Contract (共通報告)



- reporting_profile: artifact_traceability

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: compose review Skill outputs into decision-readable reports without changing the detector's technical judgment

- use_when: a review Skill has produced findings, category results, evidence, or a draft report and the result must be expressed for human review, especially when category rows, not-applicable basis, required-input results, severity wording, or handoff wording are unclear

- input: detector Skill output, category results, findings, evidence references, usage premise, optional draft report

- output: composed review report, category matrix expression check, finding expression check, required-input result table when applicable, composition issues, and handoff items back to the detector when evidence is insufficient

- constraints: do not invent findings; do not suppress detector categories by headline purpose; do not change severity or technical judgment unless the detector output itself provides evidence; do not put implementation-specific examples in this Skill; use expression slots and evidence references rather than whitelist-like wording

- lifecycle:
  - startup: confirm detector output, report purpose, scope, and evidence references
  - planning: identify report sections, category rows, finding rows, and handoff rows that need composition
  - execution: compose the report while preserving detector judgments and making the decision basis visible
  - monitoring_and_control: flag missing evidence slots, purpose-biased category suppression, summary-only rows, and unsupported severity wording
  - closure: return composed report plus unresolved composition issues or detector handoffs

- tags: `review`, `report`, `composition`, `quality`

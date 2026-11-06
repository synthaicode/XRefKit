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
- id: overall_operational_assessment
  statement: The report begins with an overall operational assessment, followed by its conditions, evidence and limits, before individual findings; the assessment explains which supported operational guarantees may fail and why that matters to severity judgment.
  verification: An independent quality reviewer compares every overall claim with identified detector findings and evidence, checks the required order, and rejects count-only summaries, unsupported common causes, and unverified impacts stated as observed results.
- id: content_first_and_technical_fidelity
  statement: The opening explains the concrete operational behavior or change before finding identifiers, and readable wording preserves the technical object, ownership, scope and evidence strength.
  verification: An independent quality reviewer reads the opening without following IDs, then compares it with detector evidence to reject identifier-only introductions or substitutions that broaden or change the technical claim.
- id: decision_separation_and_impact_order
  statement: Confirmed defects are ordered by evidenced operational impact, while unresolved design-policy decisions are presented separately with required choices, option-dependent impacts and missing evidence.
  verification: An independent quality reviewer checks defect ordering against supported impact and detector severity, checks explicit ties or incomparability, and rejects undecided policy presented as a confirmed defect.
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

Start the composed report with the overall operational assessment required by
Overall Assessment Composition below, then its conditions, evidence and limits,
then individual findings, followed by a separate design-policy decision section.
This report-specific order applies to the composed artifact; execution status
reporting does not replace the operational assessment.

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

## Overall Assessment Composition

Before individual findings, explain the concrete operational problem or change
and what the reviewed system can or cannot be relied on to preserve under the
evidenced conditions, including the resulting operational implications. Lead
with that meaning, not finding identifiers; IDs serve as supporting references
beside the explanation. A reader must be able to understand the opening without
looking up those IDs. For a fix report, distinguish the scoped correction from
remaining issues rather than implying that the whole system is now safe. Give the reader enough context to judge severity
across the report without reconstructing it from the finding list. A finding
count, severity tally, or shortened list of defects alone is insufficient.

Use this order: overall operational assessment; conditions, evidence and limits
supporting that assessment; then individual findings. The assessment may contain several distinct
operational concerns; it need not claim a shared cause or a single failure chain.

For every overall claim, identify the supporting finding IDs and evidence.
Keep its triggering conditions and reviewed scope beside it. Explain the
connection between the observed behavior, the affected operational guarantee,
and the potential consequence while preserving detector severity and judgment.
Distinguish observed results from inferred or possible impacts and unverified
questions. Do not invent business losses, occurrence frequency, shared causes,
or recovery guarantees. Preserve the reviewed version/time boundary; historical
findings do not establish that the current implementation remains defective.

When evidence cannot support an overall operational implication, state that
limit and return the missing premise or evidence to the detector with the
blocked decision. Do not manufacture an impact merely to fill the opening.

Simplify wording without changing the technical object, actor, ownership,
condition or evidence strength. Explain unfamiliar terms when needed while
retaining distinctions that determine the claim. Do not replace a specific
resource-lifetime or ownership failure with a broader connection, delivery or
service-failure claim unless the evidence supports that broader meaning.

## Defect Order And Design-Policy Decisions

Present confirmed defects in descending operational impact, using the
supported affected guarantee, scope, consequence and recovery limits. Preserve
the detector's severity and explain the evidence supporting the order; do not
silently regrade findings. Where impacts tie or cannot be compared on the
available evidence, state that limit and use a stable finding-ID order within
the tied or incomparable group. Unknown occurrence frequency remains unknown
and must not become an invented probability used to rank defects.

Give items requiring a design-policy decision their own section, separate from
confirmed defects. Name the decision needed, the known alternatives and their
conditional operational implications, missing premises or evidence, and the
decision owner or handoff when known. Support option-dependent impacts with
available evidence or mark them unknown. When no such decision is required,
state none rather than inventing an item. Do not invent alternatives or select a
policy merely to complete the report. If alternatives are not established,
state what the owner must clarify. An undecided expected behavior is not a
confirmed violation. When a confirmed defect also requires a policy choice for
remediation, retain the evidenced defect in the defect list and cross-reference
the separate decision item without weakening the finding or pretending that
the policy has been decided.

## Independent Report Acceptance

The independent quality reviewer owns acceptance of the composed report's
content under the existing quality phase. The composer may self-check these
conditions but must not certify its own acceptance; deterministic workflow
verification does not establish them.

- The opening explains the overall operational implications before individual
  findings, followed by the applicable conditions, evidence and limits. It is
  not merely a count, severity tally, or compressed finding list.
- The opening conveys the concrete behavior/change and operational meaning
  before IDs; identifiers only support that explanation. Readability changes
  preserve the technical object, ownership, conditions, scope and strength of
  the evidence rather than substituting a broader or different claim.
- Every overall claim is traceable to identified detector findings and evidence;
  the claim, conditions, severity and scope are consistent with those details.
- Observed results, possible impacts and unverified matters remain distinct,
  including recovery/retry boundaries and the reviewed version/time boundary
  when applicable. Unsupported business damage, frequency or shared causes
  are absent.
- Confirmed defects are ordered by evidenced operational impact without
  changing detector severity. Ties, incomparable impacts and unknown frequency
  are explicit; unsupported probability or business loss does not drive order.
- Design-policy decisions have a separate section identifying the required
  decision, known alternatives and conditional impacts, missing basis and
  owner/handoff. Unsettled policy is not labeled a confirmed defect; confirmed
  defects needing a remediation choice cross-reference the separate item.
- Category coverage and per-finding expression slots remain intact. Missing
  support is a composition issue with an explicit detector/human handoff,
  rather than a new technical finding or an asserted impact.

Record each applicable acceptance result and its evidence through the existing
quality gate. A missing or failed review remains explicit; do not represent
report composition as quality-accepted until the independent checks pass.

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
exposes the overall operational assessment and its supporting conditions,
evidence and limits before individual findings, preserves decision bases for
active categories and findings, and lists all composition issues or detector
handoffs that remain unresolved. Content acceptance requires the independent
report acceptance checks above; procedural closure alone is not acceptance.

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

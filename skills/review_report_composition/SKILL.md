<!-- xid: 02E852427ED9 -->
<a id="xid-02E852427ED9"></a>

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

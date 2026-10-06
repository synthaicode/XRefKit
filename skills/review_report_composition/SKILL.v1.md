---
schema_version: 1
skill_id: review_report_composition
xid: B1C2D3E4F5A6
aliases: [02E852427ED9, 8F312706C5F0]
summary: compose detector review outputs into decision-readable reports while preserving technical judgment and evidence
applies_when:
  - a review Skill has produced findings, category results, evidence, or a draft report for human review
  - category applicability, not-applicable basis, required-input results, severity wording, or handoff wording needs composition
exclusions:
  - do not detect technical defects or invent findings, categories, evidence, or remediations
  - do not change detector severity or technical judgment without evidence already present in detector output
  - do not suppress detector categories because of the headline purpose
inputs:
  - detector Skill name and reviewed scope
  - category results and detector status for each active category
  - findings with severity and evidence references
  - usage or review premise and optional draft report
outputs:
  - composed review report with category and finding expression checks
  - required-input result table when applicable
  - composition issues and detector handoff items
knowledge_needs: []
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
control_refs: []
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

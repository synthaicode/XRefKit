<!-- xid: B4F1C8D2A605 -->
<a id="xid-B4F1C8D2A605"></a>

# Brownfield reporting and closure

Separate human-facing output into an overview and detailed evidence. The
overview states objective, policy, investigation scope, impacted areas, result
classification, residual risk, and required decisions. Detail contains service
structure, change/impact map, data investigation, test mapping, pre/post
results, logs, and unresolved paths.

Build the opening overview around the requested change: connect its objective,
confirmed existing-system conditions, investigation scope and current result
into an overall explanation. Include the premises that qualify the result in
that explanation rather than leaving the reader to assemble them from separate
fields. Make clear what the evidence establishes and what remains unknown or
requires a human decision.

Use that overview to explain the detailed evidence: relate each affected area,
change/impact path, test result and unresolved item to the requested change and
the conclusion it supports or limits. Select explanatory detail for this change
while retaining required traceability and coverage. Preserve actors, causal
relationships, constraints, exceptions and evidence when shortening; do not
supply missing premises by inference presented as fact.

Before drafting, inventory the explicit conditions in the original source
sections governing the chosen decision: current mechanisms, scope, exceptions,
existing or planned capabilities, dependencies and review corrections. Give
each distinct condition its own ID, source location and current/planned/proposed
status; one future item does not cover another. Map every inventory item to
`reflected`, `not_applicable` with a reason, or `unknown_relevance`. Unknown
relevance cannot support an unconditional conclusion. Recheck the inventory
against the original source, not an inventory reconstructed from the draft.
The record may be a sidecar; decision-changing conditions and their effect must
also appear in prose beside the affected decision, without a new visible template.

Before shortening, map proposed changes and the way forward to the source
conditions that justify or limit them. Distinguish the existing system from
planned changes and proposals, and retain scope, exceptions, dependencies and
review corrections that could change what to do or when. Check the source back
against the draft for omitted decision-changing conditions; integrate each
condition's effect into the affected requirement, confirmation or next step.
Keep uncertain relevance explicit without inventing an effect. Supporting
coverage notes do not replace this explanation or add a mandatory report section.

Before delivery, check that the overview and details together explain the
whole change and its judgment basis without requiring the reader to reconstruct
their relationship. Preserve the phase output structure and closure obligations
below; this guidance adds no approval or maturity claim.

Every phase presents `要求事項`, `確認事項`, and `進め方` in that order, as
explicitly requested for this workflow. Preserve status/result, evidence, open
items and handoff within these sections; do not weaken shared closure rules.
Each item links change reasons, requirement XIDs, Evidence and judgment/approval
records. Apply [understanding changes](understanding-change.md#xid-84C9D6A1E730)
when technical findings change scope or the way forward. Before closure, trace every in-scope upstream item, attach evidence
and Knowledge/pattern basis, give every unknown a reason, impact, next action,
and owner, and record the next-phase input package.

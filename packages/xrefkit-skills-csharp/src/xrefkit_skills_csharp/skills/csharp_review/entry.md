# C# Review Entry

Review C# code for language-dependent defects and system-level implementation
risks beyond compiler or Roslyn diagnostics.

This Skill produces findings, evidence, unknowns, used XIDs, handoff items, and
a human-readable review_report expressing those same results. The reporting requirements below govern this Skill's own report; it does not add
cross-detector composition or out-of-scope technical review responsibility.

Do not treat compiler-detectable issues as the primary review value.
Do not infer runtime behavior without source evidence.
Do not silently absorb security, XDDP trace, or design-assumption findings;
record them as handoffs.

Return review_report as a nonempty string alongside findings, evidence, unknowns,
used_xids and handoffs under xid-schema-csharp-review. Independent report-content
acceptance uses xid-axis-csharp-operational-report; the entry below states the
checks so ordinary entry delivery does not rely on optional fragment loading.

## Evidence-driven analogous-path check


After a finding is supported by source or runtime evidence, state its violated
condition and the execution structure that made it possible. Use the active
review criteria to identify role-equivalent paths inside the declared scope;
textual resemblance alone does not establish a common defect.

Record a bounded inventory linking the finding to candidate paths and their
owners or boundaries. Inspect each candidate under its own preconditions and
record whether it is an additional manifestation, an existing finding, a
non-match, not yet verified, or an out-of-scope handoff. Preserve evidence and
negative results; do not count the same finding twice or claim a new root cause
merely because another location fails.

When runtime evidence is needed, choose a representative candidate and a
control that distinguishes the suspected mechanism from ordinary failure.
Record the exact intervention, observable state or outcome, and what the test
does not establish. A successful representative test does not verify every
candidate in the inventory.

Before reporting coverage complete, give each inventoried path an evidence-backed
disposition or explicit unverified boundary and next owner. Keep this check
within the declared scope and existing Skill exclusions; proposed scope
expansion remains a handoff rather than an unbounded search.

## Operational Report Required

Produce review_report as the human-readable expression of this detector's own
findings, evidence, unknowns and handoffs. Keep those structured outputs intact.
This requirement does not invoke or adopt the repository draft
review_report_composition Skill. Cross-detector composition and unsupported
technical claims remain handoffs to the appropriate owner.

### Generation

1. Begin with the overall operational assessment: explain the concrete behavior
   or scoped change and what cannot be relied on under the evidenced conditions.
   Put the meaning before finding IDs; IDs are supporting references. A count,
   severity tally or shortened finding list does not explain overall impact.
2. Follow with the conditions, reviewed revision/scope, evidence and limits
   supporting that assessment, then the individual findings. Link every overall
   claim to the relevant finding IDs and evidence. Separate observed results,
   source-backed implications, possible impacts and unverified matters. Historical
   results do not establish current defects; a scoped correction does not prove
   whole-system safety. If no supported operational implication can be stated,
   say why and name the missing premise instead of inventing an impact.
3. Order confirmed defects by evidenced operational impact while preserving
   detector severity. Explain the order from affected guarantees, scope,
   consequence and recovery limits. State ties or incomparable impacts and use
   stable finding-ID order within those groups. Unknown frequency stays unknown.
4. Present design-policy decisions separately from confirmed defects. Identify
   the required decision, known alternatives and evidence-supported conditional
   consequences, missing premises/evidence, and owner or handoff. Mark unknown
   owners or impacts explicitly. Do not invent options or adopt a policy. State
   none when no decision is required. A confirmed defect requiring a remediation
   choice stays a defect and cross-references the separate decision item.
5. Preserve technical objects, actors, ownership, conditions and evidence
   strength when simplifying language. Do not broaden an ownership/lifetime
   defect into connection exhaustion, delivery failure or service failure
   without evidence. Do not invent business damage, occurrence frequency,
   common causes, recovery guarantees, findings or technical severity changes.
6. Retain every applicable category, finding evidence, unknown, validation limit
   and handoff. Explain missing report support as a reporting issue, not a new
   defect. Required-input facts and clean/not-applicable category bases must not
   disappear from the readable report when present in detector output.

### Independent acceptance

The existing independent quality reviewer applies
xid-axis-csharp-operational-report to the produced report and its structured
inputs, records each check result with evidence, and returns missing or failed
content checks for correction. The producer may self-check but cannot certify
its own content acceptance. Schema validation and deterministic workflow
verification do not judge report meaning. If independent review is unavailable,
record it as not performed with the owner/handoff; do not claim quality acceptance.

The required acceptance checks are included here for entry-only MCP delivery.
They match xid-axis-csharp-operational-report in the package registry; failure
to retrieve that separate asset does not remove these checks.

- `operational_assessment_first`: The opening explains concrete operational meaning before IDs, followed by conditions, evidence and limits before individual findings; counts or short finding lists alone fail.
- `overall_evidence_consistency`: Every overall claim links to detector findings/evidence and preserves observed, inferred, possible and unverified boundaries, reviewed revision and scoped fixes.
- `technical_meaning_preserved`: Wording retains technical object, actor, ownership, conditions and evidence strength without unsupported broader guarantees, business damage, frequency or common causes.
- `impact_order_preserves_judgment`: Confirmed defects follow evidenced operational impact without severity regrading; ties/incomparability use stated stable order and unknown frequency is not invented.
- `design_decisions_separate`: Unsettled policy stays separate with needed decision, known choices, supported conditional consequences, missing basis and owner/handoff; actual defects needing a choice cross-reference that item.
- `detector_coverage_preserved`: Applicable category results, finding evidence, unknowns and handoffs remain visible; ordinary reporting does not absorb cross-detector, security, XDDP or design review.
- `independent_acceptance_recorded`: A reviewer independent of the producer records content results with evidence; schema/progression checks are not content acceptance and unavailable review is explicit.

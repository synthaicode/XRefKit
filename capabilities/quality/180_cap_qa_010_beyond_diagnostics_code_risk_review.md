<!-- xid: 4A3CA9ECFA71 -->
<a id="xid-4A3CA9ECFA71"></a>

# Capability: CAP-QA-010 Beyond-Diagnostics Code Risk Review

## Definition

- capability_id: `CAP-QA-010`
- capability_name: `beyond_diagnostics_code_risk_review`
- work_type: `judgment`
- summary: review code for risks that compiler and static-analyzer diagnostics do not detect, producing evidence-based findings without applying fixes

## Preconditions

- target code exists and its repository or project boundary is established
- a diagnostics baseline is collectable, or its absence is explicitly recorded as `baseline_unavailable`

## Trigger

- a review request targets risk domains beyond compiler/analyzer diagnostics

## Inputs

- target path (repository, solution, project, or file subset)
- optional scope filters
- diagnostics baseline (build or analyzer output)

## Outputs

- findings with severity (`critical`, `major`, `minor`, `needs_confirmation`), evidence path, violated condition, and remediation
- per-category summaries with explicit empty results for clean categories
- handoff list for out-of-scope discoveries (security scope, design assumptions)

## Review Domains

- synchronization and concurrency correctness, including waits that rely on
  time advancement alone when a producer-side state change could notify the
  waiter
- resource lifetime, ownership, and efficiency
- error handling and exception path integrity
- support lifecycle status of frameworks and dependencies
- time and culture correctness
- attribute or configuration preconditions not enforced by diagnostics

## Required Domain Knowledge

- language-specific review criteria, for C#:
  - [C# review spec](../../knowledge/csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA)
- [Common source analysis criteria](../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)

## Constraints

- exclude issues the diagnostics baseline already detects
- every finding must cite concrete evidence; unverifiable results are `needs_confirmation` with the missing evidence named
- third-party API surface claims (member existence, signatures, implemented interfaces) must be verified against the actually referenced package version — by compile probe, resolved-assembly inspection, or version-exact documentation — before a remediation is stated as actionable; unverified claims stay `needs_confirmation`
- support lifecycle claims must cite the official source URL checked
- findings only: do not apply fixes inside this capability
- do not expand into security review or design-assumption derivation; route those to the handoff list

## Assignment

- quality review step
- [Quality Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)
- implemented for C# by `skills/csharp_review/`

## Notes

- CAP-QA-001 covers conformance to specification and coding rules; this
  capability covers risk domains that no diagnostic or specification check
  expresses. Attribute-oriented checks can be deepened through `CAP-QA-005`.
- Observed basis: csharp_review runs on 2026-06-12, including one refuted
  remediation (F-002) caused by an unverified third-party API surface claim.

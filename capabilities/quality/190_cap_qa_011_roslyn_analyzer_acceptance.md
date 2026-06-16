<!-- xid: 94C1B7B9920A -->
<a id="xid-94C1B7B9920A"></a>

# Capability: CAP-QA-011 Roslyn Analyzer Acceptance

## Definition

- capability_id: `CAP-QA-011`
- capability_name: `roslyn_analyzer_acceptance`
- work_type: `judgment`
- summary: content-conditional quality-axis check that runs the Roslyn analyzer pipeline and dispositions its candidates as part of output acceptance, applied only when C# is in scope

## Preconditions

- the run is in its quality phase and the skill references this capability
- `tools/cs_scope_probe.py` reports `cs_in_scope` for the run's target or changed set
- a buildable .NET target exists, or its absence is recorded as `baseline_unavailable`

## Trigger

- a skill that references this capability reaches the quality phase and the per-run content probe reports C# in scope

## Inputs

- target path or changed-file set for the run
- collection profile or ruleset (`tools/profiles/error_policy_collection.editorconfig`)

## Outputs

- analyzer SARIF v2.1 from `tools/collect_analyzer_sarif.py`
- normalized 131 candidates from `tools/sarif_to_locator.py`
- a disposition of each candidate (accepted / refuted / `needs_confirmation`)
- a `check`-kind quality artifact set to `done` (accepted), `blocked` (a candidate fails acceptance), or `na` (C# not in scope)

## Required Domain Knowledge

- [Roslyn analyzer quality-check applicability](../../knowledge/source_analysis/150_roslyn_analyzer_quality_check_applicability.md#xid-A1B243BF7D5D)
- [External analyzer rule map](../../knowledge/source_analysis/132_csharp_error_policy_analyzer_rule_map.md#xid-C7A1E94D3B62)
- [Determinism tiers (locator extraction)](../../knowledge/source_analysis/131_csharp_error_policy_locator_tiers.md#xid-D1F4A7C3E209)

## Constraints

- applicability is content-conditional: the skill declares it *can* apply (by referencing this capability); the per-run `cs_scope_probe` decides whether it *does*. Do not run it uniformly
- not an auto-fail gate: analyzer hits are 131 candidates, never findings; a hit never fails closure on its own (see the external analyzer rule map)
- when C# is not in scope, set the quality check artifact to `na`; it must not gate closure
- when C# is in scope but no buildable target is available, record `baseline_unavailable` and continue; do not treat it as a pass or an auto-fail
- candidate disposition is the quality reviewer's judgment and must run separate from the executor context

## Assignment

- quality phase of a Skill run that references this capability and whose `model_tier` makes the quality gate mandatory
- engine: `tools/collect_analyzer_sarif.py` -> `tools/sarif_to_locator.py`; applicability engine: `tools/cs_scope_probe.py`

## Notes

- This capability is the worked example of a content-conditional, tool-type quality check item. It composes with, and does not replace, `CAP-QA-010` beyond-diagnostics review.

<!-- xid: CA1D6B8E420F -->
<a id="xid-CA1D6B8E420F"></a>

# Fixed-output authoring sample

The Skill owns the reusable method. Target-specific Knowledge owns format,
granularity, preserved exemplars, provenance, and input samples. Use
[Target Output Quality Profiles](../../../../knowledge/quality/130_target_output_quality_profiles.md#xid-D6A9F3B821C4)
and the [Fixed Output Quality Protocol](../../../../docs/core/contracts/112_fixed_output_quality_protocol.md#xid-F9C2A8D471B0).
Curate profiles with `knowledge_ontology_management`; correct generation wording
with `skill_flow_authoring` under explicit scope.

## Two targets, one method

[Example Target A](../../../../knowledge/quality/profiles/example_target_a/profile.md#xid-A7D2C9E461B0)
requires a compact decision-first report with three table columns.
[Example Target B](../../../../knowledge/quality/profiles/example_target_b/profile.md#xid-B8E3D0F572C1)
requires conditions/observations first, five columns, and fuller follow-up
reasoning. Both describe the hypothetical `example_report` Skill's
`acceptance_report` output. Their profiles and attachments live with Knowledge,
not inside this Skill's baseline folder.

Both are `example`, not actual approvals. They cannot qualify a model or
authorize production correction. Real authoring preserves actual acceptance
artifacts and source evidence, with owner-confirmed fixed features, permitted
variation, and subjective criteria. Never infer approval reasons from one example.

## Knowledge selection and per-run review

The parent extracts target/version cues, searches Knowledge metadata/XIDs, and
resolves applicable candidates. These concrete paths illustrate lookups; they
are not a required runtime folder. Package/MCP callers pass their own resolved
profile paths. Supply target revision whenever relevant and select an applicable
XID explicitly when ambiguous. Never infer applicability from last approval.

```powershell
python -m xrefkit skill reporting select --profile knowledge/quality/profiles/example_target_a/profile.md --profile knowledge/quality/profiles/example_target_b/profile.md --target example_target_a --target-revision example-1 --skill-id example_report --output-id acceptance_report --result work/selected-quality-profile.json
python -m xrefkit skill reporting check --profile knowledge/quality/profiles/example_target_a/profile.md --target example_target_a --target-revision example-1 --skill-id example_report --output-id acceptance_report --output knowledge/quality/profiles/example_target_a/assets/exemplar.txt --result work/report-format-check.json
```

The first selects one applicable profile. The second has no structural findings
but remains `needs_review`: acceptance is fictional and granularity still needs
independent review. Using Target B's exemplar for A yields `alarm`.
Missing/mismatched/ambiguous profiles remain explicit handoffs.

Attach selection and check results to existing reviewer hooks:

```powershell
python -m xrefkit skill artifact --log <run-log> --artifact QUALITY-PROFILE --kind source --target work/selected-quality-profile.json --status done --role <quality-reviewer>
python -m xrefkit skill artifact --log <run-log> --artifact CHECK-FORMAT --kind check --target work/report-format-check.json --status pending --role <quality-reviewer>
```

The reviewer sees selected Knowledge, provenance, input scope, and format/
granularity criteria. Format success alone never advances quality or closure.
Other document formats can use output-specific validators without imposing a
universal report shape. Per-run review is primary; qualification is optional.

## Portable approval and optional qualification

Each profile package contains relative approval evidence, exemplars, inputs,
and any additional resolved quality Knowledge attachments. Copying the intact
package preserves lookup and identity; original host absolute paths are not
required. Changes to applicability/profile/provenance/artifacts invalidate prior
qualification even when the Skill and model are unchanged.

For an actually approved profile, `assess`, `qualify`, `authorize`, and
`recalibrate` accept the same profile/target/Skill/output arguments.
Qualification includes target/profile revisions, so A approval does not approve
B for the same Skill/model. `--reevaluate` requests an explicit recheck.

Record actual model/provider/configuration and procedure/profile/input/output
hashes, independent contexts, and reviewer provenance. Collection JSON contains
`identity`, `producer`, and ordered `runs` (`input_hash`, `output_hash`,
`context_id`). Subjective review binds `baseline_hash`, ordered `output_hashes`,
`reviewer`, and all criterion `decisions`. Corrective method review additionally
binds `original_hash`, `candidate_hash`, independent `reviewer`, and `decision`.
CLI consistency checks do not attest actual execution or approval authenticity.

Keep profile criteria, approval evidence, exemplars, samples and Knowledge
immutable during wording correction. Explicit scoped user instruction, bounded
attempts, held-out isolation and independent method/output review remain required.
Repository-adopted candidates stay staged for coherent owner source/adoption
integration; no maturity promotion is performed.

`--contract <local.yaml>` remains supported as `legacy_local_manifest` mode. It
does not select target Knowledge and is not the destination for new target
criteria or exemplars.

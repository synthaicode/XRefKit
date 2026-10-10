<!-- xid: F9C2A8D471B0 -->
<a id="xid-F9C2A8D471B0"></a>

# Fixed Output Quality Protocol

This is an opt-in control for accepted fixed-format outputs: design documents,
test specifications, and reports. Code edits themselves are outside it; an
accompanying fixed-format report can be enrolled independently. No universal
report shape or quality score is introduced. Existing startup, review, and
closure obligations remain authoritative.

## Ownership and acceptance

- Common control owns assessment triggers, authority, and corrective adoption.
  Target-specific versioned Knowledge profiles own applicability, accepted
  format/granularity, exemplar provenance, and input samples. Individual Skill
  outputs reference applicable Knowledge instead of keeping their own copies.
- At acceptance, retain the actual approved output artifact, sample inputs,
  heading names/order, table columns/order, information placement, and required
  reporting granularity. An example alone does not define every fixed feature.
- Reusable and target-specific quality meaning and preserved exemplars belong
  to canonical Knowledge curated through
  `knowledge_ontology_management`; Skill output-specific criteria reference the
  required Knowledge. Generation method/prompt wording belongs to
  `skill_flow_authoring`. Restoring an existing definition does not require a
  Knowledge change; materially changing quality meaning does.
- A Knowledge profile uses the
  [Target Output Quality Profile](../../../knowledge/quality/130_target_output_quality_profiles.md#xid-D6A9F3B821C4)
  representation: XID/revision, target/revision, Skill/output applicability,
  approval evidence, relative exemplar/input attachments, criteria, sampling
  count, and additional quality Knowledge. Profile and attachment hashes are
  part of its identity; changes invalidate prior qualification. No new runtime
  fields or arbitrary baseline folders are copied into Skill headers. See the
  [Authoring sample](../../../skills/os/skill_flow_authoring/references/fixed_output_sample.md#xid-CA1D6B8E420F).
- Subjective quality remains independent review. Missing review is
  `needs_review`, never an inferred pass or fabricated numerical score.

## Per-run review and optional model qualification

The parent/reviewer identifies the target and relevant target version/context,
searches available Knowledge metadata through established Knowledge/XID routing,
and resolves applicable candidate XIDs. Pass resolved profiles to
`skill reporting select --profile ... --target ... --skill-id ... --output-id ...`.
The adapter does not scan a fixed folder, choose the last-used profile, or infer
the newest revision. Supply `--target-revision` whenever version matters;
omission is not proof that another version's approval applies. Missing,
mismatched, and ambiguous profiles yield `missing_profile`, `profile_mismatch`,
or `ambiguous_profile` for explicit review/handoff. `--profile-xid` must still
match target, Skill, output, and any specified target revision.

Per-run review can suffice. Give the independent quality reviewer the accepted
Knowledge profile, selection receipt, and preserved acceptance artifacts on
every applicable run. `example` and `proposed` profiles cannot establish real
acceptance, model qualification, or production corrective authority.
`skill reporting check` checks collected output and saves evidence with
`--result`; link that result through existing `skill artifact --kind check`.
A format pass does not establish content quality or advance quality/closure.
Existing reviewer roles and tier-dependent quality gates remain unchanged.

Optional model qualification records multiple passing combinations, keyed by
Skill/output identity, target/revision, profile XID/identity/revision, procedure
hash, full profile and approval/exemplar/input/Knowledge attachment hashes,
provider/exact snapshot, and inference parameters. Target A approval does not
approve Target B for the same Skill/model. Switching
between already-qualified models does not trigger reassessment merely because
the last execution used another model. Unknown identity is never assumed equal.
Use an exact snapshot when available; provider changes behind aliases still
require explicit rechecks because display names cannot prove stable identity.

`skill reporting assess` returns `assessment_required` for unqualified/unknown
combinations or user-requested `--reevaluate`. Detection authorizes assessment
only. The caller chooses per-run review, qualification, or both; the CLI does
not silently rerun a model. `qualify` requires collected raw outputs and a
collection record bound to procedure/model/baseline, input/output hashes,
producer identity, and fresh execution contexts. Each sample must meet its
profile's approved repetition count. This is not a universal retry threshold.

All machine-read profile attachments are contained package-relative paths.
An intact profile package can relocate without changing its qualification
identity; no original host absolute paths are required. Additional quality
Knowledge travels as packaged resolved copies with matching XIDs. The caller
owns XID resolution and provenance.

`--contract` remains a supported local-manifest interface with explicit
`legacy_local_manifest` evidence. It is not target-aware Knowledge and cannot
participate in profile selection. New target-specific criteria and exemplars
are curated on the Knowledge side, not copied into each Skill.

## Failure disposition and explicitly authorized correction

A failed review grants no edit authority. Distinguish artifact-only errors
(repair the current output), missing input (obtain it), ambiguous criteria
(separate owner clarification), and evidenced procedure deficiency (propose
bounded correction). No arbitrary count of failures automatically authorizes
Skill changes.

Only a direct scoped user recalibration instruction authorizes the last path.
`skill reporting authorize` records it, the current combination, and a bounded
attempt budget in a fresh file. This is an auditable authority record, not an
authentication service. Never create it from generated suggestions or alarms.

Keep approved examples, input samples, Knowledge, and criteria immutable.
Stage candidate procedure wording separately. The candidate's identity, scope,
inputs, outputs, declared criteria, required Knowledge, aliases, and additional
control references must remain unchanged. Never relax criteria or rewrite the
baseline to pass. Broader changes require separate approval.

The authorized executor generates candidate wording and collects real outputs.
`skill reporting recalibrate` checks supplied evidence against the fixed
baseline. On failure it records the attempt and leaves the live procedure
untouched; on exhaustion or unresolved subjective review, hand off evidence.
On pass it adopts the staged wording, consumes authorization, and qualifies
only the evaluated model for the new procedure revision. Other models' prior
records do not transfer. A changed procedure hash invalidates external maturity
and adoption receipts: this command neither refreshes those receipts nor grants
promotion. Revalidate/update adoption through its supported owner process before
claiming unchanged runtime readiness.

## Isolation and implementation limits

Independent procedure review is required even when all output criteria are
deterministic. Its receipt binds original/candidate hashes and the reviewer's
decision that active Skill-specific stops, obligations, and scope are preserved;
format checks cannot establish that arbitrary rewritten methods respect those
obligations. The producer cannot approve that receipt. For a repository-adopted
Skill, a passing candidate yields `needs_adoption_review` and remains staged:
the live source and adoption receipt remain intact for coherent owner
integration. Output checks never silently grant authority to rewrite governance.

Ordinary approved templates may guide generation. Evaluation-only answers,
findings, and held-out assets remain outside the evaluated target/context under
[Calibration evaluation](../../../skills/os/skill_calibration_evaluation/SKILL.v1.md#xid-E3B7A1C8D490).
Public examples are smoke checks; independent held-out review protects against
overfitting. Collection and review records are consistency checked, including
rejecting the same producer/reviewer identity, but the CLI cannot attest actual
provider execution, reviewer independence, or user instruction authenticity.

These commands are explicit workflow adapters, not model training, background
monitoring, automatic output enrollment, or a provider API. Callers collect real
outputs and attach evidence to existing review and closure. Deterministic tests
do not establish cross-model reliability.

The initial deterministic adapter checks Markdown headings and simple pipe
tables, row widths, and literal section-placement markers. It is not a complete
Markdown renderer or a Word/Excel visual validator. Other artifact formats and
semantic/readability quality remain with the existing independent reviewer or
an output-specific validator. Profile references are resolved artifact paths;
MCP XID resolution occurs in the caller, not implicitly inside this CLI.

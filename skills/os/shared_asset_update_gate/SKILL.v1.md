---
schema_version: 1
skill_id: shared_asset_update_gate
xid: 6EA2C74D91B8
summary: Analyze candidate-bound common management evidence for a selected Skill or Knowledge update without adopting or applying it.
applies_when:
- A configured host dispatches an isolated analyst for a prepared asset_update governance packet before a selected canonical application.
exclusions:
- Do not act as specialized content QA or human adoption authority.
- Do not apply candidates, issue human approvals, sign host execution receipts, or infer that a dispatch plan proves execution.
- Do not reapprove trusted sites or impose common rules on every consuming Skill.
inputs:
- A validated immutable xrefkit.governance_entry/v1 asset_update packet, a distinct opened child Skill run, scoped candidate/rule/specialist materials, and a designated output path.
outputs:
- Evidence-linked analysis artifact and exact packet-bound result containing findings, explicit unknowns and reference roles for host receipt validation.
criteria:
- id: candidate_binding
  statement: Findings belong to the supplied candidate, rules, evidence and packet identity.
  verification: Compare every finding and output identity with the frozen packet materials and target baseline.
- id: coverage
  statement: Exactly one finding covers every declared check, including all mandatory common checks.
  verification: Compare finding IDs with payload checks and inspect evidence for each finding.
- id: authority
  statement: Gate analysis preserves specialist, QA, human adoption and host execution responsibilities.
  verification: Confirm no application, approval assertion, host signature or source reapproval is generated.
knowledge_needs:
- id: sources
  query: source storage and external reference recording obligations
  required_when: Candidate uses externally sourced material or an external reference.
  seed_xids:
  - 2FAD591BF725
- id: knowledge_ontology
  query: domain knowledge ontology assessment and semantic conflict publication boundary
  required_when: Candidate adds or materially revises canonical Knowledge.
  seed_xids:
  - 5803607419B9
control_refs:
- 0F8E2A6C94D1
---
<!-- xid: 6EA2C74D91B8 -->
<a id="xid-6EA2C74D91B8"></a>

# Shared asset update gate analyst

## Startup and planning

Use an instruction-derived Workflow Runtime Binding and an actually isolated
child run distinct from the originating run. The host owns dispatch. An inert
packet or plan is not proof that this method ran. Follow the existing Skill
operating contract for work items, logging, deterministic verification, separate
quality when required, closure and handoff; do not assume the producer owns the
protocol's checker or quality role.

Confirm `kind=asset_update`, packet hash, target and candidate, rule/evidence
identities, designated output and child correlation. Consume only the selected
bounded materials. Revalidate through the configured entry before accepting
identities; changed, missing or inaccessible material is an explicit finding.
Resolve applicable Knowledge by XID rather than bulk loading every rule.
The child run must bind `parent_run_id` to `packet.binding.run_id`, `root_run_id`
to `packet.binding.run_snapshot.fields.root_run_id`, and `work_item_id` to
`packet.binding.work_item_id`; a different parent/root/item is not this analysis.

Plan exactly the `payload.checks` supplied by the entry. These must include
`authority`, `candidate_identity`, `external_references`, `specialist_evidence`
and `handoff`. Do not remove required checks, interpret an empty check list as
success, or infer undisclosed rules from memory.
Resolve the [shared gate contract](../../../docs/core/contracts/115_shared_asset_update_gate.md#xid-0F8E2A6C94D1)
and require its frozen identity among `payload.rules`. This is the single common
management source, not a caller-replaceable checklist.

## Execution

1. Inspect the actual candidate and its intended target/baseline. Check whether
   the scoped requested change, candidate identity and evidence correspond.
2. Compare the applicable common rules with supplied evidence. `authority`
   checks scope and existing decision routes, not whether this analyst can
   grant application. Human adoption remains a separate verified assertion.
3. Inspect external references by actual use. Distinguish fixed evidential basis,
   intended current-information reference and navigation-only reference. One
   source may have more than one use. Fixed basis identifies used content,
   version/commit and locator; current use identifies purpose and when freshness
   matters. Preserve current source-storage requirements and their explicit
   exceptions. A commit link alone does not satisfy a required source copy.
   Do not ask for repeated approval of an already trusted site; this does not
   relax the ambient external-input guard.
4. Check specialist evidence required for the target and change. Missing source,
   unresolved ontology conflict, absent applicable QA or stale definition
   governance remains missing/refused evidence. Mechanical edits can have
   reasoned nonapplicability; gate analysis never replaces semantic judgment,
   QA or human corrective instructions. Changes after QA require affected
   checks again through their owning route.
5. For every declared check, produce one finding with scoped material evidence.
   Use `pass`, `fail`, `unknown` or `not_applicable` for that obligation. A
   reason and at least one packet material path are required, including a
   justified nonapplicability finding. Do not use `not_applicable` to skip
   candidate identity, authorized scope or required handoff.
6. Record unresolved facts and next owner in the analysis artifact; preserve
   failure evidence rather than signing a success summary. Inspect handoff
   readiness without applying the candidate.

## Output and continuity

Save a strict JSON analysis artifact under the designated work path with
`packet_hash`, `findings`, `unknowns`, `reference_roles` and
`external_reference_disposition` only. It is the result
body EXCLUDING the `output` pointer, preventing a self-hash cycle. Preserve
detailed source locators, candidate context and next-owner reasoning in the
finding reasons/reference-role records or a separately linked judgment record.
Record the saved JSON path as a `done` `output` artifact in this child run. The
host hashes saved raw bytes and adds `output` to form the returned result:

```json
{
  "packet_hash": "<unchanged supplied packet hash>",
  "output": {"path": "<repository-relative analysis artifact>", "sha256": "<raw bytes hash>"},
  "findings": [{"id": "<declared check>", "result": "pass", "reason": "<evidence-backed reason>", "evidence": ["<packet material path>"]}],
  "unknowns": [],
  "reference_roles": [],
  "external_reference_disposition": "no_external_refs"
}
```

Every finding ID appears exactly once and the set equals `payload.checks`.
Evidence paths must be in frozen `materials`; detailed locators belong in the
analysis artifact. Role rows use exactly `role`, `source_locator`, `used_for`,
`acquired_at`, `stored_source`, `fixed_identifier`, `refresh_condition`,
`source_exception`, `exception_evidence`. Roles are `fixed_basis`,
`current_information`, `navigation`; irrelevant values are null. Follow the
shared contract's stored-source/xddp, identifier and refresh-condition rules.
Use `classified` with nonempty rows, or `no_external_refs` with empty rows and
an explicit evidence-backed inspection rationale in `external_references`.
An empty list is not a shortcut past inspection. Unknowns remain
explicit; do not return an empty list to obtain application eligibility.

## Monitoring, closure and handoff

Stop and use the owning handoff path for missing rule authority, changed packet,
missing material or upward external influence. Keep output readiness and
unresolved findings distinct: do not fake normal child closure when the
operating contract prohibits it. Run deterministic verification and closure
under that contract before asking the host to attest completed execution. A
blocked child cannot be presented as completed by changing result fields.

Return the saved analysis body and actual child log to the host. Only the
trusted host verifies and wraps execution identity, child-log hash and result
hash in its receipt. The analyst never issues a signature or human approval.
Passing findings are management evidence only; target application, human
adoption, XID/catalog/adoption consistency and runtime activation belong to
their existing owners. Public source existence and structural validation do
not establish trial maturity, host deployment or public release.

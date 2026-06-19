<!-- xid: 51E163189A50 -->
<a id="xid-51E163189A50"></a>

# Pack Manifest: editorial-ops

This manifest is the canonical, machine-checkable definition of the
`editorial-ops` Business Pack. It declares which assets the pack OWNS
(exclusive) and which it USES (shared, may live anywhere including the OS core).
For the Business Pack concept see
[Business Pack model](../../../docs/071_business_pack_model.md#xid-40511A8A06CD).

- pack_id: `editorial-ops`
- summary: take an article through intake, drafting, review (factual and reader-experience), and multi-channel release as explicit stages, so review and release are never skipped
- maturity: `trial`
- depends_on:
  - os_contract_version: `1`
- entry: `skills/packs/editorial-ops/editorial_ops_index/SKILL.md`
- owns_skills:
  - `skills/packs/editorial-ops/editorial_ops_index`
  - `skills/packs/editorial-ops/editorial_intake`
  - `skills/packs/editorial-ops/draft_authoring`
  - `skills/packs/editorial-ops/fact_review`
  - `skills/packs/editorial-ops/reader_experience_review`
  - `skills/packs/editorial-ops/crosspost_release`
- owns_knowledge:
  - `knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21`
  - `knowledge/packs/editorial-ops/120_reader_capability_model.md#xid-125B6C5E3630`
- uses_capabilities:
  - `capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- uses_knowledge:
  - `knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
- inputs: topic fragments or article seeds, source links or evidence set, optional existing draft, target publication channels and timeline
- outputs: scoped intake framing, article draft, factual review result, reader-experience review result, per-channel release package with adaptation notes and final human sign-off boundary

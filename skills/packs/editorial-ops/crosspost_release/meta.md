<!-- xid: E2E73BDF143A -->
<a id="xid-E2E73BDF143A"></a>

# Skill Meta: crosspost_release

- skill_id: `crosspost_release`
- summary: prepare a reviewed article for per-channel publication with explicit adaptation notes, release blockers, and final human sign-off boundary
- use_when: intake, drafting, and both reviews are complete enough that a release package or crosspost plan is needed
- input: latest draft, review results, target channels, and optional publication metadata
- output: release package under `work/editorial_ops/` by default, plus channel adaptation notes, unresolved blockers, and final publish checklist
- maturity: `draft`
- execution_mode: `local_default`
- model_tier: `light`
- guard_policy: `required`
- os_contract:
  - version: `1`
  - worklist_policy: `required`
  - execution_role: `required`
  - check_role: `required`
  - logging_policy: `session_required`
  - judgment_log_policy: `required_when_non_trivial`
  - unknown_risk_policy: `explicit`
  - closure_gate: `required`
  - handoff_policy: `explicit`
- constraints: do not treat release packaging as publication approval; do not erase unresolved blockers during channel adaptation; preserve a human final sign-off boundary; write the release result to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the latest draft and both review outputs exist and identify the target channels
  - planning: determine what adaptation each channel needs and which blockers still prevent release
  - execution: prepare the release package, channel notes, and final checklist
  - monitoring_and_control: stop if unresolved factual blockers are being reclassified as acceptable without owner approval
  - closure: return the release path, unresolved blockers, and the final human sign-off handoff
- tags: `editorial`, `release`, `crosspost`, `publishing`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
- `../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21`

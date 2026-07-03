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
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: prepare a reviewed article for per-channel publication with explicit adaptation notes, release blockers, and final human sign-off boundary
- responsibility: intake, drafting, and both reviews are complete enough that a release package or crosspost plan is needed
- os_contract: v1
- constraints: do not treat release packaging as publication approval; do not erase unresolved blockers during channel adaptation; preserve a human final sign-off boundary; write the release result to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the latest draft and both review outputs exist and identify the target channels
  - planning: determine what adaptation each channel needs and which blockers still prevent release
  - execution: prepare the release package, channel notes, and final checklist
  - monitoring_and_control: stop if unresolved factual blockers are being reclassified as acceptable without owner approval
  - closure: return the release path, unresolved blockers, and the final human sign-off handoff
- tags: `editorial`, `release`, `crosspost`, `publishing`
- skill_doc: `./SKILL.md`
- knowledge_refs:
- `../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21`

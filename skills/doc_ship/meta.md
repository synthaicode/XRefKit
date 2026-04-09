<!-- xid: 9F38C7A15D4E -->
<a id="xid-9F38C7A15D4E"></a>

# Skill Meta: doc_ship

- skill_id: `doc_ship`
- summary: apply approved promotion candidates from `work/` into canonical repository assets and leave traceable moved-to pointers
- use_when: `retro` or an equivalent review has identified stable promotion candidates and the user wants those candidates reflected in `docs/`, `knowledge/`, `skills/`, or `agent/`
- input: approved promotion report, related `work/` records, target canonical files or target classes, optional user wording constraints
- output: updated canonical files, `work/` pointer updates, unresolved or skipped candidate list, xref validation result
- execution_mode: `local_default`
- guard_policy: `required`
- constraints: do not ship unstable notes; do not duplicate existing canonical content; do not mix procedure and domain fact into the wrong destination
- lifecycle:
  - startup: confirm approved candidates, evidence records, and canonical targets
  - planning: map each approved item to exactly one canonical destination and update scope
  - execution: update canonical files, add new managed files when needed, and update the source `work/` pointer
  - monitoring_and_control: verify duplication, missing XIDs, and destination mismatch before completion
  - closure: run xref maintenance, summarize applied and skipped items, and preserve traceability
- tags: `documentation`, `promotion`, `knowledge-ops`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../docs/013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B`
  - `../../docs/014_working_area_policy.md#xid-111D282CA0EA`
  - `../../docs/015_shared_memory_operations.md#xid-4A423E72D2ED`

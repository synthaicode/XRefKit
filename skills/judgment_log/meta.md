<!-- xid: E3C8A16D4B02 -->
<a id="xid-E3C8A16D4B02"></a>

# Skill Meta: judgment_log

- skill_id: `judgment_log`
- summary: write a judgment log that records decision, evidence, inference boundary, confidence, and next verification step
- use_when: a task produces a non-trivial judgment that should be inspectable or reusable later, especially when confidence is mixed or alternatives exist
- input: work type, target, decision, evidence, confidence, optional alternatives, optional open questions, optional output path
- output: judgment log file and normalized judgment summary
- execution_mode: `local_default`
- guard_policy: `required`
- constraints: separate facts from inference; do not present inferred-only judgments as normal completion; preserve alternatives and open questions
- lifecycle:
  - startup: confirm judgment target and evidence, then load the schema
  - planning: separate facts from inference and classify evidence type and decision status
  - execution: write the normalized judgment log
  - monitoring_and_control: downgrade inferred-only or weakly supported conclusions as needed
  - closure: return path, status, and remaining open questions
- tags: `logging`, `judgment`, `traceability`, `work`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../docs/014_working_area_policy.md#xid-111D282CA0EA`
  - `../../docs/015_shared_memory_operations.md#xid-4A423E72D2ED`
  - `../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201`
  - `../../knowledge/organization/121_judgment_log_schema.md#xid-7B4C2D91E621`

<!-- xid: E3C8A16D4B02 -->
<a id="xid-E3C8A16D4B02"></a>

# Skill Meta: judgment_log

- skill_id: `judgment_log`
- summary: write a judgment log that records decision, evidence, inference boundary, confidence, and next verification step
- use_when: a task produces a non-trivial judgment that should be inspectable or reusable later, especially when confidence is mixed or alternatives exist
- input: work type, target, decision, evidence, confidence, optional alternatives, optional open questions, optional output path
- output: judgment log file and normalized judgment summary
- maturity: `trial`
- execution_mode: `local_default`
- guard_policy: `required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: write a judgment log that records decision, evidence, inference boundary, confidence, and next verification step
- role_responsibilities:
  - executor: a task produces a non-trivial judgment that should be inspectable or reusable later, especially when confidence is mixed or alternatives exist
- os_contract: v1
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
  - `../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA`
  - `../../../docs/core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED`
  - `../../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201`
  - `../../../knowledge/organization/121_judgment_log_schema.md#xid-7B4C2D91E621`
- observation_refs:
  - `../../../observations/2026-06-23_csharp_review_bad_mail_sender_handoff_judgment.md`
  - `../../../observations/2026-06-12_judgment_csharp_error_policy_extraction_authoring.md`

<!-- xid: 6E8296A4C2D1 -->
<a id="xid-6E8296A4C2D1"></a>

# Skill Meta: retro

- skill_id: `retro`
- summary: review session logs and current work artifacts, then propose promotion candidates from `work/` into canonical repository assets
- use_when: a task or work session is ending and the agent should determine whether stable rules, knowledge, or procedures must be promoted out of `work/`
- input: current task goal, related `work/sessions/` or `work/retrospectives/` files, changed files, optional conversation history, optional target canonical paths
- output: promotion candidate list, target location per candidate, reasons, evidence references, already-promoted checks, stay-in-work decisions, optional draft update plan
- maturity: `draft`
- execution_mode: `local_default`
- guard_policy: `required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: review session logs and current work artifacts, then propose promotion candidates from `work/` into canonical repository assets
- role_responsibilities:
  - executor: a task or work session is ending and the agent should determine whether stable rules, knowledge, or procedures must be promoted out of `work/
- os_contract: v1
- constraints: do not treat `work/` as canonical; do not promote unstable notes; do not duplicate existing canonical content without checking first
- lifecycle:
  - startup: confirm the relevant session logs, changed files, and canonical search scope
  - planning: identify candidate decisions, facts, or procedures and define canonical target classes
  - execution: compare `work/` content against existing `docs/`, `knowledge/`, `skills/`, and `agent/` content and classify each candidate
  - monitoring_and_control: downgrade weak or single-session items to `stay_in_work`; mark already-promoted items explicitly
  - closure: produce a promotion report and, when approved, prepare the canonical update set and `work/` pointer update
- tags: `retrospective`, `promotion`, `knowledge-ops`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA`
  - `../../../docs/core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED`
  - `../../../docs/quality/044_system_quality_feedback_register.md#xid-8B31F02A4013`

<!-- xid: 6E8296A4C2D1 -->
<a id="xid-6E8296A4C2D1"></a>

# Skill Meta: retro

- skill_id: `retro`
- summary: review session logs and current work artifacts, then propose promotion candidates from `work/` into canonical repository assets
- use_when: a task or work session is ending and the agent should determine whether stable rules, knowledge, or procedures must be promoted out of `work/`
- input: current task goal, related `work/sessions/` or `work/retrospectives/` files, changed files, optional conversation history, optional target canonical paths
- output: promotion candidate list, target location per candidate, reasons, evidence references, already-promoted checks, stay-in-work decisions, optional draft update plan
- constraints: do not treat `work/` as canonical; do not promote unstable notes; do not duplicate existing canonical content without checking first
- lifecycle:
  - startup: confirm the relevant session logs, changed files, and canonical search scope
  - planning: identify candidate decisions, facts, or procedures and define canonical target classes
  - execution: compare `work/` content against existing `docs/`, `knowledge/`, `skills/`, and `agent/` content and classify each candidate
  - monitoring_and_control: downgrade weak or single-session items to `stay_in_work`; mark already-promoted items explicitly
  - closure: produce a promotion report and, when approved, prepare the canonical update set and `work/` pointer update
- tags: `retrospective`, `promotion`, `knowledge-ops`
- skill_doc: `./SKILL.md`
- capability_refs: none
- knowledge_refs:
  - `../../docs/014_working_area_policy.md#xid-111D282CA0EA`
  - `../../docs/015_shared_memory_operations.md#xid-4A423E72D2ED`
  - `../../docs/044_system_quality_feedback_register.md#xid-8B31F02A4013`

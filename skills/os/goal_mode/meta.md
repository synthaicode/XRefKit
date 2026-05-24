<!-- xid: 5C2D7A91E4F3 -->
<a id="xid-5C2D7A91E4F3"></a>

# Skill Meta: goal_mode

- skill_id: `goal_mode`
- summary: preserve task state, wait for Codex usage recovery, and resume the same goal after the next 5-hour or weekly reset
- use_when: a user wants Codex work to continue toward the same goal even when usage remaining can reach `0%`, and the repository must preserve a restart-ready continuation packet instead of silently stopping
- input: current goal, current task state, changed artifacts or target paths, unresolved items, and actual quota-state evidence such as current remaining usage and the next reset indication shown by Codex
- output: continuation packet for the current goal, explicit wait condition, resume checklist, updated artifacts or handoff pointers, and unresolved items that still block safe continuation
- maturity: `trial`
- execution_mode: `local_default`
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
- constraints: do not invent quota-reset times; do not claim background wake-up or automatic resume unless a real hook or queue mechanism exists; do not lose unresolved items or next-step ownership during the wait; do not resume after a long wait without checking for drift in scope, branch state, or upstream instructions
- lifecycle:
  - startup: confirm the current goal, active boundary, quota-state evidence, and whether the run is still executable now or already needs wait preparation
  - planning: define the minimum continuation packet, resume trigger, drift-check points, and first action after recovery
  - execution: continue work while quota remains, stop new substantive work when usage reaches `0%`, record the continuation packet, wait for the next 5-hour or weekly recovery, and resume from the recorded packet
  - monitoring_and_control: keep quota-state evidence explicit, treat missing reset information as `unknown`, and re-check boundary drift before resume
  - closure: close only after the goal is completed or the continuation packet and handoff state are explicit enough for the next recovery window
- tags: `operations`, `continuation`, `quota`, `codex`, `control`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../docs/049_or_team_usage_guide.md#xid-4E2F91A6B8C1`
  - `../../../docs/050_codex_mcp_job_inbox_design.md#xid-77BCEAA247E3`
  - `../../../docs/058_skill_operating_contract.md#xid-B7A2C94F0E61`
  - `../../../docs/069_codex_goal_mode_usage_guide.md#xid-3E7B4C11A8D2`
  - `../../../docs/070_codex_goal_mode_auto_resume_design.md#xid-6F4D2A18C9E7`
- observation_refs:
  - `../../../work/sessions/2026-05-24_session_goal_mode_skill_seed.md`

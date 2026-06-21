<!-- xid: B87A2C3E4567 -->
<a id="xid-B87A2C3E4567"></a>

# Skill Meta: commonality_derivation

- skill_id: `commonality_derivation`
- summary: derive cross-cutting commonality candidates from completed primary constraint-derivation outputs
- use_when: multiple primary derivation outputs exist and the user needs a second pass for shared implementation candidates or scope-boundary checks
- input: completed DCD/UCD/LCD/ICD/ACD/AACD/CCD/XCD/ISD lists with traceable ids and optional pack-level design context
- output: CD-prefixed commonality file under `work/constraint_derivation/` by default, plus CB-prefixed boundary checks and grouped human confirmation points
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `standard`
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
- constraints: run only after primary derivation outputs exist; aggregate patterns without deciding the final abstraction; keep commonality candidates separate from scope-boundary concerns; write the result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm primary derivation lists are complete enough for a secondary pass and load the shared framework plus the commonality signals
  - planning: flatten all confirmed and unresolved items into one analyzable list while preserving source ids
  - execution: detect recurring patterns, emit CD and CB items, and present tradeoffs rather than deciding integration automatically
  - monitoring_and_control: stop if the task tries to collapse distinct business rules into one abstraction without human confirmation
  - closure: return the candidate table, boundary-check table, and the next human decisions required
- tags: `design`, `cross-cutting`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../../../knowledge/packs/constraint-derivation/180_commonality_derivation_signals.md#xid-9C27AE51D648`
- observation_refs:
  - ../../../../work/sessions/2026-06-21_skill_run_skill_flow_authoring.md

<!-- xid: 51FDA8671D61 -->
<a id="xid-51FDA8671D61"></a>

# Skill Meta: draft_authoring

- skill_id: `draft_authoring`
- summary: produce an article draft from explicit intake framing and source basis without hiding unsupported claims
- use_when: intake has already defined the article boundary and a first draft or revision draft is needed
- input: intake record, source set, channel intent, optional structure preference, and optional existing draft
- output: authoring draft under `work/editorial_ops/` by default, plus claim-to-source notes and unresolved authoring questions
- maturity: `draft`
- execution_mode: `local_default`
- model_tier: `heavy`
- guard_policy: `required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: produce an article draft from explicit intake framing and source basis without hiding unsupported claims
- role_responsibilities:
  - executor: intake has already defined the article boundary and a first draft or revision draft is needed
  - quality_reviewer: independently review output acceptance when this Skill run requires a quality gate
  - handoff_owner: record outputs, unresolved items, next owner, and handoff boundary for this Skill run
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
- constraints: do not invent missing facts to smooth the narrative; keep unsupported wording visible for later review; preserve channel-neutral source meaning before channel-specific adaptation; write the draft to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm intake exists and the source basis is sufficient to start drafting
  - planning: define the draft spine, claim order, and where unresolved questions must stay visible
  - execution: write the draft, attach claim-to-source notes, and keep unsupported sections explicit
  - monitoring_and_control: downgrade unsupported certainty to tentative wording and stop if the task tries to bury factual gaps in polished prose
  - closure: return the draft path, major unresolved questions, and the review handoff
- tags: `editorial`, `writing`, `drafting`, `authoring`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
- `../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21`

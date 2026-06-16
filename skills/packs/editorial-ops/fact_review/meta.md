<!-- xid: 7687FD352C4C -->
<a id="xid-7687FD352C4C"></a>

# Skill Meta: fact_review

- skill_id: `fact_review`
- summary: review article claims for factual separation, source support, names, numbers, links, and channel-sensitive wording risks
- use_when: a draft exists and the article needs evidence-backed checking before release or before further polishing
- input: article draft, source links or evidence set, optional claim list, and optional channel targets
- output: fact-review result under `work/editorial_ops/` by default, plus claim findings, unresolved unknowns, and release blockers
- maturity: `draft`
- execution_mode: `subagent_preferred`
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
- constraints: review concrete article claims rather than generic writing advice; keep missing support explicit as `unknown`; do not silently rewrite the draft inside the review; write the review result to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the draft and evidence set exist and identify the highest-risk claims
  - planning: decide which claim classes need checking and what counts as a release blocker
  - execution: check claims, classify findings, and write the fact-review result
  - monitoring_and_control: downgrade unsupported conclusions to `unknown` and stop if the task drifts into opinion-only editing
  - closure: return the review path, release blockers, and the author revision handoff
- tags: `editorial`, `review`, `fact-check`, `quality`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
- `../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21`

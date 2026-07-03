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
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: review article claims for factual separation, source support, names, numbers, links, and channel-sensitive wording risks
- responsibility: a draft exists and the article needs evidence-backed checking before release or before further polishing
- os_contract: v1
- constraints: review concrete article claims rather than generic writing advice; keep missing support explicit as `unknown`; do not silently rewrite the draft inside the review; write the review result to `work/editorial_ops/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm the draft and evidence set exist and identify the highest-risk claims
  - planning: decide which claim classes need checking and what counts as a release blocker
  - execution: check claims, classify findings, and write the fact-review result
  - monitoring_and_control: downgrade unsupported conclusions to `unknown` and stop if the task drifts into opinion-only editing
  - closure: return the review path, release blockers, and the author revision handoff
- tags: `editorial`, `review`, `fact-check`, `quality`
- skill_doc: `./SKILL.md`
- knowledge_refs:
- `../../../../knowledge/packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21`

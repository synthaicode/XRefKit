<!-- xid: 6F3C20A9B441 -->
<a id="xid-6F3C20A9B441"></a>

# Skill Meta: or_team_operations

- skill_id: `or_team_operations`
- summary: run the OR Team loop for AI-organization state presentation, problem structuring, approval routing, execution control, and re-observation
- use_when: user needs cross-group operating optimization, drift handling, stop-or-continue decisions, or structured improvement control beyond a local fix
- input: target scope, minimum observation data, supporting evidence, baseline reference, and operating constraints
- output: current state, problem list, cause hypotheses, improvement list, approval requirements, implementation method, re-observation method, unresolved items
- constraints: do not become the default implementation owner for product changes; execute only OR-owned changes and otherwise return controlled implementation requests
- lifecycle:
  - startup: confirm scope, minimum evidence, baseline, and operating constraints
  - planning: define observation scope, comparison baseline, and output management IDs
  - execution: present current state, structure problems, produce cause hypotheses, produce improvement list, classify approvals, and define operating disposition
  - monitoring_and_control: track approved improvements, preserve recovery conditions and re-observation conditions, and keep unresolved items explicit
  - closure: complete re-observation and close only after recovery or stable conditional continuation is confirmed
- tags: `operations`, `optimization`, `drift`, `governance`, `control`
- skill_doc: `./SKILL.md`
- capability_refs: none
- knowledge_refs:
  - `../../docs/048_or_team_operating_model.md#xid-1D7A8E2C5F10`
  - `../../docs/049_or_team_usage_guide.md#xid-4E2F91A6B8C1`
  - `../../docs/040_group_definitions.md#xid-8B31F02A4009`
  - `../../docs/043_system_quality_feedback_loop.md#xid-8B31F02A4012`

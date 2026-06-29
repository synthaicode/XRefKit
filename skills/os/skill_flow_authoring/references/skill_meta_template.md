<!-- xid: C2FF81FBEE8E -->
<a id="xid-C2FF81FBEE8E"></a>

# Skill Meta Template

Use this when creating a new Skill in XRefKit.

```md
# Skill Meta: <skill_id>

- skill_id: `<skill_id>`
- summary: <one-line purpose>
- use_when: <when the Skill should be selected>
- input: <expected inputs>
- output: <expected outputs>
- maturity: `draft|trial`
- execution_mode: `local_default|subagent_preferred|subagent_required`
- guard_policy: `required|closed_world`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: <direct specialization of the capability for this Skill>
- role_responsibilities:
  - executor: <what the executor produces or changes>
  - quality_reviewer: <what acceptance review applies when the quality gate is required>
  - handoff_owner: <what handoff boundary and next ownership must be recorded>
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
- constraints: <operational constraints and escalation boundary>
- constraints: <include what must not stay implicit for later AI reuse>
- lifecycle:
  - startup: <startup rule>
  - planning: <planning rule>
  - execution: <execution rule>
  - monitoring_and_control: <downgrade and escalation rule>
  - closure: <closure rule>
- tags: `<tag1>`, `<tag2>`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `<relative-path-to-capabilities>/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `<relative-path-to-capabilities>/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `<relative-path-to-knowledge>/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
- observation_refs:
  - `<relative-path-to-work>/sessions/<session>.md`
```

Notes:

- Keep `draft` when the procedure is not load-ready yet.
- Move to `trial` only after the Skill can actually run and has observation.
- Use `skills_private/` by default; move to `skills/` only for explicit public
  release.
- Replace the relative-path placeholders to match the actual family path such
  as `skills/os/<skill_id>/` or `skills/packs/<pack>/<skill_id>/`.
- `checker` is not a Skill-specific role responsibility. It is assigned by the
  runtime workflow protocol and advanced deterministically with
  `fm skill verify`.
- If later AI runs would need to remember something critical, encode it as
  `input`, `output`, `constraints`, `knowledge_refs`, `observation_refs`, or
  handoff/closure wording instead of leaving it unstated.

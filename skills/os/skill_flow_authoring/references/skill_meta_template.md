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
- capability_layering: `required`
- workflow_protocol: `required`
- capability: <reusable base ability>
- tuning: <direct specialization of the capability for this Skill, e.g. C# or C# + SQL>
- responsibility: <Skill-specific business use, e.g. implementation or quality check>
- os_contract: v1
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
- knowledge_refs:
  - `<common-method-knowledge-or-tuning-aware-routing-index>#xid-...`
  - `<optional-cross-tuning-routing-index-for-composite-tuning>#xid-...`
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
- `responsibility` is the Skill's business use (implementation, quality check,
  design, ...). There is no role field: every Skill is the executor, and the
  checker is the workflow protocol, advanced deterministically with
  `fm skill verify`.
- If later AI runs would need to remember something critical, encode it as
  `input`, `output`, `constraints`, `knowledge_refs`, `observation_refs`, or
  handoff/closure wording instead of leaving it unstated.

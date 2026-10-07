<!-- xid: C2FF81FBEE8E -->
<a id="xid-C2FF81FBEE8E"></a>

# SkillDefinition Template

Use this one-document format when creating a new Skill in XRefKit. The file is
normally named `SKILL.v1.md`. The historical filename of this template is kept
so existing XID links remain stable.

```md
---
schema_version: 1
skill_id: <skill_id>
xid: <12-character-XID>
aliases: []
summary: <one-line purpose>
applies_when: [<selection condition>]
exclusions: [<out-of-scope condition>]
inputs: [<required input>]
outputs: [<produced artifact>]
criteria:
  - id: <stable criterion id>
    statement: <what must be true>
    verification: <how it is checked>
knowledge_needs:
  - id: <need id>
    query: <catalog search intent>
    required_when: <activation condition>
    seed_xids: [<optional-XID>]
control_refs: []
---
<!-- xid: <12-character-XID> -->
<a id="xid-<12-character-XID>"></a>

# Skill: <skill_id>

## Method

1. <reusable judgment or procedure>

## Stop and handoff

<Skill-specific stop, exclusion, or specialist handoff only.>
```

Notes:

- Use `skills_private/` by default; move to `skills/` only for explicit public
  release.
- Replace the relative-path placeholders to match the actual family path such
  as `skills/os/<skill_id>/` or `skills/packs/<pack>/<skill_id>/`.
- Do not add fixed `capability`, `tuning`, `responsibility`, or
  `execution_mode` values. The Workflow Protocol derives them for each work
  item under the Workflow Runtime Binding contract.
- Keep maturity and observations in the external governance record. They are
  not SkillDefinition identity.
- If later AI runs would need to remember something critical, encode it as
  `inputs`, `outputs`, `criteria`, `knowledge_needs`, or Skill-specific
  handoff wording instead of leaving it unstated.

For an existing `legacy_split_v1` Skill, its `meta.md` fields remain valid
compatibility inputs. Preserve them while maintaining that format; do not use
the legacy shape as the template for a new Skill.

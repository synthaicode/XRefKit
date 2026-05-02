<!-- xid: 4E7B8D9C1A20 -->
<a id="xid-4E7B8D9C1A20"></a>

# Skill Maturity Governance

This page defines how Skills mature in XRefKit.

The repository does not treat a new Skill as a fully completed artifact at
creation time.

A Skill is not something that becomes complete just because its procedure text
was written once. Its practical value depends on whether the operating boundary
around it is clear: what the Skill may decide by itself, what must remain
explicit as unknown or risk, what must be handed back to a human, and what
evidence is needed before that handoff is acceptable.

That boundary rarely becomes clear at the moment of creation. It becomes clear
through use, observation, review, and refinement. `maturity` exists to show how
far that clarification has actually progressed.

## Core Policy

- Create new Skills as `draft` unless there is already enough operating clarity
  to justify a higher maturity.
- Use runtime logs, judgment logs, review notes, and retrospectives to observe
  missing rules, missing references, weak boundaries, and repeated judgment
  ambiguity.
- Treat maturity as the clarity level of the Skill's operating boundary with
  humans, not as a cosmetic progress label.
- Promote a Skill only when the target maturity conditions are actually met.
- Keep the current maturity explicit in `meta.md` through `maturity` or
  `status`.

## Maturity Levels

| Maturity | Meaning | Load-ready | Main expectation |
|------|------|------|------|
| `draft` | hypothesis record for a new Skill | no | identify purpose, rough I/O, and the first guess at the human/Skill boundary |
| `trial` | runnable but still being clarified through use | yes | connect operation to observations and discover where the boundary is still weak or ambiguous |
| `stable` | operationally complete Skill | yes | explicit runtime, guard, references, operating contract, and a dependable handoff boundary |
| `governed` | stable Skill with governance and audit linkage | yes | explicit governance references, promotion evidence, and an auditable responsibility boundary |
| `deprecated` | kept for compatibility/history, not for new use | no | preserve traceability and replacement path if applicable |

## Meta Schema By Maturity

### Draft Minimum

`draft` must carry only the minimum hypothesis structure:

```md
- skill_id: `<skill_id>`
- summary: short summary
- use_when: initial hypothesis
- input: initial hypothesis
- output: initial hypothesis
- skill_doc: `./SKILL.md`
- maturity: `draft`
```

`execution_mode`, `guard_policy`, `constraints`, `capability_refs`,
`knowledge_refs`, `tags`, and `os_contract` may still be absent or provisional.

### Trial Additions

`trial` is the first load-ready maturity.

Recommended additions before the first run:

```md
- maturity: `trial`
- execution_mode: `local_default`
- guard_policy: `required`
```

Required to pass `trial` check:

```md
- observation_refs:
  - `../../work/sessions/<session>.md`
```

`observation_refs` may point to:

- `work/sessions/...`
- `work/judgments/...`
- review outputs
- retrospective or promotion reports

The point is to keep the refinement basis explicit.

### Stable Requirements

To pass `stable` check, the Skill must satisfy operational completeness:

- `draft` minimum fields
- `observation_refs`
- valid `execution_mode`
- valid `guard_policy`
- `constraints`
- required runtime capability reference
- required guard references when `guard_policy: required`
- explicit closed-world wording when `guard_policy: closed_world`
- full required `os_contract`

### Governed Requirements

To pass `governed` check, the Skill must first satisfy `stable`, then add
explicit governance linkage:

```md
- governance_refs:
  - `../../docs/<governance-doc>.md#xid-...`
  - `../../work/<promotion-or-review-record>.md`
```

`governance_refs` should point to the policy, approval, audit basis, or review
record that justifies governed status.

## Check Modes

Use the CLI to check either the declared maturity or a target promotion level:

```powershell
python -m fm skill check --meta skills/<skill_id>/meta.md
python -m fm skill check --meta skills/<skill_id>/meta.md --level draft
python -m fm skill check --meta skills/<skill_id>/meta.md --level trial
python -m fm skill check --meta skills/<skill_id>/meta.md --level stable
python -m fm skill check --meta skills/<skill_id>/meta.md --level governed
```

- no `--level`: check against declared `maturity` or `status`
- `--level stable`: use as a promotion-readiness gate
- `--level governed`: use as a governance-readiness gate

## Runtime Rule

- `draft` is not load-ready
- `deprecated` is not load-ready
- `trial`, `stable`, and `governed` may be opened with:

```powershell
python -m fm skill run --meta skills/<skill_id>/meta.md --task "task text"
```

For `trial`, provisional runtime defaults may be used while the Skill is still
being clarified.

## Improvement Flow

1. Create the Skill as `draft`.
2. Add a first `SKILL.md` procedure and promote to `trial`.
3. Run the Skill and record session/judgment/review evidence.
4. Add or refine `use_when`, `input`, `output`, `constraints`,
   `execution_mode`, `guard_policy`, `capability_refs`, and `knowledge_refs`.
5. Link the observed evidence through `observation_refs`.
6. Promote to `stable` after the operating contract is explicit.
7. Add governance and audit basis through `governance_refs`.
8. Promote to `governed` only after the stricter check passes.

## Draft Template

```md
# Skill Meta: <skill_id>

- skill_id: `<skill_id>`
- summary: <one-line purpose>
- use_when: <initial hypothesis>
- input: <initial hypothesis>
- output: <initial hypothesis>
- skill_doc: `./SKILL.md`
- maturity: `draft`
```

## Trial Upgrade Template

```md
- maturity: `trial`
- execution_mode: `local_default`
- guard_policy: `required`
- observation_refs:
  - `../../work/sessions/<session>.md`
```

## Stable Upgrade Template

```md
- maturity: `stable`
- execution_mode: `subagent_preferred`
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
- constraints: <explicit operational constraints>
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
- observation_refs:
  - `../../work/sessions/<session>.md`
```

## Improvement Note Template

Use a small Markdown note or session entry when refining a Skill:

```md
# Skill Improvement Note: <skill_id>

- date: `YYYY-MM-DD`
- skill_id: `<skill_id>`
- current_maturity: `draft|trial|stable`
- observed_from:
  - `work/sessions/...`
  - `work/judgments/...`
- gap_type:
  - `use_when`
  - `input`
  - `output`
  - `constraints`
  - `guard_policy`
  - `execution_mode`
  - `capability_refs`
  - `knowledge_refs`
- summary: <what was unclear or missing>
- change_needed: <what should be updated>
- promotion_effect: <does this support trial/stable/governed promotion?>
```

## Promotion Questions

Before promoting a Skill, ask:

- Is the current `use_when` based on actual use rather than only an initial idea?
- Are the declared inputs and outputs specific enough for repeatable use?
- Are repeated judgment ambiguities now visible in `constraints` or references?
- Is `guard_policy` justified by observed context-loading behavior?
- Is `execution_mode` justified by the actual separation need?
- Are required capability and knowledge references now explicit?
- Is the operating contract explicit enough for the target maturity?
- For `governed`, is the governance or audit basis linked explicitly?

## Related

- [Skill authoring with xref](013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B)
- [Skill Operating Contract](058_skill_operating_contract.md#xid-B7A2C94F0E61)

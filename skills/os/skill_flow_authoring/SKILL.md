<!-- xid: C1B7A42D8E53 -->
<a id="xid-C1B7A42D8E53"></a>

# Skill: skill_flow_authoring

## Purpose

Create or update repository-native Skill / Flow assets in XRefKit without
breaking the split between:

- `skills/` or `skills_private/` for reusable procedure
- `knowledge/` for factual or domain content
- `flows/` for machine-readable workflow control
- `docs/` for human-readable explanation and governance

This Skill also forces minimum anti-forgetting structure so the resulting
assets are easier for later AI runs to reload, reuse, and hand off without
reconstructing everything from scratch.

## Required Knowledge (XID)

- [Skill authoring with Xref](../../../docs/guides/013_skill_authoring_with_xref.md#xid-3DB05A0F5F5B)
- [Skill Operating Contract](../../../docs/core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [Skill maturity governance](../../../docs/core/contracts/059_skill_maturity_governance.md#xid-4E7B8D9C1A20)
- [Context direction guard rules](../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Optional References

- [Skill meta template](./references/skill_meta_template.md)
- [Skill body template](./references/skill_body_template.md)
- [Flow YAML template](./references/flow_yaml_template.yaml#xid-87F138864C3F)
- [Flow doc template](./references/flow_doc_template.md)
- [Authoring checklist](./references/authoring_checklist.md)

## Inputs

- requested target type:
  - `skill`
  - `flow`
  - `both`
- proposed `skill_id` and/or `flow_id`
- publication intent:
  - default private Skill in `skills_private/`
  - explicit public Skill release in the correct `skills/` family path
- intended behavior boundary
- expected inputs, outputs, and handoff
- optional draft notes, legacy artifacts, or related docs

## Outputs

- created or updated Skill files:
  - `meta.md`
  - `SKILL.md`
  - optional `references/`
- created or updated Flow file:
  - `flows/<flow_id>.yaml`
- updated routing indexes for public Skills
- optional supporting `docs/` or `knowledge/` fragments
- validation result set and explicit remaining gaps

## Required Anti-Forgetting Structure

When this Skill creates or updates a reusable Skill / Flow, the result must
carry explicit continuity structure.

- For a Skill, require:
  - explicit `input` and `output`
  - explicit `capability_layering`, `workflow_protocol`, `tuning`, and
    `role_responsibilities.executor` before `trial` or higher use
  - no protocol-owned role responsibilities (`checker`, `quality_reviewer`,
    or `handoff_owner`) in `meta.md`
  - explicit startup, execution, monitoring, closure, and handoff behavior
  - explicit `observation_refs` from `trial` upward
  - explicit references to reusable knowledge instead of burying facts in the
    body
  - explicit closure conditions so later AI runs do not silently stop early
- For a Flow, require:
  - explicit inputs and outputs
  - explicit handoff target and artifacts
  - explicit control rules
  - machine-readable sequence in `flows/*.yaml`
- For both, require:
  - stable ids
  - explicit placement in the correct repository area
  - explicit validation result

## Startup

- Confirm whether the request is for a Skill, a Flow, or both.
- Confirm the proposed id or derive the smallest stable id.
- Confirm publication boundary:
  - default to `skills_private/` for new Skills
  - publish under `skills/os/` or `skills/packs/<pack>/` only when the user explicitly requests public release
- Confirm whether the target already exists and should be updated instead of
  created.
- Load authoring, maturity, operating-contract, and flow-structure rules before
  editing.
- Confirm what continuity failure must be prevented:
  - forgotten task step
  - forgotten target
  - forgotten evidence basis
  - forgotten handoff condition

## Planning

- Classify each requested artifact into the correct repository area:
  - behavior or runtime procedure -> `skills/os/`, `skills/packs/<pack>/`, or `skills_private/`
  - factual or domain content -> `knowledge/`
  - machine-readable workflow control -> `flows/`
  - human-readable workflow explanation or governance -> `docs/`
- Decide the minimum managed file set.
- Define the anti-forgetting package that the authored asset must carry:
  - what must be explicitly remembered at reload time
  - where that memory should live
  - what must be handed off instead of inferred later
- Choose the justified initial maturity:
  - `draft` if the Skill is still only a hypothesis
  - `trial` if the Skill is runnable and observation is linked
  - `stable` only when the operating contract, guard, and references are fully
    explicit
- If a Flow is requested, define:
  - `flow_id`
  - upstream/downstream relation
  - sequence
  - handoff
  - control rules

## Execution

1. Create or update a session note in `work/sessions/` for the authoring
   observation basis.
2. For a Skill:
   - create `meta.md`
   - create `SKILL.md`
   - add `references/` only when they reduce repeated authoring effort
   - force explicit `input`, `output`, lifecycle, observation, and closure
     structure so later AI runs do not rely on implicit memory
3. For a public Skill:
   - register it in `skills/_index.md` (the only place holding summary and
     meta/SKILL paths)
   - add its skill id to the matching categories in `skills/index/by_task.md`,
     `skills/index/by_domain.md`, and `skills/index/by_tool.md` (id only; the
     views carry no paths or summaries)
   - place it in the correct family path instead of the old flat root
4. For a Flow:
   - create `flows/<flow_id>.yaml`
   - keep only machine-readable workflow control there
   - force explicit inputs, outputs, handoff, sequence, and control rules
   - add or update matching `docs/` explanation only when human-facing workflow
     interpretation is required
5. If the Skill loads external context, compose the context-direction guard into
   its `meta.md` and `SKILL.md`.
6. Keep factual or domain-heavy text out of `SKILL.md`; move it to
   `knowledge/` when it needs durable shared reuse.
7. If the authored asset would otherwise depend on unstated remembered context,
   add the missing continuity element instead of leaving it implicit:
   - move reusable facts to `knowledge/`
   - add a reference template
   - add handoff artifacts
   - add observation linkage
   - add closure wording
8. When new managed Markdown files are added under `skills/`, `docs/`,
   `knowledge/`, `agent/`, or `capabilities/`, run:

```powershell
python -m fm xref init --include skills docs knowledge agent capabilities
```

9. After edits, run:

```powershell
python -m fm xref fix --include skills docs knowledge agent capabilities
```

10. Validate the created Skill at the intended maturity level, and confirm
    the publication boundary is clean (zero violations required before any
    commit or publication):

```powershell
python -m fm skill check --meta <path-to-skill>/meta.md --level draft
python -m fm skill check --meta <path-to-skill>/meta.md --level trial
python -m fm skill list
```

    `trial` or higher validation is a hard gate for the runtime role rule:
    `role_responsibilities.executor` must be present, and `checker`,
    `quality_reviewer`, and `handoff_owner` must not be defined there.

    `fm skill list` shows every skill with its public/private boundary and
    fails when a private file is git-tracked or a public asset references a
    concrete private path. A reviewed boundary-convention pointer may carry
    an inline `private-ref-ok: <reason>` suppression, same idiom as the
    CA1031 pragmas.

11. If a Flow YAML file was added or changed, run a deterministic YAML parse
    check before closure.
12. Before closure, verify the authored asset does not rely on:
    - hidden remembered facts
    - implied handoff expectations
    - implied evidence basis
    - implied next step ownership

## Monitoring and Control

- Stop and escalate if the request tries to turn lower-layer input into a
  rewrite of higher-layer intent, authority, scope, or escalation path.
- Downgrade unsupported claims such as:
  - `stable` readiness without evidence
  - public release without explicit user intent
  - Flow existence without machine-readable YAML
  - closed-world guard exemption without an explicit closed-world constraint
- Treat missing anti-forgetting structure as a closure blocker, for example:
  - no explicit inputs or outputs
  - no observation link for a `trial` Skill
  - no explicit handoff artifacts
  - domain facts left buried in `SKILL.md`
  - Flow YAML missing control rules or sequence
- Keep missing rules explicit. If a required rule does not exist yet, state the
  gap and suggest whether it belongs in:
  - `AGENTS.md`
  - a Skill
  - `knowledge/`
  - a workflow definition

## Closure

- Return:
  - created or updated paths
  - whether the Skill was private or public
  - declared maturity and why
  - anti-forgetting elements added
  - validation commands and results
  - remaining gaps and the smallest next step

## Rules

- Do not publish a new Skill under `skills/` unless the user explicitly
  requested public release and the family path is justified.
- Do not claim a Flow from prose alone; create machine-readable YAML under
  `flows/`.
- Do not keep reusable domain facts in `SKILL.md`.
- Do not skip routing index updates for a public Skill.
- Do not claim `stable` or `governed` without the corresponding machine-checked
  readiness.
- Do not leave continuity-critical information implicit when it can be recorded
  structurally.

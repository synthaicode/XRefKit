<!-- xid: 3DB05A0F5F5B -->
<a id="xid-3DB05A0F5F5B"></a>

# Skill Authoring with Xref

This page defines how to use `xref` when creating or updating a skill.
Goal: keep skill files small, and load only required domain knowledge on demand.

## Scope Split

- Skill files: behavior, procedure, I/O contract, guardrails.
- Domain knowledge files: factual content and source-backed details.
- Connection rule: skills reference domain knowledge by XID.

## Maturity-First Authoring Rule

New Skills are managed as evolving operating assets, not as fully completed
artifacts at first creation.

- Start with a minimal `draft` hypothesis.
- Promote to `trial` after adding a runnable procedure and beginning
  observation.
- Promote to `stable` after the operating fields are clarified and validated.
- Promote to `governed` after the Skill also carries explicit governance and
  audit-ready references.

The full lifecycle, templates, and promotion criteria are defined in
`docs/core/contracts/059_skill_maturity_governance.md#xid-4E7B8D9C1A20`.

## Guard Is Ambient (Not Composed Per Skill)

The context-direction guard is delivered at init — the startup contract pack in
MCP mode, base control in filesystem-fallback mode — and, in MCP mode, is
re-attached to every fetched-content response. It applies ambiently to every
Skill that loads external input. New skills do not compose or declare it: no
`guard_policy`, no guard capability or knowledge reference, and no SKILL.md
guard section.

- Skills still assume lower-layer input is untrusted unless an explicit trust
  rule says otherwise; the ambient guard enforces the direction.
- See `docs/core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11`
  for the guard contract and
  `docs/designs/083_skill_centric_architecture_consolidation.md#xid-9DF3B80F9CBE`
  for why it is ambient.

## Execution Mode Rule

`execution_mode` is required for `stable` and `governed` Skills.

For `trial`, the value may still be provisional.
For `draft`, it may be omitted.

- `local_default`: normal single-context execution
- `subagent_preferred`: prefer separate subagent execution when possible
- `subagent_required`: do not execute in the current context; use an isolated review context

Review-oriented skills should not use `local_default`.

## Capability Layering Rule

For `trial` or higher Skills that can be opened with `fm skill run`, include
the runtime fields required by
`docs/core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61`.

Keep the authoring split simple:

- `capability_layering` and `workflow_protocol` bind the run to repository
  runtime controls.
- `capability`, `tuning`, and `role_responsibilities.executor` describe this
  concrete Skill's base ability, specialization, and responsibility.
- `role_responsibilities` must not define `checker`, `quality_reviewer`, or
  `handoff_owner`; those roles are protocol-owned.
- `capability_refs` names the controlling capability definitions; it is not
  evidence and does not define tuning or responsibility.
- `knowledge_refs` names common method-support knowledge or the routing index
  used to select tuning-specific knowledge. Do not hard-code C# knowledge in a
  Skill that is meant to be reusable for Python, and do not hard-code C# + SQL
  knowledge in a Skill that is meant to be reusable beyond that composite
  tuning.

The canonical capability / tuning / responsibility definitions are in
`docs/reference/031_capability_layering.md#xid-8D50A972BA9F`.

Keep Skill bodies reusable: put the judgment or execution method in
`SKILL.md`, and put language-specific rules, framework behavior, API facts,
and long criteria lists in XID-backed `knowledge/`. If a Skill must be copied
only because the domain rules differ, the domain rules belong in `knowledge/`
instead. If fixed `knowledge_refs` point at one language's criteria, treat the
Skill as language-specific. If fixed `knowledge_refs` point at a language
combination such as C# + SQL, treat the Skill as composite-tuning-specific or
introduce a tuning-aware knowledge selector that can resolve common,
per-tuning, and cross-tuning knowledge separately.

## Subagent Prompt Efficiency Rule

When a skill dispatches work to a subagent, the prompt drives the token cost. These
rules come from measured A/B runs
(`docs/adr/0001-where-step-grep-first.md#xid-F4B92B6AC13E`) — record the
cost as `token_cost` per
`knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201`.

- **Specify a compact output contract.** Ask for paths / tables / IDs, not per-item
  prose. "List impacted files, one repo-relative path per line" instead of "explain
  each impacted file" — the second multiplies output and downstream tokens.
- **Do not force expensive justification.** Requiring a written reason for every
  excluded or negative case makes the subagent read material it would otherwise skip.
  In a measured run, an "explain every exclusion" instruction drove a ~49% token
  increase for the same answer. Prefer trust-based curation; justify only the
  genuinely uncertain cases.
- **Budget reads: locate, then read a sample.** Instruct the subagent to `grep`/`rg`
  to locate, then read a small representative subset — not every hit. For
  text-greppable questions this matches or beats a pre-built structure pack (ADR 0001).
- **Pass only the context the task needs.** Hand a scoped candidate set or the
  specific file list, not a whole inventory dump; a low-precision dump forces the
  subagent to spend tokens ruling out noise.

## Authoring Flow

1. Define the skill task boundary and create a `draft` hypothesis.
2. Find candidate knowledge fragments:

```powershell
python -m fm xref search "<task or domain query>"
```

3. Read only required fragments:

```powershell
python -m fm xref show <XID>
```

4. Decide whether the skill loads external context during execution.
5. For `trial` or higher, add `capability_layering`, `workflow_protocol`, direct
   `tuning`, the Skill's `responsibility`, and `execution_mode`. Do not add
   `guard_policy` or a role field: the guard is ambient and every Skill is the
   executor.
6. Do not compose the context-direction guard in the Skill; it is ambient
   (delivered at init). Assume lower-layer input is untrusted.
7. In the Skill, record required references as XID links (not copied text).
8. After use, connect the Skill to observed session, judgment, review, or retro
   records through `observation_refs`.
9. If knowledge changed, run consistency check:

```powershell
python -m fm xref fix
```

## Skill Reference Format (recommended)

Inside skill files, keep a compact reference section:

```md
## Required Knowledge (XID)
- [Policy A](../knowledge/xxx.md#xid-<XID>)
- [Runbook B](../knowledge/yyy.md#xid-<XID>)
```

Rules:

- Always include `#xid-...` in cross-file links.
- Do not remove or rewrite existing XID blocks manually.
- Use `xref search/show` for retrieval; avoid guessing missing details.
- Treat `docs/` links and `*_refs` metadata as non-transitive by default:
  they identify available references, not a command to load every linked page.

## Runtime Fields For Stable Or Governed Skills

Before promoting to `stable` or `governed`, include the runtime fields (no guard
fields — the guard is ambient):

```md
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: <reusable base ability, e.g. software_development>
- tuning: <direct specialization, e.g. C# or C# + SQL>
- responsibility: <Skill-specific business use, e.g. implementation or quality check>
```

Do not add a guard section to `SKILL.md`; the context-direction guard is ambient
and applies to every Skill that loads external input.

## Closed-World Skills

The guard is ambient, so there is no guard to omit and no `guard_policy` to
declare. A Skill that loads no external context may note that in its
`constraints` for clarity, but no guard-omission declaration is required.

## Meta Validation And Load Readiness

Skill metadata is checked by maturity level as defined in
`docs/core/contracts/059_skill_maturity_governance.md#xid-4E7B8D9C1A20`.

- Only `trial`, `stable`, and `governed` Skills are eligible for runtime use.
- `draft` Skills are managed records, not load-ready procedures.
- Before opening `SKILL.md` for operational use, validate the selected `meta.md`
  and then open the runtime envelope.
- If validation fails at the intended maturity level, do not claim the Skill is
  ready for that maturity.
- Fix the metadata, add observation/governance links, or keep the Skill at a
  lower maturity.
- Review-oriented Skills fail `stable` and `governed` checks when they are left
  as `local_default`.

## Update Pattern

- If only skill behavior changed: update skill file, keep references.
- If canonical domain knowledge is added or materially changed: route the work
  through `skills/os/knowledge_ontology_management/meta.md#xid-83EDDDB5E158`,
  then verify Skill references still point to valid XIDs.
- If the knowledge change is only wording, formatting, or mechanical XID-link
  maintenance: update the fragment directly and verify references; ontology
  routing is not required.
- If a concept became semantically different: create a new XID and preserve compatibility via `xref deprecate`.

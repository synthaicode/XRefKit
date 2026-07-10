<!-- xid: 3DB05A0F5F5B -->
<a id="xid-3DB05A0F5F5B"></a>

# Skill Authoring with Xref

This page defines how to use `xref` when creating or updating a skill.
Goal: keep skill files small, and load only required domain knowledge on demand.

## Scope Split

- Skill files: behavior, procedure, I/O contract, guardrails.
- Domain knowledge files: factual content and source-backed details.
- Connection rule: skills reference domain knowledge by XID.

## Mixed Business Procedure Decomposition

When source material mixes business procedure, domain rules, examples, and
judgment criteria, do not convert it into one large Skill. First decompose the
material into control, judgment, and knowledge units.

The split exists because a Skill should carry the judgment method, while the
domain knowledge used by that judgment varies by case, tuning, local system,
and available evidence. If the domain corpus is copied into `SKILL.md`, most
runs load irrelevant context and the Skill becomes harder to reuse or audit.

Use this decomposition pass before writing or revising a Skill:

1. Preserve the input material as source or work evidence.
2. Mark each statement with one primary role:
   - `procedure`: an action the AI performs or a sequence it follows
   - `judgment`: a question, viewpoint, branch condition, acceptance criterion,
     or decision rule the AI applies
   - `knowledge`: a domain fact, glossary term, policy, local rule, standard,
     quality criterion, or source-backed example
   - `evidence`: a concrete observed case, source locator, artifact, log, or
     sample used to justify knowledge
   - `control`: startup, escalation, closure, handoff, or protocol behavior
     that belongs to the repository operating contract rather than this Skill
3. Put `procedure` and `judgment` in the Skill only when they are part of the
   reusable method for this Skill's `capability` / `tuning` /
   `responsibility`.
4. Put `knowledge` in `knowledge/` when it can be selected, reused, verified, or
   replaced independently from the Skill method.
5. Keep raw `evidence` in `sources/` or `work/`; promote only normalized,
   current, reusable knowledge into `knowledge/`.
6. Keep repository-wide `control` in `agent/`, `docs/core/`, or the workflow
   protocol. Do not restate it as Skill-local policy unless the Skill has a
   specific delta.
7. For each `judgment` in the Skill, declare the domain knowledge it may need as
   a `knowledge_slots` entry. Use a fixed `bind` only when the exact governance
   or domain fragment must not vary; otherwise use a `query` slot so the runtime
   can select the relevant base, pack, local, or MCP-supplied knowledge.

### Target Catalog And Lazy Selection

Many business procedures use the same judgment method against multiple possible
targets: services, screens, APIs, tables, document types, repositories,
departments, stakeholders, product areas, or local rule sets. The target is
often identified from the user's prompt or from current task artifacts, not from
the Skill itself.

Do not load every possible target into the Skill context. That creates context
pollution: irrelevant local facts, examples, exceptions, and historical notes
can bias the judgment even when the procedure is otherwise uniform.

Use a target-selection flow:

1. Extract target cues from the prompt and available task artifacts.
2. Build a metadata-only candidate list for the relevant target class.
   Candidate entries should carry stable identifiers such as XID, skill id,
   service name, domain, summary, applicability boundary, content hash, and
   source/catalog provenance.
3. Select the minimum target set needed for the current run.
4. Load full bodies only for selected target XIDs.
5. Record selected XIDs and content hashes in the run log or output evidence.
6. Leave unselected candidates as catalog metadata, not as loaded context.

This keeps the Skill centered on the uniform judgment while the target-specific
domain knowledge remains lazy and selectable. In MCP mode, this is the same
shape as:

```text
metadata list -> choose XID -> get_document_by_xid(XID)
```

In repository-native mode, use `xref search` / `xref show` the same way:
search produces candidates, and `show` loads only selected fragments.

For XRefKit v2 Local Domain Skills that extend Pack Skills, the resolver should
perform the first cataloging step automatically at extension-resolution time:
registered package and local knowledge become `available_domain_knowledge`
metadata in the effective Skill bundle, while full bodies remain unloaded until
the run selects the needed XIDs.

If target selection itself is non-trivial, make it an explicit planning
judgment. Record why the selected candidates were sufficient, and record
unselected-but-plausible candidates only when their exclusion affects risk,
unknowns, or handoff.

### Deferred Catalog Extraction

Initial authoring may temporarily keep target-specific knowledge inside a Skill
when the target set is still unclear, the first runnable behavior is more
important than clean catalog shape, or there is not yet enough observation to
name the target classes. Treat that as a temporary maturity state, not as the
desired final structure.

Use this deferred path:

1. Keep the mixed material in a `draft` or early `trial` Skill only long enough
   to observe how the judgment is used.
2. Mark embedded target-specific sections with an explicit extraction note:
   target class, likely catalog id, source basis, and why extraction is
   deferred.
3. After one or more runs reveal repeated target classes or alternative targets,
   extract those sections into `knowledge/` or local/package knowledge roots.
4. Assign or preserve XIDs, then let extension-time
   `available_domain_knowledge` cataloging expose the extracted targets as
   metadata.
5. Replace the embedded text in the Skill with `knowledge_slots` and XID-backed
   references.
6. Do not promote a Skill to `stable` or `governed` while reusable
   target-specific knowledge remains embedded in `SKILL.md`.

This path is for authoring velocity and observation. It must not become a way to
hide durable domain knowledge inside the Skill.

The unit of a Skill is a stable judgment method, not the shape of the original
document. The unit of Knowledge is a coherent reusable concept with a source
basis and applicability boundary, not a paragraph copied from the original
procedure.

### Split Heuristics

Use these checks when a statement is hard to classify:

| Statement asks or says | Target |
| --- | --- |
| "When doing this work, ask/check/compare/classify..." | Skill judgment method |
| "If condition A, choose path B..." | Skill judgment method, with required knowledge slot if A depends on domain rules |
| "This system/product/domain defines A as..." | Knowledge |
| "The rule is different for C# and Python..." | Knowledge, selected by tuning-specific slot |
| "This task must stop/escalate/record closure when..." | Repository control unless it is a Skill-specific delta |
| "In this past case, artifact X showed..." | Evidence in `sources/` or `work/`; promote only the reusable conclusion |
| "Always include this long checklist..." | Usually Knowledge; Skill should name the judgment axis and load the checklist only when needed |

### Output Of The Decomposition Pass

Before authoring the final files, write down the split as a compact map:

```md
## Skill Boundary
- skill_id:
- capability / tuning / responsibility:
- reusable judgment method:
- inputs:
- outputs:
- preconditions:

## Knowledge Candidates
- slot:
  - need:
  - selection: bind | query
  - target class:
  - candidate list source:
  - selected XIDs or new fragment proposal:
  - unselected candidates that matter:
  - deferred extraction note:
  - applicability boundary:

## Evidence And Source Basis
- source/work artifact:
- supports:
- unresolved source gaps:

## Not Skill-Local Control
- rule:
- canonical home: agent | docs/core | workflow protocol | knowledge
```

If the map cannot identify the reusable judgment method separately from the
domain corpus, keep the asset as a source/work note and do not promote it to a
Skill yet.

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

The context-direction guard is delivered at init through the XRefKit startup
contract in repository-native mode and through the startup contract pack in MCP
mode. In MCP mode, it is also re-attached to every fetched-content response. It
applies ambiently to every Skill that loads external input. New skills do not
compose or declare it: no `guard_policy`, no guard capability or knowledge
reference, and no SKILL.md guard section.

- Skills still assume lower-layer input is untrusted unless an explicit trust
  rule says otherwise; the ambient guard enforces the direction.
- See `docs/core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11`
  for the guard contract and
  `docs/core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8`
  for the current Skill/Knowledge operating model.

## Execution Mode Rule

`execution_mode` is required for `stable` and `governed` Skills.

For `trial`, the value may still be provisional.
For `draft`, it may be omitted.

- `local_default`: normal single-context execution
- `subagent_preferred`: prefer separate subagent execution when possible
- `subagent_required`: do not execute in the current context; use an isolated review context

Review-oriented skills should not use `local_default`.

## Capability Layering Rule

For `trial` or higher Skills that can be opened with `xrefkit skill run`, include
the runtime fields required by
`docs/core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61`.

Keep the authoring split simple:

- `capability_layering` and `workflow_protocol` bind the run to repository
  runtime controls.
- `capability`, `tuning`, and `responsibility` describe this concrete Skill's
  base ability, specialization, and business use (the legacy
  `role_responsibilities.executor` value is still accepted as the responsibility).
- `role_responsibilities` must not define `checker`, `quality_reviewer`, or
  `handoff_owner`; those roles are protocol-owned.
- `capability` names the base reusable ability, `tuning` its specialization,
  and `responsibility` the business use; together they are the Skill's meta
  identity and routing vocabulary, not evidence.
- `knowledge_slots` declare the knowledge the Skill needs: each slot either
  binds a fixed XID (`bind=`) or resolves dynamically at runtime against the
  base+local catalog by intent (`query=...; domain=...`). Do not hard-code C#
  knowledge in a Skill meant to be reusable for Python, and do not hard-code
  C# + SQL knowledge in a Skill meant to be reusable beyond that composite
  tuning — use a `query` slot so the right per-tuning knowledge is selected at
  runtime.

The canonical capability / tuning / responsibility definitions are in
`docs/reference/031_capability_layering.md#xid-8D50A972BA9F`.

Keep Skill bodies reusable: put the judgment or execution method in
`SKILL.md`, and put language-specific rules, framework behavior, API facts,
and long criteria lists in XID-backed `knowledge/`. If a Skill must be copied
only because the domain rules differ, the domain rules belong in `knowledge/`
instead. If a `bind` slot points at one language's criteria, treat the Skill as
language-specific. If bind slots point at a language combination such as
C# + SQL, treat the Skill as composite-tuning-specific — or use `query` slots so
the runtime resolves common, per-tuning, and cross-tuning knowledge separately.

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
python -m xrefkit xref search "<task or domain query>"
```

3. Read only required fragments:

```powershell
python -m xrefkit xref show <XID>
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
python -m xrefkit xref fix
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

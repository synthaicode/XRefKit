<!-- xid: 1F93A7C24010 -->
<a id="xid-1F93A7C24010"></a>

# Capability Routing for Agents

This page defines how an agent should route a user request through workflow, capability, skill, and domain knowledge.

## Routing Layers

- Workflow lives in [Docs Index](../docs/000_index.md#xid-56DD6EB68343) and related workflow pages.
- Capability definitions live in [Capabilities Index](../capabilities/000_index.md#xid-C14253A74C4F).
- Domain knowledge lives in [Knowledge Index](../knowledge/000_index.md#xid-23059118FBB9).
- Executable procedures live in `skills/` and are listed in `skills/_index.md`.

## Mandatory Routing Order

1. Identify the business stage or user intent.
2. Use semantic routing against workflow cues, skill indexes, and known fragments to narrow the candidate route.
3. Open the relevant workflow page in `docs/` by XID when a workflow already exists.
4. From the workflow page or routing cue, identify the required capability pages in `capabilities/`.
5. From the capability pages or routing cue, identify the matching skill in `skills/`.
6. Open the runtime envelope for only the selected Skill.
7. Load only the domain knowledge needed to execute the capability via `xref search` and `xref show`.
8. Execute the skill.
9. If work state must be tracked, apply management-table and metrics knowledge before closure.

## Intent-to-Workflow Mapping

- Business learning from partial human fragments, tacit knowledge extraction, or "ask me the next best question":
  - route to `skills/packs/business-intake/business_learning_interview/meta.md`
- Business intake requests with incomplete structure should default here first, not directly to scoping.
- Business intake scoping after a first business hypothesis already exists and the business unit is already scope-ready:
  - route to `skills/packs/business-intake/business_intake_scoping/meta.md`
- Business-intake startup must use the decision table in
  [Business intake pack entry](../docs/packs/business-intake/066_business_intake_pack_entry.md#xid-732E41DCA2E8):
  - no visible business seed -> ask for one seed before starting the pack
  - visible seed but unclear goal, judgment, ownership, or handoff ->
    `business_learning_interview`
  - visible target or candidate business unit with previous/current/next
    boundary evidence -> `business_intake_scoping`
  - only local screen clicks or personal habits -> recover the business goal and
    responsibility boundary before treating the request as scope-ready
- Investigation or impact analysis:
  - [Investigation workflow](../docs/workflows/032_investigation_workflow.md#xid-8B31F02A4001)
- Addition of canonical domain knowledge, promotion of source material into
  `knowledge/`, or a material revision to concept identity, scope,
  applicability, or semantic relationships:
  - route to `skills/os/knowledge_ontology_management/meta.md`
  - mechanical wording, formatting, and XID-link maintenance do not use this
    route
- .NET application structure analysis or change-impact investigation before design or implementation (structure, DI lifetimes, pipeline order, boundaries, attribute activation):
  - route to `skills/dotnet_change_analysis/meta.md`
  - the output is a change-analysis note handed to `planning_flow` or design work, not defect findings; suspected defects hand off to `skills/csharp_review/meta.md`, suspected security gaps to `skills/security_review/meta.md`
- Estimation, supplier check, or assumption clarification:
  - [Estimation workflow](../docs/workflows/035_estimation_workflow.md#xid-8B31F02A4004)
- Requirement drafting:
  - [Requirements workflow](../docs/workflows/036_requirements_workflow.md#xid-8B31F02A4005)
- Task decomposition or execution planning:
  - [Planning workflow](../docs/workflows/037_planning_workflow.md#xid-8B31F02A4006)
- Design or coding requests that include design-side structure such as DDL, UI specs, state transitions, API contracts, batch models, or auth matrices and still leave behavior unresolved:
  - route first to `skills/packs/constraint-derivation/constraint_derivation_index/meta.md`
  - apply every matching primary derivation Skill before finalizing design or code behavior
- Coding requests with partial design where implementation would otherwise need to guess missing edge behavior:
  - do not jump straight to manufacturing
  - derive and confirm unresolved behavior through the constraint-derivation pack first, then continue to design or manufacturing workflow
- Review requests that include generated C# code, DDL plus code, or code plus external-boundary behavior and ask whether the implementation hides assumptions, mismatches, or integration-only failure scenarios:
  - route first to `skills/packs/constraint-derivation/constraint_derivation_index/meta.md`
  - apply `code_constraint_derivation`, `cross_constraint_derivation`, or `integration_scenario_derivation` as appropriate before accepting the implementation as design-valid
- Review requests focused on C# implementation risks beyond Roslyn/compiler diagnostics — async hangs, synchronization, resource efficiency, attribute misuse, support lifecycle, error/exception paths, or time/culture correctness:
  - route to `skills/csharp_review/meta.md`
  - if the request also leaves design-side behavior unresolved, apply the constraint-derivation pack first, then run `csharp_review` on the implementation
  - security-scope findings discovered during the review hand off to `skills/security_review/meta.md`; design-assumption findings hand off back to the constraint-derivation pack
- Implementation or unit testing:
  - [Manufacturing workflow](../docs/workflows/033_manufacturing_workflow.md#xid-8B31F02A4002)
- Release-plan preparation:
  - [Release planning workflow](../docs/workflows/038_release_planning_workflow.md#xid-8B31F02A4007)
- CAB-style evaluation:
  - [CAB workflow](../docs/workflows/039_cab_workflow.md#xid-8B31F02A4008)
- Leak detection, closure confirmation, or out-of-scope escalation:
  - [Closure workflow](../docs/workflows/034_closure_workflow.md#xid-8B31F02A4003)

## Capability-to-Skill Rule

- Capability pages define what must be done.
- Skill pages define how to execute it.
- Semantic routing may select a Skill directly from strong intent cues before a full capability chain is opened, but the chosen Skill must still remain consistent with repository layering and business boundary rules.
- For business-task intake, the default semantic path is:
  - learn the business from fragments
  - identify the smallest viable business unit
  - then scope that unit
- If multiple capabilities form one business step, prefer the phase skill that already composes them.
- If no suitable composed skill exists, use the nearest matching skill and load the missing capability definition explicitly.
- If processing can be separated into disjoint scopes and parallel execution does not create handoff or consistency risk, prefer subagent decomposition by scope.
- Subagent decomposition must preserve explicit scope boundaries; do not split work in a way that changes owner, evidence basis, or closure responsibility.
- Review-oriented or `judgment`-heavy skills should prefer separate subagent execution so the reviewer runs in a different context from the producer.
- When a skill `meta.md` declares `execution_mode: subagent_preferred` or `execution_mode: subagent_required`, validate that metadata before loading and follow the declared execution mode.
- The check phase MUST be advanced deterministically with `python -m fm skill verify --log <run-log>` at every maturity level, including `trial` / `local_default`; `execution_mode` relaxes the executor side only, never the check side. Deterministic verification is context-independent by construction and uses the assigned `checker` role, which must differ from the `executor` role.

## Model Tier Dispatch Rule

Skill `meta.md` may declare an optional `model_tier` field that controls which
model class executes the skill. This separates cost control (which model) from
context control (`execution_mode`, which decides isolation).

- `model_tier: light` — mechanical, routing, or template-bound work. Dispatch
  the execution phase to the `skill-executor-light` subagent
  (`.claude/agents/skill-executor-light.md`, small fast model).
- `model_tier: standard` — analysis, review, and derivation work. Dispatch the
  execution phase to the `skill-executor-standard` subagent (balanced model).
- `model_tier: heavy` — judgment-heavy synthesis, cross-structure analysis, or
  writing-quality work. Execute in the main context, or in the
  `skill-executor-heavy` subagent (inherits the main model) when
  `execution_mode` requires isolation.
- When `model_tier` is absent, treat the skill as `heavy` (main-context model).

Dispatch rules:

- For `light` and `standard`, prefer subagent execution even when
  `execution_mode` is `local_default` — `local_default` permits main-context
  execution but does not require it, and tier dispatch is how the cheaper
  model is realized.
- Skills that require direct human interaction during execution (for example
  interview-style skills) stay in the main context regardless of tier.
- `model_tier` never affects the check side. The check phase is
  workflow-progression verification (worklist completion, run-log integrity,
  artifact recording and linkage, role separation) and is advanced
  deterministically by `python -m fm skill verify`, not by a model, whatever
  the executor tier. Domain-level quality review is not the check phase's job —
  it belongs to the quality phase.
- The quality phase is the quality axis, mandatory at closure for `standard`
  and `heavy` (optional for `light` / untiered). Declare acceptance check items
  as `check`-kind artifacts at planning; run the independent `skill-quality`
  subagent (defined in `.claude/agents/skill-quality.md`) under the
  `quality_reviewer` role to set each to pass (`done`) or fail (`blocked`).
  Because a subagent cannot start another subagent, the quality subagent does
  generic acceptance verification only; when a check item names a domain-review
  Skill (e.g. `csharp_review`), the main session runs that Skill and links its
  verdict back. The quality reviewer role must differ from the executor.
- Tool-type quality checks are content-conditional, not uniform. A skill
  declares it can apply such a check by referencing the capability (e.g.
  `CAP-QA-011` for the Roslyn analyzer); per run, `python tools/cs_scope_probe.py`
  decides whether it applies, and the item is marked `na` when out of scope. The
  quality subagent runs deterministic tools itself; see
  [Roslyn analyzer quality-check applicability](../knowledge/source_analysis/150_roslyn_analyzer_quality_check_applicability.md#xid-A1B243BF7D5D).
- If a lower-tier executor reports escalation (work exceeded its tier), re-run
  the execution phase one tier up; do not let the lower tier guess.

## Knowledge Loading Rule

When a skill needs evidence or local rules:

1. Search: `python -m fm xref search "<query>"`
2. Read: `python -m fm xref show <XID>`
3. Cite the XID-backed fragment in the result or work log.

Never treat capability definitions as domain evidence. Capability pages are control definitions; evidence belongs in `knowledge/`.

## Control Rule

If the task produces `unknown`, `out_of_scope`, or closure-state questions, load:

- [Management table schema](../knowledge/organization/110_management_table_schema.md#xid-7A2F4C8D1101)
- [Metrics definition](../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

Then use the control path defined by:

- [Closure workflow](../docs/workflows/034_closure_workflow.md#xid-8B31F02A4003)
- `skills/management_table_control/SKILL.md`

## Related

- [Agent Entry](000_agent_entry.md#xid-0B5C58B5E5B2)
- [Startup xref routing policy](../docs/core/contracts/011_startup_xref_routing.md#xid-6C0B62D6366A)
- [Capability layering](../docs/reference/031_capability_layering.md#xid-8D50A972BA9F)

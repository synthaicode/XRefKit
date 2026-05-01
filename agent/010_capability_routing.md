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
  - route to `skills/business_learning_interview/meta.md`
- Business intake requests with incomplete structure should default here first, not directly to scoping.
- Business intake scoping after a first business hypothesis already exists and the business unit is already scope-ready:
  - route to `skills/business_intake_scoping/meta.md`
- Investigation or impact analysis:
  - [Investigation workflow](../docs/032_investigation_workflow.md#xid-8B31F02A4001)
- Estimation, supplier check, or assumption clarification:
  - [Estimation workflow](../docs/035_estimation_workflow.md#xid-8B31F02A4004)
- Requirement drafting:
  - [Requirements workflow](../docs/036_requirements_workflow.md#xid-8B31F02A4005)
- Task decomposition or execution planning:
  - [Planning workflow](../docs/037_planning_workflow.md#xid-8B31F02A4006)
- Implementation or unit testing:
  - [Manufacturing workflow](../docs/033_manufacturing_workflow.md#xid-8B31F02A4002)
- Release-plan preparation:
  - [Release planning workflow](../docs/038_release_planning_workflow.md#xid-8B31F02A4007)
- CAB-style evaluation:
  - [CAB workflow](../docs/039_cab_workflow.md#xid-8B31F02A4008)
- Leak detection, closure confirmation, or out-of-scope escalation:
  - [Closure workflow](../docs/034_closure_workflow.md#xid-8B31F02A4003)

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

- [Closure workflow](../docs/034_closure_workflow.md#xid-8B31F02A4003)
- `skills/management_table_control/SKILL.md`

## Related

- [Agent Entry](000_agent_entry.md#xid-0B5C58B5E5B2)
- [Startup xref routing policy](../docs/011_startup_xref_routing.md#xid-6C0B62D6366A)
- [Capability layering](../docs/031_capability_layering.md#xid-8D50A972BA9F)



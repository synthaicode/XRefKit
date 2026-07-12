<!-- xid: 14733B9B4F61 -->
<a id="xid-14733B9B4F61"></a>

# Change Impact Investigation Decomposition

This page defines how change-impact investigation is expressed through Skills,
Knowledge, and Business Pack placement when the method is reusable but its
evidence depends strongly on the target domain.

Related:

- [Skill and Knowledge operating model](../core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
- [Change analysis Skill usage](../guides/054_change_analysis_skill_usage.md#xid-C5A8F13D7E21)

## Core Point

Change-impact investigation uses three current repository surfaces:

- **Skill**: owns the executable investigation method, output contract,
  evidence handling, and unknown handling.
- **Knowledge**: supplies domain-specific viewpoints, rules, dependency types,
  activation conditions, and evidence categories.
- **Business Pack**: places the investigation in business progression and
  defines what consumes its output next.

The Skill's capability / tuning / responsibility meta triad identifies and
routes the method. It is metadata on the Skill, not a separate work artifact.

## Responsibility Split

| Surface | What it owns | Example |
| --- | --- | --- |
| Skill | reusable investigation procedure for a technical surface | `dotnet_change_analysis` |
| Knowledge | criteria for dependencies, boundaries, activation, evidence, and test viewpoints | .NET structure, custom-framework, and external-definition viewpoints |
| Business Pack | business purpose, progression, handoff target, and required outputs | investigation before requirements, planning, or design |

## Reusable Skill Method

The investigation Skill should consistently:

- identify the requested change trigger
- enumerate direct impact targets
- enumerate indirect dependencies
- separate observed evidence from inference
- preserve `unknown` instead of guessing
- produce downstream test viewpoints
- record evidence and handoff artifacts through the workflow protocol

The method remains reusable because domain-specific facts are resolved from
Knowledge rather than copied into the Skill body.

## Domain-Tuned Knowledge

Knowledge determines what the Skill looks for in each target context:

| Viewpoint | Examples |
| --- | --- |
| dependency | code call graph, database relation, XML mapping, event route, batch chain, approval flow |
| activation | runtime registration, dependency injection, annotations, XML enablement, schedules, feature flags |
| boundary | module, service, job, screen, table, document, approval step |
| evidence | source code, definitions, schema, logs, configuration, operations documentation, business rules |
| testing | UI behavior, transaction effects, batch timing, retries, report output, downstream integration |

## .NET Line-Of-Business Example

- Skill:
  [dotnet_change_analysis](../../skills/dotnet_change_analysis/SKILL.md#xid-D94E3B3A7C11)
- Knowledge:
  [Common source analysis criteria](../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001),
  [Custom framework common criteria](../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002), and
  [Dotnet change analysis viewpoints](../../knowledge/source_analysis/120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)
- Typical dependencies: controller, application service, repository, database,
  logging, batch, API, and tests
- Typical activation evidence: route registration, service wiring, attributes,
  and startup configuration

## External-Definition-Driven Example

- Skill: `dotnet_change_analysis`, using external-definition viewpoints
- Knowledge:
  [Common source analysis criteria](../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001),
  [Custom framework common criteria](../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002), and
  [External-definition change analysis viewpoints](../../knowledge/source_analysis/130_external_definition_change_analysis_viewpoints.md#xid-4D91A26BE301)
- Typical dependencies: definition-to-code mapping, load order, consuming code,
  transition targets, validation, schedules, and downstream behavior
- Activation rule: file presence alone is not evidence of runtime activation;
  verify the consuming mechanism and activation condition

## Practical Rule

1. Route to the investigation Skill whose tuning and applicability match the
   target technical surface.
2. Open the Skill through the runtime envelope.
3. Resolve only the domain Knowledge needed for the target context.
4. Execute the reusable investigation method against that evidence.
5. Record outputs, unknowns, verification, and handoff through the workflow
   protocol.
6. Let the Business Pack or subsequent semantic routing determine the next
   Skill from the resulting state.

Do not make the Skill self-contained by copying domain criteria into it. Do not
run the method without evidence appropriate to the target domain.

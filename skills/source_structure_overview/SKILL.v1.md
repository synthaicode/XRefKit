---
schema_version: 1
skill_id: source_structure_overview
xid: A6E3C9F2B470
summary: produce a reusable whole-system .NET source-structure overview with boundaries, flows, naming evidence, and validity limits
applies_when:
- user needs a baseline explanation of how a brownfield .NET repository, service, module family, or application works structurally before asking specific change-impact questions; use before `dotnet_change_analysis` when the target's current source structure knowledge is missing, stale, or too narrow
exclusions:
- do not answer a specific change-impact proposition or publish incomplete analysis as canonical Knowledge
inputs:
- target repository, service, solution, project, or directory; explicit source scope boundary; optional known domain knowledge catalog; optional intended publication mode for later source-structure finding registration
outputs:
- Markdown source-structure overview with system purpose, runtime units, major subsystem map, startup/composition flow, request/event/job flows, state and persistence boundaries, extension/plugin/feature mechanisms, Brownfield API Naming Extractor output for externally visible and data-flow-relevant naming surfaces, configuration/tenant/environment variation, external boundaries, key structural authorities, reusable domain-knowledge metadata, validity/recheck conditions, unknown structure areas, and completion-control result; when the confirmed scope cannot be completed, output an incomplete-analysis cause review instead of a source-structure overview
criteria:
- id: confirmed_scope
  statement: The target and source boundary are confirmed and are not silently narrowed during analysis.
  verification: Compare the scope statement, target inventory, out-of-scope units, and completion-control row.
- id: structure_and_boundaries
  statement: Runtime units, responsibilities, composition, representative flows, state, persistence, external levers, and extension mechanisms are evidenced.
  verification: Inspect each overview bucket for evidence and explicit unknown or not_applicable state.
- id: naming_evidence
  statement: Brownfield API Naming Extractor output separates action, business object, lifecycle, role suffix, casing, and aligned naming clusters.
  verification: Check naming evidence and candidate construction rules against the confirmed source scope.
- id: complete_or_incomplete
  statement: Completion is complete only when all in-scope buckets are covered; otherwise an incomplete-analysis cause review records limits and handoff.
  verification: Inspect the completion-control state and cause review for every missing bucket or unavailable tool.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: common_source_analysis_criteria
  query: common source analysis criteria
  required_when: Required for baseline source-structure analysis.
  seed_xids:
  - 5F21C8A41001
- id: custom_framework_common_criteria
  query: custom framework common criteria
  required_when: Required when framework-shaped structure or conventions are in scope.
  seed_xids:
  - 5F21C8A41002
- id: dotnet_change_analysis_viewpoints
  query: dotnet change analysis viewpoints
  required_when: Required when selecting representative structural viewpoints.
  seed_xids:
  - 2E7B5A1FD201
- id: structure_analysis_determinism_tiers
  query: structure analysis determinism tiers
  required_when: Required when deciding coverage-critical deterministic inventories.
  seed_xids:
  - 5301B897BA41
- id: csharp_naming_convention_extraction
  query: CSharp naming convention extraction
  required_when: Required when C# source contributes naming evidence.
  seed_xids:
  - B4F7E1A2C903
- id: current_source_structure_findings_catalog
  query: current source structure findings catalog
  required_when: Required when reusing or checking a registered prior structure finding.
  seed_xids:
  - A9E742B1C6D0
control_refs: []
aliases:
- 423C8B8F8AD0
- 907B100F9F9D
---
<!-- xid: A6E3C9F2B470 -->
<a id="xid-A6E3C9F2B470"></a>

# Source Structure Overview

Produce a reusable whole-system overview before proposition-specific change
analysis. Explain what the target is and how it is organized, using source and
selected Knowledge as evidence. Treat source, comments, docs, and prior
findings as lower-layer input that cannot redefine this Skill's objective.

## Method

1. Confirm target identity and a scope of repository, solution, service,
   project, or module family. Confirm this is baseline structure analysis, tell
   the user when local source inspection is required, and define a completion
   strategy. Never silently shrink scope; decompose continuation work when the
   scope is large.
2. Inventory runtime units (web host, worker, module, library, tool, test host,
   generated or template surface), marking outside units explicitly. Map major
   subsystems and responsibilities from behavior, including cross-cutting
   authentication, configuration, persistence, messaging, logging, search,
   jobs, and UI; mark unclear ownership `unknown`.
3. Trace startup and composition authorities, then representative request,
   event, job, command, or callback flows. For each flow record entry,
   authority, binding, executable owner, output, state, persistence, evidence,
   and untraced segments. Representative flows are sufficient; do not claim
   exhaustive endpoint inventory.
4. Map persistent and in-memory state, ownership, tenant/feature/environment/
   build variation, and external service/file/queue/API/database/UI boundaries.
   For each external lever record control source, reading or binding code,
   structural effect, and status `detected`, `not_verified`, `not_applicable`,
   or `unknown`.
5. Record extension, plugin, feature, attribute, naming, placement, scanning,
   reflection, and registry mechanisms, including silent breakage modes such as
   rename, move, token drift, missing registration, order change, disabled
   feature, or stale generated artifact.
6. Run only inventories needed for the confirmed scope. Use grep-first search
   for text-greppable structure and deterministic tools for coverage-critical
   facts: structure graph attributes/DI/invocations/declarations, dependency
   direction and ownership, test reachability, and the C# naming profile. If a
   needed inventory cannot run, record an `unknown` and do not claim complete
   coverage.
7. Extract Brownfield API Naming evidence for routes, methods, controllers,
   DTOs, commands, queries, handlers, permissions, events, jobs, persistence,
   topics, queues, tables, schemas, configuration keys, environment variables,
   generated identifiers, and protocols. Separate action verbs, business
   objects, lifecycle/state, role/boundary suffixes, casing/affixes, and
   clusters that must stay aligned. Produce construction rules only where
   evidence supports them; do not invent names for a specific change.
8. Record reusable Knowledge metadata: target, scope, overview kind,
   source basis, verified date, producer, covered subsystems and flows,
   selected inputs, validity conditions, recheck triggers, and unresolved
   verification.

## Complete versus incomplete

Every mandatory section is `done`, `not_applicable`, or `unknown`. An in-scope
`unknown` blocks normal completion until resolved, explicitly scoped out, or
escalated to its human owner. The completion-control row must state
`complete`, `continue_required`, `blocked`, or `failed`.

When the confirmed scope cannot be completed, produce an incomplete-analysis
cause review instead of an overview. Classify the primary cause as
`context_size`, `scope_too_large`, `instruction_ambiguous`, `tool_unavailable`,
`source_unavailable`, or `evidence_conflict`; include confirmed scope,
completed and incomplete buckets, missing evidence/tool output, blocking
reason, next action, and handoff owner. Do not publish that review as
canonical structure Knowledge. Handoff publication to
`source_structure_findings_registration` only after completion and validity
conditions are explicit.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: source_structure_overview

## Purpose

Produce a reusable whole-system source-structure overview for a target .NET
repository, service, solution, project, or module family.

Use this Skill before proposition-specific change analysis when the current
source structure is missing, stale, or too narrow. The output becomes domain
knowledge that later Skills, especially `dotnet_change_analysis`, can select by
XID as target source-structure context.

This Skill does not answer "what must change for this specific modification?"
That is `dotnet_change_analysis`. This Skill answers "how does this target work
structurally, and under what conditions can this overview be reused?"

## Required Knowledge (XID)

- [Common source analysis criteria](../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Custom framework common criteria](../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002)
- [Dotnet change analysis viewpoints](../../knowledge/source_analysis/120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)
- [Structure-analysis determinism tiers](../../knowledge/source_analysis/121_structure_analysis_determinism_tiers.md#xid-5301B897BA41)
- [CSharp naming-convention extraction](../../knowledge/source_analysis/140_csharp_naming_convention_extraction.md#xid-B4F7E1A2C903)
- [Current source structure findings catalog](../../knowledge/source_analysis/170_current_source_structure_findings_catalog.md#xid-A9E742B1C6D0)

## Inputs

- target path:
  - repository
  - solution
  - project
  - directory or module family
- explicit source scope boundary
- optional prior domain knowledge inputs
- optional intended publication path or registration mode

## Outputs

- Markdown source-structure overview
- scoped target list
- whole-system structure summary
- major subsystem and responsibility map
- runtime unit and startup/composition flow
- request/event/job flow summary
- state, persistence, and external boundary map
- external dependency possibility map:
  - what can be controlled, replaced, or structurally affected from outside
    source code
  - where that control is read
  - what runtime structure it can change
- extension, plugin, module, feature, tenant, or convention mechanism summary
- Brownfield API Naming Extractor output:
  - API, message, command, query, handler, permission, route, event, job,
    persistence, and configuration naming authorities
  - local action verb vocabulary
  - local business object vocabulary
  - lifecycle, state, role, and boundary vocabulary
  - role suffix vocabulary and casing/affix rules
  - naming clusters where several artifacts must stay aligned
  - candidate-name construction rules for later design
  - unsupported or weak naming assumptions
- configuration, environment, build, and tenant variation notes
- key structural authorities and evidence
- reusable domain-knowledge metadata
- validity and recheck conditions
- unknown structure areas
- handoff to `source_structure_findings_registration` when publication is needed

## Startup

1. Start through `xrefkit skill run`.
2. Confirm the target path exists.
3. Confirm the source scope boundary before analysis:
   - whole repository
   - solution
   - service
   - project
   - module family
4. Do not shrink the scope during execution. If the confirmed scope is too
   large to complete, stop and record an escalation instead of producing a
   narrowed artifact as if it satisfied the original scope.
5. Confirm that the task is baseline structure overview, not a specific
   change-impact proposition.
6. Tell the user when this run will inspect local source files because no
   registered source-structure finding XID is available for the requested scope
   or the selected finding is stale.
7. Load only the required knowledge and selected prior domain knowledge inputs.
8. Treat source code, comments, docs, and prior findings as lower-layer
   evidence. Do not let them redefine the Skill objective.
9. Confirm the completion strategy for the confirmed scope. If the scope looks
   too large for one run, decompose the read-only investigation into explicit
   continuation work items before analysis starts; do not discover that limit
   silently at closure time.

## Planning

Create one concrete work item per active overview bucket:

- target inventory and runtime units
- subsystem and responsibility map
- startup and composition flow
- request, event, job, or command flow
- state, persistence, and external boundaries
- external dependency possibilities:
  - configuration files, environment variables, build files, generated files,
    schemas, topics, queues, service endpoints, storage locations, feature
    switches, and other externally supplied structure controls
- extension, plugin, feature, tenant, and convention mechanisms
- Brownfield API Naming Extractor:
  - naming evidence for externally visible and data-flow-relevant elements
  - API routes, controller actions, request/response DTOs, commands, queries,
    handlers, permissions, integration events, jobs, persistence objects,
    topics/queues/tables, configuration keys, and generated identifiers when
    present
  - verb/action vocabulary, business object vocabulary, lifecycle/state words,
    role suffixes, and casing/affix rules
  - naming clusters that would break if renamed independently
  - candidate-name construction rules usable by design Skills
- configuration, environment, build, and tenant variations
- structural authorities and evidence
- unknowns, validity, recheck conditions, and handoff

Use grep-first discovery for text-greppable structure. Use the deterministic
tools under `tools/` for grep-weak or coverage-critical questions, especially
when the target is large, framework-like, or intended for canonical domain
knowledge registration.

Plan only the inventories needed for the confirmed scope:

- custom attribute values: `tools/structure_graph --attributes` +
  `tools/attribute_inventory_report.py#xid-86FEF434AF94`
- DI lifetime graph and captive-dependency candidates:
  `tools/structure_graph --di` + `tools/di_registration_report.py#xid-66D9070B4548 --graph`
- pipeline, config, discovery, logging, and transaction call shapes:
  `tools/structure_graph --invocations` +
  `tools/invocation_facts_report.py#xid-7577F6A5C6AC`
- async/static state/lock/DbSet/#if/TFM facts:
  `tools/structure_graph --decl` + `tools/declaration_facts_report.py#xid-4F003AE89B45`
- dependency direction, fan-in/out, and writes ownership:
  `tools/structure_graph_report.py#xid-13E32D7ED058`
- test-to-SUT reachability when test boundary is in scope:
  `tools/test_coverage_reach.py#xid-CAD4CA8E817C`
- C# naming convention profile:
  `tools/csharp_naming_profile.py#xid-2FA1A52CFEE6`

If a needed deterministic inventory cannot run, record that as an `unknown`
concern. Do not treat the overview as complete for a scope that depends on the
missing inventory.

Plan a completion-control row for the confirmed scope. It must record how the
run will decide one of these states:

- `complete`: all in-scope structure buckets are covered or explicitly not
  applicable.
- `continue_required`: analysis is not complete, but the next concrete
  investigation rows are known.
- `blocked`: analysis cannot continue without human input or an external
  environment change.
- `failed`: analysis stopped because the Skill instructions, tool setup, target
  access, or context budget were insufficient.

## Execution

### Target Inventory

- Identify the repository, solution, project, and directory boundaries in scope.
- List the major runtime units:
  - web host
  - worker
  - module
  - library
  - tool
  - test host
  - generated or template surface
- Mark units outside scope explicitly instead of silently ignoring them.

### Whole-System Structure Summary

Write a short explanation of what the target is and how it is organized before
listing details. This section is mandatory. It must be understandable without a
specific change request.

### Subsystem And Responsibility Map

- Identify major subsystems and their responsibilities.
- Derive responsibilities from behavior evidence, not only names or folders.
- Record cross-cutting subsystems such as authentication, configuration,
  persistence, messaging, logging, search/indexing, background jobs, or UI.
- Mark duplicated or unclear responsibility ownership as `unknown`.

### Startup And Composition Flow

- Identify what starts the system or scoped runtime.
- Record how services, modules, features, routes, handlers, controllers,
  commands, jobs, or plugins are composed.
- Identify local structural authorities such as manifests, attributes, module
  descriptors, configuration files, builder calls, generated files, database
  metadata, naming conventions, or external framework code.

### Runtime Flows

Record representative request, event, job, command, or callback flows.

For each flow, capture:

- entry identity
- structural authority
- binding mechanism
- executable owner
- output boundary
- state boundary
- persistence boundary
- evidence
- unknown or untraced segments

Do not require exhaustive endpoint inventory. Prefer representative flows that
explain the architecture.

### State And Boundary Map

- Identify persistent state and ownership boundaries.
- Identify in-memory runtime state that controls behavior.
- Identify tenant, feature, environment, build-configuration, or deployment
  variations that change structure.
- Identify external service, file, queue, API, database, or UI boundaries.

### External Dependency Possibility Map

Identify which parts of the target structure can depend on, be replaced by, or
be controlled from outside the source code. The purpose is not to verify the
current runtime environment or connect to external services; the purpose is to
list the external levers that can change runtime structure.

For each external dependency candidate, record:

- dependency item:
  - configuration section or key
  - environment variable
  - build property, target, package source, or compile include/exclude rule
  - external file, schema, generated artifact, template, or manifest
  - service endpoint, broker, database, cache, queue, topic, stream, table,
    index, bucket, filesystem path, state store, route, plugin, or feature flag
  - externally significant identifier such as topic name, schema subject,
    consumer group, application id, store name, route name, table/stream/index
    name, generated type name, or protocol name
- control source: config/env/file/build/code convention/external service
- reading or binding code
- structural effect:
  - startup/composition
  - module/feature activation
  - routing or handler binding
  - serialization/schema contract
  - persistence/state ownership
  - cache/state-store identity
  - messaging/topic/queue contract
  - external API/client boundary
  - build/runtime variant
- verification status:
  - `detected`: source proves the external dependency possibility exists
  - `not_verified`: the live value or external service was not checked
  - `not_applicable`: no such external dependency class applies in scope
  - `unknown`: source suggests a dependency but the control source or structural
    effect cannot be identified

Do not collapse this into a generic "external boundary" sentence. The output
must let a later Skill decide what external values or files may need to be
checked before planning a change.

### Extension And Convention Mechanisms

- Identify where runtime wiring depends on plugins, modules, features,
  attributes, naming, placement, assembly scanning, reflection, or registries.
- Record what each mechanism activates.
- Record silent breakage modes such as rename, move, token drift, missing
  registration, order change, disabled feature, or stale generated artifact.

### Brownfield API Naming Extractor

When the source scope contains externally visible APIs, messages, commands,
queries, jobs, persistence contracts, configuration contracts, or data-flow
boundaries, extract local naming rules as part of the baseline structure
overview.

This extractor is part of `source_structure_overview`, not `design_flow`.
`design_flow` consumes the extractor output from the registered source
structure finding and uses it to propose names for new or changed design
elements.

For each in-scope API or data-flow boundary, capture naming evidence from:

- route segments, HTTP methods, controller names, action names, request DTOs,
  response DTOs, and authorization/permission identifiers
- command, query, handler, validator, event, job, scheduler, module, service,
  repository, aggregate, rule, and DTO names
- topic, queue, stream, table, schema, file, configuration key, environment
  variable, generated type, protocol, and external identifier names

The output must separate these vocabularies:

- action verbs such as `Create`, `Change`, `Edit`, `Accept`, `Reject`, `Buy`,
  `Renew`, `Register`, `Mark`, `Expire`, `SignUp`, `SignOff`, `Set`, `Enable`,
  or `Disable`
- business object terms such as entities, aggregates, value objects, events,
  external resources, files, topics, queues, or persisted records
- lifecycle/state terms such as `Pending`, `Accepted`, `Rejected`, `Paid`,
  `Expired`, `Active`, `Inactive`, `Confirmed`, `Cancelled`, or local
  equivalents
- role and boundary suffixes such as `Request`, `Response`, `Command`,
  `Query`, `Handler`, `Validator`, `Dto`, `Event`, `Job`, `Module`,
  `Repository`, `Rule`, `Options`, or `Configuration`
- casing and affix rules from the deterministic naming profile when C# source
  is in scope

Also record naming clusters that must stay aligned. Examples include:

- route segment + controller action + request DTO + command/query + handler
- permission constant + authorization attribute + endpoint
- integration event + inbox/outbox stored type name + handler
- job name + scheduler registration + command
- table/schema/topic/queue/configuration key + code binding point

Produce candidate-name construction rules for later design, but do not invent
names for a specific change proposition. A construction rule describes how to
combine the local action vocabulary, business object vocabulary, lifecycle or
state vocabulary, and suffix vocabulary. If the evidence does not support a
rule, record the naming area as `unknown` or `not_applicable`.

### Domain Knowledge Metadata

Record metadata that lets this output be reused as domain knowledge:

- target identity
- source scope
- overview kind: `source-structure-overview`
- source basis
- last verified date
- producer Skill
- covered subsystems
- covered runtime flows
- selected prior knowledge inputs
- validity conditions
- recheck triggers
- unresolved verification

### Unknowns

Every mandatory section must be either `done`, `not_applicable`, or `unknown`.
Use `unknown` when evidence is missing, when a runtime path is not traced, or
when a framework-shaped assumption has not been confirmed from local source.

An in-scope `unknown` is a closure blocker unless it is resolved, explicitly
declared out of scope by the confirmed source scope, or escalated to the human
owner. Do not convert unresolved in-scope unknowns into normal completion.

### Incomplete Analysis Cause Review

If the run cannot complete the confirmed scope, produce an incomplete-analysis
cause review instead of a source-structure overview. Classify the primary cause
and supporting evidence:

- `context_size`: the target can be analyzed, but the current model/session
  context cannot hold the needed evidence and synthesis at once.
- `scope_too_large`: the confirmed source scope is too broad for a single run
  even with decomposition; a smaller human-approved target boundary is needed.
- `instruction_ambiguous`: the Skill or task instructions do not define the
  required coverage, publication threshold, or completion boundary clearly
  enough.
- `tool_unavailable`: required deterministic tools, build/restore, target
  checkout, or symbols are unavailable.
- `source_unavailable`: required source files, generated artifacts, external
  framework source, or runtime configuration are unavailable.
- `evidence_conflict`: available evidence contradicts itself and cannot be
  resolved without human decision.

The cause review must include:

- confirmed source scope
- completed buckets
- incomplete buckets
- missing evidence or tool output
- why the missing part blocks completion
- whether the next action is continue, rerun with decomposition, fix tool/source
  access, clarify instructions, or ask for human scope decision
- handoff owner

Do not publish an incomplete-analysis cause review as canonical source
structure knowledge.

## Output Shape

Use this shape or an equivalent structure:

```md
# Source Structure Overview: <target>

## Summary

## Scope

## Runtime Units

## Major Subsystems And Responsibilities

## Startup And Composition Flow

## Runtime Flow Summary

## State, Persistence, And External Boundaries

## External Dependency Possibilities

## Extension, Feature, Plugin, Tenant, And Convention Mechanisms

## Brownfield API Naming Extractor

## Key Structural Authorities

## Domain Knowledge Metadata

## Validity And Recheck Conditions

## Unknown Structure Areas

## Handoff
```

## Monitoring And Control

- Treat a missing whole-system summary as a failed overview.
- Treat missing subsystem, startup, runtime-flow, state-boundary, extension, or
  unknown sections as analysis leaks.
- Treat a missing external-dependency possibility map as an analysis leak when
  the target has configuration, build files, generated artifacts, schemas,
  external services, queues, topics, routes, storage, plugins, or other
  externally supplied structure controls.
- Treat missing Brownfield API Naming Extractor output as an analysis leak when
  the target has externally visible API, message, job, persistence,
  configuration, or data-flow naming surfaces.
- Treat scope narrowing after startup as escalation, not completion.
- Treat an in-scope unknown that affects downstream planning or design as a
  closure blocker.
- Treat a partial overview emitted without an incomplete-analysis cause review
  as a failed Skill run.
- Do not convert this Skill into proposition-specific impact analysis.
- Do not claim that a structure is framework-standard when local source changes
  or wraps the framework behavior.
- Keep generated output reusable as domain knowledge; avoid one-off task notes
  that cannot be selected later by XID.

## Closure Gate

Closure is allowed only when all of the following are recorded:

- target identity and source scope
- whole-system structure summary
- major subsystem map
- startup/composition flow
- at least one representative runtime flow or an explicit `unknown`
- state/persistence/external boundary map or explicit `not_applicable`
- external dependency possibility map or explicit `not_applicable`
- extension/convention mechanism summary or explicit `not_applicable`
- Brownfield API Naming Extractor output or explicit `not_applicable`
- key structural authorities with evidence
- validity and recheck conditions
- unknown structure areas, with each item classified as `resolved`,
  `out_of_scope`, or `escalated`
- completion-control result: `complete`
- output artifact path
- evidence artifacts
- handoff target:
  - `source_structure_findings_registration` for canonical knowledge
    registration
  - `dotnet_change_analysis` for proposition-specific change analysis

Closure is not allowed when an in-scope structure area remains simply
`unknown`. If the target is too large to finish, close by escalation and do not
publish the artifact as canonical domain knowledge.

If completion-control result is `continue_required`, `blocked`, or `failed`,
closure as a source-structure overview is forbidden. The run may only close as
an incomplete-analysis cause review with the cause classification, evidence,
next action, and handoff owner recorded.

## Reporting Contract (共通報告)



- reporting_profile: artifact_traceability

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: produce a reusable whole-system source-structure overview for a target repository or service before proposition-specific change analysis

- use_when: user needs a baseline explanation of how a brownfield .NET repository, service, module family, or application works structurally before asking specific change-impact questions; use before `dotnet_change_analysis` when the target's current source structure knowledge is missing, stale, or too narrow

- input: target repository, service, solution, project, or directory; explicit source scope boundary; optional known domain knowledge catalog; optional intended publication mode for later source-structure finding registration

- output: Markdown source-structure overview with system purpose, runtime units, major subsystem map, startup/composition flow, request/event/job flows, state and persistence boundaries, extension/plugin/feature mechanisms, Brownfield API Naming Extractor output for externally visible and data-flow-relevant naming surfaces, configuration/tenant/environment variation, external boundaries, key structural authorities, reusable domain-knowledge metadata, validity/recheck conditions, unknown structure areas, and completion-control result; when the confirmed scope cannot be completed, output an incomplete-analysis cause review instead of a source-structure overview

- constraints: do not answer a specific change-impact proposition; do not flatten the target into framework labels; explain the whole target structure before local detail; do not shrink the confirmed source scope during execution; use deterministic `tools/` inventories for grep-weak or coverage-critical structure questions when needed; extract Brownfield API Naming Extractor output when externally visible or data-flow-relevant naming surfaces are in scope; record unknowns instead of inventing missing runtime paths or unsupported naming rules; treat in-scope unresolved unknowns as closure blockers; do not publish or hand off partial analysis as canonical source-structure knowledge; when analysis cannot complete, classify whether the cause is context size, scope size, ambiguous instruction, unavailable tool/source, or evidence conflict; preserve lower-layer source evidence; hand publication to source_structure_findings_registration when canonical knowledge registration is needed

- lifecycle:
  - startup: confirm target path, fixed source scope boundary, intended overview depth, available domain knowledge inputs, whether the result is for proposal-only or later canonical registration, and the completion strategy for the fixed scope
  - planning: define subsystem buckets, runtime-flow buckets, state-boundary buckets, Brownfield API Naming Extractor buckets, structural-authority evidence searches, needed deterministic inventory tools, output path, read-only analysis rows, and completion-control rows for the fixed source scope
  - execution: produce a whole-system structure overview for the fixed source scope, map major subsystems and runtime flows, identify structural authorities and variation mechanisms, extract local brownfield API and data-flow naming rules, record reusable domain-knowledge metadata, and resolve, scope out, or escalate uncovered areas; if completion is impossible, produce an incomplete-analysis cause review instead of a partial overview
  - monitoring_and_control: treat missing whole-system sections as leaks; downgrade framework-shaped assumptions or naming rules without local evidence to `unknown`; treat in-scope unknowns and scope narrowing as closure blockers; require cause classification for incomplete analysis; stop if the task turns into proposition-specific change analysis
  - closure: return either a complete overview artifact with evidence commands, used knowledge refs, validity/recheck conditions, resolved/out-of-scope/escalated unknowns, completion-control result `complete`, and handoff target, or an incomplete-analysis cause review with next action and handoff owner; only the complete overview path may proceed to registration

- tags: `dotnet`, `source-analysis`, `structure`, `overview`, `domain-knowledge`

- knowledge_slots:
  - name=common_source_analysis_criteria; bind=5F21C8A41001
  - name=custom_framework_common_criteria; bind=5F21C8A41002
  - name=dotnet_change_analysis_viewpoints; bind=2E7B5A1FD201
  - name=structure_analysis_determinism_tiers; bind=5301B897BA41
  - name=csharp_naming_convention_extraction; bind=B4F7E1A2C903
  - name=current_source_structure_findings_catalog; bind=A9E742B1C6D0

- knowledge_inputs:
  - name=target_domain_context; accepts=source-structure-overview,current-source-structure-findings,module-map,service-map,architecture-note; purpose=optional-prior-structure-context

- observation_refs:
  - `../../observations/2026-07-04_source_structure_overview_creation.md`

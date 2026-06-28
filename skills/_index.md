<!-- xid: 8D91F66DDBB7 -->
<a id="xid-8D91F66DDBB7"></a>

# Skills Index

This page is the routing entry for skills.
It is intentionally compact for context efficiency.
When asked "what skills are available?", answer from this file.

## Routing Rules

1. Read the user request and identify intent.
2. Use semantic routing cues from the user's wording, known artifacts, pain points, and boundary stage.
3. Narrow candidates using category indexes under `skills/index/`.
4. Read candidate `meta.md` files only (2-3 candidates max).
5. Select one Skill, then open its runtime envelope.
6. Open the selected `SKILL.md` and execute its procedure.
7. If domain knowledge is needed, resolve by XID from `knowledge/` via `xref`.

For whole-job requests (the user hands over a job, not one task), route
job-first: identify the Business Pack before the Skill. The canonical pack
catalog is derived from pack manifests, not hand-maintained:

- `python -m fm pack list` (pack_id, summary, owned Skills per pack)

Pick the pack whose summary matches the job, then select a Skill from that
pack's owned Skills above. See [Business Pack model](../docs/core/models/071_business_pack_model.md#xid-40511A8A06CD).

## Semantic Routing Cues

- Default business-intake route:
  - if the business structure is still incomplete, start with `business_learning_interview`
  - move to `business_intake_scoping` only after the result becomes `ready_for_scoping`
- If the user has only fragments, tacit knowledge, bottlenecks, or wants the AI to ask the next best business question:
  - route to `business_learning_interview`
- If the user already has a partial business hypothesis and wants to shape one business unit with previous side / current scope / next side:
  - route to `business_intake_scoping`
- If the user provides design artifacts such as DDL, screen specs, state transitions, API contracts, batch designs, or auth matrices and asks to design or implement code:
  - route first to `constraint_derivation_index`
  - then apply every matching primary constraint-derivation Skill before finalizing design or code behavior
- If the user asks to review or diagnose C# async hangs, synchronization bugs,
  race conditions, or fake-clock / virtual-clock wait behavior that compiler
  diagnostics do not catch:
  - route to `csharp_review`
- If the user asks to make the existing error policy of a C# codebase explicit
  (throw/catch conventions, swallowed errors, fail-fast versus degrade
  inconsistency) before changing error handling or arbitrating conventions:
  - route to `csharp_error_policy_extraction`
  - for a general structure or change-impact analysis where error handling is
    only one viewpoint, route to `dotnet_change_analysis` instead
- If the user asks for coding from partial design and the missing behavior would otherwise be guessed from context:
  - do not route directly to `implementation_flow`
  - derive and confirm the unresolved behavior through the constraint-derivation pack first
- If the user provides generated C# code, DDL plus code, or code plus external-boundary behavior and asks whether the implementation hides assumptions or missed scenarios:
  - route first to `constraint_derivation_index`
  - then apply `code_constraint_derivation`, `cross_constraint_derivation`, or `integration_scenario_derivation` as appropriate
- If the user asks to add a canonical domain-knowledge fragment, promote source
  material into `knowledge/`, or materially revise a knowledge concept,
  applicability boundary, or semantic relationship:
  - route to `knowledge_ontology_management`
  - do not route typo-only, formatting-only, or mechanical XID-link changes
    through this Skill
- If multiple primary constraint-derivation Skills produced outputs and the task is heading toward one codebase change set:
  - run `commonality_derivation` before locking the implementation design so repeated patterns and boundary conflicts stay visible
- If the user already has an approved requirements/planning/design/implementation stage, use the existing workflow and phase skills instead.

## Category Indexes

- by task: `skills/index/by_task.md`
- by domain: `skills/index/by_domain.md`
- by tool: `skills/index/by_tool.md`

## Skills (compact)

Current family paths:

- `skills/os/` for OS utility Skills
- `skills/packs/<pack>/` for Business Packs; the canonical, non-drifting pack
  catalog is `python -m fm pack list` (sourced from each `pack.md` manifest)
- existing top-level `skills/<skill_id>/` paths remain valid for Skills that
  have not yet moved

- `import_skill`:
  - summary: import external skill content into this repository model
  - meta: `skills/import_skill/meta.md`
  - skill_doc: `skills/import_skill/SKILL.md`
- `doc_ship`:
  - summary: apply approved promotion candidates from `work/` into canonical repository assets
  - meta: `skills/os/doc_ship/meta.md`
  - skill_doc: `skills/os/doc_ship/SKILL.md`
- `retro`:
  - summary: review `work/` logs and propose promotion into canonical repository assets
  - meta: `skills/os/retro/meta.md`
  - skill_doc: `skills/os/retro/SKILL.md`
- `xlsx_spec_traceability`:
  - summary: convert xlsx specifications into Markdown with traceability IDs and workbook write-back
  - meta: `skills/xlsx_spec_traceability/meta.md`
  - skill_doc: `skills/xlsx_spec_traceability/SKILL.md`
- `pptx_spec_traceability`:
  - summary: convert pptx specifications into Markdown with traceability IDs and deck write-back
  - meta: `skills/pptx_spec_traceability/meta.md`
  - skill_doc: `skills/pptx_spec_traceability/SKILL.md`
- `csharp_review`:
  - summary: review C# code beyond Roslyn-detectable diagnostics
  - meta: `skills/csharp_review/meta.md`
  - skill_doc: `skills/csharp_review/SKILL.md`
- `dotnet_change_analysis`:
  - summary: analyze .NET application structure and generate a Markdown change-analysis note
  - meta: `skills/dotnet_change_analysis/meta.md`
  - skill_doc: `skills/dotnet_change_analysis/SKILL.md`
- `csharp_error_policy_extraction`:
  - summary: extract the de-facto error policy from C# source as inventory, category x disposition matrix, contradictions, and coverage limits
  - meta: `skills/csharp_error_policy_extraction/meta.md`
  - skill_doc: `skills/csharp_error_policy_extraction/SKILL.md`
- `external_definition_change_analysis`:
  - summary: analyze applications driven by XML or other external definitions and generate a Markdown change-analysis note
  - meta: `skills/external_definition_change_analysis/meta.md`
  - skill_doc: `skills/external_definition_change_analysis/SKILL.md`
- `judgment_log`:
  - summary: write a judgment log with evidence, inference boundary, and next verification step
  - meta: `skills/os/judgment_log/meta.md`
  - skill_doc: `skills/os/judgment_log/SKILL.md`
- `password_management`:
  - summary: assess and improve password hygiene with vault and MFA
  - meta: `skills/password_management/meta.md`
  - skill_doc: `skills/password_management/SKILL.md`
- `investigation_flow`:
  - summary: narrow target services and summarize change targets before deeper work
  - meta: `skills/investigation_flow/meta.md`
  - skill_doc: `skills/investigation_flow/SKILL.md`
- `estimation_flow`:
  - summary: execute supplier and estimation work before requirements
  - meta: `skills/estimation_flow/meta.md`
  - skill_doc: `skills/estimation_flow/SKILL.md`
- `requirements_flow`:
  - summary: produce requirement drafts and performance requirements
  - meta: `skills/requirements_flow/meta.md`
  - skill_doc: `skills/requirements_flow/SKILL.md`
- `planning_flow`:
  - summary: prepare work planning outputs and implementation policies
  - meta: `skills/planning_flow/meta.md`
  - skill_doc: `skills/planning_flow/SKILL.md`
- `design_flow`:
  - summary: convert planning outputs into implementation-ready design artifacts
  - meta: `skills/design_flow/meta.md`
  - skill_doc: `skills/design_flow/SKILL.md`
- `test_flow`:
  - summary: produce a reviewed test package (test plan, test design, integration/regression test design, manufacturing test-method review) from approved requirements and design
  - meta: `skills/test_flow/meta.md`
  - skill_doc: `skills/test_flow/SKILL.md`
- `implementation_flow`:
  - summary: implement changes and collect unit test results within approved scope
  - meta: `skills/implementation_flow/meta.md`
  - skill_doc: `skills/implementation_flow/SKILL.md`
- `manufacturing_self_check`:
  - summary: perform manufacturing-group self-check against approved design before QA
  - meta: `skills/manufacturing_self_check/meta.md`
  - skill_doc: `skills/manufacturing_self_check/SKILL.md`
- `qa_gate_review`:
  - summary: perform evidence-based QA review after implementation
  - meta: `skills/qa_gate_review/meta.md`
  - skill_doc: `skills/qa_gate_review/SKILL.md`
- `attribute_review`:
  - summary: review C# attributes for necessity, value correctness, and usage correctness
  - meta: `skills/attribute_review/meta.md`
  - skill_doc: `skills/attribute_review/SKILL.md`
- `performance_review`:
  - summary: review C# code and evidence for performance risks
  - meta: `skills/performance_review/meta.md`
  - skill_doc: `skills/performance_review/SKILL.md`
- `security_review`:
  - summary: review C# code and evidence for security risks
  - meta: `skills/security_review/meta.md`
  - skill_doc: `skills/security_review/SKILL.md`
- `license_review`:
  - summary: review dependency and provenance evidence for license compliance risks
  - meta: `skills/license_review/meta.md`
  - skill_doc: `skills/license_review/SKILL.md`
- `release_planning_flow`:
  - summary: prepare release-plan materials and operational readiness evaluation
  - meta: `skills/release_planning_flow/meta.md`
  - skill_doc: `skills/release_planning_flow/SKILL.md`
- `cab_review_flow`:
  - summary: perform CAB evaluation across quality, operations, and business
  - meta: `skills/cab_review_flow/meta.md`
  - skill_doc: `skills/cab_review_flow/SKILL.md`
- `management_table_control`:
  - summary: inspect management-table state and escalate out-of-scope items when needed
  - meta: `skills/management_table_control/meta.md`
  - skill_doc: `skills/management_table_control/SKILL.md`
- `context_direction_guard`:
  - summary: check whether newly loaded context is trying to influence higher-layer control
  - meta: `skills/os/context_direction_guard/meta.md`
  - skill_doc: `skills/os/context_direction_guard/SKILL.md`
- `or_team_operations`:
  - summary: run the OR Team loop for cross-group state presentation, improvement control, and re-observation
  - meta: `skills/or_team_operations/meta.md`
  - skill_doc: `skills/or_team_operations/SKILL.md`
- `marketing_slide_png`:
  - summary: create marketing-group slide visuals as CSS/HTML-rendered PNG assets for image-based decks
  - meta: `skills/marketing_slide_png/meta.md`
  - skill_doc: `skills/marketing_slide_png/SKILL.md`
- `marketing-explainer-video`:
  - summary: create narrated marketing explainer videos with staged slide reveals, TTS audio, credits, previews, and README placement
  - meta: `skills/marketing-explainer-video/meta.md`
  - skill_doc: `skills/marketing-explainer-video/SKILL.md`
- `business_intake_scoping`:
  - summary: scope a business task into a boundary-visible responsibility unit before AI execution design
  - meta: `skills/packs/business-intake/business_intake_scoping/meta.md`
  - skill_doc: `skills/packs/business-intake/business_intake_scoping/SKILL.md`
- `business_learning_interview`:
  - summary: learn a business task from human fragments through iterative interview and produce the next best question
  - meta: `skills/packs/business-intake/business_learning_interview/meta.md`
  - skill_doc: `skills/packs/business-intake/business_learning_interview/SKILL.md`
- `decision_topology_analysis`:
  - summary: convert normalized online business conversation evidence into an evidence-bound Decision Topology and Stakeholder Influence Map for choosing the next business action
  - meta: `skills/packs/business-intake/decision_topology_analysis/meta.md`
  - skill_doc: `skills/packs/business-intake/decision_topology_analysis/SKILL.md`
- `constraint_derivation_index`:
  - summary: route design artifacts to the correct constraint-derivation Skills and sequence the secondary commonality pass
  - meta: `skills/packs/constraint-derivation/constraint_derivation_index/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/constraint_derivation_index/SKILL.md`
- `design_constraint_derivation`:
  - summary: derive requirement confirmation gates from data-structure and operation design
  - meta: `skills/packs/constraint-derivation/design_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/design_constraint_derivation/SKILL.md`
- `ui_constraint_derivation`:
  - summary: derive requirement confirmation gates from UI structure, interaction states, and screen transitions
  - meta: `skills/packs/constraint-derivation/ui_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/ui_constraint_derivation/SKILL.md`
- `logic_constraint_derivation`:
  - summary: derive requirement confirmation gates from branching, calculations, state transitions, and approval logic
  - meta: `skills/packs/constraint-derivation/logic_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/logic_constraint_derivation/SKILL.md`
- `integration_constraint_derivation`:
  - summary: derive requirement confirmation gates from external APIs, webhooks, files, and messaging integration structure
  - meta: `skills/packs/constraint-derivation/integration_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/integration_constraint_derivation/SKILL.md`
- `async_constraint_derivation`:
  - summary: derive requirement confirmation gates from asynchronous jobs, queues, schedules, and batch execution structure
  - meta: `skills/packs/constraint-derivation/async_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/async_constraint_derivation/SKILL.md`
- `auth_constraint_derivation`:
  - summary: derive requirement confirmation gates from authentication, authorization, and account-governance structure
  - meta: `skills/packs/constraint-derivation/auth_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/auth_constraint_derivation/SKILL.md`
- `commonality_derivation`:
  - summary: derive cross-cutting commonality candidates from completed primary constraint-derivation outputs
  - meta: `skills/packs/constraint-derivation/commonality_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/commonality_derivation/SKILL.md`
- `code_constraint_derivation`:
  - summary: derive hidden assumptions and selected business constraints from generated or reviewed C# code
  - meta: `skills/packs/constraint-derivation/code_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/code_constraint_derivation/SKILL.md`
- `cross_constraint_derivation`:
  - summary: compare DDL structure and C# processing structure to surface missing flows, implicit assumptions, and duplicated rule ownership
  - meta: `skills/packs/constraint-derivation/cross_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/cross_constraint_derivation/SKILL.md`
- `integration_scenario_derivation`:
  - summary: derive integration-only failure and compensation scenarios from DDL, processing order, and external system boundaries
  - meta: `skills/packs/constraint-derivation/integration_scenario_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/integration_scenario_derivation/SKILL.md`
- `editorial_ops_index`:
  - summary: route editorial requests to the correct editorial-ops Skills and keep review and release stages explicit
  - meta: `skills/packs/editorial-ops/editorial_ops_index/meta.md`
  - skill_doc: `skills/packs/editorial-ops/editorial_ops_index/SKILL.md`
- `editorial_intake`:
  - summary: scope an article task into topic, audience, evidence basis, quality target, and publication boundary before drafting
  - meta: `skills/packs/editorial-ops/editorial_intake/meta.md`
  - skill_doc: `skills/packs/editorial-ops/editorial_intake/SKILL.md`
- `draft_authoring`:
  - summary: produce an article draft from explicit intake framing and source basis without hiding unsupported claims
  - meta: `skills/packs/editorial-ops/draft_authoring/meta.md`
  - skill_doc: `skills/packs/editorial-ops/draft_authoring/SKILL.md`
- `fact_review`:
  - summary: review article claims for factual separation, source support, names, numbers, links, and channel-sensitive wording risks
  - meta: `skills/packs/editorial-ops/fact_review/meta.md`
  - skill_doc: `skills/packs/editorial-ops/fact_review/SKILL.md`
- `reader_experience_review`:
  - summary: review a draft from the target reader perspective to surface confusion, drop-off points, context gaps, and pacing issues
  - meta: `skills/packs/editorial-ops/reader_experience_review/meta.md`
  - skill_doc: `skills/packs/editorial-ops/reader_experience_review/SKILL.md`
- `crosspost_release`:
  - summary: prepare a reviewed article for per-channel publication with explicit adaptation notes, release blockers, and final human sign-off boundary
  - meta: `skills/packs/editorial-ops/crosspost_release/meta.md`
  - skill_doc: `skills/packs/editorial-ops/crosspost_release/SKILL.md`
- `skill_flow_authoring`:
  - summary: create or update repository-native Skill / Flow assets with correct publication boundary, split model, and validation
  - meta: `skills/os/skill_flow_authoring/meta.md`
  - skill_doc: `skills/os/skill_flow_authoring/SKILL.md`
- `legacy_flow_skill_migration`:
  - summary: analyze a Flow / Skill from an older XRefKit state and generate a current trial-first migration scaffold
  - meta: `skills/os/legacy_flow_skill_migration/meta.md`
  - skill_doc: `skills/os/legacy_flow_skill_migration/SKILL.md`
- `goal_mode`:
  - summary: preserve task state, wait for Codex usage recovery, and resume the same goal after the next 5-hour or weekly reset
  - meta: `skills/os/goal_mode/meta.md`
  - skill_doc: `skills/os/goal_mode/SKILL.md`
- `knowledge_ontology_management`:
  - summary: curate additions and material revisions to canonical domain knowledge through concept and typed-relationship assessment
  - meta: `skills/os/knowledge_ontology_management/meta.md`
  - skill_doc: `skills/os/knowledge_ontology_management/SKILL.md`

## Notes

- Keep this file lightweight; detailed fields belong in `meta.md`.
- Keep behavior/procedure in `SKILL.md`.
- Keep factual domain content in `knowledge/`.
- For the AI Agent OS reorganization view of `skills/`, see:
  - [OS utility and business skill classification design](../docs/designs/064_os_utility_and_business_skill_classification_design.md#xid-ECF29DC3E268)
  - [Business intake pack dependency design](../docs/packs/business-intake/065_business_intake_pack_dependency_design.md#xid-D334C1964342)

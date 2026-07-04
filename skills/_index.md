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
- If the user provides multi-person conversation evidence where one topic
  branches into subtopics and wants topic organization, participant involvement
  per branch, central participant candidates, or bridge participants:
  - route to `conversation_topic_branch_mapping`
  - then route branch-specific decision movement to `decision_topology_analysis`
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
- If the user brings a consultation topic and wants to avoid reinventing the
  wheel by identifying prior research, established approaches, reusable
  patterns, deterministic extraction work, and remaining judgment space:
  - route to `consultation_research_mapping`
  - use current sources for drift-prone topics; do not answer from model memory
    alone when prior art or current practice matters
- If multiple primary constraint-derivation Skills produced outputs and the task is heading toward one codebase change set:
  - run `commonality_derivation` before locking the implementation design so repeated patterns and boundary conflicts stay visible
- If the user already has an approved requirements/planning/design/implementation stage, use the existing workflow and phase skills instead.

## Category Indexes

- by task: `skills/index/by_task.md`
- by domain: `skills/index/by_domain.md`
- by tool: `skills/index/by_tool.md`

## Skills (compact)

Generated by `python -m fm skill index --write` from catalog-visible `meta.md` files.

Current family paths:

- `skills/os/` for OS utility Skills
- `skills/packs/<pack>/` for legacy Business Pack paths during transition
- `packs/<pack>/skills/` for shared pack Skills
- `packs/local/<system>/skills/` for local-instance Skills; these are catalog-visible locally but not distributable
- existing top-level `skills/<skill_id>/` paths remain valid for Skills that have not yet moved

- `cab_review_flow`:
  - summary: execute CAB business activities through reusable quality, operational-readiness, and value-alignment evaluation capabilities
  - meta: `skills/cab_review_flow/meta.md`
  - skill_doc: `skills/cab_review_flow/SKILL.md`
- `csharp_error_policy_extraction`:
  - summary: extract the existing de-facto error policy from C# source as an inventory, a category-by-disposition matrix, detected contradictions, and explicit coverage limits
  - meta: `skills/csharp_error_policy_extraction/meta.md`
  - skill_doc: `skills/csharp_error_policy_extraction/SKILL.md`
- `csharp_review`:
  - summary: review C# code with a manual focus on non-Roslyn-detectable risks
  - meta: `skills/csharp_review/meta.md`
  - skill_doc: `skills/csharp_review/SKILL.md`
- `db_current_state_analysis`:
  - summary: analyze current brownfield database and persistence structure from repository evidence before DB design
  - meta: `skills/db_current_state_analysis/meta.md`
  - skill_doc: `skills/db_current_state_analysis/SKILL.md`
- `db_design`:
  - summary: produce implementation-ready brownfield database design artifacts from approved planning inputs and current source-structure findings
  - meta: `skills/db_design/meta.md`
  - skill_doc: `skills/db_design/SKILL.md`
- `design_flow`:
  - summary: execute design business activity through reusable solution-design capability
  - meta: `skills/design_flow/meta.md`
  - skill_doc: `skills/design_flow/SKILL.md`
- `dotnet_change_analysis`:
  - summary: analyze .NET application structure and generate a Markdown change-analysis note for later design or implementation work
  - meta: `skills/dotnet_change_analysis/meta.md`
  - skill_doc: `skills/dotnet_change_analysis/SKILL.md`
- `estimation_flow`:
  - summary: execute estimation business activities through reusable comparison, projection, option-structuring, and ambiguity-classification capabilities
  - meta: `skills/estimation_flow/meta.md`
  - skill_doc: `skills/estimation_flow/SKILL.md`
- `implementation_flow`:
  - summary: execute manufacturing business activities through reusable scoped realization and unit-level verification capabilities
  - meta: `skills/implementation_flow/meta.md`
  - skill_doc: `skills/implementation_flow/SKILL.md`
- `import_skill`:
  - summary: import external skill content into this repository split model
  - meta: `skills/import_skill/meta.md`
  - skill_doc: `skills/import_skill/SKILL.md`
- `investigation_flow`:
  - summary: execute the investigation workflow from service catalog analysis through change-target summary using reusable investigation capabilities
  - meta: `skills/investigation_flow/meta.md`
  - skill_doc: `skills/investigation_flow/SKILL.md`
- `manufacturing_self_check`:
  - summary: execute manufacturing self-check business activity through reusable design-alignment self-evaluation capability
  - meta: `skills/manufacturing_self_check/meta.md`
  - skill_doc: `skills/manufacturing_self_check/SKILL.md`
- `marketing-explainer-video`:
  - summary: create repository-ready narrated marketing explainer videos with staged slide reveals, TTS audio, licensing credits, previews, and README placement
  - meta: `skills/marketing-explainer-video/meta.md`
  - skill_doc: `skills/marketing-explainer-video/SKILL.md`
- `marketing_slide_png`:
  - summary: create marketing-group slide visuals or standalone repository infographics by rendering CSS/HTML diagrams to PNG
  - meta: `skills/marketing_slide_png/meta.md`
  - skill_doc: `skills/marketing_slide_png/SKILL.md`
- `consultation_research_mapping`:
  - summary: map a consultation topic to prior research, known reusable patterns, deterministic extraction work, and the remaining non-deterministic judgment space
  - meta: `skills/os/consultation_research_mapping/meta.md`
  - skill_doc: `skills/os/consultation_research_mapping/SKILL.md`
- `doc_ship`:
  - summary: apply approved promotion candidates from `work/` into canonical repository assets and leave traceable moved-to pointers
  - meta: `skills/os/doc_ship/meta.md`
  - skill_doc: `skills/os/doc_ship/SKILL.md`
- `goal_mode`:
  - summary: preserve task state, wait for Codex usage recovery, and resume the same goal after the next 5-hour or weekly reset
  - meta: `skills/os/goal_mode/meta.md`
  - skill_doc: `skills/os/goal_mode/SKILL.md`
- `judgment_log`:
  - summary: write a judgment log that records decision, evidence, inference boundary, confidence, and next verification step
  - meta: `skills/os/judgment_log/meta.md`
  - skill_doc: `skills/os/judgment_log/SKILL.md`
- `knowledge_ontology_management`:
  - summary: curate new or materially revised domain knowledge through concept identity, duplication, split, replacement, and typed-relationship assessment before canonical publication
  - meta: `skills/os/knowledge_ontology_management/meta.md`
  - skill_doc: `skills/os/knowledge_ontology_management/SKILL.md`
- `legacy_flow_skill_migration`:
  - summary: analyze a Flow / Skill from an older XRefKit state and generate a current trial-first migration scaffold
  - meta: `skills/os/legacy_flow_skill_migration/meta.md`
  - skill_doc: `skills/os/legacy_flow_skill_migration/SKILL.md`
- `retro`:
  - summary: review session logs and current work artifacts, then propose promotion candidates from `work/` into canonical repository assets
  - meta: `skills/os/retro/meta.md`
  - skill_doc: `skills/os/retro/SKILL.md`
- `skill_flow_authoring`:
  - summary: create or update repository-native Skill / Flow assets in XRefKit with correct split, publication boundary, runtime envelope, forgetting countermeasures, and validation
  - meta: `skills/os/skill_flow_authoring/meta.md`
  - skill_doc: `skills/os/skill_flow_authoring/SKILL.md`
- `source_structure_findings_registration`:
  - summary: register an existing source-structure analysis Markdown file as current canonical source-structure findings knowledge
  - meta: `skills/os/source_structure_findings_registration/meta.md`
  - skill_doc: `skills/os/source_structure_findings_registration/SKILL.md`
- `business_intake_scoping`:
  - summary: discover and scope one business task into a boundary-visible responsibility unit even when the user only knows partial materials or structure
  - meta: `skills/packs/business-intake/business_intake_scoping/meta.md`
  - skill_doc: `skills/packs/business-intake/business_intake_scoping/SKILL.md`
- `business_learning_interview`:
  - summary: learn a business task from a human through goal-first interview and convert partial fragments into a structured business hypothesis
  - meta: `skills/packs/business-intake/business_learning_interview/meta.md`
  - skill_doc: `skills/packs/business-intake/business_learning_interview/SKILL.md`
- `conversation_topic_branch_mapping`:
  - summary: map business conversation topics across days and show each topic's current state, participant involvement, central coordination candidates, unknowns, and ontology-promotion candidates
  - meta: `skills/packs/business-intake/conversation_topic_branch_mapping/meta.md`
  - skill_doc: `skills/packs/business-intake/conversation_topic_branch_mapping/SKILL.md`
- `decision_topology_analysis`:
  - summary: convert normalized online business conversation evidence into an evidence-bound Decision Topology and Stakeholder Influence Map for choosing the next business action
  - meta: `skills/packs/business-intake/decision_topology_analysis/meta.md`
  - skill_doc: `skills/packs/business-intake/decision_topology_analysis/SKILL.md`
- `async_constraint_derivation`:
  - summary: derive requirement confirmation gates from asynchronous jobs, queues, schedules, and batch execution structure
  - meta: `skills/packs/constraint-derivation/async_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/async_constraint_derivation/SKILL.md`
- `auth_constraint_derivation`:
  - summary: derive requirement confirmation gates from authentication, authorization, and account-governance structure
  - meta: `skills/packs/constraint-derivation/auth_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/auth_constraint_derivation/SKILL.md`
- `code_constraint_derivation`:
  - summary: derive hidden assumptions and selected business constraints from generated or reviewed C# code
  - meta: `skills/packs/constraint-derivation/code_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/code_constraint_derivation/SKILL.md`
- `commonality_derivation`:
  - summary: derive cross-cutting commonality candidates from completed primary constraint-derivation outputs
  - meta: `skills/packs/constraint-derivation/commonality_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/commonality_derivation/SKILL.md`
- `constraint_derivation_index`:
  - summary: route design or implementation artifacts to the correct bidirectional constraint-derivation Skills and sequence the secondary commonality pass
  - meta: `skills/packs/constraint-derivation/constraint_derivation_index/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/constraint_derivation_index/SKILL.md`
- `cross_constraint_derivation`:
  - summary: compare DDL structure and C# processing structure to surface missing flows, implicit assumptions, and duplicated rule ownership
  - meta: `skills/packs/constraint-derivation/cross_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/cross_constraint_derivation/SKILL.md`
- `design_constraint_derivation`:
  - summary: derive requirement confirmation gates from data-structure, database, relationship, and operation design
  - meta: `skills/packs/constraint-derivation/design_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/design_constraint_derivation/SKILL.md`
- `integration_constraint_derivation`:
  - summary: derive requirement confirmation gates from external APIs, webhooks, files, and messaging integration structure
  - meta: `skills/packs/constraint-derivation/integration_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/integration_constraint_derivation/SKILL.md`
- `integration_scenario_derivation`:
  - summary: derive integration-only failure and compensation scenarios from DDL, processing order, and external system boundaries
  - meta: `skills/packs/constraint-derivation/integration_scenario_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/integration_scenario_derivation/SKILL.md`
- `logic_constraint_derivation`:
  - summary: derive requirement confirmation gates from branching, calculations, state transitions, and approval logic
  - meta: `skills/packs/constraint-derivation/logic_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/logic_constraint_derivation/SKILL.md`
- `ui_constraint_derivation`:
  - summary: derive requirement confirmation gates from UI structure, interaction states, and screen transitions
  - meta: `skills/packs/constraint-derivation/ui_constraint_derivation/meta.md`
  - skill_doc: `skills/packs/constraint-derivation/ui_constraint_derivation/SKILL.md`
- `crosspost_release`:
  - summary: prepare a reviewed article for per-channel publication with explicit adaptation notes, release blockers, and final human sign-off boundary
  - meta: `skills/packs/editorial-ops/crosspost_release/meta.md`
  - skill_doc: `skills/packs/editorial-ops/crosspost_release/SKILL.md`
- `draft_authoring`:
  - summary: produce an article draft from explicit intake framing and source basis without hiding unsupported claims
  - meta: `skills/packs/editorial-ops/draft_authoring/meta.md`
  - skill_doc: `skills/packs/editorial-ops/draft_authoring/SKILL.md`
- `editorial_intake`:
  - summary: scope an article task into topic, audience, evidence basis, quality target, and publication boundary before drafting
  - meta: `skills/packs/editorial-ops/editorial_intake/meta.md`
  - skill_doc: `skills/packs/editorial-ops/editorial_intake/SKILL.md`
- `editorial_ops_index`:
  - summary: route editorial requests to the correct editorial-ops Skills and keep review and release stages explicit
  - meta: `skills/packs/editorial-ops/editorial_ops_index/meta.md`
  - skill_doc: `skills/packs/editorial-ops/editorial_ops_index/SKILL.md`
- `fact_review`:
  - summary: review article claims for factual separation, source support, names, numbers, links, and channel-sensitive wording risks
  - meta: `skills/packs/editorial-ops/fact_review/meta.md`
  - skill_doc: `skills/packs/editorial-ops/fact_review/SKILL.md`
- `reader_experience_review`:
  - summary: review a draft from the target reader perspective to surface confusion, drop-off points, context gaps, and pacing issues
  - meta: `skills/packs/editorial-ops/reader_experience_review/meta.md`
  - skill_doc: `skills/packs/editorial-ops/reader_experience_review/SKILL.md`
- `planning_flow`:
  - summary: execute planning business activity through reusable work-and-policy planning capability grounded in domain knowledge and current-source findings
  - meta: `skills/planning_flow/meta.md`
  - skill_doc: `skills/planning_flow/SKILL.md`
- `pptx_spec_traceability`:
  - summary: extract presentation specifications into Markdown, assign traceability IDs, connect slide images and shapes to nearby explanatory text, and write the IDs back into the deck
  - meta: `skills/pptx_spec_traceability/meta.md`
  - skill_doc: `skills/pptx_spec_traceability/SKILL.md`
- `qa_gate_review`:
  - summary: execute evidence-based QA across specification, performance, security, and license domains
  - meta: `skills/qa_gate_review/meta.md`
  - skill_doc: `skills/qa_gate_review/SKILL.md`
- `release_planning_flow`:
  - summary: execute release-planning business activities through reusable release-material, release-procedure, release-confirmation, signal-specification, response-structuring, and readiness-evaluation capabilities
  - meta: `skills/release_planning_flow/meta.md`
  - skill_doc: `skills/release_planning_flow/SKILL.md`
- `requirements_flow`:
  - summary: execute requirements business activities through reusable requirement and performance-constraint structuring capabilities
  - meta: `skills/requirements_flow/meta.md`
  - skill_doc: `skills/requirements_flow/SKILL.md`
- `security_review`:
  - summary: review C# code and evidence for security risks
  - meta: `skills/security_review/meta.md`
  - skill_doc: `skills/security_review/SKILL.md`
- `source_structure_overview`:
  - summary: produce a reusable whole-system source-structure overview for a target repository or service before proposition-specific change analysis
  - meta: `skills/source_structure_overview/meta.md`
  - skill_doc: `skills/source_structure_overview/SKILL.md`
- `test_flow`:
  - summary: execute test-planning, test-item structuring, integration/regression test design, and manufacturing-side test-method review
  - meta: `skills/test_flow/meta.md`
  - skill_doc: `skills/test_flow/SKILL.md`
- `xlsx_spec_traceability`:
  - summary: extract spreadsheet specifications into Markdown, assign traceability IDs, connect embedded images to nearby specification text, and write the IDs back into the workbook
  - meta: `skills/xlsx_spec_traceability/meta.md`
  - skill_doc: `skills/xlsx_spec_traceability/SKILL.md`

## Notes

- Keep this file lightweight; detailed fields belong in `meta.md`.
- Keep behavior/procedure in `SKILL.md`.
- Keep factual domain content in `knowledge/`.
- For the AI Agent OS reorganization view of `skills/`, see:
  - [OS utility and business skill classification design](../docs/designs/064_os_utility_and_business_skill_classification_design.md#xid-ECF29DC3E268)
  - [Business intake pack dependency design](../docs/packs/business-intake/065_business_intake_pack_dependency_design.md#xid-D334C1964342)

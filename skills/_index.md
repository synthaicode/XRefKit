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
4. Read candidate `SKILL.v1.md` headers only (2-3 candidates max).
5. Select one Skill, then open its runtime envelope.
6. Open the selected `SKILL.v1.md` method and execute its procedure after runtime validation.
7. If domain knowledge is needed, resolve by XID from `knowledge/` via `xref`.

For whole-job requests (the user hands over a job, not one task), route
job-first: identify the Business Pack before the Skill. The canonical pack
catalog is derived from pack manifests, not hand-maintained:

- `python -m xrefkit pack list` (pack_id, summary, owned Skills per pack)

Pick the pack whose summary matches the job, then select a Skill from that
pack's owned Skills above. See [Business Pack model](../docs/core/models/071_business_pack_model.md#xid-40511A8A06CD).

## Semantic Routing Cues

- For authorized workspace-scoped Azure DevOps test import, explicit plan binding, Task delivery or delivery reconciliation:
  - route to `azure_work_item_integration`
  - the current writer/recovery only supports PBI 10 / Task 21; load its operating-model Knowledge before operation

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

Generated by `python -m xrefkit skill index --write` from adopted SkillDefinitions or legacy metadata.

Current family paths:

- `skills/os/` for OS utility Skills
- `skills/packs/<pack>/` for legacy Business Pack paths during transition
- `packs/<pack>/skills/` for shared pack Skills
- `packs/local/<system>/skills/` for local-instance Skills; these are catalog-visible locally but not distributable
- existing top-level `skills/<skill_id>/` paths remain valid for Skills that have not yet moved

- `brownfield_workflow`:
  - summary: carry a brownfield change through traced phase outputs while preserving evidence, unknowns, and human decisions
  - meta: `skills/brownfield-workflow/SKILL.v1.md`
  - skill_doc: `skills/brownfield-workflow/SKILL.v1.md`
- `cab_review_flow`:
  - summary: execute CAB evaluation gates for quality, operational readiness, and value alignment before human release confirmation
  - meta: `skills/cab_review_flow/SKILL.v1.md`
  - skill_doc: `skills/cab_review_flow/SKILL.v1.md`
- `csharp_error_policy_extraction`:
  - summary: extract the implemented C# error policy as evidence, dispositions, contradictions, and explicit coverage limits
  - meta: `skills/csharp_error_policy_extraction/SKILL.v1.md`
  - skill_doc: `skills/csharp_error_policy_extraction/SKILL.v1.md`
- `csharp_review`:
  - summary: review C# code for language-dependent defects and system-level implementation risks beyond Roslyn diagnostics
  - meta: `skills/csharp_review/SKILL.v1.md`
  - skill_doc: `skills/csharp_review/SKILL.v1.md`
- `db_current_state_analysis`:
  - summary: Analyze a brownfield database and persistence structure from repository evidence before database design
  - meta: `skills/db_current_state_analysis/SKILL.v1.md`
  - skill_doc: `skills/db_current_state_analysis/SKILL.v1.md`
- `db_design`:
  - summary: Produce implementation-ready brownfield database design artifacts from approved requirements and current database evidence
  - meta: `skills/db_design/SKILL.v1.md`
  - skill_doc: `skills/db_design/SKILL.v1.md`
- `design_flow`:
  - summary: Prepare a human reviewed implementation ready solution design from approved planning outputs.
  - meta: `skills/design_flow/SKILL.v1.md`
  - skill_doc: `skills/design_flow/SKILL.v1.md`
- `dotnet_change_analysis`:
  - summary: analyze .NET application structure and generate a Markdown change-analysis note for later design or implementation work
  - meta: `skills/dotnet_change_analysis/SKILL.v1.md`
  - skill_doc: `skills/dotnet_change_analysis/SKILL.v1.md`
- `estimation_flow`:
  - summary: prepare estimation options, supplier checks, and assumption clarification before requirements
  - meta: `skills/estimation_flow/SKILL.v1.md`
  - skill_doc: `skills/estimation_flow/SKILL.v1.md`
- `implementation_flow`:
  - summary: Execute an approved and bounded software change and prepare it for QA review.
  - meta: `skills/implementation_flow/SKILL.v1.md`
  - skill_doc: `skills/implementation_flow/SKILL.v1.md`
- `import_skill`:
  - summary: inspect and import external Skill content while separating procedure from Knowledge and preserving inspection safety
  - meta: `skills/import_skill/SKILL.v1.md`
  - skill_doc: `skills/import_skill/SKILL.v1.md`
- `investigation_flow`:
  - summary: investigate service scope, dependencies, viewpoints, and change targets before estimation or design
  - meta: `skills/investigation_flow/SKILL.v1.md`
  - skill_doc: `skills/investigation_flow/SKILL.v1.md`
- `manufacturing_self_check`:
  - summary: check manufacturing outputs against approved design before quality review
  - meta: `skills/manufacturing_self_check/SKILL.v1.md`
  - skill_doc: `skills/manufacturing_self_check/SKILL.v1.md`
- `marketing_explainer_video`:
  - summary: create repository-ready narrated marketing explainer videos with staged slide reveals, TTS audio, credits, previews, and publication placement
  - meta: `skills/marketing-explainer-video/SKILL.v1.md`
  - skill_doc: `skills/marketing-explainer-video/SKILL.v1.md`
- `marketing_slide_png`:
  - summary: create readable and rerenderable CSS/HTML slide visuals or standalone repository infographics as PNG assets
  - meta: `skills/marketing_slide_png/SKILL.v1.md`
  - skill_doc: `skills/marketing_slide_png/SKILL.v1.md`
- `consultation_research_mapping`:
  - summary: map a consultation topic to prior research, reusable patterns, deterministic work, and remaining human judgment
  - meta: `skills/os/consultation_research_mapping/SKILL.v1.md`
  - skill_doc: `skills/os/consultation_research_mapping/SKILL.v1.md`
- `doc_ship`:
  - summary: apply approved promotion candidates from work into canonical repository assets with traceable pointers
  - meta: `skills/os/doc_ship/SKILL.v1.md`
  - skill_doc: `skills/os/doc_ship/SKILL.v1.md`
- `domain_knowledge_catalog_preparation`:
  - summary: prepare a path-free XID-addressable catalog of repository and configured external domain knowledge for Skill runs
  - meta: `skills/os/domain_knowledge_catalog_preparation/SKILL.v1.md`
  - skill_doc: `skills/os/domain_knowledge_catalog_preparation/SKILL.v1.md`
- `goal_mode`:
  - summary: preserve task state and resume the same goal after verified Codex usage recovery
  - meta: `skills/os/goal_mode/SKILL.v1.md`
  - skill_doc: `skills/os/goal_mode/SKILL.v1.md`
- `judgment_log`:
  - summary: write an inspectable judgment log with decision, evidence, inference boundary, confidence, and next verification
  - meta: `skills/os/judgment_log/SKILL.v1.md`
  - skill_doc: `skills/os/judgment_log/SKILL.v1.md`
- `knowledge_ontology_management`:
  - summary: curate new or materially revised domain knowledge through identity, duplication, split, replacement, and relationship assessment
  - meta: `skills/os/knowledge_ontology_management/SKILL.v1.md`
  - skill_doc: `skills/os/knowledge_ontology_management/SKILL.v1.md`
- `legacy_flow_skill_migration`:
  - summary: analyze an older Flow or Skill and generate a trial-first migration scaffold with explicit gaps
  - meta: `skills/os/legacy_flow_skill_migration/SKILL.v1.md`
  - skill_doc: `skills/os/legacy_flow_skill_migration/SKILL.v1.md`
- `retro`:
  - summary: review work evidence and propose stable promotion candidates while keeping transient items in work
  - meta: `skills/os/retro/SKILL.v1.md`
  - skill_doc: `skills/os/retro/SKILL.v1.md`
- `skill_calibration_evaluation`:
  - summary: run isolated calibration evaluations for installed PyPI XRefKit Skills without exposing evaluator answers
  - meta: `skills/os/skill_calibration_evaluation/SKILL.v1.md`
  - skill_doc: `skills/os/skill_calibration_evaluation/SKILL.v1.md`
- `skill_flow_authoring`:
  - summary: create or evolve repository-native Skill and Flow assets with explicit boundaries, continuity, and validation
  - meta: `skills/os/skill_flow_authoring/SKILL.v1.md`
  - skill_doc: `skills/os/skill_flow_authoring/SKILL.v1.md`
- `source_structure_findings_registration`:
  - summary: register an existing source-structure analysis as current canonical findings without re-running analysis
  - meta: `skills/os/source_structure_findings_registration/SKILL.v1.md`
  - skill_doc: `skills/os/source_structure_findings_registration/SKILL.v1.md`
- `batch_impact_regression`:
  - summary: Analyze C# and SQL Server stored-procedure batch changes with deterministic combination regression and human-gated classification
  - meta: `skills/packs/batch-regression/batch-impact-regression/SKILL.v1.md`
  - skill_doc: `skills/packs/batch-regression/batch-impact-regression/SKILL.v1.md`
- `business_intake_scoping`:
  - summary: scope one business task into a boundary-visible responsibility unit from partial information
  - meta: `skills/packs/business-intake/business_intake_scoping/SKILL.v1.md`
  - skill_doc: `skills/packs/business-intake/business_intake_scoping/SKILL.v1.md`
- `business_learning_interview`:
  - summary: learn a business task through goal-first interview cycles and turn partial fragments into a structured provisional hypothesis
  - meta: `skills/packs/business-intake/business_learning_interview/SKILL.v1.md`
  - skill_doc: `skills/packs/business-intake/business_learning_interview/SKILL.v1.md`
- `conversation_topic_branch_mapping`:
  - summary: map normalized business conversation evidence into topic branches, topic-specific involvement, coordination candidates, and explicit unknowns
  - meta: `skills/packs/business-intake/conversation_topic_branch_mapping/SKILL.v1.md`
  - skill_doc: `skills/packs/business-intake/conversation_topic_branch_mapping/SKILL.v1.md`
- `decision_topology_analysis`:
  - summary: convert normalized business conversation evidence into an evidence-bound Decision Topology and Stakeholder Influence Map for the next business action
  - meta: `skills/packs/business-intake/decision_topology_analysis/SKILL.v1.md`
  - skill_doc: `skills/packs/business-intake/decision_topology_analysis/SKILL.v1.md`
- `async_constraint_derivation`:
  - summary: derive concurrency and asynchronous execution constraints from explicit design or code structure
  - meta: `skills/packs/constraint-derivation/async_constraint_derivation/SKILL.v1.md`
  - skill_doc: `skills/packs/constraint-derivation/async_constraint_derivation/SKILL.v1.md`
- `auth_constraint_derivation`:
  - summary: derive requirement confirmation gates from authentication and authorization structure
  - meta: `skills/packs/constraint-derivation/auth_constraint_derivation/SKILL.v1.md`
  - skill_doc: `skills/packs/constraint-derivation/auth_constraint_derivation/SKILL.v1.md`
- `code_constraint_derivation`:
  - summary: derive hidden assumptions and selected business constraints from explicit C# code choices
  - meta: `skills/packs/constraint-derivation/code_constraint_derivation/SKILL.v1.md`
  - skill_doc: `skills/packs/constraint-derivation/code_constraint_derivation/SKILL.v1.md`
- `commonality_derivation`:
  - summary: derive cross-cutting commonality candidates from completed primary constraint-derivation outputs
  - meta: `skills/packs/constraint-derivation/commonality_derivation/SKILL.v1.md`
  - skill_doc: `skills/packs/constraint-derivation/commonality_derivation/SKILL.v1.md`
- `constraint_derivation_index`:
  - summary: route design or implementation artifacts to constraint-derivation Skills and sequence the secondary commonality pass
  - meta: `skills/packs/constraint-derivation/constraint_derivation_index/SKILL.v1.md`
  - skill_doc: `skills/packs/constraint-derivation/constraint_derivation_index/SKILL.v1.md`
- `cross_constraint_derivation`:
  - summary: compare DDL structure and C# processing structure to surface missing flows and implicit assumptions
  - meta: `skills/packs/constraint-derivation/cross_constraint_derivation/SKILL.v1.md`
  - skill_doc: `skills/packs/constraint-derivation/cross_constraint_derivation/SKILL.v1.md`
- `design_constraint_derivation`:
  - summary: derive requirement confirmation gates from data-structure, database, relationship, and operation design
  - meta: `skills/packs/constraint-derivation/design_constraint_derivation/SKILL.v1.md`
  - skill_doc: `skills/packs/constraint-derivation/design_constraint_derivation/SKILL.v1.md`
- `integration_constraint_derivation`:
  - summary: derive requirement confirmation gates from external APIs, webhooks, files, and messaging integration structure
  - meta: `skills/packs/constraint-derivation/integration_constraint_derivation/SKILL.v1.md`
  - skill_doc: `skills/packs/constraint-derivation/integration_constraint_derivation/SKILL.v1.md`
- `integration_scenario_derivation`:
  - summary: derive integration-only failure and compensation scenarios from persistence, processing order, and external boundaries
  - meta: `skills/packs/constraint-derivation/integration_scenario_derivation/SKILL.v1.md`
  - skill_doc: `skills/packs/constraint-derivation/integration_scenario_derivation/SKILL.v1.md`
- `logic_constraint_derivation`:
  - summary: derive requirement confirmation gates from branching, calculations, state transitions, and approval logic
  - meta: `skills/packs/constraint-derivation/logic_constraint_derivation/SKILL.v1.md`
  - skill_doc: `skills/packs/constraint-derivation/logic_constraint_derivation/SKILL.v1.md`
- `ui_constraint_derivation`:
  - summary: derive requirement confirmation gates from UI structure, interaction states, and screen transitions
  - meta: `skills/packs/constraint-derivation/ui_constraint_derivation/SKILL.v1.md`
  - skill_doc: `skills/packs/constraint-derivation/ui_constraint_derivation/SKILL.v1.md`
- `crosspost_release`:
  - summary: prepare a reviewed article for per-channel publication with adaptation notes, release blockers, and human sign-off
  - meta: `skills/packs/editorial-ops/crosspost_release/SKILL.v1.md`
  - skill_doc: `skills/packs/editorial-ops/crosspost_release/SKILL.v1.md`
- `draft_authoring`:
  - summary: produce an article draft from explicit intake framing and source basis without hiding unsupported claims
  - meta: `skills/packs/editorial-ops/draft_authoring/SKILL.v1.md`
  - skill_doc: `skills/packs/editorial-ops/draft_authoring/SKILL.v1.md`
- `editorial_intake`:
  - summary: scope an article task into topic, audience, evidence basis, quality target, and publication boundary before drafting
  - meta: `skills/packs/editorial-ops/editorial_intake/SKILL.v1.md`
  - skill_doc: `skills/packs/editorial-ops/editorial_intake/SKILL.v1.md`
- `editorial_ops_index`:
  - summary: route editorial requests to the correct editorial-ops Skills and keep review and release stages explicit
  - meta: `skills/packs/editorial-ops/editorial_ops_index/SKILL.v1.md`
  - skill_doc: `skills/packs/editorial-ops/editorial_ops_index/SKILL.v1.md`
- `fact_review`:
  - summary: review article claims for factual separation, source support, names, numbers, links, and channel-sensitive wording risks
  - meta: `skills/packs/editorial-ops/fact_review/SKILL.v1.md`
  - skill_doc: `skills/packs/editorial-ops/fact_review/SKILL.v1.md`
- `reader_experience_review`:
  - summary: review a draft from the target reader perspective to surface confusion, drop-off points, context gaps, and pacing issues
  - meta: `skills/packs/editorial-ops/reader_experience_review/SKILL.v1.md`
  - skill_doc: `skills/packs/editorial-ops/reader_experience_review/SKILL.v1.md`
- `planning_flow`:
  - summary: Prepare traceable work planning and change policies from approved requirements and current source findings.
  - meta: `skills/planning_flow/SKILL.v1.md`
  - skill_doc: `skills/planning_flow/SKILL.v1.md`
- `pptx_spec_traceability`:
  - summary: extract PowerPoint specifications into traceable Markdown and write IDs back into the deck
  - meta: `skills/pptx_spec_traceability/SKILL.v1.md`
  - skill_doc: `skills/pptx_spec_traceability/SKILL.v1.md`
- `presentation_flow_review`:
  - summary: review and restructure an explanatory presentation so claims, premises, mechanisms, and conclusions follow an explicit causal flow
  - meta: `skills/presentation_flow_review/SKILL.v1.md`
  - skill_doc: `skills/presentation_flow_review/SKILL.v1.md`
- `python_implementation_flow`:
  - summary: Execute an approved and bounded Python change and prepare it for Python or QA review.
  - meta: `skills/python_implementation_flow/SKILL.v1.md`
  - skill_doc: `skills/python_implementation_flow/SKILL.v1.md`
- `python_review`:
  - summary: review Python code for language-dependent defects and system-level implementation risks beyond configured static diagnostics
  - meta: `skills/python_review/SKILL.v1.md`
  - skill_doc: `skills/python_review/SKILL.v1.md`
- `qa_gate_review`:
  - summary: perform evidence-based QA gate review with XDDP trace continuity, domain checks, and bounded system-impact review
  - meta: `skills/qa_gate_review/SKILL.v1.md`
  - skill_doc: `skills/qa_gate_review/SKILL.v1.md`
- `release_planning_flow`:
  - summary: prepare release materials, procedures, monitoring, event response, readiness, and verification evidence for CAB
  - meta: `skills/release_planning_flow/SKILL.v1.md`
  - skill_doc: `skills/release_planning_flow/SKILL.v1.md`
- `requirements_flow`:
  - summary: draft requirements and performance constraints while preserving explicit change differences
  - meta: `skills/requirements_flow/SKILL.v1.md`
  - skill_doc: `skills/requirements_flow/SKILL.v1.md`
- `review_report_composition`:
  - summary: compose detector review outputs into decision-readable reports while preserving technical judgment and evidence
  - meta: `skills/review_report_composition/SKILL.v1.md`
  - skill_doc: `skills/review_report_composition/SKILL.v1.md`
- `security_review`:
  - summary: review C# code and evidence for security risks
  - meta: `skills/security_review/SKILL.v1.md`
  - skill_doc: `skills/security_review/SKILL.v1.md`
- `source_structure_overview`:
  - summary: produce a reusable whole-system .NET source-structure overview with boundaries, flows, naming evidence, and validity limits
  - meta: `skills/source_structure_overview/SKILL.v1.md`
  - skill_doc: `skills/source_structure_overview/SKILL.v1.md`
- `test_flow`:
  - summary: Produce a reviewed test package from approved requirements, design evidence, and test-tool knowledge.
  - meta: `skills/test_flow/SKILL.v1.md`
  - skill_doc: `skills/test_flow/SKILL.v1.md`
- `test_tool_catalog_preparation`:
  - summary: prepare an evidence-backed XID-oriented catalog of test tools by domain and environment for test planning
  - meta: `skills/test_tool_catalog_preparation/SKILL.v1.md`
  - skill_doc: `skills/test_tool_catalog_preparation/SKILL.v1.md`
- `xlsx_spec_traceability`:
  - summary: extract spreadsheet specifications into Markdown, preserve workbook traceability, and write IDs back into the source workbook
  - meta: `skills/xlsx_spec_traceability/SKILL.v1.md`
  - skill_doc: `skills/xlsx_spec_traceability/SKILL.v1.md`
- `shared_asset_update_gate`:
  - summary: Analyze candidate-bound common management evidence for a selected Skill or Knowledge update without adopting or applying it.
  - meta: `skills/os/shared_asset_update_gate/SKILL.v1.md`
  - skill_doc: `skills/os/shared_asset_update_gate/SKILL.v1.md`
- `correction_retrospective_analyst`:
  - summary: Analyze a human-authorized bounded correction sequence as work evidence without executing general retrospective promotion.
  - meta: `skills/os/correction_retrospective_analyst/SKILL.v1.md`
  - skill_doc: `skills/os/correction_retrospective_analyst/SKILL.v1.md`

- `azure_work_item_integration`:
  - summary: operate workspace-scoped Azure import, explicit plan binding, guarded Task delivery and read-only reconciliation
  - meta: `skills/os/azure_work_item_integration/SKILL.v1.md`
  - skill_doc: `skills/os/azure_work_item_integration/SKILL.v1.md`

- `local_work_management`:
  - summary: local approved-plan persistence, Markdown/Mermaid and explicit observations independent of Azure
  - meta: `skills/os/local_work_management/SKILL.v1.md`
  - skill_doc: `skills/os/local_work_management/SKILL.v1.md`

## Notes

- Keep this file lightweight; adopted metadata and method belong in `SKILL.v1.md`.
- Runtime routing values and provenance belong in the repository adoption manifest and ExecutionBinding.
- Keep factual domain content in `knowledge/`.
- For the AI Agent OS reorganization view of `skills/`, see:
  - [OS utility and business skill classification design](../docs/designs/064_os_utility_and_business_skill_classification_design.md#xid-ECF29DC3E268)
  - [Business intake pack dependency design](../docs/packs/business-intake/065_business_intake_pack_dependency_design.md#xid-D334C1964342)

The new native `azure_work_item_integration` definition is a public routing entry,
not a legacy-migration adoption receipt. Inspect it using explicit
`skill definition-catalog --path skills/os/azure_work_item_integration/SKILL.v1.md`
and run the selected source with `skill run --definition`. The adoption-derived
`skill list` does not currently enumerate this native addition; public placement
does not imply maturity promotion or MCP distribution.

The native `local_work_management` public routing entry uses explicit definition-catalog/run selection, remains unassessed without promotion evidence, and is not a fabricated legacy adoption receipt. Azure integration is an optional separately authorized route.

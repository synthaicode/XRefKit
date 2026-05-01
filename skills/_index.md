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

## Semantic Routing Cues

- Default business-intake route:
  - if the business structure is still incomplete, start with `business_learning_interview`
  - move to `business_intake_scoping` only after the result becomes `ready_for_scoping`
- If the user has only fragments, tacit knowledge, bottlenecks, or wants the AI to ask the next best business question:
  - route to `business_learning_interview`
- If the user already has a partial business hypothesis and wants to shape one business unit with previous side / current scope / next side:
  - route to `business_intake_scoping`
- If the user already has an approved requirements/planning/design/implementation stage, use the existing workflow and phase skills instead.

## Category Indexes

- by task: `skills/index/by_task.md`
- by domain: `skills/index/by_domain.md`
- by tool: `skills/index/by_tool.md`

## Skills (compact)

- `import_skill`:
  - summary: import external skill content into this repository model
  - meta: `skills/import_skill/meta.md`
  - skill_doc: `skills/import_skill/SKILL.md`
- `doc_ship`:
  - summary: apply approved promotion candidates from `work/` into canonical repository assets
  - meta: `skills/doc_ship/meta.md`
  - skill_doc: `skills/doc_ship/SKILL.md`
- `retro`:
  - summary: review `work/` logs and propose promotion into canonical repository assets
  - meta: `skills/retro/meta.md`
  - skill_doc: `skills/retro/SKILL.md`
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
- `external_definition_change_analysis`:
  - summary: analyze applications driven by XML or other external definitions and generate a Markdown change-analysis note
  - meta: `skills/external_definition_change_analysis/meta.md`
  - skill_doc: `skills/external_definition_change_analysis/SKILL.md`
- `judgment_log`:
  - summary: write a judgment log with evidence, inference boundary, and next verification step
  - meta: `skills/judgment_log/meta.md`
  - skill_doc: `skills/judgment_log/SKILL.md`
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
  - meta: `skills/context_direction_guard/meta.md`
  - skill_doc: `skills/context_direction_guard/SKILL.md`
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
  - meta: `skills/business_intake_scoping/meta.md`
  - skill_doc: `skills/business_intake_scoping/SKILL.md`
- `business_learning_interview`:
  - summary: learn a business task from human fragments through iterative interview and produce the next best question
  - meta: `skills/business_learning_interview/meta.md`
  - skill_doc: `skills/business_learning_interview/SKILL.md`

## Notes

- Keep this file lightweight; detailed fields belong in `meta.md`.
- Keep behavior/procedure in `SKILL.md`.
- Keep factual domain content in `knowledge/`.


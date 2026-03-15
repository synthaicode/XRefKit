<!-- xid: 8D91F66DDBB7 -->
<a id="xid-8D91F66DDBB7"></a>

# Skills Index

This page is the routing entry for skills.
It is intentionally compact for context efficiency.
When asked "what skills are available?", answer from this file.

## Routing Rules

1. Read the user request and identify intent.
2. Narrow candidates using category indexes under `skills/index/`.
3. Read candidate `meta.md` files only (2-3 candidates max).
4. Open the selected `SKILL.md` and execute its procedure.
5. If domain knowledge is needed, resolve by XID from `knowledge/` via `xref`.

## Category Indexes

- by task: `skills/index/by_task.md`
- by domain: `skills/index/by_domain.md`
- by tool: `skills/index/by_tool.md`

## Skills (compact)

- `import_skill`:
  - summary: import external skill content into this repository model
  - meta: `skills/import_skill/meta.md`
  - skill_doc: `skills/import_skill/SKILL.md`
- `csharp_review`:
  - summary: review C# code beyond Roslyn-detectable diagnostics
  - meta: `skills/csharp_review/meta.md`
  - skill_doc: `skills/csharp_review/SKILL.md`
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
  - summary: decompose approved requirements into an execution plan draft
  - meta: `skills/planning_flow/meta.md`
  - skill_doc: `skills/planning_flow/SKILL.md`
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

## Notes

- Keep this file lightweight; detailed fields belong in `meta.md`.
- Keep behavior/procedure in `SKILL.md`.
- Keep factual domain content in `knowledge/`.


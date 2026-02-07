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
- `devto_check`:
  - summary: check Dev.to drafts and optionally rewrite
  - meta: `skills/devto_check/meta.md`
  - skill_doc: `skills/devto_check/SKILL.md`
- `csharp_review`:
  - summary: review C# code beyond Roslyn-detectable diagnostics
  - meta: `skills/csharp_review/meta.md`
  - skill_doc: `skills/csharp_review/SKILL.md`
- `libecity_mamoru`:
  - summary: assess and strengthen personal/household protection readiness
  - meta: `skills/libecity_mamoru/meta.md`
  - skill_doc: `skills/libecity_mamoru/SKILL.md`
- `password_management`:
  - summary: assess and improve password hygiene with vault and MFA
  - meta: `skills/password_management/meta.md`
  - skill_doc: `skills/password_management/SKILL.md`

## Notes

- Keep this file lightweight; detailed fields belong in `meta.md`.
- Keep behavior/procedure in `SKILL.md`.
- Keep factual domain content in `knowledge/`.

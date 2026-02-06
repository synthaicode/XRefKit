# Skills Index

This page is the routing entry for skills.
It lists each skill with scope and when to use it.
When asked "what skills are available?", answer from this file.

## Routing Rules

1. Read the user request and identify intent.
2. Match intent to one skill from the catalog below.
3. Open the selected skill page and execute its procedure.
4. If domain knowledge is needed, resolve by XID from `knowledge/` via `xref`.

## Skill Catalog

### `import_skill`

- summary: import an external skill into this repository's split model (skill vs domain knowledge)
- use_when: a user asks to bring a skill from another repo/source and make it runnable here
- input: source URL or ZIP file path, and optional target skill id
- output: `skills/<skill_id>/SKILL.md`, updated `skills/_index.md`, and referenced knowledge in `knowledge/`
- constraints: do not leave domain facts embedded in skill files; use XID references
- skill_doc: `skills/import_skill/SKILL.md`
- knowledge_refs: none (uses existing domain fragments as needed)

## Skill Entry Template

### `<skill_id>`

- summary: one-line purpose of this skill
- use_when: concrete trigger conditions
- input: expected input shape
- output: expected output shape
- constraints: safety/quality boundaries
- skill_doc: `skills/<skill_id>/SKILL.md`
- knowledge_refs: `knowledge/...#xid-<XID>`

## Notes

- Keep behavior/procedure in skill files only.
- Keep factual domain content in `knowledge/`.
- Do not duplicate domain facts in this index.

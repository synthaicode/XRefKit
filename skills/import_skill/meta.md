# Skill Meta: import_skill

- skill_id: `import_skill`
- summary: import external skill content into this repository split model
- use_when: external skill needs to be made runnable in this repo
- input: source URL or ZIP path, optional target skill id
- output: normalized `skills/<skill_id>/SKILL.md` and index registration
- constraints: keep domain facts out of skill body; use `knowledge/...#xid-...`
- tags: `import`, `normalization`, `xref`
- skill_doc: `./SKILL.md`
- knowledge_refs: none

<!-- xid: 1DF4555E1B02 -->
<a id="xid-1DF4555E1B02"></a>

# Skill Meta: import_skill

- skill_id: `import_skill`
- summary: import external skill content into this repository split model
- use_when: external skill needs to be made runnable in this repo
- input: source URL or ZIP path, optional target skill id
- output: normalized `skills/<skill_id>/SKILL.md` and index registration
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: import external skill content into this repository split model
- responsibility: external skill needs to be made runnable in this repo
- os_contract: v1
- constraints: keep domain facts out of skill body; use `knowledge/...#xid-...`; run policy inspection before import; compose the context-direction guard by default unless the imported skill explicitly qualifies for the closed-world exception
- tags: `import`, `normalization`, `xref`
- skill_doc: `./SKILL.md`
- knowledge_slots:

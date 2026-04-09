<!-- xid: 5A7C2D4E9130 -->
<a id="xid-5A7C2D4E9130"></a>

# Skill Meta: xlsx_spec_traceability

- skill_id: `xlsx_spec_traceability`
- summary: extract spreadsheet specifications into Markdown, assign traceability IDs, connect embedded images to nearby specification text, and write the IDs back into the workbook
- use_when: user needs to convert Excel-based specifications into Markdown artifacts while preserving source traceability and reducing review burden in the original workbook
- input: source xlsx path, optional target Markdown destination, optional workbook or sheet scope, optional traceability ID prefix
- output: Markdown specification fragments, image-linked screen-item descriptions, traceability ID map, updated xlsx with written-back IDs, unresolved list
- execution_mode: `local_default`
- guard_policy: `required`
- constraints: keep the workbook path and sheet/cell/image position explicit; do not separate image-derived items from the source location they came from; write IDs back into the original workbook or the controlled workbook copy used as the source of truth
- lifecycle:
  - startup: confirm source workbook path, target scope, and ID policy
  - planning: map sheets, tables, free-text blocks, and embedded images into extraction units
  - execution: extract textual specification, connect image position to nearby text, create Markdown fragments, assign IDs, and write the IDs back to the workbook
  - monitoring_and_control: record ambiguity when image meaning and surrounding text disagree
  - closure: finalize Markdown outputs, verify workbook write-back, and preserve source pointers
- tags: `xlsx`, `excel`, `specification`, `traceability`, `image`, `import`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../docs/020_sources.md#xid-2FAD591BF725`

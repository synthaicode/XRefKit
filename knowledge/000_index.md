<!-- xid: 23059118FBB9 -->
<a id="xid-23059118FBB9"></a>

# Knowledge Index (domain canonical)

This folder stores shared domain knowledge fragments.
Skills should reference these pages by XID and load only what is needed.

## Rules

- Keep one fragment per coherent topic.
- Preserve XID blocks.
- Use links with `#xid-...` for cross-fragment references.
- After edits, run `python -m fm xref fix`.

## Entries

- [C# review spec](csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA)
- [C# quality review criteria](quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Investigation coverage checklist](investigation/100_investigation_coverage_checklist.md#xid-91E2A7C56101)
- [Management table schema](organization/110_management_table_schema.md#xid-7A2F4C8D1101)
- [Metrics definition](organization/120_metrics_definition.md#xid-7A2F4C8D1201)
- [Group boundary rules](organization/130_group_boundary_rules.md#xid-7A2F4C8D1301)

## Private knowledge

Private domain knowledge lives in `knowledge_private/` (gitignored).
See `knowledge_private/000_index.local.md` for entries.

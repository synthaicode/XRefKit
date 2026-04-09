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
- [Common source analysis criteria](source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Custom framework common criteria](source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002)
- [C# custom framework analysis criteria](csharp/110_custom_framework_analysis_criteria.md#xid-30E6A4F6F3AB)
- [C# quality review criteria](quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Test design criteria](quality/110_test_design_criteria.md#xid-8C4D2A7E5102)
- [IPA test viewpoint supplement](quality/120_ipa_test_viewpoint_supplement.md#xid-8C4D2A7E5103)
- [Investigation coverage checklist](investigation/100_investigation_coverage_checklist.md#xid-91E2A7C56101)
- [Management table schema](organization/110_management_table_schema.md#xid-7A2F4C8D1101)
- [Metrics definition](organization/120_metrics_definition.md#xid-7A2F4C8D1201)
- [IPA release activity catalog](operations/100_ipa_release_activity_catalog.md#xid-7B3E5D1A6101)
- [Group boundary rules](organization/130_group_boundary_rules.md#xid-7A2F4C8D1301)
- [LLM review knowledge usage rules](organization/140_llm_review_knowledge_usage_rules.md#xid-7A2F4C8D1401)
- [Implementation assumption gap handling](organization/150_implementation_assumption_gap_handling.md#xid-7A2F4C8D1501)
- [Context direction guard rules](organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)
- [XDDP basics](organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)

## Private knowledge

Private domain knowledge lives in `knowledge_private/` (gitignored).
See `knowledge_private/000_index.local.md` for entries.

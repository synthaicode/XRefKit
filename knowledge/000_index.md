<!-- xid: 23059118FBB9 -->
<a id="xid-23059118FBB9"></a>

# Knowledge Index (domain canonical)

This folder stores shared domain knowledge fragments.
Skills should reference these pages by XID and load only what is needed.

## Rules

- Keep one fragment per coherent topic.
- Preserve XID blocks.
- Use links with `#xid-...` for cross-fragment references.
- After edits, run `python -m xrefkit xref fix`.

## Entries

### C#

- [C# review spec](csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA)
- [C# custom framework analysis criteria](csharp/110_custom_framework_analysis_criteria.md#xid-30E6A4F6F3AB)
- [C# test synchronization patterns](csharp/120_csharp_test_synchronization_patterns.md#xid-4314A1A73CAF)
- [C# custom attribute design principles](csharp/130_csharp_custom_attribute_design_principles.md#xid-D9C3F0A7E412)

### Database

- [Database design viewpoints](database/100_database_design_viewpoints.md#xid-E7D4A11B8C06)
- [Database current-state analysis viewpoints](database/110_database_current_state_analysis_viewpoints.md#xid-F9B3C6A70412)

### Architecture

- [Service catalog Knowledge schema](architecture/100_service_catalog_knowledge_schema.md#xid-7A2F4C8D2201)
- [Service interaction and data-flow Knowledge viewpoints](architecture/110_service_interaction_data_flow_viewpoints.md#xid-7A2F4C8D2301)

### Investigation

- [Investigation coverage checklist](investigation/100_investigation_coverage_checklist.md#xid-91E2A7C56101)

### Operations

- [IPA release activity catalog](operations/100_ipa_release_activity_catalog.md#xid-7B3E5D1A6101)
- [Legacy Flow Skill migration rules](operations/130_legacy_flow_skill_migration_rules.md#xid-7B3E5D1A6104)
- [Business card PDF generation rules](operations/140_business_card_pdf_generation_rules.md#xid-9142A8CDCF76)
- [Marketing video TTS engine guidance](operations/150_marketing_video_tts_engine_guidance.md#xid-9C41D7B2A5E1)

### Organization

- [Management table schema](organization/110_management_table_schema.md#xid-7A2F4C8D1101)
- [Metrics definition](organization/120_metrics_definition.md#xid-7A2F4C8D1201)
- [Judgment log schema](organization/121_judgment_log_schema.md#xid-7B4C2D91E621)
- [Group boundary rules](organization/130_group_boundary_rules.md#xid-7A2F4C8D1301)
- [LLM review knowledge usage rules](organization/140_llm_review_knowledge_usage_rules.md#xid-7A2F4C8D1401)
- [Implementation assumption gap handling](organization/150_implementation_assumption_gap_handling.md#xid-7A2F4C8D1501)
- [Temporary traceability comment rule](organization/151_temporary_traceability_comment_rule.md#xid-22E4C7AC7063)
- [Context direction guard rules](organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601)
- [XDDP basics](organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)
- [Agent diff review gate design](organization/180_agent_diff_review_gate_design.md#xid-7A2F4C8D1801)
- [Quality feedback return rules](organization/190_quality_feedback_return_rules.md#xid-7A2F4C8D1901)
- [Domain knowledge ontology rules](organization/200_domain_knowledge_ontology_rules.md#xid-5803607419B9)
- [Term relationship model](organization/210_term_relationship_model.md#xid-7A2F4C8D2101)

### Business Pack Knowledge

#### Business intake

- [Business intake scoping rules](packs/business-intake/110_business_intake_scoping_rules.md#xid-7B3E5D1A6102)
- [Business learning interview rules](packs/business-intake/120_business_learning_interview_rules.md#xid-7B3E5D1A6103)

#### Constraint derivation

- [Constraint derivation framework](packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190)
- [Design constraint derivation catalog](packs/constraint-derivation/120_design_constraint_derivation_catalog.md#xid-2D14F88A6C01)
- [UI constraint derivation catalog](packs/constraint-derivation/130_ui_constraint_derivation_catalog.md#xid-31C5A06B7E22)
- [Logic constraint derivation catalog](packs/constraint-derivation/140_logic_constraint_derivation_catalog.md#xid-4E5B8923C912)
- [Integration constraint derivation catalog](packs/constraint-derivation/150_integration_constraint_derivation_catalog.md#xid-6F0D7C1A2E44)
- [Async constraint derivation catalog](packs/constraint-derivation/160_async_constraint_derivation_catalog.md#xid-72ECA94D1B35)
- [Auth constraint derivation catalog](packs/constraint-derivation/170_auth_constraint_derivation_catalog.md#xid-8B14D9E70326)
- [Commonality derivation signals](packs/constraint-derivation/180_commonality_derivation_signals.md#xid-9C27AE51D648)
- [Code constraint derivation catalog](packs/constraint-derivation/190_code_constraint_derivation_catalog.md#xid-A1D4E8C93B71)
- [Cross constraint derivation catalog](packs/constraint-derivation/200_cross_constraint_derivation_catalog.md#xid-B2E5F9DA4C82)
- [Integration scenario derivation catalog](packs/constraint-derivation/210_integration_scenario_derivation_catalog.md#xid-C3F60AEB5D93)

#### Editorial operations

- [Editorial operations framework](packs/editorial-ops/110_editorial_operations_framework.md#xid-F9E58E2BAD21)
- [Reader capability model](packs/editorial-ops/120_reader_capability_model.md#xid-125B6C5E3630)

### Quality

- [C# quality review criteria](quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Test design criteria](quality/110_test_design_criteria.md#xid-8C4D2A7E5102)
- [IPA test viewpoint supplement](quality/120_ipa_test_viewpoint_supplement.md#xid-8C4D2A7E5103)

### Source Analysis

- [Common source analysis criteria](source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Custom framework common criteria](source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002)
- [Dotnet change analysis viewpoints](source_analysis/120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)
- [Structure-analysis determinism tiers](source_analysis/121_structure_analysis_determinism_tiers.md#xid-5301B897BA41)
- [C# error-policy detection patterns](source_analysis/130_csharp_error_policy_detection_patterns.md#xid-C0DBC37E2A13)
- [External-definition change analysis viewpoints](source_analysis/130_external_definition_change_analysis_viewpoints.md#xid-4D91A26BE301)
- [C# error-policy detection determinism tiers](source_analysis/131_csharp_error_policy_locator_tiers.md#xid-D1F4A7C3E209)
- [C# error-policy external analyzer rule map](source_analysis/132_csharp_error_policy_analyzer_rule_map.md#xid-C7A1E94D3B62)
- [C# naming-convention extraction (brownfield)](source_analysis/140_csharp_naming_convention_extraction.md#xid-B4F7E1A2C903)
- [Roslyn analyzer quality-check applicability](source_analysis/150_roslyn_analyzer_quality_check_applicability.md#xid-A1B243BF7D5D)
- [Structure graph as TM coverage backstop](source_analysis/160_structure_graph_tm_backstop.md#xid-163AD9936979)
- [Current source structure findings catalog](source_analysis/170_current_source_structure_findings_catalog.md#xid-A9E742B1C6D0)
- [Maverick.NET Friendbook XML-command structure findings](source_analysis/171_maverick_net_friendbook_structure_findings.md#xid-B4F8D2A91C03)
- [Modular Monolith with DDD API structure findings](source_analysis/172_modular_monolith_ddd_api_structure_findings.md#xid-D8F2A6C91B74)

## Private knowledge

Private domain knowledge lives in `knowledge_private/` (gitignored).
See `knowledge_private/000_index.local.md` for entries. <!-- private-ref-ok: boundary-convention pointer; target is gitignored and no private content is exposed -->

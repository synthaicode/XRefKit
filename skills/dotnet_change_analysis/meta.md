<!-- xid: 1F4A6D20B8E1 -->
<a id="xid-1F4A6D20B8E1"></a>

# Skill Meta: dotnet_change_analysis

- skill_id: `dotnet_change_analysis`
- summary: analyze .NET application structure and generate a Markdown change-analysis note for later design or implementation work
- use_when: user needs repository-based .NET structure analysis, impact investigation, or a Markdown change-analysis note before changing code, especially brownfield code where responsibility separation is not documented and must be read from the code
- input: target path, change request or analysis objective, optional scope filters, optional output path
- output: Markdown change-analysis note, scoped target list, impacted boundary list, uncertainty list, viewpoint check results, change placement basis, prohibited-changes list derived from extracted local rules, and a handoff list for defect-level or security-scope discoveries
- maturity: `stable`
- execution_mode: `subagent_preferred`
- model_tier: `standard`
- guard_policy: `required`
- os_contract:
  - version: `1`
  - worklist_policy: `required`
  - execution_role: `required`
  - check_role: `required`
  - logging_policy: `session_required`
  - judgment_log_policy: `required_when_non_trivial`
  - unknown_risk_policy: `explicit`
  - closure_gate: `required`
  - handoff_policy: `explicit`
- constraints: do not decide implementation policy by default; record unknowns explicitly; confirm custom-attribute activation instead of stopping at inventory; record structure and change impact only — defect-level findings hand off to csharp_review and vulnerability assessment hands off to security_review
- lifecycle:
  - startup: confirm target path, change objective, scope, and required viewpoints
  - planning: define scope, output path, viewpoint buckets, and safe scope split for read-only analysis
  - execution: extract the de-facto responsibility split from behavior evidence, analyze structure, boundaries, DI registration lifetimes, local pipeline structure and ordering rules, convention-based discovery, build-configuration variants, error-handling contract, security boundary placement, logging, attributes, concurrency, performance, resources, tests, record the change placement basis, derive the prohibited-changes list from the extracted rules, and generate a Markdown note
  - monitoring_and_control: treat unrecorded viewpoints as leaks and downgrade weak conclusions to `unknown`
  - closure: return the Markdown note, impacted boundaries, and unresolved items with reasons
- tags: `dotnet`, `csharp`, `analysis`, `investigation`, `markdown`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
  - `../../capabilities/quality/190_cap_qa_011_roslyn_analyzer_acceptance.md#xid-94C1B7B9920A`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001`
  - `../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002`
  - `../../knowledge/source_analysis/120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201`
  - `../../knowledge/source_analysis/121_structure_analysis_determinism_tiers.md#xid-5301B897BA41`
  - `../../knowledge/source_analysis/160_structure_graph_tm_backstop.md#xid-163AD9936979`
- observation_refs:
  - `../../work/reports/2026-06-11_skill_improvement_note_dotnet_change_analysis.md`
  - `../../work/sessions/2026-06-11_skill_run_dotnet_change_analysis.md`
- governance_refs:
  - `../../work/reports/2026-06-11_promotion_record_dotnet_change_analysis.md`

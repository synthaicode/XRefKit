<!-- xid: B150A2A54169 -->
<a id="xid-B150A2A54169"></a>

# Skill Meta: csharp_error_policy_extraction

- skill_id: `csharp_error_policy_extraction`
- summary: extract the existing de-facto error policy from C# source as an inventory, a category-by-disposition matrix, detected contradictions, and explicit coverage limits
- use_when: user needs the implemented error policy of a C# codebase made explicit before changing error handling, unifying conventions, or arbitrating inconsistent failure behavior — a deep-dive of the error-handling-contract viewpoint of `dotnet_change_analysis`, not a defect review
- input: target path (repository, solution, or project), optional scope filters, optional existing change-analysis note from `dotnet_change_analysis`, optional output path
- output: Markdown error-policy report containing the error-handling inventory with per-item record schema, category x disposition matrix with de-facto policy candidates, contradiction list with adjudication material, DI startup-throw triage, and a mandatory coverage-limits section
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `standard`
- guard_policy: `required`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: extract the existing de-facto error policy from C# source as an inventory, a category-by-disposition matrix, detected contradictions, and explicit coverage limits
- role_responsibilities:
  - executor: user needs the implemented error policy of a C# codebase made explicit before changing error handling, unifying conventions, or arbitrating inconsistent failure behavior — a deep-dive of the error-handling-contract viewpoint of `dotnet_change_analysis`, not a defect review
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
- constraints: extraction only — record implemented behavior, never decide what the policy should be; do not fix code; never claim exhaustive coverage of omission policies; every non-trivial conclusion carries an evidence path; defect-level findings (async hangs, race conditions) hand off to csharp_review and vulnerability findings hand off to security_review; the coverage-limits section is mandatory in every report
- lifecycle:
  - startup: confirm target path, scope, output path, and whether a prior change-analysis note exists as input
  - planning: define scan scope, split inventory buckets (explicit handling, dotnet-specific paths, omission policies, global handlers), and declare the search-pattern set
  - execution: run Phase 1 inventory extraction, Phase 2 normalization into the category x disposition matrix, and Phase 3 contradiction detection with coverage limits, recording evidence paths throughout
  - monitoring_and_control: downgrade weakly supported classifications to `unclassified` or intent `inferred`; treat unrecorded buckets as leaks; keep detection limits explicit instead of claiming completeness
  - closure: return the error-policy report, the de-facto policy candidates, the contradiction list, unresolved unknowns with reasons, and the handoff list
- tags: `dotnet`, `csharp`, `analysis`, `error-handling`, `policy-extraction`, `markdown`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001`
  - `../../knowledge/source_analysis/120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201`
  - `../../knowledge/source_analysis/130_csharp_error_policy_detection_patterns.md#xid-C0DBC37E2A13`
- observation_refs:
  - `../../work/sessions/2026-06-12_skill_run_skill_flow_authoring.md`
  - `../../work/sessions/2026-06-12_skill_run_csharp_error_policy_extraction.md`
  - `../../work/reports/2026-06-12_error_policy_report_mailkit_pooling.md`

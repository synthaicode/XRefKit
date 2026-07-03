<!-- xid: 218463E0F3ED -->
<a id="xid-218463E0F3ED"></a>

# Skill Meta: csharp_review

- skill_id: `csharp_review`
- summary: review C# code with a manual focus on non-Roslyn-detectable risks
- use_when: user asks for C# review beyond Roslyn/compiler diagnostics, including async hangs, synchronization risks, or fake-clock wait behavior that Roslyn does not catch
- input: target path, optional scope filters, optional output mode
- output: check item matrix with pass/fail/escalated/not-applicable statuses, evidence-based findings for attribute misuse, resource efficiency, operational resilience, synchronization, required business input integrity, lifecycle support, error handling, time/culture correctness, state/determinism boundaries, uncertainty/escalation paths, contract/schema resilience, and traceability/context propagation, implementation-return feedback items when applicable, plus a handoff list for out-of-scope findings
- maturity: `stable`
- execution_mode: `subagent_preferred`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: `software_development`
- tuning: `C#`
- responsibility: quality check
- os_contract: v1
- constraints: exclude Roslyn-detectable issues; do not hard-fail unknown attribute values by whitelist; do not expand into security review or design-assumption derivation — route those findings to security_review or the constraint-derivation pack through the handoff list
- lifecycle:
  - startup: confirm target path and review scope, then load the review spec
  - planning: define review scope, output mode, category buckets, custom-framework analysis targets, and subagent split when scope-separated parallel review is safe
  - execution: establish Roslyn baseline and execute category-specific checks with local-evidence-first handling for custom frameworks
  - monitoring_and_control: exclude diagnostics-covered issues and downgrade unclear findings to `needs_confirmation`
  - closure: return findings, category summaries, and explicit review conditions
- tags: `csharp`, `review`, `dotnet`, `quality`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/quality/180_cap_qa_010_beyond_diagnostics_code_risk_review.md#xid-4A3CA9ECFA71`
  - `../../capabilities/quality/190_cap_qa_011_roslyn_analyzer_acceptance.md#xid-94C1B7B9920A`
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/150_cap_mgt_006_independent_run_verification.md#xid-E37644FAA6F2`
- knowledge_refs:
  - `../../knowledge/csharp/100_csharp_review_spec.md#xid-30E6A4F6F3AA`
  - `../../knowledge/organization/190_quality_feedback_return_rules.md#xid-7A2F4C8D1901`
  - `../../knowledge/csharp/120_csharp_test_synchronization_patterns.md#xid-4314A1A73CAF`
  - `../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001`
  - `../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002`
  - `../../knowledge/csharp/110_custom_framework_analysis_criteria.md#xid-30E6A4F6F3AB`
- observation_refs:
  - `../../observations/2026-06-23_session_csharp_review_generalized_observation.md`

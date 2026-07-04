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
- knowledge_slots:
  - name=review_spec; query=C# review spec beyond diagnostics; domain=csharp; min=1; required
  - name=test_sync; query=C# test synchronization patterns; domain=csharp
  - name=source_criteria; query=common source analysis criteria; domain=source_analysis
  - name=custom_framework_common; query=custom framework common criteria; domain=source_analysis
  - name=custom_framework; query=custom framework analysis criteria; domain=csharp
  - name=feedback_rules; bind=7A2F4C8D1901
- observation_refs:
  - `../../observations/2026-06-23_session_csharp_review_generalized_observation.md`

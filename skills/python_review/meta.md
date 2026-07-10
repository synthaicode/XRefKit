<!-- xid: B4C1D2E3F4A5 -->
<a id="xid-B4C1D2E3F4A5"></a>

# Skill Meta: python_review

- skill_id: `python_review`
- summary: review Python code for language-dependent defects and system-level implementation risks beyond configured static diagnostics
- use_when: user asks for Python code review beyond configured formatter, linter, type-checker, test, or dependency diagnostics, including async/event-loop hazards, resource lifetime risks, silent fallback behavior, schema/coercion risks, import-time side effects, or implementation patterns that can break system-level behavior
- input: target path, optional scope filters, optional output mode
- output: check item matrix with pass/needs_confirmation/not_applicable category statuses, static-analysis boundary table separating confirmed_by_static_analysis, not_detectable_by_static_analysis, and requires_runtime_or_human_evidence, detector facts, evidence-based findings with critical/major/minor/needs_confirmation severity, a blocked/needs-review/proceed gate verdict, and findings for Python language-dependent issues and system-level implementation risks across static baseline, resource efficiency, operational resilience, synchronization, required business input integrity, lifecycle support, error handling, time/locale/encoding correctness, state/determinism boundaries, uncertainty/escalation paths, contract/schema resilience, and traceability/context propagation, plus handoff items for implementation-local findings to python_implementation_flow, XDDP trace gaps, security findings, design/business assumptions outside this Skill, or report composition by review_report_composition
- maturity: `trial`
- execution_mode: `subagent_preferred`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: `software_development`
- tuning: `Python`
- responsibility: `quality check`
- os_contract: v1
- constraints: exclude issues already covered by configured static diagnostics; do not treat clean static analysis as proof of runtime, framework, deployment, lifecycle, third-party API, or business-intent correctness; do not assume public-framework semantics for custom Python frameworks without local evidence; do not replace XDDP trace-continuity review; do not expand into security review, design-assumption derivation, or report composition; route those findings to qa_gate_review, security_review, the constraint-derivation pack, or review_report_composition through the handoff list; when the review spans enough categories, projects, files, or evidence to risk context overflow, split execution into subagents by scope or category instead of running all checks in one context
- lifecycle:
  - startup: confirm target path and review scope, identify configured Python static baseline tools, then load the Python review spec
  - planning: define review scope, output mode, category buckets, custom-framework analysis targets, and subagent split when scope-separated review is safe or context overflow is likely
  - execution: establish configured static baseline, record what static analysis can and cannot prove, and execute category-specific checks with local-evidence-first handling for custom frameworks
  - monitoring_and_control: exclude diagnostics-covered issues and downgrade static-analysis gaps to `needs_confirmation` or `unknown` instead of passing them silently
  - closure: return findings, category summaries, gate verdict, and explicit review conditions
- tags: `python`, `review`, `quality`, `engineering`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=review_spec; bind=A9B7C6D5E4F1
  - name=source_criteria; bind=5F21C8A41001
  - name=custom_framework_common; bind=5F21C8A41002
  - name=custom_framework; bind=A9B7C6D5E4F2
  - name=feedback_rules; bind=7A2F4C8D1901
  - name=gate_design; bind=7A2F4C8D1801
- observation_refs:
  - `../../observations/2026-07-07_session_python_skill_authoring.md`

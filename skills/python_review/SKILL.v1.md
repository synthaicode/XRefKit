---
{
  "schema_version": 1,
  "skill_id": "python_review",
  "xid": "F1A7C3D9E241",
  "aliases": ["B4C1D2E3F4A6", "B4C1D2E3F4A5"],
  "summary": "review Python code for language-dependent defects and system-level implementation risks beyond configured static diagnostics",
  "applies_when": [
    "Python code review is requested beyond configured formatter, linter, type-checker, test, or dependency diagnostics",
    "the review needs language-dependent, asynchronous, resource, framework, or system-level evidence"
  ],
  "exclusions": [
    "issues already covered by configured static diagnostics are outside this review",
    "XDDP trace-continuity review belongs to qa_gate_review",
    "security review, design-assumption derivation, and human-facing report composition are handed to their owning Skills",
    "this Skill produces findings and routing evidence; remediation adoption remains a human decision"
  ],
  "inputs": ["repository, package, service, directory, or file target", "optional scope filters", "optional findings-only or findings-with-fixes output mode"],
  "outputs": ["category check matrix", "static-analysis boundary table", "evidence-based findings with severity and remediation", "gate-routing verdict and handoff items"],
  "criteria": [
    {"id": "static_boundary", "statement": "The configured static baseline is explicit and every category separates confirmed_by_static_analysis, not_detectable_by_static_analysis, and requires_runtime_or_human_evidence.", "verification": "Inspect the boundary table and record baseline_unavailable as a risk when configured tools cannot be collected."},
    {"id": "category_coverage", "statement": "Every active category has a findings result or explicit empty result, including resource, resilience, synchronization, input, lifecycle, exception, time/locale/encoding, state, contract, and traceability categories.", "verification": "Compare the result matrix with the active categories and record evidence or an explicit applicability reason."},
    {"id": "finding_evidence", "statement": "Each finding carries an evidence path, violated condition, severity, remediation, and named needs_confirmation gap when evidence is incomplete.", "verification": "Inspect every finding and do not treat clean static analysis as proof of runtime, deployment, framework, lifecycle, third-party API, or business correctness."},
    {"id": "scope_and_handoff", "statement": "Out-of-scope security, design, XDDP, implementation-return, and report-composition discoveries remain explicit handoffs with a next owner.", "verification": "Check the handoff list and confirm no out-of-scope discovery was silently absorbed."},
    {"id": "human_gate_authority", "statement": "The pre-CI verdict routes review work and does not claim correctness or replace human adoption judgment.", "verification": "Confirm blocked, needs-review, or proceed follows the declared evidence conditions and unresolved concerns remain visible."}
  ],
  "knowledge_needs": [
    {"id": "python_review_spec", "query": "Python review spec beyond configured diagnostics", "required_when": "Required for language-specific review criteria.", "seed_xids": ["A9B7C6D5E4F1"]},
    {"id": "quality_feedback_rules", "query": "quality feedback return rules", "required_when": "Required when findings are returned to an implementation owner.", "seed_xids": ["7A2F4C8D1901"]},
    {"id": "common_source_analysis", "query": "common source analysis criteria", "required_when": "Required for language-neutral resource, resilience, synchronization, input, and error criteria.", "seed_xids": ["5F21C8A41001"]},
    {"id": "custom_framework_common", "query": "custom framework common criteria", "required_when": "Required when a custom framework is present.", "seed_xids": ["5F21C8A41002"]},
    {"id": "python_custom_framework", "query": "Python custom framework analysis criteria", "required_when": "Required when Python framework extensions or custom runtime wiring are in scope.", "seed_xids": ["A9B7C6D5E4F2"]},
    {"id": "agent_diff_gate", "query": "agent diff review gate design", "required_when": "Required when producing the pre-CI gate-routing verdict.", "seed_xids": ["7A2F4C8D1801"]}
  ],
  "control_refs": []
}
---
<!-- xid: F1A7C3D9E241 -->
<a id="xid-F1A7C3D9E241"></a>

# Skill: python_review

## Review boundary

Confirm the target and declared scope, identify configured formatter, linter, type-checker, test, and dependency baselines, and keep issues already covered by those diagnostics outside this Skill. Review Python behavior beyond that baseline across resource efficiency, operational resilience, synchronization and concurrency, required business input integrity, support lifecycle, exception paths, time/locale/encoding, state and determinism, contract and schema resilience, uncertainty and escalation, traceability/context propagation, and custom framework behavior. Preserve a static-analysis boundary table for every active category.

## Evidence and method

Load the applicable Knowledge entries before claiming coverage. For each category, record `confirmed_by_static_analysis`, `not_detectable_by_static_analysis`, or `requires_runtime_or_human_evidence`. Verify decorators, registration, dependency injection, plugin discovery, lifecycle, async behavior, settings, and serialization from local framework evidence. Inspect resource lifetime, event-loop and synchronization hazards, silent fallbacks and coercion, import-time effects, exception paths, locale and encoding, state transitions, schema contracts, and trace links. Every finding includes an evidence path, severity (`critical`, `major`, `minor`, or `needs_confirmation`), violated condition, and remediation; category absence remains an explicit pass or not_applicable result.

## Unknown, stop, and handoff

If a repository, package, service, framework boundary, static baseline, lifecycle source, third-party API, or runtime precondition cannot be established, record `needs_confirmation` and the missing evidence. Mirror closure-affecting gaps as `unknown` concerns and record `baseline_unavailable` as a risk when applicable. Do not infer correctness from clean static analysis. Stop expanding this review when evidence requests fixing, security assessment, design/business-meaning derivation, XDDP trace judgment, or report composition; retain the discovery as a handoff to `python_implementation_flow`, `security_review`, `qa_gate_review`, the constraint-derivation pack, or `review_report_composition`. Human reviewers decide disputed findings, remediation adoption, and final use of the result.

## Completion

Return the complete category matrix, static-analysis boundary, detector facts, findings, pre-CI verdict (`blocked`, `needs-review`, or `proceed`), downgrade reason when needed, required follow-up, and all unresolved or handoff items. `proceed` requires declared scope and trace, triage completion, explicit configured baseline state, a result for every active category, no closure-affecting `needs_confirmation`, and no open concern.

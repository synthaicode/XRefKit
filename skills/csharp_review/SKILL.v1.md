---
{
  "schema_version": 1,
  "skill_id": "csharp_review",
  "xid": "F1A7C3D9E240",
  "aliases": ["466B980B8ED3", "218463E0F3ED"],
  "summary": "review C# code for language-dependent defects and system-level implementation risks beyond Roslyn diagnostics",
  "applies_when": [
    "C# code review is requested beyond compiler or Roslyn diagnostics",
    "the review needs language-dependent, asynchronous, synchronization, resource, or system-level evidence"
  ],
  "exclusions": [
    "Roslyn-detectable issues are outside this review",
    "XDDP trace-continuity review belongs to qa_gate_review",
    "security review, design-assumption derivation, and human-facing report composition are handed to their owning Skills",
    "this Skill produces findings and routing evidence; remediation adoption remains a human decision"
  ],
  "inputs": ["repository, solution, project, directory, or file target", "optional scope filters", "optional findings-only or findings-with-fixes output mode"],
  "outputs": ["category check matrix", "evidence-based findings with severity and remediation", "gate-routing verdict", "unknowns and handoff items"],
  "criteria": [
    {"id": "category_coverage", "statement": "Every active review category has a pass, fail, escalated, or not_applicable result, including the Roslyn baseline.", "verification": "Compare the result matrix with the active categories and record evidence or an explicit applicability reason."},
    {"id": "csharp_risk_axes", "statement": "The review considers attribute activation, resources, resilience, synchronization, required input integrity, lifecycle, exceptions, time and culture, state and determinism, contracts, and traceability when applicable.", "verification": "Check that each applicable axis has evidence-backed detector facts and that fake-clock waits and async wake-up paths are considered."},
    {"id": "finding_evidence", "statement": "Each finding carries an evidence path, violated condition, severity, remediation, and unresolved boundary when evidence is incomplete.", "verification": "Inspect every finding and downgrade unsupported conclusions to needs_confirmation."},
    {"id": "scope_and_handoff", "statement": "Out-of-scope security, design, XDDP, and report-composition discoveries remain explicit handoffs with a next owner.", "verification": "Check the handoff list and confirm no out-of-scope discovery was silently absorbed."},
    {"id": "human_gate_authority", "statement": "The pre-CI verdict routes review work and does not claim correctness or replace human adoption judgment.", "verification": "Confirm blocked, needs-review, or proceed follows the declared evidence conditions and unresolved concerns remain visible."}
  ],
  "knowledge_needs": [
    {"id": "csharp_review_spec", "query": "C# review spec beyond diagnostics", "required_when": "Required for language-specific review criteria.", "seed_xids": ["30E6A4F6F3AA"]},
    {"id": "quality_feedback_rules", "query": "quality feedback return rules", "required_when": "Required when findings are returned to an implementation owner.", "seed_xids": ["7A2F4C8D1901"]},
    {"id": "common_source_analysis", "query": "common source analysis criteria", "required_when": "Required for language-neutral resource, resilience, synchronization, input, and error criteria.", "seed_xids": ["5F21C8A41001"]},
    {"id": "custom_framework_common", "query": "custom framework common criteria", "required_when": "Required when a custom framework is present.", "seed_xids": ["5F21C8A41002"]},
    {"id": "csharp_custom_framework", "query": "C# custom framework analysis criteria", "required_when": "Required when C# framework extensions or custom runtime wiring are in scope.", "seed_xids": ["30E6A4F6F3AB"]},
    {"id": "csharp_test_synchronization", "query": "C# test synchronization patterns", "required_when": "Required when fake-clock, virtual-clock, polling, or asynchronous test waits are in scope.", "seed_xids": ["4314A1A73CAF"]},
    {"id": "agent_diff_gate", "query": "agent diff review gate design", "required_when": "Required when producing the pre-CI gate-routing verdict.", "seed_xids": ["7A2F4C8D1801"]}
  ],
  "control_refs": []
}
---
<!-- xid: F1A7C3D9E240 -->
<a id="xid-F1A7C3D9E240"></a>

# Skill: csharp_review

## Review boundary

Confirm the target and declared scope, establish the Roslyn baseline, and keep compiler- or analyzer-detectable issues outside this Skill. Review C# behavior beyond that baseline across attribute activation and preconditions, resource ownership and efficiency, operational resilience, synchronization and concurrency, required business input integrity, support lifecycle, exception paths, time and culture, state and determinism, contract and schema resilience, and traceability/context propagation. Include fake-clock or polling waits that can remain blocked when a producer-side state change does not wake the waiter.

## Evidence and method

Load the applicable Knowledge entries before claiming coverage. For each category, record what static analysis establishes and what requires runtime or human evidence. Verify custom framework behavior from local source and package evidence. For attributes, identify the definition, consumer, and activation preconditions rather than using a fixed value whitelist. For resource and concurrency paths, inspect disposal, async blocking, shared state, cancellation, queue pressure, connection lifetime, and wait wake-up behavior. For input, exceptions, time/culture, state, contracts, and traceability, preserve the input, decision, source, violated condition, and observable consequence. Every finding includes an evidence path, severity (`critical`, `major`, `minor`, or `needs_confirmation`), violated condition, and remediation; category absence remains an explicit pass or not_applicable result.

## Unknown, stop, and handoff

If a project boundary, framework consumer, lifecycle source, baseline, or runtime precondition cannot be established, record an explicit `unknown` with `needs_confirmation` and the missing evidence. Do not infer correctness from clean static analysis. Stop expanding this review when evidence requests fixing, security assessment, design/business-meaning derivation, XDDP trace judgment, or report composition; retain the discovery as a handoff to the implementation owner where applicable, `security_review`, `qa_gate_review`, the constraint-derivation pack, or `review_report_composition`. Human reviewers decide disputed findings, remediation adoption, and final use of the result.

## Completion

Return the complete category matrix, detector facts, findings, static-analysis boundary, pre-CI verdict (`blocked`, `needs-review`, or `proceed`), downgrade reason when needed, required follow-up, and all unresolved or handoff items. `proceed` requires declared scope and trace, triage completion, clean deterministic evaluation, explicit baseline state, a result for every active category, no closure-affecting `needs_confirmation`, and no open concern.

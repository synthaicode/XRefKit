---
schema_version: 1
skill_id: python_review
xid: F1A7C3D9E241
summary: review Python code for language-dependent defects and system-level implementation risks beyond configured static diagnostics
applies_when:
- user asks for Python code review beyond configured formatter, linter, type-checker, test, or dependency diagnostics, including async/event-loop hazards, resource lifetime risks, silent fallback behavior, schema/coercion risks, import-time side effects, or implementation patterns that can break system-level behavior
exclusions:
- issues already covered by configured static diagnostics are outside this review
- XDDP trace-continuity review belongs to qa_gate_review
- security review, design-assumption derivation, and human-facing report composition are handed to their owning Skills
- this Skill produces findings and routing evidence; remediation adoption remains a human decision
inputs:
- target path, optional scope filters, optional output mode
outputs:
- check item matrix with pass/needs_confirmation/not_applicable category statuses, static-analysis boundary table separating confirmed_by_static_analysis, not_detectable_by_static_analysis, and requires_runtime_or_human_evidence, detector facts, evidence-based findings with critical/major/minor/needs_confirmation severity, a blocked/needs-review/proceed gate verdict, and findings for Python language-dependent issues and system-level implementation risks across static baseline, resource efficiency, operational resilience, synchronization, required business input integrity, lifecycle support, error handling, time/locale/encoding correctness, state/determinism boundaries, uncertainty/escalation paths, contract/schema resilience, and traceability/context propagation, plus handoff items for implementation-local findings to python_implementation_flow, XDDP trace gaps, security findings, design/business assumptions outside this Skill, or report composition by review_report_composition
criteria:
- id: static_boundary
  statement: The configured static baseline is explicit and every category separates confirmed_by_static_analysis, not_detectable_by_static_analysis, and requires_runtime_or_human_evidence.
  verification: Inspect the boundary table and record baseline_unavailable as a risk when configured tools cannot be collected.
- id: category_coverage
  statement: Every active category has a findings result or explicit empty result, including resource, resilience, synchronization, input, lifecycle, exception, time/locale/encoding, state, contract, and traceability categories.
  verification: Compare the result matrix with the active categories and record evidence or an explicit applicability reason.
- id: finding_evidence
  statement: Each finding carries an evidence path, violated condition, severity, remediation, and named needs_confirmation gap when evidence is incomplete.
  verification: Inspect every finding and do not treat clean static analysis as proof of runtime, deployment, framework, lifecycle, third-party API, or business correctness.
- id: scope_and_handoff
  statement: Out-of-scope security, design, XDDP, implementation-return, and report-composition discoveries remain explicit handoffs with a next owner.
  verification: Check the handoff list and confirm no out-of-scope discovery was silently absorbed.
- id: human_gate_authority
  statement: The pre-CI verdict routes review work and does not claim correctness or replace human adoption judgment.
  verification: Confirm blocked, needs-review, or proceed follows the declared evidence conditions and unresolved concerns remain visible.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: python_review_spec
  query: Python review spec beyond configured diagnostics
  required_when: Required for language-specific review criteria.
  seed_xids:
  - A9B7C6D5E4F1
- id: quality_feedback_rules
  query: quality feedback return rules
  required_when: Required when findings are returned to an implementation owner.
  seed_xids:
  - 7A2F4C8D1901
- id: common_source_analysis
  query: common source analysis criteria
  required_when: Required for language-neutral resource, resilience, synchronization, input, and error criteria.
  seed_xids:
  - 5F21C8A41001
- id: custom_framework_common
  query: custom framework common criteria
  required_when: Required when a custom framework is present.
  seed_xids:
  - 5F21C8A41002
- id: python_custom_framework
  query: Python custom framework analysis criteria
  required_when: Required when Python framework extensions or custom runtime wiring are in scope.
  seed_xids:
  - A9B7C6D5E4F2
- id: agent_diff_gate
  query: agent diff review gate design
  required_when: Required when producing the pre-CI gate-routing verdict.
  seed_xids:
  - 7A2F4C8D1801
control_refs: []
aliases:
- B4C1D2E3F4A6
- B4C1D2E3F4A5
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

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: python_review

## Purpose

Review Python code for language-dependent defects and system-level
implementation risks beyond the repository's configured static diagnostics.
XDDP trace-continuity review is owned by `qa_gate_review`; this Skill records
suspected trace gaps as handoff items.

Use the canonical spec in
`knowledge/python/100_python_review_spec.md#xid-A9B7C6D5E4F1`.

## Required Knowledge (XID)

- [Python review spec](../../knowledge/python/100_python_review_spec.md#xid-A9B7C6D5E4F1)
- [Quality feedback return rules](../../knowledge/organization/190_quality_feedback_return_rules.md#xid-7A2F4C8D1901)
- [Common source analysis criteria](../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
- [Custom framework common criteria](../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002)
- [Python custom framework analysis criteria](../../knowledge/python/110_custom_framework_analysis_criteria.md#xid-A9B7C6D5E4F2)
- [Agent diff review gate design](../../knowledge/organization/180_agent_diff_review_gate_design.md#xid-7A2F4C8D1801)

## Inputs

- target path
- optional scope filters
- optional output mode (`findings-only` or `findings-with-fixes`)

## Outputs

- check item matrix covering static baseline and active review categories
- static-analysis boundary table that separates `confirmed_by_static_analysis`,
  `not_detectable_by_static_analysis`, and `requires_runtime_or_human_evidence`
- findings list with severity, evidence path, violated condition, and remediation
- category summaries for every active category
- gate verdict block
- handoff list for security, XDDP trace-continuity, design assumptions, and
  report-composition needs
- implementation-return feedback items when applicable

## Startup

- Confirm the target path exists.
- Confirm the review scope is defined when filters are supplied.
- Identify configured Python static baseline tools from repository evidence.
- Load the Python review spec.
- Record `needs_confirmation` if the repository, package, project, or service
  boundary cannot be established cleanly.

## Worklist

- Create one concrete work item for static baseline collection.
- Create one concrete work item per active review category for the agreed scope.
- When the scope is split across packages, services, directories, or files,
  create category work items per scope unit.
- Decide subagent split before loading broad evidence when context overflow is
  likely.

## Planning

- Define the review scope: repository, package, service, directory, or file set.
- Define output mode.
- Prepare review targets and category buckets:
  - static baseline
  - resource efficiency
  - operational resilience
  - synchronization and concurrency
  - required business input integrity
  - support lifecycle
  - error handling and exception paths
  - time, locale, and encoding
  - state and determinism boundary
  - uncertainty and escalation path
  - contract and schema resilience
  - traceability and context propagation
  - custom-framework analysis when present
- Treat the user's headline purpose as emphasis, not as a filter that disables
  other active categories.
- Decide whether XDDP trace-continuity review is in scope. If yes, route or
  pair with `qa_gate_review`; otherwise record trace-gap signals as handoff
  items.

## Execution Role

- The executor produces findings and artifacts; it never advances the check
  phase and never closes the run.
- Scope-disjoint category passes may run as parallel subagents when no
  cross-scope reasoning is required.
- The coordinator keeps the review scope, category matrix, duplicate-finding
  merge, conflicts, and final gate verdict.

## Execution

- Establish the configured Python static baseline:
  - run the repository's test, type-check, lint, format-check, and dependency
    checks when configured and feasible
  - mark diagnostics-covered concerns out of scope for this Skill
  - record `baseline_unavailable` when no configured baseline is available
- For each active category, state what static analysis actually established
  and what it did not establish. Use these buckets:
  - `confirmed_by_static_analysis`: source-visible facts supported by tools or
    direct source inspection
  - `not_detectable_by_static_analysis`: runtime, deployment, framework,
    business-intent, or external-policy facts that static analysis cannot prove
  - `requires_runtime_or_human_evidence`: named evidence needed to resolve the
    uncertainty
- Apply the Python review spec and common source-analysis criteria across every
  active category.
- Verify custom framework behavior from local evidence before relying on
  decorators, registration, dependency injection, plugin discovery, lifecycle,
  async, settings, or serialization assumptions.
- When a finding or remediation asserts a third-party API fact, verify it
  against the actually referenced package version when feasible; otherwise
  mark it `needs_confirmation`.
- Emit a matrix before findings. Categories with no finding must still appear
  as `pass` or `not_applicable`.
- Do not mark a category `pass` merely because static analysis found no issue
  when the category depends on runtime wiring, deployment limits, business
  approval, current lifecycle policy, or third-party API behavior that has not
  been verified. Use `needs_confirmation` and name the missing evidence.
- Preserve detector facts needed by `review_report_composition`.
- Mark implementation-local findings using the quality feedback return rules.

## Gate Verdict Output

Emit one pre-CI review-routing verdict:

```text
verdict: blocked | needs-review | proceed
reason: <one line>
evidence: <paths / artifact ids / baseline state>
downgrade_reason: <required when not proceed>
required_followup: <next owner or specialist Skill, or none>
```

- `blocked` when any `critical` finding stands.
- `proceed` only when the run has trace, diff scope is declared, triage is
  complete, configured static baseline state is explicit, every active category
  has a result, no closure-affecting `needs_confirmation` finding remains, and
  no concern is open.
- Otherwise use `needs-review`.

## Check Role

- The check role is the protocol-owned deterministic run-record check.
- Record the findings document as an `output` artifact and baseline or review
  evidence as `evidence` artifacts.
- Keep unresolved finding validity visible as `needs_confirmation`.

## Quality Gate

- This Skill is `model_tier: standard`, so the quality gate is mandatory at
  closure.
- Declare acceptance `check` artifacts for static-baseline disposition,
  category coverage, evidence quality, and remediation validity.
- Route human-facing report expression through `review_report_composition` when
  wording quality or decision-readable composition is required.

## Unknowns And Risks

- Mirror every `needs_confirmation` finding that affects closure as an
  `unknown` concern.
- Mirror every closure-affecting `not_detectable_by_static_analysis` or
  `requires_runtime_or_human_evidence` row as an `unknown` concern, unless it
  is explicitly out of scope for the review.
- Record `baseline_unavailable` as a `risk` concern when configured baseline
  tools cannot be collected.
- Record unresolved lifecycle status sources as `unknown` concerns with the
  required source URLs or package evidence named.

## Closure Gate

Closure is allowed only when:

- the static baseline state is explicit
- the static-analysis boundary table names what was confirmed and what remains
  outside static analysis
- every active category has a findings result or explicit empty result
- the output includes a check item matrix covering every active category
- every finding carries evidence, severity, and remediation, or a named
  `needs_confirmation` gap
- out-of-scope discoveries are on the handoff list
- the run log passes `python -m xrefkit skill close`

## Handoff

- Hand findings and category summaries to the requester or fix owner.
- Hand implementation-local findings back to `python_implementation_flow`.
- Hand security-scope findings to `security_review`.
- Hand XDDP trace-continuity findings to `qa_gate_review`.
- Hand unstated design assumptions to the constraint-derivation pack.
- Record each handoff as a `handoff` artifact in the run log.

## Rules

- Exclude issues already covered by configured static diagnostics.
- Do not assert public-framework behavior for custom Python frameworks without
  local evidence.
- Do not expand into fixing, security review, design derivation, or report
  composition.
- Do not silently drop out-of-scope discoveries.
- Use subagents when scope boundaries stay explicit and one context would hide
  category coverage.

## Reporting Contract (共通報告)



- reporting_profile: checklist_verdict

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: review Python code for language-dependent defects and system-level implementation risks beyond configured static diagnostics

- use_when: user asks for Python code review beyond configured formatter, linter, type-checker, test, or dependency diagnostics, including async/event-loop hazards, resource lifetime risks, silent fallback behavior, schema/coercion risks, import-time side effects, or implementation patterns that can break system-level behavior

- input: target path, optional scope filters, optional output mode

- output: check item matrix with pass/needs_confirmation/not_applicable category statuses, static-analysis boundary table separating confirmed_by_static_analysis, not_detectable_by_static_analysis, and requires_runtime_or_human_evidence, detector facts, evidence-based findings with critical/major/minor/needs_confirmation severity, a blocked/needs-review/proceed gate verdict, and findings for Python language-dependent issues and system-level implementation risks across static baseline, resource efficiency, operational resilience, synchronization, required business input integrity, lifecycle support, error handling, time/locale/encoding correctness, state/determinism boundaries, uncertainty/escalation paths, contract/schema resilience, and traceability/context propagation, plus handoff items for implementation-local findings to python_implementation_flow, XDDP trace gaps, security findings, design/business assumptions outside this Skill, or report composition by review_report_composition

- constraints: exclude issues already covered by configured static diagnostics; do not treat clean static analysis as proof of runtime, framework, deployment, lifecycle, third-party API, or business-intent correctness; do not assume public-framework semantics for custom Python frameworks without local evidence; do not replace XDDP trace-continuity review; do not expand into security review, design-assumption derivation, or report composition; route those findings to qa_gate_review, security_review, the constraint-derivation pack, or review_report_composition through the handoff list; when the review spans enough categories, projects, files, or evidence to risk context overflow, split execution into subagents by scope or category instead of running all checks in one context

- lifecycle:
  - startup: confirm target path and review scope, identify configured Python static baseline tools, then load the Python review spec
  - planning: define review scope, output mode, category buckets, custom-framework analysis targets, and subagent split when scope-separated review is safe or context overflow is likely
  - execution: establish configured static baseline, record what static analysis can and cannot prove, and execute category-specific checks with local-evidence-first handling for custom frameworks
  - monitoring_and_control: exclude diagnostics-covered issues and downgrade static-analysis gaps to `needs_confirmation` or `unknown` instead of passing them silently
  - closure: return findings, category summaries, gate verdict, and explicit review conditions

- tags: `python`, `review`, `quality`, `engineering`

- knowledge_slots:
  - name=review_spec; bind=A9B7C6D5E4F1
  - name=source_criteria; bind=5F21C8A41001
  - name=custom_framework_common; bind=5F21C8A41002
  - name=custom_framework; bind=A9B7C6D5E4F2
  - name=feedback_rules; bind=7A2F4C8D1901
  - name=gate_design; bind=7A2F4C8D1801

- observation_refs:
  - `../../observations/2026-07-07_session_python_skill_authoring.md`

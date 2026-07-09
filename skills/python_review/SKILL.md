<!-- xid: B4C1D2E3F4A6 -->
<a id="xid-B4C1D2E3F4A6"></a>

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

<!-- xid: 09B250B1A8FB -->
<a id="xid-09B250B1A8FB"></a>

# Skill: qa_gate_review

## Purpose

Execute the four QA review domains `specification / performance / security / license` and produce an evidence-based review result.

## Required Capability Definitions (XID)

- [CAP-QA-001 Specification Conformance Review](../../capabilities/quality/100_cap_qa_001_code_review.md#xid-7E9CCEBEDA2D)
- [CAP-QA-006 Performance Risk Review](../../capabilities/quality/140_cap_qa_006_performance_risk_review.md#xid-5A1C2F0E5506)
- [CAP-QA-007 Security Review](../../capabilities/quality/150_cap_qa_007_security_review.md#xid-5A1C2F0E5507)
- [CAP-QA-008 License Compliance Check](../../capabilities/quality/160_cap_qa_008_license_compliance_check.md#xid-5A1C2F0E5508)

## Optional Specialized Capability Definitions (XID)

- [CAP-QA-005 Attribute Usage Review](../../capabilities/quality/130_cap_qa_005_attribute_usage_review.md#xid-5A1C2F0E5505)

## Inputs

- implemented code or diff
- design evidence
- coding rules
- optional performance requirements or measurements
- optional dependency and provenance information

## Outputs

- domain review results for specification, performance, security, and license
- finding list with evidence
- uncertainty list

## Required Knowledge (XID)

- [Temporary traceability comment rule](../../knowledge/organization/151_temporary_traceability_comment_rule.md#xid-22E4C7AC7063)
- [XDDP basics](../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)

## Startup

- Confirm implemented code exists.
- Confirm design evidence exists.
- Confirm coding rules are available.
- Confirm performance evidence when performance review is in scope.
- Confirm dependency or provenance evidence when license review is in scope.
- Record `unknown` if required evidence is missing.

## Planning

- Define the review scope and target files.
- Define the intended change difference before reading the implementation in detail.
- Narrow the review target to the appropriateness of the stated difference rather than re-reviewing the whole implementation surface.
- Define the review domains:
  - specification
  - performance
  - security
  - license
- If review targets can be separated into disjoint scopes and parallel execution does not create consistency or handoff risk, split the work by scope and execute those scopes through subagents.
- Prepare management rows for each domain, review targets, findings, and unresolved evidence gaps.

## Execution

- Review the implementation as a delta against:
  - the change reason
  - the change requirement specification
  - the traced impact targets
  - the intended change method when available
- Execute `CAP-QA-001` for specification conformance against design evidence and coding rules.
- Execute `CAP-QA-006` for performance risk review.
- Execute `CAP-QA-007` for security review.
- Execute `CAP-QA-008` for license compliance check.
- Execute `CAP-QA-005` when attribute semantics need specification-focused deep review.
- Confirm that the reviewed code or diff matches the intended change scope and does not silently expand beyond the traced targets without explanation.
- Produce findings with concrete evidence.

## Monitoring and Control

- Check that each review domain has a recorded result.
- Downgrade unsupported conclusions to `unknown`.
- Downgrade review coverage to `unknown` when the intended difference is not clear enough to bound the review target.
- Preserve explicit evidence gaps.

## Closure

- Confirm all review rows are finalized as `done`, `unknown`, or `out_of_scope`.
- If code review completion is being declared for a target scope, hand off that scope for `TRACE-TEMP:` cleanup under the temporary traceability comment rule.
- Return the per-domain judgments and supporting findings.
- Hand off unresolved review items when further investigation is required.

## Rules

- Every judgment must cite evidence.
- Do not treat unsupported assumptions as facts.
- Do not decide design or implementation policy.
- Use subagents only when scope boundaries stay explicit and parallel execution is safe.
- Do not expand review into full-codebase inspection when the intended delta can be reviewed more narrowly and correctly.


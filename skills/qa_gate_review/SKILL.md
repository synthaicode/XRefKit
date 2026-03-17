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

## Startup

- Confirm implemented code exists.
- Confirm design evidence exists.
- Confirm coding rules are available.
- Confirm performance evidence when performance review is in scope.
- Confirm dependency or provenance evidence when license review is in scope.
- Record `unknown` if required evidence is missing.

## Planning

- Define the review scope and target files.
- Define the review domains:
  - specification
  - performance
  - security
  - license
- Prepare management rows for each domain, review targets, findings, and unresolved evidence gaps.

## Execution

- Execute `CAP-QA-001` for specification conformance against design evidence and coding rules.
- Execute `CAP-QA-006` for performance risk review.
- Execute `CAP-QA-007` for security review.
- Execute `CAP-QA-008` for license compliance check.
- Execute `CAP-QA-005` when attribute semantics need specification-focused deep review.
- Produce findings with concrete evidence.

## Monitoring and Control

- Check that each review domain has a recorded result.
- Downgrade unsupported conclusions to `unknown`.
- Preserve explicit evidence gaps.

## Closure

- Confirm all review rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Return the per-domain judgments and supporting findings.
- Hand off unresolved review items when further investigation is required.

## Rules

- Every judgment must cite evidence.
- Do not treat unsupported assumptions as facts.
- Do not decide design or implementation policy.


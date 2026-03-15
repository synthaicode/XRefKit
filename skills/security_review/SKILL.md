<!-- xid: 3575A687EBCA -->
<a id="xid-3575A687EBCA"></a>

# Skill: security_review

## Purpose

Execute `CAP-QA-007` and review C# code and evidence for security risks.

## Required Capability Definitions (XID)

- [CAP-QA-007 Security Review](../../capabilities/quality/150_cap_qa_007_security_review.md#xid-5A1C2F0E5507)

## Required Knowledge (XID)

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Inputs

- target code
- design evidence

## Outputs

- security review result
- risk list
- unresolved list
- execution metrics log

## Startup

- Confirm target and security-relevant evidence exist.
- Record `unknown` if required evidence is missing.

## Planning

- Define security review targets and management rows.

## Execution

- Review input handling, secrets, auth, data protection, dependency risk, and logging safety.

## Monitoring and Control

- Downgrade unsupported conclusions to `unknown`.
- Preserve explicit evidence gaps.

## Closure

- Finalize review results and preserve unresolved items.

## Rules

- Every judgment must cite evidence.
- Do not suppress security uncertainty.

<!-- xid: 547A7AF22F67 -->
<a id="xid-547A7AF22F67"></a>

# Skill: license_review

## Purpose

Execute `CAP-QA-008` and review dependency and provenance evidence for license compliance risks.

## Required Capability Definitions (XID)

- [CAP-QA-008 License Compliance Check](../../capabilities/quality/160_cap_qa_008_license_compliance_check.md#xid-5A1C2F0E5508)

## Required Knowledge (XID)

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Inputs

- package list
- dependency information
- provenance information

## Outputs

- license review result
- incompatible or unknown license list
- notice obligation list
- unresolved list
- execution metrics log

## Startup

- Confirm dependency or provenance evidence exists.
- Record `unknown` if required evidence is missing.

## Planning

- Define license review targets and management rows.

## Execution

- Review package licenses, compatibility, notices, and provenance.

## Monitoring and Control

- Downgrade unsupported conclusions to `unknown`.
- Preserve explicit evidence gaps.

## Closure

- Finalize review results and preserve unresolved items.

## Rules

- Every judgment must cite evidence.
- Do not assume package license acceptability without evidence.

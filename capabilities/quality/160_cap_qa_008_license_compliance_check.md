<!-- xid: 5A1C2F0E5508 -->
<a id="xid-5A1C2F0E5508"></a>

# Capability: CAP-QA-008 License Compliance Check

## Definition

- capability_id: `CAP-QA-008`
- capability_name: `license_compliance_check`
- work_type: `judgment`
- summary: review package and code provenance for license compliance risks

## Preconditions

- dependency information or source provenance exists

## Trigger

- manufacturing self-check or quality review requires license validation

## Inputs

- package list
- dependency information
- provenance information
- C# quality review criteria

## Outputs

- license review result
- incompatible or unknown license list
- notice obligation list
- unresolved list
- execution metrics log

## Required Domain Knowledge

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Constraints

- every judgment must cite evidence
- if evidence is insufficient, record `unknown`
- do not assume package license acceptability without evidence

## Assignment

- quality review step
- [Quality Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- This capability covers the `license` review domain.

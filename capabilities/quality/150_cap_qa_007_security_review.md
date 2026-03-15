<!-- xid: 5A1C2F0E5507 -->
<a id="xid-5A1C2F0E5507"></a>

# Capability: CAP-QA-007 Security Review

## Definition

- capability_id: `CAP-QA-007`
- capability_name: `security_review`
- work_type: `judgment`
- summary: review C# code and related evidence for security risks and control gaps

## Preconditions

- target code exists
- security-relevant evidence or design exists

## Trigger

- manufacturing self-check or quality review requires security validation

## Inputs

- target code
- design evidence
- C# quality review criteria

## Outputs

- security review result
- risk list
- unresolved list
- execution metrics log

## Required Domain Knowledge

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Constraints

- every judgment must cite evidence
- if evidence is insufficient, record `unknown`
- do not suppress security uncertainty

## Assignment

- quality review step
- [Quality Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Task Lifecycle Mapping

- Startup:
  - confirm code and security-relevant evidence exist
  - record `unknown` if required evidence is missing
- Planning:
  - define security review targets and management rows
- Execution:
  - review input handling, secrets, auth, data protection, and logging
- Monitoring and Control:
  - downgrade unsupported conclusions to `unknown`
- Closure:
  - finalize review results and preserve unresolved items

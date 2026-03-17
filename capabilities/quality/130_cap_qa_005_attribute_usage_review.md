<!-- xid: 5A1C2F0E5505 -->
<a id="xid-5A1C2F0E5505"></a>

# Capability: CAP-QA-005 Attribute Usage Review

## Definition

- capability_id: `CAP-QA-005`
- capability_name: `attribute_usage_review`
- work_type: `judgment`
- summary: review C# attributes for necessity, value correctness, and usage correctness

## Preconditions

- target C# code exists
- applicable design or rule evidence exists

## Trigger

- manufacturing self-check or quality review requires attribute validation

## Inputs

- target C# code
- design evidence
- C# quality review criteria

## Outputs

- attribute review result
- unnecessary attribute list
- invalid attribute value list
- incorrect attribute usage list
- unresolved list
- execution metrics log

## Required Domain Knowledge

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Constraints

- every judgment must cite evidence
- if evidence is insufficient, record `unknown`
- do not infer framework behavior without checking its preconditions

## Assignment

- quality review step
- [Quality Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- This capability is a specialized review under the `specification` domain.
- Use it when specification conformance depends on attribute semantics or framework attribute preconditions.

## Task Lifecycle Mapping

- Startup:
  - confirm code and evidence exist
  - record `unknown` if required evidence is missing
- Planning:
  - define attribute review targets and management rows
- Execution:
  - review attribute necessity, values, and usage patterns
- Monitoring and Control:
  - downgrade unsupported conclusions to `unknown`
- Closure:
  - finalize review results and preserve unresolved items

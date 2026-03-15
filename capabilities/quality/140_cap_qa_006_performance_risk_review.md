<!-- xid: 5A1C2F0E5506 -->
<a id="xid-5A1C2F0E5506"></a>

# Capability: CAP-QA-006 Performance Risk Review

## Definition

- capability_id: `CAP-QA-006`
- capability_name: `performance_risk_review`
- work_type: `judgment`
- summary: review C# code and related evidence for performance risks and unsupported performance claims

## Preconditions

- target code or design exists
- performance evidence or assumptions exist

## Trigger

- manufacturing self-check or quality review requires performance validation

## Inputs

- target code
- performance requirements or assumptions
- C# quality review criteria

## Outputs

- performance review result
- bottleneck candidate list
- unsupported performance claim list
- unresolved list
- execution metrics log

## Required Domain Knowledge

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Constraints

- every judgment must cite evidence
- if evidence is insufficient, record `unknown`
- do not claim measured performance without measurement evidence

## Assignment

- quality review step
- [Quality Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Task Lifecycle Mapping

- Startup:
  - confirm target and performance evidence exist
  - record `unknown` if required evidence is missing
- Planning:
  - define performance review targets and management rows
- Execution:
  - review bottlenecks, allocations, I/O, and async behavior
- Monitoring and Control:
  - downgrade unsupported conclusions to `unknown`
- Closure:
  - finalize review results and preserve unresolved items

<!-- xid: DFF93B17B4D2 -->
<a id="xid-DFF93B17B4D2"></a>

# Skill: performance_review

## Purpose

Execute `CAP-QA-006` and review C# code and evidence for performance risks.

## Required Capability Definitions (XID)

- [CAP-QA-006 Performance Risk Review](../../capabilities/quality/140_cap_qa_006_performance_risk_review.md#xid-5A1C2F0E5506)

## Required Knowledge (XID)

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Inputs

- target code
- performance requirements or assumptions

## Outputs

- performance review result
- bottleneck candidate list
- unsupported performance claim list
- unresolved list
- execution metrics log

## Startup

- Confirm target and performance evidence exist.
- Record `unknown` if required evidence is missing.

## Planning

- Define performance review targets and management rows.

## Execution

- Review allocations, I/O, database access, async behavior, and throughput risks.

## Monitoring and Control

- Downgrade unsupported conclusions to `unknown`.
- Preserve explicit evidence gaps.

## Closure

- Finalize review results and preserve unresolved items.

## Rules

- Every judgment must cite evidence.
- Do not claim measured performance without measurement evidence.

<!-- xid: 9D4D87FE33A9 -->
<a id="xid-9D4D87FE33A9"></a>

# Skill: attribute_review

## Purpose

Execute `CAP-QA-005` and review C# attributes for necessity, value correctness, and usage correctness.

## Required Capability Definitions (XID)

- [CAP-QA-005 Attribute Usage Review](../../capabilities/quality/130_cap_qa_005_attribute_usage_review.md#xid-5A1C2F0E5505)

## Required Knowledge (XID)

- [C# quality review criteria](../../knowledge/quality/100_csharp_quality_review_criteria.md#xid-8C4D2A7E5101)
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Inputs

- target C# code
- design evidence
- coding rules

## Outputs

- attribute review result
- unnecessary attribute list
- invalid attribute value list
- incorrect attribute usage list
- unresolved list
- execution metrics log

## Startup

- Confirm code and supporting evidence exist.
- Record `unknown` if required evidence is missing.

## Planning

- Define attribute review targets and management rows.

## Execution

- Check unnecessary attributes.
- Check attribute values.
- Check attribute usage patterns and preconditions.

## Monitoring and Control

- Downgrade unsupported conclusions to `unknown`.
- Preserve explicit evidence gaps.

## Closure

- Finalize review results and preserve unresolved items.

## Rules

- Every judgment must cite evidence.
- Do not infer attribute behavior without checking its preconditions.

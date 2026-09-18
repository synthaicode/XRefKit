---
schema_version: 1
skill_id: integration_constraint_derivation
xid: 9A1C4E7D2B60
aliases: [E547F90B1234, E547F90B1235]
summary: derive requirement confirmation gates from external APIs, webhooks, files, and messaging integration structure
applies_when:
  - external integration specs may leave failure, timing, retry, or idempotency behavior implicit
exclusions:
  - derive from integration structure and failure modes, not nominal success cases
  - implementation policy is not decided unless explicitly requested
inputs: [API specs, webhook definitions, file contracts, and messaging designs]
outputs: [ICD derivation table, grouped confirmation list, retry or idempotency matrices, written output path]
criteria:
  - id: integration_evidence
    statement: Every ICD item is grounded in an identified external integration surface.
    verification: Check each item against API, webhook, file, message, or service evidence.
  - id: failure_completeness
    statement: Retry, timeout, ordering, and idempotency gaps remain explicit.
    verification: Review the corresponding integration matrix and unresolved items.
  - id: output_closure
    statement: The derivation result exists at the declared output path with grouped confirmations and gaps.
    verification: Check the output path before handoff.
knowledge_needs:
  - id: constraint_derivation_framework
    query: constraint derivation framework
    required_when: Required for deriving and classifying integration signals
    seed_xids: [81A6C4E2B190]
  - id: integration_constraint_derivation_catalog
    query: integration constraint derivation catalog
    required_when: Required for selecting integration signal categories
    seed_xids: [6F0D7C1A2E44]
control_refs: [111D282CA0EA]
---
<!-- xid: 9A1C4E7D2B60 -->
<a id="xid-9A1C4E7D2B60"></a>

# Skill: integration_constraint_derivation

## Purpose

Derive requirement confirmation gates from external integration structure before failure handling gets completed implicitly.

## Inputs
- API specs, webhook definitions, file contracts, and messaging designs

## Outputs
- ICD-prefixed derivation basis table
- grouped requirement confirmation list
- retry or idempotency matrices where required
- written output path

## Startup
- Confirm the input contains external integration structure.
- Load the framework and integration catalog Knowledge.
- Identify retry, timeout, ordering, and idempotency surfaces.
- Use `work/constraint_derivation/YYYY-MM-DD_integration_constraint_derivation_<topic>.md` unless an output path is supplied.

## Execution
1. Enumerate API, webhook, file, message, and external-service interaction points.
2. Apply the integration catalog and assign `ICD-` ids.
3. Expand retry or idempotency matrices where repeated execution is possible.
4. Group results by integration surface and keep unresolved behavior explicit.
5. Write the result using the primary derivation output template or an equivalent structure.

## Monitoring and Control
- Do not assume provider defaults satisfy the business requirement.
- Stop if retry or duplicate-delivery behavior is left implicit.
- Preserve links from each ICD item back to integration evidence.

## Closure and Handoff
- Return the ICD table, grouped unresolved items, blocking gaps, and written path.
- Hand unresolved requirement decisions to the responsible human or design owner.

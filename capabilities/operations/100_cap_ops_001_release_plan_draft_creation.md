<!-- xid: 9715BACE7EB8 -->
<a id="xid-9715BACE7EB8"></a>

# Capability: CAP-OPS-001 Release Material Structuring

## Definition

- capability_id: `CAP-OPS-001`
- capability_name: `release_material_structuring`
- work_type: `execution`
- summary: draft release materials, release procedures, and release confirmation procedures from build outputs, requirements, and operational constraints

## Preconditions

- manufacturing outputs exist
- design and requirement materials exist

## Trigger

- release-planning phase starts

## Inputs

- manufacturing outputs
- release policy
- planning basis source list
- design materials
- requirement materials
- performance measurements when available

## Outputs

- release plan draft
- release basis reference
- environment release basis reference
- release procedure draft
- release confirmation procedure draft
- rollback procedure draft

## Required Domain Knowledge

- release-plan template
- acceptance criteria
- release confirmation checklist
- placement confirmation points
- behavior confirmation points
- rollback procedure
- monitoring-item definitions

## Constraints

- draft only
- each environment-specific release plan must identify which release policy entry and planning basis source it realizes
- release materials must include execution procedure, release confirmation procedure, and rollback procedure drafts
- release confirmation procedure must include placement confirmation and behavior confirmation
- do not approve release timing or go/no-go
- preserve unresolved operational assumptions explicitly

## Assignment

- release-planning phase
- [Operations Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `release plan draft creation` is a business activity in release-planning work.
- This capability is the reusable release-material structuring ability used by that activity.
## Task Lifecycle Mapping

- Startup:
  - use `Preconditions`, `Trigger`, and `Inputs` to confirm the capability can start
  - if required evidence is missing, record `unknown` before continuing
- Planning:
  - define targets, work rows, and handoff boundaries for this capability
- Execution:
  - produce the outputs defined in this capability within its stated constraints
- Monitoring and Control:
  - check progress and evidence quality through management-table and metrics rules
  - downgrade weakly supported conclusions to `unknown`
- Closure:
  - confirm the capability result is finalized as `done`, `unknown`, or `out_of_scope`
  - preserve unresolved and out-of-scope items for handoff or escalation

- execution metrics log
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)



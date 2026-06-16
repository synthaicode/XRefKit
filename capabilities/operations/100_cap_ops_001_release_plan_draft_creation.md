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

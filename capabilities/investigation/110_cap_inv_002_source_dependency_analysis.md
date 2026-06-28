<!-- xid: E994FCDA8CD1 -->
<a id="xid-E994FCDA8CD1"></a>

# Capability: CAP-INV-002 Change Impact Enumeration

## Definition

- capability_id: `CAP-INV-002`
- capability_name: `change_impact_enumeration`
- work_type: `execution`
- summary: enumerate source, dependency, data, configuration, and interface impacts needed to understand a requested change

## Preconditions

- in-scope service list from `CAP-INV-001` exists
- source code or design materials are available

## Trigger

- investigation workflow step 2 starts

## Inputs

- in-scope target list
- source code or equivalent implementation artifacts
- design documents

## Outputs

- change viewpoints
- related services, database, and master-data impact notes
- test viewpoints
- uncertainty list
- execution metrics log

## Required Domain Knowledge

- [Investigation coverage checklist](../../knowledge/investigation/100_investigation_coverage_checklist.md#xid-91E2A7C56101)
- architecture knowledge
- database structure
- service interface definitions
- master-data definitions
- [Metrics definition](../../knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201)

## Constraints

- list facts and impacts only
- do not decide change policy
- every coverage area must end as `done`, `unknown`, or `out_of_scope`
- record unresolved evidence gaps as `unknown`

## Assignment

- investigation phase step 2
- [Planning Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)
- [Design Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `source and dependency analysis` is a business activity in the investigation workflow.
- This capability is the reusable impact-enumeration ability used by that activity.

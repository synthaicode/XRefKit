<!-- xid: 1A12C5C61269 -->
<a id="xid-1A12C5C61269"></a>

# Capability: CAP-MFG-001 Scoped Code Realization

## Definition

- capability_id: `CAP-MFG-001`
- capability_name: `scoped_code_realization`
- work_type: `execution`
- summary: implement code within approved design scope

## Preconditions

- an approved design exists
- target source paths are identified
- applicable coding and naming rules are available

## Trigger

- manufacturing phase starts

## Inputs

- approved design
- design basis policy reference
- target source code
- coding rules
- naming rules

## Outputs

- implemented code
- uncertainty list
- out-of-scope list
- implementation basis design reference

## Required Domain Knowledge

- coding rules
- naming rules
- local design patterns if they constrain implementation
- [Implementation assumption gap handling](../../knowledge/organization/150_implementation_assumption_gap_handling.md#xid-7A2F4C8D1501)

## Constraints

- implement only within approved design scope
- each implementation change must identify the design artifact or design basis reference it realizes
- do not change design policy
- do not hide unresolved issues
- convert every implementation assumption gap into `unknown`, `out_of_scope`, or explicit delegated local choice
- record out-of-scope items with reasons

## Assignment

- manufacturing phase
- [Manufacturing Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- Workflow belongs in `docs/`.
- Executable procedure belongs in `skills/implementation_flow/`.
- Domain evidence belongs in `knowledge/`.
- `implementation` is a business activity in manufacturing work.
- This capability is the reusable realization ability used by that activity.

<!-- xid: 867B78FF702F -->
<a id="xid-867B78FF702F"></a>

# Capability: CAP-INV-001 Scope Classification

## Definition

- capability_id: `CAP-INV-001`
- capability_name: `scope_classification`
- work_type: `execution`
- summary: classify request scope into in-scope and out-of-scope targets using available catalog or equivalent domain evidence

## Preconditions

- a request exists
- a service catalog is available directly or through domain knowledge lookup

## Trigger

- investigation workflow step 1 starts

## Inputs

- request
- service catalog or equivalent service reference
- optional business-domain constraints

## Outputs

- in-scope service list
- out-of-scope service list with reasons
- uncertainty list for unresolved scope questions

## Required Domain Knowledge

- service catalog definitions
- business domain rules used to interpret the request
- scope classification criteria

## Constraints

- classify scope only
- do not decide implementation policy
- do not decide design policy
- record missing evidence as `unknown`

## Assignment

- investigation phase step 1
- [Planning Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- Workflow belongs in `docs/`.
- Executable procedure belongs in `skills/investigation_flow/`.
- Domain evidence belongs in `knowledge/`.
- `service catalog analysis` is a business activity in the investigation workflow.
- This capability is the reusable classification ability used by that activity.

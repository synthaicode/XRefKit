<!-- xid: BC408337F2A2 -->
<a id="xid-BC408337F2A2"></a>

# Capability: CAP-REQ-001 Requirement Structuring

## Definition

- capability_id: `CAP-REQ-001`
- capability_name: `requirement_structuring`
- work_type: `execution`
- summary: draft a requirement document from confirmed assumptions and investigation outputs

## Preconditions

- confirmed assumptions exist
- change-test viewpoint table exists

## Trigger

- requirements phase starts after assumption confirmation

## Inputs

- confirmed assumptions
- change target list
- change-test viewpoint table
- performance needs when available

## Outputs

- requirement draft

## Required Domain Knowledge

- business rules
- SLA definitions
- supplier definitions

## Constraints

- draft only
- do not approve requirements
- preserve unresolved points explicitly

## Assignment

- requirements phase
- [Planning Group](../../docs/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `requirement draft creation` is a business activity in requirements work.
- This capability is the reusable requirement-structuring ability used by that activity.

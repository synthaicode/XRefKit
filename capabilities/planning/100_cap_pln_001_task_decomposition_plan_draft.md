<!-- xid: F5193313AB79 -->
<a id="xid-F5193313AB79"></a>

# Capability: CAP-PLN-001 Work and Policy Planning Structuring

## Definition

- capability_id: `CAP-PLN-001`
- capability_name: `work_and_policy_planning_structuring`
- work_type: `execution`
- summary: structure approved requirements, domain knowledge, and current-source findings into executable work plans and downstream design policies aligned to the current codebase

## Preconditions

- approved requirement definition exists

## Trigger

- planning phase starts

## Inputs

- approved requirements
- change target list
- current source structure findings
- domain knowledge references

## Outputs

- work plan
- source modification policy
- data change policy
- data correction tool policy
- test policy
- test tool policy
- release policy
- planning basis source list

## Required Domain Knowledge

- applicable domain knowledge for the target service or business area
- current source structure and dependency findings
- [IPA release activity catalog](../../knowledge/operations/100_ipa_release_activity_catalog.md#xid-7B3E5D1A6101)
- process rules
- approval flow

## Constraints

- draft only
- planning must stay consistent with the current source structure unless an explicit deviation reason is recorded
- each planning policy must cite the current source artifacts or current-source findings used as its basis
- data change planning must state whether a dedicated data correction tool is needed and, when needed, how creation and verification of that tool will be handled
- test planning must state which test tools will be used, whether an existing tool is selected or a new tool must be created, and how that tool will be verified
- do not decide final priority or resource allocation
- preserve unresolved planning assumptions explicitly

## Assignment

- planning phase
- [Design Group](../../docs/reference/040_group_definitions.md#xid-8B31F02A4009)

## Notes

- `work planning and policy drafting` is a business activity in planning work.
- This capability is the reusable planning-structuring ability used by that activity.
- This capability uses domain knowledge and current-source analysis so that downstream design starts from the existing codebase reality, not an idealized target structure.

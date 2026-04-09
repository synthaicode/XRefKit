<!-- xid: 9C0115875B0C -->
<a id="xid-9C0115875B0C"></a>

# Skill: investigation_flow

## Purpose

Execute the investigation sequence `CAP-INV-001 -> CAP-INV-002 -> CAP-INV-003` and produce scoped change targets for later estimation or design.

## Required Capability Definitions (XID)

- [CAP-INV-001 Scope Classification](../../capabilities/investigation/100_cap_inv_001_service_catalog_analysis.md#xid-867B78FF702F)
- [CAP-INV-002 Change Impact Enumeration](../../capabilities/investigation/110_cap_inv_002_source_dependency_analysis.md#xid-E994FCDA8CD1)
- [CAP-INV-003 Structured Investigation Summary](../../capabilities/investigation/120_cap_inv_003_change_target_summary.md#xid-6AB17163C9BF)

## Required Knowledge (XID)

- [XDDP basics](../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)
- [Investigation coverage checklist](../../knowledge/investigation/100_investigation_coverage_checklist.md#xid-91E2A7C56101)

## Inputs

- request
- optional service catalog path
- optional candidate services supplied by the user
- optional repository or document paths for deeper analysis

## Outputs

- in-scope service list
- out-of-scope service list with reasons
- change-difference investigation view
- change viewpoints
- test viewpoints
- change target list
- change-test viewpoint table
- uncertainty list

## Startup

- Confirm the request exists.
- Confirm the service catalog is available directly or can be located.
- Confirm deeper analysis targets are available when step 2 is needed.
- Load the investigation coverage checklist.
- If required evidence is missing, record `unknown` before proceeding.

## Planning

- Define the investigation targets.
- Treat the request as a difference to existing behavior, assets, or interfaces.
- When official documents are weak or stale, plan selective spec-out rather than broad unfocused code reading.
- Map each business activity to its supporting capability:
  - service catalog analysis -> `CAP-INV-001`
  - source and dependency analysis -> `CAP-INV-002`
  - change-target summarization -> `CAP-INV-003`
- Define the step order: `CAP-INV-001 -> CAP-INV-002 -> CAP-INV-003`.
- Prepare management rows for services, source areas, unresolved questions, and each investigation coverage area.

## Execution

- Perform service catalog analysis by executing `CAP-INV-001`.
- Perform source and dependency analysis by executing `CAP-INV-002`.
- Perform change-target summarization by executing `CAP-INV-003`.
- Preserve the mapping between:
  - requested change
  - current affected behavior or asset
  - impacted target candidates
- Use spec-out style investigation when source code must be used to reconstruct missing understanding.

## Monitoring and Control

- Check that every investigation coverage area has a recorded state.
- Treat any unrecorded coverage area as a leak.
- Downgrade weakly supported conclusions to `unknown`.
- Downgrade impacted-target claims to `unknown` when the current source or document evidence is not strong enough to localize the change.
- Preserve the reason for every `out_of_scope` item.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Confirm no investigation coverage area remains unrecorded.
- Hand off unresolved items for later estimation or design.
- Escalate out-of-scope items when reassignment is required.

## Rules

- Do not decide implementation policy.
- Do not decide design policy.
- Every out-of-scope item must include a reason.
- Every uncertain item must include the missing evidence.
- Do not skip the current-behavior investigation when the change difference cannot be stated from documents alone.

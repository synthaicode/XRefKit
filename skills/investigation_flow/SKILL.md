<!-- xid: 9C0115875B0C -->
<a id="xid-9C0115875B0C"></a>

# Skill: investigation_flow

## Purpose

Execute the investigation sequence `CAP-INV-001 -> CAP-INV-002 -> CAP-INV-003` and produce scoped change targets for later estimation or design.

## Required Capability Definitions (XID)

- [CAP-INV-001 Service Catalog Analysis](../../capabilities/investigation/100_cap_inv_001_service_catalog_analysis.md#xid-867B78FF702F)
- [CAP-INV-002 Source and Dependency Analysis](../../capabilities/investigation/110_cap_inv_002_source_dependency_analysis.md#xid-E994FCDA8CD1)
- [CAP-INV-003 Change Target Summary](../../capabilities/investigation/120_cap_inv_003_change_target_summary.md#xid-6AB17163C9BF)

## Required Knowledge (XID)

- [Investigation coverage checklist](../../knowledge/investigation/100_investigation_coverage_checklist.md#xid-91E2A7C56101)

## Inputs

- request
- optional service catalog path
- optional candidate services supplied by the user
- optional repository or document paths for deeper analysis

## Outputs

- in-scope service list
- out-of-scope service list with reasons
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
- Define the step order: `CAP-INV-001 -> CAP-INV-002 -> CAP-INV-003`.
- Prepare management rows for services, source areas, unresolved questions, and each investigation coverage area.

## Execution

- Execute `CAP-INV-001` to identify in-scope and out-of-scope services.
- Execute `CAP-INV-002` to inspect source code, dependencies, data, interfaces, configuration, security, performance, and test viewpoints.
- Execute `CAP-INV-003` to structure outputs into a change target list and handoff summary.

## Monitoring and Control

- Check that every investigation coverage area has a recorded state.
- Treat any unrecorded coverage area as a leak.
- Downgrade weakly supported conclusions to `unknown`.
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

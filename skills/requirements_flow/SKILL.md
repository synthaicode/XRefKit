<!-- xid: 2B70BBF7B7BB -->
<a id="xid-2B70BBF7B7BB"></a>

# Skill: requirements_flow

## Purpose

Execute `CAP-REQ-001 -> CAP-REQ-002` and prepare requirement outputs for planning and later validation.

## Required Capability Definitions (XID)

- [CAP-REQ-001 Requirement Structuring](../../capabilities/requirements/100_cap_req_001_requirement_draft_creation.md#xid-BC408337F2A2)
- [CAP-REQ-002 Performance Constraint Structuring](../../capabilities/requirements/110_cap_req_002_performance_requirement_definition.md#xid-D67FAD650F8C)

## Inputs

- confirmed assumptions
- change target list
- change-test viewpoint table
- request
- optional performance constraints

## Outputs

- requirement draft
- performance requirement definition
- load-test draft plan
- change-requirement specification view for downstream tracing
- unresolved list when evidence is insufficient

## Required Knowledge (XID)

- [XDDP basics](../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)

## Startup

- Confirm assumptions are confirmed.
- Confirm change targets and test viewpoints exist.
- Confirm performance evidence exists when performance requirements are needed.
- Record `unknown` if required evidence is missing.

## Planning

- Define the requirement sections to draft.
- Treat the request as a difference against existing behavior, not only as a fresh requirement statement.
- Separate change reason, change requirement, and change specification explicitly.
- When possible, describe the intended difference in `before / after` form so downstream impact tracing can stay narrow.
- Map each business activity to its supporting capability:
  - requirement draft creation -> `CAP-REQ-001`
  - performance requirement definition -> `CAP-REQ-002`
- Define whether performance work is in scope.
- Prepare management rows for each requirement area and unresolved point.

## Execution

- Perform requirement draft creation by executing `CAP-REQ-001`.
- Perform performance requirement definition by executing `CAP-REQ-002` when performance concerns exist.
- Produce requirement statements at a precision level that can serve as downstream work instructions.
- Preserve the mapping between:
  - change reason
  - change requirement
  - change specification
- Preserve explicit change-difference statements so planning and QA can trace the same delta.
- Preserve unresolved evidence gaps as follow-up items.

## Monitoring and Control

- Check that each requirement area has a recorded status.
- Downgrade weakly supported requirement statements to `unknown`.
- Downgrade requirement text to `unknown` when the difference from current behavior cannot be stated clearly enough for tracing.
- Preserve explicit follow-up items for approval.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off unresolved requirement items for review or approval.
- Escalate out-of-scope requirement questions when reassignment is required.

## Rules

- Do not approve the requirement draft.
- Do not hide unresolved assumptions or performance evidence gaps.
- Do not collapse change reason and change specification into one statement.

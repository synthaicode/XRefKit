<!-- xid: 2B70BBF7B7BB -->
<a id="xid-2B70BBF7B7BB"></a>

# Skill: requirements_flow

## Purpose

Execute `CAP-REQ-001 -> CAP-REQ-002` and prepare requirement outputs for planning and later validation.

## Required Capability Definitions (XID)

- [CAP-REQ-001 Requirement Draft Creation](../../capabilities/requirements/100_cap_req_001_requirement_draft_creation.md#xid-BC408337F2A2)
- [CAP-REQ-002 Performance Requirement Definition](../../capabilities/requirements/110_cap_req_002_performance_requirement_definition.md#xid-D67FAD650F8C)

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
- unresolved list when evidence is insufficient

## Startup

- Confirm assumptions are confirmed.
- Confirm change targets and test viewpoints exist.
- Confirm performance evidence exists when performance requirements are needed.
- Record `unknown` if required evidence is missing.

## Planning

- Define the requirement sections to draft.
- Define whether performance work is in scope.
- Prepare management rows for each requirement area and unresolved point.

## Execution

- Execute `CAP-REQ-001` to draft the requirement document.
- Execute `CAP-REQ-002` when performance concerns exist.
- Preserve unresolved evidence gaps as follow-up items.

## Monitoring and Control

- Check that each requirement area has a recorded status.
- Downgrade weakly supported requirement statements to `unknown`.
- Preserve explicit follow-up items for approval.

## Closure

- Confirm all rows are finalized as `done`, `unknown`, or `out_of_scope`.
- Hand off unresolved requirement items for review or approval.
- Escalate out-of-scope requirement questions when reassignment is required.

## Rules

- Do not approve the requirement draft.
- Do not hide unresolved assumptions or performance evidence gaps.

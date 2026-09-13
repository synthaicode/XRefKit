<!-- xid: F2C91B7E4A60 -->
<a id="xid-F2C91B7E4A60"></a>

# Work-item model routing contract

This contract extends the instruction gateway from initial assessment into
workflow execution. It routes each dependency-ready work item from current
evidence. It does not treat one workflow, one conversation, or one previous
worker choice as the model-selection unit.

## State boundary

The client initializes `WorkflowState` from one validated `Assessment` and
persists every state returned by routing or result recording. A work item has a
stable `step_id`, `node_id`, definition hash, status, route revision, active
assignment, observations, failures, and completion or resolution evidence.

Only `pending` work whose dependencies are `done` is routable. Routing changes
an authorized assignment to `in_progress`. `in_progress`, `done`, `blocked`,
and `escalated` items are not dispatched again. A completed node can become
pending only through `initialize_instruction_workflow` with:

- a newer assessment revision;
- an explicit `scope_change` naming the affected step;
- evidence and a reason for that scope change.

Changing authorization does not redefine work-item complexity. Changed task,
scope, dependency, capability, metric, tool, or node definitions do.

## Selection boundary

`Policy.selection_strategy` is explicit:

- `priority` preserves the original instruction-gateway behavior and is the
  default for existing policies;
- `lowest_cost_eligible` chooses the lowest `cost_tier`, then policy priority
  and model ID, among candidates that pass capability, measurement, input-size,
  environment, and host constraints.

The repository contains no built-in model price table or competence claim.
Candidate tiers, limits, capabilities, and evaluation references remain
operator-supplied policy evidence. Skill `model_tier` continues to govern Skill
quality gates and is not replaced by gateway `cost_tier`.

Every `implementation` or `operation` model assignment returns an explicit
subagent dispatch plan. The client host performs the dispatch. The parent
remains the gateway and coordinator and does not execute that assigned work.
Operational work includes model judgment for activities such as PR composition,
CI interpretation, merge coordination, tag or release coordination, registry
interpretation, and clean-install result interpretation.

Deterministic commands remain tool assignments when no model judgment is
needed. Examples include an already-defined status query, checksum, package
install, or exact retry operation.

## Authorization boundary

External-action authorization is recorded independently as:

- `action`;
- exact `scope`;
- `status` (`required` or `authorized`);
- evidence when authorized.

Authorization never participates in the candidate tier or capability score.
An authorized low-cost worker may perform an authorized PR or release operation.
If authorization is required, the gateway may still report the selected model,
but it does not create an active assignment or dispatch. The host must refresh
the authorization record before execution.

## Failure and recovery boundary

A failed result records the selected model, the observed model, route evidence,
execution evidence, and one classified `FailureReport`.

A known transient failure may use `deterministic_retry` only when the report has
evidence, `known_transient=true`, and an exact `retry_tool_ref`. It remains a
tool step and does not justify model escalation.

An unexpected `tool`, `ci`, `security`, `dependency`, or `other` failure may use
`model_reroute` only when the report contains:

- failure classification evidence;
- a revised diagnosis or fix scope;
- `analysis` or `implementation` recovery kind;
- at least one additional required capability;
- evidence-bearing values for every complexity axis;
- a minimum cost tier higher than the failed assignment.

If no candidate satisfies the revised requirement, the result remains
`needs_assessment`. If evaluated candidates are blocked only by a VS Code parent
tier, it remains `conversation_upgrade_required`. Higher tier is assigned only
to this failure's diagnosis or fix route.

A successful recovery must name the active failure and provide resolution
evidence. The recovered node becomes `done`. Subsequent routine nodes are then
routed from their own original capability and complexity requirements. They do
not inherit the recovery model, capabilities, minimum tier, or route revision.

## Observation and evaluation

Each accepted result appends a route observation with selected model, observed
model, selected cost tier, evaluation reference, route evidence, outcome, and
execution evidence. A host fallback is retained as an explicit selected versus
observed mismatch; it is not rewritten as successful execution of the selected
route.

These observations support cost, retry, and acceptance evaluation. Missing
observations remain unknown. They do not authorize automatic policy rewriting.

## Generic API sequence

1. Prepare and complete the normal instruction `Assessment`.
2. Initialize or explicitly re-enter `WorkflowState`.
3. Call `route_instruction_work_items` with the latest state and fresh sources.
4. Execute only returned active assignments and host-ready subagent dispatches.
5. Call `record_instruction_work_item_result` with observed identity and evidence.
6. Persist the returned state and repeat from step 3 until complete or escalated.

The local equivalents are `xrefkit gateway workflow-init`, `workflow-route`,
and `workflow-result`.

## Related

- [Instruction gateway guide](../../guides/094_instruction_gateway.md#xid-E7A2C6109F43)
- [Skill operating contract](058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [Uncertainty protocol](016_uncertainty_protocol.md#xid-8A666C1FD121)
- [Context direction security guard](053_context_direction_security_guard.md#xid-A7F3C92D4E11)

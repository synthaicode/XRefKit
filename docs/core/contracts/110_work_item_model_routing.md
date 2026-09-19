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
at most one authorized assignment to `in_progress` per call. The state API is
stateless and returns whole-state replacements, so serial result application is
the concurrency boundary: record that result before routing the next node.
`in_progress`, `done`, `blocked`,
and `escalated` items are not dispatched again. A completed node can become
pending only through `initialize_instruction_workflow` with:

- a newer assessment revision;
- an explicit `scope_change` naming the affected step;
- evidence and a reason for that scope change.

Removing a node requires a `removed_steps` tombstone with the prior step ID,
node ID, definition hash, status, authorization snapshot, reason, and evidence.
The previous item, observations, failures, and completion evidence remain in
`WorkflowState.retired_items`. A revision cannot silently discard that history.

Changing authorization does not redefine work-item complexity. Changed task,
scope, dependency, capability, metric, tool, or node definitions do.

## Skill work-item adapter boundary

Adapter version 1 converts exactly one concrete Skill work item into one
gateway `Step`. The input carries a load-ready Skill execution profile and an
explicit work item. A model work item must provide `execution_kind`, Skill
capability inputs, evidence-bearing `model_requirements`, and values for all
six complexity axes. A deterministic work item must provide `tool_ref` and no
model requirements. This is the machine-readable decomposition boundary: the adapter never extracts
steps, dependencies, metrics, or execution kind from `SKILL.md` prose.

SkillDefinition metadata describes the reusable method and its criteria.
The [Workflow Runtime Binding contract](111_workflow_runtime_binding.md#xid-8D50A972BA9F)
owns the runtime `capability`, `tuning`, and `responsibility` fields derived
from the current instruction and recorded on the concrete work item binding;
`model_tier` remains a legacy split Skill quality-gate field and is not
SkillDefinition v1 metadata. These fields have no direct
relation to a model and are never converted into candidate capabilities, cost
tiers, or model ranking. `model_requirements` belongs to exactly one concrete work item:
it names only evaluated candidate-requirement labels, an optional minimum cost
tier, and evidence for why that work item needs them. The environment `Policy`
owns candidate limits, input limits, candidate labels, cost tiers, and
`evaluation_ref` evidence. Eligibility is determined only by the explicit work
item requirements, all six measurements, total input bytes, and that
environment-owned candidate evidence. A missing work-item requirement,
mismatched environment, or `unknown` measurement returns `needs_assessment`
with `step: null` and must not route. This applies to both model and
deterministic work items. A legacy `skill_adapter` policy block may be accepted
for compatibility, but it is ignored for model selection.

`execution_mode` is copied to model Steps. `local_default` permits analysis in
the current executor context. `subagent_preferred` emits an analysis SubAgent
dispatch when the host policy lists `analysis` in
`subagent_execution_kinds`; otherwise current-context execution remains
permitted. `subagent_required` requires that host support and stops routing when
it is absent. Host policies always retain `implementation` and `operation` in
this list for backward-compatible mandatory dispatch. Deterministic Steps never acquire a model dispatch from Skill
placement metadata.

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
quality gates and is not replaced by, mapped to, or compared with gateway
`cost_tier`.

Every `implementation` or `operation` model assignment returns an explicit
subagent dispatch plan. An `analysis` assignment also returns one when its Skill
Step declares `subagent_preferred` or `subagent_required` and the host policy
supports analysis dispatch. The client host performs the dispatch. The parent
remains the gateway and coordinator and does not execute dispatched work.
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
the authorization record before execution. This gate applies to both the
initial compatibility route and the per-work-item route.

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

1. Prepare the normal instruction sources and load the selected Skill envelope.
2. For each concrete Skill work item, call the version-1 adapter with explicit
   decomposition evidence and the environment-matched `Policy`.
3. Add every ready returned `Step` to the instruction `Assessment`; retain every
   non-ready adapter issue as `unresolved`.
4. Initialize or explicitly re-enter `WorkflowState`.
5. Call `route_instruction_work_items` with the latest state and fresh sources.
6. Execute only returned active assignments and host-ready subagent dispatches.
7. Call `record_instruction_work_item_result` with observed identity and evidence.
8. Persist the returned state and repeat from step 5 until complete or escalated.

The local adapter is `xrefkit gateway skill-adapt`; the remaining local
equivalents are `workflow-init`, `workflow-route`, and `workflow-result`.

## Related

- [Instruction gateway guide](../../guides/094_instruction_gateway.md#xid-E7A2C6109F43)
- [Skill operating contract](058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [Uncertainty protocol](016_uncertainty_protocol.md#xid-8A666C1FD121)
- [Context direction security guard](053_context_direction_security_guard.md#xid-A7F3C92D4E11)

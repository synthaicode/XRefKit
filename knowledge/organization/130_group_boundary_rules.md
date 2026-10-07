<!-- xid: 7A2F4C8D1301 -->
<a id="xid-7A2F4C8D1301"></a>

# Group Boundary Rules

This page records the canonical boundary rules for groups used in the business-capability model.

## Boundary Principles

- For a concrete group work item, `capability`, `tuning`, and `responsibility`
  use the meanings and derivation in the [Workflow Runtime Binding
  contract](../../docs/core/contracts/111_workflow_runtime_binding.md#xid-8D50A972BA9F).
- Capabilities may be reused across group boundaries. A group owns the bounded
  work-item outcome assigned to it, not the abstract capability or human
  adoption authority.
- Each group also owns self-check inside that same responsibility boundary.
- Each group runs its work with the same task lifecycle: `Startup -> Planning -> Execution -> Monitoring and Control -> Closure`.
- Planning owns value, constraints, assumptions, and requirement-level framing.
- Design owns technical realization structure and execution sequencing.
- Manufacturing owns implementation and unit-test execution inside approved scope.
- Quality owns evidence-based review and control checks.
- Operations owns release preparation and operational readiness evaluation.
- Coordinator owns routing of out-of-scope items, not quality or approval decisions.

## Prohibited Crossovers

- Planning must not decide implementation details that belong to design or manufacturing.
- Design must not decide business value or final release approval.
- Manufacturing must not change design policy silently.
- Quality must not substitute for human release approval.
- Operations must not approve final release timing.
- Coordinator must not judge quality, accept risk, or approve scope changes.

## Handoff Rules

- Cross-group handoff happens after group-internal self-check, not before it.
- Group-internal self-check must stay inside the same responsibility boundary as the executed work.
- Group-internal self-check is part of `Monitoring and Control`.
- `unknown` requires an explicit evidence-gap record.
- `out_of_scope` requires an explicit reason and handoff path.
- `missing` must be returned before closure.

<!-- xid: 7A2F4C8D1301 -->
<a id="xid-7A2F4C8D1301"></a>

# Group Boundary Rules

This page records the canonical boundary rules for groups used in the business-capability model.

## Boundary Principles

- Capabilities are reusable and may be shared across multiple responsibilities.
- Responsibility defines how a capability is exercised for a business purpose, including expected outputs, judgment criteria, and handoff behavior.
- Tuning specializes a capability by technology, framework, domain, or quality focus.
- A group does not own a capability in the abstract; it owns the responsibility for exercising tuned capabilities within its boundary.
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

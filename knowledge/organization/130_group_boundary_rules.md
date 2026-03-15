<!-- xid: 7A2F4C8D1301 -->
<a id="xid-7A2F4C8D1301"></a>

# Group Boundary Rules

This page records the canonical boundary rules for groups used in the business-capability model.

## Boundary Principles

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

- `unknown` requires an explicit evidence-gap record.
- `out_of_scope` requires an explicit reason and handoff path.
- `missing` must be returned before closure.

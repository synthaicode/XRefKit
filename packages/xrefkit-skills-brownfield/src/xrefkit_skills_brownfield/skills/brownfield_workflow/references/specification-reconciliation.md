<!-- xid: B4F1C8D2A609 -->
<a id="xid-B4F1C8D2A609"></a>

# Current specification and new requirement reconciliation

Use this procedure in the `design` phase after existing Requirement
validation and before design approval. Reconcile the current specification,
evidenced current behavior, and new requirement. Do not let implementation
behavior or AI interpretation silently decide the specification delta.

## Inputs

Collect:

- the authoritative current specification and its `requirement_ref`, version,
  authority, owner, and approval state;
- evidenced current behavior from source, tests, UI, API, logs, data, and
  operations;
- the validated new requirement and acceptance conditions;
- the draft design, service/data-flow impact, compatibility constraints, and
  existing test suite;
- known decisions, risks, downstream consumers, and unresolved items.

If the current specification or the new requirement cannot be identified,
record an impact-bearing `unknown` and do not approve a design delta.

## Reconciliation procedure

1. Preserve traceability for the current specification, current behavior, new
   requirement, design item, and affected test cases.
2. Compare current specification with current behavior. Record differences as
   evidence of drift; do not treat current behavior as business truth.
3. Compare the new requirement with the current specification and classify
   each item as `preserve`, `change`, `add`, `deprecate`, `incompatible`, or
   `unknown`.
4. Compare each classified item with the draft design, data propagation,
   compatibility, downstream consumers, and existing tests.
5. Record the required design delta, protected invariants, migration or
   rollback treatment, observability, and test impact.
6. For every conflict or `unknown`, record evidence, downstream impact,
   resolver, owner, next action, and the human decision required.
7. Obtain human approval for the reconciliation decision before design,
   manufacturing, or test-case approval proceeds.

## Before retrying implementation

Run this same reconciliation as soon as an implementation, verification or
review finding could require a correction, before looking for repair options.
Re-enter design for the affected finding and pin the Work Item revision,
reviewed candidate, requirements, acceptance criteria and observed evidence.
Check the purpose, approved design policy, its rationale and scope, operation
preconditions, success and failure conditions, exceptions and recovery policy.
Use Knowledge search and XID resolution for applicable general principles;
record each XID, revision and applicability basis. Separately cite the
project's adopted decision and exact revision. A project decision may have a
versioned record before Knowledge adoption; keep its missing XID explicit.

Apply the following evidence rules before proposing another implementation:

| Cause | Evidence and next step |
| --- | --- |
| `IMPLEMENTATION_DEFECT` | A current, applicable approved rule covers the case and the evidence shows a bounded violation. Use `IMPLEMENTATION_FIX`; record the scoped correction and regression acceptance. |
| `DESIGN_POLICY_MISSING` | The decision is material and the applicable approved sources have been checked; record the missing rule. |
| `DESIGN_POLICY_CONFLICT` | Cite the incompatible decisions at their exact revisions and the affected scope. |
| `DESIGN_POLICY_INVALID` | Show how the current applicable policy fails the requirement or constraint. A policy application error with a clear correct binding can be an implementation defect. |
| `INSUFFICIENT_EVIDENCE` | Identify the missing or stale source, investigation and owner. Use `INVESTIGATION_REQUIRED` with no presumed design defect. |
| `REQUIREMENT_CHANGE` | Cite the confirmed changed requirement and return through requirements before design. |

Use `DESIGN_REVIEW_REQUIRED` for a material gap, conflict or invalid policy,
a confirmed changed requirement, or when the affected policy must be
re-decided to change a design/authority boundary. Keep authorized unrelated
work moving. Retry history can inform investigation and limits.

### Operation failure and replay

Check whether the failure is transient, the operation's preconditions still
hold, the evidence supports success on replay, side effects or duplicate
execution are excluded, attempt/deadline/budget limits hold and the next step
is safe. Authentication failure stops same-condition execution. Invalid
response format is a contract violation. Then determine whether an applicable
approved contract already defines its treatment. A timeout or absent receipt
does not prove non-execution. Reconcile the original effect, or establish an
approved safe replay contract before retrying an operation that may have run.
Reuse current operation identity and the existing execution/retry gate.
`xrefkit_skills_brownfield.design_review.retry_disposition` accepts explicit
conditions and returns a disposition without executing an operation.

### Work Item result and Handoff

In an Engineering Decision Gate project (XID `C34E62A9B710`), prepare the
specific decision in the enrolled draft Run before choosing an authoritative
design. Use the resolved global and project references in the receipt. Record
applicability, alternatives, reconciliation and replay verification, then submit
the exact candidate for independent review. Use the authorized candidate and
action from the current Core decision for manufacturing, test design or retry.
For a reserved decision, carry the `ESCALATION_REQUIRED` decision ID as
`engineering_decision_id` in both the finding and the formal request.

When principle discovery is enabled in the host's engineering policy, include
`decision_context` at prepare. Describe the decision category, target,
requirement references, constraints, assumptions, side effects, state,
concurrency, failure impact and prior XIDs or decisions. Read the discovered
global and project references with their version and applicability conditions.
Assess every candidate and record conflicts and unknowns through `resolve`
before selecting the design. Carry the returned `reference_set_sha256`,
the same applicability assessments and the alternatives into review.
If new constraints, effects or artifact changes alter applicability, prepare
a replacement decision that supersedes the old ID and resolve its references
again. Route technical evidence gaps to investigation. Use the existing
formal Handoff for decisions reserved to an authority.

For checklist-enabled projects, Core returns the selected global and
decision-specific checks in the resolved reference set. Evaluate each against
the exact design candidate. Record check revision, applicability, status,
reason, source XID versions, pinned verification evidence, unresolved issues
and evaluator in the proposal's checklist. Honor the applicability conditions
even for a check you consider unnecessary. Preserve incomplete technical
checks in a blocked draft or authority Handoff. Retain independent review of
the recorded evaluations and technical evidence.

Use `xrefkit_skills_brownfield.design_review.make_finding` to record an explicit
technical judgment as `brownfield.design_finding/v1`. This is a versioned
artifact in the existing result and Handoff. Keep the Work Item ID/revision,
Skill Run, stable finding ID, observation, cause, outcome, rationale,
confidence, evidence pointers, principles, policy gaps, related Issue
candidates, required approval roles, open questions and next phase.
Each principle reference has `xid` (null when only a project decision exists),
`revision`, `ref` and `applicability`. Name required evidence and a resolver for
each unknown. Use the same finding ID and the same artifact for redelivery.
Record the exact reviewed candidate through evidence and link approval records
through the owning project route. Respect current Handoff and Closure gates.
For changed understanding or impact, send the existing
`brownfield.change_impact/v1` separately through the configured PM route.

## Reconciliation matrix

Each row should be traceable and contain at least:

| Field | Meaning |
|---|---|
| `reconciliation_id` | Stable row identifier |
| `requirement_ref` | Current or new Requirement reference |
| `current_spec` | Applicable current specification and version |
| `current_behavior_evidence` | Evidence of what the system currently does |
| `new_requirement` | Requested behavior or condition |
| `delta_class` | `preserve`, `change`, `add`, `deprecate`, `incompatible`, or `unknown` |
| `design_delta` | Structural and behavioral change required |
| `protected_invariants` | Existing behavior that must remain |
| `compatibility_impact` | Consumers, migration, rollback, and release impact |
| `test_impact` | Cases, expected results, evidence, and retest impact |
| `decision` | Human-approved treatment or open decision |
| `owner` | Person or role responsible for the decision |

## Required output

Produce a summary-first reconciliation result containing:

- current specification, current behavior, and new requirement scope;
- the reconciliation matrix and evidence links;
- specification drift, conflicts, protected invariants, and design deltas;
- compatibility, data-flow, downstream, migration, rollback, and test impact;
- human decisions, unresolved items, owners, and handoff conditions;
- the approved design-to-test input package.

## Human design gate

The design may proceed only when each in-scope new requirement has a recorded
delta class and decision, current behavior and current specification drift is
visible, protected invariants are explicit, and downstream/test impacts are
understood. A material `incompatible` or `unknown` row requires human decision,
revision, deferral, or escalation; it is not an implicit approval.

## UNKNOWN resolution through Decision Handoff

For each recorded checklist UNKNOWN, capture its cause, required action,
expected evidence and acceptance criteria. Use `DESIGN_UNRESOLVED` for technical
rework Brownfield can perform. For work requiring another party, classify the
gap as `MISSING_INFORMATION`, `MISSING_EVIDENCE`, `AUTHORITY_REQUIRED`,
`ENVIRONMENT_BLOCKED` or `KNOWLEDGE_GAP`. Group Check IDs by common cause,
assignee, environment, authority and routing role for the same decision.
Provide the host with the recorded finding, including the checklist question,
reason, evaluated XID revisions and exact candidate digest. The host publishes
the scoped `UNKNOWN_RESOLUTION` request through Decision Handoff.

After the original Run acknowledges the return, inspect the request and human
evidence. Use a new draft Run and decision ID, link the superseded decision,
resolve XIDs again and rerun the checklist against the current candidate.
Record the effect of the supplied information or evidence and keep incomplete
checks UNKNOWN. Risk acceptance supplies policy context. Technical claims still
need verification and independent review through the Engineering Decision Gate.

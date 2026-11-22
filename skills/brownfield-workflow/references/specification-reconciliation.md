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

Return to the design phase before starting an implementation retry after a
review or verification finding. Reuse the current reconciliation record and
the exact reviewed candidate.

1. For each finding, link the observed behavior and evidence to the approved
   design principle, requirement and acceptance condition at their recorded
   revisions. State the expected behavior and the affected boundary.
2. Record whether the evidence shows implementation drift from a clear design,
   a missing or conflicting design condition, or insufficient evidence to
   decide. If the required behavior or acceptance condition itself is unclear,
   route the question back to requirements. Preserve approved invariants and
   carry forward any unresolved finding.
3. For implementation drift, record the scoped correction and expected
   verification result. For a design gap or conflict, reconcile the design
   delta before handing it back to implementation. Where relevant, specify
   avoided effects, failure handling, recovery, escalation and the evidence
   that demonstrates each expected result. Record the owner and what would
   resolve any remaining unknown.
4. Record the judgment, grounds, affected regression coverage and retry
   conditions in the designated work record. Apply the existing design review,
   approval and retry rules for the affected scope. Resume implementation
   only when the applicable conditions are satisfied.

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

In an enrolled Engineering Decision Gate project (XID `C34E62A9B710`), record
the decision in the draft Run and provide its verified reference receipt before
choosing the design. Use the exact authorized candidate at the manufacturing or
test-design boundary. Re-enter this gate for material changes or retry decisions.

With principle discovery enabled, prepare the decision context and read the
configured and discovered references. Record all applicability assessments,
explicit unknowns and conflicts through `resolve` before selecting a design.
Use its reference-set digest in review. Supersede and reassess the decision
when the governing facts or the design candidate change.

In a checklist-enabled project, evaluate the Core-selected checks against the
exact candidate before review. Preserve reasons, applicable reference
revisions, evidence and unresolved checks in the decision record.

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

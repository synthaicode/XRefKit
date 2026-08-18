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

<!-- xid: 427525B4935A -->
<a id="xid-427525B4935A"></a>

# Workflow and decision rules

## 15-step sequence

1. Confirm system boundary, executable command, versions, isolated DB, and adapter.
2. Locate C# entry points and every SP invocation and parameter mapping.
3. Trace child SPs, functions, views, tables, temp objects, table variables, dynamic SQL, transactions, outputs, result sets, and exceptions.
4. Extract combination dimensions and values from evidence; mark missing values unknown.
5. Record business, technical, and upstream constraints in separate ledgers.
6. Compute Cartesian candidate count and post-constraint count deterministically.
7. Prove safe execution with a small input and verify DB side effects.
8. Decide full-run feasibility from measured duration, timeout, parallelism, and side effects.
9. Capture the old version as observed baseline, never as business truth.
10. Define the new requirement predicate and allowed differences with evidence and owner.
11. Run old and new on identical serialized inputs through an isolated adapter.
12. Normalize and classify each result; retain traceability for every difference.
13. Select a deterministic daily reduced regression set covering dimensions, constraints, paths, and difference classes.
14. Generate a release-time full-run procedure with rollback/restore and stop gates.
15. Escalate unresolved decisions; do not close while material unknowns remain unowned.

## Classification precedence

`system_error` > `uncertain` > `business_invalid` > `upstream_absent` >
result comparison. An explicitly configured `business_invalid` or
`upstream_absent` predicate is evidence for classification, not a substitute
for human approval. A missing predicate or unresolved dynamic path is
`uncertain`, not valid.

## Result comparison

Compare configured fields after removing or normalizing only configured
non-deterministic fields. `planned_difference` requires a matching expected
difference rule. Any other changed value is `unexplained_difference`.
Unchanged successful outcomes are `baseline_match`. Missing execution records
are `not_executed`.

## Human decisions

Present the candidate input, counts, evidence, and impact of each option for:
business validity, baseline defects, expected differences, upstream absence,
and release disposition. Do not fill these decisions by inference.

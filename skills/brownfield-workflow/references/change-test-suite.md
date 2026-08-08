<!-- xid: B4F1C8D2A604 -->
<a id="xid-B4F1C8D2A604"></a>

# Brownfield change test suite

The objective is to show that changed behavior is correct and in-scope existing
behavior is not unintentionally broken. Do not imply an unconditional
guarantee for the whole system.

## Before the change

Create or refresh the test suite from specification values, explicit
constraints, boundaries, important existing behavior, changed branches,
affected call/data paths, and protected unchanged paths. Capture input, data
state, execution path, result, and whether the result must be preserved or is
intended to change.

Use pairwise only for affected factors. Add boundary, negative,
historical-defect, multi-factor, state, retry, idempotency, concurrency,
rollback, and side-effect cases when evidence requires them. White-box
structure selects and explains cases; it does not replace business approval.

## After the change

Execute the same serialized inputs and data states where safe. Classify results
as preserved behavior, approved/planned difference, unexplained difference,
invalid/upstream-absent, uncertain, system error, or not executed. Show the
test-to-structure mapping and why each case is in scope.

## Evidence

Record tool versions, environment, test data and extraction method, raw results,
logs, expected results, failure classification, retest, residual risk, and
stable links for test, change, data, path, and evidence IDs. Separate an
overview stating objective, policy, scope, impacted areas, result, risk, and
decisions from detailed structure, data, cases, results, and unresolved paths.

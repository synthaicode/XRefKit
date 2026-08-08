<!-- xid: B4F1C8D2A614 -->
<a id="xid-B4F1C8D2A614"></a>

# Brownfield change test suite

Create or refresh the suite before the implementation change. Use specification
values and constraints, important existing behavior, changed branches,
affected call/data paths, and protected unchanged paths. Capture pre-change
inputs, data state, execution path, result, and preserve/intentional-change
decision.

Use pairwise only for affected factors and add evidence-based boundary,
negative, historical-defect, multi-factor, state, retry, idempotency,
concurrency, rollback, and side-effect cases. White-box structure explains
selection; it does not replace business approval.

After the change, run the same serialized inputs/data states where safe and
classify preserved behavior, planned difference, unexplained difference,
invalid/upstream-absent, uncertain, system error, or not executed. Separate an
overview from detailed structure, data, cases, results, logs, and unresolved
paths, using stable evidence IDs.

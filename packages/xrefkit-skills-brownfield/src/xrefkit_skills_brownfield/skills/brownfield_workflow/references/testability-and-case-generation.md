<!-- xid: B4F1C8D2A607 -->
<a id="xid-B4F1C8D2A607"></a>

# Testability gate and AI test-case generation

Use this procedure during planning and design, before test execution. Its
purpose is to confirm that an affected behavior is sufficiently defined to
create a reproducible test case, then let AI generate traceable case
candidates. It does not approve business expectations or release risk.

## Required inputs

Collect the following from upstream items and current-system evidence:

- change purpose, acceptance conditions, and scope;
- impacted service, screen, API, data, event, and downstream path;
- design delta, state transitions, error/retry behavior, and compatibility;
- current behavior or a pre-change baseline;
- input data, fixture, precondition, actor, permission, and environment;
- expected result, expected-result basis, display/format rule, tolerance, and
  error expectation;
- execution route and observable evidence source such as UI capture, API
  response, log, event, or database state;
- test tool, version, reproducibility, cleanup, result storage, and owner;
- upstream traceability and stable `xddp_row_id`, `test_id`, `evidence_id`,
  `change_point_id`, or equivalent identifiers when available.

## Gate procedure

1. Derive candidate behaviors from the approved change impact and upstream
   traceability. Do not create an independent task catalogue.
2. Check each candidate for target, purpose, precondition, input, expected
   result, observation method, pass/fail rule, evidence, and owner.
3. Check consistency between the requirement, design, current behavior,
   expected result, data state, and downstream effect.
4. Mark each field as confirmed, partial, missing, or conflicting, with the
   evidence source and downstream impact. Treat stale or unavailable evidence
   as an impact-bearing `unknown`.
5. Generate a test-case candidate only when the case can be executed and
   judged reproducibly. Attach its traceability, rationale, coverage factors,
   and required evidence.
6. For a missing or conflicting definition, do not invent an input,
   expected value, default, or business rule. Return a definition gap with
   the minimum question, resolver, owner, and handoff condition.
7. Obtain human approval for the business meaning of the expected result and
   pass/fail rule, risk-based scope, and unresolved design or requirement
   decisions before execution.

## Coverage prompts

After the basic case is defined, consider normal, error, boundary, negative,
historical-defect, state, retry, idempotency, concurrency, rollback, side
effect, and downstream-propagation cases when the affected structure or data
evidence requires them. Use pairwise only for affected factors.

## Required outputs

Produce a summary-first testability result containing:

- the gate conclusion and affected scope;
- generated case candidates with traceability and evidence requirements;
- definition gaps, conflicts, owners, and next actions;
- coverage rationale and deliberately excluded areas;
- human decisions required before execution;
- the handoff package for the Testing phase.

The gate confirms definition completeness, not business correctness. Keep both
claims separate in the report.

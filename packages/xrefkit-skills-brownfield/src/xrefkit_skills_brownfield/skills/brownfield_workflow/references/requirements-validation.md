<!-- xid: B4F1C8D2A608 -->
<a id="xid-B4F1C8D2A608"></a>

# Existing requirement validation

Use this procedure in the `requirements` phase when a Requirement, acceptance
specification, ticket, contract, or equivalent upstream definition already
exists. Validate the existing definition before treating it as the basis for
design or test generation. Do not silently rewrite it.

## Validation inputs

Collect:

- the existing Requirement and its stable identifier;
- version, update date, source, approval state, owner, and scope;
- change request and upstream item;
- current behavior evidence from source, tests, logs, UI, API, data, or
  operations;
- desired behavior, acceptance conditions, normal/error/boundary conditions;
- existing design, data-flow, service ownership, and related test artifacts;
- known decisions, constraints, risks, and unresolved items.

If the Requirement source, version, owner, or approval state cannot be
confirmed, record that as an impact-bearing `unknown`.

## Validation procedure

1. Identify the Requirement being validated and preserve its traceability.
2. Check freshness, authority, approval state, owner, scope, and applicable
   conditions.
3. Compare the Requirement with evidenced current behavior. Current behavior
   is evidence of what exists, not proof of business correctness.
4. Compare the Requirement with the change purpose, design, data-flow, and
   existing tests.
5. Check whether each acceptance condition is testable: target, precondition,
   input, expected result, observation source, pass/fail rule, and evidence.
6. Classify each finding as confirmed, missing, conflicting, stale, or
   unverified, and record its evidence and downstream impact.
7. Produce the validation result and human decision questions. Do not approve
   business meaning, resolve a specification conflict, or invent a missing
   condition on behalf of the responsible human.

## Required output

Produce a summary-first validation result containing:

- `requirement_ref` and source/version/owner/approval evidence;
- validated scope and excluded scope;
- current-behavior and desired-behavior comparison;
- acceptance-condition coverage and testability result;
- confirmed findings, missing definitions, conflicts, stale items, and
  unverified items;
- downstream impact, resolver, owner, and next action for every unresolved item;
- human decision: approve, revise, defer, or escalate;
- handoff conditions for `planning` or `design`.

## Human decision gate

The Requirement may be used as a design or test basis only after the human
confirms that its meaning, scope, acceptance conditions, and unresolved-item
treatment are appropriate. A Requirement with a material conflict, missing
expected result, unknown owner, or unverified authority must be returned for
decision rather than treated as approved.

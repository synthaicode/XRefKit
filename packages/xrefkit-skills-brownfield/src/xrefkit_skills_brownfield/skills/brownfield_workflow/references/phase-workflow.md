<!-- xid: B4F1C8D2A611 -->
<a id="xid-B4F1C8D2A611"></a>

# Brownfield phase workflow

Use the phase sequence `requirements -> planning -> design -> manufacturing ->
testing`. Preserve upstream references and carry forward decisions, unknowns,
evidence, owners, and handoff conditions.

Planning has two checkpoints. First produce the initial work policy from the
available Requirement and current-system evidence: impacted targets,
dependencies, order, tools, versions, fixtures, environment, test data,
cleanup, result storage, compatibility, migration, release, rollback, risks,
stop conditions, gates, and handoffs. After the design-phase specification
reconciliation, refine this policy from approved delta rows before
manufacturing or test-case approval. Tool preparation belongs here; execution
belongs to testing. See
`delta-detail-planning.md#xid-B4F1C8D2A610` for the second planning checkpoint.

## Implementation and verification sequence

For work that changes code, plan and record the following stages in order.

1. **Design.** Before coding, check external interfaces such as APIs, SDKs,
   and services against the applicable official documentation. Record the
   source URL and version or date, and the constraints that affect the
   design and tests. Carry unresolved contract details into the existing
   decision and handoff process.
2. **Implementation.** Implement the approved end-to-end change, including
   its failure paths, before sending the candidate to code review.
3. **Code review.** Review the complete candidate against the design and the
   documented interfaces. Address blocking findings before logic testing.
4. **Stub and logic tests.** Before testing against real dependencies, create
   stubs for the affected external interfaces and run automated logic tests
   for normal, error, and boundary cases. Record the exact candidate and
   results. Record why a stub is inapplicable for a change with no external
   boundary.
5. **Real-environment tests.** After the logic tests pass, test the same
   candidate through the real entry point and relevant dependencies under
   the existing authorization. Record the environment, result, and any
   checks still pending because a dependency or approval is unavailable.

If a test reveals a defect, correct the candidate, review the correction,
and rerun the affected logic and real-environment tests in that order.
Keep offline evidence and real-environment results distinct.

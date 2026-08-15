<!-- xid: B4F1C8D2A610 -->
<a id="xid-B4F1C8D2A610"></a>

# Post-reconciliation detailed planning

Planning is not completed only from the initial Requirement. After the current
specification, current behavior, and new requirement have been reconciled,
refine the plan from the approved delta. Use this checkpoint before
manufacturing and test-case approval.

## Two planning checkpoints

### Initial planning

Define the provisional scope, impacted targets, dependencies, tools, data,
environment, compatibility, release, rollback, risks, gates, owners, and
handoffs from the available Requirement and current-system evidence.

### Delta-detail planning

After reconciliation, replace provisional assumptions with the approved delta,
protected invariants, downstream impact, and human decisions. Re-plan the
concrete work needed to implement and verify that delta.

## Required inputs

- approved specification reconciliation matrix;
- delta class, design delta, protected invariants, compatibility and downstream
  impact for each in-scope row;
- current work policy and its assumptions;
- service/data-flow, Entity change points, current data, and existing tests;
- approved decisions, unknowns, risks, owners, and handoff conditions.

## Detailed planning procedure

1. Recalculate impacted targets and work units from each approved delta row.
2. Replace assumptions with concrete implementation points, dependencies,
   execution order, and owners.
3. Detail data migration, compatibility, release, rollback, retry, replay,
   cleanup, and operational controls where affected.
4. Detail test cases, fixtures, environments, expected results, evidence
   sources, pre/post baseline, retest, and result storage.
5. Update gates and stop conditions for `unknown`, incompatible behavior,
   unavailable data, failed evidence, and unexplained differences.
6. Trace each work unit, test, evidence item, and handoff to the reconciliation
   row and upstream item.
7. Obtain human approval that the detailed plan is executable and covers the
   approved delta before manufacturing or testing proceeds.

## Required output

Produce a post-reconciliation detail plan containing:

- `reconciliation_id` to `work_item_id` mapping;
- refined scope, work units, dependencies, order, and owners;
- implementation points and protected invariants;
- data, compatibility, release, rollback, and operational treatment;
- test cases, fixtures, expected results, evidence, baseline, and retest plan;
- updated gates, stop conditions, risks, and handoffs;
- human approval, open decisions, and conditions for manufacturing/testing.

Do not treat the initial work policy as final when the reconciliation changes
scope, behavior, compatibility, data propagation, or test impact.

<!-- xid: 8C4D2A7E5102 -->
<a id="xid-8C4D2A7E5102"></a>

# Test Design Criteria

This page defines the minimum criteria for expanding a test policy into executable test design.

## Required Coverage

| Area | What to define |
|------|------|
| Test target | which behavior, component, path, or boundary is tested |
| Test level | unit, integration, regression, scenario, or other intended level |
| Test viewpoint | normal path, edge case, error path, recovery path, security path, performance-sensitive path, long-run behavior, load or peak behavior, failure and failover behavior, business-cycle behavior |
| Input conditions | required data, configuration, state, and preconditions |
| Expected result | observable expected behavior or output |
| Trace basis | which requirement, test policy, or design artifact this test realizes |
| Automation scope | whether the test is automated, manual, or deferred |
| Out-of-scope note | what is intentionally excluded and why |

## Rules

- Test design must not be an unlabeled test list.
- Each test case or test group must cite its basis.
- Missing expected results must be recorded as `unknown`.
- Intentional exclusions must be recorded as `out_of_scope` with a reason.

## Additional Viewpoints

The following viewpoints should be considered explicitly when they matter to the target system.

| Viewpoint | What to confirm |
|------|------|
| Long run | behavior over sustained operation, including resource leaks, gradual degradation, accumulation errors, and long-duration stability |
| Load | throughput, concurrency, peak demand, queue growth, timeout behavior, and performance under realistic or stressed load |
| Failure | error handling, retry, recovery, failover, partial failure, restart behavior, and data consistency after faults |
| Business cycle | repeated operational cycles such as daily, weekly, monthly, closing, aggregation, or periodic batch scenarios |

## Source Note

- These additional viewpoints are aligned with IPA's non-functional requirements approach, especially availability, performance and scalability, and operability and maintainability concerns.
- See [IPA test viewpoint supplement](120_ipa_test_viewpoint_supplement.md#xid-8C4D2A7E5103).

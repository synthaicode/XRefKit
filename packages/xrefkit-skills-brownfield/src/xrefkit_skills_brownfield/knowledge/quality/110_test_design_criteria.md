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
- Executable tests must not be handed off without explicit preparation coverage
  for test data, environment setup, initial state, cleanup/reset, evidence
  capture, and execution configuration, or an explicit unresolved-state reason.
- Repeatable or fragile setup, execution, reset, or evidence collection steps
  should be scripted when scripting materially improves reproducibility,
  consistency, or handoff clarity.
- Test tools, helper scripts, test data, environment items, and setup/clear-up
  procedures are testware; keep them traceable to the test basis and test items.

## Additional Viewpoints

The following viewpoints should be considered explicitly when they matter to the target system.

| Viewpoint | What to confirm |
|------|------|
| Long run | behavior over sustained operation, including resource leaks, gradual degradation, accumulation errors, and long-duration stability |
| Load | throughput, concurrency, peak demand, queue growth, timeout behavior, and performance under realistic or stressed load |
| Failure | error handling, retry, recovery, failover, partial failure, restart behavior, and data consistency after faults |
| Business cycle | repeated operational cycles such as daily, weekly, monthly, closing, aggregation, or periodic batch scenarios |

## Test Implementation Preparation

The following preparation work products should be considered before test
execution is handed off.

| Preparation item | What to define |
|------|------|
| Test data | required records, files, messages, edge values, masking/synthetic data needs, data ownership, refresh timing, and cleanup rules |
| Test environment | target configuration, deployed version, infrastructure, dependencies, service virtualization/stubs/drivers/simulators, and environment verification |
| Initial state | database state, queue/topic state, file state, cache/session state, feature flags, tenant settings, and time/clock assumptions |
| Execution configuration | browser/OS/runtime/DB/configuration matrix, assigned tester or runner, test suite/case mapping, and execution schedule/order |
| Helper script | local-domain script or command that prepares data, verifies environment, invokes tools, resets state, or collects evidence |
| Evidence capture | logs, screenshots, reports, coverage output, exported data, trace IDs, result location, and retention rule |
| Cleanup/reset | rollback, deletion, fixture reset, environment restore, seed refresh, and idempotency or rerun behavior |
| Tool gap | missing tool or script, affected test items, creation/verification plan, owner, handoff, and availability condition |

## Source Notes

- ISTQB CTFL 4.0.1 separates test design, test implementation, and test
  execution. Test design defines test data, environment, infrastructure, and
  tools; test implementation creates or acquires testware such as test data,
  procedures, suites, manual/automated scripts, execution schedule, and verified
  environment items.
- ISTQB Glossary treats scripts, inputs, expected results, setup/clear-up
  procedures, files, databases, environments, and additional testing utilities
  as testware.
- Azure Test Plans models test plans, suites, test cases, configurations,
  assigned testers, execution, and result tracking; configuration differences
  should be represented explicitly.
- DORA's test data management guidance emphasizes that automated test suites
  need adequate test data available on demand and should not be constrained by
  unavailable data.
- Google Developers guidance for automated/CI testing emphasizes integrating
  tests with architecture, platform, language, and delivery pipeline.

## IPA Source Note

- These additional viewpoints are aligned with IPA's non-functional requirements approach, especially availability, performance and scalability, and operability and maintainability concerns.
- See [IPA test viewpoint supplement](120_ipa_test_viewpoint_supplement.md#xid-8C4D2A7E5103).

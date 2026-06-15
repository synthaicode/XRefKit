<!-- xid: 4314A1A73CAF -->
<a id="xid-4314A1A73CAF"></a>

# C# Test Synchronization Patterns

This page records the adopted remediation patterns for test-synchronization
races that compiler diagnostics do not catch, and the required application
mode for them.

## Status

- adopted as the preferred remediation family (owner decision, 2026-06-13)
- application mode: **per-case proposal and approval** — see below

## Application Mode (binding)

- These patterns are precedents, not auto-apply rules.
- When a matching occurrence is found, the AI proposes the concrete change
  with evidence (file, line, and the race window described) and waits for
  approval before modifying the test.
- Bulk application across a codebase without per-case approval is not
  allowed, even when every occurrence matches the anti-pattern exactly.
- A declined proposal is recorded as a judgment, not retried verbatim.

## Anti-Patterns (what to detect)

- `await Task.Yield()` used as a synchronization guarantee before advancing
  a fake clock or asserting cross-task state: yielding once does not
  guarantee the other task reached its wait point or state transition.
- Real-time waits (`Task.Delay`, real `SystemClock`) in unit tests to make
  time-based behavior (idle timeout, expiry) occur: environment-dependent
  and flaky under CI load.

## Adopted Patterns

1. Waiting for a blocked operation to park on its timer before advancing a
   fake clock:

   ```csharp
   var delayCallsBefore = clock.DelayCallCount;
   var blocked = pool.AcquireLeaseAsync();
   Assert.True(
       SpinWait.SpinUntil(
           () => clock.DelayCallCount >= delayCallsBefore + 1,
           TimeSpan.FromSeconds(1)),
       "Expected the blocked operation to park on a timer wait.");
   clock.Advance(timeout);
   ```

2. Waiting for an observable state transition instead of yielding:

   ```csharp
   Assert.True(
       SpinWait.SpinUntil(() => pool.GetSnapshot().WaitingCallers == 1,
           TimeSpan.FromSeconds(1)),
       "Expected the second acquire to register as a waiting caller.");
   ```

3. Time-based expiry driven by a fake clock, never by real elapsed time:

   ```csharp
   // idleTimeout: 5s in options, FakeClock injected
   clock.Advance(TimeSpan.FromSeconds(6));
   ```

Common properties: the wait condition is an observable producer-side signal
(`DelayCallCount`, a snapshot field), the spin has an explicit timeout, and
the assertion message names what was expected.

## Precedent Evidence

- MailKit.Pooling, 2026-06-12: findings F-005, F-006, F-007 in
  `work/sessions/2026-06-12_csharp_review_mailkit_pooling_findings.md`;
  fixes validated in `tests/MailKit.Pooling.Tests/Pool/PoolStateTransitionTests.cs`
  (commit `7b9b645` on `fix/csharp-review-findings`).
- The same repository already contained the correct pattern
  (`Blocked_Acquire_Does_Not_Wake_From_Stale_Return_Signals`,
  `DisposeAsync_Wakes_Blocked_Acquire_With_ObjectDisposedException`), which
  served as the local precedent for the fixes.

## Boundary

- This page records remediation patterns; detection criteria live in the
  [C# review spec](100_csharp_review_spec.md#xid-30E6A4F6F3AA).
- The patterns assume a fake clock that exposes an observable wait-arrival
  signal (such as `DelayCallCount`); when the local clock abstraction lacks
  one, propose adding the signal first instead of forcing the pattern.

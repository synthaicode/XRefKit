# Case 004: candidate reduction and full-run feasibility

## Task

Derive a reproducible candidate set from the explicit dimensions and
constraints, measure the full-run feasibility, and recommend a reduced daily
regression set. Do not call the result a mathematically balanced orthogonal
array.

## Explicit dimensions

```yaml
region: [JP, US, EU]
mode: [Full, Delta]
priority: [Normal, Rush]
```

Candidate count before constraints is 12.

## Explicit constraints

- `EU + Delta` is upstream_absent for every priority.
- `US + Rush` is business-invalid for `Full` and `Delta`.
- `JP + Delta + Rush` is allowed but must be represented in the reduced set.

## Measured execution facts

- one isolated candidate takes 2.5 minutes;
- 8 workers are available, but the database side-effect audit permits only 2
  concurrent workers;
- 8 candidates caused lock waits in the small safe run;
- rollback/restore was verified for the small run;
- 6 candidates have unexplained new result differences;
- the release window is 30 minutes.

## Existing reduced-set proposal

```yaml
reduced_set:
  - {region: JP, mode: Full, priority: Normal}
  - {region: JP, mode: Delta, priority: Rush}
  - {region: US, mode: Full, priority: Normal}
  - {region: EU, mode: Full, priority: Rush}
  - {region: EU, mode: Delta, priority: Normal}
```

The proposal omits the `US + Rush` invalid class and includes `EU + Delta`
even though that class is upstream_absent.

## Required output

Report candidate/post-constraint counts, identify invalid and upstream-absent
classes, assess the full-run window and concurrency risk, correct or reject the
reduced-set proposal, and specify the release-time full-run stop gates.

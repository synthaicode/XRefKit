<!-- xid: A9B7C6D5E4F1 -->
<a id="xid-A9B7C6D5E4F1"></a>

# Python Review Spec

This fragment defines the canonical Python-specific overlay for source review.

## Scope Boundary

- Apply the language-neutral criteria in
  [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001).
- Exclude issues already covered by the configured static baseline such as
  type checker, formatter, linter, dependency scanner, or test diagnostics.
- Hand security findings to `security_review`; hand design-assumption findings
  to the constraint-derivation pack.

## Category Evaluation Rule

Evaluate each category by its own axis. Use `not_applicable` only when the
reviewed scope has no construct for that category. Use `needs_confirmation`
when constructs exist but dependency, runtime, framework, or deployment
evidence is insufficient.

## Python Static Baseline

Collect the configured baseline before manual findings when possible:

- `pytest` or the repository's test runner
- `mypy`, `pyright`, or another configured type checker
- `ruff`, `flake8`, `pylint`, or another configured linter
- package or lock-file vulnerability/dependency checks when already present

If no configured tool exists, record `baseline_unavailable` and continue
manual review.

## Static Analysis Boundary

Separate static-analysis evidence from reviewer judgment. Static analysis can
usually establish local, source-visible facts such as:

- syntax, import, type, lint, format, and configured test diagnostics
- direct resource lifetime patterns visible in source
- broad exception handlers and default-return branches visible in source
- obvious async misuse, un-awaited coroutine/task candidates, and blocking
  calls in visibly async paths
- dependency declarations, lock-file versions, and configured package metadata
- schema/model options and serializer settings visible in code or config
- hardcoded time, locale, encoding, retry, timeout, and batch-size values

Static analysis usually cannot prove the following without additional evidence:

- actual runtime framework registration, decorator consumption, plugin loading,
  dependency-injection wiring, or import-discovery order
- production volume, backlog size, concurrency, timing, timeout, retry, and
  deployment limits
- whether a default value is business-approved or invented by code
- whether a fallback path is acceptable for the real business decision it gates
- third-party API behavior not visible in the referenced package version
- lifecycle/support status that depends on current external release policy
- whether telemetry, trace ids, or source identities are sufficient for
  operations, audit, or handoff in the deployed environment

When static evidence is insufficient, do not convert the category to `pass`.
Record `needs_confirmation` in the finding or matrix row, name the missing
evidence, and mirror closure-affecting items as `unknown` concerns in the Skill
run log.

## Resource Efficiency Checks

For Python, also check:

- unbounded materialization of generators, query results, files, or responses
- repeated serialization, regex compilation, connection creation, or model
  loading in hot paths
- file, socket, subprocess, cursor, and client lifetimes without context
  managers or explicit cleanup
- accidental quadratic behavior from nested loops, list membership, repeated
  concatenation, or repeated DataFrame transformations
- large in-memory buffering where streaming or bounded batches are required

## Operational Resilience Checks

For Python, also check:

- per-item creation of HTTP clients, database engines, pools, sessions,
  subprocesses, browser drivers, ML models, or event loops
- retry loops without jitter, budget, deadline, or idempotency guard
- queue, file, ETL, scrape, or batch workers without leases, atomic claims,
  bounded batch size, dead-letter handling, or source identity preservation
- multiprocessing, thread-pool, async task, and worker-pool paths where failure
  or cancellation can orphan work
- dependency or import-time side effects that can break process startup,
  test isolation, server reload, or worker fork behavior

## Synchronization And Concurrency Checks

For Python, also check:

- blocking I/O or CPU-heavy work inside `async` event-loop paths
- `asyncio.create_task` or background tasks without ownership, cancellation,
  exception observation, or shutdown join
- thread, process, or coroutine shared state without a clear owner or lock
- use of non-thread-safe clients, sessions, connections, or caches across
  threads or processes
- polling-only wait loops that cannot wake from the state transition they are
  waiting for

## Required Business Input Integrity Checks

For Python, common silent fallback forms include:

- `dict.get(..., default)` for required values
- `or` fallback that treats valid falsey values as missing
- broad `except` returning `None`, `False`, `0`, empty strings, or empty
  collections
- optional config, environment variable, cache, API, message, or file values
  converted into invented defaults

Distinguish explicitly configured defaults from values invented by code.

## Error Handling And Exception Path Checks

For Python, also check:

- bare `except` or broad `except Exception` that suppresses, converts, or logs
  and continues after decision-critical failure
- `finally` or context-manager gaps that skip cleanup, rollback, ack/nack,
  quarantine, or failure-state recording
- task, callback, thread, process, or subprocess failures that are never
  awaited, joined, inspected, or propagated
- retries around non-idempotent operations without an operation identity
- exception wrapping that loses source, payload, attempt, or correlation
  evidence needed for diagnosis

## Time, Locale, And Encoding Checks

For Python, also check:

- naive and timezone-aware `datetime` mixing
- local-time arithmetic across persistence, scheduling, retention, or protocol
  boundaries
- locale-sensitive parsing/formatting where invariant or explicit locale is
  required
- implicit text encodings for files, subprocess output, HTTP payloads, CSV,
  JSON lines, or logs where deployment defaults can differ

## State And Determinism Boundary Checks

For Python, also check:

- module-level mutable state, singleton clients, caches, monkey patches, random
  seeds, environment mutation, and global logging configuration
- hidden side effects at import time
- mutable default arguments and shared class-level mutable values
- retry, replay, duplicate-message, worker-restart, or test-order paths where
  non-idempotent state transitions can repeat silently

## Uncertainty And Escalation Path Checks

Apply [Common source analysis criteria](../source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001)
for language-neutral uncertainty and escalation path review.

For Python, also check:

- `dict.get`, `os.getenv`, falsey-value fallbacks, `int`/`float` conversion,
  regular-expression matching, parsers, and classifiers whose missing, invalid,
  no-match, or low-confidence result becomes a normal default, empty
  collection, or `None` without an explicit controlled disposition
- `Optional`/`Union` values, dataclass defaults, and Pydantic defaults that
  turn an unresolved or unsupported value into a valid-looking value and allow
  it to propagate past the decision boundary
- LLM, external API, rule-engine, classifier, or model outputs represented as
  plain dictionaries, dataclasses, or Pydantic models without a confidence,
  status, and unsupported-value disposition when a downstream decision depends
  on the result
- parse, classification, schema-conversion, or model-output paths that use
  bare `except`, `except Exception: return None`, or equivalent exception-to-
  default handling instead of rejection, retry, quarantine,
  `needs_confirmation`, or an explicit handoff

## Contract And Schema Resilience Checks

For Python, also check:

- Pydantic, dataclass, attrs, marshmallow, Django/DRF, FastAPI, JSON, YAML,
  CSV, protobuf, or custom mapping behavior for unknown fields, missing fields,
  enum expansion, nullability, coercion, and version metadata
- permissive parsing or coercion that drops fields required for routing,
  authorization, idempotency, billing, audit, or compliance
- boundary parse failures that crash outside a controlled reject, retry,
  quarantine, unknown, or handoff path

## Traceability And Context Propagation Checks

For Python, also check:

- logging context, trace/span context, request id, tenant/user/source identity,
  attempt count, and source metadata across async tasks, worker queues,
  subprocesses, callbacks, and agent handoffs
- `contextvars`, thread-local state, process-global state, and logging filters
  that leak context across unrelated work
- detached work that loses failure attribution or source identity

## Support Lifecycle Checks

Check at least:

- Python runtime support status
- framework and package support status when a version is visible
- dependency constraints that block supported Python versions

Use current authoritative sources for lifecycle dates; do not rely on memory
for version support windows.

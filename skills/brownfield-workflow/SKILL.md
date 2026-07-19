---
name: brownfield-workflow
description: Structure brownfield change work across requirements, planning, design, manufacturing, and testing by re-organizing upstream items into phase results, decisions, unknowns, evidence, gates, and handoffs. Use when an existing codebase or system must be changed without treating its current implementation as the complete specification.
---
<!-- xid: A17C4E8B2D91 -->
<a id="xid-A17C4E8B2D91"></a>

# Brownfield Workflow

Use this Skill to carry one brownfield change through five connected phases:
requirements, planning, design, manufacturing, and testing.

The central rule is to preserve the upstream item as the traceability anchor.
Do not create a large independent design or task catalogue. Re-organize each
upstream item for the current phase and classify the result as `done`,
`unknown`, or `out_of_scope`.

## Inputs

- user request and change purpose;
- current-system findings, source locations, tests, logs, configuration, and
  database information when available;
- the previous phase's items and decisions;
- constraints, risks, and existing evidence.

If a required input is absent, record an `unknown` with the missing evidence or
decision. Do not infer it from the existing implementation.

## Common item structure

For every phase, maintain a compact management table or equivalent structure:

| Field | Meaning |
|---|---|
| `id` | Stable item identifier |
| `upstream_ref` | Requirement or plan item that this item realizes |
| `target` | Source, DB, API, test, configuration, or operational target |
| `phase_result` | Current phase's concrete result |
| `state` | `done`, `unknown`, or `out_of_scope` |
| `basis` | Evidence, source location, or decision basis |
| `impact` | Downstream effect |
| `next_action` | Confirmation, analysis, implementation, test, or handoff |
| `owner` | Person or role needed for the next decision |

Do not use `unknown` as a bare label. State what is unknown, why it is unknown,
what it affects, and who or what can resolve it.

## Phase workflow

### 1. Requirements

Re-organize the request and current-state evidence into:

- change purpose and expected business result;
- current behavior supported by evidence;
- desired behavior and acceptance conditions;
- in-scope and out-of-scope targets;
- normal, error, boundary, and non-functional requirements;
- assumptions and unresolved decisions.

Keep current behavior, requested change, and assumption separate. The existing
code is evidence of current behavior, not automatically the business
requirement.

Output a requirements summary containing the acceptance conditions and the
unresolved list. Do not approve the final business requirement on behalf of the
responsible human.

### 2. Planning

Re-organize the approved requirements into an executable work plan:

- impacted source, DB, API, batch, configuration, test, and document targets;
- work units, dependencies, execution order, and parallel work;
- source-change, data-change, release, rollback, and compatibility policies;
- risks, unknowns, stop conditions, and phase gates;
- verification approach and evidence-collection method;
- test tools, versions, fixtures, environment, external dependencies, test
  data, cleanup, result storage, and local/CI execution method.

The **work policy is produced in this phase**. Later phases reference it rather
than redefining it. Preparing the test tools and environment belongs to
planning; executing the tests belongs to testing.

Output a planning summary first, followed by the work items and policies.
Include the planning basis and unresolved planning decisions.

### 3. Design

Re-organize each requirements and planning item as an implementation-facing
design item. Cover only the design areas needed by the upstream items:

- current-to-target structural delta;
- component and responsibility changes;
- API, message, DB, and data contracts;
- processing order, state transitions, transactions, idempotency, and
  concurrency;
- error, retry, timeout, compensation, and rollback behavior;
- compatibility, migration, and external-boundary behavior;
- observability and audit evidence;
- design-to-test viewpoints.

For each item, record the design result or an explicit unknown. Do not invent
behavior to make the design appear complete. Preserve the upstream reference,
design basis, affected target, downstream impact, and required decision owner.

Output a concise design summary first. The summary must show:

1. what is decided;
2. what is unknown or awaiting confirmation;
3. what is blocked by that unknown;
4. what must be handed to manufacturing or testing.

Create detailed API, DB, flow, or error artifacts only when they are required
by a traced item. Do not make downstream Skills infer test scope from broad
design prose; provide explicit test handoff rows.

### 4. Manufacturing

Re-organize approved design items into implementation units:

- code changes;
- DB and migration changes;
- configuration and integration changes;
- test additions or updates;
- build, format, static-analysis, and consistency checks.

Implement only items with an approved design basis. If implementation exposes
an unresolved design or requirement decision, stop that item and return it as
`unknown` or `blocked`; do not silently decide it in code.

Output the implementation summary, changed-target map, verification evidence,
and unresolved handoff items.

### 5. Testing

Re-organize the design-to-test handoff and planning test policy into an
executable test set:

- baseline and environment readiness;
- unit, integration, regression, boundary, negative, migration,
  compatibility, retry, idempotency, concurrency, and rollback tests as
  applicable;
- expected result and evidence to collect for each item;
- result classification for failures;
- retest and residual-risk decisions.

Use the planned tools and environment. Record tool versions, test data,
execution context, logs, and raw results. Distinguish a defect, environment
problem, existing failure, and expected change.

Output a test summary first, followed by results and unresolved release
decisions. Do not mark the work complete while acceptance conditions or
release-impacting unknowns remain unclassified.

## Summary-first output contract

Every phase must begin its output with a summary containing:

- phase conclusion;
- unresolved items, ordered by downstream impact;
- blockers and required decisions;
- completed items;
- next handoff;
- links or references to detailed evidence.

The detailed artifacts are evidence and working material. The summary is the
human review entry point.

## Closure and handoff

Before closing a phase:

- trace every in-scope upstream item to a result;
- classify every item as `done`, `unknown`, or `out_of_scope`;
- attach evidence or a decision basis to `done` items;
- give every `unknown` a reason, impact, next action, and owner;
- record the next phase's input package and handoff conditions;
- stop when proceeding would require guessing business behavior, structure,
  compatibility, data handling, or test acceptance.

Do not approve business requirements, design, release, or residual risk unless
the responsible human or governing workflow owns that decision.

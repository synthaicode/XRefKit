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

Use Knowledge- and pattern-first execution. Before each phase judgment, search
relevant `knowledge/` fragments and inspect the current system for an existing
implementation or test pattern. Record whether each change `follows`,
`adapts`, `introduces`, or is `unknown` against that pattern. Existing code
and past Knowledge are evidence and decision aids, not automatic business
truth; deviations require an explicit basis and decision owner.

At the requirements-to-design boundary, resolve two specific Knowledge inputs:
the service catalog identifies which existing service owns the behavior, and
the service-interaction/data-flow record identifies communication and database
propagation. If either is missing or stale, service ownership or flow impact is
`unknown`; do not infer it from a namespace, folder, or one call site.

## Inputs

- user request and change purpose;
- service catalog and service-interaction/data-flow Knowledge;
- existing service catalog, architecture, API, event, ERD, DDL, or data-flow artifacts when available;
- current-system findings, source locations, tests, logs, configuration, and
  database information when available;
- the previous phase's items and decisions;
- constraints, risks, and existing evidence.

If a required input is absent, record an `unknown` with the missing evidence or
 decision. Do not infer it from the existing implementation.

## Knowledge and pattern preflight

At startup and each phase boundary, search applicable Knowledge by XID, verify
its scope and freshness/recheck condition, inspect the target's local pattern,
and record the Knowledge references plus pattern decision in each item. Stop
and mark `unknown` when the missing Knowledge or pattern evidence would force a
guess. Planning must include a phase-by-phase Knowledge reuse plan for design,
manufacturing, and testing. Durable facts belong in `knowledge/`, not in this
procedure.

The planning Knowledge plan must identify the service owner, affected service
flows, communication contracts, database read/write ownership, and downstream
propagation for each in-scope item.

## Importing existing service and flow information

When service or flow information already exists in documents, exports, diagrams,
OpenAPI/AsyncAPI, DDL/ERD, CMDB extracts, code-analysis reports, or other
artifacts, import it before performing new discovery:

1. preserve the original artifact as lower-layer source evidence; if it is an
   external source, follow the source-ingestion policy and retain its locator;
2. search canonical Knowledge by service identity, aliases, database identity,
   endpoint/event names, and flow terms;
3. classify each candidate as `create`, `extend`, `refresh`, `split`,
   `reject_duplicate`, or `proposal_only`;
4. normalize only the reusable service records and flow records into the
   service-catalog and data-flow Knowledge schemas; do not copy the whole source
   document into `knowledge/`;
5. attach source/evidence references, target scope, verification date or
   commit, freshness/recheck condition, coverage, and unresolved conflicts;
6. cross-check communication and DB claims against current source, contracts,
   and DB evidence. Contradictions remain `unknown` or an explicit judgment;
7. update canonical Knowledge and `knowledge/000_index.md` only under an
   authorized `apply` decision. Without that authority, create a reviewable
   `work/` proposal and hand it to `knowledge_ontology_management`.

The import result must record the source artifact, concept decision, resulting
XIDs, facts omitted and why, conflicts, freshness condition, and publication or
handoff status. Existing analysis already containing the required findings is
registered and normalized; it is not re-analyzed from scratch.

### Canonical Knowledge path fast path

When the input points to an existing file under `knowledge/` and that file has
an XID anchor, use the path as a canonical Knowledge reference:

1. normalize and verify that the path is inside `knowledge/`;
2. resolve the file's XID and load it with `python -m xrefkit xref show <XID>`;
3. confirm that the fragment is the intended service catalog or data-flow
   concept and that its applicability and freshness conditions cover the target;
4. record `knowledge_import_results` with `mode: canonical_path_reuse`, the
   supplied path, resolved XID, applicability result, freshness result, and
   any unresolved gap;
5. use the resolved XID directly in `knowledge_refs` and phase decisions. Do
   not copy, re-register, or create a duplicate fragment;
6. if the requested change would alter the fragment's meaning, stop the
   Brownfield item and hand the semantic update to
   `knowledge_ontology_management` as `extend`, `split`, `supersede`, or
   `proposal_only` rather than editing the referenced Knowledge inline.

If the path is under `knowledge/` but has no valid XID, or the XID does not
resolve, classify the input as `unknown` and hand it to Knowledge registration;
do not silently treat the path as canonical.

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
| `knowledge_refs` | XID references to reusable Knowledge used for this item |
| `pattern_decision` | `follows`, `adapts`, `introduces`, or `unknown` |
| `pattern_basis` | Existing target pattern, evidence, delta, and decision owner |
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
The design-to-test handoff must carry the selected service and flow records,
including contract, persistence, compatibility, retry, idempotency, and
rollback viewpoints where applicable.
Use the selected design Knowledge and local pattern result to make the
current-to-target delta explicit. If the design adapts or introduces a pattern,
record why the existing pattern is insufficient and who owns that decision.

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
Implement against the approved pattern decision and Knowledge references. If
hard evidence contradicts the basis, classify the assumption gap and hand the
correction back upstream; do not silently create a new local convention.

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
Start from the test Knowledge and regression patterns selected in planning,
then add change-specific cases for the approved delta. Show which patterns are
reused, adapted, or newly introduced.

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
- attach Knowledge XIDs and a pattern decision/basis to every in-scope item;
- give every `unknown` a reason, impact, next action, and owner;
- record the next phase's input package and handoff conditions;
- stop when proceeding would require guessing business behavior, structure,
  compatibility, data handling, or test acceptance.

Do not approve business requirements, design, release, or residual risk unless
the responsible human or governing workflow owns that decision.
## Reporting Contract (共通報告)



- reporting_profile: phase_summary

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

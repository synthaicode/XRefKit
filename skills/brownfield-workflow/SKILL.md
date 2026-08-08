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

## Scope-adjusted DFD and Entity change mapping

When the brownfield item involves multiple services generating, transforming,
approving, retaining, or consuming data, create a scope-declared DFD view when
it helps a human review the impact. Do not force every detail into one diagram.
Use a hierarchy that can be expanded without changing the meaning of the
parent view:

- `Level 0`: business context, external actors, major processes, and primary
  data outcomes;
- `Level 1`: service-to-service generation, transformation, event/API/file
  propagation, and persistence boundaries;
- `Level 2`: primary Entities, supporting Entities, derived/projection data,
  ownership, and source-of-truth;
- `Level 3`: change points, changed fields, status transitions, human
  approvals, logical deletion, audit history, retry/replay, and downstream
  effects.

Select the lowest level required by the decision: broad impact uses Levels 0-1,
requirements and design use Levels 1-2, and implementation/test impact uses
Levels 2-3. Every view must state `scope`, `included`, `excluded`, `detail_level`,
and `unknowns`, and must retain stable `service_id`, `entity_id`, `flow_id`, and
`change_point_id` links to its evidence.

Treat the Entity lifecycle as a data-flow concern. For each in-scope primary
Entity, map its supporting Entities, generated or derived Entities, producing
service, source-of-truth, permitted writers, and downstream consumers. Record
updates as named change points rather than one generic update arrow, including
the actor, trigger, before/after state, changed fields, business meaning,
evidence, and downstream effect. Model logical deletion as a state transition
and propagation (`active -> logically_deleted -> archived -> purged`) rather
than assuming physical removal.

For important status changes, record the transition owner, human actor where
applicable, approval/rejection evidence, audit record, emitted event, and
allowed downstream processing. Keep business status separate from technical
processing status. If ownership, state transition, retention behavior, or
propagation cannot be established from evidence, record an impact-bearing
`unknown` and its resolver; do not infer it from a call graph or field name.

Use DFD for data movement, Entity/ER views for structure, state diagrams for
lifecycles, and sequence or process views for temporal behavior. Cross-link the
views instead of duplicating untraceable detail. Include the selected DFD and
Entity change rows in the design-to-test handoff so tests cover status,
approval, logical deletion, restoration, replay, and downstream propagation
where applicable.

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

#### Brownfield file editing integrity

When manufacturing edits an existing text file, establish a file-preservation
record before changing it. Do not use a text API that silently applies the
platform default encoding, BOM policy, or universal-newline translation.

The pre-edit record must contain the confirmed original character encoding and
identification basis, BOM presence and exact BOM bytes, the original newline
convention (`LF`, `CRLF`, `CR`, or `mixed`), the original file bytes or a
cryptographic hash with retained byte evidence, and the exact Unicode string
obtained by strict decoding with the original encoding after BOM handling.

Edit the decoded Unicode string while preserving the recorded encoding, BOM,
and newline policy. Disable universal-newline translation. Ambiguous encoding,
undecodable bytes, or a requested policy change is `unknown` and requires an
owner decision; do not guess.

After saving, read raw bytes and require: exact BOM preservation; strict
decoding with the original encoding; unchanged newline convention; unchanged
Unicode strings outside approved change spans; strict re-encoding of the full
edited Unicode string with the original encoding and BOM policy; and exact
equality between those re-encoded bytes and the saved bytes.

The key round-trip assertion is:

```text
after_bytes == after_bytes.decode(original_encoding, strict).encode(original_encoding, strict)
```

Apply BOM handling consistently around this assertion. It proves encoding
validity, not absence of pre-existing mojibake. Detect mojibake introduced by
the edit by strictly decoding both versions with the original encoding and
comparing Unicode sequences, permitting differences only in approved spans.
The handoff must include the pre-edit record, hashes or byte evidence,
post-edit verification, BOM/newline results, approved spans, Unicode diff, and
any residual detection limitation.

#### Human/AI concurrent-edit guard

The pre-edit byte hash is also a concurrency revision token. A text read is
not permission to write indefinitely. Immediately before writing, read the
file again as raw bytes and compare its exact bytes (or a cryptographic hash)
with the pre-edit revision token. If they differ, another actor—including a
human or another AI operation—has edited the file. Abort the write, preserve
the current file, and classify the item as `unknown` or `blocked` pending a
fresh read and rebase of the intended change. Never write the previously
prepared content over the changed file.

The write path must be a compare-and-swap sequence:

```text
before = read_bytes(path)
plan = edit(strict_decode(before, original_encoding))
current = read_bytes(path)
if current != before:
    abort_without_write()
else:
    atomically_replace(path, encode_with_original_policy(plan))
```

Use an atomic temporary-file replacement only after the revision check passes,
and run the post-write byte/Unicode verification against the replacement. A
process lock may reduce simultaneous writes, but it does not replace the
revision check because it cannot detect edits made by tools outside the lock.
If the file is deleted, replaced, renamed, or its metadata indicates a
different target before the write, treat that as a conflict and abort as well.

#### Specification-alignment guard

Byte-level concurrency checks cannot detect an edit based on the wrong
understanding of the specification. Treat the AI's current understanding as a
hypothesis, never as authoritative fact. Before preparing file content, record
a semantic edit contract containing the requested outcome, authoritative
source or decision owner, exact intended changes, protected invariants and
out-of-scope text, and acceptance checks. Separate repository facts, user
decisions, inferences, and unresolved assumptions.

Compare that contract with the current authoritative specification, applicable
Knowledge, local pattern, and relevant tests or schemas. If the sources
conflict, the requested behavior is ambiguous, or a required source is missing
or stale, do not prepare a write. Stop as `unknown` or escalate for a human
decision. A syntactically valid edit, a successful encoding round trip, or a
passing narrow test does not authorize a semantically unsupported change.

Before atomic replacement, verify both gates:

```text
semantic_alignment == confirmed
and current_bytes == pre_edit_revision
```

After replacement, verify the acceptance checks and re-check protected
invariants. If semantic verification fails, stop the item, retain the saved
bytes for diagnosis, and do not make a compensating edit based on the same
unconfirmed interpretation. Re-read the authoritative source and obtain a new
decision or rebase the change.

#### Historical conflict investigation

When specification alignment is not confirmed, investigate the conflict's
history before requesting a decision. Use a bounded time window anchored to
known revisions—for example, the last confirmed-good revision through the
current revision—not an arbitrary broad history scan. If the repository is
under Git, inspect the relevant file history, commit diffs, rename-following
history, and line attribution (`log`, `show`, `diff`, `blame`) for that window.
Include uncommitted state in the investigation; committed history cannot prove
that a current human edit did not happen after the last commit.

Record whether the conflict appears to have been introduced by a requirement
change, implementation change, generated-file refresh, merge/rebase, manual
edit, or an unresolved pre-existing discrepancy. Record commit IDs, authors,
timestamps, affected lines, and links to the authoritative decision where
available. Treat commit message text, author identity, file timestamps, and
code history as evidence only; none overrides an explicit current requirement
or decision owner.

If the conflict cannot be resolved from the bounded history and authoritative
sources, keep the write blocked. Do not select the newest commit merely because
it is newest, and do not infer intent from a timestamp alone. For untracked or
non-Git files, use the available audit/version history; if none exists, record
the absence as an evidence gap and escalate.

#### Uncommitted-file policy

Treat uncommitted worktree changes and untracked files as protected current
state. Before editing, inspect the target's worktree state and diff, including
untracked-file status where applicable. A clean repository history is not a
clean target state. Never use reset, checkout, clean, stash, or a broad restore
operation to make the target appear clean unless that exact action is explicitly
authorized.

Classify the worktree state before writing:

- `pre_existing_human_or_unknown`: preserve it, do not overwrite it, and stop
  for ownership or merge direction when the intended change overlaps it;
- `ai_owned_current_work`: continue only with the same work-unit identity,
  unchanged revision token, and confirmed semantic alignment;
- `non_overlapping_changes`: preserve the unrelated hunks and apply only the
  approved target change;
- `mixed_or_overlapping`: create a reviewable three-way merge or patch proposal
  without modifying the source, then obtain a decision before writing.

If ownership cannot be established, classify the state as
`pre_existing_human_or_unknown`. Do not infer ownership from file timestamps,
editor names, or the fact that the current process can write the file. After a
permitted write, re-check `status` and the target diff and record which hunks
were preserved, changed, or left unresolved.

#### New-file extension conformity

When adding a file, do not treat the extension as a complete specification.
Use it to select existing-file peers and extract code-writing rules from them.
Group peers by a coherent scope such as the same folder, package, module, or
responsibility boundary. Within each scope, cluster observed rules and select
the rule followed by the majority of representative files. Prefer the nearest
coherent scope in this order: same directory, same package/module subtree,
nearest owning component, then repository-wide fallback. Do not let a
repository-wide majority override a clear local folder rule.

Record the peer paths, scope, observed rule signatures, file counts per rule,
selected majority, and confidence. A majority is usable only when the files are
representative and the margin is meaningful; a tie, weak margin, or multiple
equally coherent scopes is an unresolved pattern conflict and requires a
decision. Never use one arbitrary example as the rule.

Before creating the file, compare peer conventions for filename and placement,
encoding/BOM/newline, headers and metadata, formatting and trailing newline,
import/include order, declaration structure, schema/API/configuration/test
layout, and required companion files, registration, indexes, or build tooling.
State which conventions the new file follows, adapts, or introduces, with
evidence and an owner for each deviation.

Validate the parent directory/worktree revision immediately before creation so
that a human or another AI cannot add a same-named or companion file unnoticed.
Create atomically, then run the extension-specific parser, formatter, linter,
schema check, or test where available. If reliable peers are absent, peers
disagree without a decision, the extension is new, or required registration is
unknown, stop as `unknown` or create a proposal. Do not invent a convention
merely because the file parses.

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

# Brownfield Workflow

Carry one brownfield change through requirements, planning, design,
manufacturing, and testing. Preserve the upstream item as the traceability
anchor; do not create an independent task catalogue.

Use a Knowledge- and pattern-first loop: search applicable repository Knowledge
before each phase judgment, compare the change with the target's existing
patterns, and record `follows`, `adapts`, `introduces`, or `unknown`. Knowledge
and existing implementation are evidence, not automatic business truth.

Before requirements become design, resolve the service catalog record for the
responsible existing service and the service-interaction/data-flow records for
communication and database propagation. Missing or stale ownership, contract,
or flow evidence is `unknown`; do not infer it from a namespace, folder, or one
call site.

For every phase, return a summary first containing the conclusion, unresolved
items ordered by downstream impact, blockers, completed items, next handoff,
and references to detailed evidence.

Maintain each item with:

- stable `id`;
- `upstream_ref`;
- target;
- current phase result;
- state: `done`, `unknown`, or `out_of_scope`;
- evidence or decision basis;
- `knowledge_refs` (XID references used for the item);
- `pattern_decision` and `pattern_basis`;
- `knowledge_import_results` when an existing catalog or flow artifact was supplied;
- downstream impact;
- next action and owner.

Do not use `unknown` as a bare label. State what is unknown, why it is unknown,
what it affects, and who or what can resolve it. Do not infer missing behavior
from the existing implementation; existing code is evidence of current
behavior, not automatically the business requirement.

Planning must produce a phase-by-phase Knowledge reuse plan covering design,
manufacturing, and testing. Verify each Knowledge fragment's applicability and
freshness/recheck condition. If an applicable existing pattern cannot be
followed, record the deviation, rationale, evidence, and decision owner before
handing the item onward.

The plan must identify service ownership, affected flows, communication
contracts, database read/write ownership, and downstream propagation for each
in-scope item.

## Scope-adjusted DFD and Entity change mapping

When multiple services generate, transform, approve, retain, or consume the
same data, create a scope-declared DFD view when it helps human review. Keep
the view hierarchical: `Level 0` for business context, `Level 1` for service
flows and persistence, `Level 2` for primary/supporting/derived Entities and
ownership, and `Level 3` for change points, status transitions, approvals,
logical deletion, audit, retry/replay, and downstream effects.

Choose the lowest level required by the decision and declare `scope`,
`included`, `excluded`, `detail_level`, and `unknowns`. Preserve stable
`service_id`, `entity_id`, `flow_id`, and `change_point_id` links. Map each
primary Entity's supporting and derived Entities, producing service,
source-of-truth, permitted writers, and consumers. Replace generic update
arrows with named change points carrying actor, trigger, before/after state,
changed fields, business meaning, evidence, and downstream effect.

Model logical deletion as lifecycle and propagation, not disappearance:
`active -> logically_deleted -> archived -> purged`. For important status
changes, record transition owner, human actor, approval/rejection evidence,
audit record, emitted event, and allowed downstream processing. Keep business
status distinct from technical processing status. If ownership, transition,
retention, or propagation is not evidenced, record an impact-bearing `unknown`
and resolver. Use DFD for movement, ER/Entity views for structure, state views
for lifecycle, and sequence/process views for timing; cross-link them in the
design-to-test handoff.

When these records already exist in documents, exports, diagrams, OpenAPI/
AsyncAPI, DDL/ERD, CMDB extracts, or analysis reports, import them before new
discovery. Preserve the original source, search canonical XIDs, classify each
concept as `create`, `extend`, `refresh`, `split`, `reject_duplicate`, or
`proposal_only`, normalize into the two Knowledge schemas, attach evidence and
freshness, and record conflicts. Apply canonical changes only when authorized;
otherwise hand a `work/` proposal to `knowledge_ontology_management`.

If the supplied input is already an XID-bearing file under `knowledge/`, use
the canonical path fast path: verify the path boundary, resolve the XID with
`xref show`, confirm applicability and freshness, record
`mode: canonical_path_reuse`, and use that XID directly. Do not duplicate or
re-register the fragment. Semantic changes go to
`knowledge_ontology_management`; an invalid or XID-less path remains unknown.

## Requirements

Re-organize the request and current-state evidence into purpose, current
behavior, desired behavior, acceptance conditions, scope, normal/error/boundary
conditions, non-functional requirements, assumptions, and unresolved decisions.
Do not approve human-owned business requirements.

## Planning

Re-organize approved requirements into impacted targets, work units,
dependencies, execution order, compatibility/data/release/rollback policies,
risks, stop conditions, phase gates, and verification evidence. Produce the
work policy here. Include test tools, versions, fixtures, environment,
dependencies, test data, cleanup, result storage, and local/CI execution. Test
tool preparation belongs to planning; test execution belongs to testing.

## Design

Re-organize each requirements and planning item into only the required design
areas: current-to-target delta, component responsibility, API/message/DB/data
contracts, processing order and state, transaction/idempotency/concurrency,
error/retry/timeout/rollback behavior, compatibility/migration, observability,
and design-to-test handoff. Output decisions and explicit unknowns. Create
detailed artifacts only for traced items; do not make testing infer scope from
broad prose.

Use the selected design Knowledge and pattern-conformity result to make the
delta explicit. An `adapts` or `introduces` decision requires an explicit basis
and owner; it is not implementation freedom.

## Manufacturing

Re-organize approved design items into implementation units for code, DB,
migrations, configuration, integrations, tests, and build/static checks. If
implementation exposes an unresolved requirement or design decision, stop that
item and return it as `unknown` or `blocked`; do not decide silently in code.

Implement only against the approved Knowledge and pattern basis. If hard
evidence refutes that basis, record the assumption gap and correction handoff.

### Brownfield file editing integrity

For an existing text file, record before editing: the confirmed original
encoding and identification basis, BOM presence and exact BOM bytes, newline
convention (`LF`, `CRLF`, `CR`, or `mixed`), original bytes or a cryptographic
hash with retained byte evidence, and the exact Unicode string from strict
decoding with the original encoding after BOM handling.

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

### Human/AI concurrent-edit guard

Treat the pre-edit byte hash as a concurrency revision token. Immediately
before writing, read the file again as raw bytes and compare its exact bytes or
cryptographic hash with that token. If they differ, another actor—human or AI—
has edited the file. Abort without writing, preserve the current file, and
classify the item as `unknown` or `blocked` until the current content is read
again and the intended change is rebased. Never overwrite the changed file
with previously prepared content.

The write path is compare-and-swap:

```text
before = read_bytes(path)
plan = edit(strict_decode(before, original_encoding))
current = read_bytes(path)
if current != before:
    abort_without_write()
else:
    atomically_replace(path, encode_with_original_policy(plan))
```

Use atomic temporary-file replacement only after the revision check passes,
then run post-write byte/Unicode verification. A process lock can reduce
simultaneous writes but cannot replace the revision check, because edits from
tools outside the lock remain possible. Deletion, replacement, rename, or a
different target identity before writing is also a conflict and must abort.

### Specification-alignment guard

Byte-level concurrency checks cannot detect a change based on the wrong
understanding of the specification. Treat the AI's understanding as a
hypothesis, not authority. Before preparing content, record a semantic edit
contract with the requested outcome, authoritative source or decision owner,
intended changes, protected invariants, out-of-scope text, and acceptance
checks. Separate repository facts, user decisions, inferences, and unresolved
assumptions.

Compare the contract with current authoritative specifications, applicable
Knowledge, local patterns, and relevant tests or schemas. If sources conflict,
behavior is ambiguous, or required evidence is missing or stale, do not prepare
a write. Stop as `unknown` or escalate for a human decision. Valid encoding,
successful round-trip verification, or a narrow passing test does not authorize
a semantically unsupported edit.

Atomic replacement requires both gates:

```text
semantic_alignment == confirmed
and current_bytes == pre_edit_revision
```

After replacement, verify acceptance checks and protected invariants. If
semantic verification fails, retain the saved bytes for diagnosis, stop, and
re-read the authoritative source before any further edit.

### Historical conflict investigation

When specification alignment is not confirmed, investigate the conflict before
requesting a decision. Use a bounded window anchored to known revisions, such
as the last confirmed-good revision through the current revision. In Git,
inspect relevant file history, commit diffs, rename-following history, and
line attribution (`log`, `show`, `diff`, `blame`) for that window. Include
uncommitted state; committed history cannot prove that a current human edit did
not occur after the last commit.

Record whether the conflict appears to come from a requirement change,
implementation change, generated-file refresh, merge/rebase, manual edit, or
an unresolved pre-existing discrepancy. Record commit IDs, authors, timestamps,
affected lines, and authoritative decision links where available. Commit
messages, author identity, file timestamps, and code history are evidence only;
none overrides a current explicit requirement or decision owner.

If bounded history and authoritative sources do not resolve the conflict, keep
the write blocked. Do not choose the newest commit merely because it is newest,
or infer intent from a timestamp alone. For non-Git files, use available audit
or version history; if none exists, record the evidence gap and escalate.

### Uncommitted-file policy

Treat uncommitted worktree changes and untracked files as protected current
state. Before editing, inspect the target's worktree status and diff, including
untracked-file status. Clean commit history does not mean the target is clean.
Never reset, checkout, clean, stash, or broadly restore the target to make it
appear clean unless explicitly authorized.

Classify the state before writing as one of:

- `pre_existing_human_or_unknown`: preserve it and stop when the intended edit
  overlaps it;
- `ai_owned_current_work`: continue only with the same work-unit identity,
  unchanged revision token, and confirmed semantic alignment;
- `non_overlapping_changes`: preserve unrelated hunks and apply only the
  approved target change;
- `mixed_or_overlapping`: create a reviewable three-way merge or patch proposal
  without modifying the source, then obtain a decision.

If ownership is unknown, use `pre_existing_human_or_unknown`. Do not infer it
from timestamps, editor names, or write access. After a permitted write,
re-check worktree status and the target diff, recording preserved, changed, and
unresolved hunks.

### New-file extension conformity

When adding a file, use the extension to select existing-file peers and extract
code-writing rules from them. Group peers by a coherent scope such as the same
folder, package, module, or responsibility boundary. Within each scope, cluster
observed rules and select the rule followed by the majority of representative
files. Prefer scopes in this order: same directory, same package/module
subtree, nearest owning component, then repository-wide fallback. A broad
majority must not override a clear local folder rule.

Record peer paths, scope, observed rule signatures, file counts per rule,
selected majority, and confidence. A tie, weak margin, or equally coherent
scopes is an unresolved pattern conflict and requires a decision. Never use one
arbitrary example as the rule.

Compare peers before creation for filename and placement, encoding/BOM/newline,
headers and metadata, formatting and trailing newline, import/include order,
declaration structure, schema/API/configuration/test layout, and required
companion files or registration. State which conventions the new file follows,
adapts, or introduces, with evidence and an owner for deviations.

Check the parent directory/worktree revision immediately before creation so a
same-named or companion file added by a human or another AI is detected. Create
atomically and run the available extension-specific parser, formatter, linter,
schema check, or test. If reliable peers are absent, peers conflict without a
decision, the extension is new, or registration is unknown, stop as `unknown`
or create a proposal. Do not invent a convention merely because the file parses.

## Testing

Re-organize the design-to-test handoff and planned test policy into executable
tests. Cover applicable baseline, unit, integration, regression, boundary,
negative, migration, compatibility, retry, idempotency, concurrency, and
rollback cases. Record tool versions, context, test data, logs, raw results,
failure classification, retest, and residual risk.

## Closure

Trace every in-scope upstream item to a result. Classify every item, attach
evidence to completed items, give every unknown a reason/impact/action/owner,
and record the next phase's input package and handoff conditions. Stop when
proceeding would require guessing business behavior, structure,
compatibility, data handling, or test acceptance.

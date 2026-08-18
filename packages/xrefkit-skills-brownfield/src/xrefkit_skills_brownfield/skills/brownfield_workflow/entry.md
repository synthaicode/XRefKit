# Brownfield Workflow

Carry one brownfield change through requirements, planning, design,
manufacturing, and testing. Preserve the upstream item as the traceability
anchor and do not create untraced work.

Use Knowledge- and pattern-first execution. Search applicable Knowledge before
each phase judgment, compare the change with the existing pattern, and record
`follows`, `adapts`, `introduces`, or `unknown`. Existing implementation and
Knowledge are evidence, not automatic business truth.

Before requirements become design, resolve service ownership and the
service-interaction/data-flow records for communication and database
propagation. Missing or stale evidence is an impact-bearing `unknown`.

Maintain each item with stable `id`, `upstream_ref`, `target`, phase result,
state, evidence/decision basis, `knowledge_refs`, `pattern_decision`,
`pattern_basis`, impact, next action, and owner. Do not use `unknown` as a bare
label.

Load the detailed procedure only when needed:

- `references/phase-workflow.md`
- `references/requirements-validation.md`
- `references/specification-reconciliation.md`
- `references/delta-detail-planning.md`
- `references/ipa-reconstruction-guide-mapping.md`
- `references/service-data-impact.md`
- `references/file-edit-integrity.md`
- `references/change-test-suite.md`
- `references/testability-and-case-generation.md`
- `references/reporting-and-closure.md`

The test procedure must declare investigation scope, existing-data investigation
method, white-box structure-to-test mapping, pre-change test suite,
change-impact selection, testability input completeness, AI-generated case
candidates, definition gaps, post-change comparison, and overview/detail
evidence. Tool preparation and the testability gate belong in planning/design;
test execution belongs in testing. Do not generate a case by guessing a missing
input, expected result, business rule, or evidence source.

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

After saving, read raw bytes and require exact BOM preservation, strict
decoding with the original encoding, unchanged newline convention, unchanged
Unicode strings outside approved change spans, strict re-encoding with the
original encoding and BOM policy, and exact equality between those re-encoded
bytes and the saved bytes.

The key round-trip assertion is:

```text
after_bytes == after_bytes.decode(original_encoding, strict).encode(original_encoding, strict)
```

This proves encoding validity, not absence of pre-existing mojibake. Detect
mojibake introduced by the edit by strictly decoding both versions and
comparing Unicode sequences, permitting differences only in approved spans.
The handoff includes the pre-edit record, hashes or byte evidence,
post-edit verification, BOM/newline results, approved spans, Unicode diff, and
any residual detection limitation.

### Human/AI concurrent-edit guard

Treat the pre-edit byte hash as a concurrency revision token. Immediately
before writing, read the file again as raw bytes and compare its exact bytes or
cryptographic hash with that token. If they differ, another actor—human or
AI—has edited the file. Abort without writing, preserve the current file, and
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
untracked-file status. Clean commit history does not mean that the target is
clean. Never reset, checkout, clean, stash, or broadly restore the target to
make it appear clean unless explicitly authorized.

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

## Phase-based use

Route the request to one phase and carry forward the same upstream reference,
evidence, unknowns, owners, and decisions:

- `requirements`: current/desired behavior, acceptance, scope, and decisions;
- `planning`: impact scope, dependencies, tools, data, fixtures, gates, and
  handoff;
- `design`: traced structural delta, contracts, and testability/case-definition
  check;
- `manufacturing`: approved implementation with file and concurrency integrity;
- `testing`: approved suite execution, evidence, pre/post comparison, and
  residual risk;
- `closure`: upstream trace, unknown classification, decisions, and handoff.

If the phase is not stated, infer it only from the requested deliverable and
make the selected phase explicit in the summary. Stop when the phase requires
an unresolved business, design, data, expected-result, or ownership decision.

When an existing Requirement is supplied, validate its source, version,
authority, owner, freshness, consistency with current evidence, and
testability before using it as a design or test basis. Do not silently rewrite
or approve it.

In `design`, reconcile the current specification, evidenced current behavior,
and validated new requirement. Record the delta class, protected invariants,
compatibility/downstream impact, test impact, owner, and human decision before
approving the design delta.

After reconciliation, refine the initial work policy from the approved delta
before manufacturing or test-case approval. Recalculate work units, data,
compatibility, rollback, evidence, test, gates, owners, and handoffs; do not
treat the Requirement-only plan as final.

Every phase starts with a summary containing conclusion, downstream-ordered
unknowns, blockers, completed items, next handoff, and evidence links. Before
closure, trace every upstream item, attach evidence and Knowledge/pattern
basis, give each unknown a resolver and owner, and stop when proceeding would
require guessing.

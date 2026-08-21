<!-- xid: 9F4C2A7D1B60 -->
<a id="xid-9F4C2A7D1B60"></a>

# Instruction-Backed Workflow Protocol

XRefKit v0.4.3 extends the workflow protocol to instructions that do not have
an applicable Skill. This does not make the instruction an implicit Skill and
does not make the protocol responsible for judging output quality.

When an ordinary Skill document exists but is not an XRefKit-managed Skill,
use the parallel [`general_skill` work type](092_general_skill_workflow_protocol.md#xid-4D8A6C2F1B90).
It preserves the same protocol gates while keeping source procedure,
XRefKit-managed Skill identity, and governance evidence separate.

## Start Gate

Start an instruction-backed run with:

```powershell
xrefkit workflow run --task "..." --completion-condition "..." --json
```

If the instruction has no completion condition, the command stops. The caller
must either provide one or explicitly select the repository defaults:

```powershell
xrefkit workflow run --task "..." --use-default-completion-conditions --json
```

The run log records whether the completion basis was `explicit` or `default`.

## Procedural Completion

The default conditions are:

- all concrete work items are done or escalated;
- an output artifact and an evidence artifact are recorded;
- unknowns and risks are resolved or escalated; and
- execution, check, and handoff phases are complete or escalated.

The existing workflow commands update and verify the run log:

```powershell
xrefkit skill workitem ...
xrefkit skill artifact ...
xrefkit skill phase ...
xrefkit skill verify --log <run-log>
xrefkit skill close --log <run-log>
```

For a Prompt Flow with delegated child Skill Runs, reconcile the parent before
advancing its check phase and applying the existing closure gate:

```powershell
xrefkit workflow reconcile --log <parent-run-log> [--apply-child-status]
xrefkit skill verify --log <parent-run-log>
xrefkit skill close --log <parent-run-log>
```

`workflow reconcile` checks the recorded parent-child correlation, delegated
child closure state, delegated child output/evidence/artifact/concern records,
parent output/evidence/artifact/concern records, and parent work-item
completion. By default it only
reports findings. `--apply-child-status` explicitly reflects a closed child
(`done` or `escalated`) onto its linked parent work item; it does not execute
the child, perform recovery, or close the parent.

When a parent has delegated child runs, `skill close --log <parent-run-log>`
also requires a passing reconcile recorded after the latest child delegation
and parent work-item update. This prevents a stale reconcile result from being
used as the parent closure basis.

The main AI records semantic routing on the generic parent Flow before it
delegates a Work Item or continues with generic work:

```powershell
xrefkit workflow routing `
  --log <parent-run-log> `
  --selected-skill <skill-id> `
  --candidate <skill-id> `
  --reason "The Work Item matches the Skill responsibility" `
  --target-work-item WI-001
```

For a generic fallback, omit `--selected-skill` and use
`--selection-mode fallback`. When semantic routing is uncertain, omit
`--selected-skill`, use `--selection-mode needs_clarification`, and record the
human decision requirement. This command records and validates the main AI's
decision; it does not perform hidden semantic selection or start a child run.
The subsequent `workflow delegate` action remains explicit and work-item
scoped.

Recovery proposals must remain bounded and human-controlled. Record the
executable action, owner, verification method, maximum attempts, and stop
conditions together with the resume location and reason:

```powershell
xrefkit workflow recovery `
  --log <run-log> `
  --recovery-id REC-001 `
  --status proposed `
  --resume-location "WI-001 checkpoint" `
  --reason "The previous executor stopped before verification" `
  --next-action "Run the recorded verification command" `
  --executable-action "Run verification command once" `
  --owner recovery-owner `
  --verification-method "Verify the recorded check passes" `
  --maximum-attempts 2 `
  --stop-condition "Stop after two failed attempts"
```

The dashboard records this proposal and its later human confirmation. It does
not execute the action or create an unbounded retry loop.

Continuation keeps the original `flow_id` and `root_run_id` and records the
prior run as `parent_run_id`. A changed outcome or scope creates a new Work
Item with `--supersedes`; unrelated work starts a new Flow instead of reusing
the prior correlation:

```powershell
xrefkit workflow run --task "Continue the same prompt flow" `
  --flow-id FLOW-001 --root-run-id <root-run-id> `
  --parent-run-id <prior-run-id> --work-item-id WI-001

xrefkit skill workitem --log <run-log> --item WI-002 --supersedes WI-001 `
  --text "Revised scope" --completion-criterion "The revised scope is recorded" `
  --status pending --role instruction:executor
```

These commands verify process records. They do not inspect the content of the
output artifact.

When the main AI selects an existing Skill for a Work Item's quality review,
it may record the selection and start the child review run together:

```powershell
xrefkit workflow quality-review `
  --parent-log <parent-run-log> `
  --root . `
  --meta skills/<review-skill>/meta.md `
  --selected-skill <review-skill-id> `
  --candidate <review-skill-id> `
  --reason "The Work Item output requires this existing review capability" `
  --task "Review the Work Item output" `
  --work-item-id WI-001
```

This command does not perform semantic selection. The selected Skill and
reason must come from the main AI. If selection is uncertain, record
`needs_clarification` instead and do not start the child review.

Every work item must also declare its own procedural completion criterion:

```powershell
xrefkit skill workitem --log <run-log> --item WI-001 `
  --text "Update the document" `
  --completion-criterion "The document is updated and xref check passes" `
  --status pending --role instruction:executor
```

If the criterion cannot yet be defined, do not invent one. Register the item
as `unknown`, `blocked`, or `escalated` and provide
`--criterion-unknown-reason`. Such an item cannot be treated as normally done
until the uncertainty is resolved or explicitly handed off.

After creation, a completion criterion is immutable. If the required outcome
changes, create a new item and link it to the previous item:

```powershell
xrefkit skill workitem --log <run-log> --item WI-002 `
  --supersedes WI-001 `
  --text "Apply the revised requirement" `
  --completion-criterion "The revised requirement is implemented and verified" `
  --status pending --role instruction:executor
```

Updating `WI-001` with a different criterion is rejected. `verify` also checks
that every `supersedes` reference points to an existing work item.

## Human Output Acceptance

Output quality is a separate human decision. Record it after review:

```powershell
xrefkit skill feedback --log <run-log> --kind human \
  --status accepted --target OUT-001 --note "accepted by reviewer"
```

An accepted output does not replace procedural verification, and procedural
closure does not claim that the output is semantically correct. The two facts
remain separately auditable.

## Optional Run-Boundary Human Evaluation

Handoff always returns control to the human; it does not wait for an evaluation.
When the human issues a subsequent request, they may optionally connect it to
the preceding run:

```powershell
xrefkit skill evaluate --log <run-log> `
  --decision accepted `
  --classification continuation `
  --next-handling continue_next_step `
  --purpose-fit "The requested purpose remains valid" `
  --verified "OUT-001 and EVD-001" `
  --uncertainty "none"
```

The human-confirmed classification can be `continuation`, `correction`,
`scope_change`, `new_work`, or `needs_clarification`. An AI may propose a
classification for the next request, but it cannot confirm it on the human's
behalf. The record is optional and does not block a normal low-risk
continuation. Use scoped findings for multi-target runs. If evidence or
criteria are not versioned or snapshotted, record a comparability gap rather
than attributing differences to the target object.

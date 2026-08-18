<!-- xid: 9F4C2A7D1B60 -->
<a id="xid-9F4C2A7D1B60"></a>

# Instruction-Backed Workflow Protocol

XRefKit v0.4.3 extends the workflow protocol to instructions that do not have
an applicable Skill. This does not make the instruction an implicit Skill and
does not make the protocol responsible for judging output quality.

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

These commands verify process records. They do not inspect the content of the
output artifact.

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

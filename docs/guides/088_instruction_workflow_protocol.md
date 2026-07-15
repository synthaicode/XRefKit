<!-- xid: 9F4C2A7D1B60 -->
<a id="xid-9F4C2A7D1B60"></a>

# Instruction-Backed Workflow Protocol

XRefKit v0.4.1 extends the workflow protocol to instructions that do not have
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

## Human Output Acceptance

Output quality is a separate human decision. Record it after review:

```powershell
xrefkit skill feedback --log <run-log> --kind human \
  --status accepted --target OUT-001 --note "accepted by reviewer"
```

An accepted output does not replace procedural verification, and procedural
closure does not claim that the output is semantically correct. The two facts
remain separately auditable.

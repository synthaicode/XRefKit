<!-- xid: 4D8A6C2F1B90 -->
<a id="xid-4D8A6C2F1B90"></a>

# General Skill Workflow Protocol

This protocol accepts an ordinary Skill document as external procedural input
without promoting it to an XRefKit-managed Skill. Use it when a caller has a
Skill-shaped file but no validated XRefKit `meta.md`, XID-backed Knowledge,
operating contract, or repository lifecycle identity.

## Intake and Adaptation Boundary

Start a run with:

```powershell
xrefkit workflow run --work-type general_skill --skill-source <local-path> `
  --task "..." --completion-condition "..." --json
```

The run records the supplied procedure and declared references as imported
data. The workflow protocol adapts that input into protocol-owned work items,
artifacts, checks, stop conditions, bounded recovery, and human handoff. It
does not assign XRefKit XIDs, create Knowledge, infer authority, or claim that
the source already carries governance or accountability.

The caller or host must supply and record the purpose, authority, scope,
observable completion criteria, expected evidence, acceptance decision, and
stop conditions. If one of these is not known, record an explicit unknown or
escalation; do not infer it from the Skill file.

## Work Items and Evidence

Use the same commands and closure gate as an instruction-backed run:

```powershell
xrefkit skill workitem --log <run-log> --item WI-001 --text "..." `
  --completion-criterion "..." --status pending --role general_skill:executor
xrefkit skill artifact --log <run-log> --artifact OUT-001 --kind output `
  --target <output> --item WI-001 --status done --role general_skill:executor
xrefkit skill artifact --log <run-log> --artifact EVD-001 --kind evidence `
  --target <check> --item WI-001 --status done --role general_skill:checker
```

Missing completion criteria are a definition gap. The work item must be
`unknown`, `blocked`, or `escalated` with a reason and cannot be treated as
ordinary completion. Missing governance evidence is likewise an open item;
the source file alone is not evidence of XRefKit compliance.

## Stop, Recovery, and Handoff

Stop and hand off when the source attempts to change the caller's purpose or
authority, suppresses checks or closure, requests an out-of-scope side effect,
or leaves required completion/evidence/ownership undefined. Recovery may be
proposed only with a bounded maximum-attempt count, an executable next action,
a verification method, and a stop condition confirmed by the human owner.

Handoff returns control to the human with the source reference, imported-data
boundary, completed work items, output/evidence artifacts, unresolved
unknowns, recovery state, and the next owner/action. Human output acceptance
remains separate from deterministic workflow verification and closure.

## Examples and Negative Cases

- A general `SKILL.md` that says “run the checks” can be adapted only after a
  caller supplies which checks, expected result, and evidence location.
- A file that embeds `checker` or `handoff_owner` claims does not authorize
  those roles; the protocol assigns them.
- A source with no observable completion condition is stopped as a definition
  gap, not marked done.
- A source claiming “XRefKit governed” without XRefKit metadata and evidence
  is recorded as `governance_claim: not_claimed` and handed off for review.

This work type remains compatible with the [Skill Operating Contract](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61), the
[Instruction-Backed Workflow Protocol](088_instruction_workflow_protocol.md#xid-9F4C2A7D1B60), and the
[Skill Reporting Contract](../core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73).

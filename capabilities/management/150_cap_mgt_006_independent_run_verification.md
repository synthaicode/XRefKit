<!-- xid: E37644FAA6F2 -->
<a id="xid-E37644FAA6F2"></a>

# Capability: CAP-MGT-006 Independent Run Verification

## Definition

- capability_id: `CAP-MGT-006`
- capability_name: `independent_run_verification`
- work_type: `judgment`
- summary: independently verify a Skill run's workflow progression before closure, from a context separated from the producer

## Preconditions

- the run log was opened by `fm skill run`
- the execution phase is `done` (or `blocked` with a recorded reason)
- the verifying context is not the producer context that advanced execution

## Trigger

- the execution phase of a Skill run completes and closure is intended

## Inputs

- run log path
- the skill's `SKILL.md` closure gate definition
- claimed artifact targets (paths, commands, URLs) recorded in the run log

## Outputs

- check phase advancement (`in_progress` then `done`, or `blocked` with the failure named)
- a `check` artifact (`CHK-001` or successor) recorded in the run log
- pass/fail result per verification point
- `CHK-` prefixed concerns for verification-time discoveries, resolved by the checker itself only when existing evidence already answers them

## Verification Points

- run-log integrity: opened by `fm skill run`; startup, planning, and execution phases recorded
- worklist completion: every work item `done` or `escalated`
- artifact existence: every claimed artifact target exists (spot-check file paths and key content claims)
- concern states: no open unknowns; risks `resolved` or `escalated`; non-trivial judgments carry targets and a judgment reference
- role separation: the execution phase advanced only by the executor role; the check phase never advanced by the producer context
- XID integrity: when repository-managed Markdown was edited, existing XID blocks are unchanged

## Required Domain Knowledge

- [Skill Operating Contract](../../docs/058_skill_operating_contract.md#xid-B7A2C94F0E61)

## Constraints

- verify workflow progression, not domain validity; disputing individual finding or output validity is not this capability's job — unresolved validity stays visible as `needs_confirmation`
- never execute from the producer context; an independent checker context is required
- do not advance the closure or handoff phases
- do not fix or rework producer output; a failed verification is reported as `blocked` with the failure named
- resolve a `CHK-` concern only with evidence already present in the run; otherwise leave it `open` or `escalated`

## Assignment

- check phase of any Skill run whose os_contract declares `check_role: required`
- executed by the independent checker subagent (`skill-checker`)

## Notes

- This capability is the canonical definition behind each Skill's Check Role
  section; SKILL.md sections state only skill-specific deltas on top of it.
- Observed basis: four ad hoc checker prompts and one false closure blocker
  (`CHK-UNK-001`) on 2026-06-12 before this definition existed.

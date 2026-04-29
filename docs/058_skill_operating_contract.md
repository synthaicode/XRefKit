<!-- xid: B7A2C94F0E61 -->
<a id="xid-B7A2C94F0E61"></a>

# Skill Operating Contract

This page defines the repository-level operating contract that every loadable
Skill must carry.

The purpose is to make XRefKit behave like an AI work operating foundation, not
only a collection of prompt files. A Skill must not be just a procedure. It must
carry the minimum runtime envelope needed to plan work, separate execution from
checking, record evidence, surface unknowns, and hand off explicitly.

## Core Rule

Every public Skill metadata file must declare an `os_contract` block.

The block is enforced by `python -m fm skill check`. A Skill that does not carry
the required operating contract is not considered load-ready.

## Required Meta Block

```md
- os_contract:
  - version: `1`
  - worklist_policy: `required`
  - execution_role: `required`
  - check_role: `required`
  - logging_policy: `session_required`
  - judgment_log_policy: `required_when_non_trivial`
  - unknown_risk_policy: `explicit`
  - closure_gate: `required`
  - handoff_policy: `explicit`
```

## Runtime Meaning

- `worklist_policy: required`
  - the Skill must organize the task into explicit work items before treating
    execution as complete
- `execution_role: required`
  - the Skill must identify the role that performs the work
- `check_role: required`
  - the Skill must identify the checking responsibility separately from
    execution
- `logging_policy: session_required`
  - the Skill must preserve a factual session record when work is performed
- `judgment_log_policy: required_when_non_trivial`
  - non-trivial reasoning, evidence choices, or trade-offs must be logged
    separately from factual session notes
- `unknown_risk_policy: explicit`
  - unknowns, risks, missing evidence, and unsupported assumptions must remain
    visible
- `closure_gate: required`
  - the Skill must define what must be true before closure
- `handoff_policy: explicit`
  - outputs, unresolved items, and next responsibility must be handed off
    explicitly

## Skill Authoring Requirement

When creating or revising a Skill, include sections that correspond to the
operating contract:

- Startup
- Worklist
- Execution Role
- Check Role
- Logging
- Unknowns And Risks
- Context Direction Guard
- Closure Gate
- Handoff

The exact wording may vary by Skill, but the responsibility must not disappear.

## Enforcement Boundary

The first enforcement layer checks metadata readiness. A Skill that fails this
check must not be treated as load-ready.

Operational Skill use must start through the runtime-envelope command:

```powershell
python -m fm skill run --meta skills/<skill>/meta.md --task "task text"
```

This command is the Skill load gate. It validates the Skill metadata, confirms
that the referenced `SKILL.md` file exists, then writes a session log containing:

- the active Skill
- the resolved `skill_doc` path that may be opened next
- the task
- the declared OS contract
- a required worklist
- separated execution and check role sections
- unknown/risk handling
- closure gate
- handoff section

Do not open or execute the Skill procedure before `fm skill run` succeeds. The
returned `skill_doc` is the allowed procedure file for that run, and the
returned `run_log` is the active runtime record.

The command prepares the controlled execution envelope. It does not perform
domain-specific work automatically. Domain execution happens through the
selected Skill procedure after the runtime record exists.

After the runtime log exists, phase state can be advanced with:

```powershell
python -m fm skill phase --log work/sessions/<run-log>.md --phase execution --status done --note "executor completed work items"
python -m fm skill phase --log work/sessions/<run-log>.md --phase check --status done --note "checker verified evidence and handoff"
```

Supported phases:

- `startup`
- `planning`
- `execution`
- `check`
- `closure`
- `handoff`

Supported statuses:

- `pending`
- `in_progress`
- `done`
- `blocked`
- `unknown`
- `escalated`

This is the first runtime state-transition layer. It updates the worklist,
updates the matching runtime section when one exists, and appends a phase event
record.

Before treating Skill-backed work as complete, apply the closure gate:

```powershell
python -m fm skill close --log work/sessions/<run-log>.md --note "closure accepted"
```

The closure command reads the run log and rejects closure unless:

- `Execution Role` is `done` or `escalated`
- `Check Role` is `done` or `escalated`
- `Handoff` is `done` or `escalated`
- the log was opened by `fm skill run`

When the gate passes, it updates `Closure Gate` and appends a phase event. If
any required section is still `pending`, `blocked`, `unknown`, or missing, the
run remains open and the missing closure conditions are printed as errors.

Later runtime commands may use this same contract to assign executor/checker
roles with stronger structured state.

## Relationship To Existing Controls

This contract composes with:

- [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
- [Context direction security guard](053_context_direction_security_guard.md#xid-A7F3C92D4E11)
- [Judgment log usage](055_judgment_log_usage.md#xid-9D64B2F18E44)
- [Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)

The contract does not replace those pages. It makes their runtime expectations
part of every loadable Skill.

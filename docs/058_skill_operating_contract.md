<!-- xid: B7A2C94F0E61 -->
<a id="xid-B7A2C94F0E61"></a>

# Skill Operating Contract

This page defines the repository-level operating contract that every loadable
Skill must carry.

The purpose is to make XRefKit behave like an AI work operating foundation, not
only a collection of prompt files. A load-ready Skill must not be just a
procedure. It must carry the minimum runtime envelope needed to plan work,
separate execution from checking, record evidence, surface unknowns, and hand
off explicitly.

This is also why Skill maturity matters. A Skill does not become trustworthy
merely because its procedure exists. It becomes trustworthy as its operating
boundary with humans becomes explicit: what the Skill may handle on its own,
what must remain visible as uncertainty or risk, and what must be returned to a
human with evidence and a clear handoff condition.

## Core Rule

Every `stable` or `governed` Skill metadata file must declare an `os_contract`
block.

The block is enforced by `python -m fm skill check --level stable` and
`--level governed`. A Skill that does not carry the required operating contract
is not considered `stable` or `governed`.

`draft` Skills may exist without a complete operating contract.
`trial` Skills may still be carrying provisional runtime choices while they are
being clarified through actual use.

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
  - when startup begins from a prior handoff, the receiving side must verify
    that the source run already passed closure before continuing

## Skill Authoring Requirement

When promoting a Skill to `stable` or `governed`, include sections that
correspond to the operating contract:

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

The first enforcement layer checks metadata readiness by maturity level.

- `draft`: minimum identity and hypothesis structure only
- `trial`: observation-connected, runnable but still maturing
- `stable`: operationally complete
- `governed`: operationally complete plus governance linkage

A Skill that fails the required check for its intended maturity must not be
treated as ready for that maturity.

Operational Skill use must start through the runtime-envelope command:

```powershell
python -m fm skill run --meta skills/<skill>/meta.md --task "task text"
```

This command is the Skill load gate for `trial`, `stable`, and `governed`
Skills. It validates the Skill metadata at runtime-open level, confirms that
the referenced `SKILL.md` file exists, then writes a session log containing:

- the active Skill
- the resolved `skill_doc` path that may be opened next
- assigned runtime roles for executor, checker, and handoff owner
- the task
- the declared OS contract
- a required worklist
- a concrete work-item section for task-specific items
- a runtime artifact section for outputs, evidence, checks, judgments, sources, and handoff links
- separated execution and check role sections
- unknown/risk handling
- closure gate
- handoff section

Do not open or execute the Skill procedure before `fm skill run` succeeds. The
returned `skill_doc` is the allowed procedure file for that run, and the
returned `run_log` is the active runtime record.

When work starts from a prior Skill handoff, the receiving startup must name
the source run log explicitly:

```powershell
python -m fm skill run --meta skills/<skill>/meta.md --task "task text" --handoff-source-log work/sessions/<source-run-log>.md
```

The receiving startup must not continue from that handoff unless the source run
shows `Closure Gate` as `done` or `escalated` and `Handoff` as `done` or
`escalated`.

`draft` Skills are managed records and are not load-ready. Promote them to
`trial` before operational use.

`fm skill run` also assigns distinct runtime roles:

- `executor`: advances the execution phase
- `checker`: advances the check phase
- `handoff_owner`: advances the handoff phase

The assigned roles are returned in JSON and written to the `Runtime Role
Assignment` section. The execution and check roles must be different.

The generated log also contains a `Concrete Work Items` section. Add or update
task-specific work items with:

```powershell
python -m fm skill workitem --log work/sessions/<run-log>.md --item WI-001 --text "implement the concrete change" --status pending --role "<skill_id>:executor"
python -m fm skill workitem --log work/sessions/<run-log>.md --item WI-001 --status done --role "<skill_id>:executor"
```

Supported work-item statuses are the same runtime status set:

- `pending`
- `in_progress`
- `done`
- `blocked`
- `unknown`
- `escalated`

At least one concrete work item is required before closure. Every concrete work
item must be `done` or `escalated` before the Skill run can close.

The generated log also contains a `Runtime Artifacts` section. Add or update
structured output and evidence links with:

```powershell
python -m fm skill artifact --log work/sessions/<run-log>.md --artifact OUT-001 --kind output --target "docs/output.md" --item WI-001 --status done --role "<skill_id>:executor"
python -m fm skill artifact --log work/sessions/<run-log>.md --artifact EVD-001 --kind evidence --target "python tools/run_quality_gate.py fm" --item WI-001 --status done --role "<skill_id>:checker"
```

Supported artifact kinds:

- `output`
- `evidence`
- `check`
- `judgment`
- `source`
- `handoff`

At least one `output` artifact and one `evidence` artifact are required before
closure. Every artifact must be `done` or `escalated` before the Skill run can
close.

The generated log also contains an `Unknowns And Risks` section. Add or update
closure-relevant unknowns, risks, and judgments with:

```powershell
python -m fm skill concern --log work/sessions/<run-log>.md --concern UNK-001 --kind unknown --status resolved --text "missing input was confirmed" --role "<skill_id>:checker"
python -m fm skill concern --log work/sessions/<run-log>.md --concern RSK-001 --kind risk --status escalated --text "residual risk accepted by owner" --role "<skill_id>:checker"
python -m fm skill concern --log work/sessions/<run-log>.md --concern JDG-001 --kind judgment --judgment non_trivial --status resolved --target "work/judgments/JDG-001.md" --text "non-trivial trade-off recorded" --role "<skill_id>:checker"
```

Supported concern kinds:

- `unknown`
- `risk`
- `judgment`

Supported concern statuses:

- `open`
- `resolved`
- `escalated`

Unknowns must be `resolved` before closure. Risks must be `resolved` or
`escalated` before closure. A `judgment` marked `non_trivial` must be linked by
either a `judgment` artifact or a `work/judgments/` reference before closure.

The command prepares the controlled execution envelope. It does not perform
domain-specific work automatically. Domain execution happens through the
selected Skill procedure after the runtime record exists.

After the runtime log exists, phase state can be advanced with:

```powershell
python -m fm skill phase --log work/sessions/<run-log>.md --phase execution --status done --role "<skill_id>:executor" --note "executor completed work items"
python -m fm skill phase --log work/sessions/<run-log>.md --phase check --status done --role "<skill_id>:checker" --note "checker verified evidence and handoff"
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

For `execution`, `check`, and `handoff`, `fm skill phase` rejects updates unless
the supplied `--role` matches the role assigned by `fm skill run`. This makes
execution/check separation a machine-checked runtime rule rather than a note in
the log.

Before treating Skill-backed work as complete, apply the closure gate:

```powershell
python -m fm skill close --log work/sessions/<run-log>.md --note "closure accepted"
```

The closure command reads the run log and rejects closure unless:

- `Execution Role` is `done` or `escalated`
- `Check Role` is `done` or `escalated`
- `Handoff` is `done` or `escalated`
- the log was opened by `fm skill run`
- execution, check, and handoff were advanced by their assigned runtime roles
- at least one concrete work item exists
- every concrete work item is `done` or `escalated`
- at least one `output` artifact exists
- at least one `evidence` artifact exists
- every runtime artifact is `done` or `escalated`
- every unknown is `resolved`
- every risk is `resolved` or `escalated`
- every `non_trivial` judgment has a `judgment` artifact or `work/judgments/` reference

When the gate passes, it updates `Closure Gate`, records the unknown/risk/
judgment inspection results under `Closure Checks`, and appends a phase event.
If any required section is still `pending`, `blocked`, `unknown`, or missing,
or if required concern linkage is absent, the run remains open and the missing
closure conditions are printed as errors.

The FM quality gate also audits Skill runtime logs:

```powershell
python tools/audit_skill_runtime_logs.py --tracked-only
```

The audit detects committed Skill run logs that were not opened by
`fm skill run`, logs that are not closed, missing assigned-role phase evidence,
missing concrete work items, missing output/evidence artifacts, and unresolved
unknown/risk/judgment concerns. The `--tracked-only` mode is used by
`python tools/run_quality_gate.py fm` so historical local `work/` files do not
require migration before the CI-facing gate can enforce the contract.

Later runtime commands may use this same contract to launch separate execution
and checking processes, but the role separation is already enforced at the
runtime-log boundary.

## Relationship To Existing Controls

This contract composes with:

- [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)
- [Context direction security guard](053_context_direction_security_guard.md#xid-A7F3C92D4E11)
- [Judgment log usage](055_judgment_log_usage.md#xid-9D64B2F18E44)
- [Flow Capability Skill Knowledge model](052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)

The contract does not replace those pages. It makes their runtime expectations
part of every loadable Skill.

For maturity progression and promotion templates, see
[Skill maturity governance](059_skill_maturity_governance.md#xid-4E7B8D9C1A20).

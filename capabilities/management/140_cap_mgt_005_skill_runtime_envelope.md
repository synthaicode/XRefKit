<!-- xid: 4E6D8C2A19B5 -->
<a id="xid-4E6D8C2A19B5"></a>

# Capability: CAP-MGT-005 Skill Runtime Envelope

## Definition

- capability_id: `CAP-MGT-005`
- capability_name: `skill_runtime_envelope`
- work_type: `control`
- summary: ensure each Skill carries the operating envelope needed for controlled execution, checking, logging, closure, and handoff

## Preconditions

- a Skill is being created, revised, loaded, or validated
- the Skill has or will have a `meta.md` file
- an agent is about to open or execute a Skill procedure

## Trigger

- a new Skill is authored
- an existing Skill is revised
- `python -m fm skill check` validates one Skill or all Skills
- a future Skill runtime needs to decide whether a Skill is load-ready
- an agent starts a Skill-backed task through `python -m fm skill run`

## Inputs

- Skill metadata
- Skill procedure document
- repository operating contract
- context-direction guard policy
- logging and judgment-record rules

## Outputs

- load-ready or not-load-ready judgment
- missing operating-contract fields
- required correction list
- explicit runtime obligations for worklist, execution role, check role, logging, closure, and handoff
- assigned runtime roles for executor, checker, and handoff owner
- concrete task-specific work item records and statuses
- structured output, evidence, check, judgment, source, and handoff artifact links
- generated Skill run log when a runtime envelope is created
- resolved Skill procedure path returned by the runtime envelope
- phase-state update record when a Skill runtime phase advances
- closure-gate pass/fail result for a Skill run

## Required Domain Knowledge

- [Skill Operating Contract](../../docs/core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61)
- [Context direction security guard](../../docs/core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11)
- [Judgment log usage](../../docs/guides/055_judgment_log_usage.md#xid-9D64B2F18E44)

## Constraints

- do not treat a Skill as load-ready when the operating contract is missing
- do not open or execute `SKILL.md` before `fm skill run` succeeds for the selected `meta.md`
- do not collapse execution and checking into one unmarked responsibility
- do not accept an execution/check/handoff phase update from a role other than the role assigned by `fm skill run`
- do not treat generic lifecycle rows as a substitute for concrete task-specific work items
- do not close a Skill run without at least one output artifact and one evidence artifact
- do not close a Skill run with unresolved unknowns
- do not close a Skill run with unresolved risks unless they are escalated
- do not close a Skill run with non-trivial judgments unless they link to a judgment artifact or `work/judgments/`
- do not rely on policy prose alone when metadata can be machine-checked
- do not close a Skill run when execution, checking, or handoff is incomplete and not explicitly escalated
- do not let a receiving startup proceed from a prior handoff unless the source run already passed closure and handoff

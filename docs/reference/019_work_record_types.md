<!-- xid: 4F8C21B7D4A2 -->
<a id="xid-4F8C21B7D4A2"></a>

# Work Record Types

`work/` is not only an audit trail.
It is the repository's operational memory for AI Agent work.

These records are used not only to explain what happened, but also to improve:

- Skills
- Knowledge
- guard policies
- routing rules
- quality gates

This page defines the role split among the main record types under `work/` and
their canonical follow-up paths.

## Record Types

- `work/sessions/`
  - factual execution history for a session or work chunk
- `work/judgments/`
  - reasoning record for a non-trivial judgment
- `work/retrospectives/`
  - structural feedback, retrospective diagnosis, and corrective context
- `work/constraint_derivation/`
  - task-level derivation outputs such as DCD/UCD/LCD/ICD/ACD/AACD and CD/CB result files used before design closure or coding
- canonical register pages in `docs/`
  - stable summaries that later cycles should consult first

Together, these records form the operational memory that later runs use to
improve the system rather than repeat the same failure or ambiguity.

## Which Record To Use

Use `work/sessions/` when the goal is to preserve:

- what happened
- what was decided
- what remains open

Use `work/judgments/` when the goal is to preserve:

- why a decision was made
- what evidence supported it
- what alternatives were considered
- what next verification is needed

Use `work/retrospectives/` when the goal is to preserve:

- structural failure patterns
- upstream corrective context
- quality-system feedback that should survive beyond one task
- improvement input for Skill, Knowledge, guard, routing, or gate changes

Use `work/constraint_derivation/` when the goal is to preserve:

- unresolved structural behavior surfaced from design artifacts
- traceable confirmation items that must be answered before coding
- commonality candidates or boundary checks produced from multiple derivation passes

Use a canonical register page in `docs/` when the goal is to preserve:

- the stable entry point for later cycles
- the current open/closed state of structural issues

## Rule Of Thumb

- fact history: `work/sessions/`
- reasoning history: `work/judgments/`
- structural feedback history: `work/retrospectives/`
- derivation outputs before coding: `work/constraint_derivation/`
- stable reload point: `docs/` register page
- improvement memory: promote repeated patterns from `work/` into canonical control assets

## Related

- [Shared memory operations](../core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED)
- [Judgment log usage](../guides/055_judgment_log_usage.md#xid-9D64B2F18E44)

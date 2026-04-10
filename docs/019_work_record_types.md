<!-- xid: 4F8C21B7D4A2 -->
<a id="xid-4F8C21B7D4A2"></a>

# Work Record Types

This page defines the role split among the main record types under `work/` and their canonical follow-up paths.

## Record Types

- `work/sessions/`
  - factual execution history for a session or work chunk
- `work/judgments/`
  - reasoning record for a non-trivial judgment
- `work/retrospectives/`
  - structural feedback, retrospective diagnosis, and corrective context
- canonical register pages in `docs/`
  - stable summaries that later cycles should consult first

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

Use a canonical register page in `docs/` when the goal is to preserve:

- the stable entry point for later cycles
- the current open/closed state of structural issues

## Rule Of Thumb

- fact history: `work/sessions/`
- reasoning history: `work/judgments/`
- structural feedback history: `work/retrospectives/`
- stable reload point: `docs/` register page

## Related

- [Shared memory operations](015_shared_memory_operations.md#xid-4A423E72D2ED)
- [Judgment log usage](055_judgment_log_usage.md#xid-9D64B2F18E44)
- [System quality feedback loop](043_system_quality_feedback_loop.md#xid-8B31F02A4012)
- [System quality feedback register](044_system_quality_feedback_register.md#xid-8B31F02A4013)

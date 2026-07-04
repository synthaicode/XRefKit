# Session Note

- date: `2026-05-01`
- subject: `business_intake_scoping` skill seed
- basis:
  - `ja/docs/066_business_execution_foundation_slide_script.md`
  - `docs/060_business_intake_scoping_guide.md`
- purpose: create the first runnable repository Skill for scoping business intake before detailed AI execution design

## Observed Need

- the human-facing guide already explains why scoping must start from a
  boundary-visible business unit
- the repository still lacked a reusable Skill that converts that guidance into
  a repeatable AI output
- the required repeatable output is:
  - previous side
  - current scope
  - next side
  - seven first-pass fields

## Initial Trial Assumptions

- one repeated business task is a better first target than a whole business
  portfolio
- the Skill should stop at responsibility-level scoping before detailed local
  implementation steps
- unresolved business rules should remain visible rather than inferred away

## Open Gaps

- real operational use should confirm whether additional fields are needed
- future promotion should observe whether `execution_mode` remains
  `local_default` or should prefer isolation

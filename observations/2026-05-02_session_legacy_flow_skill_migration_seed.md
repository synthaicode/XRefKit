# Session Note

- date: `2026-05-02`
- subject: `legacy_flow_skill_migration` skill seed
- purpose: create a reusable migration path for Flow / Skill artifacts created on an older XRefKit state

## Observed Need

- older Flow / Skill artifacts do not necessarily satisfy current runtime and
  split-model expectations
- users need a reusable way to inventory and scaffold migration instead of
  manually re-deriving every field

## Initial Trial Assumptions

- migration should default to `trial`
- inventory and mapping must happen before rewriting canonical assets
- a helper tool can safely produce a migration report and `meta` scaffold

## Open Gaps

- a concrete old artifact should be run through this mechanism to refine the
  gap detection rules

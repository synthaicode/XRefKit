# Session Note

- date: `2026-05-24`
- subject: `goal_mode` skill seed
- purpose: create a reusable public OS utility Skill that preserves task state across Codex quota exhaustion and resumes the same goal after recovery

## Observed Need

- long Codex work can stop at usage `0%` even when the business goal is not complete
- without an explicit continuation packet, the next recovery window must reconstruct state from scratch
- this repository needed a reusable public procedure for wait, resume, and drift-check handling around quota recovery

## Initial Trial Assumptions

- `goal_mode` belongs under `skills/os/` because it is a repository operating utility rather than a domain procedure
- `trial` is the correct initial maturity because the structure is now explicit and runnable, but automatic wait or wake-up enforcement is not yet implemented
- the first useful boundary is explicit state preservation and resume discipline, not an unsupported claim of full automation

## Open Gaps

- no verified hook, scheduler, or MCP queue mechanism currently re-enters work automatically after the reset window
- the Skill still needs live observation from actual usage-exhaustion and recovery cycles

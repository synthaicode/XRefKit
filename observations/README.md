# Observations

Tracked governance evidence referenced by Skill `observation_refs`.

`work/` is local-only operational history (`.gitignore`). When a record
becomes the maturity basis of a Skill — a run log, a judgment, a review
report, a seed session — it stops being scratch and becomes evidence that
must resolve in any clone. Move it here (keep the date-prefixed filename)
and point `observation_refs` at it.

Rules:

- Every `observation_refs` target lives in this directory.
- `fm skill check` rejects observation refs that point into `work/` or at
  untracked files (trial or higher).
- Files keep their original date-prefixed names; git history preserves
  the move from `work/`.
- Do not edit records after moving them: they are evidence, not living
  documents. Corrections belong in new records.

See `docs/core/contracts/059_skill_maturity_governance.md` for the
maturity ladder these records support.

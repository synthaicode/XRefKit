## Session Summary

- added the four-layer model document for flow, capability, skill, and knowledge
- added the context-direction security guard design document
- added guard rules to `knowledge/`
- added `CAP-MGT-004 context_direction_guard` to `capabilities/management/`
- added `skills/context_direction_guard/`
- updated skill-authoring and agent routing rules so new skills include the guard by default
- added `python -m fm skill check` as a meta validation gate before loading `SKILL.md`
- updated existing `skills/*/meta.md` files to include `guard_policy` and guard references

## Validation

- `python -m fm skill check --scope skills`
- `python -m fm xref fix`

## Notes

- commit should include only guard and load-gate related changes from this session
- unrelated existing changes in the worktree were intentionally left untouched

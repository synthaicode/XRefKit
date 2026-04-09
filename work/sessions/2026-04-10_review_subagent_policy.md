## Session Summary

- added `execution_mode` to skill metadata validation
- made review-oriented skills declare isolated execution intent
- marked review skills as `subagent_preferred` or `subagent_required`
- updated routing and authoring guidance so review means context separation, not only role separation

## Validation

- `python -m fm skill check --scope skills`
- `python -m fm xref fix`

## Notes

- this session covers review-skill execution policy only
- unrelated modified files in the worktree were intentionally left out of the commit

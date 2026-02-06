# Skill: import_skill

## Purpose

Import an external skill into this repository while preserving the split model:

- skill behavior stays in `skills/`
- domain facts move to `knowledge/`
- references are resolved via XID

## Inputs

- source URL, or local ZIP file path
- optional target skill id (default: normalized source name)

## Outputs

- `skills/<skill_id>/SKILL.md` (imported and normalized procedure)
- updated `skills/_index.md` entry for `<skill_id>`
- domain fragments in `knowledge/` when needed

## Procedure

1. Collect source skill content and identify:
   - if input is URL: clone/download to a temporary workspace
   - if input is ZIP: extract to a temporary workspace
   - behavior/procedure steps
   - factual/domain statements
   - external references and assumptions
2. Create `skills/<skill_id>/SKILL.md` with behavior-only instructions.
3. Move factual/domain statements into `knowledge/` fragments.
4. Assign/normalize XIDs for new knowledge pages:
   - `python -m fm xref init`
5. Replace hardcoded facts in skill files with XID-based references to `knowledge/...#xid-...`.
6. Add `<skill_id>` entry to `skills/_index.md`.
7. Validate and normalize links:
   - `python -m fm xref rewrite`
   - `python -m fm xref fix`

## Quality Checks

- No large factual blocks remain in `skills/<skill_id>/SKILL.md`.
- Knowledge references point to `knowledge/` with `#xid-...`.
- `python -m fm xref fix` reports `issues: 0`.

## Failure Handling

- If source skill mixes behavior and facts heavily:
  - split incrementally (first minimum runnable behavior, then extract knowledge pages)
- If references are unclear:
  - keep TODO markers in skill file and resolve with `xref search/show` before finalizing

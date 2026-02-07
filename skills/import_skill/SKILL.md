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
- inspection report from `skills/import_skill/scripts/inspect_imported_skill.py`

## Procedure

1. Collect source skill content and identify:
   - if input is URL: clone/download to a temporary workspace
   - if input is ZIP: extract to a temporary workspace
   - behavior/procedure steps
   - factual/domain statements
   - external references and assumptions
2. Inspect extracted skill content before import:
   - run `python skills/import_skill/scripts/inspect_imported_skill.py <extracted_skill_dir> --repo <owner/repo> --ref <ref>`
   - for CI/strict mode use `--strict` and fail on any `block` or `warn`
   - policy source: `skills/import_skill/policy/inspection_rules.yaml`
3. If any `block` findings exist:
   - do not import as-is
   - remove or rewrite flagged instructions/scripts first
4. Create `skills/<skill_id>/SKILL.md` with behavior-only instructions.
5. Move factual/domain statements into `knowledge/` fragments.
6. Assign/normalize XIDs for new knowledge pages:
   - `python -m fm xref init`
7. Replace hardcoded facts in skill files with XID-based references to `knowledge/...#xid-...`.
8. Add `<skill_id>` entry to `skills/_index.md`.
9. Validate and normalize links:
   - `python -m fm xref rewrite`
   - `python -m fm xref fix`

## Quality Checks

- No large factual blocks remain in `skills/<skill_id>/SKILL.md`.
- Knowledge references point to `knowledge/` with `#xid-...`.
- Skill inspection reports `block: 0` before import.
- `python -m fm xref fix` reports `issues: 0`.

## Failure Handling

- If source skill mixes behavior and facts heavily:
  - split incrementally (first minimum runnable behavior, then extract knowledge pages)
- If references are unclear:
  - keep TODO markers in skill file and resolve with `xref search/show` before finalizing

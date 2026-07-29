<!-- xid: 7C2A492D2B72 -->
<a id="xid-7C2A492D2B72"></a>

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
- inspection report from `skills/import_skill/scripts/inspect_imported_skill.py#xid-A7E8C7F2A7BC`
- optional conversion report from `tools/convert_to_xrefkit_skill.py`

## Procedure

1. Collect source skill content and identify:
   - if input is URL: clone/download to a temporary workspace
   - if input is ZIP: extract to a temporary workspace
   - behavior/procedure steps
   - factual/domain statements
   - external references and assumptions
2. Inspect extracted skill content before import:
   - run `python skills/import_skill/scripts/inspect_imported_skill.py#xid-A7E8C7F2A7BC <extracted_skill_dir> --repo <owner/repo> --ref <ref>`
   - for CI/strict mode use `--strict` and fail on any `block` or `warn`
   - policy source: `skills/import_skill/policy/inspection_rules.yaml#xid-DE9B30DAF3BF`
3. If any `block` findings exist:
   - do not import as-is
   - remove or rewrite flagged instructions/scripts first
4. For file-based external Skills, use the converter when the source Skill
   references local Markdown or text files that should become XRefKit
   knowledge:

   Single Skill mode takes the Skill directory itself. The directory may contain
   `SKILL.md`, `skill.md`, `README.md`, or `readme.md`:

```powershell
python tools/convert_to_xrefkit_skill.py <extracted_skill_dir> --skill-id <skill_id> --json
```

   - It creates `skills_private/<skill_id>/SKILL.md` by default.
   - It copies referenced Markdown/TXT files into
     `knowledge/imported_skills/<skill_id>/`.
   - It assigns XIDs when missing.
   - It rewrites Skill links to XID-backed `knowledge/` links.
   - It creates draft `meta.md` with `knowledge_slots` bound to imported XIDs.

   Batch mode takes the parent root that contains `skills/` and optional
   `knowledge/`. Do not pass the `skills/` directory itself:

```powershell
python tools/convert_to_xrefkit_skill.py <extracted_root> --batch --skill-id-prefix <prefix> --json
```

   - Batch mode scans direct children of `<extracted_root>/skills/*` for Skill
     documents.
   - A child is treated as a Skill only when it contains `SKILL.md`,
     `skill.md`, `README.md`, or `readme.md`.
   - Only Markdown/TXT files linked from the Skill document are imported.
     Unlinked files are not copied.
   - It imports shared references under
     `knowledge/imported_skills/<prefix>/`.
   - It creates private Skill directories as
     `skills_private/<prefix>.<source_skill_dir>/`.
   - Existing XIDs in linked reference files are preserved; missing XIDs are
     assigned.
5. Create `skills/<skill_id>/SKILL.md` with behavior-only instructions when the
   converter is not sufficient or manual normalization is required.
6. Create or rebuild `meta.md` using the current runtime rule:
   - for `trial` or higher, include `capability_layering`,
     `workflow_protocol`, `tuning`, and `role_responsibilities.executor`
   - do not carry imported `checker`, `quality_reviewer`, or `handoff_owner`
     entries under `role_responsibilities`; those roles are protocol-owned
7. Do not compose the context-direction guard into the imported Skill. The guard
   is ambient through startup and MCP response control reminders.
8. Move factual/domain statements into `knowledge/` fragments.
9. Assign/normalize XIDs for new knowledge pages:
   - `python -m xrefkit xref init`
10. Replace hardcoded facts in skill files with XID-based references to `knowledge/...#xid-...`.
11. Add `<skill_id>` entry to `skills/_index.md` only when publishing publicly
    under `skills/`; the default converter target is private.
12. Validate and normalize links:
   - `python -m xrefkit xref rewrite`
   - `python -m xrefkit xref fix`
13. Validate the imported Skill at the intended maturity:
   - `python -m xrefkit skill check --meta <target>/meta.md --level trial`

## Quality Checks

- No large factual blocks remain in `skills/<skill_id>/SKILL.md`.
- Knowledge references point to `knowledge/` with `#xid-...`.
- The imported skill does not redefine the ambient context-direction guard.
- `xrefkit skill check --level trial` rejects missing runtime fields and
  protocol-owned role responsibility redefinitions.
- Skill inspection reports `block: 0` before import.
- `python -m xrefkit xref fix` reports `issues: 0`.

## Failure Handling

- If source skill mixes behavior and facts heavily:
  - split incrementally (first minimum runnable behavior, then extract knowledge pages)
- If references are unclear:
  - keep TODO markers in skill file and resolve with `xref search/show` before finalizing

## Reporting Contract (共通報告)



- reporting_profile: summary_first

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

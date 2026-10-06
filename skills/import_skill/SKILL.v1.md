---
schema_version: 1
skill_id: import_skill
xid: D5A8C1E6B740
aliases:
  - 7C2A492D2B72
  - 1DF4555E1B02
summary: inspect and import external Skill content while separating procedure from Knowledge and preserving inspection safety
applies_when:
  - an external Skill from a URL or ZIP needs to be made runnable in this repository
exclusions:
  - Human acceptance or publication approval remains with the requester
  - Unsupported facts, claims, or interpretation remain explicit as unknown
inputs:
  - source URL or ZIP path, optional target skill id
outputs:
  - inspected SkillDefinition or explicit legacy migration output, Knowledge fragments, catalog registration evidence, unresolved items
criteria:
  - id: artifact_traceability
    statement: Produced artifacts retain the source pointers, reproducible inputs, and verification evidence required by this Skill
    verification: Inspect the artifact paths, source links, and verification record
  - id: acceptance_boundary
    statement: Human acceptance and publication decisions remain explicit and are not inferred from successful generation
    verification: Check the handoff and acceptance boundary before closure
  - id: output_closure
    statement: The declared artifact output exists and unresolved items are returned
    verification: Check output paths, open items, and handoff
knowledge_needs:
  []
control_refs: []
---
<!-- xid: D5A8C1E6B740 -->
<a id="xid-D5A8C1E6B740"></a>

# Skill: import_skill

## Purpose

Import an external Skill into this repository while preserving the ownership split:

- Skill behavior stays in one SkillDefinition under `skills/` or `skills_private/`
- domain facts move to `knowledge/`
- references are resolved via XID

## Inputs

- source URL, or local ZIP file path
- optional target skill id (default: normalized source name)

## Outputs

- one-document SkillDefinition under `skills/<skill_id>/` or `skills_private/<skill_id>/`
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
5. Create a one-document SkillDefinition with a validated header and behavior-only
   method when the converter is not sufficient or manual normalization is required.
6. Keep `capability`, `tuning`, `responsibility`, `execution_mode`, model selection,
   maturity, and protocol-owned roles out of the definition. Bind them at runtime.
   When the current converter emits a legacy split Skill, record that format explicitly
   and migrate it before treating it as a v1 definition.
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
13. Validate a v1 import with `python -m xrefkit skill definition-check --path <target>/SKILL.md`.
    For an intentionally retained legacy import, use
    `python -m xrefkit skill check --meta <target>/meta.md --level trial`.

## Quality Checks

- No large factual blocks remain in `skills/<skill_id>/SKILL.md`.
- Knowledge references point to `knowledge/` with `#xid-...`.
- The imported skill does not redefine the ambient context-direction guard.
- `xrefkit skill definition-check` rejects runtime routing fields and malformed
  SkillDefinition metadata.
- Skill inspection reports `block: 0` before import.
- `python -m xrefkit xref fix` reports `issues: 0`.

## Failure Handling

- If source skill mixes behavior and facts heavily:
  - split incrementally (first minimum runnable behavior, then extract knowledge pages)
- If references are unclear:
  - keep TODO markers in skill file and resolve with `xref search/show` before finalizing

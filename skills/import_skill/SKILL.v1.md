---
schema_version: 1
skill_id: import_skill
xid: D5A8C1E6B740
summary: inspect and import external Skill content while separating procedure from Knowledge and preserving inspection safety
applies_when:
- external skill needs to be made runnable in this repo
exclusions:
- Human acceptance or publication approval remains with the requester
- Unsupported facts, claims, or interpretation remain explicit as unknown
inputs:
- source URL or ZIP path, optional target skill id
outputs:
- Repository SkillDefinition v1 assets with external runtime/governance records; supported external legacy assets retain their split format; preserve the source procedure's other outputs and evidence.
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
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs: []
control_refs: []
aliases:
- 7C2A492D2B72
- 1DF4555E1B02
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

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Source-format and guard conflict

The split-file creation, metadata fields, role fields, index paths, and `--meta` validation in the historical procedure apply only when authoring the supported external legacy format. For adopted repository Skills, use the single-document required header and method in [SkillDefinition contract](../../docs/core/contracts/096_skill_definition_contract.md#xid-E6A19D4B72C3), and keep runtime/governance/observation records outside the definition header. Preserve the input, output, lifecycle, observation evidence, role boundary, and justified-maturity obligations.

The historical source declaration asking to compose the context-direction guard into each Skill contradicts the ambient startup delivery in [Context Direction Security Guard](../../docs/core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11). That declaration is retained for audit only and must not be executed; apply the already loaded shared guard. The source conflict is explicitly reported for review.

### Original Skill-specific procedure

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

### Original Skill-specific declarations

- summary: import external skill content into this repository split model

- use_when: external skill needs to be made runnable in this repo

- input: source URL or ZIP path, optional target skill id

- output: normalized `skills/<skill_id>/SKILL.md` and index registration

- constraints: keep domain facts out of skill body; use `knowledge/...#xid-...`; run policy inspection before import; compose the context-direction guard by default unless the imported skill explicitly qualifies for the closed-world exception

- tags: `import`, `normalization`, `xref`

- knowledge_slots:

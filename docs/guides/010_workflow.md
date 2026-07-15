<!-- xid: 7D1E1C0279F1 -->
<a id="xid-7D1E1C0279F1"></a>

# Repository Work and XID Maintenance Workflow

This guide summarizes the current repository-native work sequence and the XID
maintenance steps used when repository assets change. XID maintenance supports
the workflow; it is not the workflow by itself.

## Repository Work Sequence

1. Start from the active vendor startup file and load the repository-native
   [XRefKit startup contract](../core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22).
2. Apply the startup contract's base-control and xref-routing source set in the
   defined order. Do not discover startup context by recursively following
   `docs/` links or by bulk-loading `docs/000_index.md`.
3. Identify the user's goal and decide whether the task requires a Skill. If
   no Skill applies, use an instruction-backed workflow run and require explicit
   completion conditions or an explicit default-condition opt-in.
4. When a Skill is required, route semantically from `skills/_index.md` and the
   needed `skills/index/*` entries. Read candidate `meta.md` files only; do not
   open a candidate `SKILL.md` yet.
5. Open the selected Skill's runtime envelope before reading its procedure:

   ```powershell
   python -m xrefkit skill run --meta <path-to-meta.md> --task "<task>" --json
   ```

6. Read only the returned `skill_doc`. Use the assigned roles and returned
   `run_log` for work items, artifacts, concerns, phases, deterministic
   verification, handoff, and closure. In MCP mode, bind the returned `run_id`
   before task-specific XID access.
7. Resolve task-specific Knowledge or documents only when needed:

   ```powershell
   python -m xrefkit xref search "<query>"
   python -m xrefkit xref show <XID>
   ```

8. Record the work in `work/`. Before final completion, ensure the current task
   has a date-prefixed `work/sessions/` event log. Skill-backed work must also
   complete its runtime records, run `xrefkit skill verify`, and pass or
   explicitly escalate `xrefkit skill close`.

The full Skill runtime sequence is documented in
[Workflow Protocol Sequence For Humans](087_workflow_protocol_sequence_for_humans.md#xid-E8B4D2F19A63).

## Current Content Model

- `skills/` contains executable procedures and their meta identity.
- `knowledge/` contains shared evidence, facts, domain rules, and local rules.
- the generic workflow protocol wraps each Skill run or instruction-backed run
  and owns deterministic progression and closure checks.
- `work/` contains non-canonical execution records.
- `sources/` contains original materials retained for human verification.
- `tools/` and the `xrefkit` runtime provide deterministic operations.

Skill routing uses the capability / tuning / responsibility meta triad.

## Managed Markdown and XID Rules

- Keep the XID comment and anchor near the top of each managed Markdown file.
- Treat the XID as the reference identity. Cross-file links must include
  `#xid-<XID>`.
- Metadata and manifest references written as `path.md#xid-<XID>` are also
  path-validated and rewritten. Fenced examples are not rewritten.
- Preserve an existing XID when editing, renaming, moving, or splitting the
  document that retains the original meaning.
- Use a new XID when a page becomes a different semantic entity.
- Treat `docs/` links as lookup handles, not recursive loading instructions.

## XID Maintenance Commands

Use the narrow command that matches the change:

```powershell
# Assign XIDs to new managed Markdown files
python -m xrefkit xref init

# Rewrite XID-bearing paths after rename, move, split, or merge
python -m xrefkit xref rewrite

# Validate XIDs and managed links
python -m xrefkit xref check

# Show best-effort human review hints
python -m xrefkit xref check --review

# Run init + rewrite + check as one maintenance pass
python -m xrefkit xref fix
```

`xref check` and `xref fix` return exit code `1` when issues remain. Do not
treat the work as complete until relevant issues are resolved or explicitly
recorded as unverified.

## Common Document Operations

### Add a managed document

1. Add the file in the current canonical location (`docs/`, `agent/`,
   `knowledge/`, or `skills/`).
2. Follow nearby formatting, character encoding, and encoding-form conventions.
3. Run `python -m xrefkit xref init`.
4. Add XID-bearing references and run `python -m xrefkit xref check`.

### Rename or move

1. Preserve the existing XID block.
2. Move or rename the file.
3. Run `python -m xrefkit xref rewrite`.
4. Run `python -m xrefkit xref check`.

### Split

1. Keep the original XID in the page that retains the original semantic
   identity.
2. Give each new semantic fragment a new XID with `xref init`.
3. Rewire references, then run `xref rewrite` and `xref check`.

### Merge

1. Choose the surviving semantic identity; normally preserve the XID with the
   relevant inbound references.
2. Repoint references before removing the redundant page.
3. Remove it only after `xref check` reports no broken reference.

### Replace a page with a semantic successor

Do not reuse the old XID for a different meaning. Create a new page and record
the replacement relationship:

```powershell
python -m xrefkit xref deprecate <OLD_XID> <NEW_XID> --note "<reason>"
python -m xrefkit xref rewrite
python -m xrefkit xref check --review
```

### Ingest sources into Knowledge

1. Retain the original under `sources/` so humans can verify it.
2. Add or update focused XID-addressable fragments under `knowledge/` and cite
   their source basis.
3. Keep domain facts out of Skill procedure bodies.
4. Run the relevant deterministic validation and XID checks.

Details: [Sources](../reference/020_sources.md#xid-2FAD591BF725).

## Document Update Rule

Canonical documents describe the latest authoritative state only. Do not keep
obsolete alternatives or migration history in the target document. Git holds
previous document states; operational history belongs in the appropriate
`work/` record. See
[Document Update Policy](../policies/074_document_update_policy.md#xid-B1D42A6F90C3).

## Structured Source Files

- Preserve the existing formatting style, character encoding, and encoding
  form unless the task explicitly requires a controlled change.
- For XML, inspect the surrounding semantic grouping and insert new entries in
  the structurally appropriate location rather than appending mechanically.
- After editing XML, JSON, YAML, or another parseable format, run the project's
  deterministic parser, formatter, linter, compiler, or validator.
- Do not treat the edit as complete until the relevant validator reports no
  parse error.

### XML/JSON Parse-Validation Checklist

Use this checklist whenever an edit touches XML or JSON:

1. Confirm the file's existing formatting style, character encoding, and
   encoding form before editing.
2. For XML, inspect the surrounding semantic grouping and insert new entries
   where the existing structure indicates, not automatically at the end.
3. Apply the minimal change needed; avoid unrelated reformatting or reordering.
4. Run a deterministic parser, formatter, linter, compiler, or validator
   appropriate to the file.
5. Confirm the parser or validator reports no error.
6. If the validator rewrites output, confirm the resulting file still follows
   the repository's existing formatting conventions.
7. If parse validation cannot be executed, record that fact explicitly and
   treat the work as incomplete.

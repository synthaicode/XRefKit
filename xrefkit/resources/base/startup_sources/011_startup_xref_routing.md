<!-- xid: 6C0B62D6366A -->
<a id="xid-6C0B62D6366A"></a>

# Startup Xref Routing Policy

This page defines the shared xref routing policy for startup behavior across
vendor-specific startup files (Copilot, Claude, Devin/AGENTS, Cursor, ChatGPT,
etc.).

For the XRefKit repository-native startup target, use
`docs/core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22`.

For the concrete sequence reference, use
`docs/core/contracts/077_initialization_sequence.md#xid-A264E296AC71`.

## Startup Sequence

XRefKit repository-native startup target is defined by
`docs/core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22`.

Startup order is defined by
`docs/core/contracts/077_initialization_sequence.md#xid-A264E296AC71`.
Use that page for the concrete MCP and filesystem fallback sequence.

`docs/000_index.md` is a table of contents for lookup and human orientation. It
is not part of the mandatory startup read path.

## Shared Policy

- Apply base AI control rules before repository-specific xref routing; the
  layer boundary is defined in
  `docs/core/models/017_base_and_xref_layering.md#xid-5A1C8E4D2F90`.
- Manage skill definitions and domain knowledge as separate files.
- Treat domain knowledge in `knowledge/` as shared/common.
- A Skill's capability/tuning/responsibility is its meta identity and the routing vocabulary.
- When updating repository documents, apply the document update policy in
  `docs/policies/074_document_update_policy.md#xid-B1D42A6F90C3`: target
  documents describe the latest authoritative state; prior document states stay
  in Git history, and operational history goes to the appropriate `work/`
  record when needed.
- Each skill reads only what it needs, on demand, via `xref`.
- Treat `skills/_index.md` as the canonical skill catalog for listing/routing skills.
- Select the target Skill by semantic routing from user intent, available fragments, and routing indexes before opening any specific Skill.
- For business-intake requests where structure is still incomplete, prefer learning-first routing:
  - first `business_learning_interview`
  - then `business_intake_scoping` only after the business unit becomes scope-ready
- Treat direct `--meta <path>` selection as an execution detail after routing, not as the normal human-facing routing method.
- When a task uses a Skill, start it through the runtime envelope defined in
  `docs/core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61`
  before opening or executing `SKILL.md`.
- Route to the target Skill by semantic routing from user intent and the Skill
  catalog (capability/tuning/responsibility triad); there is no separate
  capability-routing model.
- When a task or skill needs domain knowledge, route via:
  - `python -m xrefkit xref search "<query>"`
  - `python -m xrefkit xref show <XID>`
- Keep references XID-based (`#xid-...`) and keep existing XID blocks unchanged.
- Treat cross-references in `docs/` as navigation metadata, not as recursive
  load instructions. Do not follow transitive document links at startup or
  Skill load time unless the current task explicitly needs that target
  fragment.
- After edits, run `python -m xrefkit xref fix`.

## Execution Environment

This repository is developed on **Windows**, where the default shell is
**PowerShell**. Do not assume a POSIX / Bash shell.

- Bash-only syntax fails on the default shell and triggers retry loops that silently
  inflate token cost (each retry re-transmits the whole conversation plus the error).
  Do not assume: `&&` / `||` (unsupported in PowerShell 5.1), `export`, `/dev/null`,
  `ls -la`, or inline `VAR=value cmd`.
- Use PowerShell equivalents (`$env:VAR = 'x'`, `2>$null`, `Get-ChildItem -Force`),
  or run a Bash-compatible shell explicitly (Git Bash / WSL) when POSIX syntax is
  needed — and keep every command in the syntax of the shell it actually runs in.
- If the agent can pin its terminal, prefer one known shell (for example Git Bash)
  so the model's shell habits match the environment.
- This is a token-cost control; metric terms are defined in
  `knowledge/organization/120_metrics_definition.md#xid-7A2F4C8D1201`.

## Lookup Index

Use `docs/000_index.md#xid-56DD6EB68343` when a task needs a specific document
outside the startup path. Index entries are lookup handles, not additional
startup load requirements.



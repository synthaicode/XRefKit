<!-- xid: D0E1327DDD7F -->
<a id="xid-D0E1327DDD7F"></a>

# Repository Structure (Human View)

This page describes the top-level directory layout only.
For the repository purpose and operating model, see [Overview](000_overview.md#xid-7C6C2B46A9D1).

## Top-level directories

- `docs/`: Human-facing docs; root contains only entry and repository-wide orientation pages
  - `docs/core/contracts/`: Normative OS-core contracts loaded or enforced at runtime
  - `docs/core/models/`: Stable OS-core layering and responsibility models
  - `docs/packs/<pack-id>/`: Pack-owned entries, guides, workflows, and dependency designs
  - `docs/workflows/`: Shared human-facing workflow pages and their page schema
  - `docs/guides/`: Human-facing usage, orientation, and migration guides
  - `docs/operating-models/`: Human-facing team and function operating models
  - `docs/designs/`: System, migration, decomposition, and integration design documents
  - `docs/policies/`: Explicit repository policies
  - `docs/quality/`: Cross-workflow quality assurance and feedback mechanism pages
  - `docs/reference/`: Reference definitions, source handling, naming conventions, matrices, and baselines
  - `docs/assets/`: Shared non-Markdown documentation assets such as diagrams and PDFs
- `flows/`: Machine-readable workflow control structures in YAML
- `capabilities/`: Reusable capability definitions (inputs, outputs, triggers, constraints)
- `agent/`: Agent entry + operational contract (keep L0 short and stable)
- `fm/`: CLI implementation (`python -m fm ...`)
- `knowledge/`: Shared domain knowledge fragments
- `skills/`: Executable procedures and routing index
- `sources/`: Original materials (PDF/Excel/Web snapshots, etc.) kept in-repo for human review
- `.github/`: GitHub control plane (Copilot instructions, prompts, CI)
- `.cursor/`: Cursor rules

## Generated artifacts / caches

- `.xref/`: Generated artifacts (e.g., `.xref/xid-index.json`, `ctx pack` outputs)
  - This is workspace state and is typically not committed (gitignored)

## Entry points

- Human entry: `docs/000_index.md`
- Agent entry: `agent/000_agent_entry.md`

## Representative startup files

- `README.md`: Project summary and basic usage
- `CLAUDE.md`: Claude Code contract (optional)
- `AGENTS.md`: Devin contract (optional)
- `.github/copilot-instructions.md`: GitHub Copilot instructions (optional)

## Minimal tree

```text
.
├─ docs/          # Human-facing docs (XID-managed)
│  ├─ core/       # Explicit OS-core contracts and models
│  ├─ packs/      # Pack-owned documentation grouped by pack id
│  ├─ workflows/  # Shared workflow documentation and schema
│  ├─ guides/     # Human-facing usage and migration guidance
│  ├─ operating-models/ # Team and function operating models
│  ├─ designs/    # System and integration design documents
│  ├─ policies/   # Explicit repository policies
│  ├─ quality/    # Cross-workflow quality assurance and feedback mechanisms
│  ├─ reference/  # Definitions, conventions, matrices, and baselines
│  └─ assets/     # Non-Markdown documentation assets
├─ flows/         # Workflow YAML models
├─ capabilities/  # Capability definitions (XID-managed)
├─ agent/         # Agent entry/contract (XID-managed)
├─ fm/            # CLI implementation
├─ knowledge/     # Shared domain knowledge
├─ skills/        # Executable skills
├─ sources/       # Original materials (PDF/Excel/Web)
├─ .github/       # Copilot/CI
├─ .cursor/       # Cursor rules
└─ .xref/         # Generated artifacts/caches (gitignored)
```

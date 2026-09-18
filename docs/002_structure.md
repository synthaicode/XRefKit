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
  - `docs/guides/`: Human-facing usage, orientation, and migration guides
  - `docs/designs/`: System, migration, decomposition, and integration design documents
  - `docs/policies/`: Explicit repository policies
  - `docs/reference/`: Reference definitions, source handling, naming conventions, matrices, and baselines
  - `docs/presentations/`: Shareable presentation artifacts such as PowerPoint decks
- `agent/`: Agent entry + operational contract (keep L0 short and stable)
- `xrefkit/`: installable runtime, CLI, resolver, tools registry, and MCP adapter
- `knowledge/`: Shared domain knowledge fragments
- `skills/`: Executable procedures and routing index
- `observations/`: Tracked Skill maturity and governance evidence
- `packages/`: Installable Skill and Knowledge package sources
- `projects/`: Executable subprojects governed by the project quality baseline
- `tools/`: Deterministic analysis, maintenance, and quality utilities
- `tests/`: Runtime, CLI, MCP, and contract verification
- `work/`: Non-canonical session logs, judgments, drafts, and handoffs
- `human-docs/`: Human-language publication trees derived from canonical assets
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
│  ├─ guides/     # Human-facing usage and migration guidance
│  ├─ designs/    # System and integration design documents
│  ├─ policies/   # Explicit repository policies
│  ├─ reference/  # Definitions, conventions, matrices, and baselines
│  └─ presentations/ # Shareable presentation artifacts
├─ agent/         # Agent entry/contract (XID-managed)
├─ xrefkit/       # installable runtime and integrated MCP adapter
├─ knowledge/     # Shared domain knowledge
├─ skills/        # Executable skills
├─ observations/  # Tracked maturity/governance evidence
├─ packages/      # Installable Skill/Knowledge packages
├─ projects/      # Executable subprojects
├─ tools/         # Deterministic utilities and quality checks
├─ tests/         # Runtime and contract verification
├─ work/          # Non-canonical operational records
├─ human-docs/    # Human-language publication trees
├─ sources/       # Original materials (PDF/Excel/Web)
├─ .github/       # Copilot/CI
├─ .cursor/       # Cursor rules
└─ .xref/         # Generated artifacts/caches (gitignored)
```

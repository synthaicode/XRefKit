<!-- xid: D0E1327DDD7F -->
<a id="xid-D0E1327DDD7F"></a>

# Repository Structure (Human View)

This page describes the top-level directory layout only.
For the repository purpose and operating model, see [Overview](000_overview.md#xid-7C6C2B46A9D1).

## Top-level directories

- `docs/`: Human-facing docs (background, design, operations, indexes)
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

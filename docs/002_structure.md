<!-- xid: D0E1327DDD7F -->
<a id="xid-D0E1327DDD7F"></a>

# Repository Structure (human view)

This repository provides the operational pattern and tooling to reference split documents by XID and prevent link breakage after rename/move/split/merge.

## Top-level directories

- `docs/`: Human-facing docs (background, design, operations, indexes)
- `agent/`: Agent entry + operational contract (keep L0 short and stable)
- `fm/`: CLI implementation (`python -m fm ...`)
- `sources/`: Original materials (PDF/Excel/Web snapshots, etc.) kept in-repo for human review
- `.github/`: GitHub control plane (Copilot instructions, prompts, CI)
- `.cursor/`: Cursor rules

## Generated artifacts / caches

- `.xref/`: Generated artifacts (e.g., `.xref/xid-index.json`, `ctx pack` outputs)
  - This is workspace state and is typically not committed (gitignored)

## Entry points

- Human entry: `docs/000_index.md`
- Agent entry: `agent/000_agent_entry.md`

## Representative files

- `README.md`: Project summary and basic usage
- `CLAUDE.md`: Claude Code contract (optional)
- `AGENTS.md`: Devin contract (optional)
- `.github/copilot-instructions.md`: GitHub Copilot instructions (optional)

## Minimal tree

```text
.
├─ docs/          # Human-facing docs (XID-managed)
├─ agent/         # Agent entry/contract (XID-managed)
├─ fm/            # CLI implementation
├─ sources/       # Original materials (PDF/Excel/Web)
├─ .github/       # Copilot/CI
├─ .cursor/       # Cursor rules
└─ .xref/         # Generated artifacts/caches (gitignored)
```

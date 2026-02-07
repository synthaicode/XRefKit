# XRefKit

XRefKit is an OSS knowledge-ops toolkit for sharing knowledge with AI.

It keeps original sources (PDF/Excel/Web snapshots, etc.) in-repo, and maintains an AI-readable knowledge base as small Markdown “fragments”. Cross-document references use stable IDs (**XIDs**) so links keep working across rename/move/split/merge operations.
In this architecture, `xref` is a supporting feature: the primary goal is to connect skills/agents with the right domain knowledge fragments in `knowledge/`.

## Entry Points

- Human entry: `docs/000_index.md`
- Agent contract (always read): `agent/000_agent_entry.md`

Vendor startup files should stay minimal: show how to load domain knowledge via `xref`, and centralize all detailed policy in the entry points above.

## Quick Start

```powershell
# 1) Validate Python environment
python --version

# 2) Run one-shot maintenance
python -m fm xref fix

# 3) Find and open relevant knowledge fragments
python -m fm xref search "your query"
python -m fm xref show 1A2B3C4D5E6F
```

If `xref fix` reports issues, fix them first before editing links manually.

## Why XIDs

When knowledge is split across many files, links break easily. XRefKit treats the `#xid-...` fragment as the primary key and rewrites only the *path* portion when files move.

Each managed Markdown file carries an XID block:

```md
<!-- xid: 1A2B3C4D5E6F -->
<a id="xid-1A2B3C4D5E6F"></a>
```

## Typical Workflow

1. Add or update source material in `sources/`.
2. Convert key points into Markdown fragments under `docs/` or `knowledge/`.
3. Keep references XID-based (`#xid-...`), not path-based.
4. Run `python -m fm xref fix` after edits.
5. Use `xref search/show` or `ctx pack` to load only the needed context.

## Why XRefKit (beyond links)

- **Multi-agent consistency via normalization**: keep domain knowledge in one canonical place (`knowledge/`), and have agent/tool instructions point to it by XID.
- **Loose coupling of instructions**: keep “how to behave” small and stable, and fetch “what to know” on demand (`xref search/show`, `ctx pack`).
- **Human+AI shared knowledge base**: keep originals in `sources/` for human verification, and maintain AI-readable fragments in `docs/` with stable references.
- **Skill-driven execution**: manage diverse reusable skills in `skills/` and route from `skills/_index.md`.
- **Traceable decision history**: share AI execution logs in `work/` so others can follow decisions and handovers.
- **Critical caveat**: changing an XID is a semantic decision (what the ID *means*). Treat it as human-reviewed, and use `xref deprecate` to keep old links valid.

## Commands

```powershell
# Add/replace missing XIDs
python -m fm xref init

# Rewrite managed links that contain #xid-... to correct relative paths
python -m fm xref rewrite

# Validate XIDs and managed links
python -m fm xref check

# One-shot maintenance (init + rewrite + check)
python -m fm xref fix

# Human-review hints (best-effort)
python -m fm xref check --review

# Search and read only what you need
python -m fm xref search "query"
python -m fm xref show 1A2B3C4D5E6F

# Build a small context pack (seed + neighbors)
python -m fm ctx pack --seed 7C6C2B46A9D1 --depth 1 --out .xref\\pack.md
```

`python -m fm xref check` and `python -m fm xref fix` return exit code `1` when issues are found, so they can fail CI correctly.

## Repository Map

- `docs/`: human-facing operational docs and policy
- `knowledge/`: shared domain knowledge fragments
- `sources/`: original source material for human verification
- `skills/`: skill definitions and routing index (`skills/_index.md`)
- `work/`: AI-authored execution logs and retrospectives for traceability
- `agent/`: agent entry and contract
- `fm/`: CLI implementation (`xref`, `ctx`)

# XRefKit

XRefKit is a toolkit for making domain knowledge referenceable, traceable, and maintainable for AI-assisted work.

▶️ Watch the 2-minute overview: [Why XRefKit exists and how it helps AI teams use domain knowledge](en/docs/video/063_ai_organization_explainer_clear/ai_team_explainer_clear_en_azure.mp4)

XRefKit is not only a document repository or a link-maintenance tool.
It is an information architecture for controlled AI work.

The repository is designed so AI can load only the knowledge it needs,
follow explicit work boundaries, and remain auditable by humans.

Its core model separates flow, capability, skill, knowledge, and stable XID-based references
so AI behavior, knowledge access, and work responsibility do not collapse into one layer.

XRefKit is an OSS knowledge-ops toolkit for sharing knowledge with AI.
Reading the repository does not require Python, but the standard operational commands in `fm/`
such as `python -m fm xref ...` require a local Python runtime.

It keeps original sources (PDF/Excel/Web snapshots, etc.) in-repo, and maintains an AI-readable knowledge base as small Markdown “fragments”. Cross-document references use stable IDs (**XIDs**) so links keep working across rename/move/split/merge operations.
Originally, the visible center of this repository was XID-based link durability.
Now, the repository should be understood more broadly as an operating base for controlled AI work:

- base AI control rules
- repository-specific knowledge routing
- stable knowledge references
- reusable work structure for skills, capabilities, and workflows

In this architecture, `xref` is a supporting feature. The primary goal is to connect agents and skills with the right domain knowledge fragments in `knowledge/` under explicit operating rules.

## Entry Points

- Human entry: `docs/000_index.md`
- Agent contract (always read): `agent/000_agent_entry.md`

Use `README.md` for a short external-facing introduction.
Use `docs/000_index.md` for the detailed internal documentation map.

Vendor startup files should stay minimal: show how to load domain knowledge via `xref`, and centralize detailed policy in the entry points above.

## What This Repository Manages

This repository is not just a link-maintenance tool.
It manages the minimum structure needed for AI to work in a stable, reviewable way.

That structure includes:

- operating rules for how AI should behave
- repository-specific knowledge loading rules
- reusable workflow, capability, and skill boundaries
- source-backed knowledge fragments with stable references

In practice, this means the repository now treats AI contract and control rules as first-class assets, not just auxiliary notes around XID management.

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

## Minimal Workflow

1. Add or update source material in `sources/`.
2. Convert workflow control structure into `flows/`, workflow/governance explanation into `docs/`, capability definitions into `capabilities/`, and domain facts into `knowledge/`.
3. Keep references XID-based (`#xid-...`), not path-based.
4. Run `python -m fm xref fix` after edits.
5. Use `xref search/show` or `ctx pack` to load only the needed context.

For the broader repository reading order and policy map, start from `docs/000_index.md`.

## Why XRefKit (beyond links)

- **AI operating contract**: keep base control rules such as startup behavior, uncertainty handling, logging expectations, and context-boundary control explicit in the repository.
- **Multi-agent consistency via normalization**: keep domain knowledge in one canonical place (`knowledge/`), keep reusable work-unit definitions in `capabilities/`, and have agent/tool instructions point to them by XID.
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
- `flows/`: machine-readable workflow control structures
- `capabilities/`: reusable capability definitions
- `knowledge/`: shared domain knowledge fragments
- `sources/`: original source material for human verification
- `skills/`: skill definitions and routing index (`skills/_index.md`)
- `work/`: AI-authored execution logs and retrospectives for traceability
- `agent/`: agent entry and contract
- `fm/`: CLI implementation (`xref`, `ctx`)

For explanations of these areas, use:

- `docs/000_overview.md`
- `docs/002_structure.md`
- `docs/000_index.md`

## Current Positioning

If you read this repository today, the main value is not only that links survive file movement.
The main value is that AI behavior, knowledge loading, work structure, and traceability are made explicit in one place.

XID durability remains important, but it supports that larger goal.

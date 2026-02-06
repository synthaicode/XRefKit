<!-- xid: 7C6C2B46A9D1 -->
<a id="xid-7C6C2B46A9D1"></a>

# Overview

This repository is a workspace for building an AI/human collaborative “knowledge operations” system: keep original sources in-repo, extract AI-readable fragments, and keep references stable as the docs evolve.

## The core problem

- Agent design forces documents to be split (context limits)
- Human-facing explanation (`docs/`) and agent-facing instructions (`agent/`) need different granularity
- With many files, links break easily during split/merge/move/delete

## Approach: reference by XID

References treat the **XID** as the primary key.

- Each managed Markdown file has an XID
- Managed links include `#xid-<XID>`
- After rename/move, `python -m fm xref rewrite` updates only the *path* portion of managed links

## Positioning: xref is a supporting feature

The primary value of this repository is to **connect each skill to domain knowledge fragments in `knowledge/`**.
`xref` is intentionally a supporting capability that keeps those connections durable.

- Separation rule: keep skill files and domain-knowledge files separate.
- Shared knowledge rule: `knowledge/` is common domain knowledge across skills.
- Primary: skills select and consume the right knowledge fragments for the task
- Supporting: `fm xref` maintains IDs, link paths, and breakage checks
- Outcome: skill-to-knowledge wiring stays stable even when tools or agents change

## What it means for AI to “manage XIDs”

It does **not** mean the AI invents IDs. It means the AI (or CI) uses `fm` commands to keep the system consistent.

- `python -m fm xref init` assigns/replaces XIDs (AI runs it and interprets results)
- Run `init` / `rewrite` / `check` until `issues: 0`
- If you want a lookup file, regenerate it only when XIDs change

## Minimal repository layout

- `docs/`: Human-facing docs (background, design, operations)
- `knowledge/`: Shared domain knowledge fragments (XID-managed)
- `skills/`: Skill definitions (behavior/procedure, references to XIDs)
- `work/`: AI-authored retrospectives and handover logs (non-canonical)
- `agent/`: Agent entry + contract (keep L0 short and stable)
- `fm/`: CLI implementation (`python -m fm ...`)
- `sources/`: Original materials (PDF/Excel/Web snapshots, etc.) for human review
- `.github/`: GitHub-side “control plane” (Copilot instructions, prompts, CI)

## Tool integrations (examples)

Keep vendor startup files minimal (`xref` route + central links), and centralize detailed policy in `docs/` + `agent/`.
Shared startup policy: [Startup xref routing policy](011_startup_xref_routing.md#xid-6C0B62D6366A)

- GitHub Copilot: `.github/copilot-instructions.md`
- Claude Code: `CLAUDE.md`
- Devin: `AGENTS.md`
- ChatGPT: `CHATGPT.md`
- Cursor: `.cursor/rules/*.mdc`

## Common commands

```powershell
python -m fm xref init
python -m fm xref rewrite
python -m fm xref check
python -m fm xref check --review

python -m fm xref search "query"
python -m fm xref show 1A2B3C4D5E6F

python -m fm xref index > .xref/xid-index.json
```

`.xref/` is for generated artifacts and caches (gitignored). XRefKit also uses `.xref/xid-index.json` as an index cache to avoid rescanning when nothing changed.

Workflow: [Workflow](010_workflow.md#xid-7D1E1C0279F1)

Agent entry: [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)

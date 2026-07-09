# XRefKit

AI agents often stop halfway, guess missing context, or produce work that looks
plausible but cannot be reviewed or handed off.

XRefKit is a portable Python package and repository model for AI-assisted work
that must reproduce domain procedures and judgments.

It runs as its own control repository and helps AI agents:

- load the right knowledge before acting
- select reusable Skills
- record judgments and evidence
- preserve handoffs across humans, agents, and sessions
- close work only through explicit quality gates

The package provides XID resolution, compact runtime contracts, Skill execution,
catalog-first context loading, deterministic closure gates, client-side tools,
and a thin MCP adapter over the same rules.

▶️ Download the 2-minute overview: [Why XRefKit exists and how it helps AI teams use domain knowledge](https://raw.githubusercontent.com/synthaicode/XRefKit/main/readme.mp4)

## Security and API Keys

XRefKit does not require Claude, OpenAI, GitHub, or other provider API keys to explore the repository.

This repository is a governance and knowledge-operations framework for AI-assisted work. It does not ask users to paste API keys into the repository, issue trackers, prompts, or configuration files.

If you use XRefKit with an external AI agent such as Claude Code, Codex, or GitHub Copilot, authenticate that agent through the official provider mechanism outside this repository.

Do not commit secrets, API keys, access tokens, `.env` files, or provider credentials to this repository.

XRefKit does not include repository-managed Claude settings, hooks, MCP server auto-approval, or provider endpoint redirection.

Before running any AI agent in this repository, review agent startup files and tool settings. XRefKit treats repository-controlled agent configuration as part of the trust boundary.

## The Problem

Using AI for real work creates recurring operating problems:

![Why XRefKit is needed](human-docs/en/assets/why_xrefkit_needed/whatis_xrefkit.png)

- the AI can act from incomplete context or unsupported guesses
- procedures, domain facts, and judgment criteria get mixed together in prompts
- execution, checking, and handoff collapse into one opaque step
- work becomes hard to continue across agents, humans, or sessions
- outputs may lack evidence, closure discipline, or auditability

## What XRefKit Provides

XRefKit makes AI work explicit by separating:

- Skills: executable work units, each identified by a capability/tuning/responsibility triad and carrying its execution and check contract
- Knowledge: source-backed domain facts and local rules loaded only when needed
- Workflow protocol: the generic, deterministic per-Skill control (phases, verification, closure) that wraps every Skill run
- Semantic routing: selecting the right Skill for a goal from user intent and the Skill catalog
- Evidence: logs, judgments, concerns, and quality checks
- XIDs: stable references that survive file movement and restructuring so AI can load targeted context without treating the whole repository as one prompt

This separation prevents prompts, domain facts, execution steps, review criteria,
and handoff records from collapsing into one opaque instruction block.

![XRefKit repository snapshot](human-docs/en/assets/xrefkit_repository_snapshot/xrefkit_repository_snapshot.png)

## How It Works

1. Original materials are kept in `sources/`.
2. AI-readable knowledge is maintained in `knowledge/`.
3. Work is defined in `skills/` (executable procedure with a capability/tuning/responsibility identity) and `knowledge/`.
4. Agents are routed semantically to the right Skill and load only the relevant context.
5. Evidence and quality gates make incomplete or unsupported work visible.

## Quick Start

Install the package and initialize an instance:

```powershell
python -m pip install -e .
xrefkit init
xrefkit --help
```

Start the integrated MCP server over stdio:

```powershell
xrefkit mcp serve --repo . --transport stdio
```

XRefKit is designed to be driven by an AI agent. The agent first resolves the
startup contract XID, selects a Skill or source target from a compact catalog,
and expands only the selected body.

Here, `sources/` is the human drop point for original materials, existing Skill artifacts, rules, and examples that the AI will turn into repository-managed assets.

If you are migrating an existing Skill:

1. Place the source Skill or related source materials in `sources/`.
2. Ask the AI agent to migrate that Skill into the XRefKit repository model.
3. Have the migration process separate procedure, source-backed knowledge, and runtime structure as needed.
4. Review whether the migrated Skill is usable for the intended work.

If you are creating a new Skill:

1. Place the source materials, rules, or task examples in `sources/`.
2. Ask the AI agent to use the Skill authoring flow (`skill_flow_authoring`) to create a new Skill.
3. Have the authoring process separate procedure, source-backed knowledge, and runtime structure as needed.
4. Review whether the new Skill is usable for the intended work.

In both cases:

1. Give the AI agent a concrete work request with the goal, expected output, and constraints.
2. Inspect `work/` records as operational memory, then refine the Skill, knowledge, guard conditions, routing rules, and quality gates based on what happened.

## How to Explore This Repository

Point your AI agent at this repository and ask directly.

Startup instruction files for Claude, Codex, and GitHub Copilot are included.

These files are plain-text operating instructions. They do not contain API keys, provider credentials, hooks, MCP server definitions, or network redirection settings.

The agent can read the operating contract and explain the repository structure in context.

## Repository Map

- `xrefkit/`: installable runtime, resolver, Skill control, tools registry, and MCP adapter
- `docs/`: human-facing docs and policy
- `knowledge/`: source-backed knowledge fragments
- `sources/`: original materials for verification
- `skills/`: Skill definitions and routing index
- `tools/`: XID-backed client-side command implementations and packaged assets
- `work/`: operational memory for execution logs, judgments, handoffs, retrospectives, and improvement input
- `agent/`: agent entry and operating contract
- `human-docs/`: human-facing Japanese and English docs, materials, assets, and video packages
- `site/`: generated publication output, source manifest, and compatibility routes

## Runtime and Context Model

- Base runtime obligations are authored structurally and compiled into package resources with source hashes and token budgets.
- Repository, installed-package, and MCP providers resolve the same XID identities; conflicts and stale base packs fail explicitly.
- Source structure is split into a target catalog and finding catalog. The AI loads lists before selected details.
- `xrefkit catalog maintain --apply-safe` promotes only unambiguous candidate findings; conflicts remain in a review queue.
- MCP exposes the shared resolver and catalogs. It does not own independent domain rules or execute client tools.

## Entry Points

- Human documentation: `docs/000_index.md`
- Human-facing language trees: `human-docs/ja/000_index.md`, `human-docs/en/`
- Agent entry: `agent/000_agent_entry.md`

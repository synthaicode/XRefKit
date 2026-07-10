<!-- xid: 7C6C2B46A9D1 -->
<a id="xid-7C6C2B46A9D1"></a>

# Overview

This repository is a workspace for building a repository-based AI Agent OS:
keep original sources in-repo, extract AI-readable fragments, and keep
references stable as the docs evolve.

Here, OS means an operating layer for controlled AI Agent work, not a
low-level system OS or an LLM runtime.

Originally, the most visible mechanism in this repository was XID-based reference durability.
The current repository should be understood more broadly as a controlled AI
work base:

- explicit AI operating rules
- repository-specific knowledge routing
- reusable Skill and Knowledge structure
- stable references across evolving knowledge assets

For the explicit reorganization direction, see
[AI Agent OS Reorganization Design](designs/063_ai_agent_os_reorganization_design.md#xid-22CAE81A6D3E).

## The core problem

- Agent design forces documents to be split (context limits)
- Human-facing explanation (`docs/`) and agent-facing instructions (`agent/`) need different granularity
- With many files, links break easily during split/merge/move/delete
- Capable models still need explicit control over boundary, uncertainty, and knowledge loading

## Approach: reference by XID

References treat the **XID** as the primary key.

- Each managed Markdown file has an XID
- Managed links include `#xid-<XID>`
- After rename/move, `python -m xrefkit xref rewrite` updates only the *path* portion of managed links

## Positioning: xref is a supporting feature

The primary value of this repository is to **connect each skill to domain knowledge fragments in `knowledge/`**.
`xref` is intentionally a supporting capability that keeps those connections durable.

- Separation rule: keep skill files and domain-knowledge files separate.
- Shared knowledge rule: `knowledge/` is common domain knowledge across skills.
- Primary: skills select and consume the right knowledge fragments for the task
- Supporting: `xrefkit xref` maintains IDs, link paths, and breakage checks
- Outcome: skill-to-knowledge wiring stays stable even when tools or agents change

In operating-model terms, this wiring is the OS's nervous system: `xref` is how
the OS delivers `knowledge/` fragments to the task (作業) that needs them. See
[Operating model: the OS drives business through tasks](#operating-model-the-os-drives-business-through-tasks)
below.

The repository therefore manages more than link stability:

- base AI control rules
- knowledge-loading rules
- work-structure boundaries
- durable references for the knowledge layer

## Internal layering

This repository intentionally keeps two layers together:

- base control: common AI behavior control such as guard, uncertainty handling, and startup contract
- xref routing: XRefKit-specific knowledge loading and reference management

See [Base control and xref routing layers](core/models/017_base_and_xref_layering.md#xid-5A1C8E4D2F90) for the exact boundary.

As the repository is reorganized toward a clearer AI Agent OS shape, those
layers should be treated as an operating core rather than as only
documentation structure.

## Operating model: the OS drives business through tasks

Read together, those layers are the **OS**: base control plus xref routing form
the operating core that **drives business work (業務)**. The OS behaves like the
nervous system that carries control and knowledge to where work actually happens.

The operating model has four levels:

1. **OS** (base control + xref routing): routing, load gating,
   execution/check separation, closure, audit, and `xref` durability. The OS
   *executes business work*; it does not host detachable "apps".
2. **Business (業務)**: a work domain (for example, C# code review). A business
   is a **bundle of tasks** and requires domain knowledge to carry out. It is
   expressed as a Business Pack (Skills + Knowledge).
3. **Task (作業)**: a single work unit, done efficiently with a fit-for-purpose
   tool. A task reaches the domain knowledge it needs through **XID**.
4. **Tools (`tools/`)**: task-specialized determinism — a shared deterministic
   primitive layer (like syscalls/libc). Both the OS control plane and business
   tasks call into it; it is not partitioned by which layer calls a tool.

Domain knowledge lives in `knowledge/`, and `xref`/XID is how the OS makes that
knowledge reachable and usable by the right task. This is why `xref` is not a
side feature: it is the conduit the OS uses to deliver knowledge to work.

### Reuse established knowledge and tools

The same principle applies at every level: **reuse established external authority
instead of homegrown invention.**

- **Business (業務)** is defined *from existing, established domain knowledge*
  (industry standards and established practice — for ITSM, for example, ITIL,
  ISO/IEC 20000, CAB). This prevents reinventing the wheel and suppresses flawed
  self-styled (自己流) processes that bake defects into the design itself.
- A **task (作業)** splits into a deterministic part and a non-deterministic part.
  Push as much as possible into the deterministic part and, for it, **prefer
  reusing established OSS over building bespoke tools** (reuse-before-build, as
  with Roslyn + SARIF). Reserve the non-deterministic part for genuine LLM
  judgment only.

Both are the same move: validated external authority carries fewer defects, so it
needs less rework. Self-styled approaches embed defects at the design root, which
is far cheaper to prevent upstream than to recover through downstream gates. This
fits the source-backed knowledge model (`sources/` → `knowledge/`; see
[Sources](reference/020_sources.md#xid-2FAD591BF725)).

### Control is the source of efficiency

The OS is optimized for **efficient task processing**, where efficiency means
**minimizing rework, re-execution, and audit failure**. Control and quality
gates are therefore kept and strengthened, not treated as overhead — they are
how work stays efficient. The through-line at every level is **determinism**:
deterministic checks at the OS level (`xrefkit skill verify`,
`tools/run_quality_gate.py`) and deterministic tools at the task level (the
`tools/` extractors) make output reproducible, which removes rework and keeps
work auditable. Determinism is both the efficiency mechanism and the control
mechanism.

## What it means for AI to “manage XIDs”

It does **not** mean the AI invents IDs. It means the AI (or CI) uses `fm` commands to keep the system consistent.

- `python -m xrefkit xref init` assigns/replaces XIDs (AI runs it and interprets results)
- Run `init` / `rewrite` / `check` until `issues: 0`
- If you want a lookup file, regenerate it only when XIDs change

## Minimal repository layout

- `docs/`: Human-facing docs (background, design, operations)
- `knowledge/`: Shared domain knowledge fragments (XID-managed)
- `skills/`: Skill definitions (behavior/procedure, references to XIDs)
- `work/`: AI-authored operational memory for sessions, judgments,
  retrospectives, and handover logs (non-canonical)
- `agent/`: Agent entry + contract (keep L0 short and stable)
- `xrefkit/`: installable runtime, CLI, resolver, tools registry, and MCP adapter
- `sources/`: Original materials (PDF/Excel/Web snapshots, etc.) for human review
- `.github/`: GitHub-side “control plane” (Copilot instructions, prompts, CI)

## Tool integrations (examples)

Keep vendor startup files minimal (`xref` route + central links), and centralize detailed policy in `docs/` + `agent/`.
XRefKit startup target: [XRefKit startup contract](core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22)
Shared xref routing policy: [Startup xref routing policy](core/contracts/011_startup_xref_routing.md#xid-6C0B62D6366A)

- GitHub Copilot: `.github/copilot-instructions.md`
- Claude Code: `CLAUDE.md`
- Devin: `AGENTS.md`
- ChatGPT: `CHATGPT.md`
- Cursor: `.cursor/rules/*.mdc`

## Common commands

```powershell
python -m xrefkit xref init
python -m xrefkit xref rewrite
python -m xrefkit xref check
python -m xrefkit xref check --review

python -m xrefkit xref search "query"
python -m xrefkit xref show 1A2B3C4D5E6F

python -m xrefkit xref index > .xref/xid-index.json
```

`.xref/` is for generated artifacts and caches (gitignored). XRefKit also uses `.xref/xid-index.json` as an index cache to avoid rescanning when nothing changed.

`work/` is not only an audit trail.
It is operational memory used to improve Skills, Knowledge, guard policies,
routing rules, and quality gates after execution.

Workflow: [Workflow](guides/010_workflow.md#xid-7D1E1C0279F1)

Agent entry: [Agent Entry](../agent/000_agent_entry.md#xid-0B5C58B5E5B2)

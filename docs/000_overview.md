<!-- xid: 7C6C2B46A9D1 -->
<a id="xid-7C6C2B46A9D1"></a>

# Overview

XRefKit is a repository-based operating layer for controlled AI work. It
connects an instruction to an appropriate reusable method, supplies only the
Knowledge needed for the current judgment, records what execution actually
observed, and leaves adoption of consequential results to an accountable
human.

The repository manages more than durable links. It manages the boundaries
between procedure, Knowledge, evidence, runtime authority, execution, and
canonical change.

## The judgment-material path

The core problem is resolving the material needed for a judgment without
confusing availability with authority. A user request may require a Skill
procedure, domain Knowledge, external evidence, deterministic tools, and a
quality or adoption decision. XRefKit keeps those roles distinct:

```text
instruction
  -> semantic routing
  -> instruction-derived runtime binding
  -> selected Skill procedure
  -> on-demand XID Knowledge and evidence
  -> execution and observation
  -> verification, reporting, and human adoption
```

The runtime preserves `unknown` when required information or authority is
missing. It does not turn a resolved document into an instruction, a client
event into server confirmation, or an AI proposal into a canonical change.

## XID and on-demand Knowledge

XIDs are stable identities for repository-managed assets. Managed links carry
`#xid-<XID>` so path changes can be repaired without changing identity.

`xrefkit xref` maintains the identity and path layer. Skill routing selects
Knowledge semantically; the runtime resolves only the selected XIDs. A catalog
entry or server-side resolution is not proof that the body was loaded into
context or used as a judgment basis. Run records distinguish referenced,
loaded, and used Knowledge and retain source hashes where available.

## Runtime and responsibility layers

- **Base control** governs startup, uncertainty, context direction, evidence,
  handoff, and human authority boundaries.
- **XRefKit routing** selects Skills and Knowledge from the active catalog and
  builds the runtime context needed for the work item.
- **Skill procedure** defines how the selected work is performed.
- **Knowledge** provides reusable domain facts, rules, viewpoints, and
  evidence categories.
- **Workflow and reporting protocols** define execution records, checks,
  closure, human-facing status, and handoff.
- **Client and human** perform or evaluate the work. The client executes after
  the runtime binding succeeds; the human decides semantic acceptance and
  canonical adoption.

The single definition of the runtime `capability`, `tuning`,
`responsibility`, and `execution_mode` fields is the
[Workflow Runtime Binding contract](core/contracts/111_workflow_runtime_binding.md#xid-8D50A972BA9F).
`model_requirements` remains a separate per-work-item model-eligibility input.

Business work is organized into Skills, Knowledge, and where useful a
manifest-driven Business Pack. OS utility Skills protect or improve the
operating layer; domain Skills perform business work inside that boundary.

## Execution observation

Execution observation is part of the control surface. Skill Runs and
instruction-backed workflows retain run identity, runtime binding, XID
references, loaded and used Knowledge, work items, artifacts, concerns, phase
state, checks, closure, handoff, and available host evidence.

Dashboard data and proposal-only analysis make observations inspectable. An
observation supports a bounded improvement proposal; it does not authorize a
rewrite of canonical Skill or Knowledge. Decision trace keeps changes,
checkpoints, return paths, and human evaluation visible across repository
state.

## MCP and local boundaries

MCP is a distribution and audit boundary. It can provide startup context,
resolve XIDs, transfer selected Skill content, expose protocol blocks, and
provide guarded tools. It does not execute Skill procedures or replace human
authority.

Local Skill edits preserve provenance and avoid overwriting existing edits.
Local Knowledge is separately registered. Contribution returns pass through
staging, sealing, review, and explicit adoption; publication and live
verification remain separate states.

## Repository layout

- `docs/`: human-facing contracts, models, guides, designs, policies,
  references, packs, and presentations
- `agent/`: vendor-independent agent entry and operational contract
- `xrefkit/`: installable runtime, CLI, resolver, deterministic tools, and MCP
  adapter
- `skills/`: executable procedures and routing indexes
- `knowledge/`: shared domain Knowledge fragments
- `tools/`: deterministic analysis and quality utilities
- `work/`: non-canonical run logs, judgments, drafts, and handoff records
- `observations/`: tracked evidence used for Skill maturity and governance
- `sources/`: original materials retained for review
- `.xref/`: generated indexes and caches, normally ignored by Git

## Common entry points

Human orientation starts at [Docs Index](000_index.md#xid-56DD6EB68343).
Repository startup starts at [XRefKit Startup Contract](core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22).
The current architecture and retained package compatibility are described in
[XRefKit v2](xrefkit-v2-mvp.md#xid-E179D62EA4F4).

Common checks include:

```powershell
python -m xrefkit xref check
python -m xrefkit xref search "<query>"
python -m xrefkit xref show <XID>
python -m xrefkit skill run --definition <path-to-SKILL.v1.md> --task "<task>" --capability "<capability>" --tuning "<tuning>" --responsibility "<responsibility>" --execution-mode <mode> --json
# Legacy split compatibility only:
python -m xrefkit skill run --meta <path-to-meta.md> --task "<task>" --json
python -m xrefkit workflow run --task "<task>" --completion-condition "<condition>" --json
```

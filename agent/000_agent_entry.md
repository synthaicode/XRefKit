<!-- xid: 0B5C58B5E5B2 -->
<a id="xid-0B5C58B5E5B2"></a>

# Agent Entry (L0 / always read)

This file is the agent-side entry point. Human-facing background lives under `docs/`. Keep this page short and stable: it is the **operational contract**.

Related: [Overview](../docs/000_overview.md#xid-7C6C2B46A9D1)

## Contract (required)

- Apply base control rules first, then follow XRefKit-specific routing; see [Base control and xref routing layers](../docs/017_base_and_xref_layering.md#xid-5A1C8E4D2F90)
- Use XIDs as primary keys for references (links must include `#xid-...`)
- Keep skill instructions and domain knowledge in separate files
- Treat `knowledge/` as shared domain knowledge; skills load only needed fragments on demand
- Treat `capabilities/` as reusable work-unit definitions, not as evidence
- Default new skill creation to private (`skills_private/`); publish to `skills/` only when the user explicitly requests public release
- New skills MUST include the context-direction security guard by default unless they explicitly declare closed-world execution with no newly loaded external context
- New skills MUST include the Skill operating contract (`os_contract`) so worklist, execution role, check role, logging, unknown/risk handling, closure, and handoff are load-gated
- Skill execution MUST start with `python -m fm skill run --meta <path-to-meta.md> --task "<task>"`; do not open or execute `SKILL.md` until this command succeeds and returns a run log
- During Skill execution, update the run log with `python -m fm skill phase --log <run-log> --phase <phase> --status <status>`
- Before treating Skill-backed work as complete, run `python -m fm skill close --log <run-log>` and resolve or escalate any failed closure checks
- MUST write execution logs/retrospectives to `work/` automatically (non-canonical)
- MUST use date-prefixed filenames for `work/` logs (`YYYY-MM-DD_<type>_<topic>.md`)
- MUST create or update a `work/sessions/` log before final task completion and before `commit`/`push`
- MUST promote stabilized decisions/facts from `work/` to canonical locations (`docs/` or `knowledge/`)
- Follow shared-memory event logging rules in [Shared memory operations](../docs/015_shared_memory_operations.md#xid-4A423E72D2ED)
- Follow the Skill operating contract in [Skill Operating Contract](../docs/058_skill_operating_contract.md#xid-B7A2C94F0E61)
- Follow uncertainty protocol in [Uncertainty protocol](../docs/016_uncertainty_protocol.md#xid-8A666C1FD121)
- Do not fill missing information by guessing; first find the relevant XIDs and read them
- When creating new documents, follow the existing document format conventions, character encoding, and encoding form used by the surrounding repository area unless an intentional change is explicitly required
- After rename/move/split/merge, run link validation (`xref check`)
- When editing source files, preserve the existing file format conventions, character encoding, and encoding form unless an intentional change is explicitly required
- When adding entries to XML, place them according to the existing semantic grouping and structure; do not append blindly to the end
- After editing structured source files such as XML, JSON, YAML, or similar parseable formats, run a deterministic parser or equivalent deterministic validation step and confirm no parse error remains
- For XML and JSON edits, execute the structured-format checklist in [Workflow](../docs/010_workflow.md#xid-7D1E1C0279F1) before treating the work as complete

## How to reference (fixed procedure)

1. Read skill routing entry: `skills/_index.md`
2. Narrow candidates via `skills/index/*`, then read candidate `meta.md` files
3. Start the selected Skill through the runtime envelope: `python -m fm skill run --meta <path-to-meta.md> --task "<task>" --json`
4. Preserve the returned `run_log`; open selected `SKILL.md` only from the returned `skill_doc`
5. Mark runtime progress with `python -m fm skill phase --log <run-log> --phase <phase> --status <status>`
6. Before completion, run `python -m fm skill close --log <run-log>` and keep failed closure checks explicit
7. Read the entry index: [Docs Index](../docs/000_index.md#xid-56DD6EB68343)
8. If the task maps to the business-capability model, follow [Capability Routing for Agents](010_capability_routing.md#xid-1F93A7C24010)
9. Find candidate XIDs: `python -m fm xref search "<query>"`
10. Read only what you need: `python -m fm xref show <XID>`

If the user asks for available skills, answer from `skills/_index.md` first.

## Role of xref during skill execution

When a skill needs domain knowledge to proceed, `xref` is the routing layer:

1. Search the relevant knowledge fragment by intent or keyword (`xref search`)
2. Resolve and load only the needed fragment (`xref show`)
3. Continue skill execution with explicit XID-backed references

## Related

- [Base control and xref routing layers](../docs/017_base_and_xref_layering.md#xid-5A1C8E4D2F90)
- [Capability Routing for Agents](010_capability_routing.md#xid-1F93A7C24010)

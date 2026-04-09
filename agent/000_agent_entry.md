<!-- xid: 0B5C58B5E5B2 -->
<a id="xid-0B5C58B5E5B2"></a>

# Agent Entry (L0 / always read)

This file is the agent-side entry point. Human-facing background lives under `docs/`. Keep this page short and stable: it is the **operational contract**.

Related: [Overview](../docs/000_overview.md#xid-7C6C2B46A9D1)

## Contract (required)

- Use XIDs as primary keys for references (links must include `#xid-...`)
- Keep skill instructions and domain knowledge in separate files
- Treat `knowledge/` as shared domain knowledge; skills load only needed fragments on demand
- Treat `capabilities/` as reusable work-unit definitions, not as evidence
- Default new skill creation to private (`skills_private/`); publish to `skills/` only when the user explicitly requests public release
- New skills MUST include the context-direction security guard by default unless they explicitly declare closed-world execution with no newly loaded external context
- MUST write execution logs/retrospectives to `work/` automatically (non-canonical)
- MUST use date-prefixed filenames for `work/` logs (`YYYY-MM-DD_<type>_<topic>.md`)
- MUST create or update a `work/sessions/` log before final task completion and before `commit`/`push`
- MUST promote stabilized decisions/facts from `work/` to canonical locations (`docs/` or `knowledge/`)
- Follow shared-memory event logging rules in [Shared memory operations](../docs/015_shared_memory_operations.md#xid-4A423E72D2ED)
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
3. Validate the selected `meta.md` before opening `SKILL.md`: `python -m fm skill check --meta <path-to-meta.md>`
4. Open selected `SKILL.md` only when the meta validation passes
5. Read the entry index: [Docs Index](../docs/000_index.md#xid-56DD6EB68343)
6. If the task maps to the business-capability model, follow [Capability Routing for Agents](010_capability_routing.md#xid-1F93A7C24010)
7. Find candidate XIDs: `python -m fm xref search "<query>"`
8. Read only what you need: `python -m fm xref show <XID>`

If the user asks for available skills, answer from `skills/_index.md` first.

## Role of xref during skill execution

When a skill needs domain knowledge to proceed, `xref` is the routing layer:

1. Search the relevant knowledge fragment by intent or keyword (`xref search`)
2. Resolve and load only the needed fragment (`xref show`)
3. Continue skill execution with explicit XID-backed references

## Related

- [Capability Routing for Agents](010_capability_routing.md#xid-1F93A7C24010)

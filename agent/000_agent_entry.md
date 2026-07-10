<!-- xid: 0B5C58B5E5B2 -->
<a id="xid-0B5C58B5E5B2"></a>

# Agent Entry (L0 / always read)

This file is the agent-side entry point. Human-facing background lives under `docs/`. Keep this page short and stable: it is the **operational contract**.

When the XRefKit MCP server is configured, load this file through
`get_startup_context` / `get_document_by_xid` and follow the server-returned
`load_order`. Do not bypass MCP-only mode by reading local governance Markdown.

## Contract (required)

- Apply base control rules first, then follow XRefKit-specific routing; the
  layer boundary is defined in
  `docs/core/models/017_base_and_xref_layering.md#xid-5A1C8E4D2F90`
- Use XIDs as primary keys for references (links must include `#xid-...`)
- Keep skill instructions and domain knowledge in separate files
- Treat `knowledge/` as shared domain knowledge; skills load only needed fragments on demand
- Treat `capabilities/` as reusable work-unit definitions, not as evidence
- Default new skill creation to private (`skills_private/`); publish to `skills/` only when the user explicitly requests public release
- The context-direction security guard is delivered at init (startup contract pack / base control) and applies ambiently to every Skill that loads external input; new skills do not compose or declare it
- New skills MUST include the Skill operating contract (`os_contract`) so worklist, execution role, check role, logging, unknown/risk handling, closure, and handoff are load-gated
- Skill execution MUST start with `python -m xrefkit skill run --meta <path-to-meta.md> --task "<task>"`; do not open or execute `SKILL.md` until this command succeeds and returns a run log
- In MCP mode, after `skill run` returns `run_id`, call `bind_skill_run` with
  that `run_id` and `skill_id`, then execute its returned
  `client_record_command` against the returned `run_log` before task-specific
  XID access
- Skill-backed work MUST add concrete task items with `python -m xrefkit skill workitem --log <run-log> --item <id> --status <status> --role <assigned-role>` before closure
- Skill-backed work MUST record outputs and evidence with `python -m xrefkit skill artifact --log <run-log> --artifact <id> --kind <kind> --target <target> --status <status> --role <assigned-role>` before closure
- Skill-backed work MUST record closure-relevant unknowns, risks, and non-trivial judgments with `python -m xrefkit skill concern --log <run-log> --concern <id> --kind <unknown|risk|judgment> --status <open|resolved|escalated> --role <assigned-role>` before closure when they exist
- During Skill execution, update the run log with `python -m xrefkit skill phase --log <run-log> --phase <phase> --status <status> --role <assigned-role>`
- The check phase MUST be advanced deterministically with `python -m xrefkit skill verify --log <run-log>` at every maturity level, including `trial`; the producer context must not advance its own check phase, and deterministic verification (context-independent by construction) satisfies that separation
- Before treating Skill-backed work as complete, run `python -m xrefkit skill close --log <run-log>` and resolve or escalate any failed closure checks
- MUST write execution logs/retrospectives to `work/` automatically (non-canonical)
- MUST use date-prefixed filenames for `work/` logs (`YYYY-MM-DD_<type>_<topic>.md`)
- MUST create or update a `work/sessions/` log before final task completion and before `commit`/`push`
- MUST promote stabilized decisions/facts from `work/` to canonical locations (`docs/` or `knowledge/`)
- Follow shared-memory event logging rules in `docs/core/contracts/015_shared_memory_operations.md#xid-4A423E72D2ED`
- Follow the Skill operating contract in `docs/core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61`
- Follow uncertainty protocol in `docs/core/contracts/016_uncertainty_protocol.md#xid-8A666C1FD121`
- Do not fill missing information by guessing; first find the relevant XIDs and read them
- When creating new documents, follow the existing document format conventions, character encoding, and encoding form used by the surrounding repository area unless an intentional change is explicitly required
- After rename/move/split/merge, run link validation (`xref check`)
- When editing source files, preserve the existing file format conventions, character encoding, and encoding form unless an intentional change is explicitly required
- When adding entries to XML, place them according to the existing semantic grouping and structure; do not append blindly to the end
- After editing structured source files such as XML, JSON, YAML, or similar parseable formats, run a deterministic parser or equivalent deterministic validation step and confirm no parse error remains
- For XML and JSON edits, execute the structured-format checklist in `docs/guides/010_workflow.md#xid-7D1E1C0279F1` before treating the work as complete

## How to reference (fixed procedure)

1. Read skill routing entry: `skills/_index.md`
2. Narrow candidates via `skills/index/*`, then read candidate `meta.md` files
3. Start the selected Skill through the runtime envelope: `python -m xrefkit skill run --meta <path-to-meta.md> --task "<task>" --json`
4. Preserve the returned `run_log`; open selected `SKILL.md` only from the returned `skill_doc`
5. In MCP mode, bind the returned `run_id` through `bind_skill_run`, then run
   its `client_record_command` against `run_log`
6. Add concrete task items with `python -m xrefkit skill workitem --log <run-log> --item <id> --text "<item>" --status pending --role <assigned-role>`
7. Record output and evidence links with `python -m xrefkit skill artifact --log <run-log> --artifact <id> --kind <kind> --target <target> --status done --role <assigned-role>`
8. Record closure-relevant unknowns, risks, and non-trivial judgments with `python -m xrefkit skill concern --log <run-log> --concern <id> --kind <kind> --status <status> --role <assigned-role>` when they exist
9. Use the returned assigned roles; mark runtime progress with `python -m xrefkit skill phase --log <run-log> --phase <phase> --status <status> --role <assigned-role>`; advance the check phase with `python -m xrefkit skill verify --log <run-log>` (deterministic), never from the producer context
10. Before completion, run `python -m xrefkit skill close --log <run-log>` and keep failed closure checks explicit
11. If the task needs a document outside the selected route, use `docs/000_index.md#xid-56DD6EB68343` as a lookup index, not as a bulk read target
12. Find candidate XIDs: `python -m xrefkit xref search "<query>"`
13. Read only what you need: `python -m xrefkit xref show <XID>`

If the user asks for available skills, answer from `skills/_index.md` first.

## Role of xref during skill execution

When a skill needs domain knowledge to proceed, `xref` is the routing layer:

1. Search the relevant knowledge fragment by intent or keyword (`xref search`)
2. Resolve and load only the needed fragment (`xref show`)
3. Continue skill execution with explicit XID-backed references

# XRefKit Skill Run Dashboard

This app displays recorded operational state from XRefKit Skill runs stored
under a client repository's `work/sessions` directory.

## Approach

The dashboard does not parse Skill logs in TypeScript. It calls the repository runtime command:

```powershell
python -m xrefkit dashboard data --root <repo-root> --sessions-dir <repo-root>\work\sessions
```

This keeps run-log interpretation in `xrefkit.dashboard`, where parsing and
recorded workflow-closure checks are implemented. The app is a local UI over
that payload; it does not judge output quality.

The payload distinguishes unversioned historical logs, `legacy_split_v1`, and
`skill_definition_v1`. When recorded, it exposes definition identity, maturity
and governance references, plus the runtime `capability`, `tuning`,
`responsibility`, and `execution_mode`. Missing historical fields remain
`unknown`; the dashboard does not backfill them.

In addition to recorded runtime state, the payload exposes `missing_information`
for each run and `missing_information_ranking` across runs. These fields identify
information that is not recorded or cannot be correlated for the run, including
correlation IDs, routing traces, loaded-XID traces, Knowledge application
evidence, search traces, human feedback, outcome feedback, and measured token
usage. They are tuning observations and do not change the Skill closure result.

When MCP correlation is available, the shared `run_id` emitted by
`xrefkit skill run` links the local run and MCP audit records. The MCP server may
write `run.bound`, `knowledge.search`, `skill.ranked`, `skill.selected`, and
`xid.resolved` events to its audit JSONL. The dashboard joins matching events to
the local Markdown run log; it does not inject audit bodies into model context.

## Usage

From this directory:

```powershell
npm install
npm run dev
```

Open the printed local URL. By default, the app reads `../../work/sessions` relative to this project directory.

Environment overrides:

- `XREFKIT_ROOT`: repository root that owns the `work` directory.
- `XREFKIT_SESSIONS_DIR`: explicit Skill session log directory.
- `XREFKIT_MCP_AUDIT_LOG`: MCP audit JSONL; defaults to `<root>/work/mcp/xid_audit.jsonl`.
- `PYTHON`: Python executable to use.

## Checks

```powershell
npm run check
```

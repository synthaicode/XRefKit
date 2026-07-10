# XRefKit Skill Run Dashboard

This app displays the operational state of XRefKit Skill runs recorded under a client repository's `work/sessions` directory.

## Approach

The dashboard does not parse Skill logs in TypeScript. It calls the repository runtime command:

```powershell
python -m xrefkit dashboard data --root <repo-root> --sessions-dir <repo-root>\work\sessions
```

This keeps log interpretation in `xrefkit.dashboard`, where the Skill run parser and closure rules already live. The app is a local UI over that deterministic payload.

In addition to recorded runtime state, the payload exposes `missing_information`
for each run and `missing_information_ranking` across runs. These fields identify
missing correlation IDs, routing traces, loaded-XID traces, Knowledge application
evidence, search traces, human feedback, outcome feedback, and measured token
usage. They are tuning observations and do not change the Skill closure result.

MCP correlation uses the shared `run_id` emitted by `xrefkit skill run`. The
MCP server writes `run.bound`, `knowledge.search`, `skill.ranked`,
`skill.selected`, and `xid.resolved` events to its audit JSONL. The dashboard
joins those events to the local Markdown run log without loading audit bodies
into the model context.

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

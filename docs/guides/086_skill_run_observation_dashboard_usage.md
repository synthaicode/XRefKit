<!-- xid: 4A4763A2DE63 -->
<a id="xid-4A4763A2DE63"></a>

# Skill Run Observation Dashboard Usage

This guide explains how to run the Skill Run Observation Dashboard on a user's
local machine.

## Purpose

Use this dashboard to inspect Skill run logs emitted under `work/sessions/`.
It is an observation surface for humans, not a Skill executor and not an MCP
server.

The dashboard shows:

- Skill run status
- closure and quality gate state
- outputs, evidence, checks, handoffs, unknowns, risks, and judgments
- selected and used XIDs
- available but unused XIDs

Base repository XIDs and local XIDs are both included when they appear in the
Skill run log. Local XIDs include entries supplied through a domain-knowledge
catalog and entries served from local knowledge such as `packs/local/...`.

## Runtime Assumption

The dashboard is designed for local trusted use.

- It runs with Python on the user's machine.
- It reads local files from the selected repository root.
- It binds to `127.0.0.1` by default.
- It does not require MCP to start.
- It does not expose local paths as a domain-knowledge retrieval contract.

Do not treat this dashboard as an externally hosted service unless the binding,
network, and data exposure rules are reviewed separately.

## Start

From the repository root:

```powershell
python -m fm dashboard serve --root .
```

Default URL:

```text
http://127.0.0.1:8765/
```

To open the browser automatically:

```powershell
python -m fm dashboard serve --root . --open-browser
```

## Port Or Session Directory Options

Use another port when `8765` is already in use:

```powershell
python -m fm dashboard serve --root . --port 8766
```

Use another session log directory when the Skill run logs are not under the
default `work/sessions/`:

```powershell
python -m fm dashboard serve --root . --sessions-dir path\to\sessions
```

## JSON Output

Use the JSON command when the dashboard data needs to be inspected by another
local tool or test:

```powershell
python -m fm dashboard data --root .
```

The running dashboard also exposes JSON at:

```text
http://127.0.0.1:8765/api/runs
```

The health endpoint is:

```text
http://127.0.0.1:8765/healthz
```

## Stop

If the dashboard is running in the foreground terminal, stop it with
`Ctrl+C`.

If it was started in another process, stop the process that owns the selected
port. On Windows:

```powershell
Get-NetTCPConnection -LocalPort 8765 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess
Stop-Process -Id <OwningProcess>
```

## XID Display Rules

The `XID Usage` tab is derived from Skill run logs.

- Available XIDs come from the `Available Domain Knowledge` section.
- Selected XIDs come from the `Selected Knowledge Inputs` section.
- Used XIDs come from selected knowledge inputs plus runtime artifact or
  concern targets that look like XIDs.
- Unused XIDs are available XIDs that were not selected or used.

This includes local XIDs. A local XID is still an XID for dashboard purposes;
the dashboard does not need to know whether the source was base, shared pack, or
local pack as long as the run log records it by XID.

## Troubleshooting

If the page is empty, check that the selected root has Skill run logs under
`work/sessions/` or pass `--sessions-dir`.

If the browser cannot connect, confirm the server is listening:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/healthz
```

If local XIDs do not appear, confirm the Skill run log recorded them in the
domain-knowledge sections or as runtime evidence/artifact targets.

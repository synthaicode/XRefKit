<!-- xid: 4F8C2A7D1E90 -->
<a id="xid-4F8C2A7D1E90"></a>

# Install XRefKit and connect Skill Packages

Install XRefKit into the Python environment used by the client or server. Python
3.11 or later is required. Run these commands in the intended workspace:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install xrefkit
python -m xrefkit init
python -m xrefkit --help
```

`init` creates `.xrefkit/instance.toml` and missing `AGENTS.md`, `CLAUDE.md` and
`CHATGPT.md` files. Existing files are preserved. Use `--no-startup-files` when
startup files are unnecessary. The module form works even when the `xrefkit`
executable is not on PATH.

## Connect an AI client through MCP

Install the MCP extra in the server's Python environment:

```powershell
python -m pip install "xrefkit[mcp]"
python -m xrefkit mcp serve --repo C:\xrefkit-server --transport streamable-http --host 127.0.0.1 --port 8000
```

Configure the AI client's MCP connection to `http://127.0.0.1:8000/mcp` for this
local example, or to the administrator-provided endpoint for a remote server.
The client starts with `get_startup_context`, routes from the task purpose, and
fetches the selected Skill. Opening VS Code alone does not guarantee an AI
message or a startup call; start the conversation with your intended task.

The server supplies definitions and resources. The client runs the AI and local
Python tools. Human approval, business judgment and final acceptance remain
explicit. Client-local paths are never assumed readable on a remote server.

For a generated local stdio configuration, use:

```powershell
python -m xrefkit mcp setup --repo C:\xrefkit-server
python -m xrefkit mcp setup apply --source C:\path\to\generated-setup --repo C:\xrefkit-server
```

Inspect the generated `SETUP.md` before applying it. Apply creates
`.vscode/mcp.json` and adds routing instructions to `AGENTS.md` and `CLAUDE.md`.
Use `--force` only when intentionally replacing existing MCP configuration.

## Migrate an older environment

After installing and connecting the new environment, tell its AI:
"Migrate this old XRefKit environment." You do not need to instruct an old
AI first or manually prepare tests before starting.

For custom Skills that call Python, including shared `tools/` modules outside
Skill folders, use the
[guided legacy Python migration](117_guided_legacy_python_migration.md#xid-6D73C9A12E40)
route. It separates client inspection, preparation and test evidence, governed
upload/adoption, server registration, and hash-checked local resource use.
Observed legacy behavior and business-approved expectations remain distinct.

The document-only compatibility route remains available when the source and
target are accessible in the same environment. `plan_legacy_migration(source)`
returns selectable Skill folders and Knowledge documents. Execute its returned
client command with an explicit `--target` for every selected unit. The source
and target must be separate non-overlapping folders. Existing changed files are
reported as conflicts rather than overwritten.

An administrator may request this import during setup:

```powershell
python -m xrefkit mcp setup --repo C:\xrefkit-server --import C:\old-skills
```

`--import` writes converted Skill/Knowledge files into `--repo`; the temporary
setup output is not an isolated migration destination. Use a separate target
repository when an isolated review is needed. Inspect `import-report.json`.
Setup also runs XID maintenance in the target repository.

The document-only importer uses the folder-based `legacy_split_v1` converter;
this does not adopt a SkillDefinition v1 or promote its maturity. Selected
Skills include their directly linked Knowledge; unlinked Knowledge can be
selected separately. Unsupported resources remain explicit.

Server-scoped `.xrefkit/legacy-migration.json` retains selected targets,
prepared artifacts, failures and retrieval receipts. Conversion or a local CLI
read alone is insufficient: retrieve pending bodies with `get_document_by_xid`
without `known_version`, or with `get_skill`. Conditional omission is not a new
retrieval receipt. Restarting or upgrading does not reset this state. Do not
reset damaged state or infer success from a package version. Only explicit
confirmation that no legacy assets exist permits `dismiss_legacy_migration`.
For Python migrations, definition retrieval alone does not establish behavioral
completion; follow the guided route's workflow evidence and remaining checks.

## Install and discover official Skill Packages

Install only the distributions needed:

```powershell
python -m pip install xrefkit-skills-batch-regression
python -m pip install xrefkit-skills-csharp
python -m pip install xrefkit-skills-brownfield
python -m xrefkit package discover --json
```

MCP automatically discovers `xrefkit.skill_packages` entry points installed in
its own interpreter. Restart the server after installation and verify live
`list_skills`, `rank_skills_for_purpose` and selected `get_skill` responses.
Installing into a different interpreter does not register a package with that
server. Package files need not be copied into the repository merely for ranking.

CLI resolution enables package IDs explicitly:

```powershell
python -m xrefkit show effective-skill batch.impact_regression --mode tree --enable-entry-point-discovery --enabled-package xrefkit.skills.batch_regression
```

Repeat `--enabled-package` to enable multiple packages. For continuing CLI use,
store IDs in `xrefkit.server.toml`:

```toml
[packages]
enabled = ["xrefkit.skills.batch_regression", "xrefkit.skills.csharp"]
```

The pip distribution name and XRefKit package ID are different identifiers.
Use the package manifest or discovery output for the ID. Distribution dependency
bounds and manifest Core protocol bounds are also different; see
[Core release compatibility](112_core_skill_release_compatibility.md#xid-0C41A7D389B2).

A package may provide a canonical Markdown SkillDefinition or a legacy YAML and
entry Markdown pair. Repository-native SkillDefinition candidates require
explicit `--skill-definition` selection and applicable `--skill-governance`
records; placing a file in the repository does not activate it. Parsing and
catalog registration do not imply maturity, quality acceptance or production
adoption. See the
[distribution boundary](098_skilldefinition_distribution_boundary.md#xid-B7D3A5E91C42).

## Server options and management boundary

Use `python -m xrefkit mcp serve --help` for the exact installed option set.
Common settings are:

| Option | Default | Purpose |
| --- | --- | --- |
| `--repo` | required | Server repository root |
| `--profile reader\|admin` | `reader` | Reader or loopback-only management tools |
| `--transport stdio\|sse\|streamable-http` | `stdio` | MCP transport |
| `--host` / `--port` | `127.0.0.1` / `8000` | HTTP bind address |
| `--http-path` | `/mcp` | Streamable HTTP endpoint |
| `--ssl-certfile` / `--ssl-keyfile` | none | HTTPS certificate and key |
| `--public-base-url` | automatic | Artifact distribution URL |
| `--enable-executable-distribution` | off | Executable artifact distribution |
| `--distribution-trust-id` | none | Distribution trust identity |
| `--dist-extra-dir` | none | Additional artifact directory |
| `--enable-inbound-webdav` | off | Admin contribution staging listener |
| `--inbound-webdav-host` / `--inbound-webdav-port` | MCP listener | Upload listener binding |
| `--stateless-http` | off | Stateless Streamable HTTP |
| `--context-secret` | environment | Context-token HMAC secret |
| `--domain-knowledge-root` | none | Additional XID roots, repeatable |
| `--skill-definition` / `--skill-governance` | none | Explicit definition/governance inputs, repeatable |
| `--audit-log` | repository work area | MCP audit output |
| `--log-level` | `info` | Logging verbosity |

Reader discovery does not expose update, review or adoption operations. The
management profile binds only to loopback. Use the existing
[contribution management guide](095_mcp_contribution_return_adoption.md#xid-0E5C778EB6AF)
for upload, trusted approval and adoption configuration. Upload/adoption,
publication, distribution and live verification are separate outcomes.

New clients may exclude optional initial protocol bodies during MCP initialize:

```json
{"capabilities": {}, "xrefkit": {"excluded_protocols": ["reporting"]}}
```

Allowed names are `prompt_flow`, `workflow` and `reporting`. Omission or an empty
list includes all three. Legacy `xrefkit.initial_protocols` and repeatable
`--initial-protocol` retain include semantics for workflow/reporting, with prompt
flow included. Do not send both initialize extensions. Base uncertainty,
context-direction, XID routing and shared-memory controls remain applicable
regardless of optional protocol-body selection.

## Other distribution routes and updates

Batch Regression's legacy folder materializer is available when that interface
is specifically required:

```powershell
xrefkit-batch-regression install-mcp-skill --repo C:\xrefkit-server
```

It defaults to `skills/packs/batch-regression/batch-impact-regression`. Review
local differences before explicitly using `--force`. C# and Brownfield normally
use package entry-point discovery.

For repository bundle synchronization:

```powershell
python -m xrefkit skills sync --bundle csharp --dry-run --json
python -m xrefkit skills sync --bundle csharp
python -m xrefkit skills sync --all
```

Synchronization is separate from management staging, review and adoption. It
does not itself activate v1 candidates, accept quality, promote maturity or
prove live retrieval. See
[bundle synchronization](090_skill_bundle_sync.md#xid-8D7F2A6C4B10).

Upgrade in the same interpreter used for execution:

```powershell
python -m pip install --upgrade xrefkit
python -m pip install --upgrade xrefkit-skills-batch-regression
python -m xrefkit package discover --json
```

Verify installed compatibility, CLI resolution and live MCP retrieval separately.
`skills/_index.md` is the repository Skill catalog and is not regenerated by pip
installation. Run `python -m xrefkit skill index --write` only when repository
Skill metadata itself changes.

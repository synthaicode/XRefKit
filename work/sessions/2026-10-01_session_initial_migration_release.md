## 2026-10-01: Initial legacy migration guidance and 0.6.1 release

### Event

The candidate checkout at C:/dev/itsm/XRefKit was on
codex/mcp-startup-protocol, HEAD 2a5e39b423c51f1c2efcf34e8266053243d14ea2,
with existing modifications and untracked assets. It was read without mutation.
Implementation began in an isolated source copy. For publication, only this
task's changes were ported to a fresh main checkout at
12130e2472ae8a2f0af3e63efda21533711dcd4b (0.6.0).

### Decision

Startup returns uncached, target-repository migration guidance. The MCP server
inventories sources and records retrievals; the client-side Python CLI writes
only explicitly selected assets. Existing server ToolContract write boundaries
remain intact. State and durable staging are stored under .xrefkit, independently
of package versions. Selected asset completion requires matching MCP body
retrieval, in addition to installation integrity. Source bytes and conflicting
destination files are preserved. Unsupported resources remain explicit failures.

README covers connecting VS Code/Copilot briefly. Guide 089 and generated setup
instructions distinguish initialization from AI conversation startup, and
correctly state that setup --import writes to --repo, not the report directory.

### Human Stated Reason

The user requested help migrating the old shared XRefKit skills and knowledge
when beginning MCP use, without requiring people to specify Skill names.
The user later explicitly requested: "修正が終わったら、0.6.1としてPyPIにリリースしといて".

### Evidence

- Final repository quality gate: 907 passed, 1 skipped, 2 subtests passed;
  XID, Skill, pack, tracked runtime-log, and project baseline checks passed.
- Earlier restricted-user run: 901 passed, 5 failed, 1 skipped; the failures
  were a temporary-file permission error and Git ownership differences between
  parent and stdio child processes. They passed in the correct user environment.
- Legacy migration tests cover initial, partial, complete, restart, version
  change, conflict, retry after partial publishing, corrupted state, explicit
  scope, unsupported resources, XID collisions, and source byte preservation.
- Live stdio MCP test exercises inventory, client CLI import, get_skill,
  get_document_by_xid, and server restart using isolated fixtures.
- Bandit medium/high scan and declared dependency audit passed.
- 0.6.1 wheel/sdist build, twine metadata check, and artifact inspection passed.
- No standalone Python type/lint checker is configured. Local ClamAV was not
  run; existing release CI performs the required malware inspection and smoke
  tests before Trusted Publishing.

### Deferred

The separate GPT-6 Luna / GPT-6.1 Sol timing comparison fixture remains a
follow-up after this release. No comparison run was started.

### Open

Corporate VS Code/Copilot behavior is unverified; no company PC was operated.
Opening VS Code alone does not guarantee an AI utterance. Remote MCP clients
must confirm the filesystem mapping before executing server-path import commands.
PyPI publication and CI completion are to be confirmed from their actual results.

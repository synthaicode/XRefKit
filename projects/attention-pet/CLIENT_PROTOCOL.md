# Attention Pet client protocol v1

`attention-pet-client-v1` is the provider-neutral contract between a same-host
client adapter and Attention Pet. It does not depend on MCP or a provider's
private transcript format.

## Boundary

- The Pet listens only on `127.0.0.1`.
- Display assets and `GET /api/state` do not require authentication.
- Handshake and state writes require the per-process bearer token.
- The launcher captures the token from the first JSON line on stdout and keeps
  it in memory. The token is not part of the display URL.
- Clients send structured `WorkingSet` snapshots, not raw chat transcripts.

## Launch and discovery

```powershell
xrefkit attention-pet serve --client --port 8769
```

The first stdout line is a single JSON object:

```json
{
  "service": "xrefkit-attention-pet",
  "endpoint": "http://127.0.0.1:8769",
  "protocolVersion": "attention-pet-client-v1",
  "instanceId": "per-process random value",
  "writeToken": "per-process random value"
}
```

Before sending state, the client calls authenticated
`GET /api/client/handshake` and verifies `service`, `protocolVersion`,
`instanceId`, and the `active-session` capability. A TCP listener or HTTP 200
alone is not proof that the intended Pet process is present.

## Active session notification

`POST /api/active-session` accepts the schema in
[`schema/client-state.schema.json`](schema/client-state.schema.json). The body
identifies the provider, client process, active session, client capabilities,
selected runtime settings, and the complete structured WorkingSet.

`activationRevision` increases within one `provider + clientInstanceId`. An
older revision, or reuse of a revision for different state, returns HTTP 409.
An exact retry of the latest accepted notification is idempotent. Each session
has an independent persisted Store, and switching the active session changes
only the displayed Store. If more than one client instance is connected, the
last accepted notification selects the displayed session; revisions remain
independent for each `provider + clientInstanceId`.

## Adapter capability limits

An adapter reports what its public client API actually observes. It must not
claim immediate session switching when it sees only prompt submission.

| Adapter | Initial target | Limitation |
|---|---|---|
| Codex | `SessionStart` and `UserPromptSubmit` hooks | Public hooks do not document an immediate conversation-selection event. |
| VS Code / GitHub Copilot | Chat Participant request handler | A participant sees requests and history routed to that participant, not all built-in Copilot Chat sessions. |

The VS Code adapter is a local `ui` extension so its loopback endpoint is on
the same host as the desktop UI. PyPI distributes the Pet server and Python
client library; a VSIX or VS Code Marketplace package distributes the VS Code
adapter.

Official API references:

- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
- [VS Code Chat Participant API](https://code.visualstudio.com/api/extension-guides/ai/chat)
- [VS Code Extension Host](https://code.visualstudio.com/api/advanced-topics/extension-host)

## Failure behavior

Attention Pet is observational. Connection, authentication, schema, and
compatibility failures do not block the client. The adapter keeps only the
latest complete snapshot for retry, performs a new handshake after Pet restart,
and does not replay older session activations after a newer revision succeeds.

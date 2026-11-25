<!-- xid: 41E7A8B9C620 -->
<a id="xid-41E7A8B9C620"></a>

# SEP-2640 implementation basis

This basis realizes AN-01 and AN-02 of the [work plan](plan.md#xid-9A62E4B817C3)
before code changes. The user authorized this server extension and local tests;
the parent coordinator accepted bootstrap adapters that preserve existing gates.

## Compatibility and requirements

| Requirement | Implemented boundary |
| --- | --- |
| SEP-2640 extension capability | `initialize` advertises `capabilities.extensions["io.modelcontextprotocol/skills"] = {}` and the Resources capability. |
| Required methods | Wire-level `skills/list`, `skills/get`, and ordinary `resources/read`; a single complete list page, rejecting unsupported cursors. |
| Published shape | Agent Skills frontmatter, explicit `SKILL.md` URI, complete SHA-256/byte-size manifest, `resultType: complete`. |
| Newer base protocol | The accepted SEP explicitly makes list cache fields conditional on 2026-07-28. This implementation retains the SDK's 2025-11-25 protocol and initialization lifecycle. It does not claim the newer beta's `server/discover`, mandatory request metadata, or full 2026 base support. |
| Optional features | No `directoryRead` capability, dynamic resources, bundled downloads, or directory traversal. |
| Errors | Invalid/unknown extension URI or cursor: JSON-RPC -32602. Unexpected extension failures: -32603 without filesystem details. |
| Existing clients | Existing tool registrations, startup, bound-run checks, audit and HTTP/stdio configuration are retained. |

The SDK baseline is `mcp==1.28.0`; its request union lacks `skills/list` and
`skills/get`. A local low-level Server/ServerSession subclass extends only that
request parser and registers the handlers. FastMCP uses that server instance.
No SDK module/global class is replaced. The local run loop preserves the SDK
lifespan, experimental task setup, request context, cancellation and shutdown
behavior. The optional dependency floor is raised to the tested 1.28 API.

## Native Skill adaptation

Each unambiguous public catalog Skill gets a generated **bootstrap adapter**,
not a copy of its native procedure. Its only file is `SKILL.md`. The file teaches
a client to obtain `get_startup_context`, resolve runtime requirements, create
and bind a Skill Run, and retrieve the canonical method through `get_skill`.
This is a usable Agent Skill for entering the existing governed workflow.
Resource inspection does not create a run, unlock tools, grant local execution,
or change an existing run binding. Native supporting files are not published as
adapter files. Existing XID/tool resolution remains the method delivery route.

The generated frontmatter has a valid lowercase hyphenated name, a bounded
description, and string-valued metadata retaining the original skill ID, source
kind, maturity and content fingerprint. A digest suffix keeps normalized names
distinct; the final URI segment exactly matches `name`. Duplicate catalog IDs
and alias conflicts are excluded, rather than selecting an arbitrary source.
Private or hidden entries and paths under `skills_private` are excluded.

The fingerprint covers the canonical body and metadata identity. Native source
bytes are re-read from the catalog-selected source path so a changed definition
changes the wrapper's digest; legacy fingerprints cover the cached meta/body
that the legacy retrieval API actually serves. No URI is turned into a path.
Native source paths must remain within their catalog root and must not pass
through a symlink. A missing/unsafe source is not published.

The complete manifest contains the generated UTF-8 bytes, including their
newlines, exactly once. Reads return those same bytes as text. There is no
recursive filesystem inventory, no scripts, and no implicit permission fields.
Standard list/get/read operations are inspection-only and safe before XRefKit
startup. The wrapper explicitly preserves host approval and origin boundaries.

## Verification and evidence

Tests cover capability/wire dispatch, list/get equivalence, frontmatter fidelity,
exact UTF-8 size/digest, native content changes, legacy changes, name collisions,
private/conflicted identities, unknown/traversal/encoded URIs, missing/unsafe
sources, malformed parameters, empty catalog and unsupported cursors. Actual
stdio and HTTP transport checks exercise the registered server, plus legacy
tool/startup behavior. Independent review and final regression remain separate
work-plan items. Actual third-party client UX and deployment remain unverified.

Authoritative inputs retrieved by the parent on 2026-11-25:

- [Accepted SEP-2640](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/2eb3a8e345aaee53461a3c5c5f6900659d3ecb27/docs/seps/2640-skills-extension.mdx), local snapshot `work/sep2640/sep-2640.mdx`.
- [Current beta specification](https://github.com/modelcontextprotocol/ext-skills/blob/ff224337b01f0c9b18b81dcf99eefe66e9a52b5c/specification/beta/skills.mdx), local snapshot `work/sep2640/skills-beta.mdx`.
- Local SDK 1.28.0 source: `Server.run`, `ServerSession`, `BaseSession._receive_loop`, FastMCP handler registration.

Snapshot hashes and observed test commands/results are retained in
`work/sep2640/implementation-evidence.txt`. The current beta is comparison
evidence, not a claim that this change migrates the base protocol.

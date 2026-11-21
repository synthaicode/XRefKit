# API context assembly design candidate

This fixture classifies the engineering proposal from the archived Issue #201.
It represents a proposed design for offline validation.

## Source acquisition

Use the Runtime and versioned interfaces selected in #200. Load the native
startup instructions in order from an authorized repository snapshot. The
Core wheel supplies code and bundled assets. Project startup sources require
their own approved source. Verify the binding, root, source revision and XID.
Load selected required and optional sources only. Reject a missing, conflicting,
stale or truncated required source. Record optional omission and excerpt bounds.

## Context assembly

Keep trusted controls, user task, supporting data and tool results distinct.
Check source classification, destination, authorization and required controls
before rendering. Check serialized input, tool schemas and output reserve
against configured limits. Omit only eligible optional data, deterministically.
Hold assembly before dispatch if required content cannot fit. Record source
identity and revision, selected excerpts and omissions, payload digest, and
run and Work Item correlation in the provenance manifest.

## Planned handoff

Check the verified upstream contract for the resolver/adapter inputs (#202).
Record provenance, stop reasons and fixture evidence for scoped tool input
(#204), evaluation (#205) and controller handoff (#206). Live provider calls,
MCP mode, real repository data and retention remain separate authorization
and test scopes. Design and acceptance owners need confirmation.

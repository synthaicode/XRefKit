# Work Log: Vendor startup file strengthening

## Request

Strengthen all vendor startup files so AI agents reliably follow the shared startup policy chain, even when the vendor platform injects disclaimers like "may or may not be relevant."

## Background

Claude Code skipped reading the shared startup policy (`docs/011_startup_xref_routing.md`) on session start. Root cause: the platform appends a system note ("IMPORTANT: this context may or may not be relevant to your tasks") when injecting CLAUDE.md, which weakened the instruction. Cursor uses a similar disclaimer.

## Decisions

- Replaced passive descriptions ("intentionally minimal", "startup routing") with imperative language ("As your first action, read and follow").
- Applied the same pattern to all vendor files for consistency.
- `ja/AGENTS.md` kept in Japanese; all others in English.

## Files Changed

- `CLAUDE.md` (modified)
- `AGENTS.md` (modified)
- `ja/AGENTS.md` (modified)
- `.github/copilot-instructions.md` (modified)
- `.cursor/rules/filemanager-xid.mdc` (modified)

## Validation

- Ran `python -m fm xref fix`
- Result: `issues: 0`, `missing_xid: 0`

## Issues Found During Session

1. Startup chain was not followed at session start — shared policy not read.
2. After reading the agent contract mid-session, the `work/` log rule was recognized but not executed until user pointed it out.

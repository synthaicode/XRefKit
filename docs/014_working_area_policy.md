<!-- xid: 111D282CA0EA -->
<a id="xid-111D282CA0EA"></a>

# Working Area Policy (AI-authored retrospectives)

Use `work/` as an AI-authored retrospective and event-log area.
Use `docs/` and `knowledge/` only for reviewed, stable outputs.

## Purpose

- Preserve execution history, decisions, and intent for handover.
- Keep canonical docs focused on stable outcomes.
- Make AI-to-AI and AI-to-human transfer easier.

## Folder Roles

- `work/sessions/`: per-task execution logs written by AI
- `work/retrospectives/`: summaries of decisions, tradeoffs, and outcomes
- `work/handover/`: concise baton-pass notes for unfinished work

## File Naming Rule (required)

Because auto-routing is not guaranteed, AI MUST use date-prefixed filenames.

- Format: `YYYY-MM-DD_<type>_<topic>.md`
- Examples:
  - `2026-02-06_session_xref-policy-update.md`
  - `2026-02-06_retro_skill-import-design.md`
  - `2026-02-06_handover_pending-main-merge.md`

## Promotion Rules

1. AI MUST write logs and retrospectives to `work/` during/after tasks.
2. AI MUST promote stabilized content to:
   - `docs/` for operational/design policy
   - `knowledge/` for domain facts
3. Add/normalize XIDs after promotion:
   - `python -m fm xref init`
   - `python -m fm xref fix`
4. Keep a short pointer in `work/` (moved-to path/date).

## Notes

- `work/` is intentionally outside default `xref` include targets.
- Humans do not need to manually curate `work/`; AI writes it automatically.
- Do not treat `work/` as canonical source of truth.
- Event-log writing rules are defined in:
  - `docs/015_shared_memory_operations.md#xid-4A423E72D2ED`

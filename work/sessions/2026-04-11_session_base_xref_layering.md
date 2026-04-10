# Session Log

- date: `2026-04-11`
- topic: `base control and xref routing layering`
- summary: clarified the internal split between base AI control rules and XRefKit-specific routing without extracting a separate repository
- updated:
  - `docs/017_base_and_xref_layering.md`
  - `docs/000_index.md`
  - `docs/011_startup_xref_routing.md`
  - `docs/000_overview.md`
  - `docs/016_uncertainty_protocol.md`
  - `docs/053_context_direction_security_guard.md`
  - `agent/000_agent_entry.md`
- notes:
  - keep startup in one repository
  - treat guard and uncertainty as base control
  - treat XID and `xref` routing as XRefKit-specific
  - follow-up duplication cleanup should keep `011` as startup operation, `012` as startup structure, and `017` as layer boundary

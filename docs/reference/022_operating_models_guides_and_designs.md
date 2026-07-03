<!-- xid: 9C4E2A71D583 -->
<a id="xid-9C4E2A71D583"></a>

# Operating Models, Usage Guides, and Design Pages

This page clarifies the boundary among three nearby document types:

- operating models
- usage guides
- design documents

## Document Roles

- operating model pages:
  - define how a function or team is structured and operated
  - shared operating models live under `docs/operating-models/`
- usage guide pages:
  - explain when and how to use that function or team in practice
  - shared human-facing guides live under `docs/guides/`
- design pages:
  - define a proposed system or integration design
  - shared design documents live under `docs/designs/`
  - example: [Codex MCP job inbox design](../designs/050_codex_mcp_job_inbox_design.md#xid-77BCEAA247E3)

## Boundary Rule

Use:

- operating model pages for structure, roles, outputs, and internal operating loop
- usage guide pages for requests, preparation, interpretation, and day-to-day use
- design pages for architecture, scope, state model, interfaces, and implementation plan

Do not restate a full operating model inside a usage guide.
Do not restate a full usage guide inside a design page.

## Reading Order

1. read the operating model to understand the function
2. read the usage guide to use it
3. read the design page only when implementing or evaluating a concrete system design

## Related

- [Codex MCP job inbox design](../designs/050_codex_mcp_job_inbox_design.md#xid-77BCEAA247E3)

<!-- xid: E7D4A11B8C06 -->
<a id="xid-E7D4A11B8C06"></a>

# Database Design Viewpoints

## Purpose

This page defines reusable viewpoints for brownfield database design. It is
used by `db_design` when a design changes schema, persistence behavior, data
migration, data correction, or data-flow ownership.

## Design Axes

| Axis | Required design concern |
| --- | --- |
| Data ownership | Which module, service, aggregate, or process owns each table, collection, stream, or persisted record. |
| Logical model | Entity, relationship, cardinality, optionality, lifecycle, and state-transition meaning. |
| Physical model | Table, column, type, precision, nullability, default, computed value, index, constraint, partition, and storage boundary. |
| Naming | Existing table, column, constraint, index, schema, migration, DbSet, entity, and configuration naming rules. |
| Compatibility | Whether the change is backward compatible for existing code, deployments, reports, integrations, and rollback. |
| Migration | DDL order, data backfill, defaulting, validation, locking, batching, rollback, and deployment sequencing. |
| Data correction | Whether existing rows require correction, reconciliation, audit trail, or a dedicated tool. |
| Transaction boundary | Unit of consistency, isolation assumptions, concurrency conflicts, retry behavior, and idempotency. |
| Read/write paths | Which commands, queries, jobs, events, APIs, reports, or external consumers read or write the data. |
| External dependency | Configured connection strings, schema names, linked servers, generated scripts, migration tooling, seed data, or externally owned tables. |
| Observability | Audit columns, operation logs, reconciliation checks, metrics, and failure investigation data. |
| Security/privacy | Sensitive fields, access boundary, retention, masking, encryption, and deletion obligations. |

## Brownfield Rules

- Use the current source-structure finding as the primary structure basis.
- Use DDL, migrations, ORM mappings, DbContext/DbSet definitions, repositories,
  raw SQL, seed data, reports, and integration contracts as evidence.
- Treat database naming as local convention. Do not invent table, column,
  index, constraint, migration, or schema names from generic style guides when
  the target has existing names.
- If a design changes externally visible or data-flow-relevant names, use the
  selected source-structure finding's Brownfield API Naming Extractor output.
- If the source-structure finding does not cover persistence boundaries,
  migration assets, naming clusters, or external database dependencies needed
  by the design, refresh the finding before freezing the database design.
- Separate requirement confirmations from design-time choices. Requirement
  confirmations belong to constraint derivation; design choices belong in the
  database design package.

## Required Output Shape

A database design package should identify:

- target database, schema, table, collection, stream, or persistence boundary
- existing authority and evidence
- logical model change
- physical model change
- naming basis and candidate names
- read/write path impact
- migration and data correction plan
- compatibility and rollout plan
- transaction, consistency, and concurrency behavior
- validation and reconciliation checks
- rollback or forward-fix approach
- unresolved assumptions and required derivation outputs

## Derivation Triggers

Route to constraint derivation before implementation-facing closure when:

- DDL, schema, ER, CRUD notes, or nullable/range/enum/constraint decisions hide
  behavior that requirements did not confirm.
- DDL and C# code disagree or represent different projections of the same use
  case.
- database changes interact with asynchronous jobs, APIs, files, auth, or
  integration boundaries.
- multiple derivation outputs expose repeated patterns or ownership conflicts
  that require commonality review.

## Knowledge Relations

- depends_on: [Current source structure findings catalog](../source_analysis/170_current_source_structure_findings_catalog.md#xid-A9E742B1C6D0)
- depends_on: [CSharp naming-convention extraction](../source_analysis/140_csharp_naming_convention_extraction.md#xid-B4F7E1A2C903)
- related_to: [Design constraint derivation catalog](../packs/constraint-derivation/120_design_constraint_derivation_catalog.md#xid-2D14F88A6C01)

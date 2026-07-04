<!-- xid: A68F54D72C19 -->
<a id="xid-A68F54D72C19"></a>

# Skill: db_design

## Purpose

Produce implementation-ready brownfield database design artifacts from approved
planning inputs, current source-structure findings, and database evidence.

This Skill designs database changes. It does not implement migrations, edit
application code, or decide missing business requirements.

## Required Knowledge (XID)

- [Database design viewpoints](../../knowledge/database/100_database_design_viewpoints.md#xid-E7D4A11B8C06)
- [Database current-state analysis viewpoints](../../knowledge/database/110_database_current_state_analysis_viewpoints.md#xid-F9B3C6A70412)
- [Current source structure findings catalog](../../knowledge/source_analysis/170_current_source_structure_findings_catalog.md#xid-A9E742B1C6D0)
- [CSharp naming-convention extraction](../../knowledge/source_analysis/140_csharp_naming_convention_extraction.md#xid-B4F7E1A2C903)
- [Design constraint derivation catalog](../../knowledge/packs/constraint-derivation/120_design_constraint_derivation_catalog.md#xid-2D14F88A6C01)

## Inputs

- approved requirements
- work plan and source modification policy
- data change policy
- current source-structure finding XIDs for each source and persistence target
- current database state analysis report or XID for each DB/persistence target
- DB-unit SQL export basis recorded in the selected current database state
  analysis
- existing DDL, schema, migrations, ORM mappings, DbContext/DbSet definitions,
  repositories, raw SQL, seed data, reports, or integration contracts
- optional confirmed constraint-derivation outputs

## Outputs

- database design package
- logical model change
- physical model change
- table, column, constraint, index, schema, migration, entity, and DbSet naming
  basis and candidate names
- read/write path and data-flow impact
- migration, backfill, data correction, and reconciliation plan
- transaction, consistency, idempotency, concurrency, and rollback notes
- stored procedure return/result convention and transaction granularity basis
  when stored procedure design is in scope
- validation and test handoff notes
- source-analysis basis XIDs and selected naming evidence
- required constraint-derivation output paths
- XDDP traceability rows for DB design items, linking requirement differences to
  logical/physical DB changes, persistence/source targets, evidence basis,
  migration/correction actions, validation handoff, and unknown items
- unresolved assumptions
- unknown DB design item list with reason, missing evidence or missing decision,
  affected DB/source area, downstream impact, and handoff or confirmation owner

## Startup

- Confirm approved requirements, work plan, source modification policy, and
  data change policy exist.
- Confirm the database design scope:
  - target database, schema, table, collection, stream, persistence boundary, or
    ORM model
  - new design, change to existing design, migration-only design, data
    correction design, or rollback/compatibility design
- Confirm every source and persistence target has a registered current
  source-structure finding XID.
- Confirm every DB or persistence target has a current database state analysis
  report or XID.
- Confirm the selected current database state analysis records the DB-unit SQL
  export basis for each database in scope, or an explicit `missing` with impact.
- Confirm the selected current database state analysis contains DB naming rule
  analysis and naming clusters when new or changed DB, migration, ORM, raw SQL,
  job, message, or configuration names are required.
- Confirm the selected current database state analysis contains
  table-definition local rules when the design proposes tables or columns.
- Confirm the selected current database state analysis contains stored
  procedure naming rules when the design proposes stored procedure names.
- Confirm the selected current database state analysis contains database-level
  local rules for naming, stored procedure granularity, transaction
  configuration method, and SQL writing style when the design affects stored
  procedures, SQL, transaction behavior, or DB-specific conventions.
- Confirm the selected current database state analysis contains stored
  procedure analysis for return/result convention and transaction granularity
  when the design creates, changes, replaces, or calls stored procedures.
- Confirm the selected current database state analysis contains isolation level
  and error-handling style evidence when the design affects SQL transactions,
  stored procedures, or database command error behavior.
- Confirm the selected current database state analysis contains DDL/query
  construction rules when the design or migration work needs `DROP`, object
  existence checks, idempotent scripts, destructive-operation guards, or
  deployment script style.
- Confirm the selected source-structure finding contains persistence boundary
  evidence and Brownfield API Naming Extractor output when names cross API,
  message, job, or external data-flow boundaries.
- If the required current database state analysis is missing or stale, route
  that target through `db_current_state_analysis` before freezing DB design, but
  first tell the user that this run must inspect local SQL, DDL, ORM, migration,
  and persistence source evidence to create or refresh the current DB analysis.
- If the required source-structure or naming evidence is missing or stale,
  route back to `source_structure_overview` and
  `source_structure_findings_registration` before freezing DB design, but first
  tell the user that this run must inspect local source files to create or
  refresh the source-structure finding.
- Load only DB-relevant domain knowledge and selected source findings.

## Planning

- Classify the database design area:
  - logical model
  - physical model
  - DDL or migration
  - ORM mapping
  - read/write query path
  - data correction or reconciliation
  - integration/reporting contract
  - compatibility, rollback, or deployment sequencing
- Identify structural authorities:
  - DDL and migration files
  - ORM mappings, DbContext/DbSet, entity configuration, repositories, raw SQL
  - seed data, fixtures, reports, jobs, event handlers, API commands/queries
  - externally supplied schema names, connection strings, scripts, generated
    artifacts, or migration tooling
- Determine which names must be proposed and which existing naming evidence
  governs them.
- Decide whether current database state analysis is missing:
  - no current DB state report covers the target
  - the report does not record DB-unit SQL export basis for the target database
    or an explicit `missing` status
  - report predates relevant schema/migration/ORM changes
- report lacks required persistence inventory, current logical/physical
    model, DB naming rule analysis, naming clusters, read/write path map,
    table-definition local rules, database-level local rules, stored procedure
    analysis, external dependency map, or mismatch list for the design scope
  - live DB verification status is required by the data change policy but not
    recorded
- When current DB state analysis is missing, create a design work row for
  `db_current_state_analysis` and reload its output before drafting DB design.
- Decide whether constraint derivation is required before implementation-facing
  design closure:
  - use `design_constraint_derivation` for DDL, schema, ER, CRUD, nullable,
    range, enum, relation, default, unique, check, or status behavior gaps
  - use `cross_constraint_derivation` when DDL/schema and code disagree or
    expose different use-case projections
  - use `integration_constraint_derivation` or `async_constraint_derivation`
    when database changes affect APIs, files, messages, jobs, queues, or
    schedules
  - use `commonality_derivation` when multiple derivation outputs reveal
    repeated patterns or ownership conflicts
- Prepare output rows for design package, derivation dependencies,
  verification checks, unresolved assumptions, and handoff notes.
- Prepare XDDP traceability rows for each DB design item. Each row must link the
  requirement difference to the logical/physical change, affected DB object or
  persistence source target, current-state evidence, migration/correction action,
  validation handoff, and unknown or out-of-scope state when applicable.

## Execution

- Draft the DB design package from the current database state analysis and
  current source-structure findings. Separate:
  - requirement confirmations
  - design-time decisions
  - implementation steps
  - release or operational steps
- Maintain DB design traceability as the package is drafted. Do not add a table,
  column, procedure, query, migration, correction, transaction, or naming
  decision unless it traces to a requirement difference and to current DB/source
  evidence or an explicit `unknown`.
- Define logical model changes:
  - ownership, entity meaning, relation, cardinality, optionality, lifecycle,
    state, and business invariant
- Define physical model changes:
  - table, column, type, precision, nullability, default, computed value, index,
    constraint, partition, schema, storage, or migration artifact
- Apply table-definition local rules from current-state analysis before
  proposing column names, DB types, lengths, precision, scale, nullability,
  defaults, identities, computed columns, collation, or concurrency columns.
  Record comparison tables and rule confidence.
- Apply database-level local rules from the current-state analysis when the
  design includes stored procedures, raw SQL, transaction boundaries, or
  database-specific conventions. Record the rule source and confidence.
- Apply stored procedure naming rules from the current-state analysis before
  proposing stored procedure names. Record the schema-to-purpose rule,
  verb/action vocabulary, object term rule, suffix/prefix rule, casing and
  separator rule, operation-family pattern, examples, exceptions, and
  confidence.
- Apply stored procedure analysis from the current-state analysis when the
  design creates, changes, replaces, or calls stored procedures. Do not choose
  `OUTPUT` parameters, result sets/datasets, scalar `SELECT`, integer
  `RETURN`, status/message outputs, side-effect-only behavior, error-based
  behavior, or mixed result patterns without current-state evidence or an
  explicit `unknown`.
- Apply transaction-granularity evidence from stored procedure analysis before
  selecting caller-controlled transaction, whole-procedure transaction,
  operation-block transaction, per-row/per-item transaction, per-batch/chunk
  transaction, nested transaction/savepoint, ambient transaction, job-level
  transaction, migration/deployment transaction, or external framework
  transaction.
- Apply isolation-level evidence before selecting explicit isolation,
  caller/session/database-default isolation, native-procedure isolation options,
  or table-hint based isolation.
- Apply SQL error-handling style evidence before selecting `TRY/CATCH`,
  `@@ERROR`, `THROW`, `RAISERROR`, return-code based, output-status/message
  based, no explicit error handling, or mixed error handling.
- Apply DDL/query construction rules from the current-state analysis when the
  design includes table creation, object replacement, migration scripts,
  rollback scripts, seed scripts, or destructive operations. Record whether
  existing scripts use `DROP`, existence checks before `DROP`, idempotent
  guards, or one-shot migration style.
- Treat the DB-unit SQL export basis recorded by current-state analysis as the
  primary DB-object basis. If design evidence comes only from ORM or code, mark
  it as secondary and record the missing SQL-export confirmation.
- Derive names from the current database state analysis first, then cross-check
  source-structure naming evidence for external or data-flow-visible names.
  Record:
  - source-structure finding XID
  - current database state analysis report or XID
  - DB naming rule analysis section
  - Brownfield API Naming Extractor section when the name crosses an external
    or data-flow boundary
  - existing examples that justify the candidate
  - rule confidence: `strong`, `mixed`, `weak`, or `unknown`
  - candidate name or explicit `unknown`
- Map read/write impact:
  - API/command/query/job/event/report paths that read the data
  - API/command/query/job/event/report paths that write the data
  - transaction and consistency boundary
  - concurrency, idempotency, retry, and conflict behavior
- Design migration and data correction:
  - DDL order
  - backfill or defaulting
  - batching and locking risks
  - validation and reconciliation checks
  - rollback or forward-fix approach
  - whether a dedicated correction tool is required
- Incorporate confirmed constraint-derivation outputs. If required derivation
  has not run, mark the affected design area `unknown` and stop before
  implementation-facing closure.
- Produce a design package that implementation can review before coding.

## Output Shape

Use this shape or an equivalent structure:

```md
# Database Design: <target>

## Summary

## Scope

## Source Analysis Basis

## Current Database State Basis

## DB-Unit SQL Export Basis

## Existing Persistence Structure

## Logical Model Design

## Physical Model Design

## DB Naming Rule Basis And Candidate Names

## Table-Definition Rule Basis

## Stored Procedure, Transaction, And SQL Rule Basis

## Stored Procedure Return And Transaction Granularity Basis

## Isolation And Error-Handling Rule Basis

## DDL And Query Construction Rule Basis

## Read/Write Path Impact

## Migration And Data Correction Plan

## Transaction, Consistency, And Concurrency

## Compatibility, Rollout, And Rollback

## Validation And Reconciliation Checks

## Required Constraint-Derivation Outputs

## Unknowns And Escalations

## Handoff
```

## Monitoring And Control

- Do not treat ORM mappings, DDL, or migrations as complete requirements when
  behavior is ambiguous.
- Do not invent default, null, duplicate, missing-reference, delete-chain,
  status-transition, or conflict behavior. Route to constraint derivation or
  record `unknown`.
- Do not propose DB names without current database state naming rule analysis.
- Do not propose table columns, DB types, lengths, precision, scale,
  nullability, defaults, identity, computed columns, collation, or concurrency
  columns without table-definition local rules from current-state analysis.
- Do not propose stored procedure shape, transaction boundary, or SQL writing
  style without database-level local rules from current-state analysis.
- Do not propose stored procedure names without stored procedure naming rules
  from current-state analysis. Stored procedure naming must be based on
  existing procedure names and callers, not table names alone.
- Do not choose stored procedure return style from preference. `OUTPUT`
  parameters, result sets/datasets, scalar `SELECT`, integer `RETURN`,
  status/message outputs, side-effect-only behavior, error-based behavior, and
  mixed result patterns require current-state evidence or must remain
  `unknown`.
- Do not choose transaction granularity from preference. Caller-controlled,
  whole-procedure, operation-block, per-row/per-item, per-batch/chunk, nested,
  ambient, job-level, migration/deployment, and external framework transaction
  choices require current-state evidence or must remain `unknown`.
- Do not choose isolation level from preference. Explicit isolation,
  caller/session/database-default isolation, native-procedure isolation options,
  and table-hint based isolation require current-state evidence or must remain
  `unknown`.
- Do not choose SQL error-handling style from preference. `TRY/CATCH`,
  `@@ERROR`, `THROW`, `RAISERROR`, return-code based, output-status/message
  based, no explicit error handling, and mixed patterns require current-state
  evidence or must remain `unknown`.
- Do not choose `DROP`, omit `DROP`, add existence checks, omit existence
  checks, or choose an idempotent/one-shot script style without DDL/query
  construction rules from current-state analysis.
- Do not propose external or data-flow-visible names without registered
  source-structure naming evidence.
- Do not proceed from raw DDL or ORM snippets alone when a current database
  state analysis is required for the target.
- Do not treat ORM or code evidence as the primary DB-object basis when the
  current-state analysis has a DB-unit SQL export basis or marks that basis
  missing.
- Do not hide data migration, data correction, compatibility, rollback,
  transaction, or concurrency assumptions inside implementation notes.
- Stop if DB design closure would require implementation to guess behavior,
  naming, data ownership, migration order, or external dependency values.
- Keep implementation and migration execution out of this Skill.

## Closure

- Confirm the DB design package includes:
  - source-analysis basis XIDs
  - current database state analysis reference
  - DB-unit SQL export basis or explicit missing-impact note
  - existing persistence evidence
  - logical and physical design
  - DB naming rule basis and candidate names or explicit `unknown`
  - table-definition local rule basis when table or column design is in scope
  - stored procedure naming rule basis when stored procedure names are in scope
  - stored procedure granularity, transaction configuration, and SQL writing
    rule basis when applicable
  - stored procedure return/result convention and transaction granularity basis
    when stored procedure design is in scope
  - isolation level and SQL error-handling rule basis when SQL transaction or
    stored procedure behavior is in scope
  - DDL/query construction rule basis when migration or SQL script design is in
    scope
  - read/write path impact
  - migration and correction plan
  - transaction, consistency, and concurrency notes
  - compatibility, rollout, rollback, validation, and reconciliation notes
  - required constraint-derivation outputs or explicit `not_required`
  - XDDP traceability rows from requirement differences to DB design items,
    evidence basis, impacted DB/source targets, migration/correction actions,
    validation handoff, and unknown or out-of-scope items
  - unresolved assumptions and handoff owner
  - every `unknown` DB design item with reason, missing evidence or missing
    decision, affected table/procedure/query/source area, downstream impact, and
    handoff or confirmation owner
- Closure is blocked when required current database state analysis,
  source-structure findings, naming evidence, or constraint-derivation outputs
  are missing for implementation-facing DB design.

## Handoff

- Hand off the DB design package to `design_flow` or `implementation_flow`.
- Hand off current-state gaps to `db_current_state_analysis`.
- Hand off unresolved behavior to the matching constraint-derivation Skill.
- Hand off source-structure gaps to `source_structure_overview` and
  `source_structure_findings_registration`.

---
schema_version: 1
skill_id: db_current_state_analysis
xid: B6D4A1E9C730
aliases:
  - C48A0E2D91F5
  - 6B8C70DA119E
summary: Analyze a brownfield database and persistence structure from repository evidence before database design
applies_when:
  - A brownfield task needs current database, schema, persistence, naming, ownership, or read/write-path understanding before DB design or migration planning
exclusions:
  - Do not design a new schema or implement migrations or application code
  - Do not infer live database state or business meaning from names alone
inputs:
  - Target repository, solution, project, module, or database scope and explicit source boundary
  - A DB-unit SQL export or an explicit missing status for every database in scope
  - Current source-structure finding XIDs and secondary ORM, migration, repository, raw SQL, seed, report, job, API, and integration evidence
  - Optional live database evidence and prior DB knowledge
outputs:
  - Current-state analysis report with SQL-export basis, persistence inventory, logical and physical models, local naming rules, read/write paths, risks, mismatches, unknowns, and handoff to db_design
criteria:
  - id: sql_export_basis
    statement: Each database in scope has a recorded DB-unit SQL export basis or an explicit missing status, and source versus live verification is distinguished
    verification: Inspect the report evidence inventory and DB-Unit SQL Export Basis sections
  - id: reusable_rule_surface
    statement: The report records reusable DB naming, table-definition, database-level, and stored-procedure rules with confidence, exceptions, and evidence, or marks each area unknown or not_applicable
    verification: Check the required rule sections and their evidence before closure
  - id: design_handoff
    statement: Read/write paths, mismatches, live verification status, unresolved items, and a concrete handoff to db_design are present
    verification: Review the handoff and unknowns against the in-scope persistence objects
knowledge_needs:
  - id: database_current_state_analysis_viewpoints
    query: database current-state analysis viewpoints
    required_when: Required for current-state coverage before claiming analysis completion
    seed_xids:
      - F9B3C6A70412
  - id: database_design_viewpoints
    query: database design viewpoints relevant to reusable current-state rules
    required_when: Required when framing the handoff and reusable design inputs
    seed_xids:
      - E7D4A11B8C06
  - id: current_source_structure_findings_catalog
    query: current source structure findings catalog
    required_when: Required when source-structure findings are used as application context
    seed_xids:
      - A9E742B1C6D0
  - id: csharp_naming_convention_extraction
    query: CSharp naming-convention extraction
    required_when: Required when CSharp artifacts contribute naming evidence
    seed_xids:
      - B4F7E1A2C903
control_refs: []
---
<!-- xid: B6D4A1E9C730 -->
<a id="xid-B6D4A1E9C730"></a>

# Skill: db_current_state_analysis

## Purpose

Analyze what exists now in a brownfield database and persistence structure. This
Skill produces a reusable evidence basis for `db_design`; it does not design the
future schema, implement migrations, or decide missing requirements.

## Method

Confirm the target path, source scope, output path, current source-structure
finding XIDs, and whether the task is current-state analysis rather than design.
For every database, identify the DB-unit SQL export (DDL, generated migration
SQL, checked-in script, or vendor export) and record its identity, generation
source/version, object classes, exclusions, ordering and transaction-wrapper
semantics, or record `missing`. Treat this export as primary evidence for object
shape and DB-local rules. Use ORM mappings, DbContexts, repositories, raw SQL,
migrations, seed data, reports, jobs, APIs, tests, and integration handlers as
secondary cross-check evidence; record disagreements as mismatches.

Build a fixed worklist covering persistence inventory; logical and physical
models; database, schema, table, column, constraint, index, migration, ORM, raw
SQL, job, message, and configuration naming rules; naming clusters; table local
rules for names, types, lengths, precision, scale, nullability, defaults,
identity, computed, collation, and concurrency; and per-database rules for
stored-procedure granularity, transaction configuration, isolation, SQL style,
error handling, and DDL/query construction including `DROP` and existence
checks. Analyze stored procedures from the export and callers for naming,
purpose, result/return convention, transaction boundary and granularity,
isolation, errors, dependencies, and ownership. Map read and write paths,
external boundaries, migration authority, operational risks, and SQL-export /
ORM / code mismatches.

Do not infer business meaning from names, ownership or transaction behavior
without evidence. Do not infer live DB state from repository files; mark it
`not_verified` unless directly evidenced. Keep confidence (`strong`, `mixed`,
`weak`, or `unknown`) and exceptions for each reusable rule. If scope narrows
silently, a design decision is being made, or required evidence is missing,
stop or hand off with an explicit `unknown`. Closure requires the current-state
report, evidence inventory, all required rule sections or explicit
`not_applicable`, read/write maps, live status, mismatches, unresolved items,
and concrete rules and evidence for `db_design`.

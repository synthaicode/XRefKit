---
schema_version: 1
skill_id: db_design
xid: C7E5B2F0D841
aliases:
  - A68F54D72C19
  - 5D7C2A90B631
summary: Produce implementation-ready brownfield database design artifacts from approved requirements and current database evidence
applies_when:
  - An approved requirement changes a database, persistence boundary, migration, ORM mapping, query path, data correction, or compatibility plan
exclusions:
  - Do not implement migrations or application code
  - Do not decide missing business requirements or design from stale or missing current-state evidence
inputs:
  - Approved requirements, work plan, source-modification policy, and data-change policy
  - Current source-structure finding XIDs and current database-state analysis for every target
  - DB-unit SQL export basis and existing DDL, migrations, ORM, raw SQL, seed, report, and integration evidence
  - Optional confirmed constraint-derivation outputs
outputs:
  - Database design package with logical and physical changes, naming basis, read/write impact, migration and correction plan, transaction and consistency notes, validation handoff, XDDP traceability, unknowns, and unresolved assumptions
criteria:
  - id: current_state_gate
    statement: Every target has current source and database analysis, including SQL-export basis or explicit missing status, before design is frozen
    verification: Check the source-analysis, current-state, and DB-Unit SQL Export Basis sections for each target
  - id: evidence_traceability
    statement: Every design item traces to a requirement difference and current evidence or an explicit unknown, with local rule confidence and naming basis recorded
    verification: Inspect XDDP rows and the logical, physical, naming, and rule-basis sections
  - id: implementation_handoff
    statement: Migration, correction, validation, rollback, unresolved-item, and downstream handoff notes are complete or explicitly blocked
    verification: Review the design package closure and handoff against all affected paths
knowledge_needs:
  - id: database_design_viewpoints
    query: database design viewpoints
    required_when: Required for logical, physical, migration, and persistence design coverage
    seed_xids:
      - E7D4A11B8C06
  - id: database_current_state_analysis_viewpoints
    query: database current-state analysis viewpoints
    required_when: Required when consuming current-state evidence and local DB rules
    seed_xids:
      - F9B3C6A70412
  - id: current_source_structure_findings_catalog
    query: current source structure findings catalog
    required_when: Required when source boundaries or names affect the design
    seed_xids:
      - A9E742B1C6D0
  - id: csharp_naming_convention_extraction
    query: CSharp naming-convention extraction
    required_when: Required when CSharp or external data-flow names are designed
    seed_xids:
      - B4F7E1A2C903
  - id: design_constraint_derivation_catalog
    query: design constraint derivation catalog
    required_when: Required for schema, relation, nullability, range, enum, default, unique, check, or status gaps
    seed_xids:
      - 2D14F88A6C01
control_refs: []
---
<!-- xid: C7E5B2F0D841 -->
<a id="xid-C7E5B2F0D841"></a>

# Skill: db_design

## Purpose

Produce an implementation-ready brownfield database design package from
approved planning inputs, current source-structure findings, and current
database evidence. This Skill designs changes; it does not implement them or
decide missing business requirements.

## Method

Confirm approved requirements, work plan, source-modification policy,
data-change policy, and the target database/schema/persistence boundary. Confirm
that every target has current source findings and a current-state analysis with
the DB-unit SQL export basis, naming clusters, table-definition local rules,
database-level rules, stored-procedure analysis, read/write paths, mismatches,
and live verification status. If the analysis is missing or stale, route that
target back to `db_current_state_analysis`; if source findings are missing,
route to source-structure analysis. If required constraint derivation is absent,
keep the affected design area `unknown` and stop before implementation-facing
closure.

Classify the design area and its structural authorities. Maintain XDDP
traceability for each design item: requirement difference, logical/physical
change, affected DB or persistence target, current evidence, migration or
correction action, validation handoff, and unknown state. Apply the selected
current-state table rules for names, types, lengths, precision, scale,
nullability, defaults, identity, computed, collation, and concurrency. Apply
database-level SQL, DDL, stored-procedure naming, return/result, transaction,
isolation, and error-handling rules with their confidence and exceptions.

Design logical ownership, relations, lifecycle, and invariants; physical tables,
columns, indexes, constraints, schemas, and storage; read/write and data-flow
impact; migration order, backfill, batching, locking, reconciliation, rollback
or forward-fix; transaction, consistency, idempotency, concurrency, and retry
behavior; and implementation and test handoff. Treat the DB-unit SQL export as
the primary DB-object basis and ORM/code as secondary. Never guess when DDL,
ORM, code, or live state disagree: record the mismatch and hand it to
constraint derivation or a human owner. Closure requires a design package with
source and current-state XIDs, SQL-export basis, evidence, XDDP rows, unknowns,
validation checks, and an explicit downstream handoff.

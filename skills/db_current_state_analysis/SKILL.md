<!-- xid: C48A0E2D91F5 -->
<a id="xid-C48A0E2D91F5"></a>

# Skill: db_current_state_analysis

## Purpose

Analyze the current database and persistence structure of a brownfield system
before DB design.

This Skill answers "what exists now and how is it used?" It does not design the
future schema, implement migrations, or decide missing requirements.

## Required Knowledge (XID)

- [Database current-state analysis viewpoints](../../knowledge/database/110_database_current_state_analysis_viewpoints.md#xid-F9B3C6A70412)
- [Database design viewpoints](../../knowledge/database/100_database_design_viewpoints.md#xid-E7D4A11B8C06)
- [Current source structure findings catalog](../../knowledge/source_analysis/170_current_source_structure_findings_catalog.md#xid-A9E742B1C6D0)
- [CSharp naming-convention extraction](../../knowledge/source_analysis/140_csharp_naming_convention_extraction.md#xid-B4F7E1A2C903)

## Inputs

- target repository, solution, project, module, or database-related directory
- explicit source scope boundary
- current source-structure finding XIDs
- DB-unit SQL export files for each database in scope, such as DDL/schema/script
  dumps, migration-generated SQL, or checked-in database scripts
- migration, ORM mapping, DbContext/DbSet, repository, raw SQL, seed data,
  fixture, report, job, API, event, or integration-handler evidence used as
  secondary cross-check evidence
- optional live database inspection evidence
- optional prior DB knowledge

## Outputs

- current database state analysis report
- DB-unit SQL export basis for each database
- persistence inventory
- current logical model
- current physical model
- DB naming rule analysis and naming clusters
- table-definition local rules for column names, types, lengths, precision,
  scale, nullability, defaults, identity, computed, collation, and concurrency
  fields
- database-level local rules for naming, stored procedure granularity,
  transaction configuration, SQL writing style, and DDL/query construction
  rules
- stored procedure analysis for naming rules, purpose, return/result
  convention, transaction granularity, error style, and ownership evidence
- read/write path map
- data-flow boundary map
- external dependency and operational risk map
- DDL/ORM/code mismatch list
- unresolved verification and live DB verification status
- reusable metadata and handoff to `db_design`

## Startup

- Start through `fm skill run`.
- Confirm the target path and source scope boundary.
- Confirm the DB-unit SQL export file or file set for each database in scope.
  If no DB-unit SQL export exists, record it as `missing` and decide whether the
  analysis can continue from secondary evidence or must stop as `unknown`.
- Confirm the source-structure finding XIDs that describe the application or
  module context around the database.
- Confirm whether live DB access is available. If not, proceed source-first and
  record live DB status as `not_verified`.
- Confirm the output path.
- Confirm the task is current-state analysis, not DB design or migration
  implementation.
- Load only DB-relevant knowledge and selected prior findings.

## Planning

Create concrete work rows for the fixed scope:

- persistence inventory
- DB-unit SQL export basis inventory
- logical model extraction
- physical model extraction
- DB naming rule analysis and naming-cluster extraction
- table-definition local rule extraction by comparing existing tables in the
  same DB-unit SQL export:
  - column name rules
  - type selection rules
  - length, precision, and scale rules
  - nullability, default, identity, computed, collation, and concurrency rules
- database-level local rule extraction:
  - naming rules
  - stored procedure granularity
  - transaction configuration method
  - SQL writing rules
  - DDL/query construction rules including `DROP` usage and object-existence
    checks
- stored procedure analysis:
  - stored procedure naming rules by procedure class
  - procedure purpose and granularity
  - return/result convention
  - transaction boundary and granularity
  - isolation level and isolation-related hints
  - error, status, and row-count behavior
  - procedure-to-table ownership and caller evidence
- read path discovery
- write path discovery
- data-flow and external boundary map
- migration authority and operational risk review
- mismatch detection
- unresolved verification and design handoff

Use grep-first discovery for file-based structure. Prefer deterministic tools
when available, but do not require live DB tooling for source-first analysis.

Relevant evidence searches include:

- DB-unit SQL export files, DDL files, `.sql`, `.sqlproj`, migration-generated
  SQL, generated scripts, checked-in database scripts, seed files
- ORM mappings, entity type configurations, DbContext/DbSet declarations,
  repositories, query builders, raw SQL strings, stored procedure calls
- API commands/queries, event handlers, jobs, reports, batch scripts, correction
  tools, import/export code, and tests that reveal read/write behavior
- connection strings, schema names, migration tooling, package/tool versions,
  environment variables, deployment scripts, and feature switches

## Execution

### DB-Unit SQL Export Basis

- For each database in scope, identify the SQL export file or file set that is
  the primary basis for DB object and DB-local rule analysis.
- Record:
  - database identity and expected DBMS
  - SQL file path or source locator
  - generation source, such as live DB scripting, migration-generated SQL,
    checked-in DDL, vendor export, or tool output
  - generation date, commit, version, or `unknown`
  - included object classes: schema, table, view, index, constraint, sequence,
    trigger, procedure, function, synonym, seed data, and permissions
  - excluded or unsupported object classes
  - whether object order, dependency order, transaction wrappers, batch
    separators, comments, and tool headers are meaningful or generated noise
- Treat the DB-unit SQL export as primary evidence for DB object shape and
  DB-local rules. Use ORM, migrations, repositories, raw SQL, jobs, reports, and
  tests as secondary cross-check evidence.
- If secondary evidence disagrees with the DB-unit SQL export, record a
  mismatch instead of choosing a winner.

### Persistence Inventory

- List databases, schemas, tables, views, collections, streams, migrations,
  seed data, generated scripts, and persistence frameworks from the DB-unit SQL
  export first, then cross-check with secondary evidence.
- Mark out-of-scope persistence artifacts explicitly.
- Record whether each item is source-proven, live-verified, or unknown.

### Logical Model

- Derive current entity meanings, relationships, cardinality, optionality,
  lifecycle, status fields, and visible business invariants.
- Derive meaning from DDL, ORM mapping, code usage, tests, and source-structure
  findings. Do not infer business meaning from names alone when behavior is not
  visible.

### Physical Model

- Record table/column/type/precision/nullability/default/computed/index/key/
  constraint/schema/partition/storage facts that are visible from source.
- Keep DBMS-specific behavior explicit when it affects design.
- Mark source vs live DB differences as `unknown` unless verified.

### DB Naming Rule Analysis

- Extract naming rules for table, column, schema, constraint, index, migration,
  entity, DbSet, repository, raw SQL, job, message, seed, report, correction
  tool, generated artifact, and configuration names.
- Use deterministic naming profiles for C# artifacts when useful.
- Separate the naming surfaces. Do not collapse table rules, column rules,
  index/constraint rules, migration rules, and ORM type rules into one generic
  convention.
- For each naming surface, record:
  - casing and separator rule
  - singular/plural rule
  - prefix and suffix rule
  - abbreviation/acronym rule
  - module/schema/bounded-context prefix rule
  - lifecycle/status vocabulary
  - ORM-to-DB translation rule
  - raw SQL alias rule
  - examples and exceptions
  - confidence: `strong`, `mixed`, `weak`, or `unknown`
- Record naming clusters that must stay aligned, such as:
  - table + entity + DbSet + entity configuration + repository
  - migration name + DDL script + generated artifact
  - schema/table + raw SQL + report/query projection
  - config key + connection string + DbContext/module startup
  - outbox/inbox table + stored type name + handler
- Record candidate-name construction rules for `db_design`, not candidate names
  for a specific future change. A construction rule states how current local
  evidence combines business object terms, state/lifecycle terms, module/schema
  terms, and technical suffix/prefix patterns.

For stored procedures, extract procedure-class naming rules instead of one
generic procedure naming rule. Record:

- schema-to-purpose rule, such as API, website, integration, simulation,
  configuration, sequence, maintenance, or reporting schemas
- verb/action vocabulary, such as `Get`, `SearchFor`, `Insert`, `Update`,
  `Delete`, `Create`, `Add`, `Record`, `Populate`, `Reseed`, `Apply`, `Remove`,
  `Enable`, or `Disable`
- object term rule, including singular/plural treatment and whether the object
  term matches table, view, API resource, report projection, job concept, or
  integration payload terms
- suffix/prefix rule, such as `FromJson`, `Updates`, `IfNonexistent`,
  `ForYear`, `ToCurrentDate`, or configuration prefixes
- separator and casing rule, including whether procedure names use
  `PascalCase`, underscores between category/action segments, bracketed
  identifiers, or schema-qualified names
- operation-family rule, such as `Insert{Object}FromJson`,
  `Update{Object}FromJson`, `Delete{Object}`, `SearchFor{Object}`,
  `Get{Object}Updates`, `GetRandom{Object}`, or
  `Configuration_{Action}{Feature}`
- exception rule, including legacy names, one-off maintenance procedures, and
  names that intentionally do not match the dominant operation family
- candidate-name construction rule for future procedure design

Do not infer stored procedure naming from table naming alone. Procedure names
must be derived from existing procedure names and their callers.

### Table-Definition Local Rules

For table design, compare existing table definitions inside the same DB-unit
SQL export. Prefer comparison targets from the same database, schema, module,
bounded context, or table family before using broader repository examples.

For each recurring column role, record the local rule and evidence:

- column-name rules:
  - primary key, foreign key, natural key/code, display/name/title,
    description/memo/comment, status/type/category, amount/quantity/rate/
    percent, date/time/timestamp, audit, logical delete, tenant/organization,
    partition, and concurrency/version fields
- type rules:
  - DB type by role
  - unicode vs non-unicode string
  - fixed vs variable length string
  - integer size
  - decimal precision/scale for money, rate, quantity, or percentage
  - date/time type and timezone convention
  - boolean/flag representation
  - enum/status representation
  - binary/json/xml/text representation
- size rules:
  - string length by role
  - numeric precision and scale by role
  - max-length exceptions and evidence
  - whether sizes appear to be business limits, DB defaults, powers of two, or
    copied legacy patterns
- constraint/default rules:
  - nullability by role
  - default usage and default-constraint naming
  - identity/sequence usage
  - computed columns
  - check constraints
  - collation or character-set overrides
  - rowversion/version/concurrency tokens

Record rule confidence as `strong`, `mixed`, `weak`, or `unknown`. If existing
tables disagree, split the rule by schema, module, artifact age, or table
family instead of forcing one rule.

These rules are design inputs. Do not use this Skill to choose the final column
definition for a future table; hand the extracted local rules to `db_design`.

### Database-Level Local Rules

For each database in scope, extract a local rule set. Do not merge rules across
databases unless source evidence shows they intentionally share the same
convention.

For each database, record:

- naming rules:
  - database, schema, table, view, column, key, constraint, index, trigger,
    procedure, function, migration, seed, entity, DbSet, repository, raw SQL
    alias, and configuration naming rules
  - casing/separator, singular/plural, prefix/suffix, abbreviation/acronym,
    schema/module prefix, lifecycle/status vocabulary, and exceptions
- stored procedure granularity:
  - entity-level, use-case-level, report/query-level, command-level,
    batch-level, integration-level, maintenance-level, migration-support, or
    reusable primitive
  - whether one procedure corresponds to one operation, one workflow step, a
    whole workflow, or a reusable lower-level data access primitive
  - parameter naming, result-shape naming, error/return-code style,
    temp-table/table-variable style, and procedure-to-table ownership evidence
- transaction configuration method:
  - application unit of work, ORM transaction, explicit SQL transaction, stored
    procedure transaction, ambient transaction, job framework, migration tool,
    or external runtime setting
  - isolation level, timeout, retry, deadlock handling, idempotency marker,
    lock hint, savepoint, compensation, and rollback style when visible
  - whether isolation is explicit, inherited from caller/session/database
    defaults, native-procedure scoped, table-hint based, or unknown
  - whether transaction behavior is DB-global, schema/module-local,
    procedure-local, command-local, job-local, or tool-specific
- SQL writing rules:
  - keyword casing, identifier quoting, schema qualification, alias style,
    join layout, CTE/temp-table usage, parameter style, variable naming,
    dynamic SQL policy, pagination pattern, upsert/merge pattern, null
    handling, date/time handling, status filtering, soft-delete filtering, and
    ordering rules
  - whether raw SQL, stored procedures, migrations, reports, and ORM-generated
    SQL share one rule or use separate rules
  - error-handling style:
    - `TRY/CATCH`
    - `@@ERROR` after statements
    - `THROW`
    - `RAISERROR`
    - return-code based
    - output-status/message based
    - no explicit error handling
    - mixed by procedure class or artifact type
- DDL/query construction rules:
  - whether scripts attach `DROP` before `CREATE`, avoid `DROP`, or prefer
    `CREATE OR ALTER`, `CREATE OR REPLACE`, or `ALTER`
  - whether scripts check object existence before `DROP`, `CREATE`, `ALTER`,
    `TRUNCATE`, `DELETE`, index operations, or constraint operations
  - object-existence check idiom, such as `IF EXISTS`, `IF OBJECT_ID(...)`,
    `INFORMATION_SCHEMA`, system catalog queries, `DROP ... IF EXISTS`, or
    DBMS-specific equivalents
  - whether destructive statements require guards, comments, transactions,
    backup/reconciliation notes, or environment gates
  - whether scripts are idempotent, one-shot migration scripts, rollback
    scripts, repeatable deployment scripts, or generated snapshots
  - object operation ordering, batch separators, statement terminators, `SET`
    options, schema qualification, and dependency-handling patterns
  - whether table, view, procedure, function, trigger, index, constraint, seed,
    and permission scripts use different construction rules

For each area, record confidence as `strong`, `mixed`, `weak`, or `unknown`.
If a database has multiple rules by schema, module, artifact age, or tool, keep
the split explicit.

### Stored Procedure Analysis

For each stored procedure in scope, classify its purpose and behavior from the
DB-unit SQL export first, then cross-check callers, reports, jobs, tests, and
raw SQL invocation code.

The purpose is to extract reusable local rules for later DB design. Do not turn
this section into line-by-line query review, query tuning, or individual stored
procedure critique. Keep individual procedures as evidence for procedure-class
rules.

Record:

- stored procedure naming:
  - schema-to-purpose rule
  - verb/action vocabulary
  - object term and singular/plural rule
  - suffix/prefix rule
  - casing and separator rule
  - operation-family pattern
  - exceptions and candidate-name construction rule
- procedure purpose and granularity:
  - entity-level, use-case-level, command-level, query/report-level,
    batch-level, integration-level, maintenance-level, migration-support, or
    reusable primitive
  - whether the procedure represents one operation, one workflow step, a whole
    workflow, one report/query projection, or a lower-level data access helper
- return/result convention:
  - `OUTPUT` parameter based
  - DML `OUTPUT` clause result set, such as `OUTPUT inserted.<column>` or
    `OUTPUT deleted.<column>`
  - single result set / dataset based
  - multiple result sets
  - scalar `SELECT`
  - integer `RETURN` code
  - status/message output parameters
  - row-count based, such as `@@ROWCOUNT`
  - side-effect only with no data result
  - exception/error based, such as `RAISERROR` or `THROW`
  - mixed pattern
- transaction boundary and granularity:
  - no transaction inside the procedure; caller or application controls it
  - whole procedure transaction
  - operation-block transaction
  - per-row or per-item transaction
  - per-batch or chunk transaction
  - nested transaction or savepoint
  - ambient transaction
  - job-level, migration/deployment-level, or external tool/framework
    transaction
  - visible isolation level, timeout, retry, deadlock handling, lock hints,
    idempotency markers, compensation, and rollback behavior
- isolation level:
  - explicit isolation level, such as `SNAPSHOT`, `SERIALIZABLE`,
    `REPEATABLE READ`, `READ COMMITTED`, or `READ UNCOMMITTED`
  - native procedure isolation option
  - table hint based isolation, such as `WITH (SNAPSHOT)`
  - caller/session/database default
  - unknown
- parameter, result-shape, and procedure naming
- temp table, table variable, cursor, dynamic SQL, and common table expression
  usage when it affects design
- error, status, message, and validation style, including whether the local
  rule is `TRY/CATCH`, `@@ERROR`, `THROW`, `RAISERROR`, return-code based,
  output-status/message based, no explicit error handling, or mixed
- table, view, function, and external object dependencies
- caller evidence and expected consumers

Group SP conventions by procedure class when needed. Command procedures,
query/report procedures, batch procedures, integration procedures, and utility
procedures may intentionally use different return/result and transaction
rules. Do not force one database-global rule when local evidence is split.

Record confidence as `strong`, `mixed`, `weak`, or `unknown`. If `OUTPUT`
parameters and result sets are both used, identify the local selection rule
instead of treating the database as inconsistent.

### Read And Write Paths

- Map current read paths from APIs, queries, reports, jobs, projections, raw
  SQL, integration handlers, and tests.
- Map current write paths from commands, repositories, ORM saves, migrations,
  seeders, jobs, event handlers, raw SQL, imports, and correction tools.
- Record transaction, consistency, concurrency, idempotency, and retry evidence
  only when visible. Otherwise record `unknown`.

### External Dependency And Operational Risk Map

- Identify external levers that can change DB behavior or structure:
  connection strings, schemas, migration tooling, generated scripts, deployment
  order, seed files, package versions, linked services, reports, feature
  switches, and environment variables.
- Record operational risks visible from source:
  irreversible migrations, large backfills, long locks, manual scripts,
  missing rollback, missing reconciliation, and live DB dependency unknowns.

### Mismatch Detection

Record mismatches and weak assumptions, including:

- DDL exists but ORM mapping is absent or inconsistent.
- ORM mapping exists but DDL/migration authority is unclear.
- table/column appears in raw SQL but not in the ORM model.
- code writes a structure that reports/jobs read under different assumptions.
- source has migration history but current live DB status is not verified.
- naming cluster members drift from each other.

Do not choose a winner between DDL, ORM, and code when they disagree. Record the
mismatch and hand it to `db_design` or constraint derivation.

## Output Shape

Use this shape or an equivalent structure:

```md
# Database Current-State Analysis: <target>

## Summary

## Scope

## Source Analysis Basis

## Evidence Inventory

## DB-Unit SQL Export Basis

## Persistence Inventory

## Current Logical Model

## Current Physical Model

## DB Naming Rule Analysis

## Naming Clusters

## Table-Definition Local Rules

## Database-Level Local Rules

## Stored Procedure Analysis

## Read Path Map

## Write Path Map

## Data-Flow And External Boundaries

## Migration Authority And Operational Risks

## Mismatches And Weak Assumptions

## Live DB Verification Status

## Conclusion For Design Reuse

## Reuse Metadata

## Unknowns And Handoff
```

### Conclusion For Design Reuse

The conclusion is not a short summary. It is the reusable decision surface that
`db_design` consumes. Write it as rules and selection criteria, not as examples
or individual query notes.

Include these fixed axes:

- applicability boundary:
  - database, schema, module, procedure class, table family, artifact age, and
    source basis where the conclusion applies
- rule selection keys:
  - how to choose the relevant local rule, such as schema, procedure class,
    operation family, read/write role, API/report/job boundary, table family,
    or migration/deployment artifact type
- naming rules:
  - table, column, constraint, index, migration, ORM, raw SQL alias, and stored
    procedure naming rules that design may reuse
- stored procedure contract rules:
  - procedure naming, granularity, return/result convention, transaction
    boundary and granularity, isolation level, error/status behavior, and caller
    expectations
- table-definition rules:
  - column role to name/type/length/precision/scale/nullability/default/
    identity/computed/collation/concurrency rules
- SQL and DDL construction rules:
  - `DROP` usage, existence checks, idempotency, batch separators, destructive
    guards, statement ordering, error-handling style, and script class
    differences
- transaction and consistency rules:
  - where transaction ownership usually lives, which classes use explicit
    transactions, isolation level, retry/idempotency/locking evidence, and
    where behavior is unknown
- exception and split rules:
  - intentional rule splits by schema/module/procedure class/artifact age and
    known exceptions that must not be normalized away
- confidence:
  - `strong`, `mixed`, `weak`, or `unknown` per reusable rule
- unresolved verification:
  - missing live DB checks, missing caller evidence, hidden external controls,
    source/DB drift, and unresolved mismatches
- design handoff:
  - concrete rules `db_design` may apply, rules that require human approval,
    and areas that must remain `unknown` or route to another Skill

Closure must not rely on a conclusion that only says "analysis completed" or
lists examples. If the conclusion cannot state reusable rules on the required
axes, keep the relevant axis `unknown` and hand it off explicitly.

## Monitoring And Control

- Do not design new schema or propose future migration steps in this Skill.
- Do not analyze DB-local naming, stored procedure granularity, transaction
  configuration, or SQL writing style without first identifying the DB-unit SQL
  export basis or explicitly marking it `missing`.
- Do not infer live DB state from repository artifacts; mark live status
  `not_verified` unless direct evidence was provided.
- Do not collapse DDL, ORM, and code mismatches into a single "current state".
- Do not invent ownership, transaction, concurrency, or naming rules without
  source evidence.
- Treat missing read/write path maps as analysis leaks when the DB object is in
  scope and later design depends on it.
- Treat missing DB naming rule analysis as an analysis leak when later DB
  design will propose database, migration, ORM, raw SQL, job, message, or
  configuration names.
- Treat missing table-definition local rules as an analysis leak when later DB
  design will propose table columns, DB types, lengths, precision, scale,
  nullability, defaults, identity, computed columns, collation, or concurrency
  columns.
- Treat missing database-level local rules as an analysis leak when later DB
  design depends on naming, stored procedure granularity, transaction setup, or
  SQL writing style.
- Treat missing stored procedure analysis as an analysis leak when later DB
  design depends on stored procedure naming, purpose, return/result convention,
  transaction boundary, transaction granularity, error behavior, or caller
  expectations.
- Treat missing DDL/query construction rules as an analysis leak when later DB
  design or migration work depends on `DROP` usage, object-existence checks,
  idempotency, batch structure, destructive operation guards, or deployment
  script style.

## Closure

Closure is allowed only when the report includes:

- target identity and source scope
- source-structure finding XIDs used as context
- DB-unit SQL export basis for each database or explicit `missing`
- evidence inventory
- persistence inventory
- logical and physical model sections or explicit `not_applicable`
- DB naming rule analysis and naming clusters or explicit `not_applicable`
- table-definition local rules or explicit `not_applicable`
- database-level local rules for naming, stored procedure granularity,
  transaction configuration, SQL writing style, and DDL/query construction
  rules or explicit
  `not_applicable`
- stored procedure analysis for naming rules, purpose, return/result
  convention, transaction boundary and granularity, error style, and caller
  evidence or explicit
  `not_applicable`
- read and write path maps or explicit `unknown`
- external dependency and operational risk map
- mismatch and unresolved verification list
- live DB verification status
- handoff to `db_design`

Closure is blocked when an in-scope object needed for DB design lacks current
state, naming rule analysis, ownership, or read/write evidence and is not
explicitly marked `unknown` for handoff.

## Handoff

- Hand off complete current-state reports to `db_design`.
- Hand off source-structure gaps to `source_structure_overview` and
  `source_structure_findings_registration`.
- Hand off unresolved DDL/code mismatch or hidden behavior to the matching
  constraint-derivation Skill when design would otherwise guess.

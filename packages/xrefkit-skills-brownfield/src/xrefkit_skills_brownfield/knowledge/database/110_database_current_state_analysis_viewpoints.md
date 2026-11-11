<!-- xid: F9B3C6A70412 -->
<a id="xid-F9B3C6A70412"></a>

# Database Current-State Analysis Viewpoints

## Purpose

This page defines reusable viewpoints for analyzing the current database and
persistence structure of a brownfield system before database design.

The analysis is source-first and database-export-first. It does not assume live
database access. The primary basis is the SQL files exported per database, such
as DDL/schema/script dumps, migration-generated SQL, or other DB-unit SQL
exports. Repository artifacts such as migrations, ORM mappings, DbContexts,
repositories, raw SQL, seed data, jobs, reports, APIs, and integration handlers
are secondary cross-check evidence unless no DB-unit SQL export exists.

## Analysis Axes

| Axis | What to analyze |
| --- | --- |
| DB-unit SQL export basis | SQL files exported per database, including their source, generation method, timestamp or commit, DBMS/version, included object classes, and exclusions. |
| Persistence inventory | Databases, schemas, tables, views, collections, streams, migrations, seed data, and generated scripts in scope. |
| Ownership | Which module, service, aggregate, process, job, report, or external integration appears to own each persisted structure. |
| Logical model | Entity meaning, relation meaning, cardinality, optionality, lifecycle, state fields, and business invariants visible from source. |
| Physical model | Columns, types, precision, nullability, defaults, computed values, indexes, keys, constraints, partitions, and storage boundaries. |
| Naming rule analysis | Table, column, schema, constraint, index, migration, entity, DbSet, repository, raw SQL alias, config key, job, and message naming rules with evidence and exceptions. |
| Table-definition local rules | Column name, data type, length, precision, scale, nullability, default, identity, computed, collation, and timestamp rules derived by comparing other tables in the same DB-unit SQL export. |
| Database-level local rules | Per-database naming rules, stored procedure granularity, transaction configuration method, SQL writing rules, and DDL/query construction rules. |
| Stored procedure analysis | Procedure naming rules, purpose, return/result convention, transaction boundary and granularity, error/status behavior, dependencies, callers, and local rule confidence. |
| Read paths | Queries, reports, APIs, jobs, projections, integration handlers, and raw SQL that read each structure. |
| Write paths | Commands, migrations, jobs, event handlers, repositories, ORM saves, raw SQL, seeders, and correction tools that write each structure. |
| Data-flow boundary | Where persisted data crosses API, batch, event, file, report, cache, queue, or external-system boundaries. |
| External controls | Connection strings, schema names, migration tooling, generated artifacts, scripts, environment variables, package/tool versions, and deployment switches. |
| Operational risks | Long locks, large backfills, missing rollback, manual scripts, irreversible changes, data correction needs, and live-value unknowns. |
| Mismatch signals | DDL vs ORM mismatch, migration history vs current mapping mismatch, code path vs table ownership mismatch, and duplicate rule ownership. |

## Output Expectations

A current-state analysis should produce:

- target identity and source scope
- DB-unit SQL export basis for each database or an explicit `missing`
- evidence inventory and live DB verification status
- current persistence map
- current logical model
- current physical model
- DB naming rule analysis and naming clusters
- table-definition local rules:
  - column naming rules
  - type selection rules
  - length/precision/scale rules
  - nullability/default/identity/computed conventions
- database-level local rules:
  - naming rules
  - stored procedure granularity
  - transaction configuration method
  - SQL writing rules
  - DDL/query construction rules such as `DROP` usage and object-existence
    guards
- stored procedure analysis:
  - stored procedure naming rules by procedure class
  - procedure purpose and granularity
  - return/result convention such as `OUTPUT`, result set, return code,
    status/message output, side-effect only, or error based
  - transaction boundary and transaction granularity
  - isolation level and isolation-related hints
  - error, status, row-count, and validation behavior
  - procedure dependencies, callers, and expected consumers
- read/write path map
- external dependency and operational risk map
- mismatch and unresolved verification list
- conclusion for design reuse:
  - applicability boundary
  - rule selection keys
  - naming rules
  - stored procedure contract rules
  - table-definition rules
  - SQL and DDL construction rules
  - transaction and consistency rules
  - exception and split rules
  - confidence per reusable rule
  - unresolved verification
  - design handoff decisions
- reusable metadata for `db_design`

## Design Handoff

`db_design` uses this analysis as its current-state basis. If the analysis does
not cover a DB object, naming surface, read/write path, migration authority, or
external dependency required by the design, `db_design` must mark that area
`unknown` or route back to `db_current_state_analysis`.

## Conclusion For Design Reuse

The conclusion must be the reusable decision surface for later design. It is not
a prose summary and it is not a list of representative queries.

Use these fixed axes:

- applicability boundary:
  - database, schema, module, procedure class, table family, artifact age, and
    source basis where the conclusion applies
- rule selection keys:
  - how later design chooses the rule, such as schema, procedure class,
    operation family, read/write role, API/report/job boundary, table family, or
    migration/deployment artifact type
- naming rules:
  - table, column, constraint, index, migration, ORM, raw SQL alias, and stored
    procedure naming rules
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
  - transaction ownership, explicit transaction classes, isolation level,
    retry/idempotency/locking evidence, and unknown areas
- exception and split rules:
  - intentional rule splits by schema/module/procedure class/artifact age and
    known exceptions
- confidence:
  - `strong`, `mixed`, `weak`, or `unknown` per reusable rule
- unresolved verification:
  - live DB checks, caller evidence, external controls, source/DB drift, and
    unresolved mismatches
- design handoff:
  - rules `db_design` may apply, rules requiring human approval, and areas that
    must remain `unknown` or route to another Skill

If a conclusion cannot state reusable rules on the required axes, the missing
axis must remain `unknown` and be handed off explicitly.

## DB-Unit SQL Export Basis

For each database in scope, start from the SQL file or file set exported for
that database. Treat that export as the primary current-state source for DB
objects and DB-local rules.

Record for each export:

- database identity and expected DBMS
- SQL file path or source locator
- generation source, such as live DB scripting, migration-generated SQL,
  checked-in DDL, vendor export, or tool output
- generation date, commit, version, or unknown status
- included object classes:
  - schema
  - table
  - view
  - index
  - constraint
  - sequence
  - trigger
  - procedure
  - function
  - synonym
  - seed data
  - permissions
- exclusions or unsupported object classes
- whether object order, dependency order, transaction wrappers, batch
  separators, comments, and tool headers are meaningful or generated noise

Use migrations, ORM mappings, DbContexts, repositories, raw SQL, jobs, reports,
tests, and integration handlers to explain use and detect drift from the SQL
export. Do not let ORM or code override the DB-unit SQL export silently; record
the conflict as a mismatch.

## DB Naming Rule Analysis

The current-state analysis should extract naming rules at the same granularity
that later DB design must use. The goal is not style enforcement. The goal is to
make local brownfield naming evidence usable for candidate names.

Analyze at least these naming surfaces when present:

- database, schema, table, view, collection, stream, and sequence names
- column names, audit columns, FK columns, status columns, code columns, and
  timestamp columns
- primary key, foreign key, unique, check, default, index, trigger, procedure,
  function, and migration names
- ORM entity, value object, owned type, DbSet, entity configuration,
  repository, query object, projection, and raw SQL alias names
- outbox, inbox, event, job, report, seed, import/export, and correction-tool
  names
- connection string, configuration section, environment variable, and generated
  artifact names

Extract these rule dimensions:

- casing and separator: `PascalCase`, `camelCase`, `snake_case`,
  `SCREAMING_SNAKE`, bracketed SQL identifier, quoted identifier, or mixed
- singular/plural treatment by object kind
- prefix/suffix patterns such as `PK_`, `FK_`, `IX_`, `UQ_`, `CK_`,
  `Id`, `Code`, `Status`, `Type`, `At`, `On`, `Utc`, `History`, or
  `Audit`
- schema/module prefixing and bounded-context naming
- abbreviation and acronym treatment
- status/lifecycle vocabulary and whether names express state, event, command,
  or entity meaning
- migration naming pattern, timestamp convention, and whether migration names
  describe business intent or technical operation
- ORM-to-DB translation rule, including entity/table, property/column,
  enum/status, owned type/table, and DbSet/table relationships
- raw SQL alias convention and whether aliases match ORM/property names

Record rule confidence:

- `strong`: repeated local evidence with few or explained exceptions
- `mixed`: multiple conventions exist and the target area must choose from a
  narrower local scope
- `weak`: limited examples; candidate names require human confirmation
- `unknown`: evidence is missing or contradictory

Record exceptions with evidence instead of normalizing them away. Later design
must be able to tell whether a proposed name follows the dominant local rule,
follows a narrower subsystem rule, or is unsupported.

For stored procedures, extract procedure-class naming rules. Do not reduce SP
naming to one generic procedure casing rule.

Record:

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
- separator and casing rule, including `PascalCase`, underscores between
  category/action segments, bracketed identifiers, and schema qualification
- operation-family rule, such as `Insert{Object}FromJson`,
  `Update{Object}FromJson`, `Delete{Object}`, `SearchFor{Object}`,
  `Get{Object}Updates`, `GetRandom{Object}`, or
  `Configuration_{Action}{Feature}`
- exception rule and candidate-name construction rule

Procedure names must be derived from existing procedure names and their callers,
not from table names alone.

## Table-Definition Local Rules

For table design, extract local rules by comparing existing table definitions
inside the same DB-unit SQL export. Use neighboring tables from the same
database, schema, bounded context, module, or naming family before using
repository-wide examples.

For each recurring column role, record:

- column-name rule:
  - primary key name
  - foreign key name
  - natural key/code name
  - display/name/title field
  - description/memo/comment field
  - status/type/category field
  - amount/quantity/rate/percent field
  - date/time/timestamp field
  - audit columns such as created/updated/deleted/user/version fields
  - logical delete, tenant, organization, partition, and concurrency fields
- type rule:
  - preferred DB type by column role
  - unicode vs non-unicode string choice
  - fixed vs variable length string choice
  - integer size choice
  - decimal precision/scale by money, rate, quantity, or percentage role
  - date/time type and timezone convention
  - boolean/flag representation
  - enum/status representation
  - binary/json/xml/text representation
- size rule:
  - string length by role
  - numeric precision and scale by role
  - max-length exceptions and evidence
  - whether length values are powers of two, business limits, DB defaults, or
    copied from legacy patterns
- constraint/default rule:
  - nullability by role
  - default constraint usage and naming
  - identity/sequence usage
  - computed column usage
  - check constraint usage
  - collation or character-set override
  - rowversion/version/concurrency token usage

Record confidence per rule as `strong`, `mixed`, `weak`, or `unknown`.
When several existing tables disagree, group the evidence by narrower scope
such as schema, module, artifact age, or table family instead of forcing one
global rule.

Later `db_design` should use these table-definition local rules before
proposing new column names, DB types, lengths, precision, scale, nullability,
defaults, identities, computed columns, or concurrency columns.

## Database-Level Local Rules

For each database in scope, extract a local rule set. Do not merge different
databases into one rule unless the evidence shows they intentionally share the
same convention.

Each database-level rule set should include:

- naming rules:
  - database, schema, table, view, column, key, constraint, index, trigger,
    procedure, function, migration, seed, entity, DbSet, repository, raw SQL
    alias, and configuration names
  - singular/plural, prefix/suffix, casing/separator, abbreviation, module
    prefix, lifecycle/status vocabulary, and exception patterns
- stored procedure granularity:
  - whether procedures are organized by entity, use case, report/query,
    command, batch, integration, maintenance, or migration-support purpose
  - whether a procedure owns one operation, a workflow step, a whole workflow,
    or a reusable lower-level data access primitive
  - parameter naming, result shape naming, error/return-code style, temporary
    table/table-variable style, and procedure-to-table ownership evidence
- transaction configuration method:
  - where transaction boundaries are configured or started, such as application
    unit of work, ORM transaction, explicit SQL `BEGIN TRANSACTION`, stored
    procedure transaction, ambient transaction, job framework, or external
    migration tool
  - isolation level, timeout, retry, deadlock handling, idempotency marker,
    lock hint, savepoint, compensation, and rollback style when visible
  - whether isolation is explicit, inherited from caller/session/database
    defaults, native-procedure scoped, table-hint based, or unknown
  - whether transaction behavior is DB-global, module-local, procedure-local,
    command-local, or tool-specific
- SQL writing rules:
  - keyword casing, identifier quoting, schema qualification, alias style,
    join layout, CTE/temp-table usage, parameter style, variable naming,
    dynamic SQL policy, pagination pattern, upsert/merge pattern, null handling,
    date/time handling, status filtering, soft-delete filtering, and ordering
    rules
  - whether raw SQL, stored procedures, migrations, reports, and ORM-generated
    SQL follow the same rule or separate rules
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
  - whether scripts include `DROP` statements before `CREATE`, avoid `DROP`,
    or use `CREATE OR ALTER` / `CREATE OR REPLACE` / `ALTER`
  - whether scripts check object existence before `DROP`, `CREATE`, `ALTER`,
    `TRUNCATE`, `DELETE`, index operations, or constraint operations
  - preferred existence-check idioms, such as `IF EXISTS`, `IF OBJECT_ID(...)`,
    `INFORMATION_SCHEMA`, system catalog queries, `DROP ... IF EXISTS`, or
    vendor-specific equivalents
  - whether destructive statements require guards, comments, transactions,
    backup/reconciliation notes, or environment gates
  - whether scripts are idempotent, one-shot migration scripts, rollback
    scripts, repeatable deployment scripts, or generated snapshots
  - object operation ordering, batch separators, statement terminators, `SET`
    options, schema qualification, and dependency-handling patterns
  - whether table, view, procedure, function, trigger, index, constraint, seed,
    and permission scripts use different construction rules

Record rule confidence for each area as `strong`, `mixed`, `weak`, or
`unknown`. If a database uses multiple rule sets by schema, module, or age of
artifact, record the split rather than forcing one rule.

## Stored Procedure Analysis

Analyze stored procedures as current-state behavior, not just as named DB
objects. Start from the DB-unit SQL export and cross-check with callers,
reports, jobs, tests, and raw SQL invocation code.

The goal is reusable rule extraction for later design, not individual query
review, query tuning, or line-by-line stored procedure critique. Individual
procedures are evidence for procedure-class rules.

For each stored procedure in scope, record:

- stored procedure naming:
  - schema-to-purpose rule
  - verb/action vocabulary
  - object term and singular/plural rule
  - suffix/prefix rule
  - casing and separator rule
  - operation-family pattern
  - exceptions and candidate-name construction rule
- procedure purpose and granularity:
  - entity, use case, command, query/report, batch, integration, maintenance,
    migration-support, or reusable primitive
  - whether the procedure owns one operation, one workflow step, a whole
    workflow, one report projection, or a lower-level data access helper
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
  - caller/application controlled transaction
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
- temp table, table variable, cursor, dynamic SQL, and CTE usage when it affects
  design
- error, status, message, and validation style, including whether the local
  rule is `TRY/CATCH`, `@@ERROR`, `THROW`, `RAISERROR`, return-code based,
  output-status/message based, no explicit error handling, or mixed
- table, view, function, and external object dependencies
- caller evidence and expected consumers

Group conventions by procedure class when evidence differs. Command
procedures, query/report procedures, batch procedures, integration procedures,
and utility procedures may intentionally use different return/result and
transaction rules.

Record confidence as `strong`, `mixed`, `weak`, or `unknown`. If `OUTPUT`
parameters and result sets are both used, identify the local selection rule
instead of forcing one global convention.

## Knowledge Relations

- depends_on: [Database design viewpoints](100_database_design_viewpoints.md#xid-E7D4A11B8C06)
- depends_on: [Current source structure findings catalog](../source_analysis/170_current_source_structure_findings_catalog.md#xid-A9E742B1C6D0)
- related_to: [CSharp naming-convention extraction](../source_analysis/140_csharp_naming_convention_extraction.md#xid-B4F7E1A2C903)

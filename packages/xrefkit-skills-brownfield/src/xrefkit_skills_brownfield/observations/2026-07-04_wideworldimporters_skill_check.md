# db_current_state_analysis Skill Check: WideWorldImporters

## Summary

This check applies `db_current_state_analysis` to the public Microsoft
WideWorldImporters SQL Server sample definitions to verify whether the Skill can
extract reusable database-local rules for stored procedure return/result
conventions, transaction granularity, and stored procedure naming from real DB
source.

The purpose is rule extraction for later design reuse. It is not individual
query review, query tuning, or line-by-line stored procedure critique.

Result:

- The Skill axes are usable for real SQL definitions.
- The sample proves that return style must be classified by procedure class, not
  as one database-wide rule.
- Stored procedure naming is also procedure-class based. It uses schema,
  verb/action, object term, and suffix/prefix patterns.
- The sample also proves that `OUTPUT` must be split into:
  - parameter `OUTPUT`
  - DML `OUTPUT inserted/deleted...` result set
- Transaction granularity must be extracted per procedure class. The database
  contains no-transaction SPs, whole-procedure transactions, and per-item
  transactions.

## Source Basis

- source repository: `microsoft/sql-server-samples`
- source URL: `https://github.com/microsoft/sql-server-samples`
- checked commit: `481085dc95720244a359f1311afd6003e0bcc09c`
- local source path:
  `sources/web/github.com/microsoft/sql-server-samples/repo/samples/databases/wide-world-importers/wwi-ssdt/wwi-ssdt`
- database unit: `WideWorldImporters` OLTP SSDT project
- live DB verification: `not_verified`

## Procedure Inventory

From SQL files under `Stored Procedures` in the WideWorldImporters OLTP SSDT
project:

- stored procedures: `135`
- procedures containing parameter or DML `OUTPUT`: `41`
- procedures containing `SELECT`: `74`
- procedures containing `RETURN`: `36`
- procedures containing `BEGIN TRAN`: `21`
- procedures containing TRY/CATCH: `15`
- procedures containing `@@ERROR`: `0`
- procedures containing `THROW`: `25`
- procedures containing isolation-level options or isolation hints: `4`
- procedures containing JSON handling: `44`

## Extracted Stored Procedure Naming Rules

The reusable naming rule is procedure-class based. Do not derive SP names from
table names alone.

| Procedure class | Count | Naming rule |
| --- | ---: | --- |
| `WebApi` JSON insert | 15 | `[WebApi].[Insert{Object}FromJson]` |
| `WebApi` JSON update | 21 | `[WebApi].[Update{Object}FromJson]` |
| `WebApi` delete | 15 | `[WebApi].[Delete{Object}]` |
| `WebApi` query | 2 | `[WebApi].[SearchFor{Object}]` or `[WebApi].[Login]` |
| `Integration` update query | 13 | `Integration.Get{Object}Updates` |
| `DataLoadSimulation` lookup | 14 | `[DataLoadSimulation].[GetRandom{Object}]` |
| `DataLoadSimulation` generator/setup command | 4 | `DataLoadSimulation.Populate{Object}` |
| `DataLoadSimulation` add command | 3 | `DataLoadSimulation.Add{Object}` |
| `DataLoadSimulation` record command | 3 | `DataLoadSimulation.Record{Object}` |
| `Website` query | 5 | `Website.SearchFor{Object}` |
| `Website` command | mixed | `Website.Insert{Object}`, `Website.Record{Object}`, `Website.Invoice{Object}`, or task-specific command names |
| `Application` configuration | 14 | `[Application].Configuration_{Action}{Feature}` with actions such as `Apply`, `Remove`, `Enable`, `Disable`, and `Prepare` |
| `Sequences` maintenance | 2 | `Sequences.Reseed{Object}` |

Extracted rules:

- Procedure names are schema qualified.
- Most procedure names use `PascalCase`.
- `Application.Configuration_*` uses an underscore between the configuration
  category and the action/feature phrase.
- API JSON import/update procedures encode input format with the `FromJson`
  suffix.
- Integration extractors encode delta semantics with the `Updates` suffix.
- Query/search procedures use `SearchFor{Object}` or `Get{Object}Updates`,
  not a generic `Select{Object}` pattern.
- Simulation helper lookups use `GetRandom{Object}`.
- Maintenance procedures use action verbs such as `Reseed`, `Apply`, `Remove`,
  `Enable`, and `Disable`.
- New SP names should be constructed from the matching procedure class:
  schema + verb/action + object term + class-specific suffix.
- If no matching procedure class exists, the result should be `unknown` or a
  new naming rule must be explicitly introduced.

## Extracted Return/Result Rules

The reusable rule is not one global convention. Return/result style is selected
by procedure class.

| Procedure class | Count | Return/result convention |
| --- | ---: | --- |
| `WebApi` JSON insert | 15 | DML `OUTPUT inserted.<id>` result set plus source `SELECT` from `OPENJSON`; no explicit transaction in the SP. |
| `WebApi` JSON update | 21 | side-effect only; no explicit result visible. |
| `WebApi` delete | 15 | side-effect only; no explicit result visible. |
| `WebApi` query | 2 | `SELECT` result set. |
| `Integration` update query | 13 | `SELECT` result set plus `RETURN 0`. |
| `DataLoadSimulation` lookup | 17 | mostly parameter `OUTPUT` plus `SELECT`; one also uses `RETURN`. |
| `DataLoadSimulation` command | 25 | mixed: side-effect only, parameter `OUTPUT`, DML `OUTPUT`, `SELECT`, and explicit transaction patterns. |
| `Website` command | 6 | `RETURN` code or `SELECT` plus `RETURN`, with explicit transactions for some command procedures. |
| `Website` query | 5 | `SELECT` result set. |

Extracted rules:

- Do not decide "OUTPUT based or dataset based" globally for this DB.
- For WebApi insert SPs, new insert APIs should prefer DML `OUTPUT
  inserted.<id>` returning a result set when matching the local class.
- For Integration `Get*Updates` SPs, new update extractors should prefer a
  dataset/result set plus `RETURN 0`.
- For simulation lookup helpers, parameter `OUTPUT` is a local convention.
- For side-effect WebApi update/delete SPs, adding a result payload would be a
  design deviation unless justified.

## Extracted Transaction Granularity Rules

Transaction behavior also differs by procedure class.

| Procedure class | Count | Transaction convention |
| --- | ---: | --- |
| `WebApi` JSON insert | 15 | no explicit transaction inside SP; caller/application or statement-level behavior controls it. |
| `WebApi` JSON update | 21 | no explicit transaction inside SP. |
| `WebApi` delete | 15 | no explicit transaction inside SP. |
| `Integration` update query | 13 | no explicit transaction inside SP; read/extract behavior with temp-table staging. |
| `DataLoadSimulation` command | 13 | explicit transaction present; mostly per-order/per-operation blocks without TRY/CATCH, plus one TRY/CATCH case. |
| `Website` command | 3 | explicit transaction with TRY/CATCH, rollback on catch, `THROW`, and `RETURN` code. |
| `configuration/utility` | 5 | explicit transaction appears in selected configuration operations, often with TRY/CATCH. |

Extracted rules:

- Transaction granularity cannot be chosen from DB-wide preference.
- Website command-style procedures use whole operation transactions with
  TRY/CATCH and rollback.
- DataLoadSimulation batch generators can use per-item/per-order transactions
  inside loops.
- WebApi JSON insert/update/delete procedures generally do not open explicit
  transactions inside the SP.

## Extracted Isolation And Error-Handling Rules

| Rule area | Count | Extracted rule |
| --- | ---: | --- |
| `TRY/CATCH` | 15 | Used by selected website command, configuration/utility, and some simulation command procedures. |
| `@@ERROR` | 0 | No `@@ERROR`-based local rule was found in stored procedure source. |
| `THROW` | 25 | Used for exception propagation in procedures that use modern error handling. |
| isolation level / hint | 4 | Isolation is exceptional and class-specific, visible mainly in memory-optimized or temperature-recording procedure paths. |

Extracted rules:

- Error-handling style is not `@@ERROR` based in this source set.
- When explicit structured error handling is present, the local pattern is
  `TRY/CATCH`, often combined with rollback and `THROW`.
- Absence of `TRY/CATCH` is also a local rule for many WebApi CRUD and
  Integration extractor procedures; do not add structured error handling unless
  the procedure class calls for it.
- Isolation level is usually not explicit in stored procedures.
- Explicit `SNAPSHOT` isolation or `WITH (SNAPSHOT)` hints are specialized
  rules for memory-optimized/native or temperature-recording paths, not a
  database-wide default.

## Evidence Samples

### WebApi JSON Insert

File:
`samples/databases/wide-world-importers/wwi-ssdt/wwi-ssdt/WebApi/Stored Procedures/InsertCustomersFromJson.sql`

Evidence:

- line 1: `CREATE PROCEDURE [WebApi].[InsertCustomersFromJson]`
- line 5: DML `OUTPUT inserted.CustomerID`
- line 7: source rows from `OPENJSON`

Rule evidence:

- purpose: API JSON insert
- return/result: DML `OUTPUT` clause result set
- transaction granularity: no explicit transaction in SP

### Integration Update Extractor

File:
`samples/databases/wide-world-importers/wwi-ssdt/wwi-ssdt/Integration/Stored Procedures/GetCustomerUpdates.sql`

Evidence:

- line 2: `CREATE PROCEDURE Integration.GetCustomerUpdates`
- line 9: `SET XACT_ABORT ON`
- line 14: creates `#CustomerChanges`
- line 187: returns a result set with `SELECT`
- line 193: drops the temp table
- line 195: `RETURN 0`

Rule evidence:

- purpose: ETL/update extraction query
- return/result: dataset/result set plus return code
- transaction granularity: no explicit transaction in SP

### DataLoadSimulation Command

File:
`samples/databases/wide-world-importers/wwi-ssdt/wwi-ssdt/DataLoadSimulation/Stored Procedures/CreateCustomerOrders.sql`

Evidence:

- line 2: `CREATE PROCEDURE DataLoadSimulation.CreateCustomerOrders`
- line 48: loops per generated order
- line 51: opens `BEGIN TRAN`
- lines 61-70: calls helper SPs using parameter `OUTPUT`
- line 110: commits inside the loop

Rule evidence:

- purpose: simulation batch command
- return/result: side-effect command using helper parameter `OUTPUT`
- transaction granularity: per-order transaction block inside loop

### Website Command

File:
`samples/databases/wide-world-importers/wwi-ssdt/wwi-ssdt/Website/Stored Procedures/InsertCustomerOrders.sql`

Evidence:

- line 2: `CREATE PROCEDURE Website.InsertCustomerOrders`
- line 25: `BEGIN TRY`
- line 27: `BEGIN TRAN`
- line 54: `COMMIT`
- line 58: rollback on `XACT_STATE()`
- line 60: `THROW`
- lines 61 and 64: `RETURN -1` / `RETURN 0`

Rule evidence:

- purpose: website command
- return/result: return code with exception propagation
- transaction granularity: whole operation transaction with TRY/CATCH rollback

## Skill Assessment

The current `db_current_state_analysis` Skill can support this analysis after
the DML `OUTPUT` distinction is made explicit.

Pass:

- DB-unit SQL export basis is identifiable through the SSDT project.
- SP purpose/granularity can be grouped by schema and naming pattern.
- SP naming rules can be extracted by procedure class.
- return/result conventions can be extracted.
- transaction granularity can be extracted.
- local rule splits are visible and should be preserved.
- output can be shaped as local rules for `db_design`, with individual
  procedures retained only as evidence.

Requires care:

- Keyword counts alone overcount `OUTPUT` unless parameter `OUTPUT` and DML
  `OUTPUT` clause are separated.
- `SELECT` inside an insert/update source query is not always the returned
  dataset. The classifier must distinguish top-level final result `SELECT`
  from internal source `SELECT`.
- Live DB state, permissions, generated deployment order, and runtime caller
  transaction behavior remain `not_verified`.

## Conclusion

The conclusion must be consumed as procedure-class rules, not as individual
query reviews and not as one database-wide rule.

### Applicability Boundary

- Applies to the WideWorldImporters OLTP SSDT source under
  `wwi-ssdt/wwi-ssdt`.
- Applies to source-visible stored procedures only.
- Live DB state, runtime permissions, generated deployment order, and caller
  transaction behavior are `not_verified`.

### Rule Selection Keys

Choose rules by:

- schema: `WebApi`, `Website`, `Integration`, `DataLoadSimulation`,
  `Application`, `Sequences`
- procedure class: JSON insert/update/delete, query/search, integration update
  extractor, simulation lookup, simulation command, website command,
  configuration/utility, sequence maintenance
- operation family: insert, update, delete, search, get updates, get random,
  record, populate, apply/remove/enable/disable, reseed

Do not choose return style, transaction style, or SP name from database-wide
preference.

### Naming Rules

- WebApi JSON insert: `[WebApi].[Insert{Object}FromJson]`
- WebApi JSON update: `[WebApi].[Update{Object}FromJson]`
- WebApi delete: `[WebApi].[Delete{Object}]`
- WebApi query: `[WebApi].[SearchFor{Object}]` or named command such as
  `[WebApi].[Login]`
- Integration extractor: `Integration.Get{Object}Updates`
- DataLoadSimulation lookup: `[DataLoadSimulation].[GetRandom{Object}]`
- DataLoadSimulation generator/setup: `DataLoadSimulation.Populate{Object}`,
  `DataLoadSimulation.Add{Object}`, or `DataLoadSimulation.Record{Object}`
- Website query: `Website.SearchFor{Object}`
- Website command: task-specific command verb, such as `Insert`, `Record`, or
  `Invoice`
- Application configuration: `[Application].Configuration_{Action}{Feature}`
- Sequence maintenance: `Sequences.Reseed{Object}`

### Stored Procedure Contract Rules

- WebApi JSON insert returns inserted IDs via DML `OUTPUT inserted.<id>` result
  set.
- WebApi JSON update/delete are side-effect only unless evidence says
  otherwise.
- WebApi query returns a `SELECT` result set.
- Integration `Get*Updates` procedures return a dataset/result set plus
  `RETURN 0`.
- DataLoadSimulation lookup helpers use parameter `OUTPUT`.
- Website command procedures use return codes and may propagate errors with
  `THROW`.
- Error-handling style is class-specific:
  - Website command and selected configuration/utility procedures use
    `TRY/CATCH`.
  - `@@ERROR` is not an observed local convention.
  - WebApi CRUD and Integration extractor procedures commonly have no explicit
    structured error handling in the SP body.

### Transaction And Consistency Rules

- WebApi JSON insert/update/delete procedures generally do not open explicit
  transactions inside the SP.
- Integration `Get*Updates` procedures do not open explicit transactions and
  use read/extract staging.
- DataLoadSimulation command procedures can use per-item/per-order transaction
  blocks inside loops.
- Website command procedures use whole-operation transaction with TRY/CATCH,
  rollback, `THROW`, and return code.
- Configuration/utility procedures may use explicit transactions when changing
  database-level features.
- Isolation level:
  - default/caller/session/database isolation is implicit for most procedures.
  - explicit `SNAPSHOT` isolation appears only in specialized native/
    memory-optimized or temperature-recording paths.
  - no broad rule supports adding explicit isolation to ordinary WebApi CRUD or
    Integration extractor procedures.

### Exception And Split Rules

- `OUTPUT` must be split into parameter `OUTPUT` and DML `OUTPUT
  inserted/deleted...` result set.
- `SELECT` must be split into returned result set and internal source query.
- `DataLoadSimulation` command procedures are mixed; design must choose the
  narrower command family instead of using the schema as a single rule.
- Website command names are more task-specific than WebApi CRUD names.

### Confidence

- WebApi JSON insert/update/delete naming and return rules: `strong`.
- Integration `Get*Updates` naming and result rules: `strong`.
- DataLoadSimulation lookup naming and parameter `OUTPUT` rule: `strong`.
- DataLoadSimulation command transaction rule: `mixed`.
- Website command transaction rule: `strong` for the observed command class,
  but command naming is `mixed`.
- `TRY/CATCH` over `@@ERROR` as the explicit error-handling pattern: `strong`.
- Isolation-level rule: `mixed`, because explicit isolation is visible only in
  specialized procedure classes.
- Application configuration naming: `strong` for `Configuration_` family.

### Unresolved Verification

- live DB object state: `not_verified`
- caller-side transaction boundaries: `not_verified`
- caller/session/database default isolation: `not_verified`
- permission/runtime execution context beyond source `WITH EXECUTE AS OWNER`:
  `not_verified`
- deployment ordering and generated script behavior: `not_verified`

### Design Handoff

`db_design` may apply the strong rules above when the new design falls into the
same procedure class.

`db_design` must keep the result `unknown` or require human approval when:

- the proposed SP does not match an existing procedure class
- a WebApi update/delete should return data
- a simulation command needs transaction behavior outside its observed family
- explicit isolation is required outside the specialized procedure classes
- an implementation proposes `@@ERROR` instead of the observed `TRY/CATCH` /
  `THROW` style for explicit error handling
- a Website command name cannot be mapped to an existing command verb family
- runtime caller transaction behavior is required but not verified

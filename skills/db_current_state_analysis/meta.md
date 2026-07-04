<!-- xid: 6B8C70DA119E -->
<a id="xid-6B8C70DA119E"></a>

# Skill Meta: db_current_state_analysis

- skill_id: `db_current_state_analysis`
- summary: analyze current brownfield database and persistence structure from repository evidence before DB design
- use_when: a brownfield task needs current DB/schema/persistence understanding before database design, migration design, data correction planning, or DB-impact implementation; use before `db_design` when current database structure, naming, ownership, read/write paths, migration authority, or external DB dependencies are missing or stale
- input: target repository, source scope, DB-unit SQL export files for each database, current source-structure finding XIDs, migration/ORM/raw SQL/seed/report/job/API evidence as secondary cross-check evidence, optional live database inspection evidence, and optional prior DB knowledge
- output: current database state analysis report with DB-unit SQL export basis, persistence inventory, logical model, physical model, DB naming rule analysis, naming clusters, table-definition local rules for column names, types, lengths, precision, scale, nullability, defaults, identity, computed, collation, and concurrency fields, database-level local rules for naming, stored procedure granularity, transaction configuration method, isolation level, SQL writing style, SQL error-handling style, and DDL/query construction rules, stored procedure analysis for naming rules, return/result convention, transaction boundary and granularity, isolation level, error behavior, dependencies, and callers, read/write path map, data-flow boundaries, external dependency map, operational risks, mismatch signals, unresolved verification, reusable metadata, and handoff to `db_design`
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: database current-state analysis
- tuning: DB-unit SQL-export-first brownfield DB and persistence analysis before DB design
- responsibility: create a reusable current-state basis for database design without guessing from incomplete schema or ORM evidence
- os_contract: v1
- constraints: do not design new schema; do not implement migrations or code changes; do not assume live DB access; use DB-unit SQL export files as the primary basis for DB object shape and DB-local rules; use repository code artifacts as secondary cross-check evidence; distinguish source-proven current state from live-value verification; use current source-structure finding XIDs as context; extract DB naming rule analysis and naming clusters from actual source artifacts; extract table-definition local rules by comparing other tables in the same DB-unit SQL export before using wider examples; extract per-database local rules for naming, stored procedure granularity, transaction configuration method, isolation level, SQL writing style, SQL error-handling style, and DDL/query construction rules such as `DROP` usage and object-existence checks; extract stored procedure naming rules, return/result convention, transaction granularity, isolation level, and error-handling style from existing stored procedures and callers; record rule confidence and exceptions instead of normalizing them away; record SQL-export/ORM/code mismatches and unresolved verification explicitly; hand off design decisions to `db_design`
- lifecycle:
  - startup: confirm target scope, DB-unit SQL export files for each database, current source-structure finding XIDs, secondary persistence artifacts, optional live DB evidence, output path, and whether the result is for one-off use or later canonical knowledge
  - planning: define DB-unit SQL export basis, inventory, logical-model, physical-model, DB naming-rule, naming-cluster, table-definition local-rule, database-level local-rule, stored-procedure-analysis, read/write-path, external-dependency, operational-risk, mismatch, and unknown buckets
  - execution: analyze current persistence structure, DB naming rules, table-definition local rules, stored procedure naming rules, stored procedure granularity, stored procedure return/result convention, transaction boundary and granularity, isolation level, transaction configuration, SQL writing rules, SQL error-handling style, and DDL/query construction rules from DB-unit SQL export files first; use migrations, ORM mappings, DbContexts, repositories, raw SQL, stored procedures, seed data, reports, jobs, APIs, and integration handlers as secondary cross-check evidence; optionally incorporate live DB evidence as verification; produce reusable current-state report
  - monitoring_and_control: downgrade unsupported ownership, naming rules, table-definition rules, stored procedure naming rules, stored procedure granularity, stored procedure return/result convention, transaction granularity, isolation level, error-handling style, transaction setup, SQL writing rules, DDL/query construction rules, read/write, migration, live-value, and mismatch claims to `unknown`; stop if scope is narrowed silently or if a design decision is being made instead of current-state analysis
  - closure: return the current-state report, evidence list, source-analysis basis XIDs, live verification status, unresolved items, and handoff to `db_design`
- tags: `database`, `schema`, `persistence`, `analysis`, `brownfield`, `design-input`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=database_current_state_analysis_viewpoints; bind=F9B3C6A70412
  - name=database_design_viewpoints; bind=E7D4A11B8C06
  - name=current_source_structure_findings_catalog; bind=A9E742B1C6D0
  - name=csharp_naming_convention_extraction; bind=B4F7E1A2C903
- knowledge_inputs:
  - name=current_source_structure_finding; accepts=current-source-structure-findings,source-structure-overview; purpose=required-application-structure-context
  - name=prior_db_knowledge; accepts=database-current-state-analysis,database-design-package,source-structure-overview; purpose=optional-prior-db-context

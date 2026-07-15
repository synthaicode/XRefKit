<!-- xid: 9D2E6A4C7B81 -->
<a id="xid-9D2E6A4C7B81"></a>

# Skill Meta: batch-impact-regression

- skill_id: `batch-impact-regression`
- summary: analyze C# and SQL Server stored-procedure batch changes with deterministic combination regression and human-gated classification
- use_when: a requirement changes an existing C# batch and SQL Server SP execution path, especially when combinations are numerous and no formal test dataset exists
- input: configuration, source locations, isolated test DB details, old/new selectors, combination values and constraints, expected differences, result files, and evidence paths
- output: decision tables, orthogonal-table candidates, deterministic comparison reports, reduced regression sets, impact trace, unknowns, and human handoffs
- maturity: `trial`
- execution_mode: `local_default`
- capability: combination-based batch impact analysis and regression comparison
- constraints: never treat the baseline as business truth; never infer constraints; never execute against production; never let the model process the full candidate space; dynamic SQL or unresolved dynamic SP names remain uncertain
- lifecycle:
  - startup: load the operating contract, configuration schema, and adapter boundary; confirm safe DB target
  - planning: define the 15-step worklist, source/result boundaries, deterministic operations, human decisions, and stop conditions
  - execution: run deterministic scripts over fixture or adapter-produced artifacts
  - monitoring_and_control: stop on unsafe DB scope, missing rule evidence, unresolved dynamic dispatch, or unexplained side effects
  - closure: require JSON/CSV report, reduced-set recipe, full-run procedure, evidence paths, and human decisions
- tags: `batch`, `csharp`, `sql-server`, `regression`, `impact-analysis`
- skill_doc: `./SKILL.md`

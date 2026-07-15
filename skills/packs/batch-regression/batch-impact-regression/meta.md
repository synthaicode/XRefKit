<!-- xid: 9D2E6A4C7B81 -->
<a id="xid-9D2E6A4C7B81"></a>

# Skill Meta: batch-impact-regression

- skill_id: `batch-impact-regression`
- summary: analyze C# and SQL Server stored-procedure batch changes with deterministic combination regression and human-gated classification
- use_when: a requirement changes an existing C# batch and SQL Server SP execution path, especially when combinations are numerous and no formal test dataset exists
- input: configuration, C# solution/project and batch command, isolated test DB details, old/new selectors, combination values and constraints, expected differences, result contract, and evidence paths
- output: deterministic candidate/comparison reports, reduced regression set, full-run procedure, impact trace, unresolved decisions, and handoff artifacts
- maturity: `trial`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: combination-based batch impact analysis and regression comparison
- tuning: C# plus SQL Server stored-procedure execution-path tracing with safe isolated execution
- responsibility: execute evidence-backed change-impact analysis and prepare human-reviewable regression evidence
- os_contract: v1
- constraints: never treat the baseline as business truth; never infer constraints; never execute against production; never let the model process the full candidate space; dynamic SQL or unresolved dynamic SP names remain uncertain; unexplained differences are not auto-accepted
- lifecycle:
  - startup: load the operating contract, context guard, configuration schema, and adapter boundary; confirm public Skill inputs and safe DB target
  - planning: define the 15-step worklist, source/result boundaries, deterministic operations, human decisions, and stop conditions
  - execution: run the deterministic script over fixture or adapter-produced artifacts, preserving evidence and version selectors
  - monitoring_and_control: stop on unsafe DB scope, missing rule evidence, unresolved dynamic dispatch, or unexplained side effects; record unknown/risk/judgment concerns
  - closure: require JSON/CSV report, reduced-set recipe, full-run procedure, evidence paths, and resolved/escalated human decisions
  - handoff: deliver the report to the business owner and release/test owner; identify remaining adapter or environment work explicitly
- tags: `batch`, `csharp`, `sql-server`, `regression`, `impact-analysis`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=skill_operating_contract; bind=B7A2C94F0E61
  - name=context_direction_guard; bind=7A2F4C8D1601
- observation_refs:
  - `../../../../observations/2026-05-10_session_skill_flow_authoring_seed.md`

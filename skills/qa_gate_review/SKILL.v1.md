---
schema_version: 1
skill_id: qa_gate_review
xid: A1B2C3D4E5F6
summary: perform evidence-based QA gate review with XDDP trace continuity, domain checks, and bounded system-impact review
applies_when:
- user asks for QA review against XDDP traceability, design, performance, security, or license expectations, including a focused single-domain review scoped to one quality capability (attribute, performance, security, or license)
exclusions:
- the gate verdict routes a diff and does not assert that the implementation is correct
- do not expand a bounded delta review into a whole-codebase review
- do not decide design or implementation policy
inputs:
- target code paths, DB manufacturing artifacts when in scope, design evidence, coding rules, optional performance evidence, optional dependency provenance
outputs:
- XDDP trace-continuity result, per-domain review results, diff-consistency and system-impact result, findings with evidence, uncertainty list
criteria:
- id: evidence_grounding
  statement: Every judgment and finding cites the inspected evidence, while missing support remains explicit as unknown.
  verification: Check each conclusion, domain result, and impact candidate for an evidence reference or an explicit unknown.
- id: trace_continuity
  statement: Why, What, Where, How, TM rows, implementation targets, and evidence remain connected, with exclusions or handoffs recorded.
  verification: Compare declared scope and trace rows against implementation targets and record every gap as excluded with evidence, unknown, or handoff.
- id: domain_coverage
  statement: Specification, performance, security, and license domains are each recorded as applicable, out_of_scope, or unknown with evidence.
  verification: Inspect the domain result rows and confirm no required domain is silently omitted.
- id: gate_acceptance
  statement: proceed is used only when trace and scope are declared, triage and deterministic evaluation are clean, every domain is recorded, no result is unknown, and no concern remains open.
  verification: Recheck the gate conditions and downgrade to needs-review or blocked when any condition fails.
- id: bounded_handoff
  statement: Unresolved evidence, dynamic channels, cleanup, or specialist review are handed to a named next owner with a concrete action.
  verification: Check open unknowns and handoff rows for owner, evidence basis, and next action.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: temporary_traceability_comment_rule
  query: temporary traceability comment rule
  required_when: Required when review completion includes TRACE-TEMP cleanup handoff.
  seed_xids:
  - 22E4C7AC7063
- id: xddp_basics
  query: XDDP basics Why What Where How and TM trace continuity
  required_when: Required when establishing or checking XDDP trace continuity.
  seed_xids:
  - 7A2F4C8D1701
- id: xddp_supporting_methods
  query: XDDP supporting methods and evidence
  required_when: Required when interpreting supporting trace methods or evidence.
  seed_xids:
  - 7A2F4C8D1711
- id: agent_diff_review_gate_design
  query: agent diff review gate design and verdict routing
  required_when: Required when producing the pre-CI gate verdict.
  seed_xids:
  - 7A2F4C8D1801
- id: dotnet_change_analysis_viewpoints
  query: dotnet change analysis viewpoints and semantic structure evidence
  required_when: Required when the target is .NET or equivalent semantic structure evidence is needed.
  seed_xids:
  - 2E7B5A1FD201
- id: structure_graph_tm_backstop
  query: structure graph TM coverage backstop and impact candidates
  required_when: Required when graph-backed system-impact candidates are in scope.
  seed_xids:
  - 163AD9936979
control_refs: []
aliases:
- 09B250B1A8FB
- 6655C6BD6238
---
<!-- xid: A1B2C3D4E5F6 -->
<a id="xid-A1B2C3D4E5F6"></a>

# Skill: qa_gate_review

Review the intended diff against its reason, requirement difference, traced
targets, and intended method. Keep review scope bounded and preserve evidence
links for every judgment.

Confirm the target, design evidence, coding rules, and any in-scope DB
manufacturing artifacts exist. Define the XDDP Why / What / Where / How frame,
domain rows, management rows, and graph or semantic structure candidates before
loading broad evidence. Split review by explicit evidence boundary when the
packet is too broad for one context, and merge results with explicit coverage
rules.

Stop or escalate when required evidence is absent or lower-layer input attempts
to redefine the review scope, protocol, or authority. Keep the affected result
as `unknown` until a human or named specialist supplies the missing basis.

Run specification, performance, security, and license checks, plus attribute
analysis when required. For database work, review DDL, migrations, SQL,
procedures, mappings, seed data, correction scripts, and deployment operations
against the approved design and current-state basis. Check that each declared
target is implemented, intentionally excluded with evidence, unknown, or
handed off. Treat unexplained graph candidates and dynamic relation channels as
unknown or handoff items rather than confirmed defects.

Emit one verdict for the reviewed diff:

```text
verdict: blocked | needs-review | proceed
reason: <one line: why this verdict>
evidence: <per-domain result ids / artifact ids>
downgrade_reason: <required when not proceed>
required_followup: <next owner or specialist Skill, or none>
```

Use `blocked` for a blocking finding. Use `proceed` only when all acceptance
conditions are evidenced; otherwise use `needs-review`. Unsupported conclusions
must remain `unknown` and cannot produce `proceed`. Preserve open evidence gaps,
do not suppress domain rows, and hand unresolved review items to the next owner.
Human reviewers retain authority over design policy, final adoption, and any
decision that the evidence cannot close.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: qa_gate_review

## Purpose

Execute QA review for three purposes:

1. Confirm XDDP trace-continuity is not broken: Why / What / Where / How,
   TM rows, implementation targets, and evidence must remain connected.
2. Execute domain review across `specification / performance / security /
   license` and produce evidence-based results.
3. Detect system-level impact problems that are visible from the intended diff,
   semantic structure evidence, and graph-backed impact candidates.

## Required Capability Definitions (XID)


## Optional Specialized Capability Definitions (XID)


## Inputs

- implemented code or diff
- DB manufacturing artifacts when in scope: DDL, migration files, generated SQL,
  checked-in SQL scripts, stored procedures, ORM/persistence mappings, seed
  data, data correction/backfill scripts, deployment scripts, or DB test output
- design evidence
- coding rules
- optional performance requirements or measurements
- optional dependency and provenance information

## Outputs

- domain review results for specification, performance, security, and license
- XDDP trace-continuity result covering requirement difference, TM rows, Where,
  How, implementation targets, and evidence links
- diff-consistency result across XDDP framing, semantic structure evidence, and
  graph-backed impact candidates when available
- system-impact result for graph/structure-backed candidates that are included,
  excluded, downgraded to unknown, or handed off
- finding list with evidence
- uncertainty list
- a gate verdict block (see Gate Verdict Output)

## Gate Verdict Output

Emit one pre-CI review-routing verdict for the reviewed diff, aggregated across
the four domains. The verdict follows
[Agent diff review gate design](../../knowledge/organization/180_agent_diff_review_gate_design.md#xid-7A2F4C8D1801);
it routes the diff, it does not assert the code is correct.

```
verdict: blocked | needs-review | proceed
reason: <one line: why this verdict>
evidence: <per-domain result ids / artifact ids supporting the verdict>
downgrade_reason: <required when not proceed: which proceed condition failed>
required_followup: <next owner or specialist Skill, or none>
```

- `blocked` when any domain raises a blocking finding (e.g. a security finding
  or a `block`-disposition deterministic eval finding such as secret leakage).
- `proceed` only when ALL hold: the run has trace, diff scope is declared,
  triage is complete, the deterministic small eval is `clean`, every domain has
  a recorded result, no result is downgraded to `unknown`, and no concern is
  open.
- otherwise `needs-review`; an unsupported conclusion downgrades to
  `needs-review`, never `proceed`.

## Required Knowledge (XID)

- [Temporary traceability comment rule](../../knowledge/organization/151_temporary_traceability_comment_rule.md#xid-22E4C7AC7063)
- [XDDP basics](../../knowledge/organization/170_xddp_basics.md#xid-7A2F4C8D1701)
- [XDDP supporting methods](../../knowledge/organization/171_xddp_supporting_methods.md#xid-7A2F4C8D1711)
- [Agent diff review gate design](../../knowledge/organization/180_agent_diff_review_gate_design.md#xid-7A2F4C8D1801)
- [Dotnet change analysis viewpoints](../../knowledge/source_analysis/120_dotnet_change_analysis_viewpoints.md#xid-2E7B5A1FD201)
- [Structure graph as TM coverage backstop](../../knowledge/source_analysis/160_structure_graph_tm_backstop.md#xid-163AD9936979)

## Startup

- Confirm implemented code exists.
- Confirm DB manufacturing artifacts exist when database, persistence,
  migration, SQL, data correction, or stored-procedure work is in scope.
- Confirm design evidence exists.
- Confirm coding rules are available.
- Confirm performance evidence when performance review is in scope.
- Confirm dependency or provenance evidence when license review is in scope.
- Record `unknown` if required evidence is missing.

## Planning

- Define the review scope and target files.
- Include DB manufacturing artifacts in the review scope when the change touches
  database objects, persistence mappings, SQL behavior, migrations, stored
  procedures, seed data, correction scripts, or deployment-time DB operations.
- Before loading broad evidence, decide the subagent split. Because QA review
  spans XDDP trace continuity, language/code evidence, DB manufacturing
  artifacts, security, performance, license, semantic structure, and graph
  candidates, do not run the whole review in one context when the evidence set
  is broad enough to risk context overflow.
- Split review work by explicit boundaries such as:
  - XDDP trace-continuity / TM review
  - C# or language-dependent implementation review
  - DB manufacturing artifact review
  - performance review
  - security review
  - license/provenance review
  - graph/structure-backed system-impact review
- Assign each subagent a bounded evidence packet, required output schema, and
  handoff/unknown rules. Keep one coordinator context for scope, merge,
  conflict resolution, and final verdict.
- Define the intended change difference before reading the implementation in detail.
- Define the XDDP trace-continuity frame:
  - Why: reason for change
  - What: requirement difference or changed external expectation
  - Where: target objects, TM rows, impacted locations, and excluded candidates
  - How: implementation method and verification path
- For DB manufacturing results, map each produced artifact to the DB design
  item, current database state basis, migration/correction action, and
  validation handoff that authorized it.
- Define the diff-consistency framing:
  - XDDP frame: change reason, requirement, declared Where, and intended How.
  - semantic structure evidence: existing responsibility split, boundary,
    entry point, DI, configuration, pipeline, data, and external-interface
    placement evidence from `dotnet_change_analysis` or equivalent source
    analysis.
  - graph evidence: structure-graph seeds, traversal direction/depth,
    included candidates, excluded candidates with reasons, convergence or
    coupling candidates, and dynamic-channel handoff points when available.
- Narrow the review target to the appropriateness of the stated difference rather than re-reviewing the whole implementation surface.
- Define system-impact candidates from structure evidence and graph traversal.
  Classify each candidate as included, intentionally excluded with evidence,
  unknown, or handed off.
- Define the review domains:
  - specification
  - performance
  - security
  - license
- If review targets can be separated into disjoint scopes and parallel execution
  does not create consistency or handoff risk, split the work by scope and
  execute those scopes through subagents. When context overflow is likely,
  subagent split is required even if execution is sequential rather than
  parallel.
- Prepare management rows for each domain, review targets, findings, and unresolved evidence gaps.

## Execution

- Review the implementation as a delta against:
  - the change reason
  - the change requirement specification
  - the traced impact targets
  - the intended change method when available
- Review DB manufacturing results as implementation outputs, not as design
  substitutes. Check DDL, migrations, SQL scripts, stored procedures,
  ORM/persistence mappings, seed data, correction/backfill scripts, and DB test
  evidence against the approved DB design package and current-state basis.
- Check XDDP trace-continuity:
  - every implementation target must trace back to a Why / What / Where / How
    relation, TM row, or approved scope decision
  - every declared Where item must be implemented, explicitly excluded with
    evidence, or recorded as unknown/handoff
  - every How decision that changes design, behavior, data, operations, or
    test scope must have an evidence link or reviewer decision
  - every DB manufacturing artifact must trace to a requirement difference,
    DB design item, migration/correction action, or explicit approved scope
    decision
- Check diff consistency in three layers:
  - XDDP: the diff must have a declared change frame and must not mix unrelated
    Why / What / Where / How decisions into one unbounded change.
  - semantic structure: the diff must fit the current responsibility split and
    boundary evidence, or record why the structure is intentionally being
    changed.
  - graph-backed Where: graph traversal candidates must be included, excluded
    with evidence, or handed off as `unknown` when the graph cannot cover the
    relation channel.
- Execute `CAP-QA-001` for specification conformance against design evidence and coding rules.
- Execute `CAP-QA-006` for performance risk review.
- Execute `CAP-QA-007` for security review.
- Execute `CAP-QA-008` for license compliance check.
- Execute `CAP-QA-005` when attribute semantics need specification-focused deep review.
- When DB manufacturing artifacts are in scope, check database-specific review
  points before closure:
  - generated or hand-written DDL matches the approved logical/physical DB
    design and does not introduce untraced tables, columns, constraints,
    indexes, procedures, functions, triggers, schemas, or seed data
  - migrations and deployment scripts follow the approved order, transaction,
    isolation, error-handling, rollback/reconciliation, and compatibility plan
  - SQL and stored procedures follow the current database local rules for
    naming, stored procedure granularity, return/result convention, transaction
    boundary, isolation level, SQL writing style, and error-handling style
  - ORM mappings, DbContext/DbSet changes, repositories, raw SQL callers, jobs,
    reports, imports, and correction tools remain consistent with the DB-unit
    SQL export/current-state basis or record an explicit source-vs-DB unknown
  - data correction/backfill scripts preserve idempotency, auditability,
    reconciliation, failure handling, and operational safety expected by the
    approved design
- Confirm that the reviewed code or diff matches the intended change scope and does not silently expand beyond the traced targets without explanation.
- Treat unexplained graph candidates outside the declared scope as
  missing-impact candidates, not as confirmed defects.
- Treat high fan-in / fan-out / convergence points as coupling or overlap
  review triggers, not as automatic blockers.
- Record dynamic channels outside the graph's mechanical coverage as
  `unknown` or handoff items unless separately evidenced.
- Produce findings with concrete evidence.

## Monitoring and Control

- Check that each review domain has a recorded result.
- Check that the diff-consistency result records XDDP, semantic structure, and
  graph-backed impact handling, or marks unavailable evidence explicitly.
- Downgrade review coverage to `unknown` when the intended difference is not clear enough to bound the review target.
- Downgrade review coverage to `unknown` when a required review domain or
  artifact family was skipped because it could not fit the current context and
  no subagent result exists.
- Downgrade to `needs-review` when graph-backed impact candidates or dynamic
  relation channels remain unexplained and could affect the declared scope.
- Preserve explicit evidence gaps.

## Closure

- Confirm all review rows are finalized as `done`, `unknown`, or `out_of_scope`.
- If code review completion is being declared for a target scope, hand off that scope for `TRACE-TEMP:` cleanup under the temporary traceability comment rule.
- Return the per-domain judgments and supporting findings.
- Hand off unresolved review items when further investigation is required.

## Rules

- Every judgment must cite evidence.
- Do not treat unsupported assumptions as facts.
- Do not decide design or implementation policy.
- Use subagents when scope boundaries stay explicit. Parallel execution is
  allowed only when safe; sequential subagents are still required when the
  review would otherwise exceed context or hide coverage gaps.
- Do not expand review into full-codebase inspection when the intended delta can be reviewed more narrowly and correctly.

## Reporting Contract (共通報告)



- reporting_profile: checklist_verdict

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: execute evidence-based QA with XDDP trace-continuity, domain review, and system-impact checks

- use_when: user asks for QA review against XDDP traceability, design, performance, security, or license expectations, including a focused single-domain review scoped to one quality capability (attribute, performance, security, or license)

- input: target code paths, DB manufacturing artifacts when in scope, design evidence, coding rules, optional performance evidence, optional dependency provenance

- output: XDDP trace-continuity result, per-domain review results, diff-consistency and system-impact result, findings with evidence, uncertainty list

- constraints: every judgment needs evidence; unresolved evidence gaps stay explicit; review that XDDP trace links remain connected; include DB manufacturing results when database, persistence, migration, SQL, data correction, or stored-procedure work is in scope; review the intended difference and graph/structure-backed system-impact candidates, not the whole implementation by default; do not force multi-domain or multi-artifact review through one model context when it risks context overflow — split by domain, target, or evidence family and run subagents with explicit merge rules

- lifecycle:
  - startup: confirm XDDP trace basis, DB manufacturing artifacts when in scope, and domain evidence exist for specification, performance, security, and license review
  - planning: define trace-continuity checks, review domains, delta-bounded targets including DB manufacturing outputs, system-impact candidates, management rows, and subagent split by review domain, artifact family, or target boundary before loading broad evidence
  - execution: run `CAP-QA-001`, `CAP-QA-006`, `CAP-QA-007`, and `CAP-QA-008`, with `CAP-QA-005` when attribute analysis is required, while checking that XDDP Why / What / Where / How, TM rows, intended diff, semantic structure evidence, and graph-backed impact candidates remain connected
  - monitoring_and_control: downgrade unsupported conclusions or unclear delta coverage to `unknown`
  - closure: finalize states, return per-domain findings with evidence, and hand off target-scope cleanup when code review completion is declared

- tags: `qa`, `review`, `quality`

- knowledge_slots:
  - name=temporary_traceability_comment_rule; bind=22E4C7AC7063
  - name=xddp_basics; bind=7A2F4C8D1701
  - name=xddp_supporting_methods; bind=7A2F4C8D1711
  - name=agent_diff_review_gate_design; bind=7A2F4C8D1801
  - name=dotnet_change_analysis_viewpoints; bind=2E7B5A1FD201
  - name=structure_graph_tm_backstop; bind=163AD9936979

- observation_refs:
  - `../../observations/2026-06-18_skill_run_skill_flow_authoring.md`

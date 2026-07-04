<!-- xid: 09B250B1A8FB -->
<a id="xid-09B250B1A8FB"></a>

# Skill: qa_gate_review

## Purpose

Execute the four QA review domains `specification / performance / security / license` and produce an evidence-based review result.

## Required Capability Definitions (XID)


## Optional Specialized Capability Definitions (XID)


## Inputs

- implemented code or diff
- design evidence
- coding rules
- optional performance requirements or measurements
- optional dependency and provenance information

## Outputs

- domain review results for specification, performance, security, and license
- diff-consistency result across XDDP framing, semantic structure evidence, and
  graph-backed impact candidates when available
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
- Confirm design evidence exists.
- Confirm coding rules are available.
- Confirm performance evidence when performance review is in scope.
- Confirm dependency or provenance evidence when license review is in scope.
- Record `unknown` if required evidence is missing.

## Planning

- Define the review scope and target files.
- Define the intended change difference before reading the implementation in detail.
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
- Define the review domains:
  - specification
  - performance
  - security
  - license
- If review targets can be separated into disjoint scopes and parallel execution does not create consistency or handoff risk, split the work by scope and execute those scopes through subagents.
- Prepare management rows for each domain, review targets, findings, and unresolved evidence gaps.

## Execution

- Review the implementation as a delta against:
  - the change reason
  - the change requirement specification
  - the traced impact targets
  - the intended change method when available
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
- Downgrade unsupported conclusions to `unknown`.
- Downgrade review coverage to `unknown` when the intended difference is not clear enough to bound the review target.
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
- Use subagents only when scope boundaries stay explicit and parallel execution is safe.
- Do not expand review into full-codebase inspection when the intended delta can be reviewed more narrowly and correctly.

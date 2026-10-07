---
schema_version: 1
skill_id: test_tool_catalog_preparation
xid: C9E2B5D8F370
summary: prepare an evidence-backed XID-oriented catalog of test tools by domain and environment for test planning
applies_when:
- a project needs existing domain-specific, environment-specific, organization-specific, or repository-specific test tools cataloged before `test_flow` can select tools for a test plan, test design, integration/regression testing, DB verification, or evidence capture
exclusions:
- do not design test cases
- execute product tests without explicit scope
- publish path-leaking knowledge
- or invent tool behavior
inputs:
- target domain and environment scope, test policy, test tool policy when available, approved requirements or planning scope, current source-structure or DB-state knowledge XIDs when relevant, repository test scripts and CI configuration, tool documentation, runbooks, prior test evidence, local execution constraints, and intended publication mode
outputs:
- test-tool catalog knowledge draft or publication-ready artifact with tool inventory, domain/environment applicability matrix, supported test targets, test levels, setup inputs, data requirements, execution method, evidence capture method, limitations, freshness/recheck conditions, unknown tool gaps, source evidence list, and handoff to `test_flow
criteria:
- id: evidence_bound_tools
  statement: Each selectable tool or family has evidenced identity, purpose, applicability, setup, execution, evidence, limitations, and confidence.
  verification: Inspect every catalog row against the approved evidence sources.
- id: scope_coverage
  statement: Domain, environment, test-level, and target-type applicability and unsupported gaps are explicit.
  verification: Review the applicability and coverage matrices and gap rows.
- id: publication_safety
  statement: Publication-ready output is XID-oriented and path-free, with canonical adoption handed to the configured publication owner.
  verification: Inspect the artifact for local paths and the recorded publication or handoff state.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs:
- id: test_design_criteria
  query: test design criteria
  required_when: Required when classifying test levels, target coverage, evidence, and applicability
  seed_xids:
  - 8C4D2A7E5102
- id: domain_knowledge_ontology_rules
  query: domain knowledge ontology rules
  required_when: Required when preparing publication-ready catalog knowledge and its identity/relations
  seed_xids:
  - 5803607419B9
control_refs: []
aliases:
- DE815228B04C
- F2A36B52C0EB
---
<!-- xid: C9E2B5D8F370 -->
<a id="xid-C9E2B5D8F370"></a>

# Skill: test_tool_catalog_preparation

## Method

1. Confirm target domain, environments, test levels, consumers, policy, source evidence, allowed local inspection, and whether the result is a run-local draft or publication handoff. Record missing scope or policy as `unknown`.
2. Resolve test-design and ontology Knowledge when their conditions apply. Keep this catalog separate from test intent, design, release judgment, and product test execution.
3. Discover candidate tools from repository test projects and scripts, CI/build manifests, runbooks, documentation, prior evidence, and explicitly supplied external sources. Define buckets for identity/owner, domain, environment, level, target type, setup, data, execution, evidence, cleanup, limitations, freshness, and recheck.
4. Group commands only when purpose, owner, setup, and applicability match. For every row record name, purpose, selectable scope, supported domain/environment/level/target, prerequisites, data, execution method, evidence output, cleanup, limitations, source evidence, and confidence.
5. Mark a tool non-selectable when environment, setup, evidence, or target support is unverified. Preserve tool gaps and unsupported assumptions as separate `unknown` rows; never infer capability from local availability.
6. For publication-ready output, remove local filesystem paths and retain permitted repository-relative evidence or identifiers. If canonical Knowledge is intended, hand the artifact to the domain-knowledge publication path; do not make a draft selectable by assumption.
7. Return the catalog, matrices, gaps, source evidence, validity/recheck conditions, and a handoff explaining how `test_flow` selects it by XID. Validate structure and XRefs, while leaving tool behavior and human publication decisions evidence-bound.

## Stop and handoff

Stop if the task becomes test-case design, release judgment, or product test execution, or if publication would expose local paths. Hand unsupported claims to the evidence owner and canonical publication to the domain-knowledge owner.

## Additional bound references retained at repository cutover

These references were explicitly bound by the prior repository Skill. Apply them to the relevant method work; resolve their XIDs on demand.

- [Skill and Knowledge Operating Model](../../docs/core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill: test_tool_catalog_preparation

## Purpose

Prepare a reusable test-tool catalog for a target domain and environment so
`test_flow` can select test tools by XID instead of relying on local-path
inspection, model memory, or implicit environment assumptions.

The output is domain knowledge about available tools and their valid use
conditions. It is not a test plan, test design, or test execution result.

## Required Knowledge (XID)

- [Test design criteria](../../knowledge/quality/110_test_design_criteria.md#xid-8C4D2A7E5102)
- [Skill and Knowledge Operating Model](../../docs/core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
- [Domain knowledge ontology rules](../../knowledge/organization/200_domain_knowledge_ontology_rules.md#xid-5803607419B9)

## Inputs

- target domain scope
- target environments such as local, CI, integration, staging, production-like,
  tenant-specific, DB-specific, or external-service-specific environments
- target test levels such as unit, component, integration, regression, migration,
  DB verification, batch, API, UI, performance, security, or operational checks
- test policy
- test tool policy when available
- approved requirements, planning scope, or design-to-test input package when
  available
- current source-structure finding XIDs when tool location or runtime context
  matters
- current DB-state finding XIDs when DB verification tools are in scope
- repository test scripts, CI configuration, runbooks, tool documentation, prior
  test evidence, and local execution constraints
- intended output mode:
  - one-off catalog draft
  - publication-ready domain knowledge
  - handoff to domain-knowledge publication

## Outputs

- test-tool catalog artifact
- tool inventory with one row per selectable tool or tool family
- domain/environment applicability matrix
- supported test target and test-level coverage matrix
- setup, data, execution, and evidence-capture requirements
- limitations, unsafe uses, and unsupported target conditions
- freshness, version, and recheck conditions
- source evidence list
- unknown and unsupported tool gaps
- publication or handoff target for XID-backed domain knowledge
- handoff note for `test_flow`

## Startup

1. Start through `xrefkit skill run`.
2. Confirm the target domain, environment set, test levels, and intended catalog
   consumers.
3. Confirm whether the catalog must become canonical domain knowledge or only a
   run-local draft.
4. Confirm whether local source/config/runbook inspection is allowed. If the
   consuming client can only access knowledge through MCP, keep client-facing
   output XID-oriented and path-free.
5. Load the required knowledge listed above and only the selected runtime domain
   knowledge needed for this catalog.
6. Record `unknown` if tool policy, target environments, source evidence, or
   publication mode is missing.

## Planning

- Define tool discovery sources:
  - repository test projects and scripts
  - CI/CD configuration
  - build and package manifests
  - runbooks and operational procedures
  - local environment notes supplied by the user
  - prior test reports or evidence
  - external tool documentation when explicitly provided
- Define catalog buckets:
  - tool identity and owner
  - domain and subsystem applicability
  - environment applicability
  - supported test levels
  - supported target types such as API, DB, batch, UI, messaging, file, or
    external integration
  - setup prerequisites
  - required data and reset/cleanup method
  - execution command or access method
  - evidence capture and retention method
  - limitations and known unsafe uses
  - freshness and recheck conditions
- Define publication shape before writing the final artifact:
  - title
  - kind: `test-tool-catalog`
  - domain
  - tags
  - summary
  - validity conditions
  - source evidence
  - knowledge relations when justified

## Execution

- Inspect the approved evidence sources and collect candidate tools.
- Group multiple commands or scripts into one tool family only when they share
  the same purpose, owner, setup model, and applicability boundary.
- For each tool or family, record:
  - name
  - purpose
  - selectable scope
  - target domain/subsystem
  - supported environments
  - supported test levels
  - supported target types
  - setup prerequisites
  - required input data
  - execution method
  - output/evidence produced
  - cleanup/reset behavior
  - limitations
  - source evidence
  - confidence
- Mark a tool as not selectable when its environment, setup, evidence, or
  supported target cannot be verified.
- Record tool gaps separately from cataloged tools.
- If the output is publication-ready, remove local filesystem paths from the
  client-facing body. Keep repository-relative evidence or source identifiers
  only when they are allowed by the publication target.
- If the result should become canonical domain knowledge, hand it to the
  domain-knowledge publication path instead of assuming local draft files are
  already selectable by XID.

## Output Contract

Use this compact shape for the catalog artifact:

```md
# <domain/environment> Test Tool Catalog

## Metadata

- kind: test-tool-catalog
- domain:
- environments:
- test_levels:
- source_scope:
- validity_conditions:
- recheck_conditions:

## Summary

## Tool Catalog

| tool_id | tool_name | domain | environments | test_levels | target_types | setup | data | execution | evidence | limitations | confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Applicability Matrix

## Tool Gaps

| gap_id | scope | missing_tool_or_evidence | impact_on_test_flow | next_action |
| --- | --- | --- | --- | --- |

## Source Evidence

## Knowledge Relations
```

## Monitoring and Control

- Stop if the task turns into test case design, release judgment, or product
  test execution.
- Stop if publication-ready output would expose local filesystem paths to an
  MCP-only consumer.
- Downgrade unsupported tool capabilities, environment support, setup
  requirements, evidence methods, or data assumptions to `unknown`.
- Preserve tool gaps even when a workaround exists; the workaround must be a
  separate selectable tool or an explicit test-flow assumption.
- Do not let a tool catalog redefine requirement intent, design intent, test
  policy, release policy, or XRefKit governance.

## Closure

Closure is allowed only when all of the following are recorded:

- target domain, environments, and test levels
- tool discovery sources inspected
- tool catalog rows or an explicit no-tool result
- applicability matrix
- tool gaps and unsupported assumptions
- source evidence list
- validity and recheck conditions
- publication or handoff target
- handoff note explaining how `test_flow` should select this catalog by XID

Run:

```powershell
python -m xrefkit xref fix
```

If the catalog is published as canonical or external XID-bearing domain
knowledge, also validate that the MCP/domain-knowledge catalog exposes the new
XID metadata and that selected bodies resolve through `get_document_by_xid`.

## Rules

- Do not invent test tool behavior.
- Do not treat local availability as proof of domain applicability.
- Do not embed a target project's tool catalog inside `test_flow`.
- Do not make XID-less draft knowledge selectable by downstream Skills.
- Do not publish partial catalogs without explicit unknowns, gaps, and
  recheck conditions.

## Reporting Contract (共通報告)



- reporting_profile: artifact_traceability

Use the shared [Skill Reporting Contract](../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: prepare a domain/environment test-tool catalog as reusable domain knowledge for test planning and test design

- use_when: a project needs existing domain-specific, environment-specific, organization-specific, or repository-specific test tools cataloged before `test_flow` can select tools for a test plan, test design, integration/regression testing, DB verification, or evidence capture

- input: target domain and environment scope, test policy, test tool policy when available, approved requirements or planning scope, current source-structure or DB-state knowledge XIDs when relevant, repository test scripts and CI configuration, tool documentation, runbooks, prior test evidence, local execution constraints, and intended publication mode

- output: test-tool catalog knowledge draft or publication-ready artifact with tool inventory, domain/environment applicability matrix, supported test targets, test levels, setup inputs, data requirements, execution method, evidence capture method, limitations, freshness/recheck conditions, unknown tool gaps, source evidence list, and handoff to `test_flow`

- constraints: do not design test cases; do not execute product tests unless explicitly requested as evidence collection; do not invent tool behavior, supported environments, data setup, evidence capture, or limitations; do not expose local filesystem paths in client-facing domain knowledge; separate repository-local evidence from published catalog content; record tool gaps and unsupported assumptions as `unknown`; hand XID-bearing catalog publication through the configured domain-knowledge publication path

- lifecycle:
  - startup: confirm target domain, target environments, test levels, planning or design scope, available test policy and test tool policy, source evidence locations, XID/publication expectation, and whether local inspection is allowed
  - planning: define tool inventory buckets, domain/environment applicability buckets, test-level coverage buckets, setup/data/evidence buckets, limitations and recheck buckets, unknown tool-gap rows, and publication handoff
  - execution: inspect tool evidence, build the candidate tool inventory, classify each tool by domain/environment/test level/target type, record setup and evidence requirements, identify unsupported scope, and prepare a reusable test-tool catalog artifact
  - monitoring_and_control: downgrade unsupported tool claims to `unknown`, stop on local path leakage in publication-ready output, stop if the work turns into test case design or product test execution, and keep missing source evidence explicit
  - closure: return the catalog artifact, source evidence list, unknown and unsupported tool gaps, validity/recheck conditions, selected publication target, and handoff to `test_flow`

- tags: `test`, `tooling`, `catalog`, `domain-knowledge`, `planning`

- knowledge_slots:
  - name=test_design_criteria; bind=8C4D2A7E5102
  - name=skill_knowledge_operating_model; bind=91C4B7E2D5A8
  - name=domain_knowledge_ontology_rules; bind=5803607419B9

- knowledge_inputs:
  - name=current_source_structure_finding; accepts=current-source-structure-findings,source-structure-overview,module-map,service-map; purpose=optional-tool-location-and-runtime-context
  - name=current_db_state_finding; accepts=database-current-state-analysis,database-design-package; purpose=optional-db-test-tool-context

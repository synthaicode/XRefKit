---
schema_version: 1
skill_id: test_tool_catalog_preparation
xid: C9E2B5D8F370
aliases: [DE815228B04C, F2A36B52C0EB]
summary: prepare an evidence-backed XID-oriented catalog of test tools by domain and environment for test planning
applies_when: [test_flow needs selectable tools for a defined domain, environment, test level, or evidence task]
exclusions: [do not design test cases, execute product tests without explicit scope, publish path-leaking knowledge, or invent tool behavior]
inputs: [target domain, environments, test levels, test policy, approved planning or design scope, source and DB finding XIDs when relevant, scripts and CI configuration, runbooks, tool evidence, intended publication mode]
outputs: [tool catalog artifact, applicability and coverage matrices, setup/data/evidence requirements, limitations and gaps, source evidence, validity/recheck conditions, test_flow handoff]
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
knowledge_needs:
  - id: test_design_criteria
    query: test design criteria
    required_when: Required when classifying test levels, target coverage, evidence, and applicability
    seed_xids: [8C4D2A7E5102]
  - id: domain_knowledge_ontology_rules
    query: domain knowledge ontology rules
    required_when: Required when preparing publication-ready catalog knowledge and its identity/relations
    seed_xids: [5803607419B9]
control_refs: []
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

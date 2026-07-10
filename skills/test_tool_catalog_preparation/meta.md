<!-- xid: F2A36B52C0EB -->
<a id="xid-F2A36B52C0EB"></a>

# Skill Meta: test_tool_catalog_preparation

- skill_id: `test_tool_catalog_preparation`
- summary: prepare a domain/environment test-tool catalog as reusable domain knowledge for test planning and test design
- use_when: a project needs existing domain-specific, environment-specific, organization-specific, or repository-specific test tools cataloged before `test_flow` can select tools for a test plan, test design, integration/regression testing, DB verification, or evidence capture
- input: target domain and environment scope, test policy, test tool policy when available, approved requirements or planning scope, current source-structure or DB-state knowledge XIDs when relevant, repository test scripts and CI configuration, tool documentation, runbooks, prior test evidence, local execution constraints, and intended publication mode
- output: test-tool catalog knowledge draft or publication-ready artifact with tool inventory, domain/environment applicability matrix, supported test targets, test levels, setup inputs, data requirements, execution method, evidence capture method, limitations, freshness/recheck conditions, unknown tool gaps, source evidence list, and handoff to `test_flow`
- maturity: `draft`
- execution_mode: `subagent_preferred`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: test tool catalog preparation
- tuning: domain/environment test-tool cataloging for downstream test planning
- responsibility: create reusable test-tool selection knowledge so `test_flow` can select tools by XID instead of guessing from local environment assumptions
- os_contract: v1
- constraints: do not design test cases; do not execute product tests unless explicitly requested as evidence collection; do not invent tool behavior, supported environments, data setup, evidence capture, or limitations; do not expose local filesystem paths in client-facing domain knowledge; separate repository-local evidence from published catalog content; record tool gaps and unsupported assumptions as `unknown`; hand XID-bearing catalog publication through the configured domain-knowledge publication path
- lifecycle:
  - startup: confirm target domain, target environments, test levels, planning or design scope, available test policy and test tool policy, source evidence locations, XID/publication expectation, and whether local inspection is allowed
  - planning: define tool inventory buckets, domain/environment applicability buckets, test-level coverage buckets, setup/data/evidence buckets, limitations and recheck buckets, unknown tool-gap rows, and publication handoff
  - execution: inspect tool evidence, build the candidate tool inventory, classify each tool by domain/environment/test level/target type, record setup and evidence requirements, identify unsupported scope, and prepare a reusable test-tool catalog artifact
  - monitoring_and_control: downgrade unsupported tool claims to `unknown`, stop on local path leakage in publication-ready output, stop if the work turns into test case design or product test execution, and keep missing source evidence explicit
  - closure: return the catalog artifact, source evidence list, unknown and unsupported tool gaps, validity/recheck conditions, selected publication target, and handoff to `test_flow`
- tags: `test`, `tooling`, `catalog`, `domain-knowledge`, `planning`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=test_design_criteria; bind=8C4D2A7E5102
  - name=skill_knowledge_operating_model; bind=91C4B7E2D5A8
  - name=domain_knowledge_ontology_rules; bind=5803607419B9
- knowledge_inputs:
  - name=current_source_structure_finding; accepts=current-source-structure-findings,source-structure-overview,module-map,service-map; purpose=optional-tool-location-and-runtime-context
  - name=current_db_state_finding; accepts=database-current-state-analysis,database-design-package; purpose=optional-db-test-tool-context

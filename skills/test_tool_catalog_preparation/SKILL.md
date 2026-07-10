<!-- xid: DE815228B04C -->
<a id="xid-DE815228B04C"></a>

# Skill: test_tool_catalog_preparation

## Purpose

Prepare a reusable test-tool catalog for a target domain and environment so
`test_flow` can select test tools by XID instead of relying on local-path
inspection, model memory, or implicit environment assumptions.

The output is domain knowledge about available tools and their valid use
conditions. It is not a test plan, test design, or test execution result.

## Required Knowledge (XID)

- [Test design criteria](../../knowledge/quality/110_test_design_criteria.md#xid-8C4D2A7E5102)
- [Skill domain knowledge runtime input design](../../docs/designs/085_skill_domain_knowledge_runtime_input_design.md#xid-BC6C6D89E4E1)
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

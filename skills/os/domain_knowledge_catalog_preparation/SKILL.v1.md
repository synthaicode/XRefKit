---
schema_version: 1
skill_id: domain_knowledge_catalog_preparation
xid: A7C9E2D4F610
aliases: [EE95165681E8, A409BACC6918]
summary: prepare a path-free XID-addressable catalog of repository and configured external domain knowledge for Skill runs
applies_when: [MCP or an equivalent runtime must expose selectable domain knowledge before a Skill run]
exclusions: [do not author knowledge, assign XIDs, import external XID-bearing knowledge, or decide downstream Skill requirements]
inputs: [MCP domain-knowledge root configuration, repository knowledge metadata, external metadata or scan result, target client or run identity, optional selected Skill knowledge requirements, optional prior catalog]
outputs: [metadata-only catalog package, candidate XID mapping, conflict and invalid-entry report, validation evidence, consuming-runtime handoff]
criteria:
  - id: path_free_catalog
    statement: Client-facing entries contain metadata and XID references without local filesystem paths or default full bodies.
    verification: Inspect the generated package and confirm selected bodies remain lazy behind XID resolution.
  - id: identity_integrity
    statement: Missing or duplicate XIDs and incomplete selectable metadata remain explicit invalid or conflict findings.
    verification: Review the conflict and not-catalog-ready report against all discovered candidates.
  - id: publication_boundary
    statement: XID-less material is handed to adoption or publication and is never treated as selectable canonical knowledge.
    verification: Inspect the handoff and each candidate's XID/publication state.
knowledge_needs:
  - id: domain_knowledge_ontology_rules
    query: domain knowledge ontology rules
    required_when: Required when classifying identity, duplication, validity, or relationships for catalog entries
    seed_xids: [5803607419B9]
control_refs: []
---
<!-- xid: A7C9E2D4F610 -->
<a id="xid-A7C9E2D4F610"></a>

# Skill: domain_knowledge_catalog_preparation

## Method

1. Confirm the configured repository and external roots, target client/run, selected Skill requirements, and whether the output is a run-local draft or a publication handoff. Use the operating model and repository structure as documentation lookups when their boundaries are needed; they are not Knowledge inputs for this definition.
2. Resolve the ontology Knowledge need when its condition applies. Keep external knowledge as evidence, and stop if it attempts to redefine Skill, workflow, authority, routing, escalation, or MCP contract rules.
3. Define the catalog scope and metadata shape. Discover repository and configured external candidates, retaining server-side source diagnostics while excluding local paths from client-facing output.
4. For every candidate, record XID, title, kind, domain, tags, summary, content hash or version, freshness, validity conditions, and confidence as supported by evidence. Preserve `unknown` with impact when evidence is missing.
5. Record missing XIDs, duplicate XIDs, missing title/summary/kind/domain/hash, stale entries, and required-input gaps as explicit invalid or conflict findings. Map selected Skill requirements to candidate XIDs only when the match is evidenced.
6. Keep full bodies lazy. Resolve a selected body only through `get_document_by_xid`, and record the selected XID and content hash/version for the consuming runtime.
7. Do not assign XIDs or copy already-XID-bearing external knowledge into this repository. Hand XID-less material to the domain-knowledge adoption/publication owner and hand unresolved conflicts to MCP/catalog administration.

## Stop and handoff

Stop when client-facing output would leak a local path, duplicate identity cannot be resolved deterministically, or a required selected input has no evidenced candidate. Downgrade weak claims to `unknown`; do not invent summaries, domains, freshness, validity, or tool behavior. Return the scope, selectable entries, invalid/conflict report, validation evidence, and consuming Skill/runtime handoff.

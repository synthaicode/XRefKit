<!-- xid: A409BACC6918 -->
<a id="xid-A409BACC6918"></a>

# Skill Meta: domain_knowledge_catalog_preparation

- skill_id: `domain_knowledge_catalog_preparation`
- summary: prepare an XID-addressable domain-knowledge catalog from repository knowledge and MCP-configured external domain-knowledge roots before Skill execution
- use_when: MCP will supply domain knowledge to a Skill run and the available repository plus external XID-bearing knowledge must be listed, summarized, validated, and made selectable without exposing local paths or full bodies
- input: MCP domain-knowledge root configuration or equivalent server-side root list, repository knowledge catalog metadata, external domain-knowledge metadata or scan result, target client/run identity, optional selected Skill `knowledge_inputs`, and optional prior prepared catalog package
- output: prepared domain-knowledge catalog package, available domain-knowledge metadata list with XID/title/kind/domain/tags/summary/content hash or version/freshness/validity conditions, optional candidate mapping from Skill `knowledge_inputs` to matching XIDs, catalog conflict report, unavailable or invalid domain-knowledge report, validation evidence, and handoff target for the consuming Skill/runtime
- maturity: `trial`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: prepare MCP domain-knowledge supply for Skill runtime selection without importing external XID-bearing knowledge into this repository
- responsibility: list and summarize MCP-ingested domain knowledge, validate XID/selectability metadata, and make repository plus external domain knowledge available as one XID-addressable supply for downstream Skills
- os_contract: v1
- constraints: do not author new domain knowledge; do not assign XIDs; do not move already-XID-bearing external domain knowledge into this repository as the normal connection method; do not expose local paths in client-facing output; do not load all full bodies by default; use `get_document_by_xid` for selected bodies; treat missing XID, duplicate XID, missing summary, missing content hash/version, and unresolved required Skill inputs as blockers or explicit invalid entries
- lifecycle:
  - startup: confirm MCP/domain-knowledge root configuration, repository catalog metadata, external domain-knowledge metadata, target client/run, optional selected Skill `knowledge_inputs`, and the XID boundary; stop if external knowledge attempts to redefine XRefKit governance or if XID-less material is being treated as selectable
  - planning: define catalog scope, metadata shape, selected-Skill candidate matching, and checks for missing XID, duplicate XID, missing title/summary/kind/domain/hash, local path leakage, stale knowledge, and required input gaps
  - execution: build a compact metadata-only available-domain-knowledge list from repository knowledge plus MCP-configured external roots, map selected Skill `knowledge_inputs` to candidate XIDs when provided, record conflicts and invalid entries, and keep full bodies lazy behind `get_document_by_xid`
  - monitoring_and_control: stop on client-facing local path leakage, unresolved duplicate XIDs, required input slots without candidates, or catalog entries that cannot be safely summarized; downgrade weak metadata to `unknown` with impact instead of inventing it
  - closure: return the prepared catalog package, candidate mappings, conflict report, invalid/not-catalog-ready report, validation evidence, and handoff target for the consuming Skill/runtime
- tags: `operations`, `knowledge`, `mcp`, `catalog`, `runtime-input`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=skill_knowledge_operating_model; bind=91C4B7E2D5A8
  - name=xrefkit_startup_contract; bind=C3A1F78D9B22
  - name=repository_structure; bind=D0E1327DDD7F
  - name=domain_knowledge_ontology_rules; bind=5803607419B9
  - name=context_direction_guard_rules; bind=7A2F4C8D1601
- observation_refs:
  - `../../../observations/2026-06-28_skill_run_knowledge_ontology_management.md`

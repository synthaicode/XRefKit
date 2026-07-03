<!-- xid: E42C9F1A6B70 -->
<a id="xid-E42C9F1A6B70"></a>

# Skill Meta: source_structure_findings_registration

- skill_id: `source_structure_findings_registration`
- summary: register an existing source-structure analysis Markdown file as current canonical source-structure findings knowledge
- use_when: a user or workflow already has a source-structure analysis Markdown artifact, such as a `dotnet_change_analysis` report, and wants it read, normalized, and registered or refreshed in the current source structure findings catalog instead of running source analysis again
- input: existing analysis Markdown path or XID, target identity, source scope, analysis kind, source basis, publication mode (`proposal_only` or authorized `apply`), and optional target catalog entry or finding XID
- output: a proposed or applied canonical source-structure finding fragment, an updated current source structure findings catalog entry when authorized, source and evidence linkage, unresolved verification list, and handoff to `design_flow` or `knowledge_ontology_management`
- maturity: `trial`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: register existing source-analysis Markdown into canonical source-structure knowledge without re-running structure analysis
- responsibility: read an existing analysis Markdown artifact, extract the reusable current-source finding metadata, and prepare or apply the corresponding canonical knowledge registration
- os_contract: v1
- constraints: do not re-run source structure analysis when the provided Markdown already contains the required findings; do not invent missing structure facts from model memory; do not preserve stale catalog entries as history; canonical mutation requires authorized `apply`; when authority is absent, create a proposal and hand it to `knowledge_ontology_management`; keep only current facts in `knowledge/` and keep unresolved verification explicit
- lifecycle:
  - startup: confirm the analysis Markdown exists or the XID resolves, classify the source class, confirm publication mode, load the current source structure findings catalog and ontology/source rules, and stop on upward context influence
  - planning: search for existing catalog entries by target identity, source scope, aliases, and finding XID; decide create, refresh, split, reject_duplicate, or proposal_only handoff; identify missing required metadata before editing
  - execution: read the Markdown once for structure pivots, route/usecase traces, implicit runtime bindings, prohibited changes, selection metadata, source basis, and unresolved verification; normalize those fields into a canonical finding fragment or proposal; update the catalog only when apply is authorized
  - monitoring_and_control: downgrade unsupported or missing fields to unresolved verification; stop if the Markdown conflicts with existing current knowledge or tries to redefine workflow/Skill authority
  - closure: return the canonical finding XID or proposal path, catalog update status, source evidence, validation commands, unresolved verification, and the next handoff owner
- tags: `operations`, `knowledge`, `source-analysis`, `registration`, `xref`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
- knowledge_refs:
  - `../../../knowledge/organization/200_domain_knowledge_ontology_rules.md#xid-5803607419B9`
  - `../../../docs/reference/020_sources.md#xid-2FAD591BF725`
  - `../../../docs/policies/074_document_update_policy.md#xid-B1D42A6F90C3`
  - `../../../knowledge/source_analysis/170_current_source_structure_findings_catalog.md#xid-A9E742B1C6D0`
- observation_refs:
  - `../../../observations/2026-06-28_skill_run_knowledge_ontology_management.md`

<!-- xid: 83EDDDB5E158 -->
<a id="xid-83EDDDB5E158"></a>

# Skill Meta: knowledge_ontology_management

- skill_id: `knowledge_ontology_management`
- summary: curate new or materially revised domain knowledge through concept identity, duplication, split, replacement, and typed-relationship assessment before canonical publication
- use_when: a user or workflow will add a new canonical fragment under `knowledge/`, promote source material into domain knowledge, or materially revise the meaning, scope, applicability, or relationships of existing domain knowledge; do not use for typo-only, formatting-only, or mechanical XID-link maintenance
- input: proposed knowledge content or source material, target domain or candidate path, source basis, requested publication mode (`proposal_only` or `apply`), and any known related concepts or XIDs
- output: an ontology assessment recorded in the Skill run, a proposal or authorized canonical knowledge change, accepted typed XID relationships when justified, source and judgment linkage, validation evidence, and an explicit publication or handoff decision
- maturity: `trial`
- execution_mode: `local_default`
- guard_policy: `required`
- os_contract:
  - version: `1`
  - worklist_policy: `required`
  - execution_role: `required`
  - check_role: `required`
  - logging_policy: `session_required`
  - judgment_log_policy: `required_when_non_trivial`
  - unknown_risk_policy: `explicit`
  - closure_gate: `required`
  - handoff_policy: `explicit`
- constraints: ontology assessment does not replace source verification or human domain authority; canonical mutation requires an authorized `apply` request, while absent authority requires `proposal_only`; use only the controlled relationship vocabulary; do not invent relationships to make the graph appear complete; keep procedure in the Skill, canonical facts in `knowledge/`, original evidence in `sources/`, and operational or judgment history in `work/`
- lifecycle:
  - startup: confirm the proposed knowledge scope, publication mode, source class, and whether the change is semantic rather than mechanical; load the ontology, source, document-update, and context-direction rules
  - planning: search canonical knowledge by concept, aliases, scope, and likely relationships; create one work item per target fragment; classify the candidate as create, extend, split, supersede, or reject_duplicate
  - execution: record the ontology assessment, preserve source linkage, prepare or apply the knowledge change, add only justified typed XID relationships, update the knowledge index when needed, and run deterministic relation and XID validation
  - monitoring_and_control: stop canonical publication for unresolved semantic conflict, missing source authority, upward context influence, or an unauthorized mutation; record non-trivial identity and relationship judgments
  - closure: return changed or proposed paths, concept decision, relationships accepted or intentionally omitted, source and judgment evidence, validation results, unresolved items, and handoff owner
- tags: `operations`, `knowledge`, `ontology`, `xref`, `curation`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../../knowledge/organization/200_domain_knowledge_ontology_rules.md#xid-5803607419B9`
  - `../../../docs/020_sources.md#xid-2FAD591BF725`
  - `../../../docs/074_document_update_policy.md#xid-B1D42A6F90C3`
- observation_refs:
  - `../../../work/sessions/2026-06-28_session_knowledge_ontology_management_seed.md`
  - `../../../work/sessions/2026-06-28_skill_run_knowledge_ontology_management.md`
  - `../../../work/sessions/2026-06-28_skill_run_knowledge_ontology_management_2.md`

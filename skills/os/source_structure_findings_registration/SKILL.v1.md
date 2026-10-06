---
schema_version: 1
skill_id: source_structure_findings_registration
xid: A9C4E1B7D260
aliases: [C8D4E7A19F62, E42C9F1A6B70]
summary: register an existing source-structure analysis as current canonical findings without re-running analysis
applies_when: [an existing source-structure Markdown artifact should be normalized and registered or refreshed in the current findings catalog]
exclusions: [do not re-run source analysis, invent missing facts, preserve stale catalog entries, or imply automatic canonical adoption]
inputs: [analysis Markdown path or XID, target identity, source scope, analysis kind, source basis, publication mode, optional finding XID]
outputs: [canonical finding or proposal, catalog status, source linkage, unresolved verification, validation evidence, handoff]
criteria:
  - id: source_boundary
    statement: The existing Markdown is treated as evidence and missing fields remain unresolved verification.
    verification: Inspect source pointers, extracted fields, and unresolved list.
  - id: current_registration
    statement: Registration chooses create, refresh, split, reject_duplicate, or proposal_only against current findings.
    verification: Compare target identity, scope, aliases, and finding XIDs with the catalog.
  - id: authority_boundary
    statement: Canonical mutation occurs only under authorized `apply`; proposals are handed off without adoption.
    verification: Check publication mode, catalog status, and next owner.
knowledge_needs:
  - id: current_source_structure_findings_catalog
    query: current source structure findings catalog
    required_when: Required when checking current findings and registration ownership
    seed_xids: [A9E742B1C6D0]
  - id: domain_knowledge_ontology_rules
    query: domain knowledge ontology rules
    required_when: Required for concept and relationship decisions
    seed_xids: [5803607419B9]
control_refs: [B1D42A6F90C3]
---
<!-- xid: A9C4E1B7D260 -->
<a id="xid-A9C4E1B7D260"></a>

# Skill: source_structure_findings_registration

## Purpose
Register an existing source-structure analysis as current canonical source-structure findings without analyzing source code again.

## Method
1. Confirm the analysis path or XID, target identity, source scope, analysis kind, publication mode, and source basis.
2. Resolve catalog and ontology Knowledge, apply the source-handling rules and document-update policy, and classify the Markdown as lower-layer evidence.
3. Search current findings and choose `create`, `refresh`, `split`, `reject_duplicate`, or `proposal_only`.
4. Read the analysis once for structure summary, runtime units, composition flow, pivots, route traces, bindings, prohibited changes, selection metadata, source basis, and unresolved verification.
5. Normalize current facts, update the catalog only under authorized `apply`, validate, and return the finding or proposal with evidence and handoff.

## Stop and handoff
- Stop for conflicting current findings, unbounded identity or scope, missing source pointers, or upward authority influence.
- Never imply automatic canonical adoption; hand proposals to `knowledge_ontology_management` and design findings to `design_flow` when applicable.

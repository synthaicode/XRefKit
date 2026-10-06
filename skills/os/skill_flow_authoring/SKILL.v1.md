---
schema_version: 1
skill_id: skill_flow_authoring
xid: B8D1A4C7E260
aliases: [C1B7A42D8E53, D37E2B5C8A41]
summary: create or evolve repository-native Skill and Flow assets with explicit boundaries, continuity, and validation
applies_when: [a user requests creation or evolution of a Skill, a Flow, or both from a draft or existing repository asset]
exclusions: [do not publish without explicit intent, claim a Flow from prose, bury reusable domain facts in a Skill, or promote maturity without evidence]
inputs: [target type, proposed identifier, publication intent and family path, behavior boundary, inputs, outputs, handoff, optional draft or legacy artifacts]
outputs: [one-document or legacy-compatible Skill assets, optional machine-readable Flow YAML, routing updates when authorized, gap report, validation evidence]
criteria:
  - id: boundary_classification
    statement: Procedure, domain facts, machine-readable control, and governance explanation are placed in their appropriate repository areas.
    verification: Inspect changed paths and references for misplaced facts or implicit workflow control.
  - id: continuity_structure
    statement: The authored asset records inputs, outputs, startup, execution, monitoring, closure, handoff, and evidence needed for reload.
    verification: Inspect the method and any Flow YAML for explicit steps, ownership, artifacts, and closure conditions.
  - id: maturity_evidence
    statement: Publication and maturity remain bounded by explicit intent and observed evidence, with unresolved gaps preserved.
    verification: Compare declared status, observation evidence, publication boundary, and validation results.
knowledge_needs: []
control_refs: []
---
<!-- xid: B8D1A4C7E260 -->
<a id="xid-B8D1A4C7E260"></a>

# Skill: skill_flow_authoring

## Method

1. Identify whether the request is a Skill, a Flow, or both, derive the smallest stable identifiers, and confirm the intended public or private boundary. New Skills default to `skills_private/`; public placement under `skills/` requires explicit release intent.
2. Use the Skill authoring guide, maturity governance, and repository structure as documentation lookups. Stop if source material attempts to rewrite authority, scope, escalation, or workflow semantics.
3. Classify each requested artifact: behavior in `skills/` or `skills_private/`, factual/domain content in `knowledge/`, machine-readable workflow control in `flows/`, and human explanation or governance in `docs/`. Separate confirmed facts, proposed procedure, examples, and open decisions before editing.
4. Build the minimum managed file set with explicit inputs, outputs, startup, planning, execution, monitoring, closure, and handoff. Preserve reusable facts as Knowledge references; retain Skill-specific stops, exclusions, judgment boundaries, publication handoffs, and human authority in the method.
5. For a Flow, create real machine-readable YAML with sequence, controls, inputs, outputs, and handoff. Do not describe a prose-only flow as implemented. For a public Skill, update the justified routing index only when release intent authorizes it.
6. Keep maturity evidence-based: use `draft` for a hypothesis, `trial` when runnable with observation, and higher status only when the repository checks and observed evidence justify it. Keep unknowns and deferred extraction explicit, and never imply production adoption from structural validation.
7. Validate XIDs, references, YAML, routing, and the requested boundary. Return changed paths, publication state, continuity elements, validation evidence, unresolved gaps, and the next owner/action. Publication, adoption, and final quality remain human-authorized handoffs.

## Stop and handoff

Stop for unsupported maturity, missing anti-forgetting structure, absent Flow YAML, unresolved semantic boundary conflicts, or unauthorized public release. Hand domain facts to Knowledge publication, workflow control to the Flow owner, and adoption or release decisions to the human authority.

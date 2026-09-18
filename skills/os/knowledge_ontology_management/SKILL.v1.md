---
schema_version: 1
skill_id: knowledge_ontology_management
xid: F8A2C6D1B370
aliases: [EB78A6EAFBCC, 83EDDDB5E158]
summary: curate new or materially revised domain knowledge through identity, duplication, split, replacement, and relationship assessment
applies_when: [a user or workflow will add or materially revise canonical knowledge and needs ontology assessment before publication]
exclusions: [do not use for typo-only or mechanical link maintenance; ontology assessment does not replace source verification or human authority]
inputs: [proposed knowledge or source material, target domain or path, source basis, publication mode, related concepts or XIDs]
outputs: [ontology assessment, concept decision, proposed or authorized change, typed relationships, evidence, validation, handoff]
criteria:
  - id: concept_identity
    statement: Existing concepts, aliases, scope, and candidate XIDs are searched before create, extend, split, supersede, or duplicate decisions.
    verification: Inspect search evidence and the concept decision.
  - id: authority_boundary
    statement: "`proposal_only` and authorized `apply` remain distinct and canonical mutation is never implied automatically."
    verification: Check publication mode, authority, and resulting paths.
  - id: relationship_evidence
    statement: Relationships are added only when semantically justified and source and judgment evidence remain linked.
    verification: Inspect relationship rationale, omitted edges, and evidence.
knowledge_needs:
  - id: domain_knowledge_ontology_rules
    query: domain knowledge ontology rules
    required_when: Required for concept identity and relationship decisions
    seed_xids: [5803607419B9]
control_refs: [B1D42A6F90C3]
---
<!-- xid: F8A2C6D1B370 -->
<a id="xid-F8A2C6D1B370"></a>

# Skill: knowledge_ontology_management

## Purpose
Curate materially new or revised domain knowledge before canonical publication, with justified typed XID relationships.

## Method
1. Confirm semantic scope, source class, publication mode, and authority; use `proposal_only` absent authorized `apply`.
2. Resolve ontology Knowledge, apply the source-handling rules and document-update policy, then search canonical concepts, aliases, scope, and relationships.
3. Create one work item per fragment and classify `create`, `extend`, `split`, `supersede`, or `reject_duplicate`.
4. Preserve source linkage, record identity and relationship judgments, and prepare or apply one coherent current fragment.
5. Validate relations and XIDs, update indexes only when authorized, and return paths, decisions, evidence, unresolved items, and handoff.

## Stop and handoff
- Stop publication for semantic conflict, missing source authority, upward context influence, or unauthorized mutation.
- Never imply automatic canonical adoption; hand proposals or conflicts to the human authority or appropriate receiving Skill.

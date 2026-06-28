# Judgment: Domain Knowledge Ontology Rules Identity

- date: `2026-06-28`
- skill_id: `knowledge_ontology_management`
- target: `knowledge/organization/200_domain_knowledge_ontology_rules.md#xid-5803607419B9`
- decision: `create`

## Evidence

- The canonical Skill catalog had no ontology-management Skill before this
  change.
- Repository search found taxonomy examples and code-structure graph rules, but
  no canonical rule governing concept identity and typed semantic relationships
  for additions to `knowledge/`.
- XRefKit already provides XID identity, source policy, and context-direction
  rules that the new rule composes rather than replaces.

## Relationship Judgment

- `applies_to` the Knowledge Index because the rule governs canonical domain
  knowledge additions across the indexed knowledge surface.
- `depends_on` Context Direction Guard Rules because source-derived knowledge
  must not redefine higher-layer control.
- No stronger taxonomy relationship was asserted because the rule is a
  repository-wide curation rule rather than a specialization of one existing
  domain concept.

## Publication Boundary

The Skill is public under `skills/os/` because the requested behavior applies
whenever canonical repository domain knowledge is added. A private Skill could
not provide repository-wide semantic routing or a shared publication gate.

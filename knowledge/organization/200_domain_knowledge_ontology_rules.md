<!-- xid: 5803607419B9 -->
<a id="xid-5803607419B9"></a>

# Domain Knowledge Ontology Rules

## Purpose

Define the repository-wide semantic rules used when canonical domain knowledge
is added or materially revised.

These rules provide ontology-assisted curation for XID-backed Markdown
knowledge. They do not claim that XRefKit is an RDF/OWL store or that unstated
relations can be inferred automatically.

## Knowledge Unit

- A canonical knowledge fragment is one coherent topic under `knowledge/`.
- Its XID is the stable identity of that fragment.
- If one proposed fragment contains independently reusable topics, split it
  before publication.
- A wording-only change does not create a new knowledge identity.
- A semantic replacement uses a new XID and preserves compatibility through
  `xref deprecate`.

## Concept Decision

Classify every proposed addition or material revision as exactly one of:

- `create`: no existing fragment owns the concept
- `extend`: an existing fragment owns the concept and can remain coherent
- `split`: the proposal contains independently reusable concepts
- `supersede`: the prior concept is no longer authoritative
- `reject_duplicate`: the proposal repeats existing canonical knowledge

Base the decision on XID search results, source evidence, scope, applicability,
and semantic meaning. Filename or wording differences alone do not establish a
new concept.

## Controlled Relationship Vocabulary

Use only the following relationship types in a `## Knowledge Relations`
section:

- `broader_than`: the source fragment defines a broader concept than the target
- `narrower_than`: the source fragment specializes the target concept
- `part_of`: the source fragment is a constituent of the target concept
- `depends_on`: the source fragment requires the target concept to be applied
- `constrains`: the source fragment limits allowed interpretation or behavior
  of the target
- `applies_to`: the source fragment is applicable to the target scope
- `related_to`: the concepts are materially related but no stronger relation is
  justified

Use an XID-backed Markdown link as the target. Do not add a weak
`related_to` edge merely to ensure that an edge exists.

Do not write `supersedes` or `superseded_by` manually. Use `xref deprecate` so
the repository maintains that compatibility relationship.

## Relationship Example

```md
## Knowledge Relations

- constrains: [Knowledge Index](../000_index.md#xid-23059118FBB9)
- depends_on: [Context direction guard rules](160_context_direction_guard_rules.md#xid-7A2F4C8D1601)
```

The section is optional when no semantically justified relation exists. The
ontology assessment must still state that no canonical relation was added and
why.

## Evidence and Authority

- Preserve original material under `sources/` when the source policy requires
  it.
- Add a source pointer to source-derived knowledge.
- Treat repository-owned canonical knowledge as current evidence, not as
  authority to override the active Flow, Capability, or Skill.
- Keep proposal analysis and non-trivial relationship judgments under `work/`;
  keep only the current authoritative result in `knowledge/`.

## Required Assessment Record

For each addition or material revision, record:

- target knowledge path
- proposed primary concept
- aliases or competing terms searched
- candidate existing XIDs
- concept decision
- accepted typed relationships
- rejected relationship candidates when rejection is non-obvious
- source basis
- unresolved semantic conflicts
- publication or handoff decision

## Validation Rules

- Every relationship type must belong to the controlled vocabulary.
- Every relationship target must resolve to an existing XID.
- A fragment must not relate to itself.
- Duplicate relationship pairs are invalid.
- Every public canonical knowledge fragment must appear in
  `knowledge/000_index.md`.
- An unresolved semantic conflict blocks canonical publication.
- A source gap remains an explicit unknown; do not fill it from model recall.

## Boundary

This ontology layer organizes knowledge identity and explicit semantic
relationships. It does not replace:

- source verification
- human authority over domain decisions
- workflow or capability definitions
- Skill procedures
- formal RDF/OWL reasoning when a task explicitly requires it

## Knowledge Relations

- applies_to: [Knowledge Index](../000_index.md#xid-23059118FBB9)
- depends_on: [Context direction guard rules](160_context_direction_guard_rules.md#xid-7A2F4C8D1601)

## Related

- [Knowledge Index](../000_index.md#xid-23059118FBB9)
- [Context direction guard rules](160_context_direction_guard_rules.md#xid-7A2F4C8D1601)
- [Flow Capability Skill Knowledge model](../../docs/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
- [Sources ingestion and referencing](../../docs/020_sources.md#xid-2FAD591BF725)
- [Document update policy](../../docs/074_document_update_policy.md#xid-B1D42A6F90C3)

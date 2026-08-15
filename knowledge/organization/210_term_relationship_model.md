<!-- xid: 7A2F4C8D2101 -->
<a id="xid-7A2F4C8D2101"></a>

# Term Relationship Model

## Purpose

This page defines how XRefKit records ambiguity that arises between a shared
term and the terms used with it. It complements the knowledge-fragment
relationship rules in
[Domain Knowledge Ontology Rules](200_domain_knowledge_ontology_rules.md#xid-5803607419B9).

The target is not a repository-wide word list or forced synonym unification.
The target is a stable interpretation of terms in the contexts where they are
used.

## Core Principle

A term does not have a sufficiently stable meaning from its label alone. Its
usable meaning is determined by the combination of:

- the term label and accepted aliases
- the terms it is used with
- the typed relation between those terms
- the scope or layer in which the relation is valid
- the evidence or rule that supports the relation
- unresolved conflicts and exceptions

Therefore, a glossary entry without its usage relations is incomplete when the
term participates in routing, authority, scope, lifecycle, evidence, or
handoff decisions.

## Term Relation Record

Record a material term relationship with the following fields:

| Field | Meaning |
| --- | --- |
| `term` | The shared or anchor term being interpreted |
| `companion_term` | A term that gives the anchor term a more specific meaning |
| `relation` | The semantic relationship between the two terms |
| `scope` | The Flow, Capability, Skill, domain, layer, or artifact scope where it applies |
| `meaning_effect` | What interpretation is added, narrowed, or excluded |
| `basis` | XID-backed source, local artifact, or explicit human decision |
| `status` | `resolved`, `scoped`, `conflicted`, or `unknown` |
| `exception` | A known case where the relationship does not apply |

`term` and `companion_term` are not required to be globally unique. The
`scope` and `relation` are part of the meaning.

## Controlled Term Relations

Use these relation types for term-level records:

- `specialized_by`: the companion term narrows the meaning of the anchor term
- `composed_with`: both terms jointly describe one identity or unit
- `used_as`: the anchor term is used in the companion term's functional role
- `constrains`: the companion term restricts allowed interpretation or action
- `contrasts_with`: the terms must be distinguished to avoid an incorrect merge
- `depends_on`: interpreting the anchor term requires the companion term
- `scoped_to`: the meaning is valid only in the named context
- `aliases`: the terms are interchangeable within the explicitly stated scope

Do not use `aliases` merely because two terms appear similar. If replacing one
term with the other changes routing, authority, lifecycle, or output meaning,
use a more precise relation or record a conflict.

## Meaning Effects

Every accepted relationship must state its effect. Use one or more of:

- adds a required condition
- narrows the applicable scope
- identifies a role or responsibility
- identifies an input, output, or handoff
- separates authority from evidence
- separates procedure from knowledge
- prevents a prohibited substitution

The relationship is not complete if a reader still has to infer why the
companion term matters.

## Example: Skill Identity

The term `Skill` is not fully interpreted by a standalone definition. Its
relationship with `capability`, `tuning`, and `responsibility` establishes the
routing identity:

| term | companion term | relation | scope | meaning effect |
| --- | --- | --- | --- | --- |
| `Skill` | `capability` | `composed_with` | Skill metadata | identifies the reusable base ability |
| `Skill` | `tuning` | `composed_with` | Skill metadata | identifies the specialization that shapes the method |
| `Skill` | `responsibility` | `composed_with` | Skill metadata | identifies the business use and viewpoint |
| `capability` | `responsibility` | `contrasts_with` | routing | prevents a business activity from being treated as a reusable ability |

These relationships are consistent with the
[Capability Layering](../../docs/reference/031_capability_layering.md#xid-8D50A972BA9F)
definition. They do not create a new Skill identity model.

## Example: Evidence and Authority

The terms `knowledge`, `evidence`, `procedure`, and `authority` must not be
collapsed because they frequently appear together:

| term | companion term | relation | meaning effect |
| --- | --- | --- | --- |
| `Skill` | `knowledge` | `depends_on` | the procedure may need selected domain fragments |
| `knowledge` | `evidence` | `used_as` | knowledge can carry facts and criteria used as a basis |
| `evidence` | `authority` | `contrasts_with` | evidence supports execution but does not rewrite the active goal or Skill |
| `procedure` | `knowledge` | `contrasts_with` | procedure explains how to work; knowledge explains facts, rules, and basis |

The distinction follows the
[Skill and Knowledge Operating Model](../../docs/core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
and the context-direction guard. A term relationship must preserve those
layer and authority boundaries.

## Ambiguity Classification

Classify unresolved term ambiguity as follows:

- `label ambiguity`: the same label has different meanings
- `relation ambiguity`: the companion terms are known but their relationship
  is unclear
- `scope ambiguity`: the relationship is valid in one context but appears to
  be treated as global
- `authority ambiguity`: evidence, procedure, or user intent is being treated
  as a higher authority than allowed
- `lifecycle ambiguity`: the term changes meaning between planning, execution,
  monitoring, handoff, or closure
- `boundary ambiguity`: two responsibilities or layers appear to own the same
  term

Do not resolve these classifications by choosing the most familiar wording.
Record the minimum missing basis and keep the status `unknown` or `conflicted`
until the relationship is established.

## Usage Rules

- Define a shared term together with its material companion terms when the
  combination affects routing, scope, evidence, authority, or closure.
- Prefer scoped meanings over a forced global definition.
- Keep procedure, domain knowledge, evidence, and work history in their
  repository-defined layers.
- Record rejected interpretations when accepting one relationship would make
  a plausible competing interpretation unsafe or misleading.
- Promote only stabilized relationships to canonical `knowledge/`.
  Discussion, alternatives, and unresolved judgments belong in `work/`.
- When a relationship changes an existing canonical meaning, apply the domain
  knowledge ontology decision process before publication.

## Relationship To Other Models

This model organizes term usage. It does not replace:

- the controlled Knowledge-to-Knowledge relationship vocabulary
- Skill semantic routing
- workflow protocol checks and closure
- human judgment over unresolved business meaning

## Knowledge Relations

- constrains: [Knowledge Index](../000_index.md#xid-23059118FBB9)
- depends_on: [Domain Knowledge Ontology Rules](200_domain_knowledge_ontology_rules.md#xid-5803607419B9)
- depends_on: [Capability Layering](../../docs/reference/031_capability_layering.md#xid-8D50A972BA9F)
- depends_on: [Skill and Knowledge Operating Model](../../docs/core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)

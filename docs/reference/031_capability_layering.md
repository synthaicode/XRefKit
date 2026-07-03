<!-- xid: 8D50A972BA9F -->
<a id="xid-8D50A972BA9F"></a>

# Capability Layering

This page defines the capability / tuning / responsibility triad and how it
identifies and routes Skills after the skill-centric consolidation. It aligns
with
[Skill and knowledge operating model](../core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)
and
[Skill-centric architecture consolidation](../designs/083_skill_centric_architecture_consolidation.md#xid-9DF3B80F9CBE).

## Intent

- Keep `knowledge/` focused on domain knowledge.
- Identify each Skill by the capability / tuning / responsibility triad.
- There is no separate `capabilities/` definition layer; capability is the Skill
  meta triad element and the routing vocabulary (see the triad-as-identity rule
  below).

## Layers

- `knowledge/`: shared domain knowledge and local rules
- `skills/`: executable procedures that carry the meta triad, declare knowledge
  slots, and run under the generic workflow protocol

## The Triad

- capability:
  - reusable base professional ability
  - examples: software development, accounting, planning
- tuning:
  - specialization of a capability by technology, framework, domain, quality
    focus, or their composition
  - examples: C#, SQL, C# + SQL, .NET, construction-industry accounting,
    security-focused review
- responsibility:
  - how a tuned capability is exercised for a business purpose
  - examples: implementation, code review, finance, bookkeeping, management
    accounting

## Triad Is Skill Meta Identity

The triad is the Skill's fixed meta identity and the routing vocabulary.

- Different triad = different Skill. The triad is **not** assigned at execution
  time: `tuning` and `responsibility` are structural (they shape the Skill's
  method and viewpoints), so a differently-tuned or differently-responsible unit
  is a different Skill, not the same Skill parameterized at runtime.
- The triad is **not** stored in `capabilities/` definition files; those are
  dissolved. A controlled capability / tuning / responsibility vocabulary
  registry keeps routing terms consistent and preserves the ability inventory.
- Semantic routing matches intent and current state against the triad to select
  the Skill; only the task and its concrete inputs are supplied per run.

## Role Replacement Rule

Do not encode broad role prompts such as "you are a senior engineer" as the
Skill identity. Split them into capability, tuning, and responsibility:

| Skill use | capability | tuning | responsibility |
| --- | --- | --- | --- |
| implement C# software | software development | C# | implementation |
| implement a C# and SQL system | software development | C# + SQL | implementation |
| review C# software | software development | C# | quality check |

The capability and tuning may be shared by many Skills. The responsibility is
what differs between implementation, review, design, verification, release
preparation, or other business uses of the same tuned capability.

In Skill metadata:

- `capability` names the reusable base ability.
- `tuning` names the direct specialization (a single one such as `C#`, or a
  composed one such as `C# + SQL`).
- `responsibility` names the Skill's business use. This replaces the former
  `role_responsibilities.executor` value, which was always a responsibility, not
  a role.
- There is **no** role field. Every Skill is the executor; the checker is the
  deterministic protocol (`fm skill verify`), so recording a role on the Skill
  conveys nothing.
- `knowledge_slots` declare the knowledge the Skill needs; they are resolved at
  runtime against the base+local catalog. There are no static `knowledge_refs`
  or `capability_refs` bindings.

## Reuse Rule

The triad identity is useful only when the Skill procedure stays reusable. Keep
the Skill body focused on the judgment or execution method, and keep
language-specific, framework-specific, or domain-specific criteria in
`knowledge/`, selected through the Skill's slots.

When adding a Python implementation or review Skill after a C# one:

- keep `capability` and `responsibility` stable when the business use is the same
- change `tuning` from `C#` to `Python`
- resolve tuning-specific knowledge through the slots instead of hard-coding C#
  criteria
- share the common method and common knowledge; do not copy the Skill body when
  only the knowledge basis changes

## Composite Tuning Knowledge Rule

When `tuning` is composed, slot resolution must preserve both shared and specific
parts. For `capability: software_development`, `tuning: C# + SQL`, and
`responsibility: implementation`, the resolved knowledge set may contain:

- common software-development knowledge
- C#-specific implementation knowledge
- SQL-specific implementation knowledge
- C# / SQL boundary knowledge, such as transaction boundaries, data mapping,
  migration ordering, query parameterization, concurrency, and persistence
  consistency

Do not flatten composite tuning into one large language-specific checklist when
the common and per-tuning parts can be separated.

## Naming Rule

- Capability names should describe reusable professional ability.
- Responsibility names should describe the business use of that ability.
- Names such as `service catalog analysis` are responsibilities or activities,
  not capabilities; the supporting capability beneath them should use an
  abstract name such as `scope classification`.

Example:

- base capability: software development
- technical tuning: C# + SQL
- domain tuning: construction industry
- responsibility: implementation for a construction-industry C# and SQL system

## Review Judgment Rule

- For review-oriented `judgment` work, LLM internal knowledge is supplementary
  only.
- Primary evidence must come from local artifacts and the knowledge fragments
  resolved through the Skill's slots.
- Review knowledge usage rules are defined in
  [LLM review knowledge usage rules](../../knowledge/organization/140_llm_review_knowledge_usage_rules.md#xid-7A2F4C8D1401).

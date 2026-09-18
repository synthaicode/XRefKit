<!-- xid: 8D50A972BA9F -->
<a id="xid-8D50A972BA9F"></a>

# Capability Layering

This page defines the capability / tuning / responsibility triad and how it
identifies and routes Skills after the skill-centric consolidation. It aligns
with
[Skill and knowledge operating model](../core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8).

## Intent

- Keep `knowledge/` focused on domain knowledge.
- Use capability / tuning / responsibility as runtime routing vocabulary.
- Keep the SkillDefinition reusable and independent of a particular instruction
  binding.

## Layers

- `knowledge/`: shared domain knowledge and local rules
- `skills/`: executable SkillDefinitions that declare method, criteria, and
  Knowledge needs, and run under the generic Workflow Protocol

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

## Triad Is Runtime Routing Binding

The triad is created from the instruction and current task state as a runtime
route and execution binding. It is recorded with the run so the selected
judgment basis is observable, but it is not a fixed SkillDefinition identity.

- Different runtime triad = different routing context. The reusable method may
  remain the same SkillDefinition when the instruction changes its tuning or
  responsibility.
- A controlled capability / tuning / responsibility vocabulary registry keeps
  routing terms consistent and preserves the ability inventory.
- Semantic routing selects a SkillDefinition using `applies_when`; it then
  derives the triad and other binding fields from the instruction before the
  subagent starts.

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

In the canonical SkillDefinition v1:

- `capability`, `tuning`, and `responsibility` are supplied by the runtime
  binding derived from the instruction.
- The definition itself contains method, `applies_when`, `inputs`, `outputs`,
  `criteria`, `knowledge_needs`, and `control_refs`.
- There is **no** role field. Every Skill is the executor; the checker is the
  deterministic protocol (`xrefkit skill verify`), so recording a role on the Skill
  conveys nothing.
- `knowledge_needs` are resolved at runtime through the XID Knowledge catalog;
  legacy `knowledge_slots` and split `meta.md` are migration inputs only.

See [SkillDefinition v1](../core/contracts/096_skill_definition_contract.md#xid-E6A19D4B72C3),
[Subagent startup read](../guides/095_subagent_startup_read.md#xid-D7A4C9E2B861),
and [Complex SkillDefinition Flow](../guides/097_complex_skilldefinition_flow.md#xid-4F8C2A7D91E6).

## Reuse Rule

Keep the SkillDefinition body focused on the judgment or execution method, and
keep language-specific, framework-specific, or domain-specific criteria in
Knowledge selected through `knowledge_needs` and XID resolution.

When adding a Python implementation or review Skill after a C# one:

- derive the appropriate `capability`, `tuning`, and `responsibility` for each
  instruction
- resolve tuning-specific Knowledge through XID needs instead of hard-coding
  criteria
- share the common method and Knowledge; do not copy the SkillDefinition when
  only the runtime binding or Knowledge basis changes

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

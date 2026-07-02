# Judgment Log

## JDG-001: placement of csharp_error_policy_extraction

- date: `2026-06-12`
- topic: `skills_private vs public skills/ placement for new csharp_error_policy_extraction Skill`
- judgment: `non_trivial`
- decision: place under `skills_private/csharp_error_policy_extraction/` per the skill_flow_authoring default; treat the user's "part of the structural-analysis Skill" as a content relationship (deep-dive of the `dotnet_change_analysis` error-handling-contract viewpoint, wired via `use_when`, `knowledge_refs`, and handoff wording), not as explicit public-release intent
- evidence: `skills/os/skill_flow_authoring/SKILL.md` rules ("Do not publish a new Skill under skills/ unless the user explicitly requested public release"); precedent `skills_private/business_card_pdf_generator/`
- boundary: public release under `skills/` next to `dotnet_change_analysis`, plus routing index registration, is deferred until explicitly requested

## JDG-002: initial maturity trial

- date: `2026-06-12`
- topic: `initial maturity for csharp_error_policy_extraction`
- judgment: `non_trivial`
- decision: declare `trial` (not `draft`): the 3-phase procedure is load-ready, the meta carries the full trial schema, and `observation_refs` links the authoring run log
- evidence: `python -m fm skill check --meta skills_private/csharp_error_policy_extraction/meta.md --level trial` ok; precedent `skills_private/business_card_pdf_generator/meta.md` (trial with authoring-run observation ref)
- boundary: promotion to `stable` requires at least one operational run on a real C# codebase with recorded run evidence

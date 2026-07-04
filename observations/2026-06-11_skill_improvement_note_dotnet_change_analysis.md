# Skill Improvement Note: dotnet_change_analysis

- date: `2026-06-11`
- skill_id: `dotnet_change_analysis`
- current_maturity: `trial`
- observed_from:
  - structure review of `skills/dotnet_change_analysis/` (meta, SKILL.md, viewpoints, template) on 2026-06-11
  - `docs/054_change_analysis_skill_usage.md` (usage guide exists, but no linked run evidence)
  - `docs/055_judgment_log_usage.md` (references the skill only as a usage example)
- gap_type:
  - `output`
  - `constraints`
  - `knowledge_refs`
- summary: the skill rode the legacy maturity default (treated as stable) with
  zero observation_refs and would not pass an explicit `--level stable` or
  `--level trial` check; SKILL.md lacked the operating-contract sections
  (worklist, execution/check role, logging, unknowns, context direction guard,
  closure gate, handoff); the viewpoint catalog lacked DI registration and
  lifetime analysis, middleware/pipeline order, and security boundary
  placement; the boundary against `csharp_review` (defect findings) and
  `security_review` (vulnerability assessment) was undefined; no routing entry
  reached the skill from `agent/010_capability_routing.md`.
- change_needed: declare `maturity: trial` honestly with this note as the
  refinement basis; add `model_tier: standard`; complete the contract sections
  in SKILL.md; add DI-lifetime, pipeline-order, and security-boundary
  viewpoints to the catalog and template; define handoff boundaries to
  `planning_flow`, `csharp_review`, and `security_review`; add the routing
  entry.
- promotion_effect: supports trial now; stable promotion requires at least one
  real run log under `work/sessions/` opened by `fm skill run` and linked via
  `observation_refs`.

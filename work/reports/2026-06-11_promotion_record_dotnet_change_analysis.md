# Skill Promotion Record: dotnet_change_analysis

- date: `2026-06-11`
- skill_id: `dotnet_change_analysis`
- promotion: `trial` -> `stable`
- decided_by: repository owner (session decision, 2026-06-11)
- meta: `skills/dotnet_change_analysis/meta.md`

## Promotion Basis

| Stable requirement (docs/059) | Evidence |
|------|------|
| draft minimum fields | `meta.md` carries skill_id, summary, use_when, input, output, skill_doc |
| observation_refs | `work/reports/2026-06-11_skill_improvement_note_dotnet_change_analysis.md` (gap review) and `work/sessions/2026-06-11_skill_run_dotnet_change_analysis.md` (real run, closed) |
| valid execution_mode | `subagent_preferred` |
| valid guard_policy | `required` |
| constraints | explicit, including the analysis/fix boundary and handoff routing |
| runtime capability ref | `capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md` |
| guard references | `capabilities/management/130_cap_mgt_004_context_direction_guard.md` + `knowledge/organization/160_context_direction_guard_rules.md` |
| full os_contract | version 1, all nine policies declared |
| operating-contract sections in SKILL.md | Startup, Context Direction Guard, Worklist, Execution Role, Check Role, Logging, Planning, Execution, Monitoring and Control, Unknowns And Risks, Closure Gate, Handoff, Rules, Failure Handling |

## Refinements Leading To Promotion (2026-06-11)

1. Removed the legacy maturity default: declared `maturity` explicitly
   (was undeclared, treated as stable while failing an explicit
   `--level trial` check for missing observation_refs).
2. Completed the operating-contract sections in SKILL.md.
3. Set `model_tier: standard` (executor runs in the standard-tier subagent;
   checker always runs in the independent light checker).
4. Reframed the viewpoint catalog from known-framework checking to
   local-rule extraction (pipeline structure and order).
5. Added viewpoints: DI registration and lifetimes, convention-based
   discovery, build-configuration-dependent behavior, error handling
   contract, security boundary placement, serialization contract and
   ambient-dependency conventions; generalized documented-vs-implicit
   recording to all extracted rules. Roslyn-detectable concerns remain
   out of scope by rule.
6. Added brownfield support: de-facto responsibility extraction rule,
   change placement basis, and the follow-or-deviate-explicitly handoff
   regulation.
7. Added the prohibited-changes derivation rule (silent-breakage-only,
   evidence-required, hard/conditional classification, receiving-phase
   gate).
8. Added the routing entry in `agent/010_capability_routing.md`.

## Observed Run Evidence

- Run: `work/sessions/2026-06-11_skill_run_dotnet_change_analysis.md`
  - target: `work/external/Ksql.Linq/src` (296 .cs files), read-only
  - executor: `dotnet_change_analysis:executor` in `skill-executor-standard`
    subagent (standard model tier)
  - checker: `dotnet_change_analysis:checker` in independent `skill-checker`
    subagent (light tier), with evidence spot-checks
  - output: `work/reports/2026-06-11_change_analysis_ksql_linq_src.md`
    (viewpoints: 18 done / 1 unknown / 1 not_applicable; 5 extracted local
    rules; placement basis for 3 rule homes; 3 handoffs to csharp_review,
    1 to security_review)
  - closure: passed `fm skill close` with all work items done, output and
    evidence artifacts recorded, unknowns resolved, risks escalated
    explicitly

## Checks At Promotion Time

- `python -m fm skill check --meta skills/dotnet_change_analysis/meta.md`
  -> ok at `checked_level: stable`
- `python tools/audit_skill_runtime_logs.py --tracked-only` -> ok

## Residual Items (not blockers for stable)

- The 2026-06-11 run predates the prohibited-changes section; the next run
  will produce it as part of the note.
- Accumulate further run observations; refine viewpoint catalog if repeated
  `unknown` states cluster on the same viewpoints.
- `governed` promotion requires this record (or a successor) referenced via
  `governance_refs` plus a governance/audit basis decision.

<!-- xid: 907B100F9F9D -->
<a id="xid-907B100F9F9D"></a>

# Skill Meta: source_structure_overview

- skill_id: `source_structure_overview`
- summary: produce a reusable whole-system source-structure overview for a target repository or service before proposition-specific change analysis
- use_when: user needs a baseline explanation of how a brownfield .NET repository, service, module family, or application works structurally before asking specific change-impact questions; use before `dotnet_change_analysis` when the target's current source structure knowledge is missing, stale, or too narrow
- input: target repository, service, solution, project, or directory; explicit source scope boundary; optional known domain knowledge catalog; optional intended publication mode for later source-structure finding registration
- output: Markdown source-structure overview with system purpose, runtime units, major subsystem map, startup/composition flow, request/event/job flows, state and persistence boundaries, extension/plugin/feature mechanisms, Brownfield API Naming Extractor output for externally visible and data-flow-relevant naming surfaces, configuration/tenant/environment variation, external boundaries, key structural authorities, reusable domain-knowledge metadata, validity/recheck conditions, unknown structure areas, and completion-control result; when the confirmed scope cannot be completed, output an incomplete-analysis cause review instead of a source-structure overview
- maturity: `trial`
- execution_mode: `subagent_preferred`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: source structure analysis
- tuning: whole-system .NET source-structure overview without a specific change proposition
- responsibility: create reusable current source-structure knowledge that later proposition-specific analysis Skills can select by XID as target domain knowledge
- os_contract: v1
- constraints: do not answer a specific change-impact proposition; do not flatten the target into framework labels; explain the whole target structure before local detail; do not shrink the confirmed source scope during execution; use deterministic `tools/` inventories for grep-weak or coverage-critical structure questions when needed; extract Brownfield API Naming Extractor output when externally visible or data-flow-relevant naming surfaces are in scope; record unknowns instead of inventing missing runtime paths or unsupported naming rules; treat in-scope unresolved unknowns as closure blockers; do not publish or hand off partial analysis as canonical source-structure knowledge; when analysis cannot complete, classify whether the cause is context size, scope size, ambiguous instruction, unavailable tool/source, or evidence conflict; preserve lower-layer source evidence; hand publication to source_structure_findings_registration when canonical knowledge registration is needed
- lifecycle:
  - startup: confirm target path, fixed source scope boundary, intended overview depth, available domain knowledge inputs, whether the result is for proposal-only or later canonical registration, and the completion strategy for the fixed scope
  - planning: define subsystem buckets, runtime-flow buckets, state-boundary buckets, Brownfield API Naming Extractor buckets, structural-authority evidence searches, needed deterministic inventory tools, output path, read-only analysis rows, and completion-control rows for the fixed source scope
  - execution: produce a whole-system structure overview for the fixed source scope, map major subsystems and runtime flows, identify structural authorities and variation mechanisms, extract local brownfield API and data-flow naming rules, record reusable domain-knowledge metadata, and resolve, scope out, or escalate uncovered areas; if completion is impossible, produce an incomplete-analysis cause review instead of a partial overview
  - monitoring_and_control: treat missing whole-system sections as leaks; downgrade framework-shaped assumptions or naming rules without local evidence to `unknown`; treat in-scope unknowns and scope narrowing as closure blockers; require cause classification for incomplete analysis; stop if the task turns into proposition-specific change analysis
  - closure: return either a complete overview artifact with evidence commands, used knowledge refs, validity/recheck conditions, resolved/out-of-scope/escalated unknowns, completion-control result `complete`, and handoff target, or an incomplete-analysis cause review with next action and handoff owner; only the complete overview path may proceed to registration
- tags: `dotnet`, `source-analysis`, `structure`, `overview`, `domain-knowledge`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=common_source_analysis_criteria; bind=5F21C8A41001
  - name=custom_framework_common_criteria; bind=5F21C8A41002
  - name=dotnet_change_analysis_viewpoints; bind=2E7B5A1FD201
  - name=structure_analysis_determinism_tiers; bind=5301B897BA41
  - name=csharp_naming_convention_extraction; bind=B4F7E1A2C903
  - name=current_source_structure_findings_catalog; bind=A9E742B1C6D0
- knowledge_inputs:
  - name=target_domain_context; accepts=source-structure-overview,current-source-structure-findings,module-map,service-map,architecture-note; purpose=optional-prior-structure-context
- observation_refs:
  - `../../observations/2026-07-04_source_structure_overview_creation.md`

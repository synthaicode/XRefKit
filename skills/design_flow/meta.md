<!-- xid: 1B28D96E4C11 -->
<a id="xid-1B28D96E4C11"></a>

# Skill Meta: design_flow

- skill_id: `design_flow`
- summary: execute design business activity through reusable solution-design capability
- use_when: user needs implementation-ready design after planning outputs are approved
- input: approved requirements, work plan, source modification policy, pre-analyzed current source structure findings from canonical domain knowledge for each implementation target, Brownfield API Naming Extractor output from the selected source-structure finding when naming is design-relevant, data change policy, planning basis source list, and DB design package when database schema/persistence/migration/data-correction changes are in scope
- output: approved design, target paths, source modification design, data change design, DB design package reference when required, brownfield naming-rule basis and candidate names for external specification and data-flow elements backed by selected source-structure finding XIDs, source analysis basis reference, current-source-structure finding XIDs used as design inputs, created or refreshed current-source-structure finding XIDs when pre-analysis was missing or stale, design basis policy reference, and referenced constraint-derivation output paths when derivation was required
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute design business activity through reusable solution-design capability
- responsibility: user needs implementation-ready design after planning outputs are approved
- os_contract: v1
- constraints: preserve unresolved design assumptions explicitly; do not redefine business scope; express the change method clearly enough for pre-code review; derive candidate names for new or changed external specification and data-flow elements from the selected source-structure finding's Brownfield API Naming Extractor output instead of leaving naming to implementation or doing ad hoc source scanning in design; use pre-analyzed current source structure findings from canonical domain knowledge as the design source-analysis basis; when a source target lacks current source structure findings, the finding is stale, or naming evidence is missing for a design-relevant naming surface, perform pre-analysis with `source_structure_overview` and publish it through `source_structure_findings_registration` before freezing implementation-facing design; route database schema, persistence behavior, migration, data correction, and data ownership changes through `db_current_state_analysis` when current DB state is missing or stale, then `db_design` before implementation-facing closure; use `dotnet_change_analysis` for proposition-specific structure and impact analysis after the baseline source-structure finding exists or when the change objective needs additional coverage; when structural design artifacts still imply unresolved behavior, route through the constraint-derivation pack before freezing implementation-facing design
- lifecycle:
  - startup: confirm planning outputs, source modification policy, and pre-analyzed current source structure findings in canonical domain knowledge for each implementation target exist; if current source findings are missing, stale, or lack required Brownfield API Naming Extractor output, require `source_structure_overview` plus `source_structure_findings_registration` publication before design input is accepted; if unresolved structural design behavior remains, require constraint derivation before design closure
  - planning: define design scope, change-design boundaries, management rows, naming-rule usage needs for external specification and data-flow elements, database current-state and design needs, whether canonical source pre-analysis or naming evidence is missing or stale, required pre-analysis/registration rows, and whether constraint derivation is required before implementation-facing decisions
  - execution: perform solution design drafting through `CAP-DSN-001`, use registered current source structure finding XIDs as design inputs, create missing current source structure findings with `source_structure_overview`, publish or refresh the canonical finding through `source_structure_findings_registration`, preserve the intended change method explicitly, derive brownfield naming candidates from the selected source-structure finding's naming output, incorporate DB current-state analysis and DB design package output when database changes are in scope, and incorporate confirmed derivation outputs where structural ambiguity existed
  - monitoring_and_control: downgrade weak design assumptions, unclear change methods, missing naming evidence, missing DB current-state analysis, missing DB design package, or unsupported naming candidates to `unknown`; stop if implementation-facing design would be frozen for a source target without canonical current source structure findings or where constraint derivation should have run
  - closure: finalize states and hand off the approved design package, naming-rule basis and candidate names, source analysis basis finding XIDs, and design basis policy reference with unresolved items
- tags: `design`, `execution`, `implementation-preparation`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=xddp_basics; bind=7A2F4C8D1701
  - name=xddp_supporting_methods; bind=7A2F4C8D1711
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=current_source_structure_findings_catalog; bind=A9E742B1C6D0
  - name=csharp_naming_convention_extraction; bind=B4F7E1A2C903

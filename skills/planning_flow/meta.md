<!-- xid: E3F2F376922F -->
<a id="xid-E3F2F376922F"></a>

# Skill Meta: planning_flow

- skill_id: `planning_flow`
- summary: execute planning business activity through reusable work-and-policy planning capability grounded in domain knowledge and current-source findings
- use_when: user needs planning after requirements are approved
- input: approved requirements, change target list, current source structure findings, domain knowledge references
- output: work plan, source modification policy, data change policy, data correction tool policy, test policy, test tool policy, release policy, planning basis source list, created or refreshed current-source-structure finding XIDs when target structure was missing
- maturity: `draft`
- execution_mode: `local_default`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: execute planning business activity through reusable work-and-policy planning capability grounded in domain knowledge and current-source findings
- responsibility: user needs planning after requirements are approved
- os_contract: v1
- constraints: draft only; do not finalize priority or resource allocation; keep requirement-to-target difference tracing explicit for downstream design and review; do not use unregistered local source-structure notes as planning basis; when current source structure findings are missing or stale, create latest structure information with `source_structure_overview` and register it through `source_structure_findings_registration` before planning relies on it
- lifecycle:
  - startup: confirm approved requirements, current source findings, and domain knowledge references exist; if target structure information is missing or stale, require `source_structure_overview` plus `source_structure_findings_registration` before using it as planning basis
  - planning: define planning scope, policy targets, requirement-to-target traceability, current-source-finding gaps, structure-creation/registration rows, and management rows from domain knowledge and current-source findings
  - execution: perform work planning and policy drafting through `CAP-PLN-001` while preserving impacted target mapping and creating/registering missing current source structure findings before source policy relies on them
  - monitoring_and_control: downgrade weak planning assumptions, unsupported source-structure claims, and unclear impact mappings to `unknown`; stop closure when an in-scope source target lacks a canonical current-source-structure finding
  - closure: finalize states and hand off planning outputs, planning basis source list, current-source-structure finding XIDs, and change-design basis notes with unresolved items
- tags: `planning`, `execution`, `policy`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=xddp_basics; bind=7A2F4C8D1701
  - name=xddp_supporting_methods; bind=7A2F4C8D1711
  - name=common_source_analysis_criteria; bind=5F21C8A41001
  - name=custom_framework_common_criteria; bind=5F21C8A41002
  - name=custom_framework_analysis_criteria; bind=30E6A4F6F3AB
  - name=ipa_release_activity_catalog; bind=7B3E5D1A6101

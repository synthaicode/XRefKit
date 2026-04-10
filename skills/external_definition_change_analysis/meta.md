<!-- xid: 5E2A9C11F4D8 -->
<a id="xid-5E2A9C11F4D8"></a>

# Skill Meta: external_definition_change_analysis

- skill_id: `external_definition_change_analysis`
- summary: analyze applications driven by external definitions such as XML or configuration files and generate a Markdown change-analysis note
- use_when: user needs structure analysis or impact investigation for applications where XML, YAML, JSON, properties, or framework-specific config files control runtime behavior
- input: target path, change request or analysis objective, optional scope filters, optional output path
- output: Markdown change-analysis note, definition-to-code mapping list, impacted boundary list, unresolved dependency list, viewpoint check results
- execution_mode: `subagent_preferred`
- guard_policy: `required`
- constraints: do not assume a definition is active only because it exists; confirm consuming mechanism and activation condition; record unknowns explicitly
- lifecycle:
  - startup: confirm target path, change objective, scope, and required viewpoints
  - planning: define scope, output path, viewpoint buckets, and safe scope split for read-only analysis
  - execution: analyze external definitions, load order, mappings, activation, flow control, logging, concurrency, performance, resources, tests, and generate a Markdown note
  - monitoring_and_control: treat unrecorded viewpoints as leaks and downgrade weak conclusions to `unknown`
  - closure: return the Markdown note, mapping list, impacted boundaries, and unresolved items with reasons
- tags: `analysis`, `investigation`, `xml`, `configuration`, `markdown`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../knowledge/source_analysis/100_common_source_analysis_criteria.md#xid-5F21C8A41001`
  - `../../knowledge/source_analysis/110_custom_framework_common_criteria.md#xid-5F21C8A41002`
  - `../../knowledge/source_analysis/130_external_definition_change_analysis_viewpoints.md#xid-4D91A26BE301`

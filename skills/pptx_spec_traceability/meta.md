<!-- xid: 7F4C1A2D9E60 -->
<a id="xid-7F4C1A2D9E60"></a>

# Skill Meta: pptx_spec_traceability

- skill_id: `pptx_spec_traceability`
- summary: extract presentation specifications into Markdown, assign traceability IDs, connect slide images and shapes to nearby explanatory text, and write the IDs back into the deck
- use_when: user needs to convert PowerPoint-based specifications into Markdown artifacts while preserving slide-level traceability and reducing review burden in the original deck
- input: source pptx path, optional target Markdown destination, optional slide scope, optional traceability ID prefix
- output: Markdown specification fragments, slide-item descriptions, traceability ID map, updated pptx with written-back IDs, unresolved list
- execution_mode: `local_default`
- guard_policy: `required`
- os_contract:
  - version: `1`
  - worklist_policy: `required`
  - execution_role: `required`
  - check_role: `required`
  - logging_policy: `session_required`
  - judgment_log_policy: `required_when_non_trivial`
  - unknown_risk_policy: `explicit`
  - closure_gate: `required`
  - handoff_policy: `explicit`
- constraints: keep slide number and object position explicit; do not separate image-derived or shape-derived items from the slide text that gives them meaning; write IDs back into the original deck or the controlled deck copy used as the source of truth
- lifecycle:
  - startup: confirm source deck path, slide scope, and ID policy
  - planning: map slides, text boxes, shapes, images, notes, and callouts into extraction units
  - execution: extract specification content, connect object position to nearby explanatory text, create Markdown fragments, assign IDs, and write the IDs back to the deck
  - monitoring_and_control: record ambiguity when object meaning and nearby text disagree
  - closure: finalize Markdown outputs, verify deck write-back, and preserve source pointers
- tags: `pptx`, `powerpoint`, `presentation`, `specification`, `traceability`, `image`, `import`
- skill_doc: `./SKILL.md`
- capability_refs:
  - `../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5`
  - `../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11`
- knowledge_refs:
  - `../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601`
  - `../../docs/020_sources.md#xid-2FAD591BF725`

<!-- xid: D4701BFC6EA4 -->
<a id="xid-D4701BFC6EA4"></a>

# Skill Meta: code_constraint_derivation

- skill_id: `code_constraint_derivation`
- summary: derive hidden assumptions and selected business constraints from generated or reviewed C# code
- use_when: AI-generated or manually reviewed C# code may embed asymmetric branches, implicit preconditions, or hidden business thresholds that need human confirmation
- input: C# code files, optional target classes or methods, and optional related design context
- output: CCD-prefixed derivation file under `work/constraint_derivation/` by default, plus business-layer confirmation items and implementation-layer notes
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: derive hidden assumptions and selected business constraints from generated or reviewed C# code
- responsibility: AI-generated or manually reviewed C# code may embed asymmetric branches, implicit preconditions, or hidden business thresholds that need human confirmation
- os_contract: v1
- constraints: derive only from explicit code choices rather than generic runtime possibilities; keep language-level exception noise out; write the derivation result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm code input exists and load the framework plus the code-constraint catalog
  - planning: identify review scope, code signals, and where business-layer confirmation may be required
  - execution: detect selected code signals, classify them, and write the CCD result file
  - monitoring_and_control: stop if unsupported business meaning is being inferred from generic runtime behavior rather than explicit code choices
  - closure: return the written derivation path, high-priority confirmation items, and remaining gaps
- tags: `review`, `code`, `.NET`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- knowledge_refs:
  - `../../../../docs/policies/014_working_area_policy.md#xid-111D282CA0EA`
  - `../../../../knowledge/packs/constraint-derivation/110_constraint_derivation_framework.md#xid-81A6C4E2B190`
  - `../../../../knowledge/packs/constraint-derivation/190_code_constraint_derivation_catalog.md#xid-A1D4E8C93B71`
- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md

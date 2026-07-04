<!-- xid: B87A2C3E4567 -->
<a id="xid-B87A2C3E4567"></a>

# Skill Meta: commonality_derivation

- skill_id: `commonality_derivation`
- summary: derive cross-cutting commonality candidates from completed primary constraint-derivation outputs
- use_when: multiple primary derivation outputs exist and the user needs a second pass for shared implementation candidates or scope-boundary checks
- input: completed DCD/UCD/LCD/ICD/ACD/AACD/CCD/XCD/ISD lists with traceable ids and optional pack-level design context
- output: CD-prefixed commonality file under `work/constraint_derivation/` by default, plus CB-prefixed boundary checks and grouped human confirmation points
- maturity: `trial`
- execution_mode: `local_default`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- tuning: derive cross-cutting commonality candidates from completed primary constraint-derivation outputs
- responsibility: multiple primary derivation outputs exist and the user needs a second pass for shared implementation candidates or scope-boundary checks
- os_contract: v1
- constraints: run only after primary derivation outputs exist; aggregate patterns without deciding the final abstraction; keep commonality candidates separate from scope-boundary concerns; write the result to `work/constraint_derivation/` with a date-prefixed filename unless the user explicitly supplies another output path
- lifecycle:
  - startup: confirm primary derivation lists are complete enough for a secondary pass and load the shared framework plus the commonality signals
  - planning: flatten all confirmed and unresolved items into one analyzable list while preserving source ids
  - execution: detect recurring patterns, emit CD and CB items, and present tradeoffs rather than deciding integration automatically
  - monitoring_and_control: stop if the task tries to collapse distinct business rules into one abstraction without human confirmation
  - closure: return the candidate table, boundary-check table, and the next human decisions required
- tags: `design`, `cross-cutting`, `requirements-derivation`
- skill_doc: `./SKILL.md`
- knowledge_slots:
  - name=constraint_derivation_framework; bind=81A6C4E2B190
  - name=commonality_derivation_signals; bind=9C27AE51D648
- observation_refs:
  - ../../../../observations/2026-06-21_skill_run_skill_flow_authoring.md

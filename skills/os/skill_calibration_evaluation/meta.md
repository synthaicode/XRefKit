<!-- xid: 6F3A9C2D7B10 -->
<a id="xid-6F3A9C2D7B10"></a>

# Skill Meta: skill_calibration_evaluation

- skill_id: `skill_calibration_evaluation`
- summary: run isolated calibration evaluations for PyPI-distributed XRefKit Skills without exposing evaluator answers to the evaluated Skill
- use_when: a published XRefKit Skill package needs repeatable fixture evaluation, calibration checks, or cross-Skill drift comparison
- input: installed Skill packages, package evaluation manifests, model configuration, repetition count, and evaluator output collection path
- output: isolated evaluation plan, per-case raw outputs, calibration findings, baseline comparison, and human disposition handoff
- maturity: `trial`
- execution_mode: `subagent_preferred`
- model_tier: `standard`
- capability_layering: `required`
- workflow_protocol: `required`
- capability: `quality_assurance`
- tuning: `package_skill_calibration`
- responsibility: independent calibration evaluation of published Skill outputs
- os_contract: v1
- constraints: discover evaluation assets from installed PyPI packages only; never use repository-relative Skill or fixture paths as the package contract; never copy expected answers or calibration rules into the evaluated target; run each case in an isolated target and evaluation context; treat public cases as smoke coverage and held-out cases as a separate evaluator boundary; never auto-edit a Skill from an alarm
- lifecycle:
  - startup: discover installed package manifests and confirm model, repetition, and output paths
  - planning: build one isolated plan entry per package Skill and case; record package and corpus identity
  - execution: materialize only the fixture target and invoke the normal Skill runtime per plan entry
  - monitoring_and_control: stop on missing manifest, missing target, answer leakage, package mismatch, or incomplete run evidence
  - closure: aggregate scores and calibration alarms, record unresolved cases, and hand off disposition to the Skill owner
  - handoff: return raw outputs, evidence hashes, alarm reasons, and the next human decision
- tags: `evaluation`, `calibration`, `pypi`, `drift`
- skill_doc: `./SKILL.md`
- observation_refs:
  - `../../../observations/2026-05-10_session_skill_flow_authoring_seed.md`

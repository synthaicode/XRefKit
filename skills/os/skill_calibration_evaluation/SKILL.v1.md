---
schema_version: 1
skill_id: skill_calibration_evaluation
xid: E3B7A1C8D490
summary: run isolated calibration evaluations for installed PyPI XRefKit Skills without exposing evaluator answers
applies_when:
- a published XRefKit Skill package needs repeatable fixture evaluation, calibration checks, or cross-Skill drift comparison
exclusions:
- never use repository paths as the package contract
- leak expected answers
- or edit a Skill from an alarm without separate explicit scoped user authorization
inputs:
- installed Skill packages, package evaluation manifests, model configuration, repetition count, and evaluator output collection path
outputs:
- isolated evaluation plan, per-case raw outputs, calibration findings, baseline comparison, and human disposition handoff
criteria:
- id: isolation
  statement: Each package case runs in a fresh target with expected and calibration material outside evaluated context.
  verification: Inspect package identity, fixture isolation, and evaluator boundary for every run.
- id: evidence
  statement: Raw outputs, hashes, model details, case corpus, and run context are recorded.
  verification: Check the per-run collection record and evidence links.
- id: disposition
  statement: Pass, alarm, or blocked outcomes and unresolved questions are handed to the accountable Skill owner.
  verification: Inspect baseline comparison and human handoff.
- id: source_obligation_retention
  statement: Skill-specific source applicability, required Knowledge, prohibitions, procedures, outputs, and completion gates retain their original conditions and strength; summaries do not relax them.
  verification: Inspect the preserved source obligations and source-specific declarations, including all conditional stops, handoffs, and completion requirements. Runtime and shared-control authority follow the active startup/adoption contracts.
knowledge_needs: []
control_refs: []
aliases:
- 720938921D2C
- 6F3A9C2D7B10
---
<!-- xid: E3B7A1C8D490 -->
<a id="xid-E3B7A1C8D490"></a>

# Skill: skill_calibration_evaluation

## Purpose
Run isolated calibration and drift evaluations from the installed PyPI Skill package boundary.

## Method
1. Discover installed package manifests and confirm model snapshot, repetitions, and output path.
2. For each case, resolve the package root, validate the manifest, create a fresh target, and copy only its fixture.
3. Keep expected answers and calibration rules outside the target and evaluated context; invoke the normal package route.
4. Record package/version/hash, Skill/procedure hash, corpus and fixture hashes, model parameters, context, raw output, and evaluator result.
5. Score output presence, evidence coverage, unknown/handoff behavior, forbidden overclaims, variance, and baseline regression.

## Stop and handoff
- Stop as `blocked` on missing manifests or targets, answer leakage, package mismatch, or incomplete evidence.
- An alarm is a human-review signal, not permission to change the Skill; hand disposition to the Skill owner with raw evidence.

An explicitly authorized correction to restore approved fixed-output quality
is a separate flow under the
[Fixed Output Quality Protocol](../../../docs/core/contracts/112_fixed_output_quality_protocol.md#xid-F9C2A8D471B0).
It may adjust scoped prompt/procedure wording, but cannot change accepted
criteria/examples, bypass independent review, or expose held-out assets.
Original no-auto-edit declarations below mean that an alarm cannot itself
authorize edits; they do not prohibit this separately authorized corrective
flow. Evaluation isolation and independent review remain mandatory.

## Preserved source obligations

The source procedure and Skill-specific declarations below retain their original conditions and strength. The concise method and header above are navigation and verification summaries; they neither relax these obligations nor add different requirements. Original metadata lifecycle summaries likewise do not override the detailed original procedure. The original source identity is recorded by the adoption manifest; its aliases resolve to this canonical document.

Runtime capability, tuning, responsibility, execution mode, model choice, and maturity are not supplied by this source text. Use the active ExecutionBinding and repository adoption contract; draft refusal and explicit missing input remain in force. The adoption binding also preserves explicitly declared legacy model-tier quality gates and knowledge-input policies; it does not select a model for this session. Legacy CAP activity labels do not infer or override a runtime capability. Common Workflow, reporting, logging, uncertainty, and guard clauses refer to the already loaded startup contracts, not an independent control-policy source.

### Original Skill-specific procedure

# Skill Calibration Evaluation

Run evaluation from the installed PyPI Skill package boundary. The repository
checkout is not the runtime source of a published Skill and must not be used as
the package contract.

## Inputs

- installed packages registered through the `xrefkit.skill_packages` entry-point;
- each package's strict `package_manifest.yaml` and co-located
  `evaluation/manifest.yaml`;
- model provider, exact model snapshot, and inference parameters;
- repetition count, normally at least three independent runs;
- output directory for raw outputs, scores, and the final human handoff.

## Isolation Rule

For each manifest case:

1. resolve the package root from the installed package entry point;
2. validate the evaluation manifest and case references;
3. create a fresh temporary target directory;
4. copy only the case's `target` fixture into that directory;
5. keep `expected` and `calibration` outside the target and outside the
   evaluated model context;
6. invoke the Skill through its normal package/runtime route;
7. destroy or quarantine the temporary target after collection.

The evaluated Skill receives the target and the ordinary task input. It does
not receive the expected answer, calibration rules, case id when that would
reveal the case purpose, or the evaluator's prior findings.

Use the bundled planner to produce an auditable plan:

```powershell
python scripts/plan_package_evals.py --discover --output work/eval-plan.json
```

Use `--package-root <installed-package-root>` only for package-level smoke
verification. Do not substitute a repository Skill path for an installed
package root in a published evaluation.

## Execution and Collection

Record for every run:

- package name, version, and package hash;
- Skill id and procedure hash;
- case corpus revision and fixture hash;
- model provider, model snapshot, and parameters;
- isolated target path and execution context id;
- raw Skill output and structured output artifact;
- expected/calibration evaluator result, kept outside the target context;
- run number and timestamp.

Run cases independently. Do not place multiple cases in one model context. Do
not tell the evaluated Skill that the input is an evaluation case when the
normal Skill task can be used instead.

## Calibration Evaluation

Score more than recall. Check:

- required output presence and schema validity;
- evidence and source-path coverage;
- severity or disposition calibration;
- `needs_confirmation`, unknown, and handoff behavior;
- forbidden overclaims from the case's calibration rules;
- repeat-to-repeat variance;
- regression against an approved baseline.

An alarm is a signal for human review, not permission to change the Skill. A
missing fixture, missing answer, package mismatch, or leaked evaluator asset is
`blocked`, not a passing or skipped case.

## Public and Held-Out Boundaries

Evaluation assets shipped in a public wheel are public smoke cases. They can
verify packaging and basic behavior but cannot protect against overfitting.
Held-out cases and their expected answers belong to a separate evaluator
package or controlled CI boundary. Never add held-out answers to the public
Skill package merely to make local scoring convenient.

## Human Handoff

Return a report with:

- `pass`, `alarm`, or `blocked` per case;
- raw-output and evidence links;
- missed expectations, overclaims, and calibration breaches;
- model/Skill/Knowledge change attribution where supported;
- baseline comparison and repeat spread;
- unresolved questions and the accountable Skill owner.

The Skill owner or quality reviewer decides whether to accept the alarm,
investigate the model, revise the Skill, revise the evaluation case, or update
the approved baseline. The evaluator must not self-approve a correction.
## Reporting Contract (共通報告)



- reporting_profile: checklist_verdict

Use the shared [Skill Reporting Contract](../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. Start with these headings in this order:

1. Status — done, partial, blocked, or escalated
2. Result — what was produced or decided
3. Evidence — output, evidence, checks, or XIDs
4. Open Items — unresolved unknowns, risks, judgments, or なし
5. Handoff — next owner and next action, or なし

Keep this summary-first section visible before Skill-specific detail; do not omit empty sections.

### Original Skill-specific declarations

- summary: run isolated calibration evaluations for PyPI-distributed XRefKit Skills without exposing evaluator answers to the evaluated Skill

- use_when: a published XRefKit Skill package needs repeatable fixture evaluation, calibration checks, or cross-Skill drift comparison

- input: installed Skill packages, package evaluation manifests, model configuration, repetition count, and evaluator output collection path

- output: isolated evaluation plan, per-case raw outputs, calibration findings, baseline comparison, and human disposition handoff

- constraints: discover evaluation assets from installed PyPI packages only; never use repository-relative Skill or fixture paths as the package contract; never copy expected answers or calibration rules into the evaluated target; run each case in an isolated target and evaluation context; treat public cases as smoke coverage and held-out cases as a separate evaluator boundary; never auto-edit a Skill from an alarm

- lifecycle:
  - startup: discover installed package manifests and confirm model, repetition, and output paths
  - planning: build one isolated plan entry per package Skill and case; record package and corpus identity
  - execution: materialize only the fixture target and invoke the normal Skill runtime per plan entry
  - monitoring_and_control: stop on missing manifest, missing target, answer leakage, package mismatch, or incomplete run evidence
  - closure: aggregate scores and calibration alarms, record unresolved cases, and hand off disposition to the Skill owner
  - handoff: return raw outputs, evidence hashes, alarm reasons, and the next human decision

- tags: `evaluation`, `calibration`, `pypi`, `drift`

- observation_refs:
  - `../../../observations/2026-05-10_session_skill_flow_authoring_seed.md`

Original source description: Run isolated calibration and drift evaluations for PyPI-distributed XRefKit Skills. Use when installed Skill packages expose evaluation manifests and the evaluator must run fixtures repeatedly without revealing expected answers, calibration rules, or held-out cases to the evaluated Skill.

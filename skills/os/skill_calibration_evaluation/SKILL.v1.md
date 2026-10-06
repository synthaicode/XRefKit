---
schema_version: 1
skill_id: skill_calibration_evaluation
xid: E3B7A1C8D490
aliases: [720938921D2C, 6F3A9C2D7B10]
summary: run isolated calibration evaluations for installed PyPI XRefKit Skills without exposing evaluator answers
applies_when: [a published Skill package needs repeatable fixture evaluation, calibration checks, or drift comparison]
exclusions: [never use repository paths as the package contract, leak expected answers, or auto-edit a Skill from an alarm]
inputs: [installed Skill packages, evaluation manifests, model configuration, repetition count, output path]
outputs: [isolated evaluation plan, raw outputs, calibration findings, baseline comparison, human disposition handoff]
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
knowledge_needs: []
control_refs: []
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

<!-- xid: 34E706142F30 -->
<a id="xid-34E706142F30"></a>

# csharp_review Drift-Detection Eval

This eval measures whether changes to `csharp_review` assets (SKILL.md,
meta.md, referenced knowledge) degraded the skill's detection or calibration
behavior. It is a **regression alarm, not an optimization target** (owner
decision, 2026-06-13).

## Purpose Boundary (binding)

- Run this eval to detect drift after skill-asset changes and before
  maturity promotion.
- Do not edit `csharp_review` assets with the goal of improving the score;
  treat a passing score as "no regression", never as a quality target.
- Do not load `eval_manifest_heldout.yaml` outside `score_findings.py`; it
  carries its own context-direction-guard header. Authoring runs that find
  held-out content in context must stop and record a guard violation.

## Fixture

- Repository: external fixture checkout supplied by the eval runner.
- Revision: the runner must check out the recorded fixture revision from
  `eval_manifest.yaml`.
- Visible micro-fixtures: `references/eval/fixtures/`, used for compact
  regression cases extracted from later reviews. `eval_manifest.yaml` names
  them by `fixture_case`; concrete source paths and line anchors live in
  `references/eval/fixtures/fixture_manifest.yaml`.
- Ground truth: expected findings are recorded in `eval_manifest.yaml` and
  the guarded held-out split.

## Run Protocol

1. Check out the fixture revision named in `eval_manifest.yaml` into a
   scratch worktree. The source repository location is runner-provided and
   must not be hard-coded in this Skill asset.
2. Run `csharp_review` against the scratch path through the normal runtime
   (`fm skill run`), output mode `findings-only`. The eval run must NOT load
   this eval directory; the executor sees the fixture cold.
3. In addition to the findings document, the executor emits a structured
   `findings.yaml`:

   ```yaml
   findings:
     - id: R-001
       category: synchronization        # one of the skill's categories
       file: tests/<fixture-tests>/<path>.cs
       line: 174
       severity: major                  # critical | major | minor | needs_confirmation
       gist: one line
   handoff:
     - file: src/<fixture-project>/<path>.cs
       gist: one line
   ```

4. Score: `python score_findings.py --actual <findings.yaml> [--baseline <previous score.json>]`
5. Repeat for **N >= 3 independent runs** and report per-run scores plus the
   spread; a single run is noise, not a signal.
6. Remove the worktree after scoring.

## Drift Alarm Rules

The scorer exits non-zero (alarm) when any of:

- a `major`-or-above expected finding is missed in a run
- the per-unit outbound-connection micro-fixture is downgraded to resource
  efficiency only, or below `major`, instead of `operational_resilience`
- the source-processing micro-fixture misses discovery/enumeration outside the
  observed failure boundary, or misses source identity/correlation loss before
  source removal
- a calibration rule defined in `eval_manifest.yaml` fails
- recall regresses against the supplied baseline

Misses of `minor` / `needs_confirmation` expected findings lower recall and
appear in the report but only alarm via baseline regression, so noise on
small findings does not page anyone by itself.

## Baseline

- The originating 2026-06-12 run found all 14 by construction; it is biased
  and is NOT the baseline.
- The first true baseline is the first eval execution under this protocol;
  store its `score.json` next to this file as `baseline_score.json`.

## Goodhart Guards

- Alarm, not target (see Purpose Boundary).
- Held-out split: 3 of the 14 expected findings live only in
  `eval_manifest_heldout.yaml`.
- Rotation: when a future real review on another codebase completes with
  fix-verified findings, add it as `csharp-review-eval-fixture-v2` and
  retire v1 from active duty (keep it for historical comparison). A fixture
  that skill authors have read about in detail loses held-out power over
  time; rotation restores it.

## Files

- `eval_manifest.yaml` — visible expected findings + calibration cases
- `eval_manifest_heldout.yaml` — held-out expected findings (guarded)
- `fixtures/fixture_manifest.yaml` — concrete source map for visible
  micro-fixture cases referenced by `fixture_case`
- `score_findings.py` — scorer (exit 0 = no drift, 1 = alarm)
- `baseline_score.json` — created by the first eval execution (absent until then)

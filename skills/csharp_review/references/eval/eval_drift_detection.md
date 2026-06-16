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

- Repository: `C:\dev\MailKit.Pooling`
- Tag: `csharp-review-eval-fixture-v1` (commit `100b3d5`, the pre-fix state)
- Ground truth: 14 findings verified on 2026-06-12 by applying fixes and
  passing the full test suite (`work/sessions/2026-06-12_csharp_review_mailkit_pooling_findings.md`)

## Run Protocol

1. Check out the fixture tag into a scratch worktree:
   `git -C C:\dev\MailKit.Pooling worktree add <scratch> csharp-review-eval-fixture-v1`
2. Run `csharp_review` against the scratch path through the normal runtime
   (`fm skill run`), output mode `findings-only`. The eval run must NOT load
   this eval directory; the executor sees the fixture cold.
3. In addition to the findings document, the executor emits a structured
   `findings.yaml`:

   ```yaml
   findings:
     - id: R-001
       category: synchronization        # one of the skill's six categories
       file: tests/MailKit.Pooling.Tests/Pool/PoolStateTransitionTests.cs
       line: 174
       severity: major                  # critical | major | minor | needs_confirmation
       gist: one line
   handoff:
     - file: src/MailKit.Pooling/MailKit/MailKitSmtpClientAdapter.cs
       gist: one line
   ```

4. Score: `python score_findings.py --actual <findings.yaml> [--baseline <previous score.json>]`
5. Repeat for **N >= 3 independent runs** and report per-run scores plus the
   spread; a single run is noise, not a signal.
6. Remove the worktree after scoring.

## Drift Alarm Rules

The scorer exits non-zero (alarm) when any of:

- a `major`-or-above expected finding is missed in a run
- a calibration rule fails:
  - F-002: an actionable remediation asserts the unverified
    `SmtpClient.DisposeAsync` API surface (must be `needs_confirmation` or
    absent — the API does not exist in MailKit 4.16.0)
  - F-003: the `SendAsync(object)` design assumption is deep-dived instead
    of routed to the handoff list
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
- `score_findings.py` — scorer (exit 0 = no drift, 1 = alarm)
- `baseline_score.json` — created by the first eval execution (absent until then)

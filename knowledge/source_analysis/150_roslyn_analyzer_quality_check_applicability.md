<!-- xid: A1B243BF7D5D -->
<a id="xid-A1B243BF7D5D"></a>

# Roslyn Analyzer Quality-Check Applicability

This page defines when the Roslyn analyzer pipeline is used as a quality-axis
check, and how that decision is made. The pipeline itself
(`tools/collect_analyzer_sarif.py` -> `tools/sarif_to_locator.py`) is the
collection and normalization engine; this page is the *applicability policy*.

## Principle: content-conditional, not uniform

The Roslyn analyzer check is run **as a function of work content**, not on
every run. Running it uniformly wastes build time on non-C# work and creates a
false sense of coverage. The decision has two layers (applicability model C):

1. **Skill declares it can apply.** A skill that may produce or change C#
   references [CAP-QA-011 Roslyn Analyzer Acceptance](../../capabilities/quality/190_cap_qa_011_roslyn_analyzer_acceptance.md#xid-94C1B7B9920A)
   in its `capability_refs`. A skill that never touches C# does not.
2. **Per-run content probe decides it does apply.** Within a declaring skill,
   `tools/cs_scope_probe.py` scans the run's target or changed set and reports
   `cs_in_scope`. The check applies only when the probe is positive.

## Content signal

C# is in scope when the run's target tree or changed-file set contains:

- any `*.cs` file, or
- a `*.csproj` / `*.sln` build target

`tools/cs_scope_probe.py --target <path> [--changed-from <ref>] --json`
returns `cs_in_scope` and `roslyn_quality_check` (`applicable` / `na`). Files
under `bin/`, `obj/`, `.git/`, `.vs/`, `node_modules/` are excluded.

## Procedure (quality phase)

1. Run the probe against the run's target or changed set.
2. If `na` (C# not in scope): record the quality check artifact as `na`. It
   does not gate closure.
3. If `applicable`:
   - run `collect_analyzer_sarif.py` -> `sarif_to_locator.py` to produce 131
     candidates; if no buildable target exists, record `baseline_unavailable`
     and continue.
   - the quality reviewer dispositions each candidate (accepted / refuted /
     `needs_confirmation`).
   - set the `check`-kind quality artifact to `done` when dispositioned, or
     `blocked` when a candidate fails acceptance.

## Boundaries

- **Not an auto-fail gate.** Analyzer hits are 131 *candidates*, never
  findings; a hit never fails closure on its own. See
  [External analyzer rule map](132_csharp_error_policy_analyzer_rule_map.md#xid-C7A1E94D3B62).
- **Quality axis only.** This is output acceptance, not progression. The
  deterministic check phase (`fm skill verify`) never runs this.
- **Disposition is judgment, separated from execution.** The quality reviewer
  dispositions candidates in a context separate from the executor.

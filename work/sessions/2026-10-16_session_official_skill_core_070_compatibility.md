# 2026-10-16 Official Skill compatibility release preparation

User authorized Core 0.7.0 implementation and public release. Parent explicitly delegated necessary compatible official package patch publication. Local repository startup is the selected authority. `release_planning_flow` runtime refused draft/deprecated execution; instruction-backed workflow 649d0718-53d2-4cd4-94c5-0ff003cb9518 records this bounded work. Host model eligibility policy was unavailable; inherited model used without a fabricated policy result.

## Scope and public baseline

Live PyPI JSON checked 2026-10-16: brownfield 0.1.5, csharp 0.1.1, batch-regression 0.4.3 all require Core >=0.6.1,<0.7.0. XDDP design returned HTTP 404 and remains source-only.

Prepare brownfield 0.1.6, csharp 0.1.2, batch-regression 0.4.4 with >=0.6.1,<0.8.0 dependency admission. XDDP source-only 0.1.0 updates admission but receives no publication tag. No Skill bodies, protocol ranges or maturity changed. Core remains 0.6.3 in this prerequisite change.

## Verification and review

Parent independently reviewed the 14-file source diff with no blockers: project/manifest versions agree, future 0.8.0 remains excluded, source-only boundary retained. This is source review, not fabricated GitHub reviewer approval. Main has no protection or rulesets at query time; all actual CI gates still required before merge.

`xref fix`: no changes, missing_xid 0, issues 0. `git diff --check`: passed.
Initial full compatibility run exposed a Brownfield test issue: the checker runs repository tests against prior public versions, so its future-admission assertion cannot apply to old 0.1.5. Fixed by checking admission based on installed Skill version; installed current Core must still satisfy its requirement. Failure evidence retained in .tmp/compatibility-preflight; published scope rerun separately.

Exact Core 0.7.0 behavior remains unverified until its later exact-wheel compatibility gate. Public descriptions must not represent this dependency preparation as completed 0.7.0 behavioral certification.

## Publication outcome

PR https://github.com/synthaicode/XRefKit/pull/162 passed all CI and merged at dfe9fbd2b5d704b2149942de33fb6e2254913c16. Three matching package tags were pushed at this merge. PyPI publication workflows succeeded: Brownfield 38884927952, CSharp 38884928144, Batch Regression 38884928197. GitHub bundle workflows 38884927915, 38884928003, 38884928223 succeeded with ZIP and SHA256 assets.

Public PyPI independently confirms Brownfield 0.1.6, CSharp 0.1.2, Batch Regression 0.4.4, all with wheel/sdist and xrefkit>=0.6.1,<0.8.0. Final fresh published-scope validation downloads actual registry wheels, verifies hashes, runs installed regression suites (10+1+6; no skips) and combined installation/resolution against exact built Core 0.6.3: all passed. Source-only XDDP is still 404. Evidence: 2026-10-16_evidence_official_skill_released_compatibility.json.

Dependency-release obligation complete. Core 0.7.0 exact-wheel compatibility verification remains with parent feature release; real legacy-user environment remains unavailable.

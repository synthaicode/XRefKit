# Core 0.7.0 release validation

## Scope and boundaries

The implementation is validated against representative legacy Skills sharing
Python modules and resources. No customer legacy environment was supplied.
Observed baseline output does not approve business expectations. Imported Skills
remain draft; workflow closure is process evidence. Server-side Python execution
is not enabled. Exact upload contents still require human review because secret
screening is heuristic.

## Reviewed source and artifact

- Source correction commit: `30a1a97`.
- Local wheel: `dist/070-reviewed/xrefkit-0.7.0-py3-none-any.whl`.
- SHA256: `d30ef901af4715a6a71bd2064fb849612ed15842c5637f5c66f63338819c1c72`.
- Wheel and sdist build: passed.
- Artifact allowlist, archives, required bootstrap members and credential-pattern
  inspection: passed. Twine metadata check: both artifacts passed.
- Public tag builds may have a different archive hash; publication must verify
  the actual published artifact and installation separately.

## Executed checks

- Corrected local full quality gate: exit 0; 1510 passed, 4 skipped and 108
  subtests passed in 584.60 seconds. Subsequent xref, Skill structure, pack lint,
  tracked-runtime audit and project baseline stages all passed.
- Source commit `30a1a971e7203553b8ee27ef881846d5fedf9834` CI run
  [38887141164](https://github.com/synthaicode/XRefKit/actions/runs/38887141164)
  succeeded: quality/security, build, artifact/malware inspection, clean wheel
  installs on Python 3.11/3.12/3.13, clean sdist install and official compatibility.
- Migration-focused suite before the final identity correction: 48 passed.
- Final repository adoption, real stdio subagent startup and resource suite:
  79 passed in 82.84 seconds.
- Independent identity/adoption regression recheck: 3 passed in 16.80 seconds.
- Independent earlier remediation checks: guidance 10 passed, resources 4 passed.
- Corrected exact-wheel official compatibility: published 17 and candidate 43
  tests passed, zero skips; both combined environments passed. XDDP was explicitly
  confirmed not published. See `2026-10-16_evidence_core_070_reviewed_compatibility.json`.
- Bandit configured medium/high gate: zero medium/high findings (62 low).
- Declared dependency audit: no known vulnerabilities. This is not a claim about
  all packages installed in the developer environment.

## Failed and superseded evidence

The first completed local full run had 4 failed, 1506 passed, 4 skipped and 108
subtests passed in 609.82 seconds. Three failures were stale catalog expectations;
one was an embedded reference returning the package identity rather than the
serving repository identity. All four received targeted successful retests.
Earlier interrupted local runs do not count as passes. Old pre-correction wheel
compatibility results do not qualify the new source for release.

## Pending final gates

Independent baseline quality accepted with verdict `proceed`. Both implementation
and review runtimes passed deterministic verification and closure. Final
evidence-head CI and public installation verification remain pending. No release
completion is claimed here.

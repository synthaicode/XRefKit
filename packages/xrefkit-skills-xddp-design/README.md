# xrefkit-skills-xddp-design

Text-only XRefKit Skill Package for XDDP change design.

This package exposes `package_root()` through the `xrefkit.skill_packages`
entry point group so XRefKit can discover `package_manifest.yaml`.

It does not include executable tools.

## Candidate compatibility

This is a source-only, unpublished candidate at version 0.1.0. Its supported
Python distribution range is `xrefkit>=0.6.1,<0.7.0` with Python >=3.11.
The manifest's `xrefkit_core: ">=2.0.0 <3.0.0"` denotes the Core protocol,
not the version of the Python distribution. Publication is a separate decision.

The Core release gate builds this candidate and exercises its installed entry
point, actual registry/resolver contract inheritance, required Knowledge,
review axes and schema, inline fragments, on-demand branches, and CLI. It also
tests the candidate in combination with all other official candidates.

Run package regressions from outside the repository after installing the built
wheel or sdist with its `test` extra and Core 0.6.1:

```powershell
python -m pip check
python -I -m pytest <absolute-package-tests-path> --import-mode=importlib -o pythonpath=
```

The schema tests validate representative synthetic change-design output and
reject omitted mandatory fields or malformed traceability. They do not execute
an AI or certify business correctness, completeness of evidence, or real project
change-design judgments. The two packaged evaluation cases remain isolated from
their expected/calibration documents; the independent-run evaluation policy is
not claimed as completed by deterministic package tests.

# xrefkit-skills-csharp

Text-only XRefKit Skill Package for C# and .NET analysis.

This package exposes `package_root()` through the `xrefkit.skill_packages`
entry point group so XRefKit can discover `package_manifest.yaml`.

It does not include executable tools.

Compatibility: requires XRefKit >=0.6.1,<0.8.0 and Python >=3.11.
The manifest requirement >=2.0.0 <3.0.0 refers to the Skill Package
core protocol, separately from the Python distribution version.

## 0.1.4

C# review now requires a human-readable `review_report` alongside the existing
structured findings, evidence, unknowns, used XIDs and handoffs. Consumers that
validate or construct results must supply this additional required field.
The entry returned by MCP carries the report instructions directly: explain
operational meaning before finding IDs, tie overall claims to evidence, preserve
observed/possible/unverified boundaries, order defects by supported impact without
regrading severity, and separate design-policy decisions and their owners.

A dedicated report review axis requires independent content checking. Schema
validation checks shape only; it does not certify report quality or guarantee
that a client runs the independent review. The repository's draft
`review_report_composition` Skill is neither adopted nor invoked by this update.
Detector scope and the detection-quality limitations documented below remain.

## 0.1.3

C# review now follows evidence-backed findings with a bounded inventory of
role-equivalent paths. Record each candidate's evidence, duplicate or additional
manifestation, non-match, unverified boundary, and handoff. Representative runtime
tests require controls and do not establish coverage of every similar path.

This procedure update does not promote Skill maturity or certify detection quality.
Three independent reviews of the repository candidate triggered major-miss alarms
in the existing evaluation (match rates 0.200, 0.267, 0.267). There was no previous
score baseline, so neither improvement nor absence of regression was established.
These limitations remain open; distribution and installation checks are separate.

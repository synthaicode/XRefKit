# Public evaluation corpus: csharp_review

This directory contains public synthetic evaluation cases for the published
`csharp_review` Skill. It is evaluation corpus, not runtime Knowledge, and must
not be loaded into an ordinary review context as answer material.

Each case is a fixture target path containing source and project artifacts. The
fixture does not prescribe an output format or tell the Skill which findings to
seek. The expected structured answers and calibration rules are evaluator-side
assets.
The cases evaluate findings beyond Roslyn/compiler diagnostics, evidence and
severity calibration, needs-confirmation behavior, and handoff boundaries for
security, design assumptions, XDDP trace continuity, and report composition.

The corpus is intentionally separate from the Skill's procedure and from the
private held-out drift split under `skills/csharp_review/references/eval/`.

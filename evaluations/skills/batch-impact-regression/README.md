# Public evaluation cases: batch-impact-regression

This directory contains public, synthetic evaluation cases for the published
`batch-impact-regression` Skill.

These files are evaluation corpus, not runtime Knowledge. They must not be
loaded as domain context during an ordinary Skill run. The evaluator must
record the PyPI package version and hash, Skill procedure hash, selected
Knowledge hashes, model snapshot/configuration, and this corpus revision.

Public cases are smoke/regression cases. They do not replace held-out cases
used to detect overfitting or Goodhart effects.

The suite is intentionally multi-case. A single happy-path comparison is not
enough to evaluate this Skill: the cases cover the 15-step workflow, result
classification precedence, safe execution gates, dynamic dispatch unknowns,
traceability, reduced-set selection, and human handoff.

See [coverage.yaml](coverage.yaml) for the case-to-workflow mapping.

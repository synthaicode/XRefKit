# Session Note: csharp_review generalized observation basis

- skill_id: `csharp_review`
- date: 2026-06-23
- scope: generalized review observations only

## Purpose

Record the non-example-specific basis for `csharp_review` rules. This note is
intentionally free of concrete product names, source paths, API names, fixture
class names, and copied code snippets so the Skill remains rule-driven rather
than example-whitelisted.

## General Observations

- Review rules must be expressed as reusable conditions, not as named examples.
- Operational resilience findings should be driven by resource ownership,
  lifecycle, shared scope, volume pressure, blast radius, and diagnosability.
- Required-input integrity findings should apply to both loud failures and
  silent substitutions on mandatory business inputs.
- Eval fixtures may contain source paths and code because they are scorer data,
  but Skill-facing instructions and metadata must not rely on those concrete
  examples for detection.

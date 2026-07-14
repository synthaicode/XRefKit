# Copywriting Trial Authoring Basis

- date: `2026-07-13`
- skill_id: `copywriting`
- promotion: `draft -> trial`
- publication_boundary: `private`

## Observed Need

The first requested operational use is to rename a set of Japanese public
concepts so practitioners recognize their own AI-operation problems, repeat the
names in team conversation, and reach stable canonical pages.

The initial terminology attempt showed a concrete copy problem: technically
accurate Japanese translations did not feel familiar enough to the intended
audience. The user explicitly requested a new pass using the copywriting Skill.

## Load-Readiness Observation

- The Skill body already defines explicit inputs, outputs, work items,
  execution, monitoring, closure, and handoff.
- The metadata already defines execution mode, capability layering, workflow
  protocol, capability, tuning, responsibility, operating contract,
  constraints, lifecycle, and a fixed copywriting-knowledge slot.
- Draft validation passed.
- Trial validation identified one missing requirement: a durable
  `observation_refs` entry.
- Runtime correctly refused to open the Skill while its maturity remained
  `draft`.

## Promotion Decision

Promote the Skill to `trial` for the first real brief. This authoring basis is
the bootstrap observation required for load readiness; it is not evidence of
stable quality or broad effectiveness.

Keep the Skill private. Do not publish it or claim `stable` maturity from this
observation.

## First-Run Boundary

- audience: Japanese practitioners experiencing AI-operation problems
- asset: reusable Japanese concept names and headline candidates
- desired action: recognize the problem, reuse the term, and follow the term to
  a canonical page
- proof boundary: existing articles, current repository definitions, and
  explicit human feedback
- approval owner: the user
- publication state: proposal only

## Follow-up Rule

After real runs, add or replace observation references only when usage reveals
a reusable boundary, missing input, weak output contract, or accepted
improvement. Routine successful runs do not become maturity evidence by
default.

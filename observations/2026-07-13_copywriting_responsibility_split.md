# Copywriting Responsibility Split Authoring Basis

- date: `2026-07-13`
- status: `authoring_basis`
- concept: `evidence-grounded copywriting`
- affected_skill_ids:
  - `copywriting`
  - `copywriting-compose`
  - `copywriting-review`
  - `copywriting-publish-readiness`
  - `copywriting-experiment`

## Observation

The existing `copywriting` Skill carried concept definition, composition,
review, publication gating, and experiment design in one execution procedure.
This made small drafting and review requests inherit publication and
measurement requirements that did not belong to their task mode.

## Authorized Change

The user authorized retaining `copywriting` as the canonical concept and
semantic entry while splitting execution into compose, review,
publish-readiness, and experiment responsibilities.

## Required Continuity

- Keep one shared audience, offer, desired-action, evidence, claim-ledger, and
  next-surface vocabulary.
- Preserve claim IDs and evidence references across Skill handoffs.
- Keep draft continuation separate from publication blocking.
- Do not require variants or measurement unless the active task needs them.
- Do not let an AI grant legal approval.

## Maturity Boundary

This observation supports initial `trial` use of the split Skills. It does not
establish audience acceptance, specialist approval, or stable maturity. Real
runs must replace or supplement this authoring basis when they reveal stronger
operating evidence.

## Runtime Resolver Observation

The current local `skill run` validates Meta `knowledge_slots` but does not
materialize them as Domain Knowledge Inputs. Repository-native execution must
therefore resolve the bound XIDs explicitly with `xref show`; MCP execution
uses the XID document resolver. The Skill family does not duplicate physical
knowledge paths as a workaround.

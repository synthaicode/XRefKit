<!-- xid: 9E4A71C6B2D8 -->
<a id="xid-9E4A71C6B2D8"></a>

# Draft-to-Trial Evolution Loop

Use this loop when the user has a rough note, prompt, legacy Skill, or partial
`meta.md` and wants to grow it into a reusable XRefKit Skill.

## Input Classification

Separate the input into four inventories before editing:

- confirmed purpose and trigger phrases
- proposed procedure and boundaries
- factual/domain material that belongs in `knowledge/`
- unknowns, missing evidence, and decisions requiring human confirmation

Do not treat a rough note as an approved Skill boundary.

## Evolution Stages

1. **Intake**: ask only the questions needed to identify the target, users,
   inputs, outputs, handoff, publication boundary, and expected evidence.
2. **Scaffold**: create or update one `SKILL.v1.md` definition and only the
   required `references/` or `flows/` files. Maintain `meta.md` plus `SKILL.md`
   only for an explicit legacy split target. Default a new Skill to private
   placement.
3. **Gap diagnosis**: run definition validation and report missing definition
   fields, unresolved runtime-binding derivation at the run boundary, mixed
   procedure/facts, unclear scope, missing handoff, missing observation, and
   unsupported maturity claims.
4. **Human revision**: present the gaps and proposed changes before applying
   changes that alter the Skill boundary, publication scope, or authority.
5. **Trial promotion**: propose `trial` only when the Skill is runnable, has
   explicit criteria and closure, and has external observation evidence. Keep
   runtime binding and governance status outside the SkillDefinition and keep
   unresolved gaps visible.
6. **Observation loop**: run the Skill on a bounded real task, record outputs,
   evidence, unknowns, and quality feedback, then return to diagnosis.

## Minimum Scaffold

The first scaffold should make the following explicit even when values remain
open:

- `skill_id`, purpose, trigger, and boundary
- input and output artifacts
- reusable method and Skill-specific stop/handoff conditions; common Workflow
  phases remain initialization-owned
- applicability, exclusions, criteria, Knowledge needs, and Skill-specific
  control deltas; runtime binding field names may be noted but values are not
  stored in the Skill
- maturity basis and unresolved gaps
- knowledge XIDs or a deferred extraction note

## Stop Conditions

Stop and ask for confirmation when the draft would:

- publish under `skills/` without explicit public-release intent
- claim `trial` or higher without runnable evidence
- mix procedure and durable domain facts without a split decision
- silently choose an authority, owner, or external side effect
- replace an existing Skill instead of updating or versioning it explicitly

## Output

Return the created or updated paths, the maturity decision, the gap list, the
evidence required for the next stage, and the smallest next action. Do not
describe a scaffold as a completed or stable Skill.


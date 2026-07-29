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
2. **Scaffold**: create or update `meta.md`, `SKILL.md`, and only the required
   `references/` or `flows/` files. Default a new Skill to private placement.
3. **Gap diagnosis**: run draft validation and report missing runtime fields,
   mixed procedure/facts, unclear scope, missing handoff, missing observation,
   and unsupported maturity claims.
4. **Human revision**: present the gaps and proposed changes before applying
   changes that alter the Skill boundary, publication scope, or authority.
5. **Trial promotion**: promote to `trial` only when the Skill is runnable,
   has the required executor role, explicit lifecycle and closure, and an
   observation reference. Keep unresolved gaps visible.
6. **Observation loop**: run the Skill on a bounded real task, record outputs,
   evidence, unknowns, and quality feedback, then return to diagnosis.

## Minimum Scaffold

The first scaffold should make the following explicit even when values remain
open:

- `skill_id`, purpose, trigger, and boundary
- input and output artifacts
- startup, planning, execution, monitoring, closure, and handoff
- `capability_layering`, `workflow_protocol`, tuning, and executor role
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


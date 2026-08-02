<!-- xid: 84C920557A2C -->
<a id="xid-84C920557A2C"></a>

# Skill Body Template

```md
# Skill: <skill_id>

## Purpose

<one-paragraph purpose>

## Required Knowledge (XID)

- [Reference name](<relative-path-to-docs-or-knowledge>/<path>.md#xid-...)

## Optional References

- [Template or helper](./references/<file>.md)

## Inputs

- <input 1>
- <input 2>

## Outputs

- <output 1>
- <output 2>

## Reporting Contract (共通報告)

Use the shared [Skill Reporting Contract](../../../../docs/core/contracts/081_skill_reporting_contract.md#xid-6B2D9F4A1C73) in the final report. When the request is in Japanese, use the Japanese human-facing form in this order: `結論`, `状態`, `理由` when required, `確認したこと`, `残っている課題`, and `次にすること`. Keep IDs, paths, commands, and status enum values stable. Write the user's equivalent of `なし` when a section is empty.
If the status is `partial`, `blocked`, `escalated`, or `needs-review`, add a
`Reason` / `理由` section immediately after `Status` and state the concrete
conditions that caused the status.
For checklists and matrices, add a `詳細` / `Details` column. Every `fail`,
`unknown`, or `not_checked` result must link to the corresponding stable
finding, open-item, or coverage anchor, such as `[CR-001](#cr-001)`. The
detailed finding heading must use the same ID as its anchor.
When category names are not self-explanatory, add a `説明` / `Description`
column with a URL to the canonical category definition. Keep this link
separate from the result-specific detail anchor.

- reporting_profile: `summary_first` / `gate_verdict` / `checklist_verdict` / `phase_summary` / `artifact_traceability`

## Anti-Forgetting Structure

- explicitly state what later AI runs must not have to reconstruct
- explicitly state where reusable facts live
- explicitly state what must be handed off with evidence

## Startup

- <confirm boundary>
- <confirm required artifacts>
- <load required rules>
- For multi-step or resumable work, record `route`, `goal`, `context`,
- `constraints`, `done_when`, `out_of_scope`, `verification_commands`,
- `stop_conditions`, and `handoff_location` before substantial execution.

## Planning

- <scope decision>
- <target file decision>
- <maturity decision>

## Execution

1. <perform creation/update step>
2. <perform validation step>
- At each meaningful boundary, record the current step, owned boundary,
- expected check, actual result, decisions or blockers, and next step.

## Monitoring and Control

- <Skill-specific evidence, state-transition, or scope-leak condition>
- <stop and escalate condition>
- Stop and re-route when goal, scope, required data, tool result, user
- priority, or verification basis changes; do not hide the change in an
- assumption.
- Do not claim completion from prior summaries or memory; use fresh evidence
- from the current run.

## Closure

- <return outputs and gaps>
- Include modified files, verification command and result, key decisions,
- current priority, context-audit result, blockers, and next action in the
- handoff when the work is resumable.

## Rules

- <must not rule>
- <must not rule>
```

Authoring notes:

- Keep procedure in the Skill.
- Move reusable domain facts to `knowledge/`.
- Replace sample links with real `#xid-...` references before treating the
  Skill as ready.
- Replace the relative-path placeholder so it matches the actual family path of
  the Skill.
- If the Skill loads external context, include the guard.
- If a later AI could forget it, encode it structurally instead of assuming it
  will stay in memory.

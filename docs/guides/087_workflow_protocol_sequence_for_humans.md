<!-- xid: E8B4D2F19A63 -->
<a id="xid-E8B4D2F19A63"></a>

# Workflow Protocol Sequence For Humans

This guide explains how XRefKit's workflow protocol, `xrefkit skill` commands, Skill
execution, deterministic verification, and quality review fit together.

## Short Version

`xrefkit skill` is the deterministic runtime harness. It does not interpret a
Skill's business procedure and does not judge output quality.

The AI executor interprets the selected `SKILL.md` and performs the actual
work.

`xrefkit skill verify` is deterministic verification of the run log. It checks
whether the workflow progression was recorded correctly. It is not a model
reviewer and it does not inspect output quality.

Quality acceptance is a separate axis. When required, the `quality_reviewer`
role checks output acceptability through `check` artifacts and the quality
phase.

## Main Actors

| Actor | What it does |
|---|---|
| User | Provides the goal, constraints, and human decisions when escalation is needed. |
| Main AI / harness / client | Routes the task, runs `xrefkit skill` commands, manages the run log, and may orchestrate subagents. |
| `xrefkit skill run` | Opens the runtime envelope, validates Skill metadata, resolves `skill_doc`, assigns runtime roles, and creates the run log. |
| Skill executor AI | Reads the returned `skill_doc` and performs the Skill procedure. |
| `xrefkit skill verify` | Deterministically verifies workflow-progression records and advances the check phase. |
| Quality reviewer | Accepts or blocks output quality when the quality gate is required. |
| `xrefkit skill close` | Applies closure checks and records whether the run can close or must remain blocked or escalated. |

## Full Sequence

```text
1. User gives a goal.

2. Main AI / harness routes the goal to a Skill.
   - Routing is semantic and therefore non-deterministic.
   - The selected Skill is identified by meta identity and applicability.

3. Main AI / harness opens the runtime envelope.
   python -m xrefkit skill run --meta <skill-meta> --task "<task>" --json

4. `xrefkit skill run` creates the run log.
   - validates metadata at runtime-open level
   - confirms the referenced SKILL.md exists
   - returns run_log and skill_doc
   - assigns executor, checker, quality_reviewer, and handoff_owner roles
   - records workflow_protocol, os_contract, worklist, artifact sections,
     unknown/risk handling, quality gate, closure gate, and handoff section

5. Skill executor AI opens only the returned skill_doc.
   - The executor interprets SKILL.md.
   - The executor performs the actual work.
   - If model_tier is light or standard, execution may be delegated to a
     tier-matched executor subagent.
   - If model_tier is heavy or unset, execution may remain in the main context.

6. Main AI / harness records concrete work items.
   python -m xrefkit skill workitem --log <run-log> --item WI-001 --text "<work>" --status pending --role "<skill>:executor"

7. Executor completes work items and records status.
   python -m xrefkit skill workitem --log <run-log> --item WI-001 --status done --role "<skill>:executor"

8. Main AI / harness records outputs and evidence.
   python -m xrefkit skill artifact --log <run-log> --artifact OUT-001 --kind output --target "<path>" --item WI-001 --status done --role "<skill>:executor"
   python -m xrefkit skill artifact --log <run-log> --artifact EVD-001 --kind evidence --target "<command-or-source>" --item WI-001 --status done --role "<skill>:executor"

9. Main AI / harness records unknowns, risks, or judgments when they exist.
   python -m xrefkit skill concern --log <run-log> --concern UNK-001 --kind unknown --status resolved --role "<skill>:checker"

10. Main AI / harness advances execution with the assigned executor role.
    python -m xrefkit skill phase --log <run-log> --phase execution --status done --role "<skill>:executor"

11. Main AI / harness calls deterministic verification.
    python -m xrefkit skill verify --log <run-log>

12. xrefkit skill verify reads the run log and advances the check phase.
    - It verifies work item completion.
    - It verifies artifact recording and linkage.
    - It verifies concern resolution or escalation.
    - It verifies role separation and progression records.
    - It does not open output artifact contents.
    - It does not judge output quality.

13. If verification is blocked, executor or harness fixes the recorded gap.
    - missing work item
    - missing artifact
    - open concern
    - wrong role
    - incomplete phase state
    Then `xrefkit skill verify` is called again.

14. If the quality gate is required, quality acceptance is recorded separately.
    - standard and heavy tiers require the quality gate.
    - light and unset tiers may close without it.
    - acceptance criteria are recorded as `check` artifacts.
    - the assigned `quality_reviewer` role advances the quality phase.

15. Main AI / harness records handoff with the assigned handoff owner role.
    python -m xrefkit skill phase --log <run-log> --phase handoff --status done --role "<skill>:handoff_owner"

16. Main AI / harness applies closure.
    python -m xrefkit skill close --log <run-log>

17. xrefkit skill close accepts, blocks, or escalates closure.
    - Closure asserts process integrity.
    - Closure does not by itself assert artifact content quality.
```

## Context Separation

```text
Main AI / harness context
  - routes the task
  - runs `xrefkit skill` commands
  - manages the run log
  - may orchestrate executor or quality subagents

Skill executor context
  - reads the returned SKILL.md
  - performs Skill-specific judgment and generation
  - may be a subagent for light / standard Skills
  - may be the main context for heavy / unset Skills

Deterministic checker context
  - is not an AI reasoning context
  - is xrefkit skill verify reading the run log
  - cannot be argued into passing by executor context

Quality reviewer context
  - evaluates output acceptability when required
  - is separate from workflow-progression verification
```

## When Verify Runs

`xrefkit skill verify` is not periodic. It is called at workflow milestones:

- after concrete work items, artifacts, concerns, and phase records are present
- before `xrefkit skill close`
- again after any blocked verification gap is repaired

The AI / harness calls it explicitly because closure requires the check phase to
be advanced by deterministic workflow-progression verification.

## Work Items And Quality

Concrete work items answer: what work must be done?

`check` artifacts and the quality gate answer: what must be true for the output
to be accepted?

A run may define acceptance checks at planning time, but output acceptance is
performed later by the quality axis when required. The executor does not approve
its own output quality.

## Boundary To Remember

- AI interprets Skill procedures and performs non-deterministic work.
- `xrefkit skill` enforces deterministic runtime progression and closure.
- quality review is separate from deterministic verification.

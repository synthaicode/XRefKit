<!-- xid: E8B4D2F19A63 -->
<a id="xid-E8B4D2F19A63"></a>

# Workflow Protocol Sequence For Humans

This guide explains how XRefKit's workflow protocol, `xrefkit skill` commands,
Skill execution, instruction-backed runs, deterministic verification, and human
quality review fit together.

## Short Version

`xrefkit skill` is the deterministic runtime harness. It does not interpret a
Skill's business procedure or an instruction's business meaning, and it does
not judge output quality. Instructions without a matching Skill can start an
instruction-backed run with `xrefkit workflow run`.

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
| `xrefkit skill run` | Opens the runtime envelope, validates the selected v1 definition or legacy metadata, fixes definition and runtime-binding identity, assigns runtime roles, and creates the run log. |
| MCP `bind_skill_run` | Binds the Skill Run `run_id` to the active MCP session and starts correlated server audit records. |
| Skill executor AI | Reads the returned `skill_doc` and performs the Skill procedure. |
| `xrefkit skill verify` | Deterministically verifies workflow-progression records and advances the check phase. |
| Quality reviewer | Accepts or blocks output quality when the quality gate is required. |
| `xrefkit skill close` | Applies closure checks and records whether the run can close or must remain blocked or escalated. |

## Full Sequence

```text
1. User gives a goal.

2. Main AI / harness routes the goal to a Skill.
   - Routing is semantic and therefore non-deterministic.
   - A v1 Skill is selected from header identity and `applies_when`; a legacy
     split Skill retains its meta identity and applicability path.

3. Main AI / harness opens the runtime envelope.
   For SkillDefinition v1, derive the runtime binding from the instruction:
   python -m xrefkit skill run --definition <SKILL.md> --task "<task>" --capability "<capability>" --tuning "<tuning>" --responsibility "<responsibility>" --execution-mode <mode> --json
   For a legacy split Skill, use its compatibility metadata:
   python -m xrefkit skill run --meta <skill-meta> --task "<task>" --json

4. `xrefkit skill run` creates the run log.
   - validates the selected one-document definition or legacy metadata
   - records `skill_definition_v1` for v1 runs and preserves the established
     legacy run-log shape for `--meta` runs; old logs are not rewritten
   - for v1, records definition path, XID, raw bytes SHA-256, maturity evidence,
     and the instruction-derived runtime binding
   - confirms the exact Skill body exists
   - returns run_log and skill_doc
   - assigns executor, checker, quality_reviewer, and handoff_owner roles
   - records workflow_protocol, os_contract, worklist, artifact sections,
     unknown/risk handling, quality gate, closure gate, and handoff section
   - generates `run_id` for client/MCP correlation

4a. In MCP mode, the harness binds the run before task-specific XID access.
    - call `bind_skill_run(run_id, skill_id, flow_id, root_run_id, parent_run_id, work_item_id, node_id)` when Prompt Flow correlation applies
    - execute its returned `client_record_command` against `run_log`
    - MCP writes search and XID-resolution events to `work/mcp/xid_audit.jsonl`
    - the client log and server audit now share `run_id`, `mcp_session_id`, and
      `repository_fingerprint`
    - MCP records resolution as `xid.resolved`; the client records actual
      context injection separately with `xrefkit skill knowledge --action load`

4b. The harness records routing and non-MCP Knowledge observations when they
    are available.
    ```powershell
    python -m xrefkit skill routing --log <run-log> --selected-skill <skill> --candidate <skill> --reason "<reason>"
    python -m xrefkit skill knowledge --log <run-log> --action apply --xid <XID> --target <artifact-or-judgment>
    python -m xrefkit skill feedback --log <run-log> --kind human --status accepted --note "<feedback>"
    ```

5. Skill executor AI opens only the returned skill_doc.
   - The executor verifies and interprets the exact selected SKILL.md.
   - For v1, the parent evaluates `knowledge_needs.required_when`, specifies
     active need IDs, and resolves only the needed Knowledge bodies by XID.
   - The executor performs the actual work.
   - Execution placement follows the active routing policy and captured
     `execution_mode`. Legacy `model_tier` remains a quality-gate compatibility
     field; it does not become SkillDefinition v1 metadata.

6. Main AI / harness records concrete work items.
   python -m xrefkit skill workitem --log <run-log> --item WI-001 --text "<work>" --completion-criterion "<observable condition>" --status pending --role "<skill>:executor"

7. Executor completes work items and records status.
   python -m xrefkit skill workitem --log <run-log> --item WI-001 --completion-criterion "<observable condition>" --status done --role "<skill>:executor"

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
    - legacy standard and heavy tiers require the quality gate.
    - legacy light and unset tiers may close without it.
    - v1 output acceptance remains a separate human or review responsibility;
      parser success, maturity, and procedural closure do not accept quality.
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

## Optional Subsequent-Request Evaluation

After closure, control is unconditionally returned to the human. The next
request may be ordinary continuation without an evaluation record. If the
human wants to connect that request to the preceding run, they may record an
optional, human-confirmed evaluation:

```powershell
xrefkit skill evaluate --log <run-log> `
  --decision accepted_with_conditions `
  --classification continuation `
  --next-handling continue_next_step `
  --purpose-fit "Purpose still fits" `
  --verified "OUT-001; EVD-001" `
  --uncertainty "none"
```

The AI can propose a classification, but only the human-provided
`--classification` is authoritative. Use scoped findings for multi-target
runs. Include `--context-ref` and record `--comparability gap` when evidence,
criteria, or configuration are not versioned or snapshotted. This records
workflow evaluation, not private model reasoning, and never blocks handoff or
low-risk continuation.

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
  - receives the definition identity and instruction-derived runtime binding
  - runs in the context selected by execution_mode and the active routing policy

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

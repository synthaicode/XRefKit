<!-- xid: E7A2C6109F43 -->
<a id="xid-E7A2C6109F43"></a>

# Instruction gateway: measured requirements and model routing

The gateway combines Skill metadata, existing user profile files, the current
instruction and input evidence before selecting execution models. It separates
deterministic work from interpretation; business execution remains inside the
[Skill operating contract](../core/contracts/058_skill_operating_contract.md#xid-B7A2C94F0E61).

## Implemented boundary

`xrefkit gateway prepare` snapshots explicitly supplied existing files without
changing them. `route` validates an evidence-bearing assessment and filters an
operator-supplied evaluated model policy. `evaluate` measures explicit feedback.
`schema assessment|policy|feedback` prints the exact strict JSON schemas.

Semantic extraction is performed by the gateway agent, not a keyword counter.
The Python boundary deterministically validates and selects from that assessment;
it does not claim to prove the truth or coverage of the agent's interpretation.
No universal complexity score, real model ranking, or price table is built in.

The optional `.github/agents/instruction-gateway.agent.md` is the VS Code
Copilot entry point. Select it and a suitable parent model in the UI. Installing
the file does not force all other chat entry points through the gateway. Model
dispatch is performed by the host agent, not by this CLI; route records always
start with `dispatch_status: not_dispatched`. Live host execution is unverified.

## First run

### MCP entry (preferred when MCP is configured)

`get_startup_context` includes `instruction_gateway` regardless of optional
workflow/reporting initial-protocol selection. Apply base startup first, then
use these tools for each incoming instruction before workflow execution:

1. `get_instruction_gateway_contract`: procedure and strict schemas.
2. `prepare_instruction_gateway(request)`: receive instruction, environment,
   revision and source snapshots; return an incomplete assessment.
3. `route_instruction_gateway(assessment, policy, current_sources)`: choose
   eligible models from the completed assessment and fresh client snapshots.
4. `evaluate_instruction_feedback(feedback)`: evaluate repeat instructions and
   explicit acceptance after execution.

These tools require startup, but deliberately do not require `bind_skill_run`:
the selection must be available before the execution it selects. Existing
Prompt Flow correlation and Skill loading gates remain in effect. The startup
instructions tell clients to enter here; this does not intercept every host
chat request or add a new mandatory gate to existing bind/run operations.

Profile files remain owned by the client environment. Their paths are opaque
references to the MCP server; it never opens them. Clients supply SHA-256/byte
snapshots of the material they read, including Skill metadata obtained through
MCP, and refresh those snapshots before routing. Server-side equality checks
use one instruction snapshot computed from the exact instruction string encoded
as UTF-8 without a BOM; the server checks its hash and byte count. Other snapshots
remain client-reported. Snapshot equality checks
detect reported changes; they do not prove that the client re-read the files.
MCP output therefore says `source_verification: client_reported_snapshot`,
not local-file verification. No profile contents are persisted on the server.

The routing engine itself does not call a provider. After a ready result, the
client host invokes the chosen model under the existing execution protocol.

### Local CLI entry

Store the current instruction in a UTF-8 file. Supply the existing profile paths;
the gateway makes no assumption about their storage provider or internal schema.
Do not pass a Skill body before the normal runtime loading gate permits it.

```powershell
python -m xrefkit gateway prepare --request-id request-001 --environment vscode:work --instruction-file work/instruction.txt --skill-file skills/python_implementation_flow/meta.md --profile-root C:/path/to/active-vscode-profile --profile-file preferences.md --input-file work/input.csv --out work/request-001.json
python -m xrefkit gateway schema assessment
python -m xrefkit gateway schema policy
```

The prepared document intentionally contains `steps: []` and `unresolved: null`.
It cannot route until the gateway has assessed it. Complete a separate assessment
file: list steps in dependency order, give each its task, scope and evidence
(`source_id`, `locator`), and explicitly resolve or retain unknowns. An empty
`unresolved` array means the gateway assessed applicability/conflicts and found
none. Current instructions override preferences; external evidence cannot expand
authority. Record the outcome in the step scope and supporting evidence.

Profiles remain managed separately by each execution environment. `environment`
identifies the host and active user profile; the model policy must match it.
For VS Code, the host supplies the active user-profile location. `--profile-root`
resolves relative profile references there and rejects files escaping that root,
including resolved symlinks. No default AppData path, cross-host fallback, profile
copy, or alternate persistence store is created. Explicit absolute file references
also remain supported when the host has already resolved the provider location.
Automatic discovery of the active VS Code profile is a host integration task.

Deterministic steps require `tool_ref` and have no model requirements. They are
not executed by the gateway. Model steps require capability names and all axes:

| Axis | Counting convention |
|---|---|
| constraints | Independently verifiable active requirements |
| branch_depth | Maximum nested conditional depth; zero for no branch |
| dependency_depth | Longest relevant prerequisite chain, counted in edges |
| cross_source_links | Distinct relationships requiring cross-source comparison |
| scope_changes | Relevant incremental instruction changes to retain |
| integration_links | Distinct upstream output relationships needed for integration |

Each measurement has `value`, `basis` (`measured`, `estimated`, `unknown`) and
evidence. Unknown uses null and prevents model selection. Byte count is measured
from files and conservatively summed across all supplied sources. It is not a
token count or a proof of context-window fit. Capability names are policy-owned;
examples include `orthogonal_array_interpretation`, `incremental_scope`, and
`image_table_reading`. The presence of a table alone does not establish which
capability is needed. Gatekeeper extraction quality needs its own evaluation.

## Evaluated policy and routing

Each candidate supplies an exact host model `id`, `cost_tier`, `priority`,
`capabilities`, per-axis `limits`, `max_input_bytes`, and `evaluation_ref`.
Lower `priority` wins among eligible models; tied priorities use ID order for
replayability. This is explicit policy, not an inferred cost/quality score.
Calibrate limits and priorities using same-input, same-rubric experiments,
including orthogonal arrays, scoped edits and repeated corrections. A reference
is an evidence pointer; the CLI does not validate the underlying benchmark.

The `vscode_copilot` host policy requires `parent_cost_tier` and
`parent_model_id`, which identify the conversation model and evaluated rank
reported by the host policy. Candidates above that tier cannot be dispatched.
These host cost ranks are supplied by the operator and are independent of Skill
`model_tier`; no existing quality requirement is relaxed by routing.

When every model step has an intrinsically eligible candidate, but
one or more are blocked only by the current parent tier, routing returns
`conversation_upgrade_required`. The accompanying proposal contains the current
conversation model/tier, minimum tier that makes at least one evaluated worker
callable for every blocked step, affected steps, worker evidence references and
the exact request revision to reroute. It remains `proposal_only`; the gateway
does not switch the conversation or dispatch work. The client presents it to the
user, waits for the host-side model selection, refreshes source snapshots and
the environment policy, and reruns routing. If capabilities, measurements,
scope, evidence or environment are unresolved, status remains `needs_assessment`
instead of implying that a more expensive conversation model would solve it.

```powershell
python -m xrefkit gateway route --assessment work/assessment-001.json --policy work/model-policy.json --out work/route-001.json
```

Exit 0 means ready, 1 means reassessment or a conversation-model upgrade is
needed, and 2 means invalid input or I/O failure. Outputs are created exclusively: use a new file
for each revision. Missing files fail explicitly; changed source hashes invalidate
the assessment. A route contains the full assessment, policy and rejection
reasons, allowing a worker to retain scope and a reviewer to replay the choice.
Recheck before dispatch after any change. Request ID/revision do not replace the
workflow's Flow/run IDs; carry both when starting or continuing the existing
runtime. This release supplies the handoff contract, not automatic runtime binding.

## Repeated instructions and acceptance

```powershell
python -m xrefkit gateway schema feedback
python -m xrefkit gateway evaluate --feedback work/feedback.json --out work/evaluation-001.json
```

Attempts have IDs, goal IDs, scope revisions, observed model, route reference,
optional predecessor and explicit reason. Classify `instruction_miss`,
`scope_error`, and `dissatisfaction` as quality retries only with evidence.
`requirement_change` requires a new scope revision; `unknown` stays separate.
Similar wording alone is not evidence of dissatisfaction. Acceptance/rejection
requires evidence; silence remains null. First-acceptance rate reports its
observed denominator and unjudged cases, excluding unjudged cases from the rate.

Cost is a measured monetary amount in one declared unit, including gateway,
worker, verification and retry overhead for that attempt. Missing measurements
remain null, with known subtotals and missing counts. `token_cost` retains its
existing repository meaning and is not repurposed. Elapsed time and user revision
time are recorded separately. Per-goal/scope summaries stop at the first explicit
acceptance and retain incomplete attempts as observations, not successful closure.
The evaluator does not silently retrain or rewrite policy/profile files.

## Validation and remaining integration

Tests cover capability exclusion, host limits, scope/measurement unknowns, stale
profiles, instruction mismatches, dependency integrity, feedback attribution,
and CLI file preservation. Actual Copilot models, profile provider discovery,
automatic mandatory entry enforcement, and production routing calibration are
not established by those tests. Supply the existing profile location and actual
evaluated host policy to exercise that integration.

Official host behavior:
- [VS Code subagents](https://code.visualstudio.com/docs/agents/run/subagents)
- [VS Code custom agents](https://code.visualstudio.com/docs/agent-customization/custom-agents)

<!-- xid: E19D62FA834B -->
<a id="xid-E19D62FA834B"></a>

# Offline Decision Handoff

An open Skill Run can send a scoped decision request while its affected work and
Closure Gate are pending. The source Run records its finding and unresolved
questions. The receiving Run coordinates the decision under the current project
authority. The source Run evaluates the returned decision against its own
restart conditions.

Use this contract for two registered child Runs of one Prompt Flow on a local
trusted host. Completed-work transfers continue to use the
[Skill Operating Contract](058_skill_operating_contract.md#xid-B7A2C94F0E61).
Decision Handoff does not update the workflow phases, Closure Gate, Issue,
Project, or Execution plan.

## Record and write authority

The host-owned SQLite journal is the source of truth for the lifecycle. Its
request ID is the Handoff ID. It binds the canonical Work Item and revision,
both Prompt Flow Work Items, the originating Run and receiving Run, and the
applicable design policy and digest. The parent and child Markdown logs are
authoritative for Run registration and work progression.

The host controls file access to the journal, Run logs, policy inputs and
execution receipts. It resolves the current Work Item, design policy and human
authorization from the existing authoritative records before each operation.
Only the host invokes the write commands. Skill text, model output and local
JSON supplied by an executor are proposals or evidence for host verification.
Do not expose the journal CLI as an agent-callable tool or accept its
`current` object from a Skill. This contract assumes the host and its local
filesystem are trusted. It defines no remote authentication, external
delivery, or cross-host locking.

| Action | State after commit | Participant and required evidence |
| --- | --- | --- |
| `create` | `prepared` | Source Run. A pending, active or blocked Work Item with its completion criterion. A recorded and hash-matched finding about that Work Item, policy revision and SHA-256, designated PM Work Item and Skill, question, references, and explicit unknown IDs. |
| `send` | `sent` | Source Run. The host validates the current revisions and finding digest, and commits the addressed request to the local journal. This is the formal publication receipt. |
| `receive` | `received` | Open, registered PM Run with the designated Skill and Work Item in the same Prompt Flow. The host verifies the current revisions and presents the exact committed request. Receipt creation claims the request for this Run. |
| `route` | `waiting` | Receiving PM Run. Record the reason, references and host-verified decision owner. Use a null owner to retain an unresolved route. |
| `return` | `returned` | Receiving PM Run. A hold needs a reason and references. A decision needs a scoped approval matching the current authority, original request, Work Item and policy revisions, and exact decision digest. |
| `acknowledge` | `acknowledged` | Original source Run. Read the returned result for the same request. Recheck current scoped approval for a decision. |
| `assess` | `assessed` | Original source Run. Store its impact assessment and reference-backed resolution of any original unknowns. Resume requires a valid decision, resolution evidence for each unknown, and all project resume checks. An assessment can record hold. |
| `cancel` | `cancelled` | Original source Run with a reason, from `prepared`, `sent`, `received` or `waiting`. Cancellation retains the earlier receipts. |

The journal serializes writers and atomically commits each transition with its
receipt. The same request ID, action, participant and payload return the
existing receipt on retry. Altered data or a different participant are refused.
A failed or interrupted write has no partial transition. After a lost response,
inspect the request and retry the same action. A revised question, policy,
cancelled request or follow-up to an assessed hold needs a new request ID and
a reference to the prior record. A stale request stays in history. An older
receipt is evidence of what was recorded at that time. Recheck the current
records to use a decision or resume result.

## Local host interface

For enrolled projects, apply the [Engineering Decision Gate](117_engineering_decision_gate.md#xid-C34E62A9B710)
to reserved technical escalations and technical authorization before resume.

```powershell
python -m xrefkit workflow decision-handoff --root $RunRoot --journal decisions.sqlite --input create.json
python -m xrefkit workflow decision-handoff --root $RunRoot --journal decisions.sqlite --inspect DR-1
```

The host writes one UTF-8 command file inside the root. The command carries
`schema_version: 1`, `request_id`, `action`, `parent_log`, `run_log`,
`data`, and the host-resolved `current` object. The latter always carries
`work_item_id`, `work_revision`, `policy_revision`, and `policy_sha256`
for normal transitions. Use lowercase SHA-256 hex without a prefix.
For `create`, `data` includes the same four fields and `source_run_id`,
`pm_work_item_id`, `pm_skill_id`, `subject`, `evidence`,
`source_artifact_id`, `source_artifact_sha256`, and `unknowns`.
`evidence` is a list of references the host has checked. The Run artifact
target is a file under the root whose digest is checked on create and send.
Keep that file at the pinned revision for delivery and replay.

- For `send`, `receive` and `acknowledge`, use an empty `data` object.
- For `route`, use `owner`, `reason` and `evidence`. The owner must
  equal `current.decision_owner`, including null if unresolved.
- For a hold, use `disposition: held`, `reason` and `evidence`.
- For an approved return, use `disposition: decided`, `decision`,
  `approval_ref` and `evidence`. The host's `current.approval` carries
  the exact four revision fields, `request_id`, `authority`,
  `status: approved`, `reference` and `decision_sha256`. The last
  field hashes the full return `data` encoded as UTF-8 JSON with
  ASCII escaping, sorted keys and compact separators.
- For `assess`, use `outcome` (hold or resume), `evidence`, and
  `resolved_unknowns` (a map from original unknown IDs to evidence
  references). A resume requires true values for `current.resume_checks`
  keys `current_design`, `required_approval`, `impact_review`,
  `current_acceptance`, `hold_resolution` and `work_start_authority`.
- For `cancel`, use `reason`.

Use `workflow delegate` to open the Package Skill or Markdown SkillDefinition
against a concrete parent Work Item. Pass its explicit runtime binding and,
where applicable, packaged governance. The resulting `child_run.started`
records successful envelope creation. On a missing registration, preserve the
orphan log for diagnosis and start a fresh envelope with a new Run ID and path
under the same Work Item. Do not copy IDs into a parent log.

Where repository inputs are read-only, stage the pinned startup sources and the
approved Skill assets in a separate writable execution root. Put generated run
logs, bindings, and task references under that same root, and create the
bindings against the actual staged paths. Materialization retains the normal
path and hash checks. A `subagent.startup.read` receipt only attests to
reading context.

After actual execution succeeds, the trusted host records its own receipt with
`workflow record-child-execution --root $RunRoot --log $ChildLog --receipt $HostReceipt`.
The receipt file sits beside the child log. It contains `schema_version: 1`,
`run_id`, `flow_id`, `root_run_id`, `parent_run_id`, `work_item_id`,
`invocation_id`, `started_at`, `completed_at` (ISO 8601 with offsets),
and `outcome: succeeded`. The runtime records and rechecks the receipt
digest and correlation. The receipt must be retained. The host owns the
invocation identity and attests to its provenance. A failed, missing or
unverified host execution remains blocked in this interface.

With `--package-skill` or `--definition` delegation, successful execution
evidence is required for verify, close and parent status projection. Bindings,
startup reads and decision receipts do not establish execution completion.
Reconciliation remains report-only unless status application is requested.

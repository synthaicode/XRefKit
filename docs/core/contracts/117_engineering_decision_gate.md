<!-- xid: C34E62A9B710 -->
<a id="xid-C34E62A9B710"></a>

# Engineering Decision Gate

A draft Run can investigate, create candidate artifacts and pass procedural
closure. Manufacturing, test design and retry in an enrolled project require
a current decision for the exact candidate. The decision has its own lifecycle
and uses the existing [decision handoff](116_decision_handoff.md#xid-E19D62FA834B)
for requests to a decision authority.

## Project enrollment

Place a UTF-8 `engineering-decision-policy.json` at the project root. Protect
that policy, the SQLite journal `.xrefkit-engineering-decisions.sqlite`, Run
logs and evidence from untrusted writers. The trusted host assigns the action
for each dispatch using the authoritative Work Item, and consumes the exact
candidate in the receipt. Enrolled `skill run`, `workflow run` and
`workflow delegate` require a registered Work Item and an explicit action.
Use `draft` for proposal-only Runs, including PM and orchestration.

Policy schema version 1 has these objects.

| Object | Required values |
| --- | --- |
| `work_items[work_item_id]` | `revision`, `actions` from `draft`, `manufacturing`, `test_design`, `retry`, nonempty `required_xids`, `required_checks`, `reviewers`, and `approver` (designated authority or null where review suffices). |
| `catalog[xid]` | `kind` (`global` or `project`), `revision`, `path` under the root, and raw-file lowercase `sha256`. The file must declare the exact XID. The host selects references using XRefKit search and resolution. |
| `reviews[decision_id]` | `reviewer`, `prepared_sha256`, `proposal_sha256`, and `verdict` of `pass`. The reviewer must be configured for the item and distinct from the proposer. |
| `approvals[decision_id]` | `approver`, `prepared_sha256`, `proposal_sha256`, and `status` of `approved` when the Work Item requires an approver. |

The host authenticates reviewer and approver records. The gate verifies
reference content, scope, version, evidence digests and those attestations.
The reviewer evaluates technical validity, exceptions, priority and conflicting
evidence. Existing project start authorization still applies. Draft producers
must not write trusted policy, reviews or approvals.

## Lifecycle

1. Open the registered draft Run. Identify a decision when a change affects
   a contract, an invariant, an expected result or safe retry.
2. Run `workflow engineering-decision --root ROOT --input COMMAND.json` with
   `action: prepare`, `decision_id`, `work_item_id`, relative `run_log`,
   `proposer` and `question`. The receipt contains the exact reference
   contents and unresolved XIDs. Supply them to the draft executor before
   selecting or evaluating a design.
3. Submit `action: review`, the same `decision_id` and a `proposal`. The
   gate checks the evidence structure and returns both digests. The reviewer
   and any designated approver examine the exact candidate, applicability
   and verification before the host registers their attestations.
4. Submit `action: finalize` with the same proposal. The finalized result is
   immutable. An identical retry returns the recorded result. A changed
   context or proposal requires a new ID. Revoke the old review or approval
   when superseding an authorization within the same Work Item revision.
5. The host calls
   `workflow engineering-decision --root ROOT --use WORK_ITEM ACTION DECISION`
   at dispatch or opens a managed Run with `--work-item-id`,
   `--engineering-action`, `--engineering-decision-id` and
   `--engineering-candidate`. Binding, subagent startup, verification and
   closure recheck a protected Run's decision. A managed
   `workflow recovery --status confirmed` requires a current `retry`
   decision and records its exact candidate.

A proposal has `classification`, `rationale`, `basis` keyed by XID
(`applicability` of `applies`, `not_applicable` or `unresolved`, plus
`reason`), `verification` keyed by configured check ID (each with `status`
of `pass`, `fail` or `unknown`, plus `path` and raw-file `sha256`),
`candidate` (the artifact `path` and raw-file `sha256`, or null), and
`actions`. `DETERMINED` requires the complete resolved XID basis from both
catalog types, resolved applicability, all required passing checks, an exact
candidate and matching current review and approval. `CONDITIONAL`,
`BLOCKED` and `ESCALATION_REQUIRED` record the reason and confer no protected
action. Unaffected work can have its own scoped decision.

## Handoff and pilot boundary

A formal authority escalation carries the finalized `ESCALATION_REQUIRED`
decision ID in the Brownfield finding and in the Handoff request. Run, Work
Item and revision must match. The existing PM Handoff may record hold.
After a decision return, managed resume requires a `DETERMINED`
manufacturing decision from technical re-evaluation. Include the original
`handoff_request_id` in that decision's prepare command and put the new
engineering decision ID in the assessment.

This pilot covers Core's enrolled local Run and decision-consumption routes.
The host must protect the root, trusted inputs, and action routing and use
the returned artifact for real dispatch. External shells, file publishers,
and Project automation have their own execution boundary.

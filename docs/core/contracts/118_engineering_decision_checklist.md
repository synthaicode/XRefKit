<!-- xid: 9C6E7A2B105D -->
<a id="xid-9C6E7A2B105D"></a>

# Engineering Decision Checklist

This contract extends the [Engineering Decision Gate](117_engineering_decision_gate.md#xid-C34E62A9B710).
In a managed project's `engineering-decision-policy.json`, enable
`"discovery": true` and `"checklist": true`. The second flag requires the
first. Projects can continue using their existing proposal shapes without
this opt-in. On changing the flag, keep old decisions available for audit
and prepare a new decision before relying on it for protected actions.

## Selection and reference identity

The Core wheel carries `xrefkit/resources/engineering-decision-checklist.json`.
`resolve` selects the ten common GDC questions and the relevant category
questions. API integration, state management, concurrency,
architecture change and security select their corresponding groups.
Yes or unknown external effects, state and concurrency add their respective
groups. A state decision also adds concurrency screening even if the
concurrency flag is no. Recovery uses the common checks and adds groups from
the structured effects. The host supplies the decision context.

Core selects related approved XIDs by the resolved candidate references and
their areas. GDC-04 links all required applicable XIDs. A question with
unmapped knowledge areas records a `knowledge_gaps` list. Brownfield can
cite other resolved XIDs and relevant evidence for a check. The reviewed
technical decision must account for any gap before relying on a guarantee.
The checklist defines the questions and the XID provides the engineering basis.

The selected definitions are stored as `reference_set.checklist` in the
resolution. Each contains `check_id`, `category`, `question`,
`applicability`, `related_xids`, `required`, `revision` and
`knowledge_gaps`. The reference-set SHA-256 commits to this selection as
well as to the resolved principles and their recorded applicability.

## Proposal

For enrolled decisions the existing proposal contains a `checklist` object.
Its `decision_id`, `reference_set_sha256` and `candidate` must match the
current decision and the exact candidate in the proposal. `results` maps
check IDs to records with these properties.

| Field | Expected content |
| --- | --- |
| `revision` | Selected check revision. |
| `applicability` | `applies` or `not_applicable` according to the selected condition. |
| `result` | `PASS`, `FAIL`, `NOT_APPLICABLE` or `UNKNOWN`. |
| `reason`, `evaluator` | Nonempty explanation and identity. |
| `references` | Object mapping resolved XIDs to their recorded revisions. GDC-04 PASS must include all required applicable XIDs. |
| `evidence` | Array of `{path, sha256}` for evidence within the Run root. PASS and FAIL require at least one pinned file. |
| `unresolved` | Array of open items. UNKNOWN requires at least one. PASS and NOT_APPLICABLE require an empty array. |

Only CON-02 through CON-05 allow NOT_APPLICABLE when structured concurrency
is explicitly no and the decision is outside the concurrency category.
CON-01 still records evidence for screening. Unknown concurrency requires
evaluation. A reason is mandatory for each NOT_APPLICABLE.

`review`, `finalize` and protected use require all selected required
results for DETERMINED. Missing results, FAIL and UNKNOWN block it.
The non-authorizing states can retain incomplete evaluations.
Independent review and approval still attest to the same proposal
digest, which includes the checklist. An evaluator cannot review their own
record. Core revalidates definition, current XIDs, candidate and evidence
when the decision is consumed. Changed inputs require a new decision and
new review under the existing supersession procedure.

## Roles and Handoff

Brownfield evaluates the selected questions, verifies evidence, and
addresses shortcomings. Independent reviewers assess the technical claims.
Core validates structure, identity, completion and pinned evidence.
PM reads `checklist_pending` through `workflow engineering-decision
--inspect DECISION` and carries unresolved items and schedule impact through
the existing Handoff. PM sends technical reassessment to Brownfield.

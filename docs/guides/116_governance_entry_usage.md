<!-- xid: 3B7A9D12E6F4 -->
<a id="xid-3B7A9D12E6F4"></a>

# Governance Entry Usage Guide

This bounded repository trial implements the entries proposed by the
[shared update design](../designs/113_shared_asset_update_gate_design.md#xid-A93D741E6BC2)
and [retrospective design](../designs/114_correction_retrospective_design.md#xid-D4F83A17B9C6).
Use the [shared management contract](../core/contracts/115_shared_asset_update_gate.md#xid-0F8E2A6C94D1)
on this route. Other update routes and raw edits are not intercepted.

## Public Analysis Methods

The user explicitly chose public common Skills:
[shared asset update gate](../../skills/os/shared_asset_update_gate/SKILL.v1.md#xid-6EA2C74D91B8)
and [correction retrospective analyst](../../skills/os/correction_retrospective_analyst/SKILL.v1.md#xid-4BC7E192A6D0).
Their native v1 source-adoption records identify source hashes and explicit
human authority without fabricated legacy migration receipts or runtime defaults.
All runtime binding inputs remain instruction-derived and explicitly required;
source registration does not promote maturity. Open their existing Skill-run
runtime only when the host can satisfy eligibility and clean checkpoint
boundaries. Package consumers need the repository rule sources and environment;
this guide does not promise provider portability beyond the repository trial.

## Prepare and Dispatch

```powershell
python -m xrefkit governance --root . prepare --request work/request.json --out work/packet.json
```

The request supplies `kind`, parent `log`, an existing execution-binding
`binding_request`, unique material paths, and `payload`. Parent work item must
remain open with a completion criterion. A packet freezes the run context and
all selected material hashes. Filesystem paths are canonical portable relative
paths inside the root, not aliases or escapes.

For `asset_update`, the payload contains `candidate`, `target`, `rules`,
`specialist_evidence` and `checks`. The candidate is separate from the target.
The trial accepts one Markdown target under `skills/`, `skills_private/` or
`knowledge/`, including new-target absence or the existing target hash. It
does not perform companion-file synchronization. Rules include this shared
contract and the source-storage contract at their repository paths, and core
check IDs cannot be omitted. Snapshot candidate, rules, specialist/QA evidence
and reference sources needed by the analyst. Record applicable checks and
supported specialist nonapplicability; neither the main agent nor deterministic
code establishes semantic acceptance.

For `correction_retrospective`, the payload contains `scope`, `reason`,
`consent`, `task_basis` and `correction_evidence`. `task_basis` is immutable inline
task/requirement text, not an unresolved live pointer. Consent is
`{intent: execute_retrospective, scope: <same scope>, evidence: <material path>}`;
freeze the explicit human instruction and bounded correction/material evidence.
It is a scoped instruction record, not a parser that interprets acknowledgments.

The Python host API `dispatch(root, packet, host_dispatch, host_verifier)` calls
an injected **trusted host adapter**. That adapter actually starts the isolated
public gate or correction retrospective analyst, passing only this packet and selected
materials through the existing Skill/run/subagent startup mechanisms. The
package does not itself create host agents. The child run must correlate with
the packet's parent/root/workitem, record its output artifact and pass closure.

The analyst saves the structured result body **without** an `output` pointer.
The host adds `{path, sha256}` as `output`, checks actual dispatch provenance,
and signs an execution event binding packet, child log, Skill and result hashes.
The CLI provides no host-signing or human-approval-issuing command. A plan or an
unsigned caller assertion is insufficient. Operator-controlled adapters and
keys are trust boundaries, not protection against a compromised host.

## Validate and Apply

```powershell
python -m xrefkit governance --root . validate --request work/packet.json --receipt work/host-receipt.json --out work/validated.json
python -m xrefkit governance --root . apply --request work/packet.json --receipt work/host-receipt.json --approval-file work/human-assertion.txt --out work/reflection.json
```

The configured host verifier checks execution signatures; a **separate**
outside-AI human verifier checks `action=apply_governed_asset`, packet, target,
result identity and expiry. The CLI's operator environment provides
`XREFKIT_GOVERNANCE_HOST_SECRET` and `XREFKIT_GOVERNANCE_HUMAN_SECRET`, which
must differ. Do not place keys in packets, analyst inputs or checked-in files.
Production host adapters should keep authority outside analyst access.

Application rejects failed/unknown findings, unresolved unknowns, missing
execution evidence, changed input/result bytes and stale target baselines.
New files use exclusive creation; existing files use a per-resolved-target
cooperating-writer lock, baseline comparison and atomic replacement. This is
not a filesystem-wide transaction or exclusion of unrelated writers: external
writes and hostile symlink changes require host controls. The reflected target
hash is returned; maturity, catalog/adoption metadata, specialist postchecks,
Git publication and runtime activation remain separate existing actions.

The CLI reserves its evidence output before applying. If application succeeds
but saving that evidence fails, it returns exit code `3` and reports that the
canonical application completed, with the reflected target hash. Inspect the
target and recover the evidence before retrying; this is not an unapplied rejection.

The selected CLI/API application endpoint is integrated. MCP edit-overlay
activation, Knowledge contribution adoption, generators, direct filesystem
edits, alternate checkouts and bulk companion files are **not** integrated by
this trial. Existing HMAC contribution approvals and atomic transports remain
unchanged. Do not report this route as coverage of those paths.

## Retrospective Suggestions

`suggest` takes a request containing non-canonical `state_path`, bounded
`scope`, concrete `reason`, evidence paths and optionally an explicit response
(`declined`, `deferred`, `unanswered`, `accepted`, `human_request`). It persists
scope/reason/evidence identity, suppressing the same suggestion across new
request IDs. New substantive evidence can justify another suggestion; an
explicit later human request can override suppression. The host records the
actual human response; the API does not infer it from silence or "OK".
The host must establish whether new evidence is substantive: a changed hash
records identity and does not itself prove a meaningful correction.

After scoped consent, prepare and dispatch the retrospective packet as above.
Its result is proposals and explicit unknowns for human review. It cannot enter
`apply`, adopt rules or save personal memory. Optional analysis does not block
ordinary task closure. Main-agent attention reduction and semantic improvement
require observations; structure tests alone do not establish those effects.

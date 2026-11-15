<!-- xid: 6E7D3B90A152 -->
<a id="xid-6E7D3B90A152"></a>

# Quality Issue Management Console

The Python dashboard is the XRefKit Management Console. Quality Issues are
reports about explicit human corrections to AI outputs. They support improvement
of XRefKit's shared rules; they do not replace Brownfield or Project Management
business outputs.

## Start the console

Run against the repository that owns the MCP Contribution Return inbox:

```powershell
python -m xrefkit dashboard serve --root C:\path\to\repository
```

The default address is `http://127.0.0.1:8765/`. The four areas share one server:

| Area | Use |
| --- | --- |
| Quality Issues | Filter reports, inspect observed facts, correction and output references, hypotheses, unknowns, related reports, and human decisions. |
| Governance | Inspect the existing Contribution Return inbox and review bundles; review or adopt through the existing signed approval operations. |
| Runtime Diagnostics | Existing Plans, Overview, Prompt Flows, Recovery, Attention, Closure, Evidence, Handoff, XID Usage, Analysis, Missing Information, and Decision Trace panels. |
| Quality Evaluation | Open recorded Skill quality gates and evaluation artifacts; compare Issue output references and human verification evidence. |

The console starts in Quality Issues. Existing `?panel=...` and `?run_id=...`
links continue to open Runtime Diagnostics. `/api/runs` and `dashboard data`
retain their payload contracts. Run logs are optional diagnostic evidence;
normal Issue review uses the report and its history. Management evidence routes
and all writes require a local connection. Existing runtime diagnostics remain
available on an explicitly configured non-loopback interface; they have no new
reader authentication, so use that configuration only on a trusted network.

## Client correction hook

The host must deliver the correction event to its Client AI. MCP cannot read or
watch the host's conversation. No universal host hook is installed by XRefKit.
The supported Python adapter is `xrefkit.quality_issues.submit_quality_feedback`:

```python
from xrefkit.quality_issues import submit_quality_feedback

# Invoke from a host-owned correction callback after local sanitization.
result = await submit_quality_feedback(
    call_tool=mcp_session.call_tool,
    report=report,
    observation=skill_observation,
    contribution_id=stable_report_uuid,
    title="Missing agreed heading",
    summary="A previously agreed output heading was omitted.",
    policy=host_transfer_policy,
    destination="configured-improvement-server",
    knowledge_versions=actually_used_knowledge_versions,
)
```

`call_tool` accepts the MCP tool name and argument dictionary. The adapter calls
the existing `submit_contribution_return` with `kind="skill_observation"` and
optional `quality_issue` metadata. Existing clients without that metadata keep
their contracts. The destination must be the server actually selected by the
host transport; a free-form destination string alone is not transport identity.

The client first uses the existing Feedback evaluation semantics. Quality
retries require explicit correction evidence and retain the evaluated scope
revision. Requirement changes have a new scope revision. Unclassified repetition
remains `unknown`; attempt count alone cannot establish a Quality Issue. A single
explicit quality correction may be reported.

The report carries sanitized summaries and content hashes for the human
correction and original/corrected output, a diff summary, observed facts,
separate cause hypotheses, unknowns, impact, and an optional similarity key.
`output_after=null` is supported when the revised output is not available.
Use `get_quality_issue_contract` for the exact schema. Source Skill hash and
maturity, Run ID, MCP session, and used Knowledge hashes are checked or bound by
the existing contribution path. `unassessed` stays explicit for a Quality Issue
about an unassessed Skill; it does not promote that Skill.

### Permission and privacy

Configure a `TransferPolicy` in the host's existing configuration:

```json
{
  "destination": "configured-improvement-server",
  "allowed": true,
  "data_classification": "sanitized_nonconfidential",
  "authorization_reference": "approved host improvement-report policy"
}
```

This is a configuration example, not authorization for any real destination.
Confidential, personal, unknown, denied, or destination-mismatched transfers
fail locally before the transport call. Do not send raw prompts, raw business
outputs, credentials, or personal information. The host owns semantic redaction;
the bounded schema and sensitive-pattern rejection are additional checks, not a
complete data-loss prevention classifier. The MCP intake validates again.

Use the existing startup, Skill selection, Run binding, and contribution-enabled
server profile. A reader profile does not gain write authority through this
feature. Stable report UUIDs make unchanged retries in the same bound MCP
session idempotent; the existing contribution payload also binds the MCP session.
Reconnecting under a different session with the same report UUID conflicts;
use a distinct report identity and retain the relationship instead of changing
the old report. Changing the payload under the same UUID is refused. Distinct reports remain distinct even when their
similarity keys match. A similarity key is a client suggestion, not a confirmed
root cause or formal duplicate judgment.

Catch adapter/transport errors in the host, record their evidence, and continue
the user's current work where its existing workflow permits. Do not interpret a
submission failure as success or repeatedly ask the user to authorize each
report when the configured policy already authorizes it. Real host event wiring
and organizational redaction policy must be supplied and verified by the host.

## Human decisions

The states are `reported`, `triaged`, `under_review`,
`approved_for_improvement`, `resolved`, `closed`, `rejected`, and `deferred`.
Every new report starts `reported`. There is no invented mandatory linear
sequence; humans may revisit a decision. `resolved` requires verification
evidence. Related Issue IDs can be recorded without deleting individual reports.

Decisions use the existing `HumanApprovalVerifier` trust boundary. For the
bundled HMAC verifier, configure `XREFKIT_CONTRIBUTION_APPROVAL_SECRET` in the
trusted server environment with the same secret used by its existing trusted
approval issuer. The secret must contain at least 32 UTF-8 bytes. Never put it
in a report, browser field, URL, or MCP argument. Without a verifier the console
is read-only. Configuring the secret does not provide a human identity provider.

1. Select an Issue and fill in state, reviewer, reason, verification references,
   and related Issue IDs.
2. Choose **Prepare approval request**. The console returns exact unsigned
   claims for the trusted issuer; it does not grant approval.
3. Have the existing trusted, human-authenticated issuer verify the human
   choice and sign those claims with a unique `assertion_id` and expiration.
4. Paste the signed assertion and choose **Record decision**.

The existing `issue_hmac_approval_assertion` helper is available only to the
trusted issuer or tests. Do not expose an endpoint that calls it for arbitrary
AI-supplied claims. A reviewer name or a CSRF token is not proof of human approval.

Assertions bind the decision, report payload hash, and expected Issue revision.
The server rejects stale revisions, altered claims, and conflicting decision-ID
replays. Signed history is append-only. Failed submissions retain form values;
reload an Issue and obtain a new assertion when another reviewer has changed it.
The browser write endpoint additionally requires a local connection, matching
Host/Origin, and its CSRF token. Serve human decision operations on loopback.

## Governance and source links

An Issue's **Approved for Improvement** state is a decision to investigate or
improve. It never changes canonical files, Skill maturity, Knowledge identity,
or Contribution adoption status. Continue through existing Skill Authoring,
Knowledge Ontology Management, shared update gates, quality checks, and human
approval for the proposed source change.

The Governance area opens the existing contribution review bundle, including
its immutable submitted files and verified review/adoption events. Select
**Review or adopt**, fill in the human reviewer and reason, and select the
separate action:

- **Review contribution**: accept or reject; acceptance fixes the approved
  repository path. Prepare the exact approval request, obtain an assertion from
  the trusted issuer, and record the review. An accepted review returns its
  one-time adoption token; retain it securely. Replays do not return that token.
- **Adopt accepted contribution**: supply the accepted review's adoption token
  and reason. For governed Knowledge updates, supply the existing governance
  packet and host receipt in the advanced evidence fields. The trusted host
  verifier uses `XREFKIT_GOVERNANCE_HOST_SECRET`, which must differ from the
  human approval secret. Missing required governance evidence fails closed.

These forms delegate to the existing catalog `review_contribution_return` and
`adopt_contribution_return` operations with their ownership, XID, target,
collision, governance, signature, and token checks intact. Signed contribution
events record browser actions; the console does not invent an MCP session or
claim that a browser action originated in the MCP audit log. Their assertions
and adoption tokens remain separate from Issue decision assertions. See the
[Contribution Return adoption guide](095_mcp_contribution_return_adoption.md#xid-0E5C778EB6AF).

Skill and Knowledge links resolve the current catalog document, explicitly
marked as current. Compare its content hash with the report's pinned hash before
using it as historical evidence. Missing or ambiguous catalog entries are
unavailable; the console does not invent an old revision or follow client-supplied
filesystem paths. Original output bodies remain client-local.

## Compatibility and UI consolidation

The Next.js project remains available because actual deployments and users of
that surface have not been established. Its existing `/api/runs` adapter calls
`xrefkit dashboard data`; that API remains compatible. Python provides the
existing run search/filter/refresh/selection, evidence and missing-information
views and the additional Flow, Recovery, Plans, and Decision Trace views.
Retirement requires confirming real usage and migration with owners, not merely
finding no code references. No Next.js files or business features are removed.

## Verification boundaries

Synthetic tests cover browser rendering, existing runtime panels, HTTP listing
and filtering, missing records, signed decisions/history/replay/stale revisions,
CSRF/origin rejection, read-only configuration, and untrusted text rendering.
Core tests separately cover correction classification, confidentiality refusal,
Contribution compatibility, and MCP Client-to-Server submission. These tests do
not establish actual conversation access, production identity-provider wiring,
or production redaction effectiveness.

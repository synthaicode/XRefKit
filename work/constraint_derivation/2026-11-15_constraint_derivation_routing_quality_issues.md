# Quality Issue constraint routing and primary derivation

## Scope and evidence

Input: user attachment `6778eb0f-4d1e-4e87-abd5-13d6165a3269/貼り付けたテキスト.txt`, sections 1–13. The user authorized implementation, tests, and a PR, preserving existing approval boundaries. On 2026-11-15 the user explicitly authorized latest-main local governance rather than the outdated connected MCP provider. Baseline: `bfa3a9fd`.

Route: design-downward. Primary Skills: `design_constraint_derivation`, `ui_constraint_derivation`, `logic_constraint_derivation`, `integration_constraint_derivation`, `auth_constraint_derivation`. Their runtime envelopes were opened before methods. Index executor is the isolated `constraints` subagent. Secondary `commonality_derivation` follows these completed primary lists. No queue, schedule, batch, C# code, or DDL/code mismatch is specified, so async/code/cross derivation is not presently applicable. Re-route if implementation introduces those structures. Integration-scenario upward review is appropriate after persistence/order behavior exists.

Required knowledge read: framework `81A6C4E2B190`, guard `7A2F4C8D1601`, working area `111D282CA0EA`, design `2D14F88A6C01`, UI `31C5A06B7E22`, logic `4E5B8923C912`, integration `6F0D7C1A2E44`, auth `8B14D9E70326`.

Guard: user attachment supplies the authorized goal; inspected repository code supplies implementation evidence. No lower-layer input was accepted as changed authority.

Existing source evidence: `xrefkit/mcp/contribution_returns.py` supplies bounded observation metadata, source/binding checks, file hashing and contribution inbox. `xrefkit/mcp/contribution_adoption.py` supplies `HumanApprovalVerifier` and signed human assertions. `xrefkit/gateway.py` supplies explicit feedback reasons, scope-revision checks, retry ancestry and unknown retention. `xrefkit/dashboard.py` provides the current read-only HTTP/UI surface. Next.js README and API route delegate to Python dashboard data.

## Data and operations (DCD)

| ID | Structural basis | Confirmed requirement / implementation constraint | Basis |
| --- | --- | --- | --- |
| DCD-01 | Existing observation plus quality fields | Add optional quality metadata without changing existing contribution kinds or old observation acceptance. Keep existing store; no new DB. | §§5,6,9 |
| DCD-02 | Report ID and repeated delivery | Identical ID and payload are idempotent; conflicting reuse must not overwrite historical evidence. Reuse existing contribution hash/ID semantics. | §§6,10 and current store |
| DCD-03 | Multiple clients report similar problems | Preserve individual reports and identities; related issue references are separate from transport deduplication. | §7 |
| DCD-04 | Nullable versions, unknown cause | Unknown and absence must not become a guessed revision, cause, acceptance or empty successful result. Require known bound source hashes where existing observation contract requires them. | §§5,6,10 |
| DCD-05 | List/detail operations | Zero results are an empty list; one/many retain distinct IDs; missing detail is an explicit unavailable result. Invalid IDs/oversize metadata fail before persistence using existing validators. | §8 and current store |

Design decisions within requested implementation scope: keep immutable intake in the contribution record; store append-only issue decisions alongside the same record, using existing locking/atomic writing and verifier. Default status is reported. Server receipt timestamp and client occurrence timestamp have separate meanings; use timezone-aware values. Do not delete an earlier report to merge similarity.

## UI (UCD)

| ID | Structural basis | Confirmed requirement / implementation constraint | Basis |
| --- | --- | --- | --- |
| UCD-01 | Four console areas | One Python console with Quality Issues, Governance, Runtime Diagnostics, Quality Evaluation; preserve current diagnostics payload and screens. | §8 |
| UCD-02 | Lists/filter/detail | Render zero-result and unavailable-target states explicitly; show issue observations, suspected causes, unknowns and human history separately. Escape untrusted displayed text. | §§6–8 |
| UCD-03 | Human judgment submit | Server validates all decisions and evidence; failed validation preserves current state. Repeated click must not duplicate a decision; stale page must not overwrite intervening history. | §§7,10 |
| UCD-04 | Existing UI removal | Keep Next.js until required features and actual usage are verified; API compatibility comparison alone is insufficient proof of zero users. | §8 |

Design decisions: list ordering and filter arrangement are implementation choices; document them. Use explicit submit controls rather than automatic selection changes. Protect writes against cross-origin requests and stale state. Expose links to existing governance artifacts without presenting Issue approval as adoption.

## Logic and state (LCD)

| ID | Structural basis | Confirmed requirement / implementation constraint | Basis |
| --- | --- | --- | --- |
| LCD-01 | Feedback reason branches | Initial/requirement-change/unknown alone do not establish a quality issue. Quality reasons require explicit correction evidence and retain scope revision. | §§4,5 and existing Feedback |
| LCD-02 | Retry ancestry | Repetition counts apply to linked corrections of the same goal/scope; raw utterance count is not evidence. Explicit incorrect output may qualify without repeated attempts. | §4 |
| LCD-03 | State set | Support reported, triaged, under review, approved for improvement, resolved, closed, rejected and deferred, using repository enum conventions. | §7 |
| LCD-04 | Formal improvement | Issue state changes never authorize canonical Skill/Knowledge updates or contribution adoption. Resolution requires recorded improvement/verification evidence. | §§6,7,9 |
| LCD-05 | Concurrent decisions | Preserve all accepted decisions; reject stale revision rather than silently losing a decision. Same decision ID cannot mean two different decisions. | §§6,7,10 |

State/action matrix axes (more than eight combinations): current issue revision, requested status, authenticated human assertion, decision ID, resolution evidence. AI intake can only establish reported. Human decisions use explicit status and evidence. Invalid enum, stale revision, mismatched/reused decision ID, missing human assertion, and resolved without evidence are rejection branches. User did not prescribe mandatory linear progression or forbid reopening: do not invent a business rule requiring every intermediate status. A human-directed status change with append-only history is a bounded design option; document it as implementation behavior, not a pre-existing rule.

| Current state / identity | Action and conditions | Resulting state / history | Trace |
| --- | --- | --- | --- |
| No existing report | Valid authorized AI intake with a new report ID | `reported`; one immutable report, no human decision or adoption | DCD-01/02, LCD-03/04 |
| Any valid current state | New human decision for a valid non-`resolved` target; valid assertion, current revision, new decision ID and decision evidence | Requested target; append one human decision, preserve prior history; no mandatory intermediate transition or canonical adoption | LCD-03/04/05, AACD-01/02 |
| Any valid current state | New human decision for `resolved`; all preceding validity conditions plus improvement/verification evidence | `resolved`; append evidence-bound human decision; no canonical adoption | LCD-04/05 |
| Any valid current state | Request `resolved` without improvement/verification evidence | Reject; current state and history unchanged | LCD-04 |
| Any valid current state | New decision targets a stale revision | Reject; current state and intervening history unchanged | LCD-05 |
| Any valid current state; decision ID already recorded | Exact repeated decision and valid verification of the original decision identity/content | Return the existing decision receipt; do not replay its transition or append another event, including if later decisions changed current state | DCD-02, LCD-05, UCD-03 |
| Any valid current state; decision ID already recorded | Same decision ID with different content | Reject conflict; original decision, current state and history unchanged | DCD-02, LCD-05 |
| Any valid current state | Undefined target state, malformed decision, or missing/expired/mismatched human assertion | Reject; state/history unchanged; reviewer name alone grants no authority | LCD-03/05, AACD-01/02/03 |

The exact-repeat row is receipt retrieval, not authorization for a new transition. Multiple invalid conditions do not require a newly invented business precedence: every invalid new decision must leave state/history unchanged. This table restates the preservation boundaries above and does not approve a new lifecycle policy.

## Integration (ICD)

| ID | Structural basis | Confirmed requirement / implementation constraint | Basis |
| --- | --- | --- | --- |
| ICD-01 | Client evaluation to server submission | Reuse feedback evaluation and contribution transport; client owns observation/classification and submission. Server cannot observe arbitrary host conversation. | §5 |
| ICD-02 | Permission boundary before send | Client must check configured destination and permitted data before network submission; server validates again. Raw prompts/business diffs cannot be silently sent as evidence. | §§5,6 |
| ICD-03 | Submission failure | Surface submission outcome to caller without treating it as business-work failure or acceptance; no new background worker/queue. | §§3,5,9 |
| ICD-04 | Live host integration | Deterministic callback/helper integration tests establish API behavior, not automatic invocation by every host. Real host trigger remains a separate verification item. | §5 |

| Delivery case | Required observable result |
| --- | --- |
| First valid submission | One immutable reported receipt |
| Retry after failure before persistence | Same ID may create one receipt |
| Retry after success/response loss, same payload | Existing receipt, no extra report |
| Same ID, changed payload | Conflict, original unchanged |
| Different client/report IDs, similar issue | Both reports retained, relationship may be recorded |
| Denied destination/sensitive data | Client does not send; server rejects if directly submitted |

No retry timing or queue guarantee is invented. Use explicit caller retry with stable ID and existing transport semantics.

## Authorization (AACD)

| ID | Structural basis | Confirmed requirement / implementation constraint | Basis |
| --- | --- | --- | --- |
| AACD-01 | AI reporter vs human reviewer | Client AI submission does not confer human decision rights. A reviewer name or boolean from an AI request is insufficient authority. | §§6,7,9 |
| AACD-02 | Existing human verifier | Reuse trusted assertion verification, binding to issue payload/revision and decision content; never expose issuer secret in MCP or UI response. | Existing HumanApprovalVerifier and §9 |
| AACD-03 | Dashboard gains write capability | Validate authorization on direct POST as well as UI; reject expired/mismatched assertions, wrong origin, stale revision and malformed body. | §§7,9 |
| AACD-04 | Data classification | Preserve bounded safe references and sanitized summaries. Generic secret pattern matching is defense in depth, not proof that arbitrary prose contains no PII or business secrets. | §6 |

| Actor/condition | Intake | Issue decision | Canonical adoption |
| --- | --- | --- | --- |
| Bound client, permitted sanitized evidence | Allowed under existing transport policy | Denied without trusted human assertion | Existing separate gates only |
| Bound client, sensitive/denied destination | Denied | No added rights | No added rights |
| Human, valid decision-bound assertion | No special intake bypass | Allowed with validation/history | Existing separate gates only |
| Human label only, missing/expired/mismatched assertion | No special intake bypass | Denied | Denied by existing separate gates |

## Open items and handoff

No new business requirement is adopted by this derivation. The supplied request already authorizes the above preservation boundaries and scoped implementation choices. Implementation owner must verify actual transport/profile configuration and trusted human assertion integration rather than assert unobserved deployment behavior.

未確定 verification limits: live host automatic trigger support; actual Next.js deployments/use; production identity-provider integration. These do not justify deleting Next.js or claiming universal automatic conversation observation. Keep them visible in PR and final report. If a new account/tenant system, execution queue, autonomous adoption, or business transition policy becomes necessary, stop and return that expanded decision to the user.

Next owner: implementation executor, then independent quality reviewer. Required checks are the user's twelve test groups, including negative direct API authority checks, unchanged canonical files after intake/decision, and existing dashboard/contribution regression suites. Primary output-content review remains outstanding until independently reviewed; runtime record verification is not quality acceptance.

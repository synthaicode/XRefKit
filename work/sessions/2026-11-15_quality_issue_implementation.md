# Quality Issue implementation evidence

## 2026-11-15: Bounded implementation

### Event

- Implemented the user attachment sections 4–7 and 10 using optional `quality_issue` metadata on existing `skill_observation` Contribution Returns.
- Added client `prepare_quality_issue` / `submit_quality_feedback` callbacks, retaining existing Feedback evaluation and requiring configured destination authorization and sanitized nonconfidential data before network calls.
- Added immutable signed human decision events under each existing Contribution record, existing process locks and `HumanApprovalVerifier`, revision checks and assertion binding to evidence. No Knowledge, Skill or adoption mutation is performed.
- Added MCP contract/list/detail/decision tools on the existing admin profile; intake remains the existing Contribution submission tool and its audit event.
- Current `python_review` source maturity was observed as `unassessed` during the real MCP integration test. Quality observations preserve this value explicitly; legacy observations and maturity proposals retain their prior validation.
- Console implementation and parity documentation are owned by the separate console executor; this record covers backend/client/MCP.

### Decision

- User authorized latest-main local governance instead of the older connected MCP provider.
- Reuse the existing inbox and adoption boundaries. Candidate similarity groups retain individual reports and are not formal duplicate judgments.
- Preserve the existing session-bound Contribution idempotency contract: same ID and exact payload replays, changed payload conflicts; a new MCP session is a changed binding.
- Client source bodies remain local. Transferred evidence is sanitized summaries and hashes. Secret scanning is defense in depth, not proof of absence of personal or business information.

### Human Stated Reason

- User requested existing functionality reuse, no new database or execution system, and preservation of human approval authority.

### Verification

- `python -m pytest tests/test_quality_issues.py tests/test_contribution_returns.py -q`: 66 passed in 46.29 seconds, before the final optional package selector addition.
- `python -m pytest tests/test_quality_issues.py -q`: 21 passed in 19.20 seconds after optional package selector addition and strict decision-list handling.
- Real MCP stdio test uses an isolated copied content root and synthetic feedback, performs startup/Skill selection/Run binding, client callback submission, replay, listing, signed human decision and detail/history retrieval.
- Tests cover first correction, repeated correction, requirement change versus quality feedback, retained unknown, identifiers, pre-network permission/data denial, sensitive fields, idempotency, concurrent intake, individual client reports, signed human decisions, tampering, stale revisions, resolution evidence, old observations and inert canonical content.
- No configured Python linter or type checker is declared in `pyproject.toml`; syntax compile completed for changed backend modules.

### Deferred

- Independent source review, broader regression, packaging verification, PR and run closure are handed to the parent coordinator.

### Open

- A live host-specific conversation callback is not installed or verified. The integration verifies an explicit host callback over real MCP, not autonomous conversation monitoring.
- Human approval assertions require the existing separately trusted issuer; the console does not mint its own authority.
- Production deployment usage, PII classification accuracy, and live host conversation visibility remain unverified.

## 2026-11-15: Independent review feedback QI-R02

### Event

- Reviewer identified malformed decision scalar/list input being normalized by shared text helpers.
- Added explicit string checks for decision identity, status, reviewer and evidence, string checks on array elements, and None-only optional array defaults. Invalid booleans, numbers, objects and strings used as arrays are rejected before forming an approval claim.
- Added simultaneous signed human decision coverage: one append succeeds, the competing stale revision fails; replaying an older receipt after a later decision does not roll back state.
- Added an admin-only follow-up hint to `evaluate_instruction_feedback` for explicit quality feedback. It requires client common-rule assessment and configured transfer permission, and never auto-submits. Reader profile and requirement-change-only evaluations keep the previous response without the hint.

### Verification

- `python -m pytest tests/test_quality_issues.py -q`: 56 passed in 23.54 seconds after strict-type and concurrent-decision fixes.
- `python -m pytest tests/test_quality_issues.py tests/test_gateway_mcp.py -q`: 61 passed in 27.62 seconds, including admin hint and reader-profile absence over real MCP.

### Handoff

- QI-R02 fix and deterministic tests returned to the independent reviewer; implementation does not close the review finding.

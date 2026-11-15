# Quality Issue Python review

Review context: `/root/review`, independent of implementation and console producers. Base: `bfa3a9fd`. Runtime: `b136fc50-8e73-4bcb-be58-e63c040f39e3`. Source scope: `xrefkit/quality_issues.py`, the changed Contribution Return and MCP server code, Python dashboard additions, their new tests, and the string-only Management Console help-label change in `operations_cli.py`. Product files were not edited by this reviewer.

## Verdict

`needs-review`: no unresolved implementation-local code finding remains after corrections and independent rechecks. Production deployment capacity, identity-provider integration, host-trigger wiring, and Next.js real-use evidence remain unverified, and parent-owned full regression/package verification is separate. This is a review-routing verdict for human/deployment follow-up, not a release or adoption approval; it does not prevent preparing the requested reviewable PR.

## Baseline and detector evidence

- Repository CI configures pytest, XID/Skill/Pack checks, runtime-log audit, project baseline check, Bandit, dependency audit, and package build/install validation. No separate configured Python type checker or formatter was identified in `pyproject.toml` or the Core quality workflow.
- Independent focused run: `python -m pytest tests/test_quality_issues.py tests/test_quality_issue_dashboard.py -q --tb=short`: 30 passed in 26.85 seconds before finding corrections, then 65 passed in 27.37 seconds after corrections (`2026-11-15_quality_issue_review_tests.txt`).
- Final changed decision/Governance subset: 46 passed, 24 deselected in 9.25 seconds (`2026-11-15_quality_issue_review_recheck.txt`). This rechecks strict malformed input, missing-target HTTP response, concurrent signed decisions, old-receipt replay without rollback, and separate Contribution review/adoption.
- Inspected parent Bandit result `work/sessions/2026-11-15_quality_issue_bandit.json`: empty results and errors for the configured threshold. This is scanner evidence, not proof of security.
- Final Governance source review confirms that browser review/adoption calls the existing XRefCatalog functions with existing ownership, target, verifier, token and governance receipt checks. New management-evidence GET routes require loopback/allowed Host. The console does not issue its own signed assertions.
- Parent owns full-core and package regression evidence; those results are not assumed from focused tests.
- Required review source set loaded: Python spec `A9B7C6D5E4F1`, common source criteria `5F21C8A41001`, custom framework criteria `5F21C8A41002` / `A9B7C6D5E4F2`, feedback rules `7A2F4C8D1901`, review gate `7A2F4C8D1801`, and all ten active axis topics plus overload source basis `5F21C8A41111`.
- Diff triage: sensitive boundaries (external intake, filesystem persistence, concurrent decisions, human assertions). The completed independent constraint review covers explicit authority/state boundaries. This Python review is not a penetration test or production security certification.

## Category and static-analysis boundary matrix

`pass` below means no unresolved source defect in the stated inspected boundary; it is not a claim that every production condition is verified.

| Category | Disposition | confirmed_by_static_analysis / direct inspection | not_detectable_by_static_analysis | requires_runtime_or_human_evidence |
| --- | --- | --- | --- | --- |
| Static baseline | needs_confirmation for full handoff | Configured checks identified; focused/fix tests passed; configured Bandit report inspected | Full regression/build/dependency outcomes | Parent final check logs |
| Resource efficiency | needs_confirmation | Reuses existing store; per-report quotas; scoped file handles; similarity groups computed once for list | Capacity at production report/history counts | Expected inbox size, concurrency, filesystem quotas; no capacity claim |
| Operational resilience | needs_confirmation | No worker/queue/retry platform; submission errors stay observable; immutable event publish uses existing fsync/atomic-link helper; bounded concurrency tests pass | Process death/storage failure and production contention behavior | Deployment load/failure evidence |
| Synchronization | pass for local tested boundary | Existing process lock surrounds history revision check and append; no detached coroutine; competing signed decisions produce one winner and one stale rejection | Multi-host filesystem lock semantics | Actual deployment filesystem if extended beyond tested local execution |
| Required input integrity | pass-after-fix | Destination/classification gate, signature/revision fields, source hash binding; strict malformed-decision tests pass | Whether host classification and authorization evidence are truthful | Host policy integration |
| Support lifecycle | pass for declared Python range | No dependency changes; requires Python >=3.11 | Compatibility of every allowed optional dependency version | Installed-package smoke and existing CI dependency audit |
| Error paths | pass-after-fix | Intake failure observable; persistence/audit outcomes separate; missing-target HTTP regression passes; no silent source adoption | Real host choice to continue active task | Host integration |
| Time / locale / encoding | pass | Client occurrence timestamp requires timezone; server receipt/decision UTC; UTF-8 persistence and JSON | Actual host timestamp accuracy | Host evidence if occurrence accuracy is disputed |
| State / determinism | pass for tested boundary | Stable report IDs; signed append-only decisions; stale revisions rejected; replay returns old event without undoing later decisions; duplicate/concurrency tests pass | Crash timing across external transport/audit | No exactly-once transport claim |
| Uncertainty / escalation | pass in local schema | Unknown retries retained; unknown transfer denied; cause hypotheses distinct from human judgments; absent corrected output remains null | Human interpretation of summaries | Human assessment of submitted evidence |
| Contract / schema | pass-after-fix | Optional quality metadata preserves existing kind contract; unassessed accepted only in quality extension; strict report/decision input; real MCP tests pass | All historical/third-party producer combinations | Parent legacy full regression/package results |
| Trace / context | pass in inspected paths | Existing source and Run/Session binding reused; per-client reports retained; audit records decision identity without assertion secret | Universal host conversation visibility and audit deployment | Actual host trigger and production audit configuration |
| Custom framework | pass for inspected wiring | Admin-only MCP registration matches Contribution inbox; shared domain mutations and verifier; tests exercise real FastMCP | Production issuer integration and remote deployment trust | Existing trusted issuer adapter; local console boundary documented |

Python lifecycle source: the official [Python version status](https://devguide.python.org/versions/) table lists Python 3.11 and 3.12 in security support, with scheduled end dates October 2027 and October 2028 respectively (checked 2026-11-15). This supports the declared minimum and current CI runtime, not every package combination.

## Findings and recheck ledger

| ID | Severity / ownership | Evidence and violated condition | Remediation / status |
| --- | --- | --- | --- |
| QI-R01 | minor; implementation-local, console owner | `DashboardHandler.do_POST` did not catch the `KeyError` emitted by `_read_manifest` for a valid but nonexistent Issue UUID. Request escaped the controlled HTTP error boundary. | pass-after-fix: KeyError now produces controlled 404; both missing-Issue POST regressions independently passed. |
| QI-R02 | minor; implementation-local, backend owner | `quality_decision_claims` checked `verification_evidence or []` / `related_issue_ids or []`, coercing malformed falsey values to empty arrays; shared `_required_text` stringified nonstring decision evidence. Malformed input became valid-looking signed claim content. | pass-after-fix: None-only defaults, explicit string/list/item checks, assertion string guard; malformed scalar/list and HTTP regressions independently passed. |

Neither finding established a human-approval bypass. Both were returned directly to the owning implementation agents with source evidence and remediation directions.

## Required input detector facts

| Input | Decision gated | Source | Missing / invalid behavior | Default provenance | Disposition |
| --- | --- | --- | --- | --- | --- |
| Destination and data classification | Whether client may transmit | Host-supplied policy | Denied on destination mismatch, false permission, unknown/personal/confidential classification | No permissive default | pass for helper; host configuration still needs integration evidence |
| Correction reason and ancestry | Whether intake is a quality report | Explicit Feedback attempts | Requirement changes/unknown-only repetitions do not qualify | Existing Feedback semantics | pass |
| Human assertion / verifier | Whether state may change | External trusted issuer / configured verifier | Missing/mismatched/expired assertion rejected; absent verifier denies writes | No human authority inferred from name | pass in inspected domain path |
| Expected revision | Whether new history event may append | Human decision request | Wrong type/negative/stale revision rejected | No default | pass in source and concurrent test |
| Verification evidence | Whether resolved is valid | Human decision request | Empty evidence rejected for resolved; malformed types rejected after QI-R02 | None alone means omitted optional array | pass-after-fix |
| Skill / Knowledge source hashes and Run binding | What source the report refers to | Existing catalog and binding | Existing source matching and UUID/hash checks reused | No invented revision | pass; package/source replay limits remain existing constraints |

## Handoff and limits

- Keep Next.js until actual usage/migration is verified. API parity is not evidence of no users.
- The client helper is a host callback adapter, not a universal conversation observer. Real host automatic activation remains unverified.
- Human assertions must come from the configured trusted issuer; the console must not mint authority from a reviewer name. Production issuer integration remains unverified.
- New management evidence and write routes require loopback. Existing Runtime Diagnostics remain readable if explicitly exposed on a non-loopback address; the guide states the trusted-network boundary. No production remote identity integration is claimed.
- Parent owns full regression/package results and final source freeze. Final added Governance operations, label-only CLI change and finding fixes were inspected. Parent reported a synthetic browser signed-triage transition to revision 1 with history; that is parent-observed evidence, not an independently observed browser run by this reviewer.
- Review output still needs its independent report-quality check and parent deterministic verification/closure. Unverified deployment items are retained as handoff concerns, not disguised as verified product behavior.

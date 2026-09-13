# Python review: work-item model routing

- run_id: `fa7866c1-3820-4f7f-b207-d2c9d5bfb524`
- skill_id: `python_review`
- role: `python_review:executor`
- reviewed base: `282716b`
- reviewed implementation: `2c48cbe`
- excluded revision: `826fe5a` (checkpoint-only)
- output mode: `findings-only`
- scope: `xrefkit/gateway.py`, MCP adapters/contracts/registration, gateway tests, and the work-item routing contract/guide changed by `282716b..2c48cbe`

## Report

### Status
`done`

### Reason
The independent executor review and quality re-review are complete. The initial implementation had four `major` findings and one `minor` finding; all five are `pass-after-fix` in the current uncommitted diff. The repository implementation gate is `proceed`. Live-host integration and production-volume evidence remain explicit operational unknowns outside that repository-local gate.

### Result
Commit `2c48cbe` reproduced five defects. The current fix diff closes all five with regression coverage: authorization-required compatibility routes do not dispatch, the stateless state machine enforces one active assignment, removals require retained tombstones, CLI envelopes chain directly, and upgrade previews honor `lowest_cost_eligible`.

### Evidence
- Exact-target detached checkout at commit `2c48cbe`: `python -m pytest` -> `493 passed in 60.51s`.
- Exact-target focused run: `python -m pytest -q tests/test_gateway_work_items.py tests/test_gateway_mcp.py` -> `13 passed in 5.14s`.
- `python -m compileall -q xrefkit` -> exit `0` with no diagnostics.
- `git diff --check 282716b 2c48cbe` -> exit `0` with no diagnostics.
- Five minimal direct reproductions against `2c48cbe` are recorded under the findings below.
- Current uncommitted fix diff: `python -m pytest` -> `498 passed in 62.71s`; focused gateway/MCP suite -> `46 passed in 3.94s`; `compileall`, `git diff --check`, and `xref check` passed (`missing_xid: 0`, `issues: 0`).
- Independent direct after-fix probes returned: authorization `authorization_required` with zero dispatches; repeated route `waiting_active_result` with one active item; removed node retained in `retired_items`; CLI init-to-route return codes `0,0`; mixed-tier preview selected tier 2 then tier 3.
- Independent quality recheck: focused gateway/MCP suite -> `46 passed in 5.79s`; full suite -> `498 passed in 61.76s`; `python -m compileall -q xrefkit`, `python -m xrefkit xref check`, and `git diff --check` each exited `0`; xref reported `index_size: 318`, `missing_xid: 0`, `issues: 0`.

### Open Items
- `LIVE-HOST-001`: no live client-host execution established that a real host persists returned `WorkflowState` values in order, dispatches the selected worker, and reports the actual observed model. The real MCP stdio test passed locally, but it verifies the server boundary rather than host execution behavior.
- Runtime volume, workflow width, retry frequency, and state-retention limits are not available from the repository diff.

### Handoff
- Next owner: host integration owner
- Next action: resolve `LIVE-HOST-001` with one persisted multi-step execution transcript and provide representative workflow-volume evidence or accept that boundary explicitly. The implementation fixes need no further source changes from this executor review.

## Check item matrix

| Work item | Category | Initial result (`2c48cbe`) | After-fix result | Evidence / detail |
| --- | --- | --- | --- | --- |
| `REV-001` | Configured static baseline | `pass` | `pass` | Exact commit: 493 full tests and 13 focused tests passed. Current diff: 498 full tests and 46 focused tests passed. `compileall`, diff check, and xref check passed. No configured type checker, linter, formatter check, or dependency scanner is declared in `pyproject.toml`. |
| `REV-002` | Resource efficiency | `needs_confirmation` | `needs_confirmation` | No direct per-item client/resource creation was introduced. Production workflow width, repeated-result volume, and retained-state size remain unavailable; see [static boundary](#static-analysis-boundary). |
| `REV-003` | Operational resilience | `finding` | `pass` | [PY-WIMR-002](#py-wimr-002--parallel-results-can-silently-overwrite-one-another) and [PY-WIMR-004](#py-wimr-004--documented-cli-state-chaining-fails) are `pass-after-fix`. |
| `REV-004` | Synchronization and concurrency | `finding` | `pass` | [PY-WIMR-002](#py-wimr-002--parallel-results-can-silently-overwrite-one-another) is `pass-after-fix`, including repeated routing before result recording. |
| `REV-005` | Required business input integrity | `finding` | `pass` | [PY-WIMR-001](#py-wimr-001--compatibility-route-dispatches-without-required-authorization) is `pass-after-fix`. |
| `REV-006` | Support lifecycle | `pass` | `pass` | `pyproject.toml` requires Python `>=3.11`; Python 3.11 and 3.12 are supported security branches on the current [Python versions status](https://devguide.python.org/versions/). Local verification used Python 3.12.9, Pydantic 2.13.4, and MCP 1.28.0. |
| `REV-007` | Error handling and exception paths | `pass` | `pass` | Pydantic validation rejects stale/invalid route identities and `main()` converts `OSError`/`ValueError` into a nonzero JSON error. No swallowed exception path was found in the changed Python boundary. |
| `REV-008` | Time, locale, and encoding | `pass` | `pass` | Stable hashes use sorted UTF-8 JSON; instruction snapshots explicitly use UTF-8/UTF-8-SIG. No time or locale decision was introduced. |
| `REV-009` | State and determinism boundary | `finding` | `pass` | [PY-WIMR-002](#py-wimr-002--parallel-results-can-silently-overwrite-one-another) and [PY-WIMR-003](#py-wimr-003--removed-work-items-lose-their-record) are `pass-after-fix`. |
| `REV-010` | Uncertainty and escalation paths | `finding` | `pass` | [PY-WIMR-001](#py-wimr-001--compatibility-route-dispatches-without-required-authorization) is `pass-after-fix`; `needs_assessment`, `authorization_required`, and `conversation_upgrade_required` are explicit. |
| `REV-011` | Contract and schema resilience | `finding` | `pass` | [PY-WIMR-003](#py-wimr-003--removed-work-items-lose-their-record), [PY-WIMR-004](#py-wimr-004--documented-cli-state-chaining-fails), and [PY-WIMR-005](#py-wimr-005--upgrade-preview-ignores-lowest-cost-selection) are `pass-after-fix`. |
| `REV-012` | Traceability and context propagation | `finding` | `needs_confirmation` | Source-local state loss is fixed; live selected-versus-observed host propagation remains `needs_confirmation`. |
| `REV-013` | Custom framework integration | `needs_confirmation` | `needs_confirmation` | Pydantic schemas, local wrappers, and real MCP stdio tests passed with MCP 1.28.0. Actual Codex/VS Code host dispatch, state persistence, and observed-model reporting were not exercised (`LIVE-HOST-001`). |

Initial coverage: `pass=4`, `finding=7`, `needs_confirmation=2`, `not_applicable=0`, `not_checked=0`.

After-fix coverage: `pass=10`, `finding=0`, `needs_confirmation=3`, `not_applicable=0`, `not_checked=0`.

## Static-analysis boundary

| Work item / category | `confirmed_by_static_analysis` | `not_detectable_by_static_analysis` | `requires_runtime_or_human_evidence` |
| --- | --- | --- | --- |
| `REV-001` baseline | Test, compile, and diff-whitespace results are explicit for `2c48cbe`; configured baseline is pytest only. | Behavior outside the tested environments. | CI run on supported host matrix, if different from local Python 3.12.9. |
| `REV-002` resource efficiency | Routing uses bounded source hashing chunks, but deep-copies and returns the complete workflow state; no per-item network client is created. | Production workflow width, result/retry frequency, serialized state size, host memory limits. | Representative maximum workflow and retry-volume measurement. |
| `REV-003` operational resilience | Initial CLI chaining and stale-state failures reproduced. The current diff accepts CLI envelopes and returns `waiting_active_result` until the active result is recorded. | Host persistence ordering, crash recovery, and retry policy. | One interrupted/restarted workflow transcript from the real host. |
| `REV-004` synchronization | Initial multiple-active behavior reproduced. The current diff enforces at most one `in_progress` item in `WorkflowState`, routes at most one node, and does not activate another node on repeated routing. | Whether each client host persists the returned serial state before continuing. | Real-host serial re-entry transcript. |
| `REV-005` required input integrity | Initial compatibility-route dispatch reproduced. The current diff returns `authorization_required`, preserves model selection, and emits no dispatch. | Whether the host presents and refreshes required authorization correctly. | Real-host authorization refresh transcript if operational acceptance requires it. |
| `REV-006` support lifecycle | Declared Python/Pydantic/MCP constraints and installed versions are visible; local tests pass. | Future dependency releases and each deployment's selected versions. | CI dependency matrix or lock evidence when release policy requires it. |
| `REV-007` errors | Boundary validators and CLI error conversion are source-visible and covered by tests. | Host presentation/retry behavior for MCP tool errors. | Real host error transcript for operational acceptance. |
| `REV-008` time/locale/encoding | UTF-8 hashing/reading and deterministic JSON hashing are explicit; no datetime/locale logic exists in scope. | Filesystem/provider normalization outside the supplied byte snapshots. | Cross-host snapshot check only if those hosts transform input bytes. |
| `REV-009` state/determinism | Initial stale parallel state and removed-step loss reproduced. The current diff enforces one active assignment and preserves exact removed-item tombstones plus retired history. | External persistence atomicity and recovery after client interruption. | Real-host serial persistence test. |
| `REV-010` uncertainty/escalation | Unknown metrics reject candidates; source mismatch becomes `needs_assessment`; parent-tier mismatch becomes `conversation_upgrade_required`. | Human interpretation of classifications and authorization evidence. | Human/host evidence for the authorization refresh boundary. |
| `REV-011` contract/schema | Strict schemas remain in place; the current CLI loader accepts raw states or returned envelopes; tombstone structure and upgrade ordering have regression tests. | Backward compatibility of external stored states not represented by repository fixtures. | Migration fixtures from a real previously persisted state, if such states exist. |
| `REV-012` traceability | Route IDs, route revisions, selected/observed model fields, evidence, failure history, and resolution evidence are present; the current diff retains removed-item history and prevents multiple active assignments. | Operational sufficiency of evidence strings and live host attribution. | Persisted end-to-end route/result record from a real host. |
| `REV-013` custom framework | Local MCP wrapper registration, schema exposure, startup gating, and stdio invocation pass. | Codex/VS Code dispatch semantics and selected-versus-observed model availability. | `LIVE-HOST-001`: real host workflow transcript. |

## Findings

### PY-WIMR-001 — compatibility route dispatches without required authorization

- Severity: `major`
- After-fix disposition: `pass-after-fix`
- After-fix evidence: current `xrefkit/gateway.py:486-603` records required authorization separately, suppresses dispatch unless authorized, and returns `authorization_required`; `tests/test_gateway.py:78-92` covers the compatibility route. Independent probe returned `authorization_required`, `dispatch_status=authorization_required`, and zero dispatches.
- Evidence: `xrefkit/gateway.py:471-489` in `2c48cbe`; contract: `docs/core/contracts/110_work_item_model_routing.md:56-69`.
- Reproduction: a model `operation` step with `authorization.status="required"` returns `status=ready`, `dispatch_status=subagent_dispatch_required`, and one dispatch from `route()`.
- Violated condition: when authorization is required, the gateway may select/report a model but must not create an assignment or dispatch.
- Impact: the still-exposed `route_instruction_gateway` compatibility path instructs the host to dispatch an external operation before authorization is refreshed.
- Remediation: apply the same authorization gate used by `route_work_items()` to `route()`, keep model selection visible, suppress dispatch, and return an authorization-required disposition. Cover model and deterministic external steps.
- Return: implementation-local; no design decision is required.

### PY-WIMR-002 — parallel results can silently overwrite one another

- Severity: `major`
- After-fix disposition: `pass-after-fix`
- After-fix evidence: current `xrefkit/gateway.py:390-391` rejects more than one active item; `xrefkit/gateway.py:827-835` prevents a new route while one is active; `xrefkit/gateway.py:1068-1075` returns `waiting_active_result`; `tests/test_gateway_work_items.py:340-367` covers both the initial route and repeated route before result recording. Independent probe preserved `[a=in_progress,b=pending]` on the repeat call.
- Evidence: `xrefkit/gateway.py:720-724`, `xrefkit/gateway.py:914-947`, and `xrefkit/gateway.py:1019-1085` in `2c48cbe`.
- Reproduction: two independent ready items `a` and `b` are both routed `in_progress`. Recording each result independently from the same returned state succeeds; one returned state is `[a=done,b=in_progress]` and the other is `[a=in_progress,b=done]`. Persisting either last silently loses the other completion.
- Violated condition: every returned state is a safe re-entry token and accepted results must preserve prior accepted observations/completion state.
- Impact: parallel host dispatch can erase completion evidence, leave already-executed work active, and permit duplicate execution.
- Remediation: either route only one ready item per state token, or add an enforced monotonic state revision/CAS plus a merge operation that rejects stale whole-state updates. Document and test the chosen concurrency contract.
- Return: implementation-local if single-item routing is selected; a parallel merge design requires coordinator judgment.

### PY-WIMR-003 — removed work items lose their record

- Severity: `major`
- After-fix disposition: `pass-after-fix`
- After-fix evidence: current `xrefkit/gateway.py:51-76` defines evidenced removed-step tombstones; `xrefkit/gateway.py:352-391` validates retained records; `xrefkit/gateway.py:670-730` requires exact tombstones and copies prior state into `retired_items`; `tests/test_gateway_work_items.py:370-425` covers rejection and preserved observations/completion evidence. Independent probe returned active `[a=done]` and retired `[b=done]`.
- Evidence: `xrefkit/gateway.py:136-142` and `xrefkit/gateway.py:571-619` in `2c48cbe`.
- Reproduction: revision 0 completes `a` and `b`; revision 1 keeps only `a` and supplies a valid `scope_change` naming `a`. Re-entry succeeds and returns only `[a=pending]`; `b` and all its completion/observation history disappear. The schema cannot name `b` in `affected_steps` because affected IDs must exist in the new assessment.
- Violated condition: structural changes require explicit evidenced scope change, and stable work-item observations/completion evidence must remain traceable.
- Impact: deletion is neither precisely authorized nor auditable; completed, blocked, or escalated history can disappear during re-entry.
- Remediation: require an evidenced tombstone for every removed `step_id` with prior node/hash/status identity and retain retired item history in workflow state or a linked immutable artifact.
- Return: implementation-local within the approved workflow-state scope.

### PY-WIMR-004 — documented CLI state chaining fails

- Severity: `major`
- After-fix disposition: `pass-after-fix`
- After-fix evidence: current `xrefkit/gateway.py:1283-1287` accepts raw state or a returned envelope and all state-consuming CLI branches use it at `xrefkit/gateway.py:1362-1378`; `tests/test_gateway_work_items.py:492-533` chains init output directly into route and route output into result. Independent init-to-route probe returned exit codes `0,0` and `status=ready`.
- Evidence: `xrefkit/gateway.py:1244-1261`, `docs/guides/094_instruction_gateway.md:187-200`, and `tests/test_gateway_work_items.py:395-414` in `2c48cbe`.
- Reproduction: `workflow-init --out` writes an envelope containing `schema_version`, `status`, `workflow_state`, and `next_tool`; passing that documented output to `workflow-route --state` invokes strict `WorkflowState.model_validate_json()` and fails on `schema_version` as an extra field. The test manually extracts and rewrites `initialized["workflow_state"]`, masking the documented command chain.
- Violated condition: the returned workflow state is the next re-entry token, and the documented CLI output must be consumable by the next CLI step.
- Impact: the advertised local workflow stops after initialization unless a user performs an undocumented JSON extraction; the same issue affects route/result envelopes used as later state inputs.
- Remediation: make CLI state loading accept either a raw `WorkflowState` or the gateway envelope's `workflow_state`, and test direct output-file chaining across init, route, result, and re-entry.
- Return: implementation-local.

### PY-WIMR-005 — upgrade preview ignores lowest-cost selection

- Severity: `minor`
- After-fix disposition: `pass-after-fix`
- After-fix evidence: current `xrefkit/gateway.py:526-528` defines the cost-aware `selection_key` and `xrefkit/gateway.py:563-571` reuses it for the compatibility upgrade preview; `tests/test_gateway.py:163-188` covers mixed tiers and priorities. Independent probe selected tier 2 for the flexible step and tier 3 only for the capability-constrained step.
- Evidence: `xrefkit/gateway.py:462-464` and `xrefkit/gateway.py:491-500` in `2c48cbe`; contract: `docs/core/contracts/110_work_item_model_routing.md:30-38`.
- Reproduction: under `selection_strategy="lowest_cost_eligible"`, one step can use tier 2 or tier 3 while another forces a tier-3 conversation upgrade. `workers_callable_after_upgrade` reports tier 3 for both because line 497 sorts only by priority/ID, even though rerouting after upgrade would choose tier 2 for the first step.
- Violated condition: `lowest_cost_eligible` orders by cost tier, then priority, then model ID.
- Impact: the proposal overstates the worker tier/cost for an affected step and presents a preview inconsistent with the subsequent route result. It is proposal-only, so no direct dispatch occurs at this point.
- Remediation: reuse `selection_key` when selecting `workers_callable_after_upgrade` and add a mixed-tier/mixed-priority regression test for both gateway routes.
- Return: implementation-local.

## Required business input facts

| input / candidate | decision gated | source | missing or invalid behavior | default provenance | disposition | status |
| --- | --- | --- | --- | --- | --- | --- |
| `Step.authorization` | whether an external action may be assigned/dispatched | instruction/Skill evidence | initial compatibility route ignored `status="required"`; the current fix preserves selection but emits no assignment or dispatch | none | initial finding closed by `PY-WIMR-001` `pass-after-fix` | `pass` |
| complexity metrics | model eligibility | assessment evidence | unknown axes reject all candidates and return `needs_assessment` | none | controlled rejection | `pass` |
| evaluated candidate | per-item model selection | operator policy | no eligible model returns `needs_assessment` or `conversation_upgrade_required` | none | controlled disposition | `pass` |

## Gate verdict

```text
verdict: proceed
reason: all five repository implementation findings are pass-after-fix and the configured repository baseline passes
evidence: work/reviews/2026-09-14_python_review_workitem_model_routing.md; pytest 498 passed; focused pytest 46 passed; compileall pass; xref check missing_xid=0 issues=0; diff-check pass
downgrade_reason: none for the repository implementation gate; live-host execution and representative runtime-volume evidence remain explicit external unknowns
required_followup: host integration owner resolves LIVE-HOST-001 and accepts or measures RUNTIME-VOLUME-001 before claiming operational integration
```

This is a repository implementation review verdict. It does not claim live-host integration, production-volume suitability, or release approval.

## Handoff list

| Handoff | Owner | Item | Required evidence |
| --- | --- | --- | --- |
| `RETURN-IMPL-001` | `python_implementation_flow` | `PY-WIMR-001` through `PY-WIMR-005` | complete: current diff, focused regression tests, and full configured baseline verified |
| `RECHECK-001` | `python_review` | Re-dispose all five findings after implementation return | complete: all five are `pass-after-fix` |
| `LIVE-HOST-001` | host integration owner | Verify real dispatch, ordered state persistence/re-entry, and observed-model reporting | persisted end-to-end client-host transcript |
| `XDDP-HANDOFF-001` | `qa_gate_review` | Trace-continuity review remains outside this Skill | review only if the coordinator requires XDDP closure |
| `SECURITY-HANDOFF-001` | `security_review` | Authorization bypass crosses an authority boundary | specialist review only if coordinator classifies it as security scope; this report makes no security verdict |

<!-- xid: 0A4F8C62D199 -->
<a id="xid-0A4F8C62D199"></a>

# XRefKit API Execution Boundary Structure Findings

## Status, target and source basis

- Target XID: `E9A4C7B2106D` (`repository:XRefKit`, bounded Python API execution integration boundary).
- Analysis kinds: `python_structure`, `api_execution_boundary`.
- Current for Git commit `2271fb1015b01ef731982810f2bea3ff9f6ab9fe`, verified by source inspection on 2026-11-21.
- Producer: instruction-backed Python source inspection for [Issue #199](https://github.com/synthaicode/XRefKit/issues/199). Canonical normalization: `source_structure_findings_registration`.
- Scope: Core work-item routing and result projection, ExecutionBinding and host startup, MCP Runtime distribution and XID lookup, workflow and dashboard evidence, and explicit Quality Issue intake. The optional API executor is a proposed consumer of these interfaces.
- The existing client-work finding `D4B4C2657A63` covers workspace/plan handling and Azure client-work delivery and recovery. This finding covers API-execution integration pivots, including the dashboard's workflow evidence projection only.

## Structure pivots and route coverage

| Runtime unit | Observed responsibility and source |
| --- | --- |
| Gateway and client host | `WorkflowState` rejects a state with multiple in-progress work items. `route_work_items` consumes supplied state and selects at most one dependency-ready item per call. Dispatch plans give ownership to `client_host`; the host performs invocation. The returned state is a re-entry token. Per-call selection supplies no durable cross-caller claim. [Routing](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/gateway.py#L1098-L1410) |
| Result recording | `record_work_item_result` validates request, assessment, step/node and active route correlation. A model assignment requires an observed model. A mismatched reported success can still project to `done` and emit a mismatch observation. Eligible failure can return the work item to pending with a new route revision for upper routing. [Result projection](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/gateway.py#L1412-L1516) |
| Binding and startup | `build_execution_binding` derives a binding from the Skill Run and checks the expected revision; the snapshot validator checks builder-generated bindings and returns early for existing marker-free inputs. The startup reader confines material paths, checks XID/hash and active binding, bounds total context and records a startup observation. MCP resolves the selected document by XID separately. [Binding](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/execution_binding.py#L153-L204), [startup](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/subagent_startup.py#L73-L158), [XID lookup](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/mcp/catalog.py#L1289) |
| Runtime acquisition interfaces | MCP exposes the Runtime manifest, package/bundle delivery and version check. Core declares its own CLI and dependencies in `pyproject.toml`; that declaration has no OpenAI client dependency. Compatibility selection, integrity and cache rules for an optional API package are design work. [Distribution](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/mcp/catalog.py#L1234-L1287), [Core package](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/pyproject.toml) |
| Workflow and evidence | `skillrun.py` owns procedural verification, closure and child-run reconciliation; the dashboard projects recorded evidence. Explicit operator feedback passes through host preparation of `QualityReport` and `TransferPolicy` before inert Contribution Return intake. Governed Quality Issue decisions use a separate human approval verification path. [Reconciliation](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/skillrun.py#L3823-L3918), [dashboard](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/dashboard.py#L1085), [intake](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/quality_issues.py#L83-L149), [decision](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/quality_issues.py#L243-L312) |

## Requirement-to-target trace

These are affected or protected interfaces for design. Planned components and checks have no implementation evidence here. Issue #199 holds the work scope and approval gates.

| Requirement group | Protected interface or proposed change target |
| --- | --- |
| #199/#206: one execution owner, retry versus reroute | Gateway state and dispatch/result APIs, ExecutionBinding, host dispatch, and proposed API Controller. Preserve existing Skill formats, routing priority and flow correlation from [#108](https://github.com/synthaicode/XRefKit/issues/108), [#109](https://github.com/synthaicode/XRefKit/issues/109) and [#110](https://github.com/synthaicode/XRefKit/issues/110). |
| #200–#202: separate package and bounded context/provider request | Core package and MCP distribution, startup/XID lookup and proposed package contract, context and Responses adapter. Preserve error redaction from [#116](https://github.com/synthaicode/XRefKit/issues/116). |
| #201/#203/#204: Tool/Knowledge, runner capability and user authorization | Shared XID routing and proposed XRefKit-owned registry references, runner availability evidence, command policy and new destination confirmation at the effect boundary. |
| #203–#207: budget, receipts, evaluation and recovery | Proposed permission/reservation, dispatch receipt, evaluation and Controller/journal contracts; preserve Gateway result schema and Runtime verification/reconciliation. |
| #208/#209: host integration, protected interaction evidence and explicit feedback | Dashboard evidence projection, proposed protected recorder and tool candidate intake, QualityReport and Contribution Return. Tool registration remains #204 scope. |
| #210: package, host and pilot acceptance | Existing Gateway, Binding, Workflow and Quality Issue regression surfaces plus proposed offline, live and human acceptance gates. |

## Constraints and unresolved verification

- Preserve host-owned dispatch, generated/legacy binding compatibility where applicable, result vocabulary, CLI/MCP behavior, evidence correlation and separate human authority. Changes to those contracts require their owning workflow and review.
- Canonical registration establishes the inspected source structure. R2 remains a design proposal awaiting human disposition. Dispatch fencing, model conformance before success, and unknown-result reconciliation are proposed responsibilities for later verification.
- External effects, provider billing/replay, Tool registry and actual runner controls, separate package acquisition, durable cross-host coordination, protected transcripts, and end-to-end host compatibility have not been verified by this source finding. Neither #200 implementation nor fixture verification is covered. Prior baseline test observations are recorded in #199.

## Sources

- source_type: repository_source
- source_revision: 2271fb1015b01ef731982810f2bea3ff9f6ab9fe
- source_locator: pinned runtime pivots above and existing requirement-to-target trace
- inspected_at: 2026-11-21

<!-- pm-human-view:start -->
**The bounded context design is awaiting the versioned execution contract in [#200](https://github.com/synthaicode/XRefKit/issues/200).** It will resolve required startup and XID material through XRefKit and assemble only context authorized for the API call.

**Acceptance.** Verify source/version provenance, context limits and the absence of prohibited or unapproved content from provider-bound context. Required missing or stale source material must trigger the recorded hold path.

**Next.** The Runtime/context and deployment-data owners need to review the contract revision, permitted material, classification and fixture scope. Named owners and live-data authorization remain pending.

[GitHub Project #3](https://github.com/users/synthaicode/projects/3)
<!-- pm-human-view:end -->

<details>
<summary>Detailed design, decisions and evidence</summary>

## Purpose
Build bounded context from existing startup and XID sources.

Epic: #198
Canonical Project: https://github.com/users/synthaicode/projects/3
Status: proposed / not started. Implementation requires a separate instruction. Phase: P1.

<!-- api-execution-pm-plan-2026-11-21 -->
<!-- api-runtime-context-design-2026-11-21 -->
## Proposed startup, XID resolution and OpenAI context

Planning design following #200. XRefKit owns startup, Skill readiness, binding and source resolution. The API runtime owns selecting the authorized portion to send, assembling and validating a bounded request, and recording its provenance. This proposal does not authorize implementation or data transfer.

### 1. Acquire Runtime and load startup

- First-release path: use the Runtime resolved by #200 and its isolated interpreter. Select an explicit authorized XRefKit repository or approved materialized source tree and record its identity and revision. The Core wheel supplies code and bundled assets. It does not establish a project's AGENTS.md, Skill, Knowledge or repository-native startup tree, so acquire those through the approved source independently of the wheel.
- Before routing, use the repository-native sequence: applicable vendor entry, startup contract XID `C3A1F78D9B22`, then its ordered base-control and xref-routing sources. Validate the required source identities against the selected snapshot. If mandatory startup inputs are missing, ambiguous or from a different revision, stop and report the missing basis. Avoid substituting the MCP compressed pack for the native contract. [Startup contract](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/docs/core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22)
- For a routed work item, open the applicable workflow or Skill run under the existing Runtime gates. Build and validate its ExecutionBinding. For a compatible filesystem-mode child work item, the existing `workflow subagent-read` materializes bounded startup, selected protocols, Skill and declared references against the opened run. It requires an approved root and a current binding. Its receipt proves local materialization, so record API delivery separately. Retain run/flow/work-item/node and route correlation from #200. [Binding](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/execution_binding.py#L153-L204), [local reader](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/subagent_startup.py#L73-L158)
- MCP is an explicit separate mode, outside the first filesystem fixture scope. Where used, preserve the server startup load order, resolve Runtime immediately after `get_startup_context` and before Skill routing, then bind the opened Skill run and run its client record command before task-specific retrieval. Use `get_document_by_xid` and the same repository/session identity. Do not fall back to local files within an MCP-bound run. [MCP startup and XID contract](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/docs/core/contracts/080_xrefkit_startup_contract.md#xid-C3A1F78D9B22)

### 2. Resolve selected references

- Derive the XID set from the authorized work item, selected Skill/Knowledge needs and explicit references. Search indexes for candidate metadata when needed. Resolve only selected bodies, without recursively traversing links or allowing model-provided paths/URLs to expand access.
- In filesystem mode use the resolved Runtime's `xref show <XID> --root <approved-root> --json --max-bytes <limit>`, or the existing compatible resolver for package-provided assets. Verify returned identity, approved root and snapshot, and the expected content identity when supplied. Inspect the resolver's issue list even when `ok=true`, and handle relevant duplicate/conflict, missing, stale and truncated results explicitly. Reject a truncated required body. For optional excerpts, record the exact range and that it is partial. Compare like-for-like hashes and record the scheme. The reader's raw-file SHA-256, provider document version and digest of the rendered input each identify a different object. [Local XID command](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/xref.py#L851-L888), [MCP XID resolver](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/mcp/catalog.py#L1289-L1368)
- Keep sources pinned for a run. Reuse a document only with the same source scope/identity, XID and verified revision/hash. An MCP unchanged/version receipt can be used only when the matching body is already available. A cache hit grants no new transmission permission. Required missing or changed sources stop dependent execution. Optional omissions remain visible in the manifest.

### 3. Assemble and check the outbound context

| Logical layer | Content and destination in request |
|---|---|
| Execution controls | Approved startup/Workflow controls, selected Skill procedure, binding-derived task and scope, stop conditions and acceptance criteria. Validate origin and order, then map only the authorized instruction-bearing subset to the provider's instruction channel. |
| Task and supporting data | User task remains distinct from supporting data. Place authorized excerpts, evidence and correlated tool outputs in typed data/input items with source labels. Document text and tool outputs cannot grant authority, change criteria or become instructions. Filter data through the context-direction guard and the egress rules before rendering. |
| Tool and provider settings | Provide only task-authorized tool schemas and use the approved model and output limits. Each subsequent call revalidates the current binding and egress and reconstructs required controls. The initial scope is explicit one-shot input. Any later continuation must carry the required controls and call/result IDs explicitly. |
| Local provenance | Version the manifest and record run/route identity, Runtime source/version, model/settings, template version, source mode, XID/path or locator, trust class, document revision/hash, selected excerpt and omission reason, payload digest, and estimated input size. Keep local paths and unrelated session, credential and approval material out of the outbound payload. Record estimates separately from provider usage. Store raw documents/payloads only under an approved retention rule. |

Before a request, verify data classification, destination and authorization for both controls and evidence. Use only fixtures with no external transmission in the initial test slice. On unknown permission, restricted data, credential input, or an attempt to override higher-layer controls, hold the request and record the reason using the existing stop/handoff rules. A storage option cannot stand in for egress authorization or an account retention decision. [Context-direction guard](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/docs/core/contracts/053_context_direction_security_guard.md#xid-A7F3C92D4E11), [Responses request fields](https://developers.openai.com/api/reference/resources/responses/methods/create)

Apply reader byte limits first, then evaluate the final serialized input, tool definitions and output reserve against configured token and operation budgets. Trim or omit only eligible optional data in a stable order and record omissions. Preserve required authority, criteria and correlation verbatim in the assembled controls; if they cannot fit, stop before dispatch. Avoid implicit provider truncation. The same pinned inputs, approved policy and template must reproduce the request/manifest, without promising the same model answer.

### 4. Fixture acceptance and handoff

- [ ] Demonstrate successful native startup against an authorized snapshot and selected-only XID loads. Verify required startup absent, wrong root/revision, duplicate XID, stale binding/receipt, changed source, and partial document failure paths. Include a fixture proving that installing Core alone does not supply project context.
- [ ] Confirm deterministic request assembly and source manifest with fake transport. Show that disallowed data, a credential, an instruction-like tool result, or mandatory controls exceeding budget cannot be submitted. Show that optional omission is recorded, and source trust and work-item correlation survive serialization.
- [ ] Verify the resolver/adapter contract consumed by #202, the scoped tool and I/O input boundary for #204/#205 and the stop/handoff result for #206. Keep live model, input/send authorization, retention and numerical limits open under #199/#203. MCP compatibility and live delivery require their own verification.

**Source check performed:** read current `main` at `2271fb1015b01ef731982810f2bea3ff9f6ab9fe`. A local read of the startup XID with a 50-byte limit returned `truncated=true`. This checks the existing resolver behavior only. No new assembler, fixture tests or live API calls were performed.

<!-- api-runtime-context-pm-revision-2026-11-21 -->
## Project Management coordination record

**Confirmed for this planning revision:** [GitHub Project #3](https://github.com/users/synthaicode/projects/3) is the planning record, #201 is the work-item record, and the user authorized updating this Issue. The technical design above remains the proposal under review. The separate-package direction is recorded in #199. The acquisition and interface details in #200 are still proposed. **#201 implementation is not authorized and has not started.**

### Decisions and holds

All owner roles below are proposed. Named owners and formal review/approval records are pending. Record each decision with the authorizing person and role, date, applicable scope/revision, outcome, evidence link and affected Issues. The future Issue updater records the decision here or links to the owning record in #199, #200 or #203 and records which part of #201 it applies to.

| ID / decision | Proposed decision owner | Approval status and evidence needed | Affected work and resolution point |
|---|---|---|---|
| D201-1 Runtime and contract prerequisite | #200 contract owner and Runtime maintainer | Pending. Link the reviewed #200 revision for Core acquisition, compatibility and versioned request/binding/result interfaces. Confirm #199 boundary decisions that affect this slice. | Resolve the applicable #200 dependency before #201 implementation. Record the exact interface revision the fixtures will consume. |
| D201-2 Native startup mode and source identity | Runtime maintainer and repository/source owner | Pending. Approve the source root/snapshot, startup sequence and filesystem fixture scope. Provide evidence for required source identity and binding freshness. | Required before implementing startup retrieval with the selected source. MCP mode stays outside the initial slice and needs a separately reviewed compatibility scope before use. |
| D201-3 XID selection, trust and provenance | Runtime maintainer and source/Knowledge owner | Pending. Review allowed resolver entry points, required versus optional XIDs, revision/hash scheme, partial and conflict behavior, and a sample provenance manifest. | Resolve before implementing the affected resolver/manifest behavior. Confirm that optional omissions are auditable and required-source failures hold the dependent work. |
| D201-4 Request assembly, limits and verification | Runtime/adapter design owner and designated quality reviewer | Pending. Review instruction/data mapping, manifest and error contract, required-control preservation, and fixture criteria for oversize, stale inputs and lower-trust data. Agree fixture limits separately from real operating limits. | Required to accept the affected fixture slice and its outputs. Real model, input/output limits, spend, cancellation and retry policy remain open in #199/#203. |
| D201-5 Data egress and retention | Deployment/data owner and API policy owner | Pending. Record the authorized data class, destination, permitted content, credential handling and retention scope under #199. Record the live budget and model policy where applicable. | Real repository data sent to a provider and live API calls stay on hold. A synthetic, no-network fixture slice may be considered on its own once explicitly authorized. |
| D201-6 Implementation start and review authority | Project owner, with the Runtime maintainer reviewing the scope | Pending. Name the executor and reviewer, confirm the specific fixture slice, evidence expected, and the Codex usage cap or review threshold under the project plan. Record explicit start authorization. | Keep implementation unstarted until a scoped decision is linked. The planned model is GPT-6.2 Sol. The Codex usage cap remains unset. |

### Work-start and verification conditions

- **Readiness for fixture-only work:** Refresh #200's native dependency and link the reviewed prerequisite revision for the requested scope. Record the applicable decisions from D201-1 through D201-4, select the approved synthetic snapshot, name the executor/reviewer and record explicit authorization for the scoped work in D201-6. Until then, the next action is for the project owner to designate owners and arrange review of the #200 prerequisite and #201 fixture scope.
- **Fixture delivery:** Link the exact contract and fixture revision, source manifest, positive/negative check results and any unresolved concerns. The designated reviewer records the review result against the published acceptance criteria. The coordinator records any status change based on that evidence. A proposal or a fixture result does not establish authorization for MCP or external data delivery.
- **Live work:** Hold the affected scope until the data, destination and operating approvals in D201-4/D201-5 are on record. Leave the decision, impact and next owner visible if a condition is outstanding.

### Handoff to later Issues

Record the exact artifact version, acceptance evidence, any continuing hold and the receiving owner's acknowledgment when available. These are planned deliveries. No implementation artifacts or acceptance results are recorded yet.

| Receiving Issue | From #201 and evidence needed | Relationship |
|---|---|---|
| #202 Provider adapter | Approved outbound input contract for controls, data and settings, example sanitized fixture, and preflight rejection behavior. | Interface coordination. #202 has its own #200 dependency. |
| #204 Tool Dispatch | Authorized context and tool input boundary, source trust labels, scoped call/result correlation and deny-case fixture evidence. | Native #201 dependency. #203 remains a separate prerequisite. |
| #205 I/O evaluation | Expected context/evidence manifest fields and fixtures for missing, stale, oversized and disallowed data. | Evidence coordination via #204 and the existing #205 dependencies. |
| #206 Controller | Versioned assembly and provenance results, stop/handoff reasons, optional omissions and fixture evidence for context failure paths. | Native #201 dependency. Other existing prerequisites also apply. |

This revision follows the Project Management package's progress rules setup and persistence handoff as an explicit setup proposal. It applies the confirmed GitHub record mapping from #198 and leaves operational approval and named assignments unresolved.

## Proposed work-start and handoff evidence
Input: #200's schema and #199's applicable input/egress decisions. Handoff to #204 and #206: versioned context manifest, source trust boundaries and fixture results for missing or oversized context. Keep any real data transmission held until the applicable data decision is recorded.

## Planned work
- Reuse existing startup readers/resource providers; construct trusted control separately from external documents/tool outputs.
- Record Skill/Knowledge/profile revisions, hashes, selected model/inference settings and input manifests.
- Bound bytes/tokens and output payload size; compaction preserves authority, criteria, unresolved items and tool correlation. Stop when required control cannot fit.
- Define data egress filtering and secret exclusion before provider request.

## Acceptance and verification
- [ ] Fixtures cover oversized inputs, stale XIDs/hashes, injection attempts, missing mandatory context and summaries losing constraints.
- [ ] No unauthorized source lookup, path escape or credential in context/logs.
- [ ] Same manifest can reproduce input assembly; no promise of identical LLM output.

## Risk
Context truncation or lower-trust data changing authority.

## Source basis and compatibility
Baseline: 2271fb1015b01ef731982810f2bea3ff9f6ab9fe; recheck drift at implementation.
- [xrefkit/subagent_startup.py](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/subagent_startup.py)
- [xrefkit/resource_provider.py](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/resource_provider.py)
- [xrefkit/contracts.py](https://github.com/synthaicode/XRefKit/blob/2271fb1015b01ef731982810f2bea3ff9f6ab9fe/xrefkit/contracts.py)

Follow existing startup, Workflow Runtime Binding, uncertainty, context-direction and human approval contracts referenced in #198. No global redefinition of governance terms.

## Dependencies and handoff
Blocked by: #200
Implementation owner: future assigned executor; design/acceptance decisions: human/runtime owner. No staffing commitment made.
Attach verification evidence and unresolved operational limits before moving to Done. Synthetic evidence does not prove live integration.

<!-- api-execution-codex-model-plan -->
## Codex development model plan

- **Planned model:** GPT-6.2 Sol. Build context assembly, eligibility checks and fixtures.
- **Higher-tier switch:** The #199 plan reserves no Astra review for this issue. Consider GPT-6.2 Astra only for a bounded review if a material context provenance or data-egress question remains after checking the policy and fixtures. Record the reason and scope in this Issue before switching and check availability in the executing Codex account.
- **Codex usage cap: TBD (not yet set).** Record the actual model, available usage measurements, and retry reasons in this Issue. Record unavailable measurements as unknown.

Allocation basis: [#199](https://github.com/synthaicode/XRefKit/issues/199#codex-development-model-allocation). This is the development model plan. The deployed OpenAI API model and its budget are separate decisions.


</details>

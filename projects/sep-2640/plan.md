<!-- xid: 9A62E4B817C3 -->
<a id="xid-9A62E4B817C3"></a>

# SEP-2640 work plan

Revision: 4, 2026-11-25. Highest priority, from the user's instruction.
This task-level breakdown precedes implementation. It is not an estimated
schedule, a detailed Brownfield WBS or a claim that planned work has passed.

## Preflight

- Route: Project Management `progress_rules_setup` and `work_progress_coordination`, then Python implementation, independent review and tests.
- Goal: make the XRefKit MCP Server support SEP-2640 with a precisely stated compatibility boundary.
- Context: dedicated worktree `C:/dev/itsm/XRefKit-sep2640`; initial source `7303a46d`; existing FastMCP server and catalog; observed SDK `mcp==1.28.0`, base protocol `2025-11-25`.
- Constraints: preserve existing tool interfaces and unrelated original-worktree changes; retain current governance authority; do not infer execution authorization from resource inspection.
- Done when: the implemented contract is source-backed, current-diff review is resolved, targeted protocol/regression tests pass, and remaining live-client/deployment limits are named.
- Out of scope: SDK-wide protocol migration unrelated to required compatibility, organization-policy changes, new release-policy design, unrelated deployment targets and client-host permission implementations. The later user instruction explicitly adds official release and the existing MCP server update; GitHub Projects registration remains in scope.
- Verification: focused new tests, existing MCP integration/catalog/startup tests relevant to the diff, deterministic structured-data validation when applicable, and `python -m xrefkit xref fix` with resulting diff inspection.
- Stop/re-route: unresolved protocol/security behavior, inability to preserve the execution boundary, scope expansion, or evidence refuting the design basis.
- Handoff: this plan, its technical basis, `work/sep2640/` evidence and the associated Skill Run logs.

## Work breakdown

| ID | Work and owner role | Depends on | Required output / acceptance evidence | Current state |
| --- | --- | --- | --- | --- |
| PM-01 | PM executor: record task settings and split work before implementation | User instruction | Settings and this plan saved/read back; both PM runs passed deterministic verify and close | Done |
| AN-01 | Technical analysis executor: pin applicable SEP/current extension requirements and SDK compatibility | PM-01 record available | Requirement matrix distinguishing accepted SEP and current beta; supported protocol/discovery advertisement; required versus optional methods; explicit supported versions | Done; design.md compatibility matrix |
| AN-02 | Technical analysis executor: define published Skill representation and authority boundary | AN-01 | Native `SKILL.v1.md` to Agent Skills `SKILL.md` mapping; valid name/frontmatter; complete exact-byte manifest; package/repository selection; existing startup/run-binding behavior; resource inspection versus execution authorization | Done; design.md bootstrap and authority mapping |
| IM-01 | Python executor: implement catalog/resource projection | AN-02 technical basis | Bounded serving inventory, stable URIs, frontmatter, sizes/digests and safe resource reads; no arbitrary filesystem exposure | Done; skills_extension.py |
| IM-02 | Python executor: integrate wire protocol handlers and capability declaration | AN-01, IM-01 | `skills/list`, `skills/get`, `resources/read`; precise discovery/initialize compatibility; standard errors; optional directory support only if implemented and declared | Done; skills_transport.py and server.py |
| TS-01 | Test executor: validate protocol and resource behavior | IM-01, IM-02 | Positive and negative fixtures; wire-level dispatch; invalid URIs/traversal; byte/digest equality; metadata fidelity; pagination if present; package/native eligibility | Done; 9 passed, 1 privilege-dependent skip, 9 subtests |
| RV-01 | Independent reviewer: review current diff against requirements and existing boundaries | IM-01, IM-02; TS-01 evidence when available | Version-scoped review, evidence-backed findings and severity; compatibility/security/governance analysis; no producer self-acceptance | Done; independent review.md, two test findings corrected |
| IM-03 | Python executor: address review/test findings within scope | TS-01 or RV-01 findings | Each finding linked to fix or reasoned handoff; changed design basis rechecked before retry | Done; optional-import and HTTP Host test fixes reviewed |
| TS-02 | Test executor and reviewer: validate final diff and relevant regressions | TS-01, RV-01; IM-03 when needed | Fresh affected test results, relevant existing MCP regressions and review disposition for final diff | Done; repaired full quality gate passed, 1,481 tests passed |
| CL-01 | Parent coordinator: reconcile actual evidence and deliver | TS-02, XID-03, GH-01 | Plan updated with artifact links, runtime verification/closure, explicit unverified items, user-facing result and verified Project registration | Done: QA and PM closure accepted; all six Project items read back as Done |

The parent records actual executor identity when dispatching each work item.
These role labels do not appoint people or change project authority. Independent
review may begin for an identified implementation slice while test execution is
ongoing; completion still requires the final combined evidence.

## Required technical checks

1. Capability declaration must match the actually implemented transport and
   negotiated protocol. Do not advertise full `2026-07-28` support merely because
   an extension response has newer fields.
2. `skills/list` and `skills/get` must agree for each served Skill; metadata must
   match the served `SKILL.md`, including naming constraints.
3. Each manifest digest and size must match the exact bytes returned by resource
   reads, including Unicode/newlines and binary files if supported.
4. Only intended published files may be read. Invalid/unknown paths, traversal,
   symlinks or equivalent boundary escapes require explicit handling/tests.
5. Standard resource inspection must not silently create a Skill Run, grant host
   code execution, or weaken existing XRefKit startup/run-binding controls.
6. Existing tool clients and relevant catalog/startup tests retain their behavior.
7. Optional `resources/directory/read`, pagination and dynamic skills must be
   explicitly implemented/tested or excluded from the advertised scope.

## Current holds and next actions

| ID | Affected work | What remains to resolve | Resolver and resolution point |
| --- | --- | --- | --- |
| H-01 | IM-02 | SDK exposes `2025-11-25`; current extension source targets `2026-07-28` and `server/discover`. Resolved in design.md: existing 2025-11-25 initialization binding; no full 2026 base claim. | Technical analysis executor in AN-01, before IM-02 |
| H-02 | IM-01, IM-02 | Resolved in design.md: generated bootstrap Skill; native content and execution gates preserved. | Technical analysis executor in AN-02, before implementation |
| H-03 | CL-01 claims | Real-client consumption and deployment have not been exercised. | Test executor records any available live check; parent explicitly bounds final claims |

H-01 and H-02 are technical analysis inputs, not new requests for business
approval. If analysis proves that satisfying the request requires an authority
or scope change, escalate that concrete decision under the existing contracts.

## Sources and run evidence

- [Task settings](settings.md#xid-3E81B6D29A40).
- [Accepted SEP-2640](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/seps/2640-skills-extension.mdx).
- [Current Skills extension specification](https://github.com/modelcontextprotocol/ext-skills/blob/main/specification/beta/skills.mdx).
- Source snapshots: `work/sep2640/sep-2640.mdx`, `work/sep2640/skills-beta.mdx`; the technical executor records hashes and retrieval evidence before relying on an exact version.
- PM setup Run: `work/sessions/2026-11-25_skill_run_progress_rules_setup.md`, run `c6052732-3ee8-4115-bfe3-60eab53add88`.
- PM coordination Run: `work/sessions/2026-11-25_skill_run_work_progress_coordination.md`, run `dfca5030-4565-47a5-9e27-f617aee45e46`.

No implementation, quality acceptance, test pass or remote visibility is claimed
by the creation of this plan.

## Final evidence

See [delivery result](result.md#xid-73D8E921C4A6). The original implementation and
repair have recorded outcomes. GitHub Projects registration is now verified by
the parent. Additional XID verification has passed; final reconciliation and remote state
updates remain separately tracked below.

## Follow-up: repair and verify the whole test environment

The user subsequently requested `修正確認` after the failure-cause investigation.
This authorizes correction of the confirmed test-environment defects and a new
whole-gate run. It does not change the SEP transport or release scope.

| ID | Work and owner | Depends on | Acceptance evidence | State |
| --- | --- | --- | --- | --- |
| FX-01 | Python executor: isolate test environment mocking without dropping inherited empty Windows variables | Confirmed reproduction | Focused regression preserves child environment and existing assertions | Done |
| FX-02 | Parent: install repository package in the isolated test environment | Confirmed setup import error | Import succeeds from a different working directory | Done |
| FX-03 | Independent reviewer and parent: review fix, rerun full quality gate, reconcile result | FX-01, FX-02 | Final diff review and complete gate output; 1,481 passed, 8 skipped, zero failures/errors | Done |

Repair Run: `work/sessions/2026-11-25_skill_run_sep2640_test_environment_repair.md`.

## Follow-up: existing XID compatibility and GitHub Projects registration

The user explicitly required tests confirming that existing XID search and
retrieval still work after the change. The subsequent `Projectsへ登録がない`
correction and `GitHub Projects` clarification establish the remote destination.
Local plan creation alone did not fulfill that requested registration.

| ID | Work and owner | Depends on | Acceptance evidence | State |
| --- | --- | --- | --- | --- |
| XID-01 | Test/review executor: run existing XID and MCP regression tests | Current SEP implementation and repaired test environment | Existing XRef, catalog, cache, identity and native Skill tests; command and result retained | Done: observed 96 passed, 8 subtests; `work/sep2640/xid-existing-tests.txt` |
| XID-02 | Independent test/review executor: exercise existing XID APIs through the modified stdio server | XID-01; current server source | `search_knowledge_catalog`, `get_knowledge_summary`, `expand_knowledge`, `get_document_by_xid`; canonical-source content equivalence; startup refusals; cache hit/miss; unknown-XID errors and recovery | Done: independent stdio probe exit 0; 27 tool calls plus ping; xid-wire-results.json |
| XID-03 | Parent coordinator: reconcile XID proof and update result/board evidence | XID-01, XID-02 | Current-source hashes, exact command/results, covered boundaries, final report and actual destination links | Done: local evidence reconciled; QA/PM closure accepted; #301 and #302 Done read back |
| GH-01 | Parent coordinator: register the work breakdown and follow-up in GitHub Projects | User destination clarification; verified intended board/access | Real Project/item identities, status/priority fields supported by current evidence and destination readback | Done: parent registered/read back Project 7 and six issues #297–302 through the authenticated browser |

XID-01 command:

```powershell
work/sep2640/venv/Scripts/python.exe -m pytest tests/test_xref.py tests/mcp_catalog.py tests/mcp_client_cache.py tests/mcp_repository_identity.py tests/test_skill_definition_mcp.py -q
```

XID-02 executes `work/sep2640/xid-wire-probe.py` using the isolated environment.
Observed evidence: `work/sep2640/xid-wire-results.json` reports `passed`,
27 tool calls, three canonical XID cases, three startup denials, three unknown-XID
errors and successful ping/retrieval recovery. Each case has search/body/metadata
agreement and cache hit/miss checks. `xid-wire-transcript.json` retains responses.
The final `work/sep2640/xid-verification-report.md` and verification session
record are saved; the JSON, transcript and reviewer report establish this result. Failed harness attempts remain
separate evidence, not product failures.

The CLI lookup lacked `read:project`. The parent used the existing authenticated
browser and confirmed successful registration and destination readback without
changing tokens. The original worktree has no `projects/sep-2640` directory; a
second local entry is unnecessary for the clarified GitHub Projects destination.

Follow-up PM Run: `work/sessions/2026-11-25_skill_run_sep2640_xid_progress.md`,
run `35c4eee1-ee94-4990-94a0-093c76fce40e`.
Destination correction Run: `work/sessions/2026-11-25_skill_run_sep2640_github_projects_setup.md`,
run `d3f9f88b-99d3-4318-801d-192676d60675`.


## GitHub Projects mapping

Board: [XRefKit — SEP-2640 MCP Skills Extension](https://github.com/users/synthaicode/projects/7).
The parent reported successful creation/registration and browser readback of all
six issues. Every title explicitly carries `[P0]`; this records the requested
priority in the title, without claiming an unverified custom priority-field value.
Issue bodies contain dependencies, acceptance criteria, local evidence references
and the unmerged/unreleased/undeployed boundary.

| Issue | Local work mapping | Read-back board state |
| --- | --- | --- |
| [#297](https://github.com/synthaicode/XRefKit/issues/297) | AN-01, AN-02: design and compatibility | Done |
| [#298](https://github.com/synthaicode/XRefKit/issues/298) | IM-01, IM-02: implementation | Done |
| [#299](https://github.com/synthaicode/XRefKit/issues/299) | RV-01, IM-03: independent review and fixes | Done |
| [#300](https://github.com/synthaicode/XRefKit/issues/300) | TS-01, TS-02, FX-01–03: full tests and environment repair | Done |
| [#301](https://github.com/synthaicode/XRefKit/issues/301) | XID-01, XID-02: existing XID regression and stdio verification | Done; parent updated issue evidence and read back board status |
| [#302](https://github.com/synthaicode/XRefKit/issues/302) | PM-01, XID-03: coordination and evidence reconciliation | Done |

Recorded board states are the parent's observed snapshot at registration.
A completed local test does not itself update a remote Project field. The parent
must persist/read back any later status transition after receiving final evidence.


## Follow-up: release, existing MCP update and fresh-connection verification

The user now authorizes publishing the SEP-2640 version, updating the running
MCP server and verifying connection plus XID search/retrieval afterward. This
is a new operation phase after merged PR #303 (`035bab59`), not a reinterpretation
of the earlier unreleased/undeployed evidence. Existing completed implementation
and test tasks retain their original scope. No new task below is marked complete.

| ID | Work and responsible role | Depends on | Required acceptance evidence | State |
| --- | --- | --- | --- | --- |
| REL-01 | Parent release operator: release Core 0.7.14 through the existing official workflow | Merged SEP-2640 source; matching version/tag; existing required quality and artifact gates | Exact release commit/tag; successful required release CI; inspected wheel/sdist and official-Skill compatibility; GitHub Release and PyPI 0.7.14; fresh installed-artifact/version verification | In progress: parent committed version change `c402ca5`; publication not yet verified |
| DEPLOY-01 | Parent deployment operator: update the actual existing `xrefkitmcp` host from observed 0.7.9 to verified 0.7.14 | REL-01 verified artifact; actual host/executable/endpoint and supported update/recovery mechanism identified | Prior working state retained as evidence; exact installed artifact/version; actual serving process restarted through its existing mechanism and serving expected endpoint | Pending |
| DEPLOY-VERIFY | Parent/test operator: verify a fresh connection to the updated actual server | DEPLOY-01 | Actual post-update runtime/version; initialization/connection; SEP declaration and required Skill/resource requests; existing XID search and retrieval with canonical content/identity and error/recovery coverage applicable to the live endpoint | Pending |
| REL-CLOSE | Parent coordinator: reconcile release/deployment proof and GitHub Project state | REL-01, DEPLOY-01, DEPLOY-VERIFY | Release/host/test evidence links; explicit limits or failures; operation/PM runtime verification and closure; actual Project/Issue result updates and readback | Pending |

Operational Run: `2a1ff99b-1232-4c9f-b760-4ae24eac81cb`, opened by the parent
for existing official workflow execution and the explicitly identified host.
PM coordination Run: `626bbd77-135a-4ae6-91be-3b293c826a28`,
`work/sessions/2026-11-25_skill_run_sep2640_release_coordination.md`.

The release-planning Skill gate refusal is recorded in
`work/sessions/2026-11-25_session_sep2640_release_route_check.md`; the method
is not executed or copied into these operation items. Required publication
checks remain owned by `.github/workflows/python-package.yml` and
`docs/guides/112_core_skill_release_compatibility.md`.

The exact new GitHub Project/Issue mapping for these four operation items is
pending the parent's registration/readback. Existing issues #297–302 cover the
previous implementation phase; their Done states do not establish release,
deployment or fresh-connection completion. The parent must record new or
explicitly extended item identities and their observed states before REL-CLOSE.

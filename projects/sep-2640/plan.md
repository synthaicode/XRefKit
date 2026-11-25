<!-- xid: 9A62E4B817C3 -->
<a id="xid-9A62E4B817C3"></a>

# SEP-2640 work plan

Revision: 1, 2026-11-25. Highest priority, from the user's instruction.
This task-level breakdown precedes implementation. It is not an estimated
schedule, a detailed Brownfield WBS or a claim that planned work has passed.

## Preflight

- Route: Project Management `progress_rules_setup` and `work_progress_coordination`, then Python implementation, independent review and tests.
- Goal: make the XRefKit MCP Server support SEP-2640 with a precisely stated compatibility boundary.
- Context: dedicated worktree `C:/dev/itsm/XRefKit-sep2640`; initial source `7303a46d`; existing FastMCP server and catalog; observed SDK `mcp==1.28.0`, base protocol `2025-11-25`.
- Constraints: preserve existing tool interfaces and unrelated original-worktree changes; retain current governance authority; do not infer execution authorization from resource inspection.
- Done when: the implemented contract is source-backed, current-diff review is resolved, targeted protocol/regression tests pass, and remaining live-client/deployment limits are named.
- Out of scope: release, deployment, SDK-wide protocol migration unrelated to required compatibility, organization-policy changes, remote board updates and client-host permission implementations.
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
| CL-01 | Parent coordinator: reconcile actual evidence and deliver | TS-02 | Plan updated with artifact links, runtime verification/closure, explicit unverified items, user-facing result | Done; result.md records evidence, limits and closed task runs |

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

See [delivery result](result.md#xid-73D8E921C4A6). All task work items have
recorded outcomes; the follow-up repair below brought the whole quality gate to pass.

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

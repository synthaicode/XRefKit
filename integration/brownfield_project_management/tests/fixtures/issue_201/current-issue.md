<!-- pm-human-view:start -->
**Status.** Waiting for the reviewed [execution contract in #200](https://github.com/synthaicode/XRefKit/issues/200). Implementation of #201 has yet to start.

**Latest change.** #200 has started its approved offline contract work. Its reviewed contract revision is still pending.

**Purpose.** Assemble API context from approved XRefKit startup documents and XID references, within the permitted scope and size limits.

**Acceptance.** Offline tests must trace every included input to its source and version, exclude unauthorized material, and verify that missing, stale, conflicting or oversized required inputs stop assembly. Live API calls and data transfer require separate approval.

**Next.** The #200 owner links the reviewed contract revision. The project owner then confirms the permitted sources, fixture scope, executor and reviewer with the Runtime and deployment/data owners before requesting approval to start #201.

[GitHub Project #3](https://github.com/users/synthaicode/projects/3) · [Prior design, decisions, and evidence](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md)
<!-- pm-human-view:end -->

<a name="purpose"></a>
<a name="proposed-startup-xid-resolution-and-openai-context"></a>
<a name="1-acquire-runtime-and-load-startup"></a>
<a name="2-resolve-selected-references"></a>
<a name="3-assemble-and-check-the-outbound-context"></a>
<a name="4-fixture-acceptance-and-handoff"></a>
<a name="project-management-coordination-record"></a>
<a name="decisions-and-holds"></a>
<a name="work-start-and-verification-conditions"></a>
<a name="handoff-to-later-issues"></a>
<a name="proposed-work-start-and-handoff-evidence"></a>
<a name="planned-work"></a>
<a name="acceptance-and-verification"></a>
<a name="risk"></a>
<a name="source-basis-and-compatibility"></a>
<a name="dependencies-and-handoff"></a>
<a name="codex-development-model-plan"></a>

<details>
<summary>Links to previous sections</summary>

- [Purpose](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#purpose)
- [Proposed startup, XID resolution and OpenAI context](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#proposed-startup-xid-resolution-and-openai-context)
- [1. Acquire Runtime and load startup](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#1-acquire-runtime-and-load-startup)
- [2. Resolve selected references](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#2-resolve-selected-references)
- [3. Assemble and check the outbound context](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#3-assemble-and-check-the-outbound-context)
- [4. Fixture acceptance and handoff](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#4-fixture-acceptance-and-handoff)
- [Project Management coordination record](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#project-management-coordination-record)
- [Decisions and holds](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#decisions-and-holds)
- [Work-start and verification conditions](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#work-start-and-verification-conditions)
- [Handoff to later Issues](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#handoff-to-later-issues)
- [Proposed work-start and handoff evidence](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#proposed-work-start-and-handoff-evidence)
- [Planned work](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#planned-work)
- [Acceptance and verification](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#acceptance-and-verification)
- [Risk](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#risk)
- [Source basis and compatibility](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#source-basis-and-compatibility)
- [Dependencies and handoff](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#dependencies-and-handoff)
- [Codex development model plan](https://github.com/synthaicode/XRefKit/blob/15959f84daa5bf3af9feb46e9acf1e8dfd2f49b8/2026-11-21_original-body.md#codex-development-model-plan)

</details>
"""Exercise the observed #201 shape with separate current records and history."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from html import unescape
from pathlib import Path
import re

import pytest

from test_issue_projection import AtomicHost, Records, sha256
from xrefkit_skills_project_management.issue_projection import (
    IssueArchive,
    IssueSnapshot,
    ProjectionConflict,
    ProjectionError,
    VIEW_END,
)
from xrefkit_skills_project_management.issue_work_record import (
    ArtifactBinding,
    ArtifactReference,
    IssueWorkRecord,
    RecordedDecision,
    apply_current_update,
    embed_work_record,
    prepare_current_create,
    prepare_current_update,
    read_work_record,
    reconcile_current_update,
    resolve_work_handoff,
    work_record_sha256,
)


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixtures/issue_201"
ORIGINAL = ROOT.parents[2] / "sources/web/github.com/synthaicode/XRefKit/issues/201/2026-11-21_original-body.md"
ORIGINAL_HASH = "37ed0a8f8e54cd318e3e71d5365f736ea6c0cf6ee5e9ce7bf910a721f4931fc8"
ISSUE_ID = "synthaicode/XRefKit#201"


def work_fixture():
    # The transport stubs reuse the guarded host interfaces.
    store = Records()
    source = store.authority(
        issue_id=ISSUE_ID, kind="blocked", purpose="", acceptance=(), state="#201 implementation has yet to start.",
        blockers=("#200's offline checks passed; human acceptance of its reviewed contract is pending.",),
        owner="Project owner and Runtime/data owners",
        next_action="Review #201 scope and assign owners once #200 acceptance is recorded",
        required_evidence=("issue-201/design", "issue-201/verification"),
    )
    snapshot = IssueSnapshot(ISSUE_ID, "2026-11-21T06:56:41Z", (FIXTURE / "current-issue.md").read_bytes())
    archive = store.add(
        "archive", "issue-201/archive", "2026-11-21T06:26:35Z",
        IssueArchive(snapshot.issue_id, "2026-11-21T06:26:35Z"),
        content=ORIGINAL.read_bytes(),
    )
    work = IssueWorkRecord(
        snapshot.issue_id,
        "Build bounded API context from existing startup and XID sources.",
        (
            "Resolve startup and selected XIDs from the authorized source and Runtime binding.",
            "Preserve authority, source provenance and work correlation in the bounded manifest.",
            "Keep external transmission and live calls under separate approval.",
        ),
        (
            "Trace every included input to the source, revision and selected scope.",
            "Use offline fixtures to prove limits and egress controls.",
            "Stop on absent, stale, conflicting or oversized required inputs.",
        ),
        ("https://github.com/synthaicode/XRefKit/issues/200",),
        source.project.locator,
        source.pm.locator,
        tuple(
            ArtifactReference(kind, store.add(
                "technical", f"issue-201/{kind}", "fixture-v1",
                ArtifactBinding(snapshot.issue_id, kind, ISSUE_ID, status=status),
                content=(FIXTURE / filename).read_bytes(),
            ))
            for kind, filename, status in (
                ("design", "design-draft.md", "proposed"),
                ("verification", "verification-record.md", "current"),
            )
        ),
        unknowns=("Named implementation and review owners are pending.",),
        stop_conditions=("Await explicit scope-specific authorization before implementation.",
                         "Hold live API calls and real data transfer pending their own authorization."),
        history=(archive,),
    )
    return store, source, snapshot, work


def adapters(store):
    def current(pointer):
        assert pointer.role != "archive", "an Original must not be resolved as a current record"
        return store.resolve(pointer)

    return {"resolve_current": current, "resolve_history": store.resolve}


def discover(snapshot, store, source):
    mapping = {(p.role, p.locator): p for p in (source.project, source.pm)}
    return resolve_work_handoff(snapshot, resolve_management=lambda *key: mapping[key],
                                resolve_current=adapters(store)["resolve_current"])


def plan_migration(store, source, snapshot, work):
    edit_history = store.add(
        "issue_history", "issue-201/edits", snapshot.revision,
        IssueArchive(snapshot.issue_id, snapshot.revision), content=snapshot.body,
    )
    return prepare_current_update(
        snapshot, source.project, source.pm, candidate=work, prior_delivery=store.prior_delivery(snapshot),
        edit_history=edit_history, **adapters(store),
    )


def test_issue_201_current_record_and_brownfield_handoff():
    store, source, snapshot, work = work_fixture()
    plan = plan_migration(store, source, snapshot, work)
    migrated = replace(snapshot, body=plan.replacement)
    handoff = discover(migrated, store, source)
    visible = unescape(migrated.body.split(VIEW_END)[0].decode())

    assert handoff.work == work
    assert handoff.execution.status == "Todo" and handoff.execution.kind == "blocked"
    assert handoff.execution.acceptance == work.acceptance and handoff.execution.purpose == work.purpose
    assert handoff.decision_request is None and handoff.decisions == ()
    assert work.dependencies == ("https://github.com/synthaicode/XRefKit/issues/200",)
    assert [result.value.kind for result in handoff.artifacts] == ["design", "verification"]
    assert [result.value.status for result in handoff.artifacts] == ["proposed", "current"]
    assert all(sha256(result.content) != ORIGINAL_HASH for result in handoff.artifacts)
    assert sha256(ORIGINAL.read_bytes()) == ORIGINAL_HASH
    assert store.resolve(work.history[0]).content == ORIGINAL.read_bytes()
    assert len(re.findall(rb'<a name="[^"]+"></a>', migrated.body)) == 17
    assert migrated.body.endswith(snapshot.body.partition(VIEW_END)[2])
    for phrase in ("#201 implementation has yet to start", "#200's offline checks passed",
                   "human acceptance", "Technical design", "proposed", "Issue history snapshot", "Next."):
        assert phrase in visible
    assert "Decision needed." not in visible and "Source acquisition" not in visible
    assert len(visible) < 1500
    replay = prepare_current_update(migrated, source.project, source.pm, **adapters(store))
    assert not replay.changed and replay.replacement == migrated.body


def test_creation_carries_exact_work_requirements_and_rejects_a_summary_only_handoff():
    store, source, snapshot, work = work_fixture()
    with pytest.raises(ProjectionError, match="work record is absent"):
        discover(snapshot, store, source)
    plan = prepare_current_create(work, source.project, source.pm, **adapters(store))
    writer = AtomicHost(source.project)
    assert apply_current_update(plan, writer, **adapters(store)).changed
    assert read_work_record(writer.issue) == work
    assert apply_current_update(plan, writer, **adapters(store)).changed is False
    assert writer.writes == 1


def test_current_handoff_does_not_need_to_read_an_unavailable_history_snapshot():
    store, source, snapshot, work = work_fixture()
    plan = plan_migration(store, source, snapshot, work)
    del store.records[work.history[0]]
    result = discover(replace(snapshot, body=plan.replacement), store, source)
    assert result.work.history == work.history
    assert len(result.artifacts) == 2 and result.history_links == ()
    with pytest.raises(ProjectionError, match="archive: record could not be resolved"):
        apply_current_update(plan, AtomicHost(source.project, snapshot), **adapters(store))


@pytest.mark.parametrize("problem", ["missing", "revision", "digest", "wrong_work", "history"])
def test_required_current_artifact_never_falls_back_to_original(problem):
    store, source, snapshot, work = work_fixture()
    current = work.artifacts[0].record
    if problem == "history":
        wrong = replace(work.history[0], role="technical", locator="different-path")
        work = replace(work, artifacts=(ArtifactReference("design", wrong), *work.artifacts[1:]))
    else:
        found = store.records[current]
        if problem == "missing":
            del store.records[current]
        elif problem == "revision":
            store.records[current] = replace(found, revision="different-current-revision")
        elif problem == "digest":
            store.records[current] = replace(found, content=b"unverified draft")
        else:
            store.records[current] = replace(found, value=replace(found.value, issue_id="another"))
    with pytest.raises(ProjectionError):
        plan_migration(store, source, snapshot, work)


def test_approval_is_separate_from_execution_and_fixture_results():
    store, source, snapshot, work = work_fixture()
    pointer = store.add(
        "decision", "issue-201/decision/test-only", "v1",
        RecordedDecision(snapshot.issue_id, "Proposed offline check acceptance", "held", "Project owner"),
    )
    plan = plan_migration(store, source, snapshot, replace(work, decisions=(pointer,)))
    handoff = discover(replace(snapshot, body=plan.replacement), store, source)
    assert handoff.execution.kind == "blocked"
    assert handoff.decisions[0].value.outcome == "held"
    assert handoff.decision_request is None


def test_refuses_unverified_native_history_and_preserves_human_edits():
    store, source, snapshot, work = work_fixture()
    plan = plan_migration(store, source, snapshot, work)
    updated = replace(snapshot, body=plan.replacement)
    assert updated.body.endswith(snapshot.body.partition(VIEW_END)[2])
    edited = replace(snapshot, body=snapshot.body.replace(b"**Status.**", b"**Manually corrected.**"))
    with pytest.raises(ProjectionError, match="differs from the prior delivery"):
        prepare_current_update(edited, source.project, source.pm, candidate=work,
                               prior_delivery=store.prior_delivery(snapshot), **adapters(store))
    with pytest.raises(ProjectionError, match="exact prior Issue"):
        prepare_current_update(snapshot, source.project, source.pm, candidate=work,
                               prior_delivery=store.prior_delivery(snapshot), **adapters(store))


def test_artifact_write_failure_and_lost_issue_response_use_exact_readback():
    store, source, snapshot, work = work_fixture()
    plan = plan_migration(store, source, snapshot, work)
    writer = AtomicHost(source.project, snapshot)
    pointer = work.artifacts[0].record
    record = store.records.pop(pointer)
    with pytest.raises(ProjectionError, match="could not be resolved"):
        apply_current_update(plan, writer, **adapters(store))
    assert writer.writes == 0
    store.records[pointer] = record
    assert reconcile_current_update(plan, writer.issue, **adapters(store)) == "retry"
    writer.fail_after_write = True
    with pytest.raises(ProjectionError, match="outcome is unknown"):
        apply_current_update(plan, writer, **adapters(store))
    assert reconcile_current_update(plan, writer.issue, **adapters(store)) == "applied"
    writer.fail_after_write = False
    assert apply_current_update(plan, writer, **adapters(store)).changed is False
    assert writer.writes == 1


def test_concurrent_ai_candidates_and_manual_edit_require_reconciliation():
    store, source, snapshot, work = work_fixture()
    plans = (plan_migration(store, source, snapshot, work),
             plan_migration(store, source, snapshot, replace(work, requirements=("Conflicting edit",))))
    writer = AtomicHost(source.project, snapshot)

    def apply(plan):
        try:
            return apply_current_update(plan, writer, **adapters(store)).changed
        except ProjectionConflict:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(apply, plans)) == [False, True]
    assert writer.writes == 1
    writer.issue = replace(writer.issue, revision="human-edit", body=writer.issue.body + b"Human text.")
    with pytest.raises(ProjectionConflict, match="diverged"):
        reconcile_current_update(plans[0], writer.issue, **adapters(store))


def test_changed_artifact_during_write_is_not_reported_as_success():
    store, source, snapshot, work = work_fixture()
    plan = plan_migration(store, source, snapshot, work)

    class ChangedArtifactHost(AtomicHost):
        def compare_and_swap(self, plan):
            receipt = super().compare_and_swap(plan)
            store.records.pop(work.artifacts[0].record)
            return receipt

    writer = ChangedArtifactHost(source.project, snapshot)
    with pytest.raises(ProjectionError, match="Issue write confirmed but current records changed"):
        apply_current_update(plan, writer, **adapters(store))
    assert writer.writes == 1


def test_human_edit_and_marker_text_are_round_tripped_without_injection():
    store, source, snapshot, work = work_fixture()
    marker = "<!-- pm-work-record:v1 -->"
    work = replace(work, requirements=(marker,))
    modified = embed_work_record(snapshot.body + b"\nHuman comment.", work)
    assert read_work_record(replace(snapshot, body=modified)) == work
    assert modified.endswith(b"Human comment.")
    assert modified.count(b"<!-- pm-work-record:") == 1
    with pytest.raises(ProjectionError, match="one supported work record"):
        read_work_record(replace(snapshot, body=modified + b"\n" + marker.encode()))


def test_revision_change_uses_pinned_current_requirements_and_reports_only_difference():
    store, source, snapshot, work = work_fixture()
    current = replace(snapshot, revision="migration", body=plan_migration(store, source, snapshot, work).replacement)
    previous = discover(current, store, source)
    changed = replace(work, requirements=(*work.requirements, "Record fixture input provenance."))
    history = store.add(
        "issue_history", "issue-201/edits", current.revision,
        IssueArchive(current.issue_id, current.revision), content=current.body,
    )
    inputs = {
        "candidate": changed, "previous": previous, "prior_delivery": store.prior_delivery(current),
        "edit_history": history, **adapters(store),
    }
    with pytest.raises(ProjectionError, match="work record differs"):
        prepare_current_update(current, source.project, source.pm, **inputs)
    plan = prepare_current_update(current, source.project, source.pm,
                                  expected_work_record_sha256=work_record_sha256(current), **inputs)
    assert b"Changed since the previous report: requirements." in plan.replacement
    assert read_work_record(replace(current, body=plan.replacement)) == changed

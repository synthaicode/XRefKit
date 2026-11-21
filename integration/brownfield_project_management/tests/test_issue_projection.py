"""Offline regression tests for PM Issue projection with an atomic host stub."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
import hashlib
from html import unescape
import json
from threading import Barrier, Lock

import pytest

from xrefkit_skills_project_management.issue_projection import (
    DecisionOption,
    DecisionRequest,
    IssueArchive,
    IssueSnapshot,
    LegacyMigration,
    ManagedDelivery,
    MigrationAuthorization,
    PMState,
    ProjectState,
    ProjectionConflict,
    ProjectionError,
    ProjectionInput,
    Readback,
    RecordPointer,
    ReviewResult,
    VIEW_END,
    VIEW_START,
    WriteReceipt,
    apply_update,
    managed_view_sha256,
    prepare_create,
    prepare_update,
    render_view,
)


def sha256(content):
    return hashlib.sha256(content).hexdigest()


class Records:
    def __init__(self):
        self.records = {}

    def add(self, role, locator, revision, value, *, content=None):
        if content is None:
            content = json.dumps(asdict(value), sort_keys=True).encode()
        entry = RecordPointer(role, locator, revision, sha256(content))
        self.records[entry] = Readback(
            locator, revision, content, f"https://records.example/{locator}/{revision}", value,
        )
        return entry

    def resolve(self, pointer):
        return self.records[pointer]

    def authority(self, *, pm_revision="pm-1", project_revision="project-1", status="Todo", **overrides):
        project = self.add("project", "project/item", project_revision, ProjectState("issue", "item", status))
        fields = {
            "kind": "progress",
            "state": "Review the affected records",
            "purpose": "Produce the approved offline contract",
            "acceptance": ("Trace the verified requirements",),
            "owner": "Maintainer",
            "next_action": "Read the current source evidence",
        }
        fields.update(overrides)
        pm = self.add("pm", "pm", pm_revision, PMState("issue", "item", project_revision, status, **fields))
        return ProjectionInput(project, pm)

    def preserved_issue(self, issue):
        return self.add(
            "archive", "archive", issue.revision, IssueArchive(issue.issue_id, issue.revision, issue.fragments),
            content=issue.body,
        )

    def prior_delivery(self, issue):
        return self.add(
            "delivery", "delivery", issue.revision,
            ManagedDelivery(issue.issue_id, managed_view_sha256(issue.body)),
        )


class AtomicHost:
    """Tests the contract with a lock held across both comparisons and any write."""

    supports_atomic_issue_and_project_compare = True

    def __init__(self, project, snapshot=None):
        self.project = project
        self.project_item_id = "item"
        self.project_status = "Todo"
        self.issue = snapshot
        self.writes = 0
        self.fail_after_write = False
        self.lock = Lock()

    def compare_and_swap(self, plan):
        with self.lock:
            return self._compare_and_swap(plan)

    def _compare_and_swap(self, plan):
        if (plan.project, plan.project_item_id, plan.project_status) != (
            self.project, self.project_item_id, self.project_status,
        ):
            return None
        if self.issue is not None and self.issue.issue_id != plan.issue_id:
            return None
        if self.issue is not None and self.issue.body == plan.replacement:
            return self._receipt(False)
        if self.issue is None:
            if (plan.issue_revision, plan.issue_sha256) != (None, None):
                return None
        elif (plan.issue_revision, plan.issue_sha256) != (
            self.issue.revision, sha256(self.issue.body),
        ):
            return None
        self.writes += 1
        self.issue = IssueSnapshot(plan.issue_id, f"committed-{self.writes}", plan.replacement)
        if self.fail_after_write:
            raise OSError("reply was lost")
        return self._receipt(True)

    def _receipt(self, changed):
        return WriteReceipt(
            self.issue.issue_id, self.issue.revision, self.project.revision, sha256(self.issue.body), changed,
        )


def request(*, pm_revision="pm-1", **overrides):
    fields = {
        "actionable": True,
        "question": "Approve the fixture scope?",
        "owner": "Requester",
        "enables": "Accept the defined scope",
        "excluded": "Implementation start and live effects",
        "deferred": "Scope stays open",
        "why_now": "The source review is complete",
        "options": (DecisionOption("Approve", "Accept the scope"), DecisionOption("Amend", "Review the revised text")),
        "recommendation": "Approve",
        "risks": ("Transport remains unverified",),
    }
    fields.update(overrides)
    return DecisionRequest("issue", pm_revision, **fields)


def test_projected_creation_has_expected_absence_and_uses_atomic_host():
    records = Records()
    source = records.authority(required_evidence=("technical",))
    evidence = records.add("technical", "technical", "source-1", None, content=b"immutable detail")
    view = render_view(replace(source, evidence=(evidence,)), records.resolve)
    assert view.body.startswith(VIEW_START)
    assert view.body.endswith(VIEW_END + b"\n")
    assert b"Previous report basis is unknown." in view.body
    assert b"Technical evidence 1" in view.body
    assert b"immutable detail" not in view.body
    plan = prepare_create(view)
    assert plan.changed and plan.issue_revision is None and plan.issue_sha256 is None
    writer = AtomicHost(source.project)
    assert apply_update(plan, writer).changed
    assert not apply_update(plan, writer).changed
    assert writer.writes == 1


def test_existing_issue_with_different_body_refuses_new_creation():
    records = Records()
    source = records.authority()
    plan = prepare_create(render_view(source, records.resolve))
    writer = AtomicHost(source.project, IssueSnapshot("issue", "existing", b"existing human Issue"))
    with pytest.raises(ProjectionConflict):
        apply_update(plan, writer)
    assert writer.writes == 0


@pytest.mark.parametrize("fault", ["foreign item", "foreign issue", "status", "project revision"])
def test_authoritative_project_mismatch_stops_projection(fault):
    records = Records()
    source = records.authority()
    value = records.resolve(source.pm).value
    overrides = {
        "foreign item": {"item_id": "unexpected"},
        "foreign issue": {"issue_id": "unexpected"},
        "status": {"status": "unexpected"},
        "project revision": {"project_revision": "stale"},
    }
    pm = records.add("pm", "pm", "pm-1", replace(value, **overrides[fault]))
    with pytest.raises(ProjectionError, match="match authoritative Project"):
        render_view(replace(source, pm=pm), records.resolve)


@pytest.mark.parametrize("fault", ["missing", "hash", "revision", "link", "wrong role"])
def test_required_technical_pointer_and_readback_are_verified(fault):
    records = Records()
    source = records.authority(required_evidence=("technical",))
    pointer = records.add("technical", "technical", "source-1", None, content=b"known detail")
    read = records.resolve(pointer)
    if fault == "missing":
        expected = "required technical"
    else:
        source = replace(source, evidence=(pointer,))
        expected = {
            "hash": "SHA-256",
            "revision": "identity or revision",
            "link": "HTTPS",
            "wrong role": "incorrect record role",
        }[fault]
        if fault == "hash":
            records.records[pointer] = replace(read, content=b"tampered")
        elif fault == "revision":
            records.records[pointer] = replace(read, revision="other")
        elif fault == "link":
            records.records[pointer] = replace(read, link="javascript:invalid")
        elif fault == "wrong role":
            source = replace(source, evidence=(replace(pointer, role="pm"),))
    with pytest.raises(ProjectionError, match=expected):
        render_view(source, records.resolve)


def test_change_comparison_uses_previous_revision_and_stays_current_only():
    records = Records()
    previous = records.authority(next_action="Obtain the earlier answer")
    current = records.authority(
        pm_revision="pm-2", project_revision="project-2",
        owner="Review owner", next_action="Check the exact package", deadline="2026-12-01",
    )
    view = render_view(current, records.resolve, previous=previous)
    assert b"Changed since the previous report: owner, next action, deadline." in view.body
    assert b"Previous PM record" in view.body
    assert b"Obtain the earlier answer" not in view.body
    identical_current = records.authority(
        pm_revision="pm-3", project_revision="project-3", next_action="Obtain the earlier answer",
    )
    assert b"No material change" in render_view(identical_current, records.resolve, previous=previous).body
    records.records.pop(previous.pm)
    with pytest.raises(ProjectionError, match="could not be resolved"):
        render_view(current, records.resolve, previous=previous)


@pytest.mark.parametrize("kind", ["blocked", "review", "progress"])
def test_presentation_tracks_blocked_review_or_progress_without_implying_approval(kind):
    records = Records()
    source = records.authority(
        kind=kind, blockers=("The preceding work has not started",) if kind == "blocked" else (),
        review=ReviewResult("Passed for sample only", "Fixture evidence", ("No live proof",)) if kind == "progress" else None,
    )
    text = render_view(source, records.resolve).body.decode()
    assert ("Blockers." in text) == (kind == "blocked")
    assert ("Review result pending." in text) == (kind == "review")
    assert ("Passed for sample only" in text) == (kind == "progress")
    assert "Decision needed." not in text


def test_actionable_human_request_contains_bound_scope_options_and_recommendation():
    records = Records()
    source = records.authority(decision_locator="decision")
    decision = records.add("decision", "decision", "decision-1", request())
    view = render_view(replace(source, decision=decision), records.resolve)
    text = unescape(view.body.decode())
    for expected in (
        "Decision needed.", "Decision owner: Requester", "Why now: The source review is complete",
        "Enables: Accept the defined scope", "Outside scope: Implementation start and live effects",
        "If deferred: Scope stays open", "Amend: Review the revised text",
        "Recommendation: Approve", "Transport remains unverified", "Decision scope",
    ):
        assert expected in text


def test_blocked_work_keeps_staged_start_out_of_the_view_and_allows_independent_decisions():
    records = Records()
    source = records.authority(kind="blocked", blockers=("Upstream work",), decision_locator="decision")
    pending = records.add("decision", "decision", "decision-pending", request(actionable=False))
    assert b"Decision needed." not in render_view(replace(source, decision=pending), records.resolve).body
    invalid = records.add("decision", "decision", "decision-blocked", request())
    with pytest.raises(ProjectionError, match="apply while work is blocked"):
        render_view(replace(source, decision=invalid), records.resolve)
    independent = records.add("decision", "decision", "decision-independent", request(available_while_blocked=True))
    assert b"Decision needed." in render_view(replace(source, decision=independent), records.resolve).body


def test_stale_or_unavailable_explicit_decision_is_rejected():
    records = Records()
    source = records.authority(pm_revision="pm-2", decision_locator="decision")
    with pytest.raises(ProjectionError, match="linked human judgment request is missing"):
        render_view(source, records.resolve)
    stale = records.add("decision", "decision", "decision-1", request(pm_revision="pm-1"))
    with pytest.raises(ProjectionError, match="does not apply"):
        render_view(replace(source, decision=stale), records.resolve)


def test_untrusted_record_text_stays_in_inline_markdown_and_view_size_is_bounded():
    records = Records()
    supplied = "@someone \n<!-- pm-human-view:end -->\n[link](javascript:dead) <tag> https://untrusted.invalid"
    source = records.authority(purpose=supplied)
    view = render_view(source, records.resolve)
    raw = view.body.decode()
    assert raw.count(VIEW_END.decode()) == 1
    for token in ("@someone", "<tag>", "[link]", "https://untrusted.invalid"):
        assert token not in raw
        assert token in unescape(raw)
    oversized = records.authority(pm_revision="large", purpose="a" * 9000)
    with pytest.raises(ProjectionError, match="display limit"):
        render_view(oversized, records.resolve)


def prepare_fixture(records, *, prefix=b"Human plan\r\n\r\n", suffix=b"\r\n\r\nHuman edits here\r\n"):
    project = records.authority().project
    initial = records.authority()
    original_view = render_view(initial, records.resolve)
    original = IssueSnapshot("issue", "old-issue", prefix + original_view.body[:-1].replace(b"\n", b"\r\n") + suffix)
    source = records.authority(pm_revision="pm-2", state="Ready for independent review")
    view = render_view(source, records.resolve)
    archive = records.preserved_issue(original)
    delivery = records.prior_delivery(original)
    plan = prepare_update(original, view, archive=archive, prior_delivery=delivery, resolve=records.resolve)
    return project, original, view, archive, delivery, plan


def test_update_preserves_outside_bytes_and_never_appends_managed_history():
    records = Records()
    prefix = b"Human intro\n\n"
    suffix = b"\n\nOutside record remains\n"
    project, original, view, _, _, plan = prepare_fixture(records, prefix=prefix, suffix=suffix)
    assert plan.replacement == prefix + view.body[:-1].replace(b"\n", b"\r\n") + suffix
    assert plan.replacement.count(VIEW_START) == plan.replacement.count(VIEW_END) == 1
    writer = AtomicHost(project, original)
    assert apply_update(plan, writer).changed
    assert prepare_update(writer.issue, view, resolve=records.resolve).changed is False


def test_regular_overwrite_requires_exact_archive_and_unchanged_prior_managed_delivery():
    records = Records()
    _, original, view, archive, delivery, _ = prepare_fixture(records)
    with pytest.raises(ProjectionError, match="prior Human View delivery"):
        prepare_update(original, view, archive=archive, resolve=records.resolve)
    with pytest.raises(ProjectionError, match="exact prior Issue"):
        prepare_update(original, view, prior_delivery=delivery, resolve=records.resolve)
    changed = replace(original, revision="edited", body=original.body.replace(b"Review the affected records", b"Human correction"))
    changed_archive = records.preserved_issue(changed)
    with pytest.raises(ProjectionError, match="differs from the prior delivery"):
        prepare_update(
            changed, view, archive=changed_archive, prior_delivery=delivery, resolve=records.resolve,
        )
    under_archived = records.add(
        "archive", "archive-other", "old-issue", IssueArchive("issue", "old-issue"), content=original.body[:-1],
    )
    with pytest.raises(ProjectionError, match="complete prior"):
        prepare_update(original, view, archive=under_archived, prior_delivery=delivery, resolve=records.resolve)


@pytest.mark.parametrize("body", [VIEW_START, VIEW_END + b"\n" + VIEW_START, VIEW_START + b"\n" + VIEW_END * 2])
def test_malformed_or_repeated_markers_refuse(body):
    records = Records()
    view = render_view(records.authority(), records.resolve)
    with pytest.raises(ProjectionError, match="well-formed"):
        prepare_update(IssueSnapshot("issue", "tip", body), view, resolve=records.resolve)


def test_legacy_migration_reads_exact_archive_and_verified_complete_alias_plan():
    records = Records()
    source = records.authority()
    view = render_view(source, records.resolve)
    body = b"## Earlier decision\n\nKeep the full evidence.\n"
    issue = IssueSnapshot("issue", "legacy", body, ("earlier-decision",))
    saved = records.preserved_issue(issue)
    auth = records.add(
        "migration_authorization", "human-approval", "1",
        MigrationAuthorization("issue", "legacy", sha256(body), "Requester", issue.fragments),
    )
    migration = LegacyMigration(auth, issue.fragments)
    with pytest.raises(ProjectionError, match="separately authorized"):
        prepare_update(issue, view, archive=saved, resolve=records.resolve)
    for snapshot, proposed_migration in (
        (replace(issue, fragments=None), migration),
        (issue, replace(migration, aliases=())),
        (replace(issue, fragments=("unverified",)), migration),
    ):
        with pytest.raises(ProjectionError, match="complete old fragment aliases"):
            prepare_update(snapshot, view, archive=saved, migration=proposed_migration, resolve=records.resolve)
    proposal = prepare_update(issue, view, archive=saved, migration=migration, resolve=records.resolve)
    assert b'<a name="earlier-decision"></a>' in proposal.replacement
    assert b"https://records.example/archive/legacy#earlier-decision" in proposal.replacement
    assert records.resolve(saved).content == body
    host = AtomicHost(source.project, issue)
    assert apply_update(proposal, host).changed


@pytest.mark.parametrize("what_changes", ["issue", "project"])
def test_revision_conflict_refuses_write(what_changes):
    records = Records()
    project, original, _, _, _, plan = prepare_fixture(records)
    writer = AtomicHost(project, original)
    if what_changes == "issue":
        writer.issue = replace(original, body=original.body + b"new human edit", revision="latest")
    else:
        writer.project = replace(writer.project, revision="newer")
    with pytest.raises(ProjectionConflict):
        apply_update(plan, writer)
    assert writer.writes == 0


def test_two_candidates_cannot_both_commit_against_one_original_issue_revision():
    records = Records()
    project, original, _, archive, delivery, one = prepare_fixture(records)
    another_source = records.authority(pm_revision="pm-3", state="Contradictory candidate view")
    another = render_view(another_source, records.resolve)
    two = prepare_update(original, another, archive=archive, prior_delivery=delivery, resolve=records.resolve)
    writer = AtomicHost(project, original)
    start = Barrier(2)

    def attempt(plan):
        start.wait(timeout=10)
        try:
            return apply_update(plan, writer).changed
        except ProjectionConflict:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, [one, two]))
    assert sorted(results) == [False, True]
    assert writer.writes == 1


def test_atomic_writer_required_and_lost_receipt_can_be_reconciled_without_rewrite():
    records = Records()
    project, original, _, _, _, plan = prepare_fixture(records)
    writer = AtomicHost(project, original)
    writer.supports_atomic_issue_and_project_compare = False
    with pytest.raises(ProjectionError, match="cannot enforce atomic"):
        apply_update(plan, writer)
    assert writer.writes == 0
    writer.supports_atomic_issue_and_project_compare = True
    writer.fail_after_write = True
    with pytest.raises(ProjectionError, match="outcome is unknown"):
        apply_update(plan, writer)
    assert writer.issue.body == plan.replacement
    assert not apply_update(plan, writer).changed
    assert writer.writes == 1


def test_authorized_legacy_extraction_can_remove_details_from_a_marked_issue():
    records = Records()
    source = records.authority()
    view = render_view(source, records.resolve)
    details = b"\n<details>\n\n## Earlier decision\n\nEvidence.\n\n</details>\n"
    issue = IssueSnapshot("issue", "legacy", view.body + details, ("earlier-decision",))
    archive = records.preserved_issue(issue)
    auth = records.add(
        "migration_authorization", "human-approval", "1",
        MigrationAuthorization("issue", "legacy", sha256(issue.body), "Requester", issue.fragments),
    )
    assert prepare_update(issue, view, resolve=records.resolve).replacement == issue.body
    plan = prepare_update(
        issue, view, archive=archive, migration=LegacyMigration(auth, issue.fragments),
        resolve=records.resolve,
    )
    host = AtomicHost(source.project, issue)
    assert apply_update(plan, host).changed
    assert not apply_update(plan, host).changed
    assert not prepare_update(host.issue, view, resolve=records.resolve).changed
    assert details not in host.issue.body
    assert records.resolve(archive).content.endswith(details)

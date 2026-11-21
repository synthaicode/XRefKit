"""Replay the observed #201 inputs against an offline, immutable record resolver."""
from dataclasses import asdict
import hashlib
from html import unescape
import json
from pathlib import Path
import re

from xrefkit_skills_project_management.issue_projection import (
    IssueArchive,
    IssueSnapshot,
    LegacyMigration,
    MigrationAuthorization,
    PMState,
    ProjectState,
    ProjectionInput,
    Readback,
    RecordPointer,
    prepare_update,
    render_view,
)


_SOURCE = (
    Path(__file__).resolve().parents[3]
    / "sources/web/github.com/synthaicode/XRefKit/issues/201/2026-11-21_original-body.md"
)
_SOURCE_DIGEST = "37ed0a8f8e54cd318e3e71d5365f736ea6c0cf6ee5e9ce7bf910a721f4931fc8"


def issue_201_fixture():
    """Normalize the recorded planning facts; the fixture never resolves the network."""
    source = _SOURCE.read_bytes()
    assert hashlib.sha256(source).hexdigest() == _SOURCE_DIGEST
    issue = "synthaicode/XRefKit#201"
    item = "project-3/issue-201"
    project_revision = "fixture-project-201-readback"
    snapshot = ProjectState(issue_id=issue, item_id=item, status="Todo")
    progress = PMState(
        issue_id=issue, item_id=item, project_revision=project_revision,
        status="Todo", kind="blocked", state="#200の契約確定待ち。#201の実装は未着手です。",
        purpose="API向けに、許可された情報だけでコンテキストを構築する。",
        acceptance=(
            "情報源と版を追跡でき、許可された範囲と上限を守る。必須情報が欠落・失効した場合は停止する。",
        ),
        owner="プロジェクト責任者とRuntime・データ管理の各担当（担当者名は未確定）",
        next_action="#200の契約確定後、実装範囲・必要な承認・受入条件を確認する。",
        blockers=("#200の契約が未確定のため、現時点では実装開始の判断を求めません。",),
        risks=("実データの外部送信とAPI実行には、別途承認が必要です。",),
        required_evidence=("fixture/201/technical",),
    )
    rows = {}

    def record(role, revision, content, link, value):
        locator = f"fixture/201/{role}"
        pointer = RecordPointer(
            role=role, locator=locator, revision=revision,
            sha256=hashlib.sha256(content).hexdigest(),
        )
        rows[locator] = Readback(
            locator=locator, revision=revision, content=content, link=link, value=value,
        )
        return pointer

    project = record(
        "project", project_revision, json.dumps(asdict(snapshot)).encode(),
        "https://github.com/users/synthaicode/projects/3", snapshot,
    )
    pm = record(
        "pm", "fixture-pm-201-v1", json.dumps(asdict(progress), ensure_ascii=False).encode(),
        "https://records.example.test/201/management/v1", progress,
    )
    technical = record(
        "technical", "2026-11-21T06:26:35Z", source,
        "https://records.example.test/201/technical/original", None,
    )
    return ProjectionInput(project=project, pm=pm, evidence=(technical,)), rows


def test_issue_201_generates_a_compact_view_from_separate_records():
    inputs, rows = issue_201_fixture()

    def resolve(pointer):
        return rows[pointer.locator]

    view = render_view(inputs, resolve)
    body = unescape(view.body.decode("utf-8"))
    assert "#200の契約確定待ち" in body and "実装は未着手" in body
    assert "#200の契約確定後" in body and "担当者名は未確定" in body
    assert "https://records.example.test/201/technical/original" in body
    assert "https://records.example.test/201/management/v1" in body
    assert "**Decision needed.**" not in body
    assert "<details>" not in body and "### 1. Acquire Runtime" not in body
    assert len(view.body) < len(_SOURCE.read_bytes()) // 4
    assert view.body == render_view(inputs, resolve).body
    assert rows[inputs.evidence[0].locator].content == _SOURCE.read_bytes()


def test_issue_201_copy_migration_keeps_source_and_is_repeatable():
    inputs, rows = issue_201_fixture()
    source = _SOURCE.read_bytes()
    # A fixture inventory for this copy's simple ASCII headings. A production
    # host must verify the actual rendered anchors and archive destinations.
    headings = re.findall(r"^#{2,3} +(.+)$", source.decode("utf-8"), re.MULTILINE)
    aliases = tuple(re.sub(r"[^a-z0-9 -]", "", title.lower()).replace(" ", "-")
                    for title in headings)
    assert len(aliases) == len(set(aliases)) == 17
    revision = "2026-11-21T06:26:35Z"
    issue = IssueSnapshot("synthaicode/XRefKit#201", revision, source, aliases)
    archive = RecordPointer("archive", "fixture/201/archive", revision, _SOURCE_DIGEST)
    archive_url = "https://records.example.test/201/issue-history/original"
    rows[archive.locator] = Readback(
        archive.locator, revision, source, archive_url,
        IssueArchive(issue.issue_id, revision, aliases),
    )
    authorization_value = MigrationAuthorization(
        issue.issue_id, revision, _SOURCE_DIGEST, "offline-fixture-owner", aliases,
    )
    authorization_bytes = json.dumps(asdict(authorization_value)).encode()
    authorization = RecordPointer(
        "migration_authorization", "fixture/201/migration-approval", "fixture-only",
        hashlib.sha256(authorization_bytes).hexdigest(),
    )
    rows[authorization.locator] = Readback(
        authorization.locator, authorization.revision, authorization_bytes,
        "https://records.example.test/201/approval/fixture-only", authorization_value,
    )

    def resolve(pointer):
        return rows[pointer.locator]

    view = render_view(inputs, resolve)
    migration = LegacyMigration(authorization, aliases)
    plan = prepare_update(issue, view, archive=archive, resolve=resolve, migration=migration)
    new_body = plan.replacement.decode("utf-8")
    assert "<details>" not in new_body and "## Proposed startup" not in new_body
    for alias in aliases:
        assert f'{archive_url}#{alias}' in new_body
    assert rows[archive.locator].content == _SOURCE.read_bytes()
    assert plan == prepare_update(issue, view, archive=archive, resolve=resolve, migration=migration)

    migrated = IssueSnapshot(issue.issue_id, "fixture-second-revision", plan.replacement)
    replay = prepare_update(migrated, view, resolve=resolve)
    assert replay.replacement == migrated.body and not replay.changed

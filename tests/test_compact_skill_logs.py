import pytest

from test_skill_definition_runtime import _open_run
from test_subagent_startup import command
from xrefkit.skillrun import _section_body


@pytest.mark.parametrize("legacy", [False, True])
def test_compact_and_legacy_logs_keep_evidence_through_closure(tmp_path, legacy):
    _, log = _open_run(tmp_path)
    text = log.read_text(encoding="utf-8")
    marker = "- log_format: `compact_v1`\n- operating_contract_xid: `B7A2C94F0E61`\n"
    assert marker in text
    assert "- rule:" not in text
    if legacy:
        text = text.replace(marker, "", 1)
        text = text.replace(
            "## Token Usage\n\n", "## Token Usage\n\n- rule: legacy token guidance\n", 1
        )
        log.write_text(text, encoding="utf-8")

    def update(*args):
        code, output = command("skill", *args, "--log", str(log))
        assert code == 0, output

    # User data that resembles omitted template lines must survive updates.
    note = "literal evidence\n- rule: user supplied detail\n- log_format: `compact_v1`"
    update("tokens", "--input", "120", "--output", "30", "--note", note)
    update("workitem", "--item", "WI-1", "--completion-criterion", "report covers target", "--status", "done", "--role", "definition_sample:executor")
    for artifact_id, kind, target in (
        ("OUT", "output", "report.md"), ("EVIDENCE", "evidence", "tests passed"),
    ):
        update("artifact", "--artifact", artifact_id, "--kind", kind, "--target", target,
               "--item", "WI-1", "--status", "done", "--role", "definition_sample:executor")
    update("concern", "--concern", "RISK", "--kind", "risk", "--status", "resolved",
           "--text", "Compatibility checked", "--target", "tests passed", "--role", "definition_sample:executor")
    for phase in ("startup", "planning", "execution"):
        update("phase", "--phase", phase, "--status", "done", "--role", "definition_sample:executor")
    update("verify")
    update("phase", "--phase", "handoff", "--status", "done", "--role", "definition_sample:handoff_owner")
    update("close")
    text = log.read_text(encoding="utf-8")
    assert note in text
    assert "Compatibility checked" in text
    assert ("- rule: each work item requires" in text) is legacy
    assert ("- rule: outputs, evidence" in text) is legacy
    assert ("- rule: unknowns, missing evidence" in text) is legacy
    assert "- total: `150`" in text
    assert "- target: report.md" in text or "target=`report.md`" in text
    assert "## Closure Gate\n\n- status: `done`" in text
    assert ("- rule: record tokens consumed" in text) is legacy
    for section in ("Worklist", "Quality Gate"):
        body, _, _ = _section_body(text, section)
        for heading in ("Status", "Result", "Checks Performed", "Evidence", "Open Items", "Handoff"):
            assert f"### {heading}\n" in body


def test_workflow_log_keeps_existing_format(tmp_path):
    log = tmp_path / "work" / "workflow.md"
    code, output = command(
        "workflow", "run", "--root", str(tmp_path), "--task", "Inspect target",
        "--completion-condition", "Target inspected", "--out", str(log),
    )
    assert code == 0, output
    original = log.read_text(encoding="utf-8")
    assert "log_format" not in original
    assert "- rule: do not treat the instruction" in original
    code, output = command("skill", "tokens", "--log", str(log), "--total", "20")
    assert code == 0, output
    assert "- rule: record tokens consumed" in log.read_text(encoding="utf-8")


def test_compaction_only_removes_template_rules_and_preserves_task(monkeypatch, tmp_path):
    from xrefkit import skillrun

    render = skillrun._render_log
    captured = {}

    def capture(**kwargs):
        captured.update(kwargs)
        return render(**kwargs)

    monkeypatch.setattr(skillrun, "_render_log", capture)
    _open_run(tmp_path)
    captured["task"] = "Keep these literal lines:\n- rule: task requirement\n- log_format: `other`"
    compact = render(**captured)
    verbose = render(**{**captured, "compact": False})
    assert captured["task"] in compact
    assert len(compact.encode("utf-8")) < len(verbose.encode("utf-8")) * 0.8

    # Every non-boilerplate line survives in the same order, including reports.
    def data_lines(text):
        return [line for line in text.splitlines() if line and not line.startswith((
            "- rule:", "- log_format:", "- operating_contract_xid:",
        ))]

    assert data_lines(compact) == data_lines(verbose)


def test_dashboard_payload_is_identical_for_compact_and_verbose_runs(monkeypatch, tmp_path):
    import json
    import os
    from datetime import datetime, timezone
    from itertools import count
    from uuid import UUID

    from xrefkit import dashboard, skillrun

    render = skillrun._render_log
    captured = {}

    def capture(**kwargs):
        captured.update(kwargs)
        return render(**kwargs)

    monkeypatch.setattr(skillrun, "_render_log", capture)
    _, log = _open_run(tmp_path)
    provenance = {"capability": {"origin": "explicit_input", "selected_value": "repository inspection"}}

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            fixed = cls(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
            return fixed.astimezone(tz) if tz else fixed.replace(tzinfo=None)

    monkeypatch.setattr(skillrun, "datetime", FixedDatetime)
    monkeypatch.setattr(dashboard, "datetime", FixedDatetime)
    snapshots = []
    for compact in (False, True):
        event_ids = count(1)
        monkeypatch.setattr(skillrun.uuid, "uuid4", lambda: UUID(int=next(event_ids)))
        identity = {**captured["definition_identity"], "runtime_provenance": json.dumps(
            provenance, sort_keys=True, separators=(",", ":") if compact else None,
        )}
        log.write_text(render(**{**captured, "definition_identity": identity, "compact": compact}), encoding="utf-8")

        def snapshot():
            # Compare the whole public payload, with no fields removed. The same
            # file path and frozen clocks make file/observation timestamps equal.
            os.utime(log, (1792929600, 1792929600))
            return dashboard.build_payload(tmp_path, log.parent)

        def update(*args):
            code, output = command("skill", *args, "--log", str(log))
            assert code == 0, output

        initial = snapshot()
        assert "token_usage" in {item["code"] for item in initial["runs"][0]["missing_information"]}
        update("workitem", "--item", "WI-1", "--text", "Inspect target",
               "--completion-criterion", "report covers target", "--status", "done", "--role", "definition_sample:executor")
        for artifact_id, kind, target in (("OUT-1", "output", "report.md"), ("EVD-1", "evidence", "tests passed")):
            update("artifact", "--artifact", artifact_id, "--kind", kind, "--target", target,
                   "--item", "WI-1", "--status", "done", "--role", "definition_sample:executor")
        update("concern", "--concern", "RISK-1", "--kind", "risk", "--status", "resolved",
               "--text", "Compatibility checked", "--target", "tests passed", "--role", "definition_sample:executor")
        update("correlate", "--run-id", captured["run_id"], "--mcp-session-id", "mcp-1", "--repository-fingerprint", "repo-1")
        update("routing", "--selected-skill", "definition_sample", "--candidate", "definition_sample", "--reason", "best match")
        update("knowledge", "--action", "search", "--query", "service map", "--status", "hit", "--xid", "SERVICE123456")
        update("knowledge", "--action", "load", "--xid", "SERVICE123456", "--content-hash", "hash-1")
        update("knowledge", "--action", "apply", "--xid", "SERVICE123456", "--content-hash", "hash-1", "--target", "OUT-1")
        update("feedback", "--kind", "human", "--status", "accepted", "--note", "accepted")
        update("feedback", "--kind", "outcome", "--status", "successful", "--note", "successful")
        update("tokens", "--input", "120", "--output", "30")
        populated = snapshot()
        run = populated["runs"][0]
        assert run["missing_information"] == []
        assert run["counts"]["work_items"] == 1
        assert run["counts"]["artifacts"] == 2
        assert run["counts"]["risks"] == 1
        assert run["loaded_xids"] == run["used_xids"] == ["SERVICE123456"]
        assert run["definition_format"] == "skill_definition_v1"
        assert run["definition_xid"] == "ABCDEF123456"
        assert run["definition_sha256"] == captured["definition_identity"]["sha256"]
        assert run["capability"] == "repository inspection"
        assert {event["event"] for event in run["observation_events"]} >= {
            "skill.routed", "knowledge.search", "knowledge.loaded", "knowledge.applied", "human.feedback", "outcome.feedback",
        }
        for phase in ("startup", "planning", "execution"):
            update("phase", "--phase", phase, "--status", "done", "--role", "definition_sample:executor")
        update("verify")
        update("phase", "--phase", "handoff", "--status", "done", "--role", "definition_sample:handoff_owner")
        update("close")
        closed = snapshot()
        assert closed["runs"][0]["status"] == "closed"
        text = log.read_text(encoding="utf-8")
        assert json.loads(skillrun._log_field(text, "definition_runtime_provenance")) == provenance
        assert skillrun._parse_token_usage(text) == {"status": "recorded", "input": "120", "output": "30", "total": "150"}
        snapshots.append((initial, populated, closed))

    assert snapshots[0] == snapshots[1]

"""Observable understanding/change behavior; old public releases keep old tests."""
from copy import deepcopy
from importlib.metadata import version
import json
import subprocess
import sys

import pytest
from packaging.version import Version


def sample():
    def row(identity, text, status):
        return {"id": identity, "text": text, "status": status, "owner": "project-owner",
                "reason": "initial request", "requirement_xids": ["ABCDEF123456"],
                "evidence_refs": ["request/1"], "decision_refs": [], "approval_refs": [],
                "artifact_refs": ["source"], "affected_task_ids": ["migrate"]}
    return {"schema": "brownfield.understanding/v1", "project_id": "migration", "revision": 1,
            "recorded_at": "2026-11-14T15:00:00+09:00", "reason": "initial request",
            "evidence_refs": ["request/1"], "decision_refs": [], "approval_refs": [],
            "requirements": [row("req", "Preserve existing images", "candidate")],
            "confirmations": [row("volume", "How much data must migrate?", "open")],
            "approach": [row("investigate", "Inspect current storage", "proposed")],
            "artifacts": [{"id": "source", "ref": "source/storage.sql", "revision": "sha256:123",
                           "requirement_xids": ["ABCDEF123456"], "evidence_refs": ["scan/1"]}],
            "knowledge_requirements": [{"id": "migration-speed", "requirement_xids": ["ABCDEF123456"],
                "question": "Can migration finish in the permitted downtime?", "query": "migration throughput",
                "needed_for": "migration method decision", "status": "open", "knowledge_refs": [],
                "evidence_refs": ["inventory/1"], "decision_refs": [], "owner": "technical-owner",
                "reason": "Throughput is unmeasured", "method": "Measure representative migration throughput",
                "expected_evidence": "Measured throughput with data volume and environment",
                "decision_ref": "decision/migration", "resolution_point": "before method approval"}]}


if Version(version("xrefkit-skills-brownfield")) >= Version("0.3.0"):
    from xrefkit_skills_brownfield.understanding import (
        analyze_understanding, compare_understanding, render_report, save_analysis, validate_understanding,
    )

    def test_released_contract_carries_new_outputs_and_example():
        import yaml
        from xrefkit_skills_brownfield import package_root
        root = package_root()
        contract = yaml.safe_load((root/"skills/brownfield_workflow.skill.yaml").read_text())
        manifest = yaml.safe_load((root/"package_manifest.yaml").read_text())
        required = {"understanding_revision", "understanding_changes", "knowledge_requirement_analysis",
                    "requirement_artifact_traceability", "decision_investigation_plan",
                    "project_management_impact_notification", "three_section_report"}
        assert required <= set(contract["required_outputs"])
        assert required <= set(manifest["provides"]["skills"][0]["required_outputs"])
        assert analyze_understanding(json.loads((root/"examples/understanding-r001.json").read_text()))["traceability"]

    def test_change_detection_includes_evidence_approval_and_artifact_revision():
        before = sample()
        after = deepcopy(before)
        after.update(revision=2, reason="Migration discovery")
        after["requirements"][0].update(text="Preserve all original image metadata", reason="Inventory found metadata")
        after["confirmations"][0].update(status="answered", reason="Count measured", evidence_refs=["count/2"])
        after["approach"][0].update(status="approved", reason="Owner selected investigation", approval_refs=["approval/2"])
        after["artifacts"][0]["revision"] = "sha256:456"
        result = analyze_understanding(after, before)
        assert len(result["changes"]) == 4
        changed = {r["item_id"]: r for r in result["changes"]}
        assert "evidence_refs" in changed["volume"]["changed_fields"]
        assert "approval_refs" in changed["investigate"]["changed_fields"]
        assert changed["artifact:source"]["reason"] == "Migration discovery"
        assert result["notification"]["affected_task_ids"] == ["migrate"]
        assert result["notification"]["requirement_xids"] == ["ABCDEF123456"]
        assert result["notification"]["approval_refs"] == ["approval/2"]
        assert before == sample()

    def test_removed_requirement_retains_old_trace_and_current_removal_reason():
        before = sample()
        after = deepcopy(before)
        after.update(revision=2, reason="Owner removed scope", evidence_refs=["removal/2"])
        for key in ("requirements", "confirmations", "approach", "artifacts", "knowledge_requirements"):
            after[key] = []
        changes = compare_understanding(before, after)
        assert len(changes) == 5 and all(r["kind"] == "removed" for r in changes)
        assert all(r["reason"] == "Owner removed scope" for r in changes)
        notice = analyze_understanding(after, before)["notification"]
        assert notice["requirement_xids"] == ["ABCDEF123456"]
        assert "removal/2" in notice["evidence_refs"]

    def test_knowledge_plan_and_gaps_preserve_authority_and_missing_fields():
        doc = sample()
        result = analyze_understanding(doc)
        analysis = result["knowledge_requirement_analysis"]
        assert analysis["decision_activities"][0]["status"] == "proposed"
        assert "duration" not in analysis["decision_activities"][0]
        assert analysis["holds"][0]["status"] == "open"
        doc["knowledge_requirements"][0]["expected_evidence"] = None
        analysis = analyze_understanding(doc)["knowledge_requirement_analysis"]
        assert analysis["decision_activities"] == []
        assert analysis["gaps"][0]["missing_plan_fields"] == ["expected_evidence"]
        assert analysis["holds"][0]["next_action"] == "Supply expected_evidence"

    def test_satisfied_knowledge_is_not_investigation_or_approval():
        doc = sample()
        doc["knowledge_requirements"][0].update(status="satisfied", knowledge_refs=["knowledge/throughput-r2"])
        analysis = analyze_understanding(doc)["knowledge_requirement_analysis"]
        assert len(analysis["satisfied"]) == 1
        assert not analysis["gaps"] and not analysis["decision_activities"] and not analysis["holds"]
        assert doc["requirements"][0]["status"] == "candidate"

    def test_traceability_and_exact_three_standard_sections():
        result = analyze_understanding(sample())
        trace = result["traceability"][0]
        assert trace["artifacts"][0]["revision"] == "sha256:123"
        assert trace["knowledge_requirements"] == ["migration-speed"]
        report = render_report(result)
        assert [line for line in report.splitlines() if line.startswith("## ")] == ["## 要求事項", "## 確認事項", "## 進め方"]
        assert "request/1" in report and "Throughput is unmeasured" in report
        assert "before method approval" in report

    def test_create_only_analysis_retry_and_revision_conflict(tmp_path):
        doc = sample()
        path = save_analysis(tmp_path, doc)
        raw = path.read_bytes()
        assert save_analysis(tmp_path, doc) == path
        doc["reason"] = "different input at same revision"
        with pytest.raises(ValueError, match="already exists"):
            save_analysis(tmp_path, doc)
        assert path.read_bytes() == raw
        stored = json.loads(raw)
        assert stored["current"] == sample()
        assert stored["analysis"]["notification"]["notification_id"] == "migration-understanding-r001"

    def test_failed_write_has_no_published_or_temporary_revision(tmp_path, monkeypatch):
        import xrefkit_skills_brownfield.understanding as module
        def fail(_):
            raise OSError("simulated storage failure")
        monkeypatch.setattr(module.os, "fsync", fail)
        with pytest.raises(OSError, match="storage failure"):
            save_analysis(tmp_path, sample())
        assert list(tmp_path.iterdir()) == []

    def test_open_knowledge_and_activity_do_not_show_empty_record_message():
        before = sample()
        before["confirmations"] = []
        before["approach"] = []
        after = deepcopy(before)
        after["revision"] = 2
        report = render_report(analyze_understanding(after, before))
        assert "記録なし" not in report
        assert report.count("Throughput is unmeasured") == 2
        assert analyze_understanding(after, before)["notification"]["requirement_xids"] == ["ABCDEF123456"]

    @pytest.mark.parametrize("mutate", [
        lambda d: d.update(revision=True),
        lambda d: d.update(recorded_at="2026-11-14"),
        lambda d: d["requirements"][0].update(status="confirmed"),
        lambda d: d["requirements"][0].update(requirement_xids=["REQ-1"]),
        lambda d: d["confirmations"][0].update(requirement_xids=["FFFFFFFFFFFF"]),
        lambda d: d["approach"][0].update(artifact_refs=["missing"]),
        lambda d: d["artifacts"][0].update(requirement_xids=[]),
        lambda d: d["knowledge_requirements"][0].update(status="satisfied"),
        lambda d: d["requirements"].append(deepcopy(d["requirements"][0])),
        lambda d: d["requirements"][0].update(id="artifact:source"),
        lambda d: d.update(automatic_approval=True),
    ])
    def test_invalid_records_rejected(mutate):
        doc = sample()
        mutate(doc)
        with pytest.raises(ValueError):
            validate_understanding(doc)

    def test_wrong_project_revision_and_time_refused():
        before = sample()
        with pytest.raises(ValueError, match="advance"):
            compare_understanding(before, before)
        after = deepcopy(before)
        after.update(revision=2, project_id="other")
        with pytest.raises(ValueError, match="projects"):
            compare_understanding(before, after)
        after.update(project_id="migration", recorded_at="2026-11-13T00:00:00Z")
        with pytest.raises(ValueError, match="timestamp"):
            compare_understanding(before, after)

    def test_cli_standard_and_json_output(tmp_path):
        path = tmp_path / "input.json"
        path.write_text(json.dumps(sample()), encoding="utf-8")
        command = [sys.executable, "-I", "-X", "utf8", "-m", "xrefkit_skills_brownfield.understanding", str(path)]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 0, result.stderr
        assert result.stdout.startswith("## 要求事項")
        result = subprocess.run(command + ["--json"], capture_output=True, text=True, encoding="utf-8")
        assert json.loads(result.stdout)["schema"] == "brownfield.analysis/v1"
        path.write_text('{"schema": 1, "schema": 2}', encoding="utf-8")
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 2 and "duplicate JSON key" in result.stderr

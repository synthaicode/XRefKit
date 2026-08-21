import json
from pathlib import Path

from xrefkit.host_precheck import build_precheck_report
from xrefkit.__main__ import main


def _spec(**overrides):
    value = {
        "host": "Codex Desktop 1.2",
        "extension": "XRefKit extension 0.4.8",
        "transcript_reference": "human-run/transcript-001",
        "baseline": {"skill": "brownfield_workflow", "result": "managed"},
        "observed": {"skill": "brownfield_workflow", "result": "managed"},
        "evidence": {"bootstrap": True, "discovery": True, "route_selection": True},
        "catalog": "available",
        "intent": "clear",
    }
    value.update(overrides)
    return value


def test_precheck_passes_only_with_observable_managed_route_evidence():
    report = build_precheck_report(_spec())
    assert report["schema"] == "xrefkit.host_compatibility_precheck/v1"
    assert report["assessment"]["status"] == "pass"
    assert "private model reasoning" in report["unobservable"]


def test_precheck_blocks_generic_preselection_without_claiming_override():
    report = build_precheck_report(_spec(generic_preselection=True))
    assert report["assessment"]["status"] == "blocked"
    assert "explicit XRefKit entrypoint" in report["assessment"]["next_action"]
    assert any("whether XRefKit overrode" in item for item in report["unobservable"])


def test_precheck_distinguishes_missing_catalog_and_ambiguous_intent():
    assert build_precheck_report(_spec(catalog="unavailable"))["assessment"]["status"] == "blocked"
    assert build_precheck_report(_spec(intent="ambiguous"))["assessment"]["status"] == "needs_human_confirmation"


def test_precheck_cli_writes_repeatable_json_report(tmp_path: Path, capsys):
    source = tmp_path / "input.json"
    output = tmp_path / "report.json"
    source.write_text(json.dumps(_spec()), encoding="utf-8")
    assert main(["host", "precheck", "--input", str(source), "--out", str(output)]) == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["assessment"]["status"] == "pass"
    assert json.loads(capsys.readouterr().out)["schema"] == report["schema"]

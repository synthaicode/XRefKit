"""Release gates must distinguish incompatibility from missing evidence."""
from __future__ import annotations

import json
import urllib.error
import zipfile
from types import SimpleNamespace

import pytest
import yaml

from tools import check_installed_skill_contract as installed
from tools import check_skill_compatibility as gate


def wheel(tmp_path, dependency="xrefkit>=0.6.1,<0.7.0"):
    path = tmp_path / "demo-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("demo-0.1.0.dist-info/METADATA",
                         "Name: demo\nVersion: 0.1.0\nRequires-Dist: " + dependency + "\n")
    return path


def test_old_upper_bound_stops_gate(tmp_path):
    with pytest.raises(gate.GateError, match="excluded") as error:
        gate.check_dependency(wheel(tmp_path, "xrefkit>=0.4.3,<0.5.0"), "demo", "0.6.1")
    assert error.value.status == "incompatible"


def test_matching_dependency_and_marker_are_checked(tmp_path):
    assert gate.check_dependency(wheel(tmp_path), "demo", "0.6.1") == "0.1.0"
    with pytest.raises(gate.GateError, match="missing active"):
        gate.check_dependency(wheel(tmp_path, 'xrefkit>=0.6.1; extra == "never"'), "demo", "0.6.1")


def test_inventory_cannot_silently_omit_an_entry_point(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/official_skill_packages.json").write_text(
        json.dumps({"schema_version": 1, "packages": []}), encoding="utf-8")
    package = tmp_path / "packages/demo"
    package.mkdir(parents=True)
    (package / "pyproject.toml").write_text(
        '[project]\nname="demo"\n[project.entry-points."xrefkit.skill_packages"]\ndemo="demo:root"\n',
        encoding="utf-8")
    with pytest.raises(gate.GateError, match="does not match"):
        gate.inventory(tmp_path)


@pytest.mark.parametrize("exception,reason", [
    (urllib.error.URLError("offline"), "registry_unavailable"),
    (urllib.error.HTTPError("https://pypi.org", 404, "missing", {}, None), "registry_missing"),
])
def test_registry_failure_is_blocked_not_incompatible(monkeypatch, exception, reason):
    def unavailable(*args, **kwargs):
        raise exception
    monkeypatch.setattr(gate.urllib.request, "urlopen", unavailable)
    with pytest.raises(gate.GateError, match=reason) as error:
        gate._download("https://pypi.org/pypi/demo/json")
    assert error.value.status == "blocked"


def contract_fixture(tmp_path, monkeypatch):
    from xrefkit.loaders import load_package_manifest
    from xrefkit import discovery
    root = tmp_path / "package"
    root.mkdir()
    manifest = {"package_id": "official.demo", "package_type": "skill_package",
                "version": "0.1.0", "requires": {"xrefkit_core": ">=2.0.0 <3.0.0"},
                "provides": {"skills": [{"id": "demo.skill", "xid": "demo.skill.xid",
                    "path": "demo.skill.yaml", "required_outputs": ["result"]}]},
                "contract": {}}
    skill = {"skill_id": "demo.skill", "xid": "demo.skill.xid",
             "entry": {"xid": "demo.entry.xid", "path": "entry.md", "load_policy": "required_inline"},
             "required_outputs": ["result"], "extension_policy": {}}
    (root / "package_manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (root / "demo.skill.yaml").write_text(yaml.safe_dump(skill), encoding="utf-8")
    (root / "entry.md").write_text("Representative workflow entry", encoding="utf-8")
    monkeypatch.setattr(installed.metadata, "version", lambda name: "0.6.1")
    monkeypatch.setattr(installed.metadata, "distribution", lambda name: SimpleNamespace(
        version="0.1.0", entry_points=[SimpleNamespace(group="xrefkit.skill_packages", name="demo")]))
    def discovered():
        return [discovery.DiscoveredSkillPackage("demo", root, root / "package_manifest.yaml",
                                                load_package_manifest(root / "package_manifest.yaml"))]
    monkeypatch.setattr(discovery, "discover_skill_packages", discovered)
    return root, manifest, skill


def test_real_resolver_probe_passes_representative_fixture(tmp_path, monkeypatch):
    contract_fixture(tmp_path, monkeypatch)
    assert installed.verify_installed("demo", "official.demo", "0.6.1")["skills"] == ["demo.skill"]


def test_real_protocol_rejection_stops_installed_probe(tmp_path, monkeypatch):
    root, manifest, _ = contract_fixture(tmp_path, monkeypatch)
    manifest["requires"]["xrefkit_core"] = ">=3.0.0"
    (root / "package_manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="current core is 2.0.0"):
        installed.verify_installed("demo", "official.demo", "0.6.1")


def test_schema_error_stops_installed_probe(tmp_path, monkeypatch):
    root, _, skill = contract_fixture(tmp_path, monkeypatch)
    skill["unsupported_schema_field"] = True
    (root / "demo.skill.yaml").write_text(yaml.safe_dump(skill), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported_schema_field"):
        installed.verify_installed("demo", "official.demo", "0.6.1")


def test_missing_entry_or_required_reference_stops_probe(tmp_path, monkeypatch):
    root, _, _ = contract_fixture(tmp_path, monkeypatch)
    (root / "entry.md").unlink()
    with pytest.raises(FileNotFoundError):
        installed.verify_installed("demo", "official.demo", "0.6.1")


def test_missing_declared_knowledge_reference_stops_probe(tmp_path, monkeypatch):
    root, manifest, skill = contract_fixture(tmp_path, monkeypatch)
    manifest["provides"]["skills"][0]["required_knowledge"] = ["missing.knowledge.xid"]
    skill["required_knowledge"] = ["missing.knowledge.xid"]
    (root / "package_manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    (root / "demo.skill.yaml").write_text(yaml.safe_dump(skill), encoding="utf-8")
    with pytest.raises(KeyError, match="unknown XID"):
        installed.verify_installed("demo", "official.demo", "0.6.1")


def test_combined_registry_rejects_cross_package_xid_collision(tmp_path, monkeypatch):
    from xrefkit import discovery
    from xrefkit.loaders import load_package_manifest
    root, manifest, _ = contract_fixture(tmp_path, monkeypatch)
    first = discovery.discover_skill_packages()[0]
    other = tmp_path / "other"
    other.mkdir()
    manifest["package_id"] = "official.other"
    (other / "package_manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    second = discovery.DiscoveredSkillPackage("other", other, other / "package_manifest.yaml",
                                              load_package_manifest(other / "package_manifest.yaml"))
    monkeypatch.setattr(discovery, "discover_skill_packages", lambda: [first, second])
    with pytest.raises(ValueError, match="duplicate XID"):
        installed.verify_installed("demo", "official.demo", "0.6.1", {"official.demo", "official.other"})


def test_nonempty_declared_contract_cannot_disappear(tmp_path, monkeypatch):
    root, manifest, _ = contract_fixture(tmp_path, monkeypatch)
    manifest["provides"]["skills"][0]["required_knowledge"] = ["missing.knowledge.xid"]
    (root / "package_manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="runtime lost manifest required_knowledge"):
        installed.verify_installed("demo", "official.demo", "0.6.1")


def test_failed_published_scope_is_a_failure(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="0.1.0"\n', encoding="utf-8")
    core = wheel(tmp_path)
    monkeypatch.setattr(gate, "wheel_metadata", lambda path: {"Name": "xrefkit", "Version": "0.1.0"})
    monkeypatch.setattr(gate, "inventory", lambda repo: [
        {"name": "demo", "path": "packages/demo", "package_id": "official.demo", "publication": "pypi"}])
    monkeypatch.setattr(gate, "published_wheel", lambda name, dest: core)
    def incompatible(*args):
        raise gate.GateError("incompatible", "old published upper bound")
    monkeypatch.setattr(gate, "check_dependency", incompatible)
    report = gate.check(tmp_path, core, "published", tmp_path / "evidence")
    assert report["ok"] is False
    assert report["results"][0]["status"] == "incompatible"


def test_passing_candidate_cannot_rescue_incompatible_public_wheel(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="0.1.0"\n', encoding="utf-8")
    core = wheel(tmp_path)
    monkeypatch.setattr(gate, "wheel_metadata", lambda path: {"Name": "xrefkit", "Version": "0.1.0"})
    monkeypatch.setattr(gate, "inventory", lambda repo: [
        {"name": "demo", "path": "packages/demo", "package_id": "official.demo", "publication": "pypi"}])
    monkeypatch.setattr(gate, "published_wheel", lambda name, dest: core)
    def fake_build(command, cwd, log, **kwargs):
        dist = cwd / "dist"
        dist.mkdir()
        (dist / "candidate.whl").write_bytes(core.read_bytes())
    monkeypatch.setattr(gate, "run", fake_build)
    def dependency(path, *args):
        if path == core:
            raise gate.GateError("incompatible", "old published upper bound")
        return "0.1.0"
    monkeypatch.setattr(gate, "check_dependency", dependency)
    monkeypatch.setattr(gate, "probe", lambda *args: {"executed_tests": 4})
    report = gate.check(tmp_path, core, "all", tmp_path / "evidence")
    assert [(row["scope"], row["status"]) for row in report["results"]] == [
        ("published", "incompatible"), ("candidate", "passed")]
    assert report["ok"] is False


@pytest.mark.parametrize("registry_status,expected", [("registry_missing", "not_published"),
                                                      ("registry_unavailable", "blocked")])
def test_source_only_status_requires_registry_evidence(tmp_path, monkeypatch, registry_status, expected):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="0.1.0"\n', encoding="utf-8")
    core = wheel(tmp_path)
    monkeypatch.setattr(gate, "wheel_metadata", lambda path: {"Name": "xrefkit", "Version": "0.1.0"})
    monkeypatch.setattr(gate, "inventory", lambda repo: [
        {"name": "demo", "path": "packages/demo", "package_id": "official.demo", "publication": "source_only"}])
    def registry(url):
        raise gate.GateError("blocked", registry_status)
    monkeypatch.setattr(gate, "_download", registry)
    report = gate.check(tmp_path, core, "published", tmp_path / "evidence")
    assert report["results"][0]["status"] == expected
    assert report["ok"] is (expected == "not_published")


def test_missing_package_regression_tests_are_unverified(tmp_path, monkeypatch):
    monkeypatch.setattr(gate.venv.EnvBuilder, "create", lambda self, path: None)
    monkeypatch.setattr(gate, "run", lambda *args, **kwargs: "")
    with pytest.raises(gate.GateError, match="no package regression tests") as error:
        gate.probe(tmp_path, {"name": "demo", "path": "packages/demo", "package_id": "official.demo"},
                   tmp_path / "skill.whl", tmp_path / "core.whl", "0.6.1", tmp_path, tmp_path / "log")
    assert error.value.status == "blocked"


def test_core_publish_has_both_scopes_and_fresh_published_check():
    from pathlib import Path
    workflow = yaml.safe_load((Path(__file__).resolve().parents[1]
                              / ".github/workflows/python-package.yml").read_text(encoding="utf-8"))
    assert "skill-compatibility" in workflow["jobs"]["publish-to-pypi"]["needs"]
    gate_steps = workflow["jobs"]["skill-compatibility"]["steps"]
    assert any("--scope all" in step.get("run", "") for step in gate_steps)
    publish_steps = workflow["jobs"]["publish-to-pypi"]["steps"]
    fresh_index = next(i for i, step in enumerate(publish_steps) if "--scope published" in step.get("run", ""))
    release_index = next(i for i, step in enumerate(publish_steps) if "gh release create" in step.get("run", ""))
    assert fresh_index < release_index


@pytest.mark.parametrize("xml", [
    '<testsuites><testsuite tests="0" skipped="0"/></testsuites>',
    '<testsuites><testsuite tests="4" skipped="1"/></testsuites>',
])
def test_missing_or_skipped_regression_coverage_cannot_pass(tmp_path, xml):
    path = tmp_path / "result.xml"
    path.write_text(xml, encoding="utf-8")
    with pytest.raises(gate.GateError, match="unverified regression coverage") as error:
        gate.regression_result(path)
    assert error.value.status == "blocked"


def test_complete_regression_evidence_is_counted(tmp_path):
    path = tmp_path / "result.xml"
    path.write_text('<testsuites><testsuite tests="4" skipped="0" errors="0" failures="0"/></testsuites>',
                    encoding="utf-8")
    assert gate.regression_result(path) == {"executed_tests": 4, "skipped_tests": 0}


def test_cli_returns_failure_for_failed_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "check", lambda *args: {"ok": False, "status": "incompatible"})
    assert gate.main(["--core-wheel", str(tmp_path / "core.whl"),
                      "--output", str(tmp_path / "report")]) == 1
    assert json.loads((tmp_path / "report/report.json").read_text())["ok"] is False

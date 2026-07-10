from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from xrefkit.cli import main
from xrefkit.discovery import discover_skill_packages, package_list_rows
from xrefkit.loaders import load_package_manifest
from xrefkit.workspace import build_registry


class FakeEntryPoint:
    def __init__(self, name: str, root: Path) -> None:
        self.name = name
        self._root = root

    def load(self):
        return lambda: self._root


class FakeEntryPoints(list):
    def select(self, *, group: str):
        if group == "xrefkit.skill_packages":
            return self
        return []


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_yaml(path: Path, data: dict) -> None:
    _write(path, yaml.safe_dump(data, sort_keys=False))


def _skill_package(root: Path, package_id: str) -> Path:
    _write(root / "skills" / "change_design" / "entry.md", "entry\n")
    _write(root / "skills" / "change_design.skill.yaml", yaml.safe_dump({
        "skill_id": "xddp.design.change_design",
        "xid": f"xid-skill-{package_id.replace('.', '-')}",
        "entry": {
            "xid": f"xid-entry-{package_id.replace('.', '-')}",
            "path": "skills/change_design/entry.md",
            "load_policy": "required_inline",
        },
        "required_outputs": ["traceability"],
        "extension_policy": {},
    }, sort_keys=False))
    manifest_path = root / "package_manifest.yaml"
    _write_yaml(manifest_path, {
        "package_id": package_id,
        "package_type": "skill_package",
        "version": "1.0.0",
        "requires": {"xrefkit_core": ">=2.0.0 <3.0.0"},
        "provides": {
            "skills": [
                {
                    "id": "xddp.design.change_design",
                    "xid": f"xid-skill-{package_id.replace('.', '-')}",
                    "path": "skills/change_design.skill.yaml",
                }
            ]
        },
        "contract": {},
    })
    return manifest_path


def _patch_entry_points(monkeypatch: pytest.MonkeyPatch, roots: list[Path]) -> None:
    import xrefkit.discovery as discovery

    fake = FakeEntryPoints(FakeEntryPoint(f"pkg{index}", root) for index, root in enumerate(roots))
    monkeypatch.setattr(discovery.metadata, "entry_points", lambda: fake)


def test_entry_point_discovery_reads_package_manifest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "installed_pkg"
    _skill_package(root, "xrefkit.skills.xddp.design")
    _patch_entry_points(monkeypatch, [root])

    discovered = discover_skill_packages()

    assert len(discovered) == 1
    assert discovered[0].package_id == "xrefkit.skills.xddp.design"
    assert discovered[0].manifest_path == root / "package_manifest.yaml"


def test_package_list_marks_discovered_enabled_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "installed_pkg"
    _skill_package(root, "xrefkit.skills.xddp.design")
    _patch_entry_points(monkeypatch, [root])

    rows = package_list_rows(enabled_package_ids={"xrefkit.skills.xddp.design"})

    assert rows[0]["enabled"] is True


def test_entry_point_discovery_does_not_register_disabled_packages(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "installed_pkg"
    _skill_package(root, "xrefkit.skills.xddp.design")
    _patch_entry_points(monkeypatch, [root])

    registry = build_registry(package_manifests=[], discover_entry_points=True, enabled_package_ids=set())

    assert registry.packages.list() == []
    assert registry.skills.list() == []


def test_entry_point_discovery_registers_enabled_packages(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root = tmp_path / "installed_pkg"
    _skill_package(root, "xrefkit.skills.xddp.design")
    _patch_entry_points(monkeypatch, [root])

    registry = build_registry(
        package_manifests=[],
        discover_entry_points=True,
        enabled_package_ids={"xrefkit.skills.xddp.design"},
    )

    assert registry.packages.require("xrefkit.skills.xddp.design")
    assert registry.skills.require("xddp.design.change_design")


def test_cli_package_discover_and_list(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "installed_pkg"
    _skill_package(root, "xrefkit.skills.xddp.design")
    _patch_entry_points(monkeypatch, [root])

    assert main(["package", "discover", "--json"]) == 0
    discovered = json.loads(capsys.readouterr().out)
    assert discovered[0]["package_id"] == "xrefkit.skills.xddp.design"

    assert main(["package", "list", "--json", "--enabled-package", "xrefkit.skills.xddp.design"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed[0]["enabled"] is True


def test_repository_xddp_design_package_root_supports_entry_point_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    package_src = repo_root / "packages" / "xrefkit-skills-xddp-design" / "src"
    monkeypatch.syspath_prepend(str(package_src))

    import xrefkit_skills_xddp_design

    package_root = xrefkit_skills_xddp_design.package_root()
    _patch_entry_points(monkeypatch, [package_root])

    filesystem_manifest = load_package_manifest(package_root / "package_manifest.yaml")
    discovered = discover_skill_packages()
    registry = build_registry(
        package_manifests=[],
        discover_entry_points=True,
        enabled_package_ids={"xrefkit.skills.xddp.design"},
    )

    assert filesystem_manifest.package_id == "xrefkit.skills.xddp.design"
    assert discovered[0].package_id == "xrefkit.skills.xddp.design"
    assert registry.packages.require("xrefkit.skills.xddp.design")
    assert registry.skills.require("xddp.design.change_design")


def test_repository_csharp_package_root_supports_entry_point_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    package_src = repo_root / "packages" / "xrefkit-skills-csharp" / "src"
    monkeypatch.syspath_prepend(str(package_src))

    import xrefkit_skills_csharp

    package_root = xrefkit_skills_csharp.package_root()
    _patch_entry_points(monkeypatch, [package_root])

    filesystem_manifest = load_package_manifest(package_root / "package_manifest.yaml")
    discovered = discover_skill_packages()
    registry = build_registry(
        package_manifests=[],
        discover_entry_points=True,
        enabled_package_ids={"xrefkit.skills.csharp"},
    )

    assert filesystem_manifest.package_id == "xrefkit.skills.csharp"
    assert discovered[0].package_id == "xrefkit.skills.csharp"
    assert registry.packages.require("xrefkit.skills.csharp")
    assert registry.skills.require("csharp.review")

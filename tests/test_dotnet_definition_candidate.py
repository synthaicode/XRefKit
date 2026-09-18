import json
import shutil
from pathlib import Path

import pytest

from tools.convert_dotnet_skill_definition import convert
from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition
from xrefkit.skillmeta import _parse_meta_lines


def test_representative_conversion_is_lossless_and_nonactivating(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    source = repo / "skills/dotnet_change_analysis"
    dest = tmp_path / "skills/dotnet_change_analysis"
    shutil.copytree(source, dest)
    before = {p.name: p.read_bytes() for p in [dest / "SKILL.md", dest / "meta.md"]}
    result = convert(tmp_path, Path("work/candidate"))
    candidate = load_skill_definition(Path(result["candidate"]))
    manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
    assert candidate["method"].encode("utf-8") == before["SKILL.md"]
    assert {row["source_key"]: row["source_value"] for row in manifest["meta_coverage"]} == _parse_meta_lines(before["meta.md"].decode("utf-8"))
    assert len(candidate["metadata"]["knowledge_needs"]) == 5
    assert len(candidate["metadata"]["criteria"]) == 9
    assert not result["runtime_activated"]
    assert not manifest["runtime_activated"]
    assert {p.name: p.read_bytes() for p in [dest / "SKILL.md", dest / "meta.md"]} == before
    assert convert(tmp_path, Path("work/candidate")) == result
    Path(result["candidate"]).write_text("user edited candidate", encoding="utf-8")
    with pytest.raises(ValueError, match="different content"):
        convert(tmp_path, Path("work/candidate"))
    assert Path(result["candidate"]).read_text() == "user edited candidate"


def test_conversion_cannot_write_outside_work(tmp_path):
    with pytest.raises(ValueError, match="root/work"):
        convert(tmp_path, Path("skills/overwrite"))


def test_simplified_candidate_retains_analysis_method_and_removes_common_controls():
    repo = Path(__file__).resolve().parents[1]
    skill = (repo / "work/skill-definition-candidate/dotnet_change_analysis/SKILL.md").read_text(encoding="utf-8")
    manifest = json.loads((repo / "work/skill-definition-candidate/dotnet_change_analysis/migration.json").read_text(encoding="utf-8"))
    assert "## Where Impacted-Boundary Analysis (grep-first)" in skill
    assert "## Semantic-Inventory Mode (deterministic pack — grep-weak questions only)" in skill
    assert "## Closure Gate" in skill
    assert "## Handoff" in skill
    assert "## Context Direction Guard" not in skill
    assert "## Worklist" not in skill
    assert "## Execution Role" not in skill
    assert "## Reporting Contract" not in skill
    assert "## Required Knowledge (XID)" not in skill
    assert manifest["method_preserved_byte_for_byte"] is False
    assert "Failure Handling" in manifest["simplification_coverage_map"]["removed_common_sections"]
    assert "Execution" in manifest["simplification_coverage_map"]["retained_skill_specific_sections"]


def test_representative_definition_resolves_runtime_selected_knowledge():
    repo = Path(__file__).resolve().parents[1]
    relative = Path("work/skill-definition-candidate/dotnet_change_analysis/SKILL.md")
    definition = load_skill_definition(repo / relative)
    catalog = XRefCatalog.build(repo, skill_definition_paths=[relative])
    entries = [entry for entry in catalog.skills if entry.skill_id == "dotnet_change_analysis"]
    assert len(entries) == 1
    assert entries[0].definition_format == "skill_definition_v1"

    need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
    result = catalog.resolve_skill_knowledge("dotnet_change_analysis", need_ids)
    assert result["unresolved_activation"] == []
    assert result["unsatisfied_required"] == []
    assert [need["id"] for need in result["needs"]] == need_ids
    for source, resolved in zip(definition["metadata"]["knowledge_needs"], result["needs"], strict=True):
        assert resolved["activation_state"] == "active"
        assert resolved["required"] is True
        assert resolved["satisfied"] is True
        assert resolved["candidates"][0]["xid"] == source["seed_xids"][0]


def test_tracked_v1_definition_resolves_knowledge_and_explicit_selection_is_single_entry():
    repo = Path(__file__).resolve().parents[1]
    relative = Path("skills/dotnet_change_analysis/SKILL.v1.md")
    definition = load_skill_definition(repo / relative)
    candidate = load_skill_definition(repo / "work/skill-definition-candidate/dotnet_change_analysis/SKILL.md")
    assert definition["metadata"]["xid"] == "9883EF4E8CA9"
    assert set(definition["metadata"]["aliases"]) == {"D94E3B3A7C11", "1F4A6D20B8E1"}
    migrated_method = definition["method"].replace("9883EF4E8CA9", "D94E3B3A7C11")
    assert migrated_method.splitlines() == candidate["method"].splitlines()
    catalog = XRefCatalog.build(repo, skill_definition_paths=[relative])
    entries = [entry for entry in catalog.skills if entry.skill_id == "dotnet_change_analysis"]
    assert len(entries) == 1
    assert entries[0].definition_format == "skill_definition_v1"
    need_ids = [need["id"] for need in definition["metadata"]["knowledge_needs"]]
    result = catalog.resolve_skill_knowledge("dotnet_change_analysis", need_ids)
    assert result["unresolved_activation"] == []
    assert result["unsatisfied_required"] == []
    assert [need["id"] for need in result["needs"]] == need_ids


def test_legacy_meta_still_points_to_legacy_body():
    repo = Path(__file__).resolve().parents[1]
    meta = (repo / "skills/dotnet_change_analysis/meta.md").read_text(encoding="utf-8")
    assert "skill_doc: `./SKILL.md`" in meta

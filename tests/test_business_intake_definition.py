from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.skill_definition import load_skill_definition


CASES = (
    ("business_learning_interview", "B6C4E9A2D781", "4D8E1A7C5B92", "2B6D4F18A3C1", "7B3E5D1A6103"),
    ("business_intake_scoping", "B6C4E9A2D782", "6F2A9C41E8B3", "4E9B2C18D740", "7B3E5D1A6102"),
)


def test_business_intake_v1_definitions_parse_select_resolve_and_preserve_legacy():
    repo = Path(__file__).resolve().parents[1]
    paths = []
    for skill_id, xid, body_xid, meta_xid, rule_xid in CASES:
        directory = repo / "skills/packs/business-intake" / skill_id
        definition_path = directory / "SKILL.v1.md"
        paths.append(definition_path.relative_to(repo))
        definition = load_skill_definition(definition_path)
        metadata = definition["metadata"]
        assert metadata["schema_version"] == 1
        assert metadata["skill_id"] == skill_id
        assert metadata["xid"] == xid
        assert set(metadata["aliases"]) == {body_xid, meta_xid}
        assert metadata["xid"] not in metadata["aliases"]
        assert len(metadata["aliases"]) == len(set(metadata["aliases"]))
        assert not {
            "capability", "tuning", "responsibility", "execution_mode",
            "model", "model_tier", "maturity",
        } & set(metadata)
        assert metadata["control_refs"] == []
        assert metadata["knowledge_needs"][0]["seed_xids"] == [rule_xid]
        assert "docs/packs/business-intake/" in definition["method"]

        catalog = XRefCatalog.build(repo, skill_definition_paths=[definition_path.relative_to(repo)])
        entries = [entry for entry in catalog.skills if entry.skill_id == skill_id]
        assert len(entries) == 1
        assert entries[0].definition_format == "skill_definition_v1"
        assert entries[0].definition_xid == xid
        resolved = catalog.resolve_skill_knowledge(skill_id, ["business_" + ("learning_interview" if skill_id == "business_learning_interview" else "intake_scoping") + "_rules"])
        assert resolved["unresolved_activation"] == []
        assert resolved["unsatisfied_required"] == []
        assert resolved["needs"][0]["satisfied"] is True

        legacy = (directory / "SKILL.md").read_text(encoding="utf-8")
        meta = (directory / "meta.md").read_text(encoding="utf-8")
        assert f"<!-- xid: {body_xid} -->" in legacy
        assert f"<!-- xid: {meta_xid} -->" in meta
        assert "skill_doc: `./SKILL.md`" in meta

    catalog = XRefCatalog.build(repo, skill_definition_paths=paths)
    assert {entry.skill_id for entry in catalog.skills if entry.definition_format == "skill_definition_v1"} == {
        "business_learning_interview", "business_intake_scoping"
    }

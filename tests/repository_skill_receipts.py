"""Checks for retired repository identities, distinct from external legacy fixtures."""
from pathlib import Path

from xrefkit.repository_skills import load_repository_adoption, repository_skill
from xrefkit.skill_definition import load_skill_definition


def assert_legacy_receipt(source: Path):
    repo = Path(__file__).resolve().parents[1]
    adoption = load_repository_adoption(repo)
    entry = repository_skill(repo, source.as_posix(), adoption)
    assert entry is not None
    relative = source.relative_to(repo).as_posix()
    receipt = next(row for row in entry["legacy_sources"] if row["path"] == relative)
    definition = load_skill_definition(repo / entry["definition_path"])
    assert receipt["xid"] in definition["metadata"]["aliases"]
    assert len(receipt["sha256"]) == 64
    assert entry["definition_sha256"] == definition["content_hash"]
    return receipt


def assert_preserved_source_boundary(definition):
    """Original requirements may be retained; runtime authority stays external."""
    metadata = definition["metadata"]
    assert {"capability", "tuning", "responsibility", "execution_mode", "model", "model_tier", "maturity"}.isdisjoint(metadata)
    assert any(c["id"] == "source_obligation_retention" for c in metadata["criteria"])
    method = definition["method"]
    assert "they neither relax these obligations nor add different requirements" in method
    assert "not an independent control-policy source" in method
    assert "Legacy CAP activity labels do not infer or override a runtime capability" in method
    return True

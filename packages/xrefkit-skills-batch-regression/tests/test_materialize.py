from pathlib import Path

import pytest

from xrefkit_skills_batch_regression.mcp_materialize import materialize


def test_materialize_creates_folder_based_mcp_skill(tmp_path: Path) -> None:
    result = materialize(tmp_path)
    skill_root = tmp_path / "skills" / "packs" / "batch-regression" / "batch-impact-regression"

    assert result["mcp_reload_required"] is True
    assert (skill_root / "meta.md").is_file()
    assert (skill_root / "SKILL.md").is_file()
    assert (skill_root / "scripts" / "batch_regression.py").is_file()
    assert (skill_root / "references" / "workflow.md").is_file()


def test_materialize_does_not_overwrite_without_force(tmp_path: Path) -> None:
    materialize(tmp_path)

    with pytest.raises(FileExistsError):
        materialize(tmp_path)

    result = materialize(tmp_path, force=True)
    assert result["copied_files"]


def test_materialize_rejects_target_outside_repository(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        materialize(tmp_path, target=tmp_path.parent / "outside")

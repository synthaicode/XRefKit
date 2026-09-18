import json
import shutil
from pathlib import Path

import pytest

from tools.convert_dotnet_skill_definition import convert
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

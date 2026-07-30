from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from xrefkit.skills_sync import sync_bundle


def _zip_bytes() -> bytes:
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("xrefkit-skills-demo/skills/demo/meta.md", "<!-- xid: skill-demo -->\n# Demo\n")
        archive.writestr("xrefkit-skills-demo/skills/demo/SKILL.md", "<!-- xid: skill-demo-body -->\n# Demo\n")
        archive.writestr("xrefkit-skills-demo/knowledge/demo.md", "<!-- xid: knowledge-demo -->\n# Knowledge\n")
    return payload.getvalue()


def test_sync_bundle_extracts_skill_and_knowledge(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    release = {
        "tag_name": "skills-2026.07.30",
        "assets": [{"name": "xrefkit-skills-demo-1.0.0.zip", "browser_download_url": "https://example.test/demo.zip"}],
    }

    def fake_json(_url: str) -> dict:
        return release

    def fake_download(_asset: dict) -> tuple[str, bytes]:
        return "xrefkit-skills-demo-1.0.0.zip", _zip_bytes()

    monkeypatch.setattr("xrefkit.skills_sync._github_json", fake_json)
    monkeypatch.setattr("xrefkit.skills_sync._download_asset", fake_download)

    result = sync_bundle(repo=tmp_path, source_repository="owner/repo", bundle="demo")

    assert result.release == "skills-2026.07.30"
    assert (tmp_path / "skills/demo/SKILL.md").is_file()
    assert (tmp_path / "knowledge/demo.md").is_file()
    state = json.loads((tmp_path / ".xrefkit/skill-sync/demo.json").read_text(encoding="utf-8"))
    assert state["files"] == ["knowledge/demo.md", "skills/demo/SKILL.md", "skills/demo/meta.md"]


def test_sync_bundle_refuses_unmanaged_collision(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    release = {"tag_name": "v1", "assets": [{"name": "xrefkit-skills-demo-1.0.0.zip", "browser_download_url": "https://example.test/demo.zip"}]}
    monkeypatch.setattr("xrefkit.skills_sync._github_json", lambda _url: release)
    monkeypatch.setattr("xrefkit.skills_sync._download_asset", lambda _asset: ("demo.zip", _zip_bytes()))
    target = tmp_path / "skills/demo/SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("local", encoding="utf-8")

    with pytest.raises(RuntimeError, match="not owned by sync state"):
        sync_bundle(repo=tmp_path, source_repository="owner/repo", bundle="demo")

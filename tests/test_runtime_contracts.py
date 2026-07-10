from __future__ import annotations

import json
from pathlib import Path

import yaml

from xrefkit.contracts import compile_base_runtime, verify_base_runtime


def _fixture(tmp_path: Path, *, approval: str = "accepted", extra_must: bool = False) -> Path:
    source = tmp_path / "docs" / "contract.md"
    source.parent.mkdir(parents=True)
    extra = "- Client MUST review this pending rule.\n" if extra_must else ""
    source.write_text(
        "<!-- xid: A1234567890B -->\n<a id=\"xid-A1234567890B\"></a>\n\n"
        "# Contract\n\n- Client MUST load startup.\n" + extra,
        encoding="utf-8",
    )
    manifest = {
        "schema": "xrefkit.base_runtime/v1",
        "profile": "model-compact",
        "compiler_version": 1,
        "approval": {"status": approval, "owner": "test", "approved_on": "2026-07-10"},
        "estimator": {"id": "chars_div_4", "version": 1},
        "budgets": {"l0_tokens": 100, "l1_tokens": 200, "selected_context_tokens": 400},
        "sources": [{"xid": "A1234567890B", "path": "docs/contract.md"}],
        "obligations": [
            {
                "id": "startup.load",
                "source_xid": "A1234567890B",
                "level": "must",
                "statement": "Load startup.",
                "source_match": "Client MUST load startup.",
            }
        ],
        "conditional_loads": [],
    }
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def test_compile_base_runtime_writes_compact_resources(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)

    result = compile_base_runtime(tmp_path, manifest, "out")

    assert result["release_ready"] is True
    assert result["lint_candidates"] == []
    assert (tmp_path / "out" / "contracts.json").is_file()
    assert (tmp_path / "out" / "current.json").is_file()
    assert len(list((tmp_path / "out" / "generations").iterdir())) == 1
    compiled = json.loads((tmp_path / "out" / "contracts.json").read_text(encoding="utf-8"))
    assert compiled["obligations"][0]["id"] == "startup.load"


def test_release_verify_blocks_pending_lint_candidate(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path, extra_must=True)
    compile_base_runtime(tmp_path, manifest, "out")

    result = verify_base_runtime(tmp_path, manifest, "out", release=True)

    assert result["ok"] is False
    assert "pending normative lint candidates: 1" in result["errors"]


def test_draft_verify_allows_pending_and_unapproved_manifest(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path, approval="pending", extra_must=True)
    compile_base_runtime(tmp_path, manifest, "out")

    result = verify_base_runtime(tmp_path, manifest, "out", release=False)

    assert result["ok"] is True
    assert result["release_ready"] is False


def test_verify_does_not_rewrite_stale_compiled_output(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)
    compile_base_runtime(tmp_path, manifest, "out")
    generation = next((tmp_path / "out" / "generations").iterdir())
    output = generation / "contracts.json"
    output.write_text("{}", encoding="utf-8")

    result = verify_base_runtime(tmp_path, manifest, "out", release=True)

    assert result["ok"] is False
    assert "compiled contracts differ" in result["errors"][0]
    assert output.read_text(encoding="utf-8") == "{}"


def test_verify_reports_corrupt_model_body_as_structured_error(tmp_path: Path) -> None:
    manifest = _fixture(tmp_path)
    compile_base_runtime(tmp_path, manifest, "out")
    (tmp_path / "out" / "generations").joinpath(
        next((tmp_path / "out" / "generations").iterdir()).name,
        "model_body.md",
    ).write_bytes(b"\xff")

    result = verify_base_runtime(tmp_path, manifest, "out", release=True)

    assert result["ok"] is False
    assert any("compiled model body cannot be read" in error for error in result["errors"])

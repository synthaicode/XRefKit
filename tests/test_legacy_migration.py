from __future__ import annotations

import asyncio
import json
import sys
import subprocess
import os
from pathlib import Path

import pytest

from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.mcp.legacy_migration import (
    STATE, dismiss_legacy_migration, import_legacy_assets, migration_context,
    plan_legacy_migration, record_mcp_retrieval,
)


def legacy(tmp_path: Path) -> tuple[Path, Path]:
    source, root = tmp_path / "legacy", tmp_path / "target"
    root.mkdir()
    (source / "skills" / "nested" / "review").mkdir(parents=True)
    (source / "knowledge").mkdir()
    (source / "skills" / "nested" / "review" / "SKILL.md").write_text(
        "# Review\n\nUse [rules](../../../knowledge/rules.md).\n", encoding="utf-8")
    (source / "knowledge" / "rules.md").write_text("# Rules\n\nKeep evidence.\n", encoding="utf-8")
    (source / "knowledge" / "unlinked.txt").write_text("Independent knowledge.\n", encoding="utf-8")
    return source, root


def snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def documents(root: Path) -> list[dict]:
    data = json.loads((root / STATE).read_text(encoding="utf-8"))
    catalog = XRefCatalog.build(root)
    return [catalog.get_document_by_xid(a["xid"]) for unit in data["units"].values()
            for a in unit.get("artifacts", []) if unit["status"] == "installed"]


def test_first_partial_complete_restart_and_upgrade(tmp_path, monkeypatch):
    source, root = legacy(tmp_path)
    original = snapshot(source)
    catalog = XRefCatalog.build(root)
    first = catalog.get_startup_context()["legacy_migration"]
    assert first["status"] == "not_started"
    assert first["client_instructions"]
    assert not (root / STATE).exists()
    plan = plan_legacy_migration(root, str(source))
    assert "knowledge/unlinked.txt" in plan["targets"]
    assert "skills/nested/review" in plan["targets"]
    assert not (root / STATE).exists()  # inventory has no write side effect
    result = import_legacy_assets(root, str(source), plan["targets"])
    assert result["ok"]
    assert migration_context(root)["status"] == "in_progress"
    bodies = documents(root)
    # Catalog/CLI verification does not masquerade as an MCP retrieval.
    assert migration_context(root)["status"] == "in_progress"
    record_mcp_retrieval(root, bodies[:1])
    remaining = migration_context(root)
    assert remaining["status"] == "in_progress"
    assert sum(len(u["retrievals"]) for u in remaining["remaining"]) < len(bodies)
    record_mcp_retrieval(root, bodies)
    completed = migration_context(root)
    assert completed["status"] == "completed"
    assert completed["client_instructions"] == []
    assert completed["remaining"] == []
    state = (root / STATE).read_bytes()
    import xrefkit.mcp
    monkeypatch.setattr(xrefkit.mcp, "__version__", "999.0.0")
    restarted = XRefCatalog.build(root).get_startup_context({"irrelevant": "cached"})
    assert restarted["legacy_migration"]["status"] == "completed"
    assert (root / STATE).read_bytes() == state
    assert snapshot(source) == original


def test_explicit_scope_and_dismissal(tmp_path):
    source, root = legacy(tmp_path)
    assert dismiss_legacy_migration(root)["status"] == "not_required"
    assert XRefCatalog.build(root).get_startup_context()["legacy_migration"]["client_instructions"] == []
    result = import_legacy_assets(root, str(source), ["knowledge/unlinked.txt"])
    assert result["ok"]
    assert not (root / "skills").exists()
    with pytest.raises(ValueError, match="cannot dismiss"):
        dismiss_legacy_migration(root)
    record_mcp_retrieval(root, documents(root))
    assert migration_context(root)["status"] == "completed"


def test_conflict_failure_retry_and_existing_assets_protected(tmp_path):
    source, root = legacy(tmp_path)
    protected = root / "skills" / "imported.nested_review" / "SKILL.md"
    protected.parent.mkdir(parents=True)
    protected.write_bytes(b"Existing customized skill\n")
    result = import_legacy_assets(root, str(source), ["skills/nested/review", "knowledge/unlinked.txt"], prefix="imported")
    assert not result["ok"]
    remaining = migration_context(root)["remaining"]
    assert remaining[0]["status"] == "failed"
    assert "refusing to overwrite" in remaining[0]["error"]
    assert protected.read_bytes() == b"Existing customized skill\n"
    record_mcp_retrieval(root, documents(root))
    assert [u["target"] for u in migration_context(root)["remaining"]] == ["skills/nested/review"]
    # Simulate a user moving their customized file aside after reviewing conflict.
    protected.rename(protected.with_suffix(".backup"))
    assert import_legacy_assets(root, str(source), ["skills/nested/review"], prefix="imported")["ok"]
    record_mcp_retrieval(root, documents(root))
    assert migration_context(root)["status"] == "completed"
    assert protected.with_suffix(".backup").read_bytes() == b"Existing customized skill\n"


def test_partial_publish_retry_is_stable(tmp_path, monkeypatch):
    source, root = legacy(tmp_path)
    real_link = os.link
    failed = False
    def fail_once(source_path, destination, *args, **kwargs):
        nonlocal failed
        if Path(destination).name == "meta.md" and not failed:
            failed = True
            raise OSError("fixture disk failure")
        return real_link(source_path, destination, *args, **kwargs)
    monkeypatch.setattr(os, "link", fail_once)
    assert not import_legacy_assets(root, str(source), ["skills/nested/review"])["ok"]
    published = snapshot(root / "skills")
    assert import_legacy_assets(root, str(source), ["skills/nested/review"])["ok"]
    assert all(snapshot(root / "skills")[p] == b for p, b in published.items())
    record_mcp_retrieval(root, documents(root))
    assert migration_context(root)["status"] == "completed"


def test_receipts_require_matching_body_identity_and_content(tmp_path):
    source, root = legacy(tmp_path)
    import_legacy_assets(root, str(source), ["knowledge/unlinked.txt"])
    body = documents(root)[0]
    for wrong in ({**body, "content": None}, {**body, "content": "wrong"},
                  {**body, "path": "other.md"}, {**body, "xid": "wrong"}):
        record_mcp_retrieval(root, [wrong])
        assert migration_context(root)["status"] == "in_progress"
    record_mcp_retrieval(root, [body])
    assert migration_context(root)["status"] == "completed"
    state = json.loads((root / STATE).read_text(encoding="utf-8"))
    path = root / next(iter(state["units"].values()))["artifacts"][0]["path"]
    path.write_text("Customized after migration", encoding="utf-8")
    assert migration_context(root)["status"] == "in_progress"
    assert not import_legacy_assets(root, str(source), ["knowledge/unlinked.txt"])["ok"]
    assert path.read_text(encoding="utf-8") == "Customized after migration"


def test_corrupt_state_and_overlap_are_not_reset(tmp_path):
    source, root = legacy(tmp_path)
    for bad in ("{", '{"schema_version": 999, "units": {}}'):
        (root / STATE).parent.mkdir(exist_ok=True)
        (root / STATE).write_text(bad, encoding="utf-8")
        assert migration_context(root)["status"] == "blocked"
        with pytest.raises(ValueError):
            import_legacy_assets(root, str(source), ["knowledge/unlinked.txt"])
        assert (root / STATE).read_text(encoding="utf-8") == bad
    for overlap in (root, root.parent):
        with pytest.raises(ValueError, match="non-overlapping"):
            plan_legacy_migration(root, str(overlap))
    with pytest.raises(ValueError, match="exact targets"):
        import_legacy_assets(root, str(source), ["../escape"])


def test_existing_xid_conflict_preserves_catalog_and_source(tmp_path):
    source, root = legacy(tmp_path)
    xid = "ABCDEF012345"
    (source / "knowledge" / "rules.md").write_text(f"<!-- xid: {xid} -->\n# Legacy rules\n", encoding="utf-8")
    existing = root / "knowledge" / "existing.md"
    existing.parent.mkdir()
    existing.write_text(f"<!-- xid: {xid} -->\n# Customized rules\n", encoding="utf-8")
    before = snapshot(source)
    result = import_legacy_assets(root, str(source), ["knowledge/rules.md"])
    assert not result["ok"]
    assert "XID conflict" in result["migration"]["remaining"][0]["error"]
    assert XRefCatalog.build(root).get_document_by_xid(xid)["title"] == "Customized rules"
    assert snapshot(source) == before


def test_unsupported_skill_resources_are_reported_without_false_completion(tmp_path):
    source, root = legacy(tmp_path)
    (source / "skills/nested/review/helper.py").write_text("print('legacy')", encoding="utf-8")
    plan = plan_legacy_migration(root, str(source))
    assert "skills/nested/review/helper.py" in plan["unsupported"]
    assert not import_legacy_assets(root, str(source), ["skills/nested/review"])["ok"]
    assert migration_context(root)["status"] == "in_progress"
    assert not (root / "skills").exists()


def test_live_stdio_retrieval_and_restart(tmp_path):
    pytest.importorskip("mcp")
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    source, root = legacy(tmp_path)
    original = snapshot(source)
    params = StdioServerParameters(command=sys.executable,
                                  args=["-m", "xrefkit", "mcp", "serve", "--repo", str(root)])
    async def exercise():
        async def call(session, tool, arguments=None):
            result = await session.call_tool(tool, arguments or {})
            assert not result.isError, result
            return result.structuredContent or json.loads(result.content[0].text)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                startup = await call(session, "get_startup_context")
                assert startup["legacy_migration"]["status"] == "not_started"
                plan = await call(session, "plan_legacy_migration", {"source": str(source)})
                argv = [sys.executable, *plan["client_import_command"][1:]]
                for target in plan["targets"]:
                    argv.extend(["--target", target])
                proc = await asyncio.to_thread(subprocess.run, argv, capture_output=True, text=True, check=False)
                assert proc.returncode == 0, proc.stdout + proc.stderr
                result = json.loads(proc.stdout)
                assert result["ok"]
                skill_id = result["converted_skills"][0]["skill_id"]
                await call(session, "get_skill", {"skill_id": skill_id})
                context = (await call(session, "get_startup_context"))["legacy_migration"]
                assert context["status"] == "in_progress"
                for unit in context["remaining"]:
                    for pending in unit["retrievals"]:
                        await call(session, "get_document_by_xid", {"xid": pending["xid"]})
                assert (await call(session, "get_startup_context"))["legacy_migration"]["status"] == "completed"
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                context = (await call(session, "get_startup_context"))["legacy_migration"]
                assert context["status"] == "completed"
                assert not context["client_instructions"]
    asyncio.run(exercise())
    assert snapshot(source) == original

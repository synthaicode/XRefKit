from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

from xrefkit.mcp.audit import SessionRunBinding
from xrefkit.mcp.contribution_returns import (
    MAX_EVIDENCE_ROWS,
    MAX_METADATA_BYTES,
    export_contribution_return,
    list_contribution_returns,
    submit_contribution_return,
)


def binding() -> SessionRunBinding:
    return SessionRunBinding(
        run_id=str(uuid.uuid4()),
        mcp_session_id=str(uuid.uuid4()),
        repository_fingerprint="a" * 32,
        skill_id="sample",
    )


def source() -> dict:
    return {
        "provider_id": "xrefkit-mcp",
        "provider_version": "test",
        "package_id": None,
        "package_version": None,
        "skill_id": "sample",
        "skill_content_hash": "b" * 64,
        "knowledge_versions": [],
        "verification": "matched_current_catalog",
    }


def file(path: str, content: str) -> dict:
    return {
        "path": path,
        "content": content,
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def test_knowledge_submission_is_inert_idempotent_and_exportable(tmp_path: Path) -> None:
    contribution_id = str(uuid.uuid4())
    content = "<!-- xid: LOCAL123 -->\n\n# Local rule\n\nBody.\n"
    arguments = dict(
        binding=binding(), source_snapshot=source(), contribution_id=contribution_id,
        kind="knowledge", title="Local rule", summary="Review this rule",
        files=[file("knowledge/local_rule.md", content)], knowledge={"xid": "LOCAL123"},
    )

    created = submit_contribution_return(tmp_path, **arguments)
    replayed = submit_contribution_return(tmp_path, **arguments)
    listed = list_contribution_returns(tmp_path)
    exported = export_contribution_return(tmp_path, contribution_id)

    assert created["status"] == "pending_review"
    assert created["created"] is True
    assert replayed["idempotent_replay"] is True
    assert len(listed) == 1
    assert "content" not in listed[0]["files"][0]
    assert exported["activation_performed"] is False
    assert exported["review_bundle"]["files"][0]["content"] == content


def test_changed_retry_and_invalid_input_leave_original_unchanged(tmp_path: Path) -> None:
    contribution_id = str(uuid.uuid4())
    content = "<!-- xid: LOCAL123 -->\n\n# Local rule\n"
    common = dict(
        binding=binding(), source_snapshot=source(), contribution_id=contribution_id,
        kind="knowledge", title="Local rule", summary="Review this rule",
        knowledge={"xid": "LOCAL123"},
    )
    submit_contribution_return(tmp_path, files=[file("rule.md", content)], **common)

    with pytest.raises(ValueError, match="different payload"):
        submit_contribution_return(
            tmp_path, files=[file("rule.md", content + "changed\n")], **common
        )
    with pytest.raises(ValueError, match="unsafe contribution path"):
        submit_contribution_return(
            tmp_path,
            **{**common, "contribution_id": str(uuid.uuid4())},
            files=[file("../rule.md", content)],
        )
    assert len(list_contribution_returns(tmp_path)) == 1


@pytest.mark.parametrize(
    "unsafe_path",
    ["tools/check.py:stream", "CON", "tools/NUL.txt", "tools/check.py.", "tools/check.py "],
)
def test_windows_alias_paths_are_rejected(tmp_path: Path, unsafe_path: str) -> None:
    content = "<!-- xid: LOCAL123 -->\n\n# Local rule\n"
    with pytest.raises(ValueError, match="unsafe contribution path"):
        submit_contribution_return(
            tmp_path, binding=binding(), source_snapshot=source(),
            contribution_id=str(uuid.uuid4()), kind="knowledge", title="Local",
            summary="Review", files=[file(unsafe_path, content)],
            knowledge={"xid": "LOCAL123"},
        )


def test_case_alias_paths_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duplicate contribution path"):
        submit_contribution_return(
            tmp_path, binding=binding(), source_snapshot=source(),
            contribution_id=str(uuid.uuid4()), kind="deterministic_tool", title="Tool",
            summary="Review", files=[file("tools/A.py", "a"), file("TOOLS/a.PY", "b")],
            deterministic_tool={
                "runtime": "python", "entrypoint": "tools/A.py",
                "input_contract": {}, "output_contract": {},
                "verification_evidence": [{"kind": "test", "command": "x", "result": "pass"}],
            },
        )


def test_metadata_limits_are_enforced_before_persistence(tmp_path: Path) -> None:
    content = "<!-- xid: LOCAL123 -->\n\n# Local rule\n"
    with pytest.raises(ValueError, match="summary exceeds byte limit"):
        submit_contribution_return(
            tmp_path, binding=binding(), source_snapshot=source(),
            contribution_id=str(uuid.uuid4()), kind="knowledge", title="Local",
            summary="x" * (MAX_METADATA_BYTES + 1), files=[file("rule.md", content)],
            knowledge={"xid": "LOCAL123"},
        )
    assert list_contribution_returns(tmp_path) == []


def test_evidence_row_limit_is_enforced(tmp_path: Path) -> None:
    evidence = [
        {"kind": "test", "command": "x", "result": "pass"}
        for _ in range(MAX_EVIDENCE_ROWS + 1)
    ]
    with pytest.raises(ValueError, match="evidence exceeds row limit"):
        submit_contribution_return(
            tmp_path, binding=binding(), source_snapshot=source(),
            contribution_id=str(uuid.uuid4()), kind="deterministic_tool", title="Tool",
            summary="Review", files=[file("tools/check.py", "pass\n")],
            deterministic_tool={
                "runtime": "python", "entrypoint": "tools/check.py",
                "input_contract": {}, "output_contract": {},
                "verification_evidence": evidence,
            },
        )


def test_contract_metadata_total_and_depth_are_bounded(tmp_path: Path) -> None:
    common = dict(
        binding=binding(), source_snapshot=source(), kind="deterministic_tool",
        title="Tool", summary="Review", files=[file("tools/check.py", "pass\n")],
    )
    base_tool = {
        "runtime": "python", "entrypoint": "tools/check.py", "output_contract": {},
        "verification_evidence": [{"kind": "test", "command": "x", "result": "pass"}],
    }
    with pytest.raises(ValueError, match="exceeds byte limit"):
        submit_contribution_return(
            tmp_path, contribution_id=str(uuid.uuid4()), **common,
            deterministic_tool={**base_tool, "input_contract": {"description": "x" * MAX_METADATA_BYTES}},
        )
    with pytest.raises(ValueError, match="metadata exceeds byte limit"):
        submit_contribution_return(
            tmp_path, contribution_id=str(uuid.uuid4()), **common,
            deterministic_tool={
                **base_tool,
                "input_contract": {f"field{index}": "x" * 60_000 for index in range(5)},
            },
        )
    nested: dict[str, object] = {}
    cursor = nested
    for _ in range(20):
        child: dict[str, object] = {}
        cursor["child"] = child
        cursor = child
    with pytest.raises(ValueError, match="JSON depth limit"):
        submit_contribution_return(
            tmp_path, contribution_id=str(uuid.uuid4()), **common,
            deterministic_tool={**base_tool, "input_contract": nested},
        )


def test_deterministic_tool_requires_contract_evidence_and_is_not_executed(tmp_path: Path) -> None:
    content = "raise RuntimeError('must not execute during intake')\n"
    result = submit_contribution_return(
        tmp_path,
        binding=binding(), source_snapshot=source(), contribution_id=str(uuid.uuid4()),
        kind="deterministic_tool", title="Checker", summary="Review the checker",
        files=[file("tools/check.py", content)],
        deterministic_tool={
            "runtime": "python>=3.11", "entrypoint": "tools/check.py",
            "input_contract": {"type": "object"},
            "output_contract": {"type": "object"},
            "verification_evidence": [
                {"kind": "test", "command": "pytest", "result": "passed"}
            ],
        },
    )
    assert result["kind"] == "deterministic_tool"
    assert result["status"] == "pending_review"


def test_contribution_return_over_real_mcp_stdio(tmp_path: Path) -> None:
    anyio = pytest.importorskip("anyio")
    pytest.importorskip("mcp")
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    root = Path(__file__).resolve().parents[1]
    contribution_id = str(uuid.uuid4())
    record_dir = root / ".xrefkit" / "contribution-returns" / contribution_id

    async def scenario(errlog) -> None:
        parameters = StdioServerParameters(
            command=sys.executable,
            cwd=str(root),
            args=["-m", "xrefkit.mcp.server", "--repo", str(root),
                  "--audit-log", str(tmp_path / "audit.jsonl")],
        )
        async with stdio_client(parameters, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                startup = await session.call_tool("get_startup_context", {})
                assert not startup.isError
                rejected = await session.call_tool("submit_contribution_return", {
                    "contribution_id": contribution_id, "kind": "knowledge",
                    "title": "Returned", "summary": "Review", "files": [],
                    "skill_content_hash": "0" * 64, "knowledge": {"xid": "RETURN123"}})
                assert rejected.isError
                assert "XREFKIT_SKILL_RUN_REQUIRED" in rejected.content[0].text

                skill = await session.call_tool("get_skill", {"skill_id": "python_review"})
                skill_body = skill.structuredContent["skill_content"]
                skill_hash = hashlib.sha256(skill_body.encode("utf-8")).hexdigest()
                run_id = str(uuid.uuid4())
                bound = await session.call_tool(
                    "bind_skill_run", {"run_id": run_id, "skill_id": "python_review"}
                )
                assert not bound.isError
                contract = await session.call_tool("get_contribution_return_contract", {})
                assert contract.structuredContent["status"] == "pending_review"
                body = "<!-- xid: RETURN123 -->\n\n# Returned Knowledge\n\nBody.\n"
                args = {
                    "contribution_id": contribution_id,
                    "kind": "knowledge",
                    "title": "Returned Knowledge",
                    "summary": "Review this local learning",
                    "files": [file("knowledge/returned.md", body)],
                    "skill_content_hash": skill_hash,
                    "knowledge_versions": [],
                    "knowledge": {"xid": "RETURN123"},
                }
                stale_source = await session.call_tool(
                    "submit_contribution_return", {**args, "skill_content_hash": "0" * 64}
                )
                assert stale_source.isError
                assert "does not match the current MCP Skill body" in stale_source.content[0].text
                submitted = await session.call_tool("submit_contribution_return", args)
                replayed = await session.call_tool("submit_contribution_return", args)
                assert not submitted.isError
                assert submitted.structuredContent["status"] == "pending_review"
                assert replayed.structuredContent["idempotent_replay"] is True
                listed = await session.call_tool("list_contribution_returns", {})
                rows = listed.structuredContent["result"]
                assert any(row["contribution_id"] == contribution_id for row in rows)
                exported = await session.call_tool(
                    "export_contribution_return", {"contribution_id": contribution_id}
                )
                assert exported.structuredContent["activation_performed"] is False
                knowledge = await session.call_tool("list_knowledge_catalog", {})
                assert "RETURN123" not in {
                    row["xid"] for row in knowledge.structuredContent["result"]
                }

    try:
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
            anyio.run(scenario, errlog)
    finally:
        shutil.rmtree(record_dir, ignore_errors=True)
        inbox = record_dir.parent
        for lock_file in (inbox / "inbox.lock", inbox / "inbox.lock.lock"):
            lock_file.unlink(missing_ok=True)
        try:
            inbox.rmdir()
            inbox.parent.rmdir()
        except OSError:
            pass

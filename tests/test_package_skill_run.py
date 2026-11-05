import pytest


@pytest.mark.parametrize(
    ("module", "reference", "xid"),
    [
        ("xrefkit_skills_csharp", "xrefkit.skills.csharp::csharp.review", "xid-skill-csharp-review"),
        ("xrefkit_skills_brownfield", "xrefkit.skills.brownfield::brownfield.workflow", "xid-skill-brownfield-workflow"),
        ("xrefkit_skills_batch_regression", "xrefkit.skills.batch_regression::batch.impact_regression", "xid-skill-batch-impact-regression"),
    ],
)
def test_installed_package_run_binds_over_mcp(tmp_path, module, reference, xid):
    import json
    import os
    import subprocess
    import sys
    import tempfile
    from pathlib import Path

    pytest.importorskip(module)
    from xrefkit.discovery import discover_skill_packages
    package_id = reference.split("::")[0]
    package = next(item for item in discover_skill_packages() if item.package_id == package_id)
    package_knowledge_xids = [asset.xid for asset in package.manifest.provides.knowledge]
    anyio = pytest.importorskip("anyio")
    pytest.importorskip("mcp")
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    repo = Path(__file__).resolve().parents[1]
    cli = [sys.executable, "-m", "xrefkit"]

    env = {**os.environ, "PYTHONPATH": str(repo)}

    def run_cli(*args):
        return subprocess.check_output(
            cli + list(args), cwd=tmp_path, env=env, encoding="utf-8"
        )

    args = [
        "skill", "run",
        "--package-skill", reference,
        "--task", "Verify package run startup and MCP binding",
        "--capability", "integration verification", "--tuning", "XRefKit package startup",
        "--responsibility", "Verify run creation and correlation",
        "--execution-mode", "subagent_required", "--json",
    ]
    run = json.loads(run_cli(*args))
    assert run["skill_id"] == reference.split("::")[1]
    log_path = Path(run["run_log"])
    assert log_path.is_relative_to(tmp_path)
    assert Path(run["skill_doc"]).is_file()
    log = log_path.read_text(encoding="utf-8")
    assert "maturity: `unassessed`" in log
    assert f"package_skill_xid: `{xid}`" in log
    assert "package_skill_sha256:" in log

    rejected = subprocess.run(
        cli + [arg for arg in args if arg not in {"--capability", "integration verification"}],
        cwd=tmp_path, env=env, capture_output=True, encoding="utf-8",
    )
    assert rejected.returncode == 1
    assert json.loads(rejected.stdout)["run_id"] is None

    async def scenario():
        server = StdioServerParameters(
            command=sys.executable,
            args=[
                "-m", "xrefkit.mcp.server", "--repo", str(repo),
                "--audit-log", str(tmp_path / "mcp-audit.jsonl"),
            ],
            cwd=str(repo),
        )
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr:
            async with stdio_client(server, errlog=stderr) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    startup = await session.call_tool("get_startup_context", {})
                    assert not startup.isError, startup.content
                    binding = await session.call_tool(
                        "bind_skill_run",
                        {"run_id": run["run_id"], "skill_id": run["skill_id"]},
                    )
                    assert not binding.isError, binding.content
                    bound = binding.structuredContent
                    assert bound["run_id"] == run["run_id"]
                    assert bound["skill_id"] == run["skill_id"]
                    assert "xrefkit skill correlate" in bound["client_record_command"]
                    run_cli(
                        "skill", "correlate", "--log", str(log_path),
                        "--run-id", bound["run_id"],
                        "--mcp-session-id", bound["mcp_session_id"],
                        "--repository-fingerprint", bound["repository_fingerprint"],
                    )
                    assert bound["mcp_session_id"] in log_path.read_text(encoding="utf-8")
                    requirements = await session.call_tool(
                        "get_skill_requirements", {"skill_id": run["skill_id"]}
                    )
                    assert not requirements.isError, requirements.content
                    assert not requirements.structuredContent["missing"]
                    for xid in package_knowledge_xids:
                        document = await session.call_tool("get_document_by_xid", {"xid": xid})
                        assert not document.isError, document.content
                        expanded = await session.call_tool("expand_knowledge", {"xid": xid})
                        assert not expanded.isError, expanded.content
                        assert expanded.structuredContent["content"]

                    skill = await session.call_tool("get_skill", {"skill_id": run["skill_id"]})
                    assert not skill.isError, skill.content
                    assert skill.structuredContent["skill_id"] == run["skill_id"]

    anyio.run(scenario)

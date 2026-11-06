"""Smoke installed official packages through real MCP, outside the checkout."""
import asyncio
import importlib.metadata
import os
import sys
import tempfile
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from xrefkit.discovery import discover_skill_packages


async def main():
    for name, version in (("xrefkit-skills-brownfield", "0.1.6"), ("xrefkit-skills-csharp", "0.1.4")):
        assert importlib.metadata.version(name) == version
    packages = discover_skill_packages()
    checks = 0
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "xrefkit.mcp.server", "--repo", str(root), "--audit-log", str(root / "audit.jsonl")],
            cwd=str(root),
            env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
        )
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errors:
            async with stdio_client(server, errlog=errors) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    async def call(name, arguments):
                        nonlocal checks
                        result = await session.call_tool(name, arguments)
                        assert not result.isError, (name, result.content)
                        checks += 1
                        return result.structuredContent

                    await call("get_startup_context", {})
                    for package in packages:
                        provides = package.manifest.provides
                        for asset in provides.knowledge:
                            await call("get_document_by_xid", {"xid": asset.xid})
                            await call("expand_knowledge", {"xid": asset.xid})
                        for asset in [*provides.review_axes, *provides.schemas]:
                            await call("get_document_by_xid", {"xid": asset.xid})
                        for skill in provides.skills:
                            resolved = await call("resolve_skill_knowledge", {"skill_id": skill.id})
                            assert resolved["slots"]
                            assert not resolved["unsatisfied_required"], resolved
    print(f"Installed combined package MCP: {checks} checks passed")


if __name__ == "__main__":
    asyncio.run(main())

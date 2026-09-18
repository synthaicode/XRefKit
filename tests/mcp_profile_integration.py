from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys


class McpProfileIntegrationTests(unittest.TestCase):
    def test_reader_hides_update_tools_and_admin_exposes_them(self) -> None:
        try:
            import anyio
            from mcp.client.session import ClientSession
            from mcp.client.stdio import StdioServerParameters, stdio_client
        except ImportError as exc:
            self.skipTest(f"mcp integration dependency is unavailable: {exc}")

        async def tool_names(profile: str) -> tuple[set[str], dict]:
            repo = Path(__file__).resolve().parents[1]
            with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr:
                server = StdioServerParameters(
                    command=sys.executable,
                    args=[
                        "-m",
                        "xrefkit.mcp.server",
                        "--repo",
                        str(repo),
                        "--profile",
                        profile,
                        "--audit-log",
                        str(Path(tempfile.gettempdir()) / f"xrefkit-{profile}-audit.jsonl"),
                    ],
                    cwd=str(repo),
                )
                async with stdio_client(server, errlog=stderr) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tools = await session.list_tools()
                        startup = await session.call_tool("get_startup_context", {})
                        return (
                            {item.name for item in tools.tools},
                            startup.structuredContent["server_profile"],
                        )

        reader_tools, reader_profile = anyio.run(tool_names, "reader")
        admin_tools, admin_profile = anyio.run(tool_names, "admin")

        self.assertNotIn("prepare_skill_edit", reader_tools)
        self.assertNotIn("create_local_knowledge", reader_tools)
        self.assertNotIn("create_contribution_upload_session", reader_tools)
        self.assertNotIn("adopt_contribution_return", reader_tools)
        self.assertIn("prepare_skill_edit", admin_tools)
        self.assertIn("create_local_knowledge", admin_tools)
        self.assertIn("create_contribution_upload_session", admin_tools)
        self.assertIn("adopt_contribution_return", admin_tools)
        self.assertEqual(reader_profile["name"], "reader")
        self.assertIs(reader_profile["skill_updates"], False)
        self.assertEqual(admin_profile["name"], "admin")
        self.assertIs(admin_profile["skill_updates"], True)
        self.assertEqual(admin_profile["update_transport"], "local_overlay")
        self.assertIs(admin_profile["inbound_webdav"], False)

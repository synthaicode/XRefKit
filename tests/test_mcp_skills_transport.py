from __future__ import annotations

from datetime import timedelta
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

try:
    import anyio
    from mcp import types
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from mcp.shared.exceptions import McpError
except ImportError as exc:
    raise unittest.SkipTest(f"optional MCP integration dependency unavailable: {exc}") from exc
from pydantic import RootModel

from xrefkit.mcp.skills_extension import EXTENSION_ID


async def request(session, method, params=None):
    data = {"method": method}
    if params is not None:
        data["params"] = params
    return (await session.send_request(RootModel(data), types.EmptyResult, request_read_timeout_seconds=timedelta(seconds=20))).model_dump(by_alias=True, exclude_none=True)


class SkillsStdioTests(unittest.TestCase):
    def test_actual_server_wire_and_legacy_tools(self):
        async def scenario():
            repo = Path(__file__).resolve().parents[1]
            with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr:
                server = StdioServerParameters(command=sys.executable, args=["-m", "xrefkit.mcp.server", "--repo", str(repo), "--audit-log", str(Path(tmp) / "audit.jsonl")], cwd=str(repo))
                async with stdio_client(server, errlog=stderr) as (read, write):
                    async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
                        initialized = await session.initialize()
                        self.assertEqual(initialized.protocolVersion, "2025-11-25")
                        self.assertEqual(initialized.capabilities.model_extra["extensions"][EXTENSION_ID], {})
                        self.assertIsNotNone(initialized.capabilities.resources)
                        listing = await request(session, "skills/list", {})
                        self.assertEqual(listing["resultType"], "complete")
                        self.assertTrue(listing["skills"])
                        entry = listing["skills"][0]
                        self.assertEqual((await request(session, "skills/get", {"uri": entry["uri"]}))["skill"], entry)
                        resource = await session.read_resource(entry["uri"])
                        raw = resource.contents[0].text.encode("utf-8")
                        self.assertEqual(entry["resources"][0]["digest"], "sha256:" + hashlib.sha256(raw).hexdigest())
                        self.assertEqual(entry["resources"][0]["size"], len(raw))
                        self.assertIn(entry["uri"], {str(item.uri) for item in (await session.list_resources()).resources})
                        # Resource inspection must not have satisfied legacy startup.
                        denied = await session.call_tool("get_skill", {"skill_id": entry["frontmatter"]["metadata"]["xrefkit-skill-id"]})
                        self.assertTrue(denied.isError)
                        tools = {tool.name for tool in (await session.list_tools()).tools}
                        self.assertIn("get_startup_context", tools)
                        self.assertIn("get_skill", tools)
                        self.assertNotIn("skills/list", tools)
                        startup = await session.call_tool("get_startup_context", {})
                        self.assertFalse(startup.isError)
                        native = await session.call_tool("get_skill", {"skill_id": entry["frontmatter"]["metadata"]["xrefkit-skill-id"]})
                        self.assertFalse(native.isError)
                        for method, params in [("skills/get", {}), ("skills/get", {"uri": True}), ("skills/get", {"uri": None}), ("skills/get", {"uri": []}), ("skills/get", {"uri": "skill://xrefkit/../secret"}), ("skills/list", {"cursor": "unknown"}), ("skills/list", {"cursor": True}), ("skills/list", {"cursor": []}), ("resources/read", {"uri": "skill://xrefkit/%2e%2e/secret"})]:
                            with self.subTest(method=method, params=params):
                                with self.assertRaises(McpError) as caught:
                                    await request(session, method, params)
                                self.assertEqual(caught.exception.error.code, -32602)
                        await session.send_ping()
        anyio.run(scenario)


class SkillsHttpTests(unittest.TestCase):
    def test_http_extension_and_legacy_dispatch(self):
        try:
            from starlette.testclient import TestClient
        except ImportError as exc:
            self.skipTest(f"optional HTTP test dependency unavailable: {exc}")
        from xrefkit.mcp.catalog import XRefCatalog
        from xrefkit.mcp.skills_extension import SkillsExtension
        from xrefkit.mcp.skills_transport import SkillsFastMCP, install_skills_handlers

        repo = Path(__file__).resolve().parents[1]
        catalog = XRefCatalog.build(repo, discover_packages=False)
        app = SkillsFastMCP("skills-http-test", stateless_http=True, json_response=True)
        install_skills_handlers(app, SkillsExtension(catalog))

        @app.tool()
        def legacy_echo(value: str) -> str:
            return value

        with TestClient(app.streamable_http_app(), base_url="http://127.0.0.1:8000") as client:
            def send(method, params):
                response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, headers={"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-11-25"})
                self.assertEqual(response.status_code, 200, response.text)
                return response.json()

            initialized = send("initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}})["result"]
            self.assertEqual(initialized["capabilities"]["extensions"][EXTENSION_ID], {})
            entries = send("skills/list", {})["result"]["skills"]
            self.assertTrue(entries)
            entry = entries[0]
            self.assertEqual(send("skills/get", {"uri": entry["uri"]})["result"]["skill"], entry)
            raw = send("resources/read", {"uri": entry["uri"]})["result"]["contents"][0]["text"].encode("utf-8")
            self.assertEqual(entry["resources"][0]["digest"], "sha256:" + hashlib.sha256(raw).hexdigest())
            self.assertEqual(send("skills/list", {"cursor": None})["error"]["code"], -32602)
            self.assertEqual(send("skills/get", {"uri": "skill://xrefkit/unknown/SKILL.md"})["error"]["code"], -32602)
            result = send("tools/call", {"name": "legacy_echo", "arguments": {"value": "still works"}})["result"]
            self.assertFalse(result["isError"])
            self.assertEqual(result["content"][0]["text"], "still works")


if __name__ == "__main__":
    unittest.main()

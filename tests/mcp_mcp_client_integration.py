from __future__ import annotations

import base64
import io
import tempfile
import unittest
import zipfile


class McpClientIntegrationTests(unittest.TestCase):
    def test_startup_and_skill_links_resolve_over_mcp(self) -> None:
        try:
            import anyio
            from mcp.client.session import ClientSession
            from mcp.client.stdio import StdioServerParameters, stdio_client
        except ImportError as exc:
            self.skipTest(f"mcp integration dependency is unavailable: {exc}")

        # errlog needs a real OS file handle on Windows (subprocess creation
        # calls stderr.fileno()), so a plain io.StringIO() will not work here.
        captured_stderr = tempfile.TemporaryFile(mode="w+", encoding="utf-8")
        results: dict[str, object] = {}

        async def scenario() -> None:
            server = StdioServerParameters(
                command="python",
                args=[
                    "-m",
                    "xrefkit.mcp.server",
                    "--repo",
                    r"C:\dev\itsm\XRefKit",
                ],
                cwd=r"C:\dev\itsm\XRefKit",
            )
            async with stdio_client(server, errlog=captured_stderr) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    identity_result = await session.call_tool(
                        "get_repository_identity",
                        {},
                    )
                    identity = identity_result.structuredContent
                    self.assertEqual(
                        len(identity["repository_fingerprint"]),
                        32,
                    )
                    self.assertEqual(
                        identity["cache_namespace"],
                        identity["repository_fingerprint"],
                    )

                    rejected_result = await session.call_tool(
                        "get_document_by_xid",
                        {"xid": "8A666C1FD121"},
                    )
                    self.assertTrue(rejected_result.isError)
                    self.assertIn(
                        "XREFKIT_STARTUP_REQUIRED",
                        rejected_result.content[0].text,
                    )

                    rejected_fm_result = await session.call_tool(
                        "get_xrefkit_runtime_manifest", {}
                    )
                    self.assertTrue(rejected_fm_result.isError)
                    self.assertIn(
                        "XREFKIT_STARTUP_REQUIRED",
                        rejected_fm_result.content[0].text,
                    )

                    rejected_bodies_result = await session.call_tool(
                        "list_skills",
                        {"include_content": True, "limit": 1},
                    )
                    self.assertTrue(rejected_bodies_result.isError)
                    self.assertIn(
                        "XREFKIT_STARTUP_REQUIRED",
                        rejected_bodies_result.content[0].text,
                    )

                    metadata_skills_result = await session.call_tool(
                        "list_skills",
                        {"limit": 1},
                    )
                    self.assertFalse(metadata_skills_result.isError)
                    metadata_entry = metadata_skills_result.structuredContent[
                        "result"
                    ][0]
                    self.assertIsNone(metadata_entry["meta_content"])
                    self.assertIsNone(metadata_entry["skill_content"])
                    self.assertTrue(metadata_entry["document_versions"])

                    startup_result = await session.call_tool("get_startup_context", {})
                    startup = startup_result.structuredContent
                    self.assertEqual(
                        startup["repository_identity"]["repository_fingerprint"],
                        identity["repository_fingerprint"],
                    )
                    self.assertEqual(
                        startup["link_resolution"]["resolver_tool"],
                        "get_document_by_xid",
                    )
                    self.assertEqual(startup["access_policy"]["mode"], "mcp_only")
                    self.assertEqual(
                        startup["access_policy"]["required_tools"]["xid_link_resolution"],
                        "get_document_by_xid",
                    )
                    self.assertTrue(
                        any(
                            "get_document_by_xid" in instruction
                            for instruction in startup["client_instructions"]
                        )
                    )
                    obligation_ids = {
                        obligation["id"] for obligation in startup["client_obligations"]
                    }
                    self.assertIn("startup.first_call", obligation_ids)
                    self.assertIn("tools.materialize_from_mcp", obligation_ids)
                    self.assertIn("core_runtime.fetch_immediately", obligation_ids)

                    core_runtime = startup["core_runtime_distribution"]
                    self.assertEqual(core_runtime["package_id"], "xrefkit")
                    self.assertIs(
                        core_runtime["update_policy"]["gated_by_skill_selection"], False
                    )

                    # Unlike client_tool_download, the xrefkit runtime must be
                    # reachable without ever selecting a Skill first.
                    fm_bundle_result = await session.call_tool(
                        "get_xrefkit_runtime_bundle", {}
                    )
                    self.assertFalse(fm_bundle_result.isError)
                    fm_bundle = fm_bundle_result.structuredContent
                    fm_paths = {file["path"] for file in fm_bundle["files"]}
                    self.assertIn("xrefkit/__init__.py", fm_paths)
                    self.assertIn("xrefkit/skillrun.py", fm_paths)

                    fm_file_result = await session.call_tool(
                        "get_xrefkit_runtime_file", {"path": "xrefkit/__init__.py"}
                    )
                    self.assertIn("__version__", fm_file_result.structuredContent["content"])

                    fm_package_result = await session.call_tool(
                        "get_xrefkit_runtime_pip_package", {}
                    )
                    fm_package = fm_package_result.structuredContent
                    self.assertEqual(fm_package["package_id"], "xrefkit")
                    self.assertGreater(len(fm_package["content_base64"]), 1000)

                    fm_version_result = await session.call_tool(
                        "check_xrefkit_runtime_version", {"installed": {}}
                    )
                    self.assertIs(fm_version_result.structuredContent["ok"], False)

                    uncertainty = next(
                        ref
                        for ref in startup["references"]
                        if ref["xid"] == "8A666C1FD121"
                    )
                    self.assertIsNone(uncertainty["content"])
                    self.assertIs(uncertainty["content_omitted"], True)
                    self.assertIs(uncertainty["included_in_startup_contract_pack"], True)
                    self.assertIn(
                        "Startup Contract Pack v1",
                        startup["startup_contract_pack"]["body"],
                    )
                    self.assertEqual(
                        startup["startup_contract_pack"]["source_hashes"][uncertainty["xid"]],
                        uncertainty["content_hash"],
                    )
                    self.assertGreater(len(uncertainty["links"]), 0)
                    self.assertEqual(
                        uncertainty["links"][0]["resolver_tool"],
                        "get_document_by_xid",
                    )
                    cached_startup_result = await session.call_tool(
                        "get_startup_context",
                        {
                            "known_document_versions": {
                                ref["xid"]: ref["content_hash"]
                                for ref in startup["references"]
                            }
                        },
                    )
                    cached_startup = cached_startup_result.structuredContent
                    self.assertTrue(
                        all(
                            ref["content_omitted"]
                            and ref["content"] is None
                            and ref["included_in_startup_contract_pack"]
                            for ref in cached_startup["references"]
                        )
                    )

                    startup_link_xid = uncertainty["links"][0]["xid"]
                    startup_doc_result = await session.call_tool(
                        "get_document_by_xid", {"xid": startup_link_xid}
                    )
                    startup_doc = startup_doc_result.structuredContent
                    self.assertEqual(startup_doc["xid"], startup_link_xid)
                    self.assertEqual(
                        startup_doc["repository_fingerprint"],
                        identity["repository_fingerprint"],
                    )
                    self.assertGreater(len(startup_doc["content"]), 1000)
                    self.assertIn("control_reminder", startup_doc)
                    cached_doc_result = await session.call_tool(
                        "get_document_by_xid",
                        {
                            "xid": startup_link_xid,
                            "known_version": startup_doc["content_hash"],
                        },
                    )
                    cached_doc = cached_doc_result.structuredContent
                    self.assertEqual(cached_doc["cache_status"], "not_modified")
                    self.assertIs(cached_doc["content_omitted"], True)
                    self.assertNotIn("content", cached_doc)

                    rejected_manifest_result = await session.call_tool(
                        "get_client_tool_manifest", {}
                    )
                    self.assertTrue(rejected_manifest_result.isError)
                    self.assertIn(
                        "XREFKIT_SKILL_SELECTION_REQUIRED",
                        rejected_manifest_result.content[0].text,
                    )

                    skill_result = await session.call_tool(
                        "get_skill", {"skill_id": "csharp_review"}
                    )
                    skill = skill_result.structuredContent
                    self.assertEqual(skill["skill_id"], "csharp_review")
                    self.assertIn("# Skill: csharp_review", skill["skill_content"])
                    self.assertGreater(len(skill["skill_links"]), 0)
                    self.assertIn("client_tool_download", skill)
                    self.assertIs(skill["client_tool_download"]["do_not_download_at_startup"], True)
                    self.assertEqual(
                        skill["client_tool_download"]["manifest_tool"],
                        "get_client_tool_manifest",
                    )
                    self.assertEqual(
                        skill["skill_links"][0]["resolver_tool"],
                        "get_document_by_xid",
                    )
                    cache_aware_skill_result = await session.call_tool(
                        "get_skill",
                        {
                            "skill_id": "csharp_review",
                            "known_document_versions": {},
                        },
                    )
                    cache_aware_skill = cache_aware_skill_result.structuredContent
                    self.assertIsNone(cache_aware_skill["meta_content"])
                    self.assertIsNone(cache_aware_skill["skill_content"])
                    self.assertEqual(len(cache_aware_skill["documents"]), 2)
                    skill_versions = {
                        document["xid"]: document["content_hash"]
                        for document in cache_aware_skill["documents"]
                    }
                    cached_skill_result = await session.call_tool(
                        "get_skill",
                        {
                            "skill_id": "csharp_review",
                            "known_document_versions": skill_versions,
                        },
                    )
                    cached_skill = cached_skill_result.structuredContent
                    self.assertTrue(
                        all(
                            document["cache_status"] == "not_modified"
                            and "content" not in document
                            for document in cached_skill["documents"]
                        )
                    )

                    skill_link_xid = skill["skill_links"][0]["xid"]
                    skill_doc_result = await session.call_tool(
                        "get_document_by_xid", {"xid": skill_link_xid}
                    )
                    skill_doc = skill_doc_result.structuredContent
                    self.assertEqual(skill_doc["xid"], skill_link_xid)
                    self.assertGreater(len(skill_doc["content"]), 1000)

                    manifest_result = await session.call_tool(
                        "get_client_tool_manifest", {}
                    )
                    manifest = manifest_result.structuredContent
                    self.assertEqual(manifest["execution_location"], "client")
                    self.assertEqual(manifest["version"], "0.1.0")
                    self.assertIs(manifest["server_executes_tools"], False)
                    self.assertEqual(manifest["file_hash_algorithm"], "sha256")
                    self.assertEqual(
                        manifest["materialization"]["bundle_tool"],
                        "get_client_tool_bundle",
                    )
                    self.assertIn("xrefkit-client-tools", manifest["required_package_ids"])
                    self.assertTrue(
                        any(
                            file["path"] == "tools/cs_scope_probe.py"
                            for file in manifest["files"]
                        )
                    )
                    self.assertTrue(
                        any(
                            file["path"]
                            == "skills/import_skill/scripts/inspect_imported_skill.py"
                            for file in manifest["files"]
                        )
                    )

                    tool_file_result = await session.call_tool(
                        "get_client_tool_file",
                        {"path": "tools/cs_scope_probe.py"},
                    )
                    tool_file = tool_file_result.structuredContent
                    self.assertEqual(tool_file["kind"], "python")
                    self.assertIn("argparse", tool_file["imports"])
                    self.assertIn("def main", tool_file["content"])

                    skill_script_result = await session.call_tool(
                        "get_client_tool_file",
                        {
                            "path": "skills/import_skill/scripts/inspect_imported_skill.py"
                        },
                    )
                    skill_script = skill_script_result.structuredContent
                    self.assertEqual(skill_script["kind"], "python")
                    self.assertEqual(
                        skill_script["run_hint"],
                        "python skills/import_skill/scripts/inspect_imported_skill.py",
                    )

                    package_result = await session.call_tool(
                        "get_client_tool_pip_package", {}
                    )
                    package = package_result.structuredContent
                    self.assertEqual(package["package_format"], "zip-sdist")
                    self.assertEqual(package["version"], "0.1.0")
                    self.assertIn("python -m pip install", package["install_command"])
                    self.assertGreater(len(package["content_base64"]), 1000)
                    self.assertTrue(
                        any(
                            "skills" in warning
                            for warning in package["warnings"]
                        )
                    )
                    package_zip = zipfile.ZipFile(
                        io.BytesIO(base64.b64decode(package["content_base64"]))
                    )
                    self.assertFalse(
                        any("/skills/" in name for name in package_zip.namelist())
                    )

                    version_result = await session.call_tool(
                        "check_client_tool_versions",
                        {
                            "installed": {
                                "xrefkit-client-python-tools": "0.1.0",
                                "xrefkit-client-tools": "0.1.0",
                            }
                        },
                    )
                    self.assertIs(version_result.structuredContent["ok"], True)

                    contracts_result = await session.call_tool("list_tool_contracts", {})
                    contracts = {
                        contract["tool_id"]: contract
                        for contract in contracts_result.structuredContent["result"]
                    }
                    self.assertEqual(
                        contracts["xref.list_skills"]["response_envelope"],
                        "mcp_result_array",
                    )
                    self.assertEqual(
                        contracts["xref.get_document_by_xid"]["input_json_schema"]["properties"]["xid"]["type"],
                        "string",
                    )

                    knowledge_context_result = await session.call_tool(
                        "build_knowledge_context",
                        {"query": "csharp review synchronization", "limit": 3},
                    )
                    knowledge_context = knowledge_context_result.structuredContent
                    self.assertGreater(len(knowledge_context["entries"]), 0)
                    results["knowledge_context"] = knowledge_context

        anyio.run(scenario)

        captured_stderr.seek(0)
        console_output = captured_stderr.read()
        captured_stderr.close()
        self.assertIn("tool=get_startup_context xid=8A666C1FD121", console_output)
        for expanded in results["knowledge_context"]["entries"]:
            self.assertIn(
                f"tool=build_knowledge_context xid={expanded['entry']['xid']}",
                console_output,
            )


if __name__ == "__main__":
    unittest.main()

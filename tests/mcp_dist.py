from __future__ import annotations

import base64
import hashlib
import io
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from xrefkit.mcp.bootstrap import (
    BootstrapError,
    materialize_package_zip,
    parse_jsonrpc_response,
    verify_sha256,
)
from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.mcp.dist import BOOTSTRAP_FILENAME, ArtifactDistribution
from xrefkit.mcp.server import (
    _pip_package_http_response,
    _with_artifact_distribution,
    _with_http_distribution,
)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class DistRepoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        write(
            self.repo / "xrefkit" / "__init__.py",
            '__version__ = "1.2.3"\n',
        )
        write(
            self.repo / "xrefkit" / "cli.py",
            "def main() -> int:\n    return 0\n",
        )
        write(
            self.repo / "tools" / "sample_tool.py",
            "def main() -> int:\n    return 0\n",
        )
        self.catalog = XRefCatalog.build(self.repo)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()


class DeterministicPackageTests(DistRepoTestCase):
    def test_rebuilt_pip_packages_have_identical_bytes(self) -> None:
        first = self.catalog.get_xrefkit_runtime_pip_package()
        second = self.catalog.get_xrefkit_runtime_pip_package()

        self.assertEqual(first["content_hash"], second["content_hash"])
        self.assertEqual(first["content_base64"], second["content_base64"])

        first_tools = self.catalog.get_client_tool_pip_package()
        second_tools = self.catalog.get_client_tool_pip_package()
        self.assertEqual(first_tools["content_hash"], second_tools["content_hash"])


class ArtifactDistributionTests(DistRepoTestCase):
    def test_artifacts_include_packages_and_bootstrap(self) -> None:
        dist = ArtifactDistribution(self.catalog)
        filenames = [artifact.filename for artifact in dist.artifacts()]

        self.assertIn("xrefkit-1.2.3.zip", filenames)
        self.assertIn("xrefkit-client-tools-0.1.0.zip", filenames)
        self.assertIn(BOOTSTRAP_FILENAME, filenames)

    def test_artifact_bytes_match_declared_sha256(self) -> None:
        dist = ArtifactDistribution(self.catalog)
        for artifact in dist.artifacts():
            self.assertEqual(
                hashlib.sha256(artifact.content).hexdigest(),
                artifact.sha256,
                artifact.filename,
            )
            self.assertEqual(len(artifact.content), artifact.size_bytes)

    def test_artifact_hash_matches_mcp_pip_package_hash(self) -> None:
        dist = ArtifactDistribution(self.catalog)
        package = self.catalog.get_xrefkit_runtime_pip_package()
        artifact = dist.get(package["filename"])

        self.assertIsNotNone(artifact)
        self.assertEqual(artifact.sha256, package["content_hash"])
        self.assertEqual(
            artifact.content,
            base64.b64decode(package["content_base64"]),
        )

    def test_unknown_artifact_returns_none(self) -> None:
        dist = ArtifactDistribution(self.catalog)
        self.assertIsNone(dist.get("../etc/passwd"))
        self.assertIsNone(dist.get("missing.zip"))

    def test_index_manifest_lists_urls_and_hashes(self) -> None:
        dist = ArtifactDistribution(self.catalog)
        manifest = dist.index_manifest("https://example.test:8443")

        self.assertEqual(manifest["hash_algorithm"], "sha256")
        self.assertEqual(
            manifest["bootstrap_url"],
            "https://example.test:8443/dist/bootstrap.py",
        )
        for entry in manifest["artifacts"]:
            self.assertTrue(
                entry["url"].startswith("https://example.test:8443/dist/"),
                entry["url"],
            )
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")

    def test_index_html_is_pip_find_links_compatible(self) -> None:
        dist = ArtifactDistribution(self.catalog)
        html = dist.index_html()

        self.assertIn('href="xrefkit-1.2.3.zip#sha256=', html)
        self.assertIn('href="bootstrap.py#sha256=', html)

    def test_extra_dir_files_are_mirrored(self) -> None:
        extra_dir = self.repo / "extra"
        extra_dir.mkdir()
        (extra_dir / "PyYAML-6.0.2-py3-none-any.whl").write_bytes(b"fake-wheel")

        dist = ArtifactDistribution(self.catalog, extra_dir)
        wheel = dist.get("PyYAML-6.0.2-py3-none-any.whl")

        self.assertIsNotNone(wheel)
        self.assertEqual(wheel.kind, "wheel")
        self.assertEqual(wheel.sha256, hashlib.sha256(b"fake-wheel").hexdigest())

    def test_describe_for_mcp_prescribes_out_of_band_fetch(self) -> None:
        dist = ArtifactDistribution(self.catalog)
        block = dist.describe_for_mcp("http://127.0.0.1:8000")

        self.assertEqual(block["transport"], "plain_http")
        self.assertEqual(
            block["index_json_url"], "http://127.0.0.1:8000/dist/index.json"
        )
        self.assertIn("bootstrap.py", block["bootstrap_run"])
        self.assertTrue(
            any("out-of-band" in instruction for instruction in block["instructions"])
        )
        for entry in block["artifacts"]:
            self.assertNotIn("content", entry)
            self.assertNotIn("content_base64", entry)


class ServerAugmentationTests(DistRepoTestCase):
    def test_pip_package_http_response_replaces_base64_with_url(self) -> None:
        package = self.catalog.get_xrefkit_runtime_pip_package()
        response = _pip_package_http_response(package, "https://example.test:8443")

        self.assertIsNone(response["content_base64"])
        self.assertTrue(response["content_omitted"])
        self.assertEqual(
            response["download_url"],
            f"https://example.test:8443/dist/{package['filename']}",
        )
        self.assertEqual(response["content_hash"], package["content_hash"])

    def test_http_distribution_passthrough_without_dist(self) -> None:
        result = {"package_id": "x"}
        self.assertEqual(_with_http_distribution(result, None, ""), result)

    def test_http_distribution_pointer_added_when_active(self) -> None:
        dist = ArtifactDistribution(self.catalog)
        result = _with_http_distribution({"package_id": "x"}, dist, "http://h:1")

        self.assertTrue(result["http_distribution"]["preferred"])
        self.assertEqual(
            result["http_distribution"]["index_json_url"],
            "http://h:1/dist/index.json",
        )

    def test_startup_context_gains_artifact_distribution(self) -> None:
        dist = ArtifactDistribution(self.catalog)
        startup = {
            "client_instructions": ["existing"],
            "core_runtime_distribution": {"materialization": {"source": "xrefkit.mcp"}},
        }
        result = _with_artifact_distribution(startup, dist, "http://h:1")

        self.assertIn("artifact_distribution", result)
        self.assertEqual(result["client_instructions"][0], "existing")
        self.assertTrue(
            any(
                "artifact_distribution" in instruction
                for instruction in result["client_instructions"]
            )
        )
        materialization = result["core_runtime_distribution"]["materialization"]
        self.assertTrue(materialization["http_download"]["preferred"])
        self.assertEqual(materialization["source"], "xrefkit.mcp")


class BootstrapTests(unittest.TestCase):
    def _package_zip(self, members: dict[str, str]) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, content in members.items():
                archive.writestr(name, content)
        return buffer.getvalue()

    def test_materialize_strips_package_root_and_metadata(self) -> None:
        content = self._package_zip(
            {
                "pkg-1.0/pyproject.toml": "[project]\n",
                "pkg-1.0/README.md": "readme\n",
                "pkg-1.0/xrefkit/__init__.py": "__version__ = '1.0'\n",
                "pkg-1.0/xrefkit/sub/mod.py": "x = 1\n",
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            written = materialize_package_zip(content, target)

            self.assertEqual(sorted(written), ["xrefkit/__init__.py", "xrefkit/sub/mod.py"])
            self.assertTrue((target / "xrefkit" / "sub" / "mod.py").is_file())
            self.assertFalse((target / "pyproject.toml").exists())
            self.assertFalse((target / "README.md").exists())

    def test_materialize_skips_traversal_members(self) -> None:
        content = self._package_zip(
            {
                "pkg-1.0/xrefkit/ok.py": "x = 1\n",
                "pkg-1.0/../evil.py": "x = 1\n",
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            written = materialize_package_zip(content, target)

            self.assertEqual(written, ["xrefkit/ok.py"])
            self.assertFalse((target.parent / "evil.py").exists())

    def test_verify_sha256_rejects_mismatch(self) -> None:
        with self.assertRaisesRegex(BootstrapError, "sha256 mismatch"):
            verify_sha256(b"content", "0" * 64, "artifact.zip")

    def test_parse_jsonrpc_response_handles_sse_and_plain_json(self) -> None:
        sse = (
            b'event: message\n'
            b'data: {"jsonrpc": "2.0", "id": 1, "result": {"ok": true}}\n\n'
        )
        self.assertEqual(parse_jsonrpc_response(sse)["result"], {"ok": True})

        plain = b'{"jsonrpc": "2.0", "id": 2, "result": {"ok": false}}'
        self.assertEqual(parse_jsonrpc_response(plain)["result"], {"ok": False})

    def test_bootstrap_script_uses_only_stdlib_imports(self) -> None:
        source = (
            Path(__file__).parent.parent
            / "xrefkit"
            / "mcp"
            / "bootstrap.py"
        ).read_text(encoding="utf-8")
        allowed = {
            "__future__",
            "argparse",
            "hashlib",
            "io",
            "json",
            "pathlib",
            "ssl",
            "subprocess",
            "sys",
            "urllib",
            "urllib.request",
            "zipfile",
        }
        imported = {
            match.group(1)
            for match in re.finditer(
                r"^(?:from|import)\s+([A-Za-z0-9_.]+)", source, re.MULTILINE
            )
        }
        self.assertTrue(
            imported <= allowed,
            f"non-stdlib imports in bootstrap.py: {sorted(imported - allowed)}",
        )


if __name__ == "__main__":
    unittest.main()

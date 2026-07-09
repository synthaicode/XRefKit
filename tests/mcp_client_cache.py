from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from xrefkit.mcp.client_cache import (
    DocumentCacheProtocolError,
    XidDocumentCache,
)
from xrefkit.mcp.repository import stable_hash


REPOSITORY_FINGERPRINT = "a" * 32


def cacheable_document(
    content: str,
    *,
    xid: str = "ABC123",
    repository_fingerprint: str = REPOSITORY_FINGERPRINT,
) -> dict:
    version = stable_hash(content)
    return {
        "xid": xid,
        "title": "Cached document",
        "summary": "Cache test",
        "content": content,
        "links": [],
        "content_hash": version,
        "repository_fingerprint": repository_fingerprint,
        "cache_status": "miss",
        "content_omitted": False,
        "cache_policy": {"cache_recommended": True},
    }


class XidDocumentCacheTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache = XidDocumentCache(
            self.temp_dir.name,
            REPOSITORY_FINGERPRINT,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_stores_loads_and_lists_valid_versions(self) -> None:
        document = cacheable_document("current content")

        self.assertIs(self.cache.store(document), True)

        loaded = self.cache.load("ABC123")
        self.assertEqual(loaded["content"], "current content")
        self.assertEqual(
            self.cache.known_versions(),
            {"ABC123": document["content_hash"]},
        )

    def test_corrupt_cache_entry_is_evicted_and_treated_as_miss(self) -> None:
        cache_path = Path(
            self.temp_dir.name,
            REPOSITORY_FINGERPRINT,
            "ABC123.json",
        )
        cache_path.parent.mkdir(parents=True)
        cache_path.write_text("{not-json", encoding="utf-8")

        self.assertIsNone(self.cache.load("ABC123"))
        self.assertFalse(cache_path.exists())

    def test_rejects_document_whose_content_does_not_match_version(self) -> None:
        document = cacheable_document("current content")
        document["content"] = "tampered"

        with self.assertRaises(DocumentCacheProtocolError):
            self.cache.store(document)

    def test_bypasses_document_when_server_cost_gate_rejects_cache(self) -> None:
        document = cacheable_document("small")
        document["cache_policy"] = {"cache_recommended": False}

        self.assertIs(self.cache.store(document), False)
        self.assertIsNone(self.cache.load("ABC123"))

    def test_repository_namespaces_isolate_the_same_xid(self) -> None:
        other_fingerprint = "b" * 32
        other_cache = XidDocumentCache(
            self.temp_dir.name,
            other_fingerprint,
        )
        first = cacheable_document("first repository")
        second = cacheable_document(
            "second repository",
            repository_fingerprint=other_fingerprint,
        )

        self.cache.store(first)
        other_cache.store(second)

        self.assertEqual(self.cache.load("ABC123")["content"], "first repository")
        self.assertEqual(
            other_cache.load("ABC123")["content"],
            "second repository",
        )
        self.assertNotEqual(self.cache.cache_dir, other_cache.cache_dir)

    async def test_resolve_uses_cached_body_after_not_modified_response(self) -> None:
        document = cacheable_document("current content")
        self.cache.store(document)
        calls: list[tuple[str, str | None]] = []

        async def fetch(xid: str, known_version: str | None) -> dict:
            calls.append((xid, known_version))
            return {
                "xid": xid,
                "title": "Current server title",
                "content_hash": document["content_hash"],
                "repository_fingerprint": REPOSITORY_FINGERPRINT,
                "cache_status": "not_modified",
                "content_omitted": True,
                "cache_policy": {"cache_recommended": True},
            }

        resolved = await self.cache.resolve("ABC123", fetch)

        self.assertEqual(resolved["content"], "current content")
        self.assertEqual(resolved["title"], "Current server title")
        self.assertNotIn("path", resolved)
        self.assertEqual(resolved["client_cache_status"], "hit")
        self.assertEqual(calls, [("ABC123", document["content_hash"])])

    async def test_resolve_replaces_stale_entry(self) -> None:
        old = cacheable_document("old content")
        current = cacheable_document("new content")
        self.cache.store(old)

        async def fetch(xid: str, known_version: str | None) -> dict:
            self.assertEqual(known_version, old["content_hash"])
            response = dict(current)
            response["cache_status"] = "modified"
            return response

        resolved = await self.cache.resolve("ABC123", fetch)

        self.assertEqual(resolved["content"], "new content")
        self.assertEqual(resolved["client_cache_status"], "refreshed")
        self.assertEqual(self.cache.load("ABC123")["content"], "new content")

    async def test_resolve_startup_sends_only_previous_startup_versions(self) -> None:
        startup_documents = [
            cacheable_document("startup one", xid="STARTUP1"),
            cacheable_document("startup two", xid="STARTUP2"),
        ]
        calls: list[dict[str, str]] = []

        async def fetch(known_versions: dict[str, str]) -> dict:
            calls.append(dict(known_versions))
            references: list[dict] = []
            for document in startup_documents:
                if known_versions.get(document["xid"]) == document["content_hash"]:
                    references.append(
                        {
                            "xid": document["xid"],
                            "content_hash": document["content_hash"],
                            "repository_fingerprint": REPOSITORY_FINGERPRINT,
                            "cache_status": "not_modified",
                            "content_omitted": True,
                        }
                    )
                else:
                    references.append(document)
            return {"references": references}

        first = await self.cache.resolve_startup(fetch)
        self.cache.store(cacheable_document("other", xid="OTHER"))
        second = await self.cache.resolve_startup(fetch)

        self.assertEqual(calls[0], {})
        self.assertEqual(
            calls[1],
            {
                document["xid"]: document["content_hash"]
                for document in startup_documents
            },
        )
        self.assertEqual(
            [reference["content"] for reference in second["references"]],
            ["startup one", "startup two"],
        )
        self.assertEqual(first["references"][0]["client_cache_status"], "refreshed")
        entries = self.cache.startup_decision_log_entries()
        self.assertEqual(entries[0]["known_version_xids"], [])
        self.assertEqual(entries[1]["known_version_xids"], ["STARTUP1", "STARTUP2"])

    async def test_resolve_startup_records_client_decision_xids(self) -> None:
        startup_documents = [
            cacheable_document("startup one", xid="STARTUP1"),
            cacheable_document("startup two", xid="STARTUP2"),
        ]

        async def fetch(known_versions: dict[str, str]) -> dict:
            return {
                "load_order": ["STARTUP1", "STARTUP2"],
                "startup_contract_pack": {
                    "source_xids": ["STARTUP1", "STARTUP2"],
                },
                "references": startup_documents,
            }

        await self.cache.resolve_startup(fetch)

        entries = self.cache.startup_decision_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["event"], "startup_xid_decision")
        self.assertEqual(
            entries[0]["repository_fingerprint"],
            REPOSITORY_FINGERPRINT,
        )
        self.assertEqual(entries[0]["load_order_xids"], ["STARTUP1", "STARTUP2"])
        self.assertEqual(
            entries[0]["startup_contract_pack_source_xids"],
            ["STARTUP1", "STARTUP2"],
        )
        self.assertEqual(entries[0]["reference_xids"], ["STARTUP1", "STARTUP2"])
        self.assertEqual(entries[0]["client_decision_xids"], ["STARTUP1", "STARTUP2"])

    async def test_resolve_refetches_when_server_omits_content_without_cache(self) -> None:
        document = cacheable_document("recovered content")
        calls: list[str | None] = []

        async def fetch(xid: str, known_version: str | None) -> dict:
            calls.append(known_version)
            if len(calls) == 1:
                return {
                    "xid": xid,
                    "content_hash": document["content_hash"],
                    "repository_fingerprint": REPOSITORY_FINGERPRINT,
                    "cache_status": "not_modified",
                    "content_omitted": True,
                    "cache_policy": {"cache_recommended": True},
                }
            return document

        resolved = await self.cache.resolve("ABC123", fetch)

        self.assertEqual(resolved["content"], "recovered content")
        self.assertEqual(calls, [None, None])

    def test_cache_file_contains_explicit_schema_and_content_hash(self) -> None:
        document = cacheable_document("current content")
        self.cache.store(document)

        payload = json.loads(
            Path(
                self.temp_dir.name,
                REPOSITORY_FINGERPRINT,
                "ABC123.json",
            ).read_text(encoding="utf-8")
        )

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(
            payload["repository_fingerprint"],
            REPOSITORY_FINGERPRINT,
        )
        self.assertEqual(payload["content_hash"], document["content_hash"])
        self.assertNotIn("version", payload)


if __name__ == "__main__":
    unittest.main()

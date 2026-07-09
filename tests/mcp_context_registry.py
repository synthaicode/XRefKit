from __future__ import annotations

import unittest

from xrefkit.mcp.context_registry import (
    REUSE_SAME_VERSION_REASON,
    PromptContextAssembler,
    SessionXidContextRegistry,
)
from xrefkit.mcp.repository import stable_hash


REPOSITORY_FINGERPRINT = "a" * 32
OTHER_REPOSITORY_FINGERPRINT = "b" * 32


def document(
    content: str,
    *,
    xid: str = "ABC123",
    repository_fingerprint: str = REPOSITORY_FINGERPRINT,
) -> dict:
    return {
        "repository_fingerprint": repository_fingerprint,
        "xid": xid,
        "title": f"Document {xid}",
        "summary": "Test document",
        "layer": "base_control",
        "required_at_init": True,
        "content_hash": stable_hash(content),
        "content": content,
        "links": [],
        "cache_status": "miss",
        "client_cache_status": "refreshed",
    }


class SessionXidContextRegistryTests(unittest.TestCase):
    def test_same_document_twice_injects_once_then_reuses_reference(self) -> None:
        doc = document("current body")
        assembler = PromptContextAssembler()

        result = assembler.assemble(
            [doc, doc],
            turn_id="turn-1",
            active_task="verify ABC123 exact wording",
        )

        self.assertEqual([item["mode"] for item in result["prompt_items"]], ["body", "reuse_existing_session_context"])
        self.assertEqual(result["prompt_items"][0]["content"], "current body")
        self.assertNotIn("content", result["prompt_items"][1])
        self.assertEqual(
            result["prompt_items"][1]["reason"],
            REUSE_SAME_VERSION_REASON,
        )
        self.assertEqual(len(result["trace"]["injected_xids"]), 1)
        self.assertEqual(len(result["trace"]["reused_xids"]), 1)

    def test_same_xid_different_content_hash_is_version_change(self) -> None:
        old = document("old body")
        new = document("new body")
        assembler = PromptContextAssembler()

        assembler.assemble(
            [old],
            turn_id="turn-1",
            active_task="verify ABC123 exact wording",
        )
        result = assembler.assemble(
            [new],
            turn_id="turn-2",
            active_task="verify ABC123 exact wording",
        )

        self.assertEqual(result["prompt_items"][0]["mode"], "body")
        self.assertEqual(result["trace"]["version_changes"][0]["old_content_hash"], old["content_hash"])
        self.assertEqual(result["trace"]["version_changes"][0]["new_content_hash"], new["content_hash"])
        self.assertEqual(result["trace"]["version_changes"][0]["action"], "replaced")

    def test_same_xid_different_repository_fingerprint_is_not_deduped(self) -> None:
        first = document("same body")
        second = document(
            "same body",
            repository_fingerprint=OTHER_REPOSITORY_FINGERPRINT,
        )
        assembler = PromptContextAssembler()

        result = assembler.assemble(
            [first, second],
            turn_id="turn-1",
            active_task="verify ABC123 exact wording",
        )

        self.assertEqual([item["mode"] for item in result["prompt_items"]], ["body", "body"])
        self.assertEqual(result["trace"]["version_changes"], [])
        self.assertEqual(len(result["trace"]["injected_xids"]), 2)

    def test_context_compaction_allows_reinjection(self) -> None:
        doc = document("current body")
        registry = SessionXidContextRegistry()
        assembler = PromptContextAssembler(registry)

        assembler.assemble(
            [doc],
            turn_id="turn-1",
            active_task="verify ABC123 exact wording",
        )
        registry.mark_context_compacted()
        result = assembler.assemble(
            [doc],
            turn_id="turn-2",
            active_task="verify ABC123 exact wording",
        )

        self.assertEqual(result["prompt_items"][0]["mode"], "body")
        self.assertEqual(result["trace"]["reused_xids"], [])

    def test_materialized_document_defaults_to_metadata_only(self) -> None:
        doc = document("future body")
        assembler = PromptContextAssembler()

        result = assembler.assemble(
            [doc],
            turn_id="turn-1",
            active_task="route a task using summaries",
        )

        self.assertEqual(result["prompt_items"][0]["mode"], "metadata_only")
        self.assertNotIn("content", result["prompt_items"][0])
        self.assertEqual(result["prompt_items"][0]["xid"], "ABC123")
        self.assertEqual(result["trace"]["injected_xids"], [])

    def test_repeated_linked_xid_body_appears_at_most_once(self) -> None:
        startup_reference = document("shared linked body", xid="LINKED1")
        linked_reference = dict(startup_reference)
        linked_reference["cache_status"] = "not_modified"
        assembler = PromptContextAssembler()

        result = assembler.assemble(
            [startup_reference, linked_reference],
            turn_id="turn-1",
            active_task="verify LINKED1 exact wording",
        )

        body_items = [item for item in result["prompt_items"] if item["mode"] == "body"]
        reuse_items = [
            item
            for item in result["prompt_items"]
            if item["mode"] == "reuse_existing_session_context"
        ]
        self.assertEqual(len(body_items), 1)
        self.assertEqual(len(reuse_items), 1)
        self.assertNotIn("content", reuse_items[0])


if __name__ == "__main__":
    unittest.main()

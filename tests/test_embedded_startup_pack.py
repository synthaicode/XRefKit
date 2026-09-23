from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from xrefkit.mcp.catalog import XRefCatalog


class EmbeddedStartupPackTests(unittest.TestCase):
    def test_consumer_pack_matches_shipped_sources(self) -> None:
        # Exercise the packaged fallback, without repository governance files.
        with tempfile.TemporaryDirectory() as directory:
            catalog = XRefCatalog.build(Path(directory))
            for excluded in (None, ["prompt_flow", "workflow", "reporting"]):
                with self.subTest(excluded=excluded):
                    context = catalog.get_startup_context(excluded_protocols=excluded)
                    pack = context["startup_contract_pack"]
                    self.assertEqual(context["missing"], [])
                    self.assertEqual(len(context["references"]), 6)
                    self.assertEqual(pack["pack_source"], "embedded_fallback")
                    self.assertFalse(pack["stale"], pack["stale_sources"])
                    self.assertEqual(pack["stale_sources"], [])
                    self.assertEqual(pack["based_on_hashes"], pack["source_hashes"])
                    self.assertTrue(pack["body"])
                    self.assertFalse(any("is STALE" in text for text in context["client_instructions"]))
                    if excluded:
                        for name in excluded:
                            self.assertIsNone(context[f"{name}_protocol"])

    def test_consumer_source_override_still_reports_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = XRefCatalog.build(root)
            xid = "5A1C8E4D2F90"
            original = catalog.get_document_by_xid(xid)["content"]
            source = root / "docs/core/models/017_base_and_xref_layering.md"
            source.parent.mkdir(parents=True)
            source.write_text(original + "\nConsumer-specific control change.\n", encoding="utf-8")

            pack = catalog.get_startup_context()["startup_contract_pack"]

            self.assertTrue(pack["stale"])
            self.assertEqual([item["xid"] for item in pack["stale_sources"]], [xid])
            self.assertNotEqual(pack["based_on_hashes"][xid], pack["source_hashes"][xid])

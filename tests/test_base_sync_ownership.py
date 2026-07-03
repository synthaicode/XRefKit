import importlib.util
import tempfile
import unittest
from pathlib import Path

from fm.ownership import load_ownership


def _load_sync_module():
    module_path = Path(__file__).resolve().parents[1] / "handoff" / "base_sync" / "xrefkit_sync_worklist.py"
    spec = importlib.util.spec_from_file_location("xrefkit_sync_worklist", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaseSyncOwnershipTests(unittest.TestCase):
    def test_pack_move_classifies_as_moved_in_base(self) -> None:
        sync = _load_sync_module()
        local = sync.State()
        copy = sync.State()
        head = sync.State()
        digest = "same-content"
        local.docs["DOC123456789"] = {
            "path": "docs/packs/business-intake/entry.md",
            "hash": digest,
            "anchors": ["DOC123456789"],
        }
        copy.docs["DOC123456789"] = {
            "path": "docs/packs/business-intake/entry.md",
            "hash": digest,
            "anchors": ["DOC123456789"],
        }
        head.docs["DOC123456789"] = {
            "path": "packs/business-intake/pack.md",
            "hash": digest,
            "anchors": ["DOC123456789"],
        }

        items = sync.classify_docs(local, copy, head)

        self.assertEqual("moved_in_base", items[0]["kind"])
        self.assertEqual("packs/business-intake/pack.md", items[0]["head_path"])

    def test_scan_local_excludes_local_pack_zone(self) -> None:
        sync = _load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ownership.yaml").write_text(
                "zones:\n"
                "  - id: local-packs\n"
                "    owner: local\n"
                "    paths:\n"
                "      - packs/local/\n"
                "    catalog: true\n"
                "    distribution: false\n"
                "    base_sync: false\n"
                "    shadowing: true\n"
                "  - id: shared-packs\n"
                "    owner: pack\n"
                "    paths:\n"
                "      - packs/*/\n"
                "    catalog: true\n"
                "    distribution: true\n"
                "    base_sync: true\n"
                "    shadowing: true\n",
                encoding="utf-8",
            )
            local_doc = root / "packs" / "local" / "acme" / "knowledge" / "fact.md"
            local_doc.parent.mkdir(parents=True)
            local_doc.write_text(
                "<!-- xid: LOCAL123456 -->\n<a id=\"xid-LOCAL123456\"></a>\n\n# Local\n",
                encoding="utf-8",
            )
            shared_doc = root / "packs" / "shared" / "knowledge" / "fact.md"
            shared_doc.parent.mkdir(parents=True)
            shared_doc.write_text(
                "<!-- xid: SHARED123456 -->\n<a id=\"xid-SHARED123456\"></a>\n\n# Shared\n",
                encoding="utf-8",
            )

            ownership = load_ownership(root)
            state, problems = sync.scan_local(root, ownership)

            self.assertEqual([], problems)
            self.assertNotIn("LOCAL123456", state.docs)
            self.assertIn("SHARED123456", state.docs)

    def test_state_from_files_excludes_non_base_sync_zone(self) -> None:
        sync = _load_sync_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ownership.yaml").write_text(
                "zones:\n"
                "  - id: derived\n"
                "    owner: generated\n"
                "    paths:\n"
                "      - site/\n"
                "    catalog: false\n"
                "    distribution: false\n"
                "    base_sync: false\n"
                "    shadowing: false\n",
                encoding="utf-8",
            )
            ownership = load_ownership(root)
            blobs = {
                "a": {"kind": "plain", "hash": "plain-a"},
                "b": {"kind": "plain", "hash": "plain-b"},
            }
            files = {
                "site/index.json": "a",
                "handoff/base_sync/HANDOFF.md": "b",
            }

            state = sync.state_from_files(files, blobs, ownership)

            self.assertNotIn("site/index.json", state.plain)
            self.assertEqual("plain-b", state.plain["handoff/base_sync/HANDOFF.md"])


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from xrefkit.ctx import ctx_pack
from xrefkit.xref import XrefConfig


class CtxPackTests(unittest.TestCase):
    def test_ctx_pack_follows_references_from_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)

            (docs / "seed.md").write_text(
                "<!-- xid: 5EED12345678 -->\n"
                '<a id="xid-5EED12345678"></a>\n\n'
                "# Seed\n\n"
                "[Child](child.md#xid-C11D12345678)\n",
                encoding="utf-8",
            )
            (docs / "child.md").write_text(
                "<!-- xid: C11D12345678 -->\n<a id=\"xid-C11D12345678\"></a>\n\n# Child\n",
                encoding="utf-8",
            )

            result = ctx_pack(
                XrefConfig(root=str(root)),
                seeds=["5EED12345678"],
                depth=1,
                max_bytes=4000,
                per_doc_bytes=1000,
            )

            packed_xids = [doc["xid"] for doc in result["docs"]]
            self.assertEqual(["5EED12345678", "C11D12345678"], packed_xids)
            self.assertIn("## Seed", result["text"])
            self.assertIn("## Child", result["text"])

    def test_ctx_pack_respects_max_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)

            (docs / "seed.md").write_text(
                "<!-- xid: SEED12345678 -->\n"
                '<a id="xid-SEED12345678"></a>\n\n'
                "# Seed\n\n"
                + ("A" * 500),
                encoding="utf-8",
            )

            result = ctx_pack(
                XrefConfig(root=str(root)),
                seeds=["SEED12345678"],
                depth=0,
                max_bytes=120,
                per_doc_bytes=1000,
            )

            self.assertEqual([], result["docs"])
            self.assertLessEqual(len(result["text"].encode("utf-8")), 120)


if __name__ == "__main__":
    unittest.main()

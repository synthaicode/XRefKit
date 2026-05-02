import tempfile
import unittest
from pathlib import Path

from fm.xref import XrefConfig, xref_check, xref_deprecate, xref_init, xref_rewrite


class XrefTests(unittest.TestCase):
    @staticmethod
    def _normalized_paths(paths: list[str]) -> list[str]:
        return [path.replace("\\", "/") for path in paths]

    def test_xref_init_adds_block_to_missing_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "docs" / "guide.md"
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text("# Guide\n", encoding="utf-8")

            result = xref_init(XrefConfig(root=str(root)), dry_run=False)

            self.assertEqual(["docs/guide.md"], self._normalized_paths(result["changed_files"]))
            text = doc.read_text(encoding="utf-8")
            self.assertIn("<!-- xid:", text)
            self.assertIn('<a id="xid-', text)

    def test_xref_rewrite_updates_paths_from_xid_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)

            target = docs / "target.md"
            target.write_text(
                "<!-- xid: ABCDEF123456 -->\n"
                '<a id="xid-ABCDEF123456"></a>\n\n'
                "# Target\n",
                encoding="utf-8",
            )
            source = docs / "nested" / "source.md"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text(
                "<!-- xid: 654321FEDCBA -->\n"
                '<a id="xid-654321FEDCBA"></a>\n\n'
                "# Source\n\n"
                "[Go](placeholder.md#xid-ABCDEF123456)\n",
                encoding="utf-8",
            )

            result = xref_rewrite(XrefConfig(root=str(root)), dry_run=False)

            self.assertEqual(["docs/nested/source.md"], self._normalized_paths(result["changed_files"]))
            rewritten = source.read_text(encoding="utf-8")
            self.assertIn("[Go](../target.md#xid-ABCDEF123456)", rewritten)

    def test_xref_check_reports_duplicates_and_broken_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)

            duplicate_a = docs / "a.md"
            duplicate_b = docs / "b.md"
            broken = docs / "broken.md"
            duplicate_a.write_text(
                "<!-- xid: DUPL11111111 -->\n<a id=\"xid-DUPL11111111\"></a>\n\n# A\n",
                encoding="utf-8",
            )
            duplicate_b.write_text(
                "<!-- xid: DUPL11111111 -->\n<a id=\"xid-DUPL11111111\"></a>\n\n# B\n",
                encoding="utf-8",
            )
            broken.write_text(
                "<!-- xid: GOOD22222222 -->\n"
                '<a id="xid-GOOD22222222"></a>\n\n'
                "# Broken\n\n"
                "[Missing](missing.md#xid-NOTFOUND1234)\n",
                encoding="utf-8",
            )

            result = xref_check(XrefConfig(root=str(root)))

            issue_types = {issue["type"] for issue in result["issues"]}
            self.assertIn("duplicate_xid", issue_types)
            self.assertIn("broken_xref", issue_types)

    def test_xref_init_inserts_block_after_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "docs" / "frontmatter.md"
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text("---\nlayout: doc\n---\n# Title\n", encoding="utf-8")

            xref_init(XrefConfig(root=str(root)), dry_run=False)

            text = doc.read_text(encoding="utf-8")
            self.assertIn("---\nlayout: doc\n---\n<!-- xid:", text)

    def test_xref_rewrite_converts_wiki_links_to_markdown_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)

            (docs / "target.md").write_text(
                "<!-- xid: TARGET123456 -->\n<a id=\"xid-TARGET123456\"></a>\n\n# Target Title\n",
                encoding="utf-8",
            )
            source = docs / "source.md"
            source.write_text(
                "<!-- xid: SOURCE123456 -->\n<a id=\"xid-SOURCE123456\"></a>\n\n# Source\n\n[[TARGET123456]]\n",
                encoding="utf-8",
            )

            xref_rewrite(XrefConfig(root=str(root)), dry_run=False)

            rewritten = source.read_text(encoding="utf-8")
            self.assertIn("[Target Title](target.md#xid-TARGET123456)", rewritten)

    def test_xref_deprecate_records_bidirectional_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)

            old_doc = docs / "old.md"
            new_doc = docs / "new.md"
            old_doc.write_text(
                "<!-- xid: OLD123456789 -->\n<a id=\"xid-OLD123456789\"></a>\n\n# Old\n",
                encoding="utf-8",
            )
            new_doc.write_text(
                "<!-- xid: NEW123456789 -->\n<a id=\"xid-NEW123456789\"></a>\n\n# New\n",
                encoding="utf-8",
            )

            result = xref_deprecate(
                XrefConfig(root=str(root)),
                old_xid="OLD123456789",
                new_xid="NEW123456789",
                note="replaced by new scope",
            )

            self.assertTrue(result["ok"])
            old_text = old_doc.read_text(encoding="utf-8")
            new_text = new_doc.read_text(encoding="utf-8")
            self.assertIn("## 互換性（XID関係）", old_text)
            self.assertIn("- superseded_by: [[NEW123456789]]", old_text)
            self.assertIn("- note: replaced by new scope", old_text)
            self.assertIn("- supersedes: [[OLD123456789]]", new_text)


if __name__ == "__main__":
    unittest.main()

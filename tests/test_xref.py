import tempfile
import unittest
from pathlib import Path

from xrefkit.xref import XrefConfig, xref_check, xref_deprecate, xref_init, xref_rewrite


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

    def test_xref_rewrite_updates_bare_refs_in_skill_meta_and_pack_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "docs" / "core" / "target.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "<!-- xid: ABCDEF123456 -->\n"
                '<a id="xid-ABCDEF123456"></a>\n\n'
                "# Target\n",
                encoding="utf-8",
            )
            meta = root / "skills" / "sample" / "meta.md"
            meta.parent.mkdir(parents=True, exist_ok=True)
            meta.write_text(
                "<!-- xid: 123456ABCDEF -->\n"
                '<a id="xid-123456ABCDEF"></a>\n\n'
                "# Meta\n\n"
                "- knowledge_refs:\n"
                "  - `../../docs/old.md#xid-ABCDEF123456`\n",
                encoding="utf-8",
            )
            manifest = root / "skills" / "packs" / "sample" / "pack.md"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(
                "<!-- xid: FEDCBA654321 -->\n"
                '<a id="xid-FEDCBA654321"></a>\n\n'
                "# Pack\n\n"
                "- entry: `docs/old.md#xid-ABCDEF123456`\n",
                encoding="utf-8",
            )

            result = xref_rewrite(XrefConfig(root=str(root)), dry_run=False)

            self.assertEqual(
                [
                    "skills/packs/sample/pack.md",
                    "skills/sample/meta.md",
                ],
                sorted(self._normalized_paths(result["changed_files"])),
            )
            self.assertIn(
                "`../../docs/core/target.md#xid-ABCDEF123456`",
                meta.read_text(encoding="utf-8"),
            )
            self.assertIn(
                "`docs/core/target.md#xid-ABCDEF123456`",
                manifest.read_text(encoding="utf-8"),
            )

    def test_xref_check_reports_stale_bare_ref_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "docs" / "core" / "target.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "<!-- xid: ABCDEF123456 -->\n"
                '<a id="xid-ABCDEF123456"></a>\n\n'
                "# Target\n",
                encoding="utf-8",
            )
            meta = root / "skills" / "sample" / "meta.md"
            meta.parent.mkdir(parents=True, exist_ok=True)
            meta.write_text(
                "<!-- xid: 123456ABCDEF -->\n"
                '<a id="xid-123456ABCDEF"></a>\n\n'
                "# Meta\n\n"
                "- knowledge_refs:\n"
                "  - `../../docs/old.md#xid-ABCDEF123456`\n",
                encoding="utf-8",
            )

            result = xref_check(XrefConfig(root=str(root)))

            stale = [
                issue
                for issue in result["issues"]
                if issue["type"] == "stale_xref_path"
            ]
            self.assertEqual(1, len(stale))
            self.assertEqual("../../docs/old.md", stale[0]["path"])
            self.assertEqual("../../docs/core/target.md", stale[0]["expected"])

    def test_xref_rewrite_leaves_bare_refs_in_fenced_examples_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "docs" / "core" / "target.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "<!-- xid: ABCDEF123456 -->\n"
                '<a id="xid-ABCDEF123456"></a>\n\n'
                "# Target\n",
                encoding="utf-8",
            )
            source = root / "docs" / "guide.md"
            source.write_text(
                "<!-- xid: 111111AAAAAA -->\n"
                '<a id="xid-111111AAAAAA"></a>\n\n'
                "# Guide\n\n"
                "```md\n"
                "- `../old.md#xid-ABCDEF123456`\n"
                "```\n",
                encoding="utf-8",
            )

            result = xref_rewrite(XrefConfig(root=str(root)), dry_run=False)

            self.assertEqual([], result["changed_files"])
            self.assertIn(
                "`../old.md#xid-ABCDEF123456`",
                source.read_text(encoding="utf-8"),
            )

    def test_xref_check_reports_duplicates_and_broken_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)

            duplicate_a = docs / "a.md"
            duplicate_b = docs / "b.md"
            broken = docs / "broken.md"
            duplicate_a.write_text(
                "<!-- xid: AAAA11111111 -->\n<a id=\"xid-AAAA11111111\"></a>\n\n# A\n",
                encoding="utf-8",
            )
            duplicate_b.write_text(
                "<!-- xid: AAAA11111111 -->\n<a id=\"xid-AAAA11111111\"></a>\n\n# B\n",
                encoding="utf-8",
            )
            broken.write_text(
                "<!-- xid: BBBB22222222 -->\n"
                '<a id="xid-BBBB22222222"></a>\n\n'
                "# Broken\n\n"
                "[Missing](missing.md#xid-FFFFFFFFFFFF)\n",
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
                "<!-- xid: ABCDEF123456 -->\n<a id=\"xid-ABCDEF123456\"></a>\n\n# Target Title\n",
                encoding="utf-8",
            )
            source = docs / "source.md"
            source.write_text(
                "<!-- xid: 654321FEDCBA -->\n<a id=\"xid-654321FEDCBA\"></a>\n\n# Source\n\n[[ABCDEF123456]]\n",
                encoding="utf-8",
            )

            xref_rewrite(XrefConfig(root=str(root)), dry_run=False)

            rewritten = source.read_text(encoding="utf-8")
            self.assertIn("[Target Title](target.md#xid-ABCDEF123456)", rewritten)

    def test_xref_deprecate_records_bidirectional_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)

            old_doc = docs / "old.md"
            new_doc = docs / "new.md"
            old_doc.write_text(
                "<!-- xid: AAAAAA111111 -->\n<a id=\"xid-AAAAAA111111\"></a>\n\n# Old\n",
                encoding="utf-8",
            )
            new_doc.write_text(
                "<!-- xid: BBBBBB222222 -->\n<a id=\"xid-BBBBBB222222\"></a>\n\n# New\n",
                encoding="utf-8",
            )

            result = xref_deprecate(
                XrefConfig(root=str(root)),
                old_xid="AAAAAA111111",
                new_xid="BBBBBB222222",
                note="replaced by new scope",
            )

            self.assertTrue(result["ok"])
            old_text = old_doc.read_text(encoding="utf-8")
            new_text = new_doc.read_text(encoding="utf-8")
            self.assertIn("## 互換性（XID関係）", old_text)
            self.assertIn("- superseded_by: [[BBBBBB222222]]", old_text)
            self.assertIn("- note: replaced by new scope", old_text)
            self.assertIn("- supersedes: [[AAAAAA111111]]", new_text)

    def test_xref_check_accepts_source_file_xid_comment_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "sample"
            ref_dir = skill_dir / "references"
            ref_dir.mkdir(parents=True, exist_ok=True)
            (ref_dir / "template.yaml").write_text(
                "# xid: CCCCCC333333\n\n"
                "flow_id: sample\n",
                encoding="utf-8",
            )
            (skill_dir / "SKILL.md").write_text(
                "<!-- xid: DDDDDD444444 -->\n"
                '<a id="xid-DDDDDD444444"></a>\n\n'
                "# Skill\n\n"
                "- [Template](./references/template.yaml#xid-CCCCCC333333)\n",
                encoding="utf-8",
            )

            result = xref_check(XrefConfig(root=str(root), include=["skills"]))

            self.assertEqual([], result["issues"])
            self.assertEqual([], result["missing_xid"])


if __name__ == "__main__":
    unittest.main()

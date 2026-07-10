import tempfile
import unittest
from pathlib import Path

from tools.check_skill_knowledge_xids import check_skill_knowledge_xids


def _write_xid_doc(path: Path, xid: str, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"<!-- xid: {xid} -->\n"
        f'<a id="xid-{xid}"></a>\n\n'
        f"# {title}\n",
        encoding="utf-8",
    )


class SkillKnowledgeXidCheckTests(unittest.TestCase):
    def test_accepts_bound_slot_and_skill_body_knowledge_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_xid_doc(root / "knowledge" / "sample.md", "A1B2C3D4E5F6", "Knowledge")
            skill_dir = root / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            _write_xid_doc(skill_dir / "SKILL.md", "ABCDEF123456", "Skill")
            (skill_dir / "SKILL.md").write_text(
                (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                + "\n## Required Knowledge (XID)\n"
                "- [Knowledge](../../knowledge/sample.md#xid-A1B2C3D4E5F6)\n",
                encoding="utf-8",
            )
            (skill_dir / "meta.md").write_text(
                "<!-- xid: 123456ABCDEF -->\n"
                '<a id="xid-123456ABCDEF"></a>\n\n'
                "# Skill Meta: sample\n\n"
                "- skill_id: `sample`\n"
                "- skill_doc: `./SKILL.md`\n"
                "- knowledge_slots:\n"
                "  - name=sample; bind=A1B2C3D4E5F6\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(root=root, scope="public")

            self.assertTrue(result.ok, [finding.to_dict() for finding in result.errors])

    def test_rejects_missing_bound_xid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            _write_xid_doc(skill_dir / "SKILL.md", "ABCDEF123456", "Skill")
            (skill_dir / "meta.md").write_text(
                "<!-- xid: 123456ABCDEF -->\n"
                '<a id="xid-123456ABCDEF"></a>\n\n'
                "# Skill Meta: sample\n\n"
                "- skill_id: `sample`\n"
                "- skill_doc: `./SKILL.md`\n"
                "- knowledge_slots:\n"
                "  - name=sample; bind=FFFFFFFFFFFF\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(root=root, scope="public")

            self.assertFalse(result.ok)
            self.assertTrue(any("bind XID not found" in finding.message for finding in result.errors))

    def test_rejects_knowledge_link_without_xid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_xid_doc(root / "knowledge" / "sample.md", "A1B2C3D4E5F6", "Knowledge")
            skill_dir = root / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            _write_xid_doc(skill_dir / "SKILL.md", "ABCDEF123456", "Skill")
            (skill_dir / "SKILL.md").write_text(
                (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                + "\n- [Knowledge](../../knowledge/sample.md)\n",
                encoding="utf-8",
            )
            (skill_dir / "meta.md").write_text(
                "<!-- xid: 123456ABCDEF -->\n"
                '<a id="xid-123456ABCDEF"></a>\n\n'
                "# Skill Meta: sample\n\n"
                "- skill_id: `sample`\n"
                "- skill_doc: `./SKILL.md`\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(root=root, scope="public")

            self.assertFalse(result.ok)
            self.assertTrue(any("missing #xid" in finding.message for finding in result.errors))

    def test_rejects_stale_knowledge_link_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_xid_doc(root / "knowledge" / "actual.md", "A1B2C3D4E5F6", "Knowledge")
            skill_dir = root / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            _write_xid_doc(skill_dir / "SKILL.md", "ABCDEF123456", "Skill")
            (skill_dir / "SKILL.md").write_text(
                (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                + "\n- [Knowledge](../../knowledge/old.md#xid-A1B2C3D4E5F6)\n",
                encoding="utf-8",
            )
            (skill_dir / "meta.md").write_text(
                "<!-- xid: 123456ABCDEF -->\n"
                '<a id="xid-123456ABCDEF"></a>\n\n'
                "# Skill Meta: sample\n\n"
                "- skill_id: `sample`\n"
                "- skill_doc: `./SKILL.md`\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(root=root, scope="public")

            self.assertFalse(result.ok)
            self.assertTrue(any("path does not match XID" in finding.message for finding in result.errors))

    def test_target_limits_checked_skill_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_xid_doc(root / "knowledge" / "sample.md", "A1B2C3D4E5F6", "Knowledge")

            good_dir = root / "skills" / "good"
            good_dir.mkdir(parents=True)
            _write_xid_doc(good_dir / "SKILL.md", "111111AAAAAA", "Good")
            (good_dir / "SKILL.md").write_text(
                (good_dir / "SKILL.md").read_text(encoding="utf-8")
                + "\n- [Knowledge](../../knowledge/sample.md#xid-A1B2C3D4E5F6)\n",
                encoding="utf-8",
            )
            (good_dir / "meta.md").write_text(
                "<!-- xid: 222222BBBBBB -->\n"
                '<a id="xid-222222BBBBBB"></a>\n\n'
                "# Skill Meta: good\n\n"
                "- skill_id: `good`\n"
                "- skill_doc: `./SKILL.md`\n",
                encoding="utf-8",
            )

            bad_dir = root / "skills" / "bad"
            bad_dir.mkdir(parents=True)
            _write_xid_doc(bad_dir / "SKILL.md", "333333CCCCCC", "Bad")
            (bad_dir / "SKILL.md").write_text(
                (bad_dir / "SKILL.md").read_text(encoding="utf-8")
                + "\n- [Knowledge](../../knowledge/sample.md)\n",
                encoding="utf-8",
            )
            (bad_dir / "meta.md").write_text(
                "<!-- xid: 444444DDDDDD -->\n"
                '<a id="xid-444444DDDDDD"></a>\n\n'
                "# Skill Meta: bad\n\n"
                "- skill_id: `bad`\n"
                "- skill_doc: `./SKILL.md`\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(
                root=root,
                scope="public",
                targets=["skills/good"],
            )

            self.assertTrue(result.ok, [finding.to_dict() for finding in result.errors])
            self.assertEqual(1, result.checked_skills)

    def test_fix_missing_xids_assigns_xid_and_updates_knowledge_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            knowledge = root / "knowledge" / "sample.md"
            knowledge.parent.mkdir(parents=True, exist_ok=True)
            knowledge.write_text("# Knowledge\n", encoding="utf-8")

            skill_dir = root / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "# Skill\n\n"
                "- [Knowledge](../../knowledge/sample.md)\n",
                encoding="utf-8",
            )
            (skill_dir / "meta.md").write_text(
                "# Skill Meta: sample\n\n"
                "- skill_id: `sample`\n"
                "- skill_doc: `./SKILL.md`\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(
                root=root,
                scope="public",
                targets=["skills/sample"],
                fix_missing_xids=True,
            )

            self.assertTrue(result.ok, [finding.to_dict() for finding in result.errors])
            self.assertIn("knowledge/sample.md", result.changed_files)
            self.assertIn("skills/sample/SKILL.md", result.changed_files)
            self.assertIn("skills/sample/meta.md", result.changed_files)
            knowledge_text = knowledge.read_text(encoding="utf-8")
            skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("<!-- xid:", knowledge_text)
            self.assertRegex(skill_text, r"\.\./\.\./knowledge/sample\.md#xid-[A-F0-9]{12}")

    def test_fix_missing_xids_uses_existing_target_xid_for_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_xid_doc(root / "knowledge" / "sample.md", "A1B2C3D4E5F6", "Knowledge")

            skill_dir = root / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            _write_xid_doc(skill_dir / "SKILL.md", "ABCDEF123456", "Skill")
            (skill_dir / "SKILL.md").write_text(
                (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                + "\n- [Knowledge](../../knowledge/sample.md)\n",
                encoding="utf-8",
            )
            _write_xid_doc(skill_dir / "meta.md", "123456ABCDEF", "Meta")
            (skill_dir / "meta.md").write_text(
                (skill_dir / "meta.md").read_text(encoding="utf-8")
                + "\n- skill_id: `sample`\n"
                "- skill_doc: `./SKILL.md`\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(
                root=root,
                scope="public",
                targets=["skills/sample"],
                fix_missing_xids=True,
            )

            self.assertTrue(result.ok, [finding.to_dict() for finding in result.errors])
            self.assertIn("../../knowledge/sample.md#xid-A1B2C3D4E5F6", (skill_dir / "SKILL.md").read_text(encoding="utf-8"))

    def test_fix_missing_xids_adds_line_comment_to_referenced_python_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "tools" / "sample.py"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("#!/usr/bin/env python\nprint('ok')\n", encoding="utf-8")

            skill_dir = root / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            _write_xid_doc(skill_dir / "SKILL.md", "ABCDEF123456", "Skill")
            (skill_dir / "SKILL.md").write_text(
                (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                + "\n- [Tool](../../tools/sample.py)\n",
                encoding="utf-8",
            )
            _write_xid_doc(skill_dir / "meta.md", "123456ABCDEF", "Meta")
            (skill_dir / "meta.md").write_text(
                (skill_dir / "meta.md").read_text(encoding="utf-8")
                + "\n- skill_id: `sample`\n"
                "- skill_doc: `./SKILL.md`\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(
                root=root,
                scope="public",
                targets=["skills/sample"],
                fix_missing_xids=True,
            )

            self.assertTrue(result.ok, [finding.to_dict() for finding in result.errors])
            self.assertIn("tools/sample.py", result.changed_files)
            source_text = source.read_text(encoding="utf-8")
            self.assertRegex(source_text, r"^#![^\n]+\n# xid: [A-F0-9]{12}\n", source_text)
            self.assertRegex(
                (skill_dir / "SKILL.md").read_text(encoding="utf-8"),
                r"\.\./\.\./tools/sample\.py#xid-[A-F0-9]{12}",
            )

    def test_fix_missing_xids_adds_slash_comment_to_referenced_csharp_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src" / "Sample.cs"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("namespace Sample;\n", encoding="utf-8")

            skill_dir = root / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            _write_xid_doc(skill_dir / "SKILL.md", "ABCDEF123456", "Skill")
            (skill_dir / "SKILL.md").write_text(
                (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                + "\n- [Source](../../src/Sample.cs)\n",
                encoding="utf-8",
            )
            _write_xid_doc(skill_dir / "meta.md", "123456ABCDEF", "Meta")
            (skill_dir / "meta.md").write_text(
                (skill_dir / "meta.md").read_text(encoding="utf-8")
                + "\n- skill_id: `sample`\n"
                "- skill_doc: `./SKILL.md`\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(
                root=root,
                scope="public",
                targets=["skills/sample"],
                fix_missing_xids=True,
            )

            self.assertTrue(result.ok, [finding.to_dict() for finding in result.errors])
            self.assertRegex(source.read_text(encoding="utf-8"), r"^// xid: [A-F0-9]{12}\n")

    def test_rejects_invalid_own_xid_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            _write_xid_doc(skill_dir / "SKILL.md", "not-canonical", "Skill")
            _write_xid_doc(skill_dir / "meta.md", "123456ABCDEF", "Meta")
            (skill_dir / "meta.md").write_text(
                (skill_dir / "meta.md").read_text(encoding="utf-8")
                + "\n- skill_id: `sample`\n"
                "- skill_doc: `./SKILL.md`\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(
                root=root,
                scope="public",
                targets=["skills/sample"],
            )

            self.assertFalse(result.ok)
            self.assertTrue(any("own XID has invalid format" in finding.message for finding in result.errors))

    def test_fix_missing_xids_replaces_invalid_markdown_xid_and_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            knowledge = root / "knowledge" / "sample.md"
            knowledge.parent.mkdir(parents=True, exist_ok=True)
            knowledge.write_text(
                "<!-- xid: bad-xid -->\n"
                '<a id="xid-bad-xid"></a>\n\n'
                "# Knowledge\n",
                encoding="utf-8",
            )

            skill_dir = root / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            _write_xid_doc(skill_dir / "SKILL.md", "ABCDEF123456", "Skill")
            (skill_dir / "SKILL.md").write_text(
                (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                + "\n- [Knowledge](../../knowledge/sample.md#xid-bad-xid)\n",
                encoding="utf-8",
            )
            _write_xid_doc(skill_dir / "meta.md", "123456ABCDEF", "Meta")
            (skill_dir / "meta.md").write_text(
                (skill_dir / "meta.md").read_text(encoding="utf-8")
                + "\n- skill_id: `sample`\n"
                "- skill_doc: `./SKILL.md`\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(
                root=root,
                scope="public",
                targets=["skills/sample"],
                fix_missing_xids=True,
            )

            self.assertTrue(result.ok, [finding.to_dict() for finding in result.errors])
            self.assertRegex(knowledge.read_text(encoding="utf-8"), r"<!-- xid: [A-F0-9]{12} -->")
            self.assertNotIn("bad-xid", (skill_dir / "SKILL.md").read_text(encoding="utf-8"))

    def test_fix_missing_xids_replaces_invalid_source_xid_and_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "tools" / "sample.py"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("# xid: bad-xid\n\nprint('ok')\n", encoding="utf-8")

            skill_dir = root / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            _write_xid_doc(skill_dir / "SKILL.md", "ABCDEF123456", "Skill")
            (skill_dir / "SKILL.md").write_text(
                (skill_dir / "SKILL.md").read_text(encoding="utf-8")
                + "\n- [Tool](../../tools/sample.py#xid-bad-xid)\n",
                encoding="utf-8",
            )
            _write_xid_doc(skill_dir / "meta.md", "123456ABCDEF", "Meta")
            (skill_dir / "meta.md").write_text(
                (skill_dir / "meta.md").read_text(encoding="utf-8")
                + "\n- skill_id: `sample`\n"
                "- skill_doc: `./SKILL.md`\n",
                encoding="utf-8",
            )

            result = check_skill_knowledge_xids(
                root=root,
                scope="public",
                targets=["skills/sample"],
                fix_missing_xids=True,
            )

            self.assertTrue(result.ok, [finding.to_dict() for finding in result.errors])
            self.assertRegex(source.read_text(encoding="utf-8"), r"^# xid: [A-F0-9]{12}\n")
            self.assertNotIn("bad-xid", (skill_dir / "SKILL.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

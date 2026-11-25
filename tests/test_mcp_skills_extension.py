from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import yaml

from xrefkit.mcp.schemas import ClosureContract, SkillCatalogEntry
from xrefkit.mcp.skills_extension import SkillsExtension


def skill(**changes):
    values = dict(
        skill_id="sample_skill", title="Sample", summary="日本語の手順", maturity="trial",
        intent=[], target_artifacts=[], applies_when=[], not_for=[], required_knowledge=[],
        required_tools=[], inputs=[], outputs=[], closure_contract=ClosureContract([], [], "", "required"),
        meta_content="metadata", meta_links=[], skill_content="native procedure", skill_links=[],
        path="skills/sample/SKILL.md", meta_path="skills/sample/meta.md", context_size={},
    )
    values.update(changes)
    return SkillCatalogEntry(**values)


class SkillProjectionTests(unittest.TestCase):
    def extension(self, entries, root=Path(".")):
        return SkillsExtension(SimpleNamespace(skills=entries, repo_root=root))

    def test_manifest_frontmatter_and_exact_utf8_bytes(self):
        extension = self.extension([skill()])
        entry = extension.list_skills()["skills"][0]
        self.assertEqual(extension.get_skill(entry["uri"])["skill"], entry)
        text = extension.read_resource(entry["uri"])["contents"][0]["text"]
        frontmatter = yaml.safe_load(text.split("---", 2)[1])
        self.assertEqual(frontmatter, entry["frontmatter"])
        self.assertTrue(entry["uri"].endswith(f"/{frontmatter['name']}/SKILL.md"))
        self.assertRegex(frontmatter["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        self.assertLessEqual(len(frontmatter["name"]), 64)
        raw = text.encode("utf-8")
        self.assertEqual(entry["resources"], [{"uri": entry["uri"], "digest": "sha256:" + hashlib.sha256(raw).hexdigest(), "size": len(raw)}])
        self.assertNotIn("native procedure", text)
        self.assertIn("get_startup_context", text)
        self.assertIn("bind_skill_run", text)
        self.assertNotIn("allowed-tools", frontmatter)

    def test_normalized_names_remain_distinct(self):
        entries = self.extension([skill(skill_id="a_b"), skill(skill_id="a-b"), skill(skill_id="A.B"), skill(skill_id="!" * 300)]).list_skills()["skills"]
        self.assertEqual(len({e["uri"] for e in entries}), 4)
        for entry in entries:
            self.assertLessEqual(len(entry["frontmatter"]["name"]), 64)

    def test_excludes_private_hidden_unpublished_and_conflicted_entries(self):
        entries = [skill(skill_id="public"), skill(skill_id="duplicate"), skill(skill_id="duplicate"),
                   skill(skill_id="aliased"), skill(skill_id="owner", legacy_skill_ids=["aliased"]),
                   skill(skill_id="private", path="skills_private/example/SKILL.md"),
                   skill(skill_id="hidden", zone_metadata={"hidden": True}),
                   skill(skill_id="local", zone_metadata={"local_only": True}),
                   skill(skill_id="not-distributed", zone_metadata={"distribution": False}),
                   skill(skill_id="draft", maturity="draft")]
        actual = {e["frontmatter"]["metadata"]["xrefkit-skill-id"] for e in self.extension(entries).list_skills()["skills"]}
        self.assertEqual(actual, {"public", "owner"})

    def test_legacy_content_change_changes_manifest(self):
        entry = skill()
        first = self.extension([entry]).list_skills()["skills"][0]
        second = self.extension([replace(entry, skill_content="changed")]).list_skills()["skills"][0]
        self.assertEqual(first["uri"], second["uri"])
        self.assertNotEqual(first["resources"], second["resources"])

    def test_native_content_changes_and_source_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "SKILL.v1.md"
            source.write_bytes(b"native\r\n")
            entry = skill(path="SKILL.v1.md", definition_format="skill_definition_v1")
            extension = self.extension([entry], root)
            first = extension.list_skills()["skills"][0]
            source.write_bytes(b"changed\n")
            second = extension.get_skill(first["uri"])["skill"]
            self.assertNotEqual(first["resources"], second["resources"])
            self.assertEqual(second["frontmatter"]["metadata"]["xrefkit-source-sha256"], hashlib.sha256(b"changed\n").hexdigest())
            self.assertEqual(self.extension([replace(entry, path="../SKILL.v1.md")], root).list_skills()["skills"], [])
            self.assertEqual(self.extension([replace(entry, path=str(source))], root).list_skills()["skills"], [])
            source.unlink()
            self.assertEqual(extension.list_skills()["skills"], [])

    def test_symlink_source_is_not_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "actual.md").write_text("source", encoding="utf-8")
            try:
                (root / "SKILL.v1.md").symlink_to(root / "actual.md")
            except OSError:
                self.skipTest("symlink privilege unavailable")
            entry = skill(path="SKILL.v1.md", definition_format="skill_definition_v1")
            self.assertEqual(self.extension([entry], root).list_skills()["skills"], [])

    def test_package_native_uses_its_declared_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.v1.md").write_text("package source", encoding="utf-8")
            entry = skill(path="SKILL.v1.md", definition_format="skill_definition_v1", source_root=tmp, package_id="example.package")
            result = self.extension([entry], root / "other-repo").list_skills()["skills"][0]
            self.assertEqual(result["frontmatter"]["metadata"]["xrefkit-package-id"], "example.package")

    def test_empty_cursor_and_unknown_paths(self):
        extension = self.extension([])
        self.assertEqual(extension.list_skills(), {"resultType": "complete", "skills": []})
        for cursor in ["", "0", "next"]:
            with self.assertRaises(ValueError):
                extension.list_skills(cursor)
        for uri in ["skill://unknown/SKILL.md", "skill://xrefkit/../SKILL.md", "skill://xrefkit/%2e%2e/SKILL.md", "file:///secret", "skill://xrefkit/test/scripts/run.py"]:
            with self.assertRaises(ValueError):
                extension.get_skill(uri)
            with self.assertRaises(ValueError):
                extension.read_resource(uri)


if __name__ == "__main__":
    unittest.main()

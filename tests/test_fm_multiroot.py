import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from xrefkit.__main__ import main
from xrefkit.packmeta import _discover_manifests
from xrefkit.xref import XrefConfig


OWNERSHIP = """\
zones:
  - id: local-packs
    owner: local
    paths:
      - packs/local/
    catalog: true
    distribution: false
    base_sync: false
    shadowing: true
  - id: shared-packs
    owner: pack
    paths:
      - packs/*/
    catalog: true
    distribution: true
    base_sync: true
    shadowing: true
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class FmMultiRootTests(unittest.TestCase):
    def test_xref_default_include_contains_packs(self) -> None:
        self.assertIn("packs", XrefConfig().resolved_include())

    def test_skill_check_discovers_pack_skill_when_ownership_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "ownership.yaml", OWNERSHIP)
            _write(
                root / "packs" / "business" / "skills" / "pack_skill" / "meta.md",
                "# Skill Meta: Pack\n\n"
                "- skill_id: `pack_skill`\n"
                "- summary: pack skill\n"
                "- use_when: pack work\n"
                "- input: input\n"
                "- output: output\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `draft`\n",
            )
            _write(root / "packs" / "business" / "skills" / "pack_skill" / "SKILL.md", "# Pack Skill\n")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = main(["skill", "check", "--root", str(root), "--level", "draft", "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, rc)
            self.assertEqual(1, len(payload))
            self.assertTrue(payload[0]["ok"])
            self.assertTrue(payload[0]["meta_path"].replace("\\", "/").endswith("packs/business/skills/pack_skill/meta.md"))

    def test_pack_manifest_discovery_includes_top_level_packs_with_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "ownership.yaml", OWNERSHIP)
            _write(root / "packs" / "business" / "pack.md", "# Pack\n")

            manifests = [path.relative_to(root).as_posix() for path in _discover_manifests(root)]

            self.assertEqual(["packs/business/pack.md"], manifests)

    def test_skill_index_generation_includes_local_pack_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "ownership.yaml", OWNERSHIP)
            _write(
                root / "skills" / "_index.md",
                "# Skills Index\n\nHand-written routing.\n\n## Skills (compact)\n\nold\n",
            )
            _write(
                root / "packs" / "local" / "acme" / "skills" / "local_skill" / "meta.md",
                "# Skill Meta: Local\n\n"
                "- skill_id: `local_skill`\n"
                "- summary: local pack skill\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `draft`\n",
            )
            _write(
                root / "packs" / "local" / "acme" / "skills" / "local_skill" / "SKILL.md",
                "# Local Skill\n",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = main(["skill", "index", "--root", str(root)])

            output = stdout.getvalue()
            self.assertEqual(0, rc)
            self.assertIn("Hand-written routing.", output)
            self.assertIn("`local_skill`", output)
            self.assertIn("packs/local/acme/skills/local_skill/meta.md", output)
            self.assertIn("catalog-visible locally but not distributable", output)


if __name__ == "__main__":
    unittest.main()

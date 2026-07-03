import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fm.__main__ import main
from fm.packmeta import _discover_manifests
from fm.xref import XrefConfig


OWNERSHIP = """\
zones:
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

    def test_flow_doctor_discovers_pack_flow_and_pack_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "ownership.yaml", OWNERSHIP)
            _write(
                root / "packs" / "business" / "capabilities" / "cap.md",
                "# Capability\n\nCAP-BIZ-001\n",
            )
            _write(
                root / "packs" / "business" / "flows" / "pack_flow.yaml",
                "flow_id: FLOW-PACK\n"
                "name: pack_flow\n"
                "doc_xid: PACKFLOWDOC\n"
                "entry: start\n"
                "steps:\n"
                "  start:\n"
                "    capability: CAP-BIZ-001\n"
                "    on:\n"
                "      Go: COMPLETE\n"
                "      _invalid_or_absent: ABORT\n",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = main(["flow", "doctor", "--root", str(root), "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, rc)
            self.assertEqual(1, len(payload))
            self.assertTrue(payload[0]["ok"])
            self.assertTrue(payload[0]["flow_path"].replace("\\", "/").endswith("packs/business/flows/pack_flow.yaml"))

    def test_pack_manifest_discovery_includes_top_level_packs_with_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "ownership.yaml", OWNERSHIP)
            _write(root / "packs" / "business" / "pack.md", "# Pack\n")

            manifests = [path.relative_to(root).as_posix() for path in _discover_manifests(root)]

            self.assertEqual(["packs/business/pack.md"], manifests)


if __name__ == "__main__":
    unittest.main()

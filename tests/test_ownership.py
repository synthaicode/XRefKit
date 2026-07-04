import tempfile
import unittest
from pathlib import Path

from fm.ownership import OwnershipError, load_ownership, validate_ownership


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
  - id: records
    owner: operational
    paths:
      - work/
    catalog: false
    distribution: false
    base_sync: false
    shadowing: false
"""


class OwnershipTests(unittest.TestCase):
    def test_load_ownership_matches_first_zone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ownership.yaml").write_text(OWNERSHIP, encoding="utf-8")

            ownership = load_ownership(root)

            self.assertIsNotNone(ownership)
            assert ownership is not None
            self.assertEqual("local-packs", ownership.zone_for("packs/local/acme/skills/x.py").id)
            self.assertEqual("shared-packs", ownership.zone_for("packs/business-intake/skills/x.py").id)
            self.assertFalse(ownership.base_sync_enabled("packs/local/acme/knowledge/fact.md"))
            self.assertTrue(ownership.base_sync_enabled("packs/business-intake/knowledge/fact.md"))
            self.assertFalse(ownership.base_sync_enabled("work/sessions/log.md"))
            self.assertTrue(ownership.base_sync_enabled("unowned/file.txt"))

    def test_validate_rejects_escaping_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ownership.yaml").write_text(
                "zones:\n"
                "  - id: bad\n"
                "    owner: base\n"
                "    paths:\n"
                "      - ../outside/\n"
                "    catalog: false\n"
                "    distribution: false\n"
                "    base_sync: false\n"
                "    shadowing: false\n",
                encoding="utf-8",
            )

            ownership = load_ownership(root)

            self.assertIsNotNone(ownership)
            assert ownership is not None
            self.assertIn("bad: path escapes repository `../outside/`", validate_ownership(root, ownership))

    def test_missing_required_field_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ownership.yaml").write_text(
                "zones:\n"
                "  - id: bad\n"
                "    owner: base\n",
                encoding="utf-8",
            )

            with self.assertRaises(OwnershipError):
                load_ownership(root)


if __name__ == "__main__":
    unittest.main()

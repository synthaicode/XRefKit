from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from xrefkit.mcp.ownership import load_ownership, validate_ownership


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


class OwnershipTests(unittest.TestCase):
    def test_load_ownership_reports_zone_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "ownership.yaml").write_text(OWNERSHIP, encoding="utf-8")

            ownership = load_ownership(root)

            self.assertIsNotNone(ownership)
            assert ownership is not None
            local = ownership.metadata_for("packs/local/acme/skills/sample/meta.md")
            shared = ownership.metadata_for("packs/business-intake/skills/sample/meta.md")
            self.assertEqual("local-packs", local["zone"])
            self.assertEqual("local/acme", local["pack_id"])
            self.assertTrue(local["local_only"])
            self.assertEqual("shared-packs", shared["zone"])
            self.assertEqual("business-intake", shared["pack_id"])
            self.assertFalse(shared["local_only"])
            self.assertTrue(ownership.content_hash)

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


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from xrefkit.packmeta import (
    _discover_manifests,
    cmd_pack_lint,
    current_os_contract_version,
    list_packs,
    validate_pack_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _valid_manifest(*, contract: str | None = None) -> str:
    version = contract or current_os_contract_version()
    return (
        "<!-- xid: ABCDEF012345 -->\n\n"
        "# Pack Manifest: sample\n\n"
        "- pack_id: `sample`\n"
        "- summary: sample pack summary\n"
        "- maturity: `trial`\n"
        "- depends_on:\n"
        f"  - os_contract_version: `{version}`\n"
        "- entry: `docs/entry.md`\n"
        "- owns_skills:\n"
        "  - `skills/packs/sample/sample_skill`\n"
    )


def _make_pack(root: Path, pack: str = "sample", skill: str = "sample_skill") -> None:
    _write(root / "skills" / "packs" / pack / skill / "meta.md", "- skill_id: `x`\n")
    _write(root / "docs" / "entry.md", "entry\n")


class PackManifestTests(unittest.TestCase):
    def test_valid_manifest_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_pack(root)
            manifest = root / "skills" / "packs" / "sample" / "pack.md"
            _write(manifest, _valid_manifest())

            result = validate_pack_manifest(manifest, root=root)

            self.assertTrue(result.ok, result.errors)
            self.assertEqual("sample", result.pack_id)

    def test_stale_os_contract_version_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_pack(root)
            manifest = root / "skills" / "packs" / "sample" / "pack.md"
            _write(manifest, _valid_manifest(contract="0"))

            result = validate_pack_manifest(manifest, root=root)

            self.assertFalse(result.ok)
            self.assertTrue(any("pack revalidation required" in e for e in result.errors), result.errors)

    def test_owned_skill_missing_meta_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "docs" / "entry.md", "entry\n")  # no skill dir created
            manifest = root / "skills" / "packs" / "sample" / "pack.md"
            _write(manifest, _valid_manifest())

            result = validate_pack_manifest(manifest, root=root)

            self.assertFalse(result.ok)
            self.assertTrue(any("no meta.md" in e for e in result.errors), result.errors)

    def test_owned_skill_in_os_core_is_boundary_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "skills" / "os" / "some_util" / "meta.md", "- skill_id: `u`\n")
            _write(root / "docs" / "entry.md", "entry\n")
            manifest = root / "skills" / "packs" / "sample" / "pack.md"
            _write(
                manifest,
                _valid_manifest().replace(
                    "  - `skills/packs/sample/sample_skill`\n",
                    "  - `skills/os/some_util`\n",
                ),
            )

            result = validate_pack_manifest(manifest, root=root)

            self.assertFalse(result.ok)
            self.assertTrue(any("boundary violation" in e for e in result.errors), result.errors)

    def test_missing_owns_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "docs" / "entry.md", "entry\n")
            manifest = root / "skills" / "packs" / "sample" / "pack.md"
            text = "\n".join(_valid_manifest().splitlines()[:8]) + "\n"  # drop owns_skills block
            _write(manifest, text)

            result = validate_pack_manifest(manifest, root=root)

            self.assertFalse(result.ok)
            self.assertTrue(any("owns no assets" in e for e in result.errors), result.errors)

    def test_cross_pack_exclusive_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Two packs both claim the same skill dir as owned.
            _write(root / "skills" / "packs" / "p1" / "shared" / "meta.md", "- skill_id: `s`\n")
            _write(root / "docs" / "entry.md", "entry\n")
            shared_owns = "- owns_skills:\n  - `skills/packs/p1/shared`\n"
            for pack in ("p1", "p2"):
                body = (
                    "<!-- xid: ABCDEF012345 -->\n\n"
                    f"# Pack Manifest: {pack}\n\n"
                    f"- pack_id: `{pack}`\n"
                    "- summary: s\n"
                    "- maturity: `trial`\n"
                    "- depends_on:\n"
                    f"  - os_contract_version: `{current_os_contract_version()}`\n"
                    "- entry: `docs/entry.md`\n"
                    + shared_owns
                )
                _write(root / "skills" / "packs" / pack / "pack.md", body)

            args = SimpleNamespace(root=str(root), manifest=None, json=True)
            rc = cmd_pack_lint(args)

            self.assertEqual(1, rc)


class RealRepoPackTests(unittest.TestCase):
    def test_all_repo_manifests_lint_clean(self) -> None:
        manifests = _discover_manifests(REPO_ROOT)
        self.assertTrue(manifests, "no pack manifests discovered under skills/packs/")
        for manifest in manifests:
            result = validate_pack_manifest(manifest, root=REPO_ROOT)
            self.assertTrue(result.ok, f"{manifest}: {result.errors}")


class PackListTests(unittest.TestCase):
    def test_list_packs_resolves_owned_skill_ids_from_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(
                root / "skills" / "packs" / "sample" / "sample_skill" / "meta.md",
                "- skill_id: `resolved_id`\n- summary: resolved summary\n",
            )
            _write(root / "docs" / "entry.md", "entry\n")
            _write(root / "skills" / "packs" / "sample" / "pack.md", _valid_manifest())

            packs = list_packs(root)

            self.assertEqual(1, len(packs))
            self.assertEqual("sample", packs[0]["pack_id"])
            self.assertEqual("resolved_id", packs[0]["skills"][0]["skill_id"])
            self.assertEqual("resolved summary", packs[0]["skills"][0]["summary"])


if __name__ == "__main__":
    unittest.main()

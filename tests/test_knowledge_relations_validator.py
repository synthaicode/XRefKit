import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "os"
    / "knowledge_ontology_management"
    / "scripts"
    / "validate_knowledge_relations.py"
)
SPEC = importlib.util.spec_from_file_location("knowledge_relations_validator", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class KnowledgeRelationsValidatorTests(unittest.TestCase):
    @staticmethod
    def _write(root: Path, relative: str, text: str) -> None:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_accepts_indexed_fragments_with_valid_relation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "knowledge/000_index.md",
                "<!-- xid: INDEX -->\n# Knowledge Index\n"
                "- [A](a.md#xid-A)\n- [B](b.md#xid-B)\n",
            )
            self._write(
                root,
                "knowledge/a.md",
                "<!-- xid: A -->\n# A\n\n## Knowledge Relations\n"
                "- depends_on: [B](b.md#xid-B)\n",
            )
            self._write(root, "knowledge/b.md", "<!-- xid: B -->\n# B\n")

            self.assertEqual([], VALIDATOR.validate(root))

    def test_reports_fragment_missing_from_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "knowledge/000_index.md",
                "<!-- xid: INDEX -->\n# Knowledge Index\n",
            )
            self._write(root, "knowledge/a.md", "<!-- xid: A -->\n# A\n")

            errors = VALIDATOR.validate(root)

            self.assertTrue(
                any("missing from knowledge/000_index.md" in error for error in errors)
            )

    def test_reports_duplicate_primary_titles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "knowledge/000_index.md",
                "<!-- xid: INDEX -->\n# Knowledge Index\n"
                "- [A](a.md#xid-A)\n- [B](b.md#xid-B)\n",
            )
            self._write(root, "knowledge/a.md", "<!-- xid: A -->\n# Same Concept\n")
            self._write(root, "knowledge/b.md", "<!-- xid: B -->\n# same concept\n")

            errors = VALIDATOR.validate(root)

            self.assertTrue(
                any("duplicate primary title 'same concept'" in error for error in errors)
            )


if __name__ == "__main__":
    unittest.main()

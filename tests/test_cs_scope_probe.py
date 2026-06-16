import tempfile
import unittest
from pathlib import Path

from tools.cs_scope_probe import probe_cs_scope


class CsScopeProbeTests(unittest.TestCase):
    def test_cs_file_in_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "Program.cs").write_text("class C {}\n", encoding="utf-8")

            report = probe_cs_scope(root)

            self.assertTrue(report["cs_in_scope"])
            self.assertEqual(1, report["cs_file_count"])
            self.assertEqual("applicable", report["roslyn_quality_check"])

    def test_build_target_in_scope_without_cs_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "App.csproj").write_text("<Project/>\n", encoding="utf-8")

            report = probe_cs_scope(root)

            self.assertTrue(report["cs_in_scope"])
            self.assertTrue(report["has_build_target"])

    def test_no_cs_is_na(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# docs\n", encoding="utf-8")
            (root / "notes.py").write_text("x = 1\n", encoding="utf-8")

            report = probe_cs_scope(root)

            self.assertFalse(report["cs_in_scope"])
            self.assertEqual("na", report["roslyn_quality_check"])

    def test_excludes_bin_obj(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "obj").mkdir()
            (root / "obj" / "Generated.cs").write_text("class G {}\n", encoding="utf-8")
            (root / "bin").mkdir()
            (root / "bin" / "Built.cs").write_text("class B {}\n", encoding="utf-8")

            report = probe_cs_scope(root)

            self.assertFalse(report["cs_in_scope"])
            self.assertEqual(0, report["cs_file_count"])


if __name__ == "__main__":
    unittest.main()

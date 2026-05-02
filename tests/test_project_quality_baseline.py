import tempfile
import unittest
from pathlib import Path

from tools.check_project_quality_baseline import validate_project


class ProjectQualityBaselineTests(unittest.TestCase):
    def test_validate_project_accepts_check_ready_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "sample-app"
            project_dir.mkdir(parents=True, exist_ok=True)
            (project_dir / "README.md").write_text("# Sample\n", encoding="utf-8")
            (project_dir / "package.json").write_text(
                "{"
                '"name":"sample-app",'
                '"scripts":{"check":"npm run lint"},'
                '"engines":{"node":">=20"},'
                '"dependencies":{"react":"1.0.0"}'
                "}",
                encoding="utf-8",
            )
            (project_dir / "package-lock.json").write_text("{}", encoding="utf-8")

            errors = validate_project(project_dir)

            self.assertEqual([], errors)

    def test_validate_project_reports_missing_baseline_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "broken-app"
            project_dir.mkdir(parents=True, exist_ok=True)
            (project_dir / "package.json").write_text(
                "{"
                '"name":"broken-app",'
                '"scripts":{"start":"node server.js"},'
                '"dependencies":{"react":"1.0.0"}'
                "}",
                encoding="utf-8",
            )

            errors = validate_project(project_dir)

            self.assertIn("missing README.md", errors)
            self.assertIn("missing scripts.check", errors)
            self.assertIn("missing engines.node", errors)
            self.assertIn("missing package-lock.json for dependency-managed project", errors)


if __name__ == "__main__":
    unittest.main()

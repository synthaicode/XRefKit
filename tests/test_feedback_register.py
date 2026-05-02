import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import check_feedback_register


class FeedbackRegisterTests(unittest.TestCase):
    def test_validate_feedback_register_accepts_real_row_with_existing_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            register = root / "docs" / "044_system_quality_feedback_register.md"
            record = root / "work" / "retrospectives" / "2026-04-18_feedback_sample.md"
            register.parent.mkdir(parents=True, exist_ok=True)
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text("# Sample\n", encoding="utf-8")
            register.write_text(
                "| feedback_id | status | severity | triggered_from | root_workflow | failed_layer | owner_group | approval_owner | first_seen | last_updated | summary | latest_record | next_action |\n"
                "|------|------|------|------|------|------|------|------|------|------|------|------|------|\n"
                "| `FB-001` | `in_progress` | `high` | `closure_workflow` | `planning_workflow` | `Planning` | `Planning Group` | `Human decision layer` | `2026-04-18` | `2026-04-18` | quality gate gap | `work/retrospectives/2026-04-18_feedback_sample.md` | finalize automation |\n",
                encoding="utf-8",
            )

            with patch.object(check_feedback_register, "REPO_ROOT", root), patch.object(
                check_feedback_register, "REGISTER_PATH", register
            ):
                errors = check_feedback_register.validate_feedback_register()

            self.assertEqual([], errors)

    def test_validate_feedback_register_rejects_placeholder_with_real_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            register = root / "docs" / "044_system_quality_feedback_register.md"
            record = root / "work" / "retrospectives" / "2026-04-18_feedback_sample.md"
            register.parent.mkdir(parents=True, exist_ok=True)
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text("# Sample\n", encoding="utf-8")
            register.write_text(
                "| feedback_id | status | severity | triggered_from | root_workflow | failed_layer | owner_group | approval_owner | first_seen | last_updated | summary | latest_record | next_action |\n"
                "|------|------|------|------|------|------|------|------|------|------|------|------|------|\n"
                "| `none_yet` | `watch` | - | - | - | - | - | - | - | - | no structural feedback has been promoted yet | - | add first record |\n"
                "| `FB-001` | `open` | `medium` | `closure_workflow` | `planning_workflow` | `Planning` | `Planning Group` | `Human decision layer` | `2026-04-18` | `2026-04-18` | quality gate gap | `work/retrospectives/2026-04-18_feedback_sample.md` | finalize automation |\n",
                encoding="utf-8",
            )

            with patch.object(check_feedback_register, "REPO_ROOT", root), patch.object(
                check_feedback_register, "REGISTER_PATH", register
            ):
                errors = check_feedback_register.validate_feedback_register()

            self.assertIn("placeholder row `none_yet` must be removed once real feedback rows exist", errors)


if __name__ == "__main__":
    unittest.main()

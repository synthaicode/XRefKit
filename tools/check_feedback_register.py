from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPO_ROOT / "docs" / "044_system_quality_feedback_register.md"
VALID_STATUS = {"open", "in_progress", "closed", "watch"}
VALID_SEVERITY = {"critical", "high", "medium", "low", "-"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_register_rows() -> list[dict[str, str]]:
    lines = REGISTER_PATH.read_text(encoding="utf-8").splitlines()
    rows: list[dict[str, str]] = []
    in_table = False

    for line in lines:
        if line.startswith("| feedback_id |"):
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("|------|"):
            continue
        if not line.startswith("|"):
            if rows:
                break
            continue

        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 13:
            continue
        rows.append(
            {
                "feedback_id": cells[0],
                "status": cells[1],
                "severity": cells[2],
                "triggered_from": cells[3],
                "root_workflow": cells[4],
                "failed_layer": cells[5],
                "owner_group": cells[6],
                "approval_owner": cells[7],
                "first_seen": cells[8],
                "last_updated": cells[9],
                "summary": cells[10],
                "latest_record": cells[11],
                "next_action": cells[12],
            }
        )
    return rows


def validate_feedback_register() -> list[str]:
    rows = _parse_register_rows()
    errors: list[str] = []

    if not rows:
        return ["feedback register table has no rows"]

    placeholder_rows = [row for row in rows if row["feedback_id"] == "none_yet"]
    real_rows = [row for row in rows if row["feedback_id"] != "none_yet"]

    if placeholder_rows and real_rows:
        errors.append("placeholder row `none_yet` must be removed once real feedback rows exist")

    seen_ids: set[str] = set()
    for row in rows:
        feedback_id = row["feedback_id"]
        if feedback_id in seen_ids:
            errors.append(f"duplicate feedback_id: {feedback_id}")
        seen_ids.add(feedback_id)

        if row["status"] not in VALID_STATUS:
            errors.append(f"{feedback_id}: invalid status `{row['status']}`")
        if row["severity"] not in VALID_SEVERITY:
            errors.append(f"{feedback_id}: invalid severity `{row['severity']}`")

        for field_name in ("first_seen", "last_updated"):
            value = row[field_name]
            if value != "-" and not DATE_RE.match(value):
                errors.append(f"{feedback_id}: invalid {field_name} `{value}`")

        latest_record = row["latest_record"]
        if latest_record != "-":
            record_path = REPO_ROOT / latest_record
            if not record_path.exists():
                errors.append(f"{feedback_id}: latest_record does not exist: {latest_record}")

    return errors


def main() -> int:
    errors = validate_feedback_register()
    if errors:
        print(f"fail: {REGISTER_PATH.relative_to(REPO_ROOT).as_posix()}")
        for error in errors:
            print(f"  error: {error}")
        return 1

    print(f"ok: {REGISTER_PATH.relative_to(REPO_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

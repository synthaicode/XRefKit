from pathlib import Path

import pytest

from xrefkit.wbs import WbsError, parse_wbs, render_rollup, write_csv


VALID = """| ID | Feature | Phase | Task | Assignee | Estimate(Person-Days) | Actual(Person-Days) | Status |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| T-001 | Intake | Analysis | A \\| B | Aki | 2 | 1 | done |
| T-002 | Intake | Implementation | Build | Aki | 3 | 0 | doing |
| T-003 | Reporting | Test | Check | Ren | 1 | 0 | todo |
"""


def test_parse_accepts_escaped_pipe_and_rolls_up() -> None:
    headers, rows = parse_wbs(VALID)
    assert headers[1] == "Feature"
    assert rows[0][3] == "A | B"
    output = render_rollup(rows)
    assert "| Intake | 5 | 1 | 2 |" in output
    assert "| Total | 6 | 1 | 3 |" in output


@pytest.mark.parametrize(
    "text, message",
    [
        (VALID.replace("| T-003 | Reporting | Test | Check | Ren | 1 | 0 | todo |", "| T-003 | Reporting | Test | Check | Ren | 1 | todo |"), "expected 8 cells"),
        (VALID.replace("| T-003 | Reporting | Test | Check | Ren | 1 | 0 | todo |", "| T-003 | Reporting | Test | Check | Ren | -1 | 0 | todo |"), "must not be negative"),
        (VALID.replace("| T-003 | Reporting | Test | Check | Ren | 1 | 0 | todo |", "| T-003 | Reporting | Test | Check | Ren | 1 | 0 | blocked |"), "Status must be"),
    ],
)
def test_parse_rejects_invalid_rows(text: str, message: str) -> None:
    with pytest.raises(WbsError, match=message):
        parse_wbs(text)


def test_csv_is_excel_readable(tmp_path: Path) -> None:
    headers, rows = parse_wbs(VALID)
    target = tmp_path / "wbs.csv"
    write_csv(headers, rows, target)
    assert target.read_bytes().startswith(b"\xef\xbb\xbf")
    assert "T-001" in target.read_text(encoding="utf-8-sig")

"""Validate and summarize a flat Markdown WBS table."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path


CANONICAL_HEADERS = ("ID", "Feature", "Phase", "Task", "Assignee", "Estimate(Person-Days)", "Actual(Person-Days)", "Status")
HEADER_ALIASES = {
    "機能": "Feature",
    "工程": "Phase",
    "タスク": "Task",
    "担当": "Assignee",
    "見積(人日)": "Estimate(Person-Days)",
    "実績(人日)": "Actual(Person-Days)",
    "状態": "Status",
}
ALLOWED_STATUS = {"todo", "doing", "done"}
SENTINEL = "\x00"


class WbsError(ValueError):
    """A user-correctable WBS format or value error."""


def split_row(line: str) -> list[str]:
    value = line.strip().replace(r"\|", SENTINEL)
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [cell.strip().replace(SENTINEL, "|") for cell in value.split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{1,}:?", cell) for cell in cells)


def parse_wbs(text: str) -> tuple[list[str], list[list[str]]]:
    table_lines = [line for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 2:
        raise WbsError("no Markdown table with a header and separator was found")
    raw_headers = split_row(table_lines[0])
    if not _is_separator(split_row(table_lines[1])):
        raise WbsError("the second table row must be a Markdown separator")
    headers = [HEADER_ALIASES.get(header, header) for header in raw_headers]
    if headers != list(CANONICAL_HEADERS):
        raise WbsError("headers must be: " + " | ".join(CANONICAL_HEADERS))
    rows: list[list[str]] = []
    for line_number, line in enumerate(table_lines[2:], 3):
        cells = split_row(line)
        if len(cells) != len(headers):
            raise WbsError(f"line {line_number}: expected {len(headers)} cells, got {len(cells)}")
        if all(not cell for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        raise WbsError("the WBS table contains no task rows")
    for index, row in enumerate(rows, 3):
        if not row[0]:
            raise WbsError(f"task row {index}: ID is empty")
        for column in (5, 6):
            try:
                number = float(row[column])
            except ValueError as exc:
                raise WbsError(f"task row {index}: {headers[column]} must be numeric") from exc
            if number < 0:
                raise WbsError(f"task row {index}: {headers[column]} must not be negative")
        if row[7] not in ALLOWED_STATUS:
            raise WbsError(f"task row {index}: Status must be one of {sorted(ALLOWED_STATUS)}")
    ids = [row[0] for row in rows]
    if len(ids) != len(set(ids)):
        raise WbsError("task IDs must be unique")
    return headers, rows


def _number(value: str) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def aggregate(rows: list[list[str]], key_index: int) -> list[list[str]]:
    totals: dict[str, list[float | int]] = defaultdict(lambda: [0.0, 0.0, 0])
    for row in rows:
        entry = totals[row[key_index]]
        entry[0] += float(row[5])
        entry[1] += float(row[6])
        entry[2] += 1
    result = [[key, _number(str(values[0])), _number(str(values[1])), values[2]] for key, values in sorted(totals.items())]
    estimate = sum(float(row[5]) for row in rows)
    actual = sum(float(row[6]) for row in rows)
    result.append(["Total", _number(str(estimate)), _number(str(actual)), len(rows)])
    return result


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---:" if i else "---" for i in range(len(headers))) + " |"]
    lines.extend("| " + " | ".join(str(cell) for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def render_rollup(rows: list[list[str]]) -> str:
    feature = aggregate(rows, 1)
    phase = aggregate(rows, 2)
    features = sorted({row[1] for row in rows})
    phases = sorted({row[2] for row in rows})
    cross = {feature: {phase: 0.0 for phase in phases} for feature in features}
    for row in rows:
        cross[row[1]][row[2]] += float(row[5])
    cross_rows = []
    for feature_name in features:
        values = [_number(str(cross[feature_name][phase])) for phase in phases]
        cross_rows.append([feature_name, *values, _number(str(sum(cross[feature_name].values())))])
    cross_rows.append(["Total", *[_number(str(sum(cross[f][p] for f in features))) for p in phases], _number(str(sum(float(r[5]) for r in rows)))])
    return "\n\n".join([
        "## Feature Rollup\n\n" + markdown_table(["Feature", "Estimate(Person-Days)", "Actual(Person-Days)", "Task Count"], feature),
        "## Phase Rollup\n\n" + markdown_table(["Phase", "Estimate(Person-Days)", "Actual(Person-Days)", "Task Count"], phase),
        "## Feature x Phase\n\n" + markdown_table(["Feature", *phases, "Total"], cross_rows),
    ])


def write_csv(headers: list[str], rows: list[list[str]], destination: Path) -> None:
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit wbs")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "rollup", "csv"):
        command = sub.add_parser(name)
        command.add_argument("source", type=Path)
        if name == "csv":
            command.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    try:
        headers, rows = parse_wbs(args.source.read_text(encoding="utf-8"))
        if args.command == "validate":
            print(f"valid: {len(rows)} task rows")
        elif args.command == "rollup":
            print(render_rollup(rows))
        else:
            write_csv(headers, rows, args.destination)
            print(f"wrote {len(rows)} task rows to {args.destination}")
    except (OSError, UnicodeError, WbsError) as exc:
        print(f"xrefkit wbs: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

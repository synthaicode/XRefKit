"""Validate typed XID relationships in canonical knowledge Markdown."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


XID_RE = re.compile(r"<!--\s*xid\s*:\s*([A-Za-z0-9_-]+)\s*-->", re.IGNORECASE)
LINK_XID_RE = re.compile(r"#xid-([A-Za-z0-9_-]+)|\[\[([A-Za-z0-9_-]+)\]\]")
RELATION_RE = re.compile(r"^-\s+([a-z_]+)\s*:\s*(.+?)\s*$")
ALLOWED_RELATIONS = {
    "broader_than",
    "narrower_than",
    "part_of",
    "depends_on",
    "constrains",
    "applies_to",
    "related_to",
}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def relation_lines(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    in_section = False
    in_fence = False
    found: list[tuple[int, str]] = []
    for number, line in enumerate(lines, start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.strip() == "## Knowledge Relations":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.strip():
            found.append((number, line.strip()))
    return found


def validate(root: Path) -> list[str]:
    knowledge = root / "knowledge"
    documents: dict[Path, tuple[str | None, str]] = {}
    known_xids: set[str] = set()
    errors: list[str] = []

    for path in sorted(knowledge.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = XID_RE.search(text)
        xid = match.group(1) if match else None
        documents[path] = (xid, text)
        if xid:
            known_xids.add(xid)

    for path, (source_xid, text) in documents.items():
        seen: set[tuple[str, str]] = set()
        for line_number, line in relation_lines(text):
            match = RELATION_RE.match(line)
            location = f"{path.relative_to(root)}:{line_number}"
            if not match:
                errors.append(f"{location}: malformed knowledge relationship")
                continue
            relation, target_text = match.groups()
            if relation not in ALLOWED_RELATIONS:
                errors.append(f"{location}: unsupported relationship '{relation}'")
                continue
            target_match = LINK_XID_RE.search(target_text)
            if not target_match:
                errors.append(f"{location}: relationship target has no XID")
                continue
            target_xid = target_match.group(1) or target_match.group(2)
            pair = (relation, target_xid)
            if target_xid not in known_xids:
                errors.append(f"{location}: unknown target XID '{target_xid}'")
            if source_xid == target_xid:
                errors.append(f"{location}: self relationship is not allowed")
            if pair in seen:
                errors.append(
                    f"{location}: duplicate relationship '{relation}' to '{target_xid}'"
                )
            seen.add(pair)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=repository_root())
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"issues: {len(errors)}")
        return 1
    print("issues: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())

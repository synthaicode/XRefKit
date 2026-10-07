"""Validate typed XID relationships in canonical knowledge Markdown."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


XID_RE = re.compile(r"<!--\s*xid\s*:\s*([A-Za-z0-9_-]+)\s*-->", re.IGNORECASE)
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
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
    xid_owners: dict[str, set[Path]] = {}
    titles: dict[str, list[Path]] = {}
    errors: list[str] = []

    for path in sorted(knowledge.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = XID_RE.search(text)
        xid = match.group(1) if match else None
        documents[path] = (xid, text)
        for declared_xid in XID_RE.findall(text):
            xid_owners.setdefault(declared_xid, set()).add(path.resolve())
        title_match = TITLE_RE.search(text)
        if title_match and path.name != "000_index.md":
            title = title_match.group(1).strip().casefold()
            titles.setdefault(title, []).append(path)

    index_text = (knowledge / "000_index.md").read_text(encoding="utf-8")
    # Semantic targets may be repository contracts or models, not only domain
    # fragments. Only knowledge owns the index/title checks above.
    for folder in ("docs", "agent", "capabilities", "skills", "tools"):
        for path in sorted((root / folder).rglob("*.md")):
            for xid in XID_RE.findall(path.read_text(encoding="utf-8-sig")):
                xid_owners.setdefault(xid, set()).add(path.resolve())
    for xid, owners in sorted(xid_owners.items()):
        if len(owners) > 1:
            rendered = ", ".join(str(path.relative_to(root.resolve())) for path in sorted(owners))
            errors.append(f"ambiguous target XID '{xid}': {rendered}")
    for path, (xid, _) in documents.items():
        if path == knowledge / "000_index.md" or not xid:
            continue
        if f"#xid-{xid}" not in index_text:
            errors.append(
                f"{path.relative_to(root)}: canonical fragment missing from knowledge/000_index.md"
            )

    for title, paths in sorted(titles.items()):
        if len(paths) > 1:
            rendered = ", ".join(str(path.relative_to(root)) for path in paths)
            errors.append(f"duplicate primary title '{title}': {rendered}")

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
            if target_xid not in xid_owners:
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

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fm.xref import (
    DocInfo,
    XrefConfig,
    _extract_xid,
    _gen_xid,
    _replace_or_insert_xid_block,
    build_index,
)


LINK_RE = re.compile(r"\[[^\]]*\]\((?P<url>[^)\s]+)(?P<rest>[^)]*)\)")
BARE_MD_XID_RE = re.compile(
    r"(?P<path>(?:(?:\.\.?|[A-Za-z0-9_.-]+)/)*[A-Za-z0-9_.-]+\.md)#xid-(?P<xid>[A-Za-z0-9_-]{6,64})\b"
)
KNOWLEDGE_MD_RE = re.compile(r"(?P<path>(?:(?:\.\.?|[A-Za-z0-9_.-]+)/)*(?:knowledge|knowledge_private)/[A-Za-z0-9_./-]+\.md)(?!#xid-)")
LOCAL_SOURCE_RE = re.compile(
    r"(?P<path>(?:(?:\.\.?|[A-Za-z0-9_.-]+)/)*[A-Za-z0-9_./-]+\.(?:"
    r"py|ps1|sh|cs|fs|vb|js|jsx|ts|tsx|java|go|rs|c|cc|cpp|h|hpp|sql|yaml|yml|toml|ini|cfg|css|scss|html|xml|svg"
    r"))(?!#xid-)"
)
FRAGMENT_XID_RE = re.compile(r"#xid-(?P<xid>[A-Za-z0-9_-]{6,64})\b")
BIND_RE = re.compile(r"(?:^|[;\s])bind=(?P<xid>[A-Za-z0-9_-]{6,64})(?:$|[;\s])")
CANONICAL_XID_RE = re.compile(r"^[A-F0-9]{12}$")
SOURCE_XID_RE = re.compile(
    r"^\s*(?://|#|--|'|/\*|<!--)\s*xid\s*:\s*([A-Za-z0-9_-]{1,64})\s*(?:\*/|-->)?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
LINE_COMMENT_PREFIX_BY_SUFFIX = {
    ".py": "#",
    ".ps1": "#",
    ".sh": "#",
    ".yaml": "#",
    ".yml": "#",
    ".toml": "#",
    ".ini": "#",
    ".cfg": "#",
    ".js": "//",
    ".jsx": "//",
    ".ts": "//",
    ".tsx": "//",
    ".cs": "//",
    ".fs": "//",
    ".vb": "'",
    ".java": "//",
    ".go": "//",
    ".rs": "//",
    ".c": "//",
    ".cc": "//",
    ".cpp": "//",
    ".h": "//",
    ".hpp": "//",
    ".css": "/*",
    ".scss": "//",
    ".sql": "--",
}
XML_COMMENT_SUFFIXES = {".html", ".xml", ".svg"}


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "path": self.path, "message": self.message}


@dataclass(frozen=True)
class CheckResult:
    checked_skills: int
    errors: list[Finding]
    warnings: list[Finding]
    changed_files: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "checked_skills": self.checked_skills,
            "errors": [finding.to_dict() for finding in self.errors],
            "warnings": [finding.to_dict() for finding in self.warnings],
            "changed_files": self.changed_files,
        }


def _repo_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def _is_markdown(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".mdx"}


def _is_canonical_xid(xid: str) -> bool:
    return CANONICAL_XID_RE.fullmatch(xid) is not None


def _source_comment_prefix(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in XML_COMMENT_SUFFIXES:
        return "<!--"
    return LINE_COMMENT_PREFIX_BY_SUFFIX.get(suffix)


def _extract_any_xid(text: str) -> str | None:
    xid = _extract_xid(text)
    if xid:
        return xid
    match = SOURCE_XID_RE.search(text)
    if match:
        return match.group(1).strip()
    return None


def _source_xid_line(path: Path, xid: str) -> str | None:
    prefix = _source_comment_prefix(path)
    if prefix is None:
        return None
    if prefix == "<!--":
        return f"<!-- xid: {xid} -->"
    if prefix == "/*":
        return f"/* xid: {xid} */"
    return f"{prefix} xid: {xid}"


def _insert_source_xid_comment(text: str, xid_line: str) -> str:
    lines = text.splitlines()
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    if insert_at < len(lines) and re.match(r"#.*coding[:=]\s*[-\w.]+", lines[insert_at]):
        insert_at += 1
    out = lines[:insert_at] + [xid_line, ""] + lines[insert_at:]
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def _replace_source_xid_comment(text: str, xid_line: str) -> str:
    return SOURCE_XID_RE.sub(xid_line, text, count=1)


def _new_unique_xid(known_xids: set[str]) -> str:
    xid = _gen_xid()
    while xid in known_xids:
        xid = _gen_xid()
    known_xids.add(xid)
    return xid


def _ensure_xid(path: Path, *, root: Path, known_xids: set[str], changed: set[str]) -> str | None:
    if not path.exists():
        return None
    text = _read_text(path)
    xid = _extract_any_xid(text)
    if xid and _is_canonical_xid(xid):
        known_xids.add(xid)
        return xid
    xid = _new_unique_xid(known_xids)
    if _is_markdown(path):
        new_text = _replace_or_insert_xid_block(text, xid)
    else:
        xid_line = _source_xid_line(path, xid)
        if xid_line is None:
            return None
        new_text = _replace_source_xid_comment(text, xid_line) if _extract_any_xid(text) else _insert_source_xid_comment(text, xid_line)
    _write_text(path, new_text)
    changed.add(_repo_rel(path, root))
    return xid


def _meta_files_from_target(root: Path, target: str) -> list[Path]:
    path = (root / target).resolve() if not Path(target).is_absolute() else Path(target).resolve()
    if path.is_file() and path.name == "meta.md":
        return [path]
    if path.is_file() and path.name == "SKILL.md" and (path.parent / "meta.md").exists():
        return [path.parent / "meta.md"]
    if path.is_dir():
        direct = path / "meta.md"
        if direct.exists():
            return [direct]
        return sorted(path.rglob("meta.md"))
    return []


def _iter_meta_files(root: Path, *, scope: str, targets: list[str] | None = None) -> Iterable[Path]:
    if targets:
        seen: set[Path] = set()
        for target in targets:
            for path in _meta_files_from_target(root, target):
                resolved = path.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)
                yield path
        return

    search_roots = [root / "skills", root / "packs"]
    if scope == "all":
        search_roots.append(root / "skills_private")

    seen: set[Path] = set()
    for base in search_roots:
        if not base.exists():
            continue
        for path in sorted(base.rglob("meta.md")):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield path


def _parse_meta_lists(text: str) -> dict[str, list[str]]:
    lists: dict[str, list[str]] = {}
    current_key: str | None = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if raw_line.startswith("- ") and ":" in stripped[2:]:
            key, value = stripped[2:].split(":", 1)
            current_key = key.strip()
            if value.strip():
                lists[current_key] = [value.strip().strip("`")]
            else:
                lists[current_key] = []
            continue
        if current_key and stripped.startswith("- "):
            lists.setdefault(current_key, []).append(stripped[2:].strip().strip("`"))

    return lists


def _parse_meta_value(text: str, key: str) -> str | None:
    prefix = f"- {key}:"
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped.startswith(prefix):
            continue
        value = stripped[len(prefix) :].strip().strip("`")
        return value or None
    return None


def _skill_doc_for(meta_path: Path, meta_text: str) -> Path:
    raw = _parse_meta_value(meta_text, "skill_doc")
    if not raw:
        return meta_path.parent / "SKILL.md"
    return (meta_path.parent / raw).resolve()


def _index_for(root: Path, *, scope: str) -> tuple[dict[str, DocInfo], list[dict[str, str]]]:
    include = ["docs", "agent", "knowledge", "capabilities", "skills", "packs"]
    if scope == "all":
        include.extend(["knowledge_private", "skills_private"])
    return build_index(XrefConfig(root=str(root), include=include))


def _resolve_link_path(source: Path, raw_path: str, root: Path) -> Path:
    normalized = raw_path.replace("\\", "/")
    if normalized.startswith(("./", "../")):
        return (source.parent / normalized).resolve()
    top = normalized.split("/", 1)[0]
    if (root / top).exists():
        return (root / normalized).resolve()
    return (source.parent / normalized).resolve()


def _referenced_knowledge_path(source: Path, raw_path: str, root: Path) -> Path | None:
    if "knowledge/" not in raw_path and "knowledge_private/" not in raw_path:
        return None
    target = _resolve_link_path(source, raw_path, root)
    if not _is_markdown(target):
        return None
    return target


def _referenced_local_source_path(source: Path, raw_path: str, root: Path) -> Path | None:
    target = _resolve_link_path(source, raw_path, root)
    try:
        target.relative_to(root)
    except ValueError:
        return None
    if not target.exists() or _is_markdown(target):
        return None
    if _source_comment_prefix(target) is None:
        return None
    return target


def _path_matches_xid_target(
    *,
    source: Path,
    raw_path: str,
    xid: str,
    root: Path,
    index: dict[str, DocInfo],
) -> bool:
    target = index.get(xid)
    if target is None:
        resolved = _resolve_link_path(source, raw_path, root)
        if not resolved.exists():
            return False
        try:
            return _extract_any_xid(_read_text(resolved)) == xid
        except UnicodeDecodeError:
            return False
    return _resolve_link_path(source, raw_path, root) == target.path.resolve()


def _check_bound_xids(
    *,
    meta_path: Path,
    meta_text: str,
    root: Path,
    index: dict[str, DocInfo],
) -> tuple[list[Finding], list[Finding]]:
    errors: list[Finding] = []
    warnings: list[Finding] = []
    rel = _repo_rel(meta_path, root)
    lists = _parse_meta_lists(meta_text)
    slots = lists.get("knowledge_slots", [])

    for slot in slots:
        bind = BIND_RE.search(slot)
        if bind:
            xid = bind.group("xid")
            if not _is_canonical_xid(xid):
                errors.append(Finding("error", rel, f"knowledge_slots bind XID has invalid format: {xid}"))
                continue
            if xid not in index:
                errors.append(Finding("error", rel, f"knowledge_slots bind XID not found: {xid}"))
            continue
        if "query=" in slot:
            warnings.append(Finding("warning", rel, f"knowledge_slots query is dynamic and not XID-bound: {slot}"))

    for ref in lists.get("knowledge_refs", []):
        xid_match = FRAGMENT_XID_RE.search(ref)
        if not xid_match:
            errors.append(Finding("error", rel, f"knowledge_refs entry is not XID-bound: {ref}"))
            continue
        xid = xid_match.group("xid")
        if not _is_canonical_xid(xid):
            errors.append(Finding("error", rel, f"knowledge_refs XID has invalid format: {xid}"))
            continue
        if xid not in index:
            errors.append(Finding("error", rel, f"knowledge_refs XID not found: {xid}"))

    return errors, warnings


def _check_own_xid_format(path: Path, root: Path) -> list[Finding]:
    if not path.exists():
        return []
    xid = _extract_any_xid(_read_text(path))
    if xid and not _is_canonical_xid(xid):
        return [Finding("error", _repo_rel(path, root), f"own XID has invalid format: {xid}")]
    return []


def _check_markdown_links(
    *,
    path: Path,
    root: Path,
    index: dict[str, DocInfo],
) -> list[Finding]:
    rel = _repo_rel(path, root)
    errors: list[Finding] = []
    text = _read_text(path)
    in_fence = False

    for line_no, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        for missing in KNOWLEDGE_MD_RE.finditer(line):
            errors.append(
                Finding(
                    "error",
                    rel,
                    f"line {line_no}: knowledge markdown reference is missing #xid: {missing.group('path')}",
                )
            )

        for link in LINK_RE.finditer(line):
            url = link.group("url")
            if "knowledge/" not in url and "knowledge_private/" not in url:
                continue
            xid_match = FRAGMENT_XID_RE.search(url)
            if not xid_match:
                errors.append(Finding("error", rel, f"line {line_no}: knowledge link is missing #xid: {url}"))
                continue
            xid = xid_match.group("xid")
            if not _is_canonical_xid(xid):
                errors.append(Finding("error", rel, f"line {line_no}: knowledge link XID has invalid format: {xid}"))
                continue
            if xid not in index:
                errors.append(Finding("error", rel, f"line {line_no}: knowledge link XID not found: {xid}"))
                continue
            raw_path = url.split("#xid-", 1)[0]
            if raw_path and not _path_matches_xid_target(
                source=path,
                raw_path=raw_path,
                xid=xid,
                root=root,
                index=index,
            ):
                expected = _repo_rel(index[xid].path, root)
                errors.append(
                    Finding(
                        "error",
                        rel,
                        f"line {line_no}: knowledge link path does not match XID {xid}; expected {expected}",
                    )
                )

        for bare in BARE_MD_XID_RE.finditer(line):
            raw_path = bare.group("path")
            if "knowledge/" not in raw_path and "knowledge_private/" not in raw_path:
                continue
            xid = bare.group("xid")
            if not _is_canonical_xid(xid):
                errors.append(Finding("error", rel, f"line {line_no}: knowledge bare-ref XID has invalid format: {xid}"))
                continue
            if xid not in index:
                errors.append(Finding("error", rel, f"line {line_no}: knowledge bare-ref XID not found: {xid}"))
                continue
            if not _path_matches_xid_target(
                source=path,
                raw_path=raw_path,
                xid=xid,
                root=root,
                index=index,
            ):
                expected = _repo_rel(index[xid].path, root)
                errors.append(
                    Finding(
                        "error",
                        rel,
                        f"line {line_no}: knowledge bare-ref path does not match XID {xid}; expected {expected}",
                    )
                )

    return errors


def _fix_markdown_missing_xids(
    *,
    path: Path,
    root: Path,
    known_xids: set[str],
    changed: set[str],
) -> None:
    text = _read_text(path)
    in_fence = False
    out_lines: list[str] = []
    changed_text = False

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out_lines.append(line)
            continue
        if in_fence:
            out_lines.append(line)
            continue

        def repl_link(match: re.Match[str]) -> str:
            nonlocal changed_text
            url = match.group("url")
            existing_xid = FRAGMENT_XID_RE.search(url)
            if existing_xid and _is_canonical_xid(existing_xid.group("xid")):
                return match.group(0)
            raw_url = url.split("#xid-", 1)[0]
            target = _referenced_knowledge_path(path, raw_url, root) or _referenced_local_source_path(path, raw_url, root)
            if target is None:
                return match.group(0)
            xid = _ensure_xid(target, root=root, known_xids=known_xids, changed=changed)
            if not xid:
                return match.group(0)
            changed_text = True
            return match.group(0).replace(url, f"{raw_url}#xid-{xid}", 1)

        line = LINK_RE.sub(repl_link, line)

        def repl_bare_knowledge(match: re.Match[str]) -> str:
            nonlocal changed_text
            raw_path = match.group("path")
            existing_xid = FRAGMENT_XID_RE.search(match.group(0))
            if existing_xid and _is_canonical_xid(existing_xid.group("xid")):
                return match.group(0)
            raw_path = raw_path.split("#xid-", 1)[0]
            target = _referenced_knowledge_path(path, raw_path, root)
            if target is None:
                return match.group(0)
            xid = _ensure_xid(target, root=root, known_xids=known_xids, changed=changed)
            if not xid:
                return match.group(0)
            changed_text = True
            return f"{raw_path}#xid-{xid}"

        line = KNOWLEDGE_MD_RE.sub(repl_bare_knowledge, line)

        def repl_bare_source(match: re.Match[str]) -> str:
            nonlocal changed_text
            raw_path = match.group("path")
            existing_xid = FRAGMENT_XID_RE.search(match.group(0))
            if existing_xid and _is_canonical_xid(existing_xid.group("xid")):
                return match.group(0)
            raw_path = raw_path.split("#xid-", 1)[0]
            target = _referenced_local_source_path(path, raw_path, root)
            if target is None:
                return match.group(0)
            xid = _ensure_xid(target, root=root, known_xids=known_xids, changed=changed)
            if not xid:
                return match.group(0)
            changed_text = True
            return f"{raw_path}#xid-{xid}"

        line = LOCAL_SOURCE_RE.sub(repl_bare_source, line)
        out_lines.append(line)

    new_text = "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")
    if changed_text and new_text != text:
        _write_text(path, new_text)
        changed.add(_repo_rel(path, root))


def _fix_missing_xids_for_skills(
    *,
    root: Path,
    scope: str,
    targets: list[str] | None,
) -> list[str]:
    index, _ = _index_for(root, scope=scope)
    known_xids = set(index)
    changed: set[str] = set()

    for meta_path in _iter_meta_files(root, scope=scope, targets=targets):
        _ensure_xid(meta_path, root=root, known_xids=known_xids, changed=changed)
        meta_text = _read_text(meta_path)
        skill_doc = _skill_doc_for(meta_path, meta_text)
        _ensure_xid(skill_doc, root=root, known_xids=known_xids, changed=changed)
        if skill_doc.exists():
            _fix_markdown_missing_xids(
                path=skill_doc,
                root=root,
                known_xids=known_xids,
                changed=changed,
            )
        _fix_markdown_missing_xids(
            path=meta_path,
            root=root,
            known_xids=known_xids,
            changed=changed,
        )

    return sorted(changed)


def check_skill_knowledge_xids(
    *,
    root: Path = REPO_ROOT,
    scope: str = "all",
    targets: list[str] | None = None,
    fix_missing_xids: bool = False,
) -> CheckResult:
    root = root.resolve()
    changed_files = (
        _fix_missing_xids_for_skills(root=root, scope=scope, targets=targets)
        if fix_missing_xids
        else []
    )
    index, index_issues = _index_for(root, scope=scope)
    errors: list[Finding] = []
    warnings: list[Finding] = []

    for issue in index_issues:
        errors.append(Finding("error", str(issue.get("path", "")), f"xref index issue: {json.dumps(issue, ensure_ascii=False)}"))

    checked_skills = 0
    for meta_path in _iter_meta_files(root, scope=scope, targets=targets):
        checked_skills += 1
        meta_text = _read_text(meta_path)
        errors.extend(_check_own_xid_format(meta_path, root))
        meta_errors, meta_warnings = _check_bound_xids(
            meta_path=meta_path,
            meta_text=meta_text,
            root=root,
            index=index,
        )
        errors.extend(meta_errors)
        warnings.extend(meta_warnings)
        errors.extend(_check_markdown_links(path=meta_path, root=root, index=index))

        skill_doc = _skill_doc_for(meta_path, meta_text)
        if not skill_doc.exists():
            errors.append(Finding("error", _repo_rel(meta_path, root), f"skill_doc not found: {_repo_rel(skill_doc, root)}"))
            continue
        errors.extend(_check_own_xid_format(skill_doc, root))
        errors.extend(_check_markdown_links(path=skill_doc, root=root, index=index))

    return CheckResult(
        checked_skills=checked_skills,
        errors=errors,
        warnings=warnings,
        changed_files=changed_files,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check that Skill metadata and Skill bodies connect knowledge references by resolvable XIDs."
    )
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repository root")
    parser.add_argument(
        "--scope",
        choices=("public", "all"),
        default="all",
        help="public checks skills/ and packs/; all also checks skills_private/ and knowledge_private/",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=None,
        help="Skill meta.md, SKILL.md, or directory to check; repeat for multiple local Skills",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--fix-missing-xids",
        action="store_true",
        help="Assign missing XIDs to checked Skill files and directly referenced local Markdown/source files, then add missing #xid fragments to those links",
    )
    args = parser.parse_args(argv)

    result = check_skill_knowledge_xids(
        root=Path(args.root),
        scope=args.scope,
        targets=args.target,
        fix_missing_xids=args.fix_missing_xids,
    )
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        status = "ok" if result.ok else "fail"
        print(
            f"{status}: skill knowledge xid check "
            f"checked_skills={result.checked_skills} errors={len(result.errors)} "
            f"warnings={len(result.warnings)} changed_files={len(result.changed_files)}"
        )
        for changed in result.changed_files:
            print(f"  changed: {changed}")
        for finding in result.errors:
            print(f"  error: {finding.path}: {finding.message}")
        for finding in result.warnings:
            print(f"  warning: {finding.path}: {finding.message}")

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

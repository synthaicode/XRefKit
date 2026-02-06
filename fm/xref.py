from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import secrets
import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


XID_COMMENT_RE = re.compile(r"<!--\s*xid\s*:\s*([A-Za-z0-9_-]{1,64})\s*-->", re.IGNORECASE)
XID_ANCHOR_RE = re.compile(
    r"""<a\s+[^>]*id=["']xid-([A-Za-z0-9_-]{1,64})["'][^>]*>\s*</a>""",
    re.IGNORECASE,
)
WIKI_XREF_RE = re.compile(r"\[\[([A-Za-z0-9_-]{6,64})\]\]")
MANAGED_FRAGMENT_RE = re.compile(r"#xid-([A-Za-z0-9_-]{6,64})\b")
_PLACEHOLDER_XIDS = {"TBD", "TODO", "TEMP", "PLACEHOLDER"}
_XID_INDEX_CACHE_VERSION = 1
_XID_RELATION_SECTION_TITLE = "互換性（XID関係）"


@dataclass(frozen=True)
class XrefConfig:
    root: str = "."
    include: list[str] | None = None
    exclude: list[str] | None = None

    def resolved_root(self) -> Path:
        return Path(self.root).resolve()

    def resolved_include(self) -> list[str]:
        return self.include if self.include is not None else ["docs", "agent", "knowledge"]

    def resolved_exclude(self) -> set[str]:
        # NOTE: `ja/` is a translation/archive area and is intentionally excluded
        # from the managed XID index to avoid duplicate XIDs across languages.
        base = {".git", ".xref", "node_modules", ".venv", "venv", "__pycache__", "ja"}
        if self.exclude is None:
            return base
        return base.union(set(self.exclude))


@dataclass(frozen=True)
class DocInfo:
    path: Path
    xid: str
    title: str | None
    content_hash: str | None = None


def _xid_index_cache_path(root: Path) -> Path:
    return root / ".xref" / "xid-index.json"


def _safe_read_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _collect_fingerprints(
    *,
    root: Path,
    include: Iterable[str],
    exclude_names: set[str],
) -> list[dict[str, object]]:
    fps: list[dict[str, object]] = []
    for p in _iter_markdown_files(root, include, exclude_names):
        try:
            st = p.stat()
        except OSError:
            continue
        fps.append(
            {
                "path": str(p.relative_to(root)).replace("\\", "/"),
                "mtime_ns": int(st.st_mtime_ns),
                "size": int(st.st_size),
            }
        )
    fps.sort(key=lambda d: str(d["path"]))
    return fps


def _fingerprints_equal(a: list[dict[str, object]], b: list[dict[str, object]]) -> bool:
    if len(a) != len(b):
        return False
    for da, db in zip(a, b, strict=True):
        if da.get("path") != db.get("path"):
            return False
        if int(da.get("mtime_ns", -1)) != int(db.get("mtime_ns", -2)):
            return False
        if int(da.get("size", -1)) != int(db.get("size", -2)):
            return False
    return True


def _try_load_cached_index(
    *,
    root: Path,
    include: list[str],
    exclude_names: set[str],
    fingerprints: list[dict[str, object]],
) -> tuple[dict[str, DocInfo], list[dict[str, str]]] | None:
    cache_path = _xid_index_cache_path(root)
    payload = _safe_read_json(cache_path)
    if not isinstance(payload, dict):
        return None

    if int(payload.get("version", 0)) != _XID_INDEX_CACHE_VERSION:
        return None
    if payload.get("include") != include:
        return None
    if payload.get("exclude_names") != sorted(exclude_names):
        return None

    cached_fps = payload.get("fingerprints")
    if not isinstance(cached_fps, list):
        return None
    if not _fingerprints_equal(fingerprints, cached_fps):
        return None

    cached_index = payload.get("index")
    if not isinstance(cached_index, dict):
        return None
    cached_issues = payload.get("issues", [])
    if not isinstance(cached_issues, list):
        return None

    index: dict[str, DocInfo] = {}
    for xid, info in cached_index.items():
        if not isinstance(xid, str) or not isinstance(info, dict):
            return None
        rel = info.get("path")
        if not isinstance(rel, str):
            return None
        title = info.get("title")
        if title is not None and not isinstance(title, str):
            return None
        content_hash = info.get("content_hash")
        if content_hash is not None and not isinstance(content_hash, str):
            return None
        index[xid] = DocInfo(path=(root / rel), xid=xid, title=title, content_hash=content_hash)

    issues: list[dict[str, str]] = []
    for it in cached_issues:
        if isinstance(it, dict):
            issues.append({str(k): str(v) for k, v in it.items()})
    return index, issues


def _write_index_cache(
    *,
    root: Path,
    include: list[str],
    exclude_names: set[str],
    fingerprints: list[dict[str, object]],
    index: dict[str, DocInfo],
    issues: list[dict[str, str]],
) -> None:
    cache_path = _xid_index_cache_path(root)
    payload = {
        "version": _XID_INDEX_CACHE_VERSION,
        "generated_at": int(time.time()),
        "include": include,
        "exclude_names": sorted(exclude_names),
        "fingerprints": fingerprints,
        "index": {
            xid: {
                "path": str(info.path.relative_to(root)).replace("\\", "/"),
                "title": info.title,
                "content_hash": info.content_hash,
            }
            for xid, info in index.items()
        },
        "issues": issues,
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _iter_markdown_files(root: Path, include: Iterable[str], exclude_names: set[str]) -> Iterable[Path]:
    for top in include:
        base = (root / top)
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".md", ".mdx"}:
                continue
            if any(part in exclude_names for part in p.parts):
                continue
            yield p


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _extract_xid(text: str) -> str | None:
    m = XID_COMMENT_RE.search(text)
    if m:
        xid = m.group(1).strip()
        if xid.upper() in _PLACEHOLDER_XIDS:
            return None
        return xid
    m = XID_ANCHOR_RE.search(text)
    if m:
        xid = m.group(1).strip()
        if xid.upper() in _PLACEHOLDER_XIDS:
            return None
        return xid
    return None


def _extract_title(text: str) -> str | None:
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _gen_xid() -> str:
    # 12 hex chars (48 bits) is enough for local doc IDs with extremely low collision risk.
    return secrets.token_hex(6).upper()

def _has_any_xid_marker(text: str) -> bool:
    return XID_COMMENT_RE.search(text) is not None or XID_ANCHOR_RE.search(text) is not None


def _normalize_for_hash(text: str) -> str:
    """
    Produce a stable-ish representation for "has this doc meaningfully changed?" hints.
    We intentionally ignore the XID block itself, and normalize line endings/whitespace.
    """
    out = text.replace("\r\n", "\n").replace("\r", "\n")
    out = XID_COMMENT_RE.sub("", out, count=1)
    out = XID_ANCHOR_RE.sub("", out, count=1)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip() + "\n"


def _content_hash(text: str) -> str:
    blob = _normalize_for_hash(text).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


def _load_any_cache_index(root: Path) -> dict[str, DocInfo] | None:
    """
    Load whatever is in the cache file without validating fingerprints.
    Used to compute "review hints" as a best-effort before overwriting cache.
    """
    payload = _safe_read_json(_xid_index_cache_path(root))
    if not isinstance(payload, dict):
        return None
    cached_index = payload.get("index")
    if not isinstance(cached_index, dict):
        return None
    out: dict[str, DocInfo] = {}
    for xid, info in cached_index.items():
        if not isinstance(xid, str) or not isinstance(info, dict):
            continue
        rel = info.get("path")
        if not isinstance(rel, str):
            continue
        title = info.get("title")
        if title is not None and not isinstance(title, str):
            title = None
        content_hash = info.get("content_hash")
        if content_hash is not None and not isinstance(content_hash, str):
            content_hash = None
        out[xid] = DocInfo(path=(root / rel), xid=xid, title=title, content_hash=content_hash)
    return out


def _replace_or_insert_xid_block(text: str, xid: str) -> str:
    """
    If an xid marker exists (including placeholders like TBD), replace it.
    Otherwise insert a new xid block near the top.
    """
    if not _has_any_xid_marker(text):
        return _ensure_xid_block(text, xid)

    new_text = text
    if XID_COMMENT_RE.search(new_text):
        new_text = XID_COMMENT_RE.sub(f"<!-- xid: {xid} -->", new_text, count=1)
    else:
        # Anchor exists but comment missing; insert comment just before the first anchor.
        new_text = XID_ANCHOR_RE.sub(f"<!-- xid: {xid} -->\n\\g<0>", new_text, count=1)

    if XID_ANCHOR_RE.search(new_text):
        new_text = XID_ANCHOR_RE.sub(f'<a id="xid-{xid}"></a>', new_text, count=1)
    else:
        # Comment exists but anchor missing; insert anchor right after the comment.
        new_text = XID_COMMENT_RE.sub(f"<!-- xid: {xid} -->\n<a id=\"xid-{xid}\"></a>", new_text, count=1)

    return new_text


def _ensure_xid_block(text: str, xid: str) -> str:
    if _extract_xid(text) is not None:
        return text
    lines = text.splitlines()
    insert_at = 0
    if lines and lines[0].strip().startswith("---"):
        # Skip YAML frontmatter if present.
        insert_at = 1
        while insert_at < len(lines):
            if lines[insert_at].strip() == "---":
                insert_at += 1
                break
            insert_at += 1
    block = [
        f"<!-- xid: {xid} -->",
        f'<a id="xid-{xid}"></a>',
        "",
    ]
    out = lines[:insert_at] + block + lines[insert_at:]
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def build_index(cfg: XrefConfig) -> tuple[dict[str, DocInfo], list[dict[str, str]]]:
    root = cfg.resolved_root()
    include = cfg.resolved_include()
    exclude_names = cfg.resolved_exclude()

    fingerprints = _collect_fingerprints(root=root, include=include, exclude_names=exclude_names)
    cached = _try_load_cached_index(
        root=root,
        include=include,
        exclude_names=exclude_names,
        fingerprints=fingerprints,
    )
    if cached is not None:
        return cached

    index: dict[str, DocInfo] = {}
    issues: list[dict[str, str]] = []
    for path in _iter_markdown_files(root, include, exclude_names):
        text = _read_text(path)
        xid = _extract_xid(text)
        if xid is None:
            continue
        if len(xid) < 6:
            issues.append(
                {
                    "type": "invalid_xid",
                    "xid": xid,
                    "path": str(path.relative_to(root)),
                    "reason": "xid_too_short",
                }
            )
            continue
        title = _extract_title(text)
        chash = _content_hash(text)
        if xid in index:
            issues.append(
                {
                    "type": "duplicate_xid",
                    "xid": xid,
                    "path_a": str(index[xid].path.relative_to(root)),
                    "path_b": str(path.relative_to(root)),
                }
            )
            continue
        index[xid] = DocInfo(path=path, xid=xid, title=title, content_hash=chash)

    _write_index_cache(
        root=root,
        include=include,
        exclude_names=exclude_names,
        fingerprints=fingerprints,
        index=index,
        issues=issues,
    )
    return index, issues


def _relative_url(from_path: Path, to_path: Path) -> str:
    rel = os.path.relpath(to_path, start=from_path.parent)
    # Markdown prefers forward slashes.
    return Path(rel).as_posix()


def _rewrite_managed_links_in_text(
    *,
    text: str,
    source_path: Path,
    root: Path,
    index: dict[str, DocInfo],
    issues: list[dict[str, str]],
) -> str:
    in_fence = False
    out_lines: list[str] = []

    # Inline link pattern; intentionally simple, but we only rewrite URLs that contain "#xid-...".
    link_re = re.compile(r"(!?)\[[^\]]*\]\(([^)\s]+)([^)]*)\)")

    for line in text.splitlines(keepends=False):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            out_lines.append(line)
            continue
        if in_fence:
            out_lines.append(line)
            continue

        def repl(m: re.Match[str]) -> str:
            if m.group(1) == "!":
                return m.group(0)
            url = m.group(2)
            rest = m.group(3)
            frag = MANAGED_FRAGMENT_RE.search(url)
            if not frag:
                return m.group(0)
            xid = frag.group(1)
            if xid not in index:
                issues.append(
                    {
                        "type": "broken_xref",
                        "xid": xid,
                        "from": str(source_path.relative_to(root)),
                    }
                )
                return m.group(0)
            target_path = index[xid].path
            if target_path.resolve() == source_path.resolve():
                new_url = f"#xid-{xid}"
            else:
                new_url = _relative_url(source_path, target_path) + f"#xid-{xid}"
            # Preserve any trailing title part: (url "title")
            return m.group(0).replace(url + rest, new_url + rest, 1)

        rewritten = link_re.sub(repl, line)

        # Convert wiki xrefs [[XID]] into standard links, so link checking works everywhere.
        def repl_wiki(m: re.Match[str]) -> str:
            xid = m.group(1)
            if xid not in index:
                issues.append(
                    {
                        "type": "broken_xref",
                        "xid": xid,
                        "from": str(source_path.relative_to(root)),
                    }
                )
                return m.group(0)
            target = index[xid]
            label = target.title or xid
            if target.path.resolve() == source_path.resolve():
                url = f"#xid-{xid}"
            else:
                url = _relative_url(source_path, target.path) + f"#xid-{xid}"
            return f"[{label}]({url})"

        rewritten = WIKI_XREF_RE.sub(repl_wiki, rewritten)
        out_lines.append(rewritten)

    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


def xref_init(cfg: XrefConfig, dry_run: bool) -> dict[str, object]:
    root = cfg.resolved_root()
    include = cfg.resolved_include()
    exclude_names = cfg.resolved_exclude()

    changed: list[str] = []
    added: list[dict[str, str]] = []
    for path in _iter_markdown_files(root, include, exclude_names):
        text = _read_text(path)
        if _extract_xid(text) is not None:
            continue
        xid = _gen_xid()
        new_text = _replace_or_insert_xid_block(text, xid)
        added.append({"path": str(path.relative_to(root)), "xid": xid})
        if new_text != text:
            changed.append(str(path.relative_to(root)))
            if not dry_run:
                _write_text(path, new_text)

    return {"changed_files": changed, "added": added, "dry_run": dry_run}


def xref_rewrite(cfg: XrefConfig, dry_run: bool) -> dict[str, object]:
    root = cfg.resolved_root()
    include = cfg.resolved_include()
    exclude_names = cfg.resolved_exclude()

    index, index_issues = build_index(cfg)
    issues: list[dict[str, str]] = list(index_issues)
    changed: list[str] = []

    for path in _iter_markdown_files(root, include, exclude_names):
        text = _read_text(path)
        new_text = _rewrite_managed_links_in_text(
            text=text, source_path=path, root=root, index=index, issues=issues
        )
        if new_text != text:
            changed.append(str(path.relative_to(root)))
            if not dry_run:
                _write_text(path, new_text)

    return {"changed_files": changed, "issues": issues, "dry_run": dry_run}


def _build_review_hints(
    *,
    root: Path,
    prev_index: dict[str, DocInfo] | None,
    curr_index: dict[str, DocInfo],
) -> list[dict[str, str]]:
    if not prev_index:
        return []

    review: list[dict[str, str]] = []
    for xid, curr in curr_index.items():
        prev = prev_index.get(xid)
        if prev is None:
            continue
        moved = str(prev.path.relative_to(root)).replace("\\", "/") != str(curr.path.relative_to(root)).replace(
            "\\", "/"
        )
        title_changed = (prev.title or "") != (curr.title or "")
        content_changed = (
            prev.content_hash is not None
            and curr.content_hash is not None
            and prev.content_hash != curr.content_hash
        )
        if not (moved or title_changed or content_changed):
            continue

        item: dict[str, str] = {"xid": xid}
        item["path_before"] = str(prev.path.relative_to(root)).replace("\\", "/")
        item["path_after"] = str(curr.path.relative_to(root)).replace("\\", "/")
        if prev.title:
            item["title_before"] = prev.title
        if curr.title:
            item["title_after"] = curr.title
        flags: list[str] = []
        if moved:
            flags.append("moved")
        if title_changed:
            flags.append("title_changed")
        if content_changed:
            flags.append("content_changed")
        item["flags"] = ",".join(flags)
        review.append(item)

    review.sort(key=lambda d: (d.get("path_after", ""), d.get("xid", "")))
    return review


def xref_check(cfg: XrefConfig, *, review: bool = False) -> dict[str, object]:
    root = cfg.resolved_root()
    include = cfg.resolved_include()
    exclude_names = cfg.resolved_exclude()

    prev_index = _load_any_cache_index(root) if review else None
    index, issues = build_index(cfg)

    missing_xid: list[str] = []
    for path in _iter_markdown_files(root, include, exclude_names):
        text = _read_text(path)
        if _extract_xid(text) is None:
            missing_xid.append(str(path.relative_to(root)))

    # Validate managed links (with #xid-...)
    for path in _iter_markdown_files(root, include, exclude_names):
        text = _read_text(path)
        for m in MANAGED_FRAGMENT_RE.finditer(text):
            xid = m.group(1)
            if xid not in index:
                issues.append(
                    {
                        "type": "broken_xref",
                        "xid": xid,
                        "from": str(path.relative_to(root)),
                    }
                )

    payload: dict[str, object] = {"index_size": len(index), "missing_xid": missing_xid, "issues": issues}
    if review:
        payload["review"] = _build_review_hints(root=root, prev_index=prev_index, curr_index=index)
    return payload


def cmd_xref(args: argparse.Namespace, cfg: XrefConfig) -> int:
    if args.xref_cmd == "init":
        result = xref_init(cfg, dry_run=bool(args.dry_run))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.xref_cmd == "rewrite":
        result = xref_rewrite(cfg, dry_run=bool(args.dry_run))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.xref_cmd == "check":
        result = xref_check(cfg, review=bool(getattr(args, "review", False)))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            missing = result["missing_xid"]
            issues = result["issues"]
            print(f"index_size: {result['index_size']}")
            print(f"missing_xid: {len(missing)}")
            for p in missing[:50]:
                print(f"  - {p}")
            if len(missing) > 50:
                print(f"  ... +{len(missing) - 50} more")
            print(f"issues: {len(issues)}")
            for i in issues[:50]:
                print("  - " + json.dumps(i, ensure_ascii=False))
            if len(issues) > 50:
                print(f"  ... +{len(issues) - 50} more")
            review_items = result.get("review") if isinstance(result, dict) else None
            if isinstance(review_items, list) and review_items:
                print(f"review: {len(review_items)}")
                for r in review_items[:50]:
                    print("  - " + json.dumps(r, ensure_ascii=False))
                if len(review_items) > 50:
                    print(f"  ... +{len(review_items) - 50} more")
        has_errors = bool(result["missing_xid"]) or bool(result["issues"])
        return 1 if has_errors else 0

    if args.xref_cmd == "fix":
        dry_run = bool(getattr(args, "dry_run", False))
        include_review = bool(getattr(args, "review", False))
        as_json = bool(getattr(args, "json", False))

        init_result = xref_init(cfg, dry_run=dry_run)
        rewrite_result = xref_rewrite(cfg, dry_run=dry_run)
        check_result = xref_check(cfg, review=include_review)
        payload = {
            "dry_run": dry_run,
            "init": init_result,
            "rewrite": rewrite_result,
            "check": check_result,
        }

        if as_json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print("phase:init")
            print(f"  changed_files: {len(init_result['changed_files'])}")
            print(f"  added_xids: {len(init_result['added'])}")
            print("phase:rewrite")
            print(f"  changed_files: {len(rewrite_result['changed_files'])}")
            print(f"  issues: {len(rewrite_result['issues'])}")
            print("phase:check")
            print(f"  index_size: {check_result['index_size']}")
            print(f"  missing_xid: {len(check_result['missing_xid'])}")
            print(f"  issues: {len(check_result['issues'])}")
            review_items = check_result.get("review")
            if isinstance(review_items, list):
                print(f"  review: {len(review_items)}")

        has_errors = bool(check_result["missing_xid"]) or bool(check_result["issues"])
        return 1 if has_errors else 0

    if args.xref_cmd == "index":
        index, index_issues = build_index(cfg)
        payload = {
            "issues": index_issues,
            "index": {xid: str(info.path.relative_to(cfg.resolved_root())) for xid, info in index.items()},
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.xref_cmd == "show":
        root = cfg.resolved_root()
        index, issues = build_index(cfg)
        xid = str(args.xid)
        if xid not in index:
            payload = {"ok": False, "xid": xid, "issues": issues, "error": "xid_not_found"}
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
        path = index[xid].path
        text = _read_text(path)
        max_bytes = int(args.max_bytes)
        blob = text.encode("utf-8")
        shown = blob[:max_bytes].decode("utf-8", errors="ignore")
        rel = str(path.relative_to(root)).replace("\\", "/")
        if args.json:
            payload = {
                "ok": True,
                "xid": xid,
                "path": rel,
                "title": index[xid].title,
                "truncated": len(blob) > max_bytes,
                "text": shown,
                "issues": issues,
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"# {index[xid].title or xid}")
            print(f"- xid: {xid}")
            print(f"- path: {rel}")
            print("")
            print(shown, end="" if shown.endswith("\n") else "\n")
            if len(blob) > max_bytes:
                print("\n... (truncated)")
        return 0

    if args.xref_cmd == "search":
        root = cfg.resolved_root()
        include = cfg.resolved_include()
        exclude_names = cfg.resolved_exclude()
        index, issues = build_index(cfg)

        query = str(args.query)
        limit = max(1, int(args.limit))

        regex = None
        if len(query) >= 3 and query.startswith("/") and query.endswith("/"):
            try:
                regex = re.compile(query[1:-1], re.IGNORECASE)
            except re.error:
                regex = None

        results: list[dict[str, object]] = []
        for path in _iter_markdown_files(root, include, exclude_names):
            text = _read_text(path)
            xid = _extract_xid(text)
            if xid is None:
                continue
            hay = text
            matched = False
            if regex is not None:
                matched = bool(regex.search(hay))
            else:
                matched = query.lower() in hay.lower()
            if not matched:
                continue

            rel = str(path.relative_to(root)).replace("\\", "/")
            title = _extract_title(text)
            snippet = ""
            # Cheap snippet: first line that matches.
            for line in text.splitlines():
                if (regex and regex.search(line)) or (not regex and query.lower() in line.lower()):
                    snippet = line.strip()
                    break
            results.append({"xid": xid, "title": title, "path": rel, "snippet": snippet})
            if len(results) >= limit:
                break

        payload = {"query": query, "results": results, "issues": issues}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            for r in results:
                label = r["title"] or r["xid"]
                print(f"- {label} ({r['path']}#xid-{r['xid']})")
                if r["snippet"]:
                    print(f"  {r['snippet']}")
        return 0

    if args.xref_cmd == "deprecate":
        result = xref_deprecate(
            cfg,
            old_xid=str(args.old_xid),
            new_xid=str(args.new_xid),
            note=(str(args.note) if args.note is not None else None),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    raise ValueError(f"Unknown xref command: {args.xref_cmd}")


def _ensure_relation_section(
    *,
    text: str,
    role: str,
    other_xid: str,
    note: str | None,
) -> str:
    """
    Add/update a human-facing section that records predecessor/successor relationship.
    This is intentionally simple and idempotent-ish.
    """
    other_link = f"[[{other_xid}]]"
    lines = text.splitlines()

    header = f"## {_XID_RELATION_SECTION_TITLE}"
    if any(l.strip() == header for l in lines):
        # Update in-place: ensure required bullets exist somewhere after the header, before next "## ".
        out: list[str] = []
        i = 0
        while i < len(lines):
            out.append(lines[i])
            if lines[i].strip() != header:
                i += 1
                continue
            i += 1
            # Consume section body.
            body: list[str] = []
            while i < len(lines) and not lines[i].startswith("## "):
                body.append(lines[i])
                i += 1

            def has_prefix(prefix: str) -> bool:
                return any(b.lstrip().startswith(prefix) for b in body)

            # Minimal normalized bullets.
            status_line = "- status: deprecated" if role == "old" else "- status: active"
            rel_line = "- superseded_by: " + other_link if role == "old" else "- supersedes: " + other_link

            if not has_prefix("- status:"):
                body = [status_line, *body]
            else:
                # If status exists, keep as-is.
                pass
            if not (has_prefix("- superseded_by:") or has_prefix("- supersedes:")):
                body = [*body, rel_line]
            else:
                # Ensure the right relationship line exists.
                if role == "old" and not has_prefix("- superseded_by:"):
                    body = [*body, rel_line]
                if role == "new" and not has_prefix("- supersedes:"):
                    body = [*body, rel_line]

            if note and not has_prefix("- note:"):
                body = [*body, f"- note: {note}"]

            out.extend(body)
        return "\n".join(out) + ("\n" if text.endswith("\n") else "")

    # Append a new section near the top (after the title if possible), otherwise at end.
    insert_at = len(lines)
    # Try to insert after the first H1 section (after first blank line after "# ").
    for idx, line in enumerate(lines):
        if line.startswith("# "):
            # find next blank line after heading block
            j = idx + 1
            while j < len(lines) and lines[j].strip() != "":
                j += 1
            # include that blank line
            insert_at = min(len(lines), j + 1)
            break

    status_line = "- status: deprecated" if role == "old" else "- status: active"
    rel_line = "- superseded_by: " + other_link if role == "old" else "- supersedes: " + other_link

    block = [
        header,
        "",
        status_line,
        rel_line,
    ]
    if note:
        block.append(f"- note: {note}")
    block.extend(["", ""])

    out_lines = lines[:insert_at] + block + lines[insert_at:]
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


def xref_deprecate(cfg: XrefConfig, *, old_xid: str, new_xid: str, note: str | None) -> dict[str, object]:
    root = cfg.resolved_root()
    index, issues = build_index(cfg)

    if old_xid not in index:
        return {"ok": False, "error": "old_xid_not_found", "old_xid": old_xid, "issues": issues}
    if new_xid not in index:
        return {"ok": False, "error": "new_xid_not_found", "new_xid": new_xid, "issues": issues}
    if old_xid == new_xid:
        return {"ok": False, "error": "same_xid", "xid": old_xid, "issues": issues}

    old_path = index[old_xid].path
    new_path = index[new_xid].path

    old_text = _read_text(old_path)
    new_text = _read_text(new_path)

    updated_old = _ensure_relation_section(text=old_text, role="old", other_xid=new_xid, note=note)
    updated_new = _ensure_relation_section(text=new_text, role="new", other_xid=old_xid, note=None)

    changed: list[str] = []
    if updated_old != old_text:
        _write_text(old_path, updated_old)
        changed.append(str(old_path.relative_to(root)))
    if updated_new != new_text:
        _write_text(new_path, updated_new)
        changed.append(str(new_path.relative_to(root)))

    return {
        "ok": True,
        "old_xid": old_xid,
        "new_xid": new_xid,
        "changed_files": changed,
        "issues": issues,
    }

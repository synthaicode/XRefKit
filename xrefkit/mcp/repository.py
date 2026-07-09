from __future__ import annotations

import hashlib
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


XID_RE = re.compile(r"xid[:=-]\s*([A-Za-z0-9]+)|#xid-([A-Za-z0-9]+)")
HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
MD_LINK_RE = re.compile(r"\]\((?P<target>[^)]+#xid-(?P<xid>[A-Za-z0-9]+))\)")
XID_TARGET_RE = re.compile(r"(?P<path>[A-Za-z0-9_.\-/]+\.md)#xid-(?P<xid>[A-Za-z0-9]+)")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def repository_identity(repo_root: Path) -> tuple[str, str]:
    """Return (fingerprint, basis) identifying the repository's content lineage.

    Basis preference:

    1. ``git_root_commits`` — the root commit(s) of HEAD's history. Every
       full clone of the same repository shares them regardless of path,
       host, or branch, so caches keyed by this fingerprint are shared
       across machines and survive checkout moves. Multiple roots (merged
       histories) are sorted and joined for determinism.
    2. ``resolved_repository_root`` — path fallback for non-git
       directories, repositories without commits, and shallow clones
       (whose grafted history would misreport the true root commit).
    """
    root_commits = _git_root_commits(repo_root)
    if root_commits:
        seed = "git-root-commits:" + ",".join(root_commits)
        return stable_hash(seed)[:32], "git_root_commits"
    normalized_root = repo_root.resolve().as_posix().casefold()
    seed = f"resolved-repository-root:{normalized_root}"
    return stable_hash(seed)[:32], "resolved_repository_root"


def repository_fingerprint(repo_root: Path) -> str:
    return repository_identity(repo_root)[0]


def _git_root_commits(repo_root: Path) -> list[str]:
    if _git_is_shallow(repo_root):
        return []
    output = _git_stdout(repo_root, ["rev-list", "--max-parents=0", "HEAD"])
    if output is None:
        return []
    return sorted(line.strip() for line in output.splitlines() if line.strip())


def _git_is_shallow(repo_root: Path) -> bool:
    output = _git_stdout(repo_root, ["rev-parse", "--is-shallow-repository"])
    return output is not None and output.strip() == "true"


def _git_stdout(repo_root: Path, arguments: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def first_xid(text: str) -> str | None:
    match = XID_RE.search(text)
    if not match:
        return None
    return match.group(1) or match.group(2)


def first_heading(text: str, fallback: str) -> str:
    match = HEADING_RE.search(text)
    return match.group(1).strip() if match else fallback


def first_paragraph(text: str) -> str:
    lines: list[str] = []
    in_heading = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("<!--") or line.startswith("<a "):
            continue
        if line.startswith("#"):
            in_heading = True
            continue
        if in_heading and not line.startswith(("-", "|", "```")):
            lines.append(line)
            if len(" ".join(lines)) > 220:
                break
        elif lines:
            break
    return " ".join(lines)[:500]


def markdown_xid_links(text: str) -> list[str]:
    return list(dict.fromkeys(match.group("xid") for match in MD_LINK_RE.finditer(text)))


def markdown_xid_link_targets(text: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in MD_LINK_RE.finditer(text):
        xid = match.group("xid")
        if xid in seen:
            continue
        seen.add(xid)
        links.append(
            {
                "xid": xid,
                "resolver_tool": "get_document_by_xid",
                "resolver_argument": "xid",
            }
        )
    return links


def markdown_xid_only_text(text: str) -> str:
    return XID_TARGET_RE.sub(lambda match: f"#xid-{match.group('xid')}", text)


def relative_to_repo(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def file_last_modified(path: Path) -> str | None:
    """UTC ISO timestamp of the file's last modification on this checkout.

    Derived from the filesystem, not from git history: catalog entries are
    rebuilt from the live repository inside MCP request handlers, and
    spawning a git subprocess there hangs the stdio transport on Windows
    (the tool result is computed but the response never reaches the
    client). revised_at is advisory metadata, so the checkout's mtime is an
    acceptable and subprocess-free source.
    """
    try:
        stat = path.stat()
    except OSError:
        return None
    return (
        datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        .isoformat(timespec="seconds")
    )


def parse_meta_bullets(text: str) -> dict[str, object]:
    result: dict[str, object] = {}
    current_key: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        top = re.match(r"^- ([A-Za-z0-9_\-]+):\s*(.*)$", line)
        if top:
            current_key = top.group(1)
            value = _clean_scalar(top.group(2))
            result[current_key] = value if value else []
            continue
        child = re.match(r"^\s+-\s+(.+)$", line)
        if child and current_key:
            existing = result.setdefault(current_key, [])
            if not isinstance(existing, list):
                existing = [existing]
                result[current_key] = existing
            existing.append(_clean_scalar(child.group(1)))
    return result


def _clean_scalar(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        value = value[1:-1]
    return value


def scalar_list(meta: dict[str, object], key: str) -> list[str]:
    value = meta.get(key)
    if isinstance(value, list):
        return [piece for item in value for piece in _split_scalar(str(item))]
    if isinstance(value, str) and value:
        return _split_scalar(value)
    return []


def _split_scalar(value: str) -> list[str]:
    if "," not in value:
        return [value] if value else []
    return [_clean_scalar(piece) for piece in value.split(",") if _clean_scalar(piece)]

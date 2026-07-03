"""Export the base-branch history as a portable manifest (run on the BASE side).

Walks every commit of the snapshot branch and records, per commit, the
XID-keyed document map (path, xid-normalized content hash, anchors) plus a
plain sha256 map for non-Markdown text files. Commits are stored as deltas
against the previous commit, so the manifest stays small.

The manifest is the "portable git history": the local side runs
xrefkit_sync_worklist.py against it with no git installed.

Usage (from the XRefKit repository root):

    python handoff/base_sync/export_base_manifest.py \
        --repo . \
        --branch origin/codex/sync-main-without-mp4-action \
        --out handoff/base_sync/base-history-manifest.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TEXT_EXTENSIONS = {
    ".md", ".py", ".yaml", ".yml", ".json", ".cs", ".csproj",
    ".ps1", ".txt", ".toml", ".gitignore",
}
# Identity comes only from DECLARATIONS (xid comment or anchor), never
# from link references like ...md#xid-XXXX, which merely point at another
# document and must not become this file's identity.
XID_DECLARATION_RE = re.compile(
    r"<!--\s*xid:\s*([A-Za-z0-9]{6,})\s*-->|<a id=\"xid-([A-Za-z0-9]{6,})\""
)
ANCHOR_RE = re.compile(r"<a id=\"xid-([A-Za-z0-9]+)\"|<!--\s*xid:\s*([A-Za-z0-9]+)")
XID_TARGET_RE = re.compile(r"(?P<path>[A-Za-z0-9_.\-/]+\.md)#xid-(?P<xid>[A-Za-z0-9]+)")


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True,
        check=True, encoding="utf-8", errors="replace",
    )
    return result.stdout


def git_bytes(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, check=True)
    return result.stdout


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def xid_normalized_hash(text: str) -> str:
    # Same convention as xrefkit_mcp content_hash: markdown links reduced to
    # bare #xid-... targets so renames of *referenced* files do not change
    # the hash. Line endings are normalized so CRLF working copies compare
    # equal to LF git blobs.
    content = XID_TARGET_RE.sub(lambda m: f"#xid-{m.group('xid')}", normalize(text))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def first_xid(text: str) -> str | None:
    match = XID_DECLARATION_RE.search(text)
    if not match:
        return None
    return match.group(1) or match.group(2)


def all_anchors(text: str) -> list[str]:
    seen: list[str] = []
    for match in ANCHOR_RE.finditer(text):
        xid = match.group(1) or match.group(2)
        if xid and xid not in seen:
            seen.append(xid)
    return seen


def describe_blob(repo: Path, blob: str, path: str) -> dict:
    raw = git_bytes(repo, "cat-file", "blob", blob)
    text = raw.decode("utf-8", errors="replace")
    if path.endswith(".md"):
        return {
            "kind": "doc",
            "xid": first_xid(text),
            "anchors": all_anchors(text),
            "hash": xid_normalized_hash(text),
        }
    return {
        "kind": "plain",
        "hash": hashlib.sha256(normalize(text).encode("utf-8")).hexdigest(),
    }


def list_tree(repo: Path, commit: str) -> dict[str, str]:
    files: dict[str, str] = {}
    for line in git(repo, "ls-tree", "-r", commit).splitlines():
        meta, path = line.split("\t", 1)
        _mode, kind, blob = meta.split()
        if kind != "blob":
            continue
        suffix = Path(path).suffix.lower() or Path(path).name
        if suffix in TEXT_EXTENSIONS or Path(path).name in TEXT_EXTENSIONS:
            files[path] = blob
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    log = git(repo, "log", "--reverse", "--format=%H %cI", args.branch)
    commits = [line.split(" ", 1) for line in log.splitlines() if line.strip()]

    blob_table: dict[str, dict] = {}
    commit_entries: list[dict] = []
    previous: dict[str, str] = {}
    for sha, date in commits:
        current = list_tree(repo, sha)
        changed = {
            path: blob for path, blob in current.items()
            if previous.get(path) != blob
        }
        removed = sorted(path for path in previous if path not in current)
        for path, blob in changed.items():
            if blob not in blob_table:
                blob_table[blob] = describe_blob(repo, blob, path)
        commit_entries.append(
            {"sha": sha, "date": date, "changed": changed, "removed": removed}
        )
        previous = current

    manifest = {
        "format": "xrefkit-base-history/1",
        "branch": args.branch,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "head": commits[-1][0] if commits else None,
        "commit_count": len(commits),
        "hash_convention": (
            "sha256 of CRLF-normalized text; .md additionally has markdown "
            "xid-link targets reduced to #xid-... before hashing "
            "(xrefkit_mcp content_hash compatible for LF files)"
        ),
        "commits": commit_entries,
        "blobs": blob_table,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    size_kb = out.stat().st_size // 1024
    print(f"manifest: {out} ({size_kb} KB, {len(commits)} commits, {len(blob_table)} blobs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

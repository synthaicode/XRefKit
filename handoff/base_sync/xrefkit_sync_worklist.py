"""Classify a locally-modified XRefKit copy against base history (LOCAL side).

Stdlib-only. Reads the portable history manifest produced by
export_base_manifest.py, content-dates the local copy (finds the base
commit it was copied from), then performs an XID-keyed 3-way comparison
(base@copy-point / base@head / local) and writes a machine-readable
worklist for the absorbing AI plus a human-readable summary.

This tool is READ-ONLY: it never modifies the local repository. All
absorption is performed by the AI following HANDOFF.md, one worklist item
at a time.

Usage:

    python xrefkit_sync_worklist.py \
        --manifest base-history-manifest.json \
        --local <path-to-local-copy> \
        --base-tree <path-to-unzipped-current-base> \
        --out-dir sync-report

Outputs in --out-dir:
    sync-worklist.json   items with kind / key / hashes / action hints
    sync-worklist.md     grouped summary
    diffs/*.diff         unified diffs for review-required items
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fm.ownership import Ownership, load_ownership, validate_ownership

TEXT_EXTENSIONS = {
    ".md", ".py", ".yaml", ".yml", ".json", ".cs", ".csproj",
    ".ps1", ".txt", ".toml", ".gitignore",
}
DEFAULT_EXCLUDED_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules",
    "bin", "obj", ".xref", "site", "work", ".tmp", "sync-report",
}
# Identity comes only from DECLARATIONS (xid comment or anchor), never
# from link references like ...md#xid-XXXX, which merely point at another
# document and must not become this file's identity.
XID_DECLARATION_RE = re.compile(
    r"<!--\s*xid:\s*([A-Za-z0-9]{6,})\s*-->|<a id=\"xid-([A-Za-z0-9]{6,})\""
)
ANCHOR_RE = re.compile(r"<a id=\"xid-([A-Za-z0-9]+)\"|<!--\s*xid:\s*([A-Za-z0-9]+)")
XID_TARGET_RE = re.compile(r"(?P<path>[A-Za-z0-9_.\-/]+\.md)#xid-(?P<xid>[A-Za-z0-9]+)")

# Translated mirrors (e.g. human-docs/ja/) legitimately declare the SAME
# XIDs as the canonical documents they translate. They must not compete for
# the XID key: they are keyed by path instead, and their anchors are
# ignored for absorbed-into resolution.
TRANSLATION_PREFIXES = ("human-docs/",)

REVIEW_REQUIRED_KINDS = {
    "both_changed",
    "base_deleted_local_modified",
    "local_deleted",
    "xid_collision",
}


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def xid_normalized_hash(text: str) -> str:
    content = XID_TARGET_RE.sub(lambda m: f"#xid-{m.group('xid')}", normalize(text))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def plain_hash(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


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


def doc_key(xid: str | None, path: str) -> str:
    if xid is None or path.startswith(TRANSLATION_PREFIXES):
        return f"path:{path}"
    return xid


def is_translation(path: str) -> bool:
    return path.startswith(TRANSLATION_PREFIXES)


def is_text_file(path: Path) -> bool:
    return (
        path.suffix.lower() in TEXT_EXTENSIONS
        or path.name in TEXT_EXTENSIONS
    )


class State:
    """docs: key -> {path, hash, anchors}; plain: path -> hash.

    Markdown documents are keyed by XID; markdown without an XID falls back
    to "path:<relative-path>" (same convention as XRefKit MCP).
    """

    def __init__(self) -> None:
        self.docs: dict[str, dict] = {}
        self.plain: dict[str, str] = {}

    def anchor_index(self) -> dict[str, str]:
        index: dict[str, str] = {}
        for key, doc in self.docs.items():
            if is_translation(doc["path"]):
                continue
            for anchor in doc.get("anchors", []):
                index.setdefault(anchor, key)
        return index


def _excluded(path: str, ownership: Ownership | None = None) -> bool:
    # Same exclusion set as the local scan, so manifest-side states and the
    # local state describe the same universe (otherwise every locally
    # excluded directory shows up as a false local_deleted).
    if any(part in DEFAULT_EXCLUDED_DIRS for part in Path(path).parts[:-1]):
        return True
    return False if ownership is None else not ownership.base_sync_enabled(path)


def state_from_files(
    files: dict[str, str],
    blobs: dict[str, dict],
    ownership: Ownership | None = None,
) -> State:
    state = State()
    for path, blob in files.items():
        if _excluded(path, ownership):
            continue
        info = blobs[blob]
        if info["kind"] == "doc":
            key = doc_key(info["xid"], path)
            state.docs[key] = {
                "path": path,
                "hash": info["hash"],
                "anchors": info.get("anchors", []),
            }
        else:
            state.plain[path] = info["hash"]
    return state


def replay_commits(manifest: dict) -> list[tuple[str, str, dict[str, str]]]:
    """Return [(sha, date, {path: blob})] for every commit."""
    snapshots: list[tuple[str, str, dict[str, str]]] = []
    current: dict[str, str] = {}
    for commit in manifest["commits"]:
        current = dict(current)
        current.update(commit["changed"])
        for path in commit["removed"]:
            current.pop(path, None)
        snapshots.append((commit["sha"], commit["date"], current))
    return snapshots


def scan_local(root: Path, ownership: Ownership | None = None) -> tuple[State, list[dict]]:
    state = State()
    problems: list[dict] = []
    seen_xids: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not is_text_file(path):
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in DEFAULT_EXCLUDED_DIRS for part in relative_parts[:-1]):
            continue
        rel = path.relative_to(root).as_posix()
        if ownership is not None and not ownership.base_sync_enabled(rel):
            continue
        text = path.read_bytes().decode("utf-8", errors="replace")
        if path.suffix.lower() == ".md":
            xid = first_xid(text)
            key = doc_key(xid, rel)
            if key == xid and xid in seen_xids:
                problems.append(
                    {
                        "kind": "xid_collision",
                        "key": xid,
                        "local_path": rel,
                        "conflicts_with": seen_xids[xid],
                        "requires": "human_review",
                    }
                )
                continue
            if key == xid and xid:
                seen_xids[xid] = rel
            state.docs[key] = {
                "path": rel,
                "hash": xid_normalized_hash(text),
                "anchors": all_anchors(text),
            }
        else:
            state.plain[rel] = plain_hash(text)
    return state, problems


def date_copy_point(
    local: State,
    snapshots: list[tuple[str, str, dict[str, str]]],
    blobs: dict[str, dict],
    ownership: Ownership | None = None,
) -> tuple[int, dict]:
    best_index = len(snapshots) - 1
    best_score = -1
    scores = []
    for index, (_sha, _date, files) in enumerate(snapshots):
        state = state_from_files(files, blobs, ownership)
        score = sum(
            1
            for key, doc in local.docs.items()
            if key in state.docs and state.docs[key]["hash"] == doc["hash"]
        )
        score += sum(
            1
            for path, digest in local.plain.items()
            if state.plain.get(path) == digest
        )
        scores.append(score)
        if score >= best_score:
            best_score = score
            best_index = index
    total = len(local.docs) + len(local.plain)
    detail = {
        "commit": snapshots[best_index][0],
        "date": snapshots[best_index][1],
        "matched": best_score,
        "local_total": total,
        "match_ratio": round(best_score / total, 4) if total else 0.0,
    }
    return best_index, detail


def classify_docs(local: State, copy: State, head: State) -> list[dict]:
    items: list[dict] = []
    head_anchors = head.anchor_index()
    keys = set(local.docs) | set(copy.docs) | set(head.docs)
    for key in sorted(keys):
        l = local.docs.get(key)
        c = copy.docs.get(key)
        h = head.docs.get(key)
        item: dict = {"key": key, "layer": "doc"}
        if l:
            item["local_path"] = l["path"]
        if h:
            item["head_path"] = h["path"]
        item["hashes"] = {
            "local": l["hash"] if l else None,
            "copy_point": c["hash"] if c else None,
            "head": h["hash"] if h else None,
        }

        if l and not c and not h:
            item["kind"] = (
                "no_xid_local_addition" if key.startswith("path:") else "local_addition"
            )
            item["action_hint"] = (
                "Intake as new: assign a new XID (no-XID files), place in the "
                "local pack, then update Skills that should reference it."
            )
        elif l and c and h:
            if l["hash"] == c["hash"] == h["hash"]:
                item["kind"] = "unchanged"
                item["action_hint"] = "No content action."
                if l["path"] != h["path"]:
                    item["kind"] = "moved_in_base"
                    item["action_hint"] = (
                        f"Same content; base moved it to {h['path']}. Optionally align the local path."
                    )
            elif l["hash"] == c["hash"]:
                item["kind"] = "base_only_advanced"
                item["action_hint"] = (
                    "Local never touched this document; adopt the base@head "
                    "version by copying it from --base-tree."
                )
            elif h["hash"] == c["hash"]:
                item["kind"] = "local_only_modified"
                item["fork_base_hash"] = c["hash"]
                item["action_hint"] = (
                    "Run the ladder: extract local facts to knowledge, "
                    "parameters to bindings; if pure procedure remains, "
                    "declare a fork (forked_from + fork_base_hash above)."
                )
            elif l["hash"] == h["hash"]:
                item["kind"] = "converged"
                item["action_hint"] = "Local and base made the same change. No action."
            else:
                item["kind"] = "both_changed"
                item["requires"] = "human_review"
                item["action_hint"] = (
                    "Do NOT merge automatically. Present the diffs to a human."
                )
        elif l and c and not h:
            if key in head_anchors:
                item["kind"] = "absorbed_into"
                item["absorbed_into"] = head_anchors[key]
                item["action_hint"] = (
                    f"Base merged this document into {head_anchors[key]}. "
                    "Repoint local references to the absorbing document; "
                    "review local edits against it if any."
                )
                if l["hash"] != c["hash"]:
                    item["requires"] = "human_review"
            elif l["hash"] == c["hash"]:
                item["kind"] = "base_deleted_local_unchanged"
                item["action_hint"] = "Base deleted it and local never changed it; delete locally."
            else:
                item["kind"] = "base_deleted_local_modified"
                item["requires"] = "human_review"
                item["action_hint"] = (
                    "Base deleted a document local had modified. A human "
                    "decides whether to keep it as a local-only document."
                )
        elif l and not c and h:
            if l["hash"] == h["hash"]:
                item["kind"] = "converged_addition"
                item["action_hint"] = "Local already matches a document base added later. No action."
            else:
                item["kind"] = "both_changed"
                item["requires"] = "human_review"
                item["action_hint"] = (
                    "Document appeared in base after the copy AND exists "
                    "locally with different content. Human review."
                )
        elif not l and c and h:
            item["kind"] = "local_deleted"
            item["requires"] = "human_review"
            item["action_hint"] = (
                "Local deleted a base document. Confirm the deletion was intentional."
            )
        elif not l and not c and h:
            item["kind"] = "base_new"
            item["action_hint"] = (
                "New base document since the copy; adopt it from --base-tree "
                "if the local materializes base content."
            )
        else:  # only at copy point
            item["kind"] = "mutually_deleted"
            item["action_hint"] = "Gone on both sides. No action."
        items.append(item)
    return items


def classify_plain(local: State, copy: State, head: State) -> list[dict]:
    items: list[dict] = []
    keys = set(local.plain) | set(copy.plain) | set(head.plain)
    for path in sorted(keys):
        l = local.plain.get(path)
        c = copy.plain.get(path)
        h = head.plain.get(path)
        item: dict = {
            "key": path,
            "layer": "plain",
            "local_path": path if l else None,
            "hashes": {"local": l, "copy_point": c, "head": h},
        }
        if l and not c and not h:
            item["kind"] = "local_addition"
            item["action_hint"] = "Local-only file; move into the local pack."
        elif l and c and h:
            if l == c == h:
                item["kind"] = "unchanged"
                item["action_hint"] = "No action."
            elif l == c:
                item["kind"] = "base_only_advanced"
                item["action_hint"] = "Adopt the base@head version from --base-tree."
            elif h == c:
                item["kind"] = "local_only_modified"
                item["fork_base_hash"] = c
                item["action_hint"] = "Local-only change; keep locally or declare a fork."
            elif l == h:
                item["kind"] = "converged"
                item["action_hint"] = "No action."
            else:
                item["kind"] = "both_changed"
                item["requires"] = "human_review"
                item["action_hint"] = "Do NOT merge automatically."
        elif l and c and not h:
            if l == c:
                item["kind"] = "base_deleted_local_unchanged"
                item["action_hint"] = "Delete locally."
            else:
                item["kind"] = "base_deleted_local_modified"
                item["requires"] = "human_review"
                item["action_hint"] = "Base deleted a file local modified. Human review."
        elif l and not c and h:
            item["kind"] = "converged_addition" if l == h else "both_changed"
            if item["kind"] == "both_changed":
                item["requires"] = "human_review"
            item["action_hint"] = "Check against base@head."
        elif not l and c and h:
            item["kind"] = "local_deleted"
            item["requires"] = "human_review"
            item["action_hint"] = "Confirm the local deletion was intentional."
        elif not l and not c and h:
            item["kind"] = "base_new"
            item["action_hint"] = "New base file since the copy."
        else:
            item["kind"] = "mutually_deleted"
            item["action_hint"] = "No action."
        items.append(item)
    return items


def write_diffs(
    items: list[dict],
    local_root: Path,
    base_tree: Path | None,
    out_dir: Path,
) -> None:
    if base_tree is None:
        return
    diff_dir = out_dir / "diffs"
    diff_dir.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(items):
        if item.get("kind") not in {"both_changed", "local_only_modified", "base_deleted_local_modified"}:
            continue
        local_path = item.get("local_path")
        base_path = item.get("head_path") or item.get("local_path") or item["key"]
        local_file = local_root / local_path if local_path else None
        base_file = base_tree / base_path
        local_lines = (
            normalize(local_file.read_bytes().decode("utf-8", errors="replace")).splitlines(keepends=True)
            if local_file and local_file.is_file()
            else []
        )
        base_lines = (
            normalize(base_file.read_bytes().decode("utf-8", errors="replace")).splitlines(keepends=True)
            if base_file.is_file()
            else []
        )
        if not local_lines and not base_lines:
            continue
        diff = difflib.unified_diff(
            base_lines, local_lines,
            fromfile=f"base/{base_path}", tofile=f"local/{local_path or item['key']}",
        )
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", item["key"])[:80]
        diff_path = diff_dir / f"{index:04d}_{item['kind']}_{safe}.diff"
        diff_path.write_text("".join(diff), encoding="utf-8")
        item["diff_file"] = diff_path.relative_to(out_dir).as_posix()


def summarize_markdown(worklist: dict) -> str:
    lines = ["# Sync Worklist Summary", ""]
    dating = worklist["copy_point"]
    lines.append(
        f"- copy point: `{dating['commit'][:12]}` ({dating['date']}), "
        f"matched {dating['matched']}/{dating['local_total']} "
        f"({dating['match_ratio']:.0%})"
    )
    lines.append(f"- manifest head: `{worklist['manifest_head'][:12]}`")
    counts: dict[str, int] = {}
    for item in worklist["items"]:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    lines.append("")
    lines.append("| kind | count |")
    lines.append("|---|---|")
    for kind, count in sorted(counts.items(), key=lambda pair: -pair[1]):
        lines.append(f"| {kind} | {count} |")
    lines.append("")
    review = [item for item in worklist["items"] if item.get("requires") == "human_review"]
    lines.append(f"## Human review required ({len(review)})")
    lines.append("")
    for item in review:
        lines.append(f"- `{item['key']}` — {item['kind']} ({item.get('diff_file', 'no diff')})")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--local", required=True)
    parser.add_argument("--base-tree", help="Unzipped current base branch tree (for diffs and adoption)")
    parser.add_argument("--out-dir", default="sync-report")
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    local_root = Path(args.local).resolve()
    base_tree = Path(args.base_tree).resolve() if args.base_tree else None
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ownership = load_ownership(local_root)
    ownership_errors = validate_ownership(local_root, ownership) if ownership else []
    if ownership_errors:
        for error in ownership_errors:
            print(f"ownership error: {error}", file=sys.stderr)
        return 2

    blobs = manifest["blobs"]
    snapshots = replay_commits(manifest)
    local_state, problems = scan_local(local_root, ownership)
    copy_index, dating = date_copy_point(local_state, snapshots, blobs, ownership)
    copy_state = state_from_files(snapshots[copy_index][2], blobs, ownership)
    head_state = state_from_files(snapshots[-1][2], blobs, ownership)

    items = problems + classify_docs(local_state, copy_state, head_state)
    items += classify_plain(local_state, copy_state, head_state)
    for index, item in enumerate(items):
        item["id"] = f"sync-{index:04d}"
        item.setdefault("status", "pending")
    write_diffs(items, local_root, base_tree, out_dir)

    worklist = {
        "format": "xrefkit-sync-worklist/1",
        "manifest_branch": manifest["branch"],
        "manifest_head": manifest["head"],
        "copy_point": dating,
        "local_root": str(local_root),
        "ownership": {
            "enabled": ownership is not None,
            "zones": ownership.to_dict()["zones"] if ownership else [],
        },
        "read_only_notice": (
            "This worklist was produced without modifying the local "
            "repository. Absorption is performed per item by the AI "
            "following HANDOFF.md; both_changed items must go to a human."
        ),
        "items": items,
    }
    (out_dir / "sync-worklist.json").write_text(
        json.dumps(worklist, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "sync-worklist.md").write_text(summarize_markdown(worklist), encoding="utf-8")
    print(f"worklist: {out_dir / 'sync-worklist.json'} ({len(items)} items)")
    print(f"summary:  {out_dir / 'sync-worklist.md'}")
    review_count = sum(1 for item in items if item.get("requires") == "human_review")
    print(f"human review required: {review_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

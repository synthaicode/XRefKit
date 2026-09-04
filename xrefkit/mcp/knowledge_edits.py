"""Project-local Knowledge additions for MCP consumers."""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .repository import first_xid

REGISTRY_RELATIVE = Path(".xrefkit") / "knowledge-edits.json"
CONTENT_RELATIVE = Path(".xrefkit") / "knowledge-edits"


def _safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-.")
    return value or "knowledge"


def _local_path(root: Path, relative: object) -> Path:
    candidate = (root / str(relative)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Knowledge edit path escapes repository root: {relative}") from exc
    return candidate


def registry_path(root: Path) -> Path:
    return root / REGISTRY_RELATIVE


def content_root(root: Path) -> Path:
    return root / CONTENT_RELATIVE


def load_registry(root: Path) -> dict[str, dict[str, Any]]:
    path = registry_path(root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"invalid Knowledge edit registry: {path}") from exc
    edits = data.get("edits", data) if isinstance(data, dict) else None
    if not isinstance(edits, dict):
        raise ValueError(f"invalid Knowledge edit registry entries: {path}")
    return {str(key): dict(value) for key, value in edits.items() if isinstance(value, dict)}


def _write_registry(root: Path, edits: dict[str, dict[str, Any]]) -> None:
    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": 1, "edits": edits}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def local_files(root: Path, *, active_only: bool = True) -> list[tuple[str, Path]]:
    result: list[tuple[str, Path]] = []
    for xid, record in load_registry(root).items():
        if active_only and record.get("active", True) is not True:
            continue
        path = _local_path(root, record.get("path", ""))
        if path.exists():
            result.append((xid, path))
    return result


def create_local_knowledge(
    root: Path,
    *,
    xid: str,
    content: str,
    filename: str | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", xid):
        raise ValueError("xid must contain only letters, digits, underscore, or hyphen")
    if first_xid(content) != xid:
        raise ValueError("content must declare the supplied XID in its first XID marker")
    if not content.strip():
        raise ValueError("Knowledge content must not be empty")
    edits = load_registry(root)
    if xid in edits and edits[xid].get("active", True) is True:
        raise ValueError(f"active local Knowledge already exists: {xid}")
    name = _safe_name(filename or xid)
    if not name.lower().endswith(".md"):
        name += ".md"
    target = content_root(root) / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = {
        "xid": xid,
        "active": True,
        "path": target.relative_to(root).as_posix(),
        "domain": domain or "local",
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "created_at": now,
        "updated_at": now,
        "source_kind": "local_new",
    }
    edits[xid] = record
    _write_registry(root, edits)
    return {**record, "created": True}


def list_local_knowledge(root: Path) -> list[dict[str, Any]]:
    result = []
    for xid, record in load_registry(root).items():
        item = dict(record)
        item["xid"] = xid
        item["active"] = record.get("active", True) is True
        item["exists"] = _local_path(root, record.get("path", "")).exists()
        result.append(item)
    return sorted(result, key=lambda item: str(item["xid"]))


def export_local_knowledge(root: Path, xid: str, *, write_patch: bool = False) -> dict[str, Any]:
    record = load_registry(root).get(xid)
    if not record or record.get("active", True) is not True:
        raise KeyError(f"active local Knowledge not found: {xid}")
    target = _local_path(root, record["path"])
    content = target.read_text(encoding="utf-8") if target.exists() else ""
    patch = "".join(
        difflib.unified_diff(
            [],
            content.splitlines(keepends=True),
            fromfile="/dev/null",
            tofile=f"knowledge/{target.name}",
        )
    )
    patch_path = None
    if write_patch:
        path = root / "work" / "mcp" / "knowledge-edits" / f"{datetime.now(timezone.utc):%Y-%m-%d}_{_safe_name(xid)}.patch"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(patch, encoding="utf-8")
        patch_path = path.relative_to(root).as_posix()
    return {
        "xid": xid,
        "path": record["path"],
        "changed": bool(content),
        "patch": patch,
        "patch_path": patch_path,
        "next_step": "add this new Knowledge document to the upstream repository, preserve its XID, verify MCP distribution, then deactivate the local addition",
    }


def deactivate_local_knowledge(root: Path, xid: str) -> dict[str, Any]:
    edits = load_registry(root)
    if xid not in edits:
        raise KeyError(f"local Knowledge not found: {xid}")
    edits[xid] = {
        **edits[xid],
        "active": False,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _write_registry(root, edits)
    return {"xid": xid, "active": False, "file_preserved": True}

"""Project-local Skill edit overlays for MCP consumers.

The MCP catalog normally exposes repository and installed-package Skills as
read-only content.  This module gives a project an explicit, durable overlay
for a Skill that needs local improvements while preserving the original XIDs
and enough provenance to prepare an upstream patch later.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REGISTRY_RELATIVE = Path(".xrefkit") / "skill-edits.json"
OVERLAY_RELATIVE = Path(".xrefkit") / "skill-edits"


def _safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-.")
    return value or "skill"


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def registry_path(root: Path) -> Path:
    return root / REGISTRY_RELATIVE


def overlay_path(root: Path, skill_id: str) -> Path:
    return root / OVERLAY_RELATIVE / _safe_name(skill_id)


def _local_path(root: Path, relative: object) -> Path:
    """Resolve registry paths without allowing an edit record to escape root."""
    candidate = (root / str(relative)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Skill edit path escapes repository root: {relative}") from exc
    return candidate


def load_registry(root: Path) -> dict[str, dict[str, Any]]:
    path = registry_path(root)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"invalid Skill edit registry: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"invalid Skill edit registry root: {path}")
    edits = data.get("edits", data)
    if not isinstance(edits, dict):
        raise ValueError(f"invalid Skill edit registry entries: {path}")
    return {str(key): dict(value) for key, value in edits.items() if isinstance(value, dict)}


def _write_registry(root: Path, edits: dict[str, dict[str, Any]]) -> None:
    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "edits": edits}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def active_edit(root: Path, skill_id: str) -> dict[str, Any] | None:
    record = load_registry(root).get(skill_id)
    if not record or record.get("active", True) is not True:
        return None
    meta = _local_path(root, record.get("overlay_meta_path", ""))
    skill = _local_path(root, record.get("overlay_skill_path", ""))
    if not meta.exists() or not skill.exists():
        return None
    return record


def list_edits(root: Path) -> list[dict[str, Any]]:
    result = []
    for skill_id, record in load_registry(root).items():
        item = dict(record)
        item["skill_id"] = skill_id
        item["active"] = record.get("active", True) is True
        item["overlay_exists"] = bool(
            _local_path(root, record.get("overlay_meta_path", "")).exists()
            and _local_path(root, record.get("overlay_skill_path", "")).exists()
        )
        result.append(item)
    return sorted(result, key=lambda item: str(item["skill_id"]))


def prepare_edit(root: Path, entry: Any) -> dict[str, Any]:
    """Copy one resolved catalog entry into a project-local editable overlay."""
    source_root = Path(entry.source_root) if entry.source_root else root
    source_meta = source_root / entry.meta_path
    source_skill = source_root / entry.path
    if not source_meta.exists() or not source_skill.exists():
        raise FileNotFoundError(f"Skill source files were not found for {entry.skill_id}")

    target = overlay_path(root, entry.skill_id)
    target.mkdir(parents=True, exist_ok=True)
    target_meta = target / "meta.md"
    target_skill = target / "SKILL.md"
    # Do not overwrite an existing edit.  This is the protection that makes a
    # later prepare call safe after the user has started local work.
    if not target_meta.exists():
        target_meta.write_text(source_meta.read_text(encoding="utf-8"), encoding="utf-8")
    if not target_skill.exists():
        target_skill.write_text(source_skill.read_text(encoding="utf-8"), encoding="utf-8")

    edits = load_registry(root)
    previous = edits.get(entry.skill_id, {})
    record = {
        **previous,
        "skill_id": entry.skill_id,
        "active": True,
        "source_kind": "package" if entry.package_id else "repository",
        "source_package_id": entry.package_id,
        "source_root": str(source_root),
        "source_meta_path": entry.meta_path,
        "source_skill_path": entry.path,
        "source_meta_hash": stable_hash(source_meta.read_text(encoding="utf-8")),
        "source_skill_hash": stable_hash(source_skill.read_text(encoding="utf-8")),
        "overlay_meta_path": target_meta.relative_to(root).as_posix(),
        "overlay_skill_path": target_skill.relative_to(root).as_posix(),
        "created_at": previous.get("created_at") or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    edits[entry.skill_id] = record
    _write_registry(root, edits)
    return {
        **record,
        "overlay_meta_hash": stable_hash(target_meta.read_text(encoding="utf-8")),
        "overlay_skill_hash": stable_hash(target_skill.read_text(encoding="utf-8")),
        "created": not bool(previous),
    }


def overlay_files(root: Path, record: dict[str, Any]) -> list[Path]:
    return [
        _local_path(root, record["overlay_meta_path"]),
        _local_path(root, record["overlay_skill_path"]),
    ]


def export_edit(root: Path, record: dict[str, Any], *, write_patch: bool = False) -> dict[str, Any]:
    """Return an upstream-ready diff and optionally save it under ``work/mcp``."""
    target_files = overlay_files(root, record)
    source_root = Path(str(record.get("source_root") or root))
    source_files = [source_root / str(record["source_meta_path"]), source_root / str(record["source_skill_path"])]
    chunks: list[str] = []
    changed_files: list[str] = []
    for index, (source, target) in enumerate(zip(source_files, target_files, strict=True)):
        source_text = source.read_text(encoding="utf-8") if source.exists() else ""
        target_text = target.read_text(encoding="utf-8") if target.exists() else ""
        if source_text == target_text:
            continue
        changed_files.append(str(target.relative_to(root)).replace("\\", "/"))
        chunks.extend(
            difflib.unified_diff(
                source_text.splitlines(keepends=True),
                target_text.splitlines(keepends=True),
                # Keep machine-local absolute paths out of an upstream patch.
                fromfile=(
                    f"{record.get('source_kind', 'source')}:{record.get('source_package_id') or ''}/"
                    f"{str(record.get(('source_meta_path', 'source_skill_path')[index], '')).replace(chr(92), '/') }"
                ),
                tofile=str(target.relative_to(root)).replace("\\", "/"),
            )
        )
    patch = "".join(chunks)
    patch_path: str | None = None
    if write_patch:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = root / "work" / "mcp" / "skill-edits" / f"{stamp}_{_safe_name(record['skill_id'])}.patch"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(patch, encoding="utf-8")
        patch_path = path.relative_to(root).as_posix()
    return {
        "skill_id": record["skill_id"],
        "source_kind": record.get("source_kind"),
        "source_package_id": record.get("source_package_id"),
        "source_meta_path": record.get("source_meta_path"),
        "source_skill_path": record.get("source_skill_path"),
        "changed": bool(changed_files),
        "changed_files": changed_files,
        "patch": patch,
        "patch_path": patch_path,
        "next_step": "review and apply this patch in the upstream repository, then verify MCP distribution before deactivating the local edit",
    }


def deactivate_edit(root: Path, skill_id: str) -> dict[str, Any]:
    edits = load_registry(root)
    if skill_id not in edits:
        raise KeyError(f"local Skill edit not found: {skill_id}")
    edits[skill_id] = {**edits[skill_id], "active": False, "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    _write_registry(root, edits)
    return {"skill_id": skill_id, "active": False, "overlay_preserved": True}

"""Inert MCP inbox for locally authored Knowledge and deterministic tools."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .audit import SessionRunBinding, _process_lock
from .repository import first_xid

SCHEMA = "xrefkit.contribution_return/v1"
STORE_RELATIVE = Path(".xrefkit") / "contribution-returns"
ALLOWED_KINDS = {"knowledge", "deterministic_tool"}
MAX_FILES = 64
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 5 * 1024 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}")


def contribution_return_contract() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "status": "pending_review",
        "allowed_kinds": sorted(ALLOWED_KINDS),
        "hash_algorithm": "sha256",
        "limits": {
            "max_files": MAX_FILES,
            "max_file_bytes": MAX_FILE_BYTES,
            "max_total_bytes": MAX_TOTAL_BYTES,
        },
        "file_schema": {
            "path": "safe relative POSIX path",
            "content": "UTF-8 text",
            "content_hash": "lowercase SHA-256 hex of UTF-8 content",
        },
        "knowledge_schema": {"xid": "string", "files": "exactly one Markdown file"},
        "deterministic_tool_schema": {
            "runtime": "non-empty string",
            "entrypoint": "path of a submitted file",
            "input_contract": "object",
            "output_contract": "object",
            "verification_evidence": "non-empty array of {kind, command, result, content_hash?}",
        },
        "source_schema": {
            "skill_content_hash": "current selected Skill SHA-256",
            "knowledge_versions": "array of {xid, content_hash} actually used",
            "package_id": "optional package identity used to disambiguate the Skill",
        },
        "ordering": [
            "get_startup_context",
            "get_skill or get_skill_requirements",
            "bind_skill_run",
            "get_contribution_return_contract",
            "submit_contribution_return",
            "list_contribution_returns or export_contribution_return",
        ],
        "activation": "never automatic; export is an inert review bundle",
    }


def submit_contribution_return(
    root: Path,
    *,
    binding: SessionRunBinding,
    source_snapshot: dict[str, Any],
    contribution_id: str,
    kind: str,
    title: str,
    summary: str,
    files: list[dict[str, Any]],
    knowledge: dict[str, Any] | None = None,
    deterministic_tool: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_id = _uuid(contribution_id)
    normalized_files = _validate_files(files)
    normalized_kind = str(kind).strip()
    if normalized_kind not in ALLOWED_KINDS:
        raise ValueError(f"unsupported contribution kind: {kind}")
    normalized_title = _required_text(title, "title")
    normalized_summary = _required_text(summary, "summary")
    kind_metadata = _validate_kind_metadata(
        normalized_kind, normalized_files, knowledge, deterministic_tool
    )
    payload = {
        "contribution_id": normalized_id,
        "kind": normalized_kind,
        "title": normalized_title,
        "summary": normalized_summary,
        "files": normalized_files,
        "kind_metadata": kind_metadata,
        "source": source_snapshot,
        "binding": binding.to_dict(),
    }
    payload_hash = _canonical_hash(payload)
    store = root.resolve() / STORE_RELATIVE
    store.mkdir(parents=True, exist_ok=True)
    final_dir = store / normalized_id
    lock_path = store / "inbox"
    with _process_lock(lock_path):
        if final_dir.exists():
            return _existing_result(final_dir, payload_hash)
        temp_dir = store / f".{normalized_id}.{uuid.uuid4().hex}.tmp"
        try:
            temp_dir.mkdir()
            content_dir = temp_dir / "files"
            content_dir.mkdir()
            for item in normalized_files:
                target = content_dir.joinpath(*PurePosixPath(item["path"]).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                _write_fsynced(target, item["content"])
            manifest = {
                "schema": SCHEMA,
                "contribution_id": normalized_id,
                "status": "pending_review",
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "payload_hash": payload_hash,
                "kind": normalized_kind,
                "title": normalized_title,
                "summary": normalized_summary,
                "files": [
                    {key: item[key] for key in ("path", "content_hash", "byte_count")}
                    for item in normalized_files
                ],
                "kind_metadata": kind_metadata,
                "source": source_snapshot,
                "binding": binding.to_dict(),
                "limits_version": 1,
            }
            _write_fsynced(
                temp_dir / "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
            os.replace(temp_dir, final_dir)
        except Exception:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if final_dir.exists():
                return _existing_result(final_dir, payload_hash)
            raise
    return {**manifest, "created": True, "idempotent_replay": False}


def list_contribution_returns(root: Path) -> list[dict[str, Any]]:
    store = root.resolve() / STORE_RELATIVE
    if not store.exists():
        return []
    result = []
    for path in sorted(store.iterdir()):
        if not path.is_dir() or path.name.startswith("."):
            continue
        manifest_path = path / "manifest.json"
        if manifest_path.is_file():
            result.append(_read_manifest(manifest_path))
    return result


def export_contribution_return(root: Path, contribution_id: str) -> dict[str, Any]:
    normalized_id = _uuid(contribution_id)
    record_dir = root.resolve() / STORE_RELATIVE / normalized_id
    manifest = _read_manifest(record_dir / "manifest.json")
    exported_files = []
    for item in manifest["files"]:
        content = (record_dir / "files").joinpath(*PurePosixPath(item["path"]).parts).read_text(
            encoding="utf-8"
        )
        if _sha256(content) != item["content_hash"]:
            raise ValueError(f"stored contribution file hash mismatch: {item['path']}")
        exported_files.append({**item, "content": content})
    return {
        "schema": SCHEMA,
        "review_bundle": {**manifest, "files": exported_files},
        "activation_performed": False,
        "next_step": "review and adopt through the receiving repository's governed process",
    }


def _validate_files(files: object) -> list[dict[str, Any]]:
    if not isinstance(files, list) or not files:
        raise ValueError("files must be a non-empty array")
    if len(files) > MAX_FILES:
        raise ValueError(f"file count exceeds limit {MAX_FILES}")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    total = 0
    for raw in files:
        if not isinstance(raw, dict):
            raise ValueError("each file must be an object")
        path = _safe_path(raw.get("path"))
        if path in seen:
            raise ValueError(f"duplicate contribution path: {path}")
        seen.add(path)
        content = raw.get("content")
        if not isinstance(content, str):
            raise ValueError(f"file content must be UTF-8 text: {path}")
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_FILE_BYTES:
            raise ValueError(f"file exceeds byte limit: {path}")
        total += len(encoded)
        supplied_hash = str(raw.get("content_hash", ""))
        if not SHA256_RE.fullmatch(supplied_hash) or supplied_hash != hashlib.sha256(encoded).hexdigest():
            raise ValueError(f"content_hash mismatch: {path}")
        result.append({
            "path": path,
            "content": content,
            "content_hash": supplied_hash,
            "byte_count": len(encoded),
        })
    if total > MAX_TOTAL_BYTES:
        raise ValueError(f"total contribution bytes exceed limit {MAX_TOTAL_BYTES}")
    return sorted(result, key=lambda item: item["path"])


def _validate_kind_metadata(
    kind: str,
    files: list[dict[str, Any]],
    knowledge: dict[str, Any] | None,
    deterministic_tool: dict[str, Any] | None,
) -> dict[str, Any]:
    if kind == "knowledge":
        if deterministic_tool is not None or not isinstance(knowledge, dict):
            raise ValueError("knowledge metadata is required only for knowledge contributions")
        if len(files) != 1 or not files[0]["path"].lower().endswith(".md"):
            raise ValueError("Knowledge contribution requires exactly one Markdown file")
        xid = _required_text(knowledge.get("xid"), "knowledge.xid")
        if first_xid(files[0]["content"]) != xid:
            raise ValueError("Knowledge XID must match the first XID marker")
        return {"xid": xid}
    if knowledge is not None or not isinstance(deterministic_tool, dict):
        raise ValueError("deterministic_tool metadata is required only for deterministic_tool contributions")
    runtime = _required_text(deterministic_tool.get("runtime"), "deterministic_tool.runtime")
    entrypoint = _safe_path(deterministic_tool.get("entrypoint"))
    if entrypoint not in {item["path"] for item in files}:
        raise ValueError("deterministic_tool.entrypoint must name a submitted file")
    input_contract = deterministic_tool.get("input_contract")
    output_contract = deterministic_tool.get("output_contract")
    if not isinstance(input_contract, dict) or not isinstance(output_contract, dict):
        raise ValueError("deterministic tool input_contract and output_contract must be objects")
    evidence = deterministic_tool.get("verification_evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("deterministic tool verification_evidence must be non-empty")
    normalized_evidence = []
    for row in evidence:
        if not isinstance(row, dict):
            raise ValueError("verification evidence rows must be objects")
        item = {
            "kind": _required_text(row.get("kind"), "verification_evidence.kind"),
            "command": _required_text(row.get("command"), "verification_evidence.command"),
            "result": _required_text(row.get("result"), "verification_evidence.result"),
        }
        if row.get("content_hash") is not None:
            value = str(row["content_hash"])
            if not SHA256_RE.fullmatch(value):
                raise ValueError("verification evidence content_hash must be lowercase SHA-256")
            item["content_hash"] = value
        normalized_evidence.append(item)
    return {
        "runtime": runtime,
        "entrypoint": entrypoint,
        "input_contract": input_contract,
        "output_contract": output_contract,
        "verification_evidence": normalized_evidence,
    }


def _safe_path(value: object) -> str:
    raw = str(value or "")
    if not raw or "\\" in raw or "\0" in raw or re.match(r"^[A-Za-z]:", raw):
        raise ValueError(f"unsafe contribution path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe contribution path: {raw!r}")
    normalized = path.as_posix()
    if normalized != raw:
        raise ValueError(f"contribution path must be normalized POSIX form: {raw!r}")
    return normalized


def _required_text(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text


def _uuid(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except ValueError as exc:
        raise ValueError(f"contribution_id must be a UUID: {value}") from exc


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_fsynced(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise KeyError(f"contribution return not found: {path.parent.name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"invalid contribution return manifest: {path}")
    return data


def _existing_result(final_dir: Path, payload_hash: str) -> dict[str, Any]:
    manifest = _read_manifest(final_dir / "manifest.json")
    if manifest.get("payload_hash") != payload_hash:
        raise ValueError("contribution_id already exists with a different payload")
    return {**manifest, "created": False, "idempotent_replay": True}

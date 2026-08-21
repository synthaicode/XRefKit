from __future__ import annotations

import json
import os
import threading
import uuid
import weakref
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if os.name == "nt":
    import msvcrt
else:
    import fcntl


AUDIT_SCHEMA = "xrefkit.mcp_audit/v1"


def _write_all(fd: int, data: bytes, *, write=None) -> None:
    writer = write or os.write
    offset = 0
    while offset < len(data):
        written = writer(fd, data[offset:])
        if written <= 0:
            raise OSError("audit log write did not make progress")
        offset += written


@contextmanager
def _process_lock(path: Path):
    lock_path = path.with_suffix(path.suffix + ".lock")
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    locked = False
    try:
        if os.name == "nt":
            if os.fstat(fd).st_size == 0:
                _write_all(fd, b"\0")
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_EX)
        locked = True
        yield
    finally:
        if locked:
            if os.name == "nt":
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


@dataclass(frozen=True)
class SessionRunBinding:
    run_id: str
    mcp_session_id: str
    repository_fingerprint: str
    skill_id: str
    flow_id: str | None = None
    root_run_id: str | None = None
    parent_run_id: str | None = None
    work_item_id: str | None = None
    node_id: str | None = None

    def to_dict(self) -> dict[str, str]:
        result = {
            "run_id": self.run_id,
            "mcp_session_id": self.mcp_session_id,
            "repository_fingerprint": self.repository_fingerprint,
            "skill_id": self.skill_id,
        }
        for key in ("flow_id", "root_run_id", "parent_run_id", "work_item_id", "node_id"):
            value = getattr(self, key)
            if value:
                result[key] = value
        return result


class SessionRunRegistry:
    def __init__(self) -> None:
        self._bindings: "weakref.WeakKeyDictionary[Any, SessionRunBinding]" = weakref.WeakKeyDictionary()
        self._lock = threading.RLock()

    def bind(
        self,
        session: Any,
        *,
        run_id: str,
        repository_fingerprint: str,
        skill_id: str,
        flow_id: str | None = None,
        root_run_id: str | None = None,
        parent_run_id: str | None = None,
        work_item_id: str | None = None,
        node_id: str | None = None,
    ) -> SessionRunBinding:
        if session is None:
            raise ValueError("MCP session is required for Skill Run binding")
        try:
            normalized_run_id = str(uuid.UUID(str(run_id)))
        except ValueError as exc:
            raise ValueError(f"run_id must be a UUID: {run_id}") from exc
        normalized_skill_id = str(skill_id).strip()
        normalized_fingerprint = str(repository_fingerprint).strip()
        if not normalized_skill_id:
            raise ValueError("skill_id is required")
        if not normalized_fingerprint:
            raise ValueError("repository_fingerprint is required")
        normalized_flow_id = str(flow_id).strip() if flow_id else None
        normalized_root_run_id = _optional_uuid(root_run_id, "root_run_id")
        normalized_parent_run_id = _optional_uuid(parent_run_id, "parent_run_id")
        normalized_work_item_id = str(work_item_id).strip() if work_item_id else None
        normalized_node_id = str(node_id).strip() if node_id else None
        with self._lock:
            current = self._bindings.get(session)
            if current is not None:
                requested = (
                    normalized_run_id, normalized_fingerprint, normalized_skill_id,
                    normalized_flow_id, normalized_root_run_id, normalized_parent_run_id,
                    normalized_work_item_id, normalized_node_id,
                )
                existing = (
                    current.run_id, current.repository_fingerprint, current.skill_id,
                    current.flow_id, current.root_run_id, current.parent_run_id,
                    current.work_item_id, current.node_id,
                )
                if requested != existing:
                    raise ValueError(
                        "MCP session is already bound to a different Skill Run; end the current run before binding another"
                    )
                return current
            mcp_session_id = current.mcp_session_id if current else str(uuid.uuid4())
            binding = SessionRunBinding(
                run_id=normalized_run_id,
                mcp_session_id=mcp_session_id,
                repository_fingerprint=normalized_fingerprint,
                skill_id=normalized_skill_id,
                flow_id=normalized_flow_id,
                root_run_id=normalized_root_run_id,
                parent_run_id=normalized_parent_run_id,
                work_item_id=normalized_work_item_id,
                node_id=normalized_node_id,
            )
            self._bindings[session] = binding
            return binding

    def end(self, session: Any, *, run_id: str) -> SessionRunBinding:
        if session is None:
            raise ValueError("MCP session is required for Skill Run end")
        try:
            normalized_run_id = str(uuid.UUID(str(run_id)))
        except ValueError as exc:
            raise ValueError(f"run_id must be a UUID: {run_id}") from exc
        with self._lock:
            current = self._bindings.get(session)
            if current is None:
                raise ValueError("MCP session has no active Skill Run binding")
            if current.run_id != normalized_run_id:
                raise ValueError("run_id does not match the active MCP Skill Run binding")
            del self._bindings[session]
            return current

    def current(self, session: Any) -> SessionRunBinding | None:
        if session is None:
            return None
        with self._lock:
            return self._bindings.get(session)


def _optional_uuid(value: str | None, field: str) -> str | None:
    if value is None or not str(value).strip():
        return None
    try:
        return str(uuid.UUID(str(value)))
    except ValueError as exc:
        raise ValueError(f"{field} must be a UUID: {value}") from exc


class McpAuditLog:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self._lock = threading.Lock()

    def append(self, event_type: str, *, binding: SessionRunBinding, **fields: object) -> dict[str, object]:
        payload: dict[str, object] = {
            **fields,
            "schema": AUDIT_SCHEMA,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": str(event_type),
            **binding.to_dict(),
        }
        line = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        with self._lock:
            with _process_lock(self.path):
                fd = os.open(self.path, flags, 0o600)
                try:
                    _write_all(fd, line)
                    os.fsync(fd)
                finally:
                    os.close(fd)
        return payload

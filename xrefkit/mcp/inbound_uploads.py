"""MCP-owned inbound WebDAV staging for inert contribution payloads."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import stat
import time
import urllib.parse
import uuid
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from .audit import SessionRunBinding, _process_lock
from .contribution_returns import MAX_FILE_BYTES, MAX_FILES, MAX_PATH_BYTES, MAX_TOTAL_BYTES


UPLOAD_STORE = Path(".xrefkit") / "inbound-uploads"
UPLOAD_ROUTE = "/webdav/uploads"
UPLOAD_SCHEMA = "xrefkit.contribution_upload/v1"
SEAL_SCHEMA = "xrefkit.contribution_upload_seal/v1"
MIN_TTL_SECONDS = 30
MAX_TTL_SECONDS = 3600
DEFAULT_TTL_SECONDS = 900
MAX_ACTIVE_SESSIONS_PER_BINDING = 8
MAX_GLOBAL_ACTIVE_SESSIONS = 128
MAX_ACTIVE_RESERVATIONS_PER_SESSION = 4
MAX_GLOBAL_ACTIVE_RESERVATIONS = 64
MAX_GLOBAL_STAGING_BYTES = 64 * 1024 * 1024
MIN_FREE_DISK_BYTES = 16 * 1024 * 1024
MAX_PATH_DEPTH = 16
MAX_COLLECTIONS = 64
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


class UploadError(ValueError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class InboundUploadManager:
    """Own short-lived upload sessions and freeze them before MCP ingestion."""

    def __init__(
        self,
        root: Path,
        *,
        public_base_url: str,
        listener: dict[str, Any],
        default_ttl_seconds: int = DEFAULT_TTL_SECONDS,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.root = root.resolve()
        self.store = self.root / UPLOAD_STORE
        self.public_base_url = _base_url(public_base_url)
        self.listener = dict(listener)
        self.default_ttl_seconds = _ttl(default_ttl_seconds)
        self.clock = clock

    def issue(
        self,
        *,
        binding: SessionRunBinding,
        expires_in_seconds: int | None = None,
    ) -> dict[str, Any]:
        ttl = _ttl(self.default_ttl_seconds if expires_in_seconds is None else expires_in_seconds)
        now = int(self.clock())
        self.store.mkdir(parents=True, exist_ok=True)
        with _process_lock(self.store / "quota"):
            self._cleanup_expired_locked(now)
            active = 0
            global_active = 0
            for path in self.store.glob("*/session.json"):
                row = _read_json(path)
                if (
                    row.get("status") == "open"
                    and int(row.get("expires_at_epoch", 0)) >= now
                ):
                    global_active += 1
                    if row.get("binding") == binding.to_dict():
                        active += 1
            if active >= MAX_ACTIVE_SESSIONS_PER_BINDING:
                raise UploadError("active upload session quota exceeded", 429)
            if global_active >= MAX_GLOBAL_ACTIVE_SESSIONS:
                raise UploadError("global active upload session quota exceeded", 429)
            if _store_bytes(self.store) + _reserved_bytes(self.store) >= MAX_GLOBAL_STAGING_BYTES:
                raise UploadError("global upload staging-byte quota exceeded", 507)
            if shutil.disk_usage(self.store).free < MIN_FREE_DISK_BYTES:
                raise UploadError("insufficient free space for upload staging", 507)
            upload_id = str(uuid.uuid4())
            token = secrets.token_urlsafe(32)
            session_dir = self.store / upload_id
            session_dir.mkdir()
            (session_dir / "files").mkdir()
            session = {
                "schema": UPLOAD_SCHEMA,
                "upload_id": upload_id,
                "status": "open",
                "issued_at": _iso(now),
                "expires_at": _iso(now + ttl),
                "expires_at_epoch": now + ttl,
                "token_hash": _sha256_bytes(token.encode("utf-8")),
                "binding": binding.to_dict(),
                "limits": {
                    "max_files": MAX_FILES,
                    "max_file_bytes": MAX_FILE_BYTES,
                    "max_total_bytes": MAX_TOTAL_BYTES,
                    "max_path_bytes": MAX_PATH_BYTES,
                    "max_path_depth": MAX_PATH_DEPTH,
                    "max_collections": MAX_COLLECTIONS,
                    "max_active_puts": MAX_ACTIVE_RESERVATIONS_PER_SESSION,
                },
            }
            _atomic_json(session_dir / "session.json", session)
        return {
            "schema": UPLOAD_SCHEMA,
            "upload_id": upload_id,
            "status": "open",
            "webdav_url": f"{self.public_base_url}{UPLOAD_ROUTE}/{upload_id}",
            "bearer_token": token,
            "expires_at": session["expires_at"],
            "allowed_methods": ["OPTIONS", "MKCOL", "PUT", "HEAD", "PROPFIND"],
            "authorization": "Bearer token; token is returned once and is not part of the URL",
            "limits": session["limits"],
            "listener": self.listener,
        }

    def authorize(self, upload_id: str, authorization: str | None) -> tuple[Path, dict[str, Any]]:
        session_dir, session = self._session(upload_id)
        token = ""
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]
        expected = str(session.get("token_hash") or "")
        supplied = _sha256_bytes(token.encode("utf-8")) if token else ""
        if not expected or not supplied or not hmac.compare_digest(expected, supplied):
            raise UploadError("invalid upload authorization", 401)
        self._require_open(session_dir, session)
        return session_dir, session

    def make_collection(self, upload_id: str, rel_path: str, authorization: str | None) -> None:
        session_dir, _session = self.authorize(upload_id, authorization)
        rel = _safe_relpath(rel_path, allow_empty=False)
        # Upload mutation and sealing share one lock so the frozen tree is an
        # exact point-in-time snapshot; a PUT/MKCOL cannot cross the seal.
        with _process_lock(self.store / "quota"), _process_lock(session_dir / "state"):
            session = _read_json(session_dir / "session.json")
            self._require_open(session_dir, session)
            files_root = session_dir / "files"
            target = _contained(files_root, rel)
            _assert_safe_chain(files_root, target.parent)
            if not target.parent.is_dir():
                raise UploadError("parent collection does not exist", 409)
            if target.exists():
                raise UploadError("collection already exists", 405)
            directories = [row for row in _tree(files_root) if row["kind"] == "directory"]
            if len(directories) >= MAX_COLLECTIONS:
                raise UploadError("upload collection-count quota exceeded", 413)
            target.mkdir()

    def begin_put(self, upload_id: str, rel_path: str, authorization: str | None) -> tuple[Path, Path, dict[str, Any]]:
        session_dir, session = self.authorize(upload_id, authorization)
        rel = _safe_relpath(rel_path, allow_empty=False)
        reservation_id = uuid.uuid4().hex
        with _process_lock(self.store / "quota"):
            self._cleanup_expired_locked(int(self.clock()))
            reservations = _reservation_rows(self.store)
            if len(reservations) >= MAX_GLOBAL_ACTIVE_RESERVATIONS:
                raise UploadError("global active upload reservation quota exceeded", 429)
            if sum(row.get("upload_id") == upload_id for row in reservations) >= MAX_ACTIVE_RESERVATIONS_PER_SESSION:
                raise UploadError("active upload reservation quota exceeded", 429)
            with _process_lock(session_dir / "state"):
                session = _read_json(session_dir / "session.json")
                self._require_open(session_dir, session)
                incoming = session_dir / ".incoming"
                incoming.mkdir(exist_ok=True)
                _assert_safe_chain(session_dir, incoming)
                temp = incoming / f"{reservation_id}.tmp"
                reservation = {
                    "reservation_id": reservation_id,
                    "upload_id": upload_id,
                    "byte_count": 0,
                    "expires_at_epoch": session["expires_at_epoch"],
                }
                _atomic_json(self._reservation_path(reservation_id), reservation)
        return session_dir, temp, {"relative": rel, "reservation_id": reservation_id}

    def reserve_chunk(self, reservation_id: str, byte_count: int) -> None:
        if byte_count < 0:
            raise UploadError("invalid upload reservation size")
        with _process_lock(self.store / "quota"):
            self._cleanup_expired_locked(int(self.clock()))
            path = self._reservation_path(reservation_id)
            reservation = _read_json(path)
            reserved = _reserved_bytes(self.store)
            if _store_bytes(self.store) + reserved + byte_count > MAX_GLOBAL_STAGING_BYTES:
                raise UploadError("global upload staging-byte quota exceeded", 507)
            reservation["byte_count"] = int(reservation["byte_count"]) + byte_count
            _atomic_json(path, reservation)

    def finish_put(self, session_dir: Path, temp: Path, rel_path: str, size: int, reservation_id: str) -> str:
        with _process_lock(self.store / "quota"):
            with _process_lock(session_dir / "state"):
                session = _read_json(session_dir / "session.json")
                self._require_open(session_dir, session)
                reservation = _read_json(self._reservation_path(reservation_id))
                if int(reservation.get("byte_count", -1)) != size:
                    raise UploadError("upload reservation size mismatch", 500)
                files_root = session_dir / "files"
                target = _contained(files_root, rel_path)
                _assert_safe_chain(files_root, target.parent)
                if not target.parent.is_dir():
                    raise UploadError("parent collection does not exist", 409)
                entries = _tree(files_root)
                file_rows = [row for row in entries if row["kind"] == "file"]
                if len(file_rows) >= MAX_FILES:
                    raise UploadError("upload file-count quota exceeded", 413)
                if sum(int(row["byte_count"]) for row in file_rows) + size > MAX_TOTAL_BYTES:
                    raise UploadError("upload total-byte quota exceeded", 413)
                if shutil.disk_usage(self.store).free < MIN_FREE_DISK_BYTES:
                    raise UploadError("insufficient free space for upload staging", 507)
                digest = _sha256_file(temp)
                try:
                    os.link(temp, target)
                except FileExistsError as exc:
                    raise UploadError("uploaded resource already exists", 412) from exc
                try:
                    temp.unlink()
                except OSError:
                    target.unlink(missing_ok=True)
                    raise
                self._reservation_path(reservation_id).unlink(missing_ok=True)
                return digest

    def abort_put(self, temp: Path, reservation_id: str) -> None:
        temp.unlink(missing_ok=True)
        with _process_lock(self.store / "quota"):
            self._reservation_path(reservation_id).unlink(missing_ok=True)

    def head(self, upload_id: str, rel_path: str, authorization: str | None) -> dict[str, Any]:
        session_dir, _session = self.authorize(upload_id, authorization)
        rel = _safe_relpath(rel_path, allow_empty=True)
        target = session_dir / "files" if not rel else _contained(session_dir / "files", rel)
        _assert_safe_node(target)
        if not target.exists():
            raise UploadError("resource not found", 404)
        if target.is_dir():
            return {"collection": True, "etag": _tree_etag(target), "byte_count": 0}
        return {
            "collection": False,
            "etag": _sha256_file(target),
            "byte_count": target.stat().st_size,
        }

    def propfind(self, upload_id: str, rel_path: str, authorization: str | None, depth: str) -> bytes:
        session_dir, _session = self.authorize(upload_id, authorization)
        rel = _safe_relpath(rel_path, allow_empty=True)
        files_root = session_dir / "files"
        target = files_root if not rel else _contained(files_root, rel)
        _assert_safe_node(target)
        if not target.exists():
            raise UploadError("resource not found", 404)
        if depth not in {"0", "1", "infinity"}:
            raise UploadError("unsupported Depth", 400)
        resources = [target]
        if target.is_dir() and depth == "1":
            resources.extend(sorted(target.iterdir(), key=lambda path: path.name.casefold()))
        elif target.is_dir() and depth == "infinity":
            resources.extend(sorted(target.rglob("*"), key=lambda path: path.as_posix().casefold()))
        multistatus = ET.Element("{DAV:}multistatus")
        base_href = f"{UPLOAD_ROUTE}/{upload_id}"
        for resource in resources:
            _assert_safe_node(resource)
            relative = resource.relative_to(files_root).as_posix()
            href = base_href + ("/" + urllib.parse.quote(relative, safe="/") if relative != "." else "")
            if resource.is_dir() and not href.endswith("/"):
                href += "/"
            response = ET.SubElement(multistatus, "{DAV:}response")
            ET.SubElement(response, "{DAV:}href").text = href
            propstat = ET.SubElement(response, "{DAV:}propstat")
            prop = ET.SubElement(propstat, "{DAV:}prop")
            resource_type = ET.SubElement(prop, "{DAV:}resourcetype")
            if resource.is_dir():
                ET.SubElement(resource_type, "{DAV:}collection")
                etag = _tree_etag(resource)
            else:
                etag = _sha256_file(resource)
                ET.SubElement(prop, "{DAV:}getcontentlength").text = str(resource.stat().st_size)
            ET.SubElement(prop, "{DAV:}getetag").text = f'"{etag}"'
            ET.SubElement(propstat, "{DAV:}status").text = "HTTP/1.1 200 OK"
        return ET.tostring(multistatus, encoding="utf-8", xml_declaration=True)

    def seal(
        self,
        *,
        binding: SessionRunBinding,
        upload_id: str,
        expected_files: list[dict[str, Any]],
        submit: Callable[[list[dict[str, Any]]], dict[str, Any]],
        request_basis: dict[str, Any],
    ) -> dict[str, Any]:
        session_dir, session = self._session(upload_id)
        normalized_expected = _expected_files(expected_files)
        full_basis = {
            "schema": SEAL_SCHEMA,
            "upload_id": upload_id,
            "binding": binding.to_dict(),
            "expected_files": normalized_expected,
            "request": request_basis,
        }
        request_hash = _canonical_hash(full_basis)
        with _process_lock(self.store / "quota"), _process_lock(session_dir / "state"):
            session = _read_json(session_dir / "session.json")
            if session.get("binding") != binding.to_dict():
                raise UploadError("upload session is bound to a different Skill Run", 403)
            sealed_path = session_dir / "sealed.json"
            if sealed_path.is_file():
                sealed = _read_json(sealed_path)
                if sealed.get("request_hash") != request_hash:
                    raise UploadError("upload was sealed with a different request", 409)
                session["status"] = "sealed"
                session["token_hash"] = None
                session["sealed_at"] = sealed["sealed_at"]
                _atomic_json(session_dir / "session.json", session)
                return {**sealed["result"], "upload_id": upload_id, "upload_sealed": True, "seal_idempotent_replay": True}
            if session.get("status") in {"invalid", "expired", "cancelled"}:
                raise UploadError(f"upload session is terminal: {session.get('status')}", 409)
            request_path = session_dir / "seal-request.json"
            frozen = session_dir / "frozen"
            if session.get("status") in {"open", "sealing"}:
                status = session.get("status")
                request_exists = request_path.is_file()
                files = session_dir / "files"
                files_exists = files.is_dir()
                frozen_exists = frozen.is_dir()
                if status == "open" and not request_exists and int(session.get("expires_at_epoch", 0)) <= int(self.clock()):
                    session["status"] = "expired"
                    session["token_hash"] = None
                    _atomic_json(session_dir / "session.json", session)
                    raise UploadError("upload session expired", 410)
                if request_exists:
                    prior = _read_json(request_path)
                    if prior.get("request_hash") != request_hash:
                        raise UploadError("upload sealing is already in progress for a different request", 409)
                else:
                    if status != "open" or not files_exists or frozen_exists:
                        raise UploadError("ambiguous upload freeze state", 409)
                    _write_json_once(request_path, {**full_basis, "request_hash": request_hash})
                    request_exists = True
                if status == "open" and frozen_exists:
                    raise UploadError("ambiguous upload freeze state", 409)
                if status == "sealing" and not request_exists:
                    raise UploadError("ambiguous upload freeze state", 409)
                session["status"] = "sealing"
                session["token_hash"] = None
                session["sealing_at"] = _iso(int(self.clock()))
                _atomic_json(session_dir / "session.json", session)
                if files_exists and not frozen_exists:
                    os.replace(files, frozen)
                elif not files_exists and frozen_exists:
                    pass
                else:
                    raise UploadError("ambiguous upload freeze state", 409)
            else:
                raise UploadError("upload session is not sealable", 409)
            try:
                actual_tree = _tree(frozen)
                expected_tree = _expected_tree(normalized_expected)
                if actual_tree != expected_tree:
                    raise UploadError("uploaded tree does not exactly match expected files", 422)
                files: list[dict[str, Any]] = []
                for expected in normalized_expected:
                    target = _contained(frozen, expected["path"])
                    content_bytes = target.read_bytes()
                    if len(content_bytes) != expected["byte_count"]:
                        raise UploadError(f"uploaded byte_count mismatch: {expected['path']}", 422)
                    if _sha256_bytes(content_bytes) != expected["content_hash"]:
                        raise UploadError(f"uploaded content_hash mismatch: {expected['path']}", 422)
                    try:
                        content = content_bytes.decode("utf-8")
                    except UnicodeDecodeError as exc:
                        raise UploadError(f"uploaded file is not UTF-8: {expected['path']}", 422) from exc
                    files.append({**expected, "content": content})
                result = submit(files)
                sealed = {
                    "schema": SEAL_SCHEMA,
                    "upload_id": upload_id,
                    "request_hash": request_hash,
                    "sealed_at": _iso(int(self.clock())),
                    "expected_tree_hash": _canonical_hash(normalized_expected),
                    "result": result,
                }
                _write_json_once(sealed_path, sealed)
                session["status"] = "sealed"
                session["sealed_at"] = sealed["sealed_at"]
                _atomic_json(session_dir / "session.json", session)
                return {**result, "upload_id": upload_id, "upload_sealed": True, "seal_idempotent_replay": False}
            except Exception as exc:
                session["status"] = "invalid"
                session["invalid_at"] = _iso(int(self.clock()))
                session["invalid_reason"] = type(exc).__name__
                _atomic_json(session_dir / "session.json", session)
                raise

    def _session(self, upload_id: str) -> tuple[Path, dict[str, Any]]:
        try:
            normalized = str(uuid.UUID(str(upload_id)))
        except ValueError as exc:
            raise UploadError("invalid upload_id", 404) from exc
        session_dir = self.store / normalized
        path = session_dir / "session.json"
        if not path.is_file():
            raise UploadError("upload session not found", 404)
        _assert_safe_chain(self.store, session_dir)
        session = _read_json(path)
        if session.get("schema") != UPLOAD_SCHEMA or session.get("upload_id") != normalized:
            raise UploadError("invalid upload session record", 500)
        return session_dir, session

    def _require_open(self, session_dir: Path, session: dict[str, Any]) -> None:
        if session.get("status") != "open":
            raise UploadError("upload session is not open", 409)
        if int(session.get("expires_at_epoch", 0)) <= int(self.clock()):
            raise UploadError("upload session expired", 410)

    def _reservation_path(self, reservation_id: str) -> Path:
        directory = self.store / ".reservations"
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{reservation_id}.json"

    def _cleanup_expired_locked(self, now: int) -> None:
        for path in self.store.glob("*/session.json"):
            session = _read_json(path)
            session_dir = path.parent
            if session.get("status") == "open" and int(session.get("expires_at_epoch", 0)) <= now:
                with _process_lock(session_dir / "state"):
                    current = _read_json(path)
                    if current.get("status") == "open" and int(current.get("expires_at_epoch", 0)) <= now:
                        current["status"] = "expired"
                        current["token_hash"] = None
                        _atomic_json(path, current)
                        for name in ("files", "frozen", ".incoming"):
                            shutil.rmtree(session_dir / name, ignore_errors=True)
            if session.get("status") in {"expired", "invalid", "sealed", "cancelled"}:
                for name in ("files", "frozen", ".incoming"):
                    shutil.rmtree(session_dir / name, ignore_errors=True)
        reservations = self.store / ".reservations"
        if reservations.is_dir():
            for path in reservations.glob("*.json"):
                try:
                    row = _read_json(path)
                except ValueError as exc:
                    raise UploadError("invalid upload reservation state", 500) from exc
                session_path = self.store / str(row.get("upload_id")) / "session.json"
                if not session_path.is_file():
                    path.unlink(missing_ok=True)
                    continue
                session = _read_json(session_path)
                keep = session.get("status") == "open" and int(session.get("expires_at_epoch", 0)) > now
                if not keep:
                    path.unlink(missing_ok=True)


def add_inbound_webdav_routes(starlette_app: Any, manager: InboundUploadManager) -> None:
    from starlette.responses import Response
    from starlette.routing import Route

    async def endpoint(request: Any) -> Response:
        upload_id = request.path_params["upload_id"]
        rel_path = request.path_params.get("path") or ""
        authorization = request.headers.get("authorization")
        method = request.method.upper()
        try:
            raw_path = bytes(request.scope.get("raw_path") or b"").lower()
            if any(marker in raw_path for marker in (b"%2f", b"%5c", b"%2e", b"%25")):
                raise UploadError("ambiguous percent-encoded upload path")
            if method == "OPTIONS":
                manager.authorize(upload_id, authorization)
                return Response(status_code=204, headers={"Allow": "OPTIONS, MKCOL, PUT, HEAD, PROPFIND", "DAV": "1"})
            if method == "MKCOL":
                manager.make_collection(upload_id, rel_path, authorization)
                return Response(status_code=201)
            if method == "PUT":
                if request.headers.get("if-none-match") != "*":
                    raise UploadError("PUT requires If-None-Match: *", 428)
                content_length = request.headers.get("content-length")
                if content_length is not None:
                    declared_size = _declared_content_length(content_length)
                    if declared_size > MAX_FILE_BYTES:
                        raise UploadError("upload file-byte quota exceeded", 413)
                session_dir, temp, state = manager.begin_put(upload_id, rel_path, authorization)
                size = 0
                try:
                    with temp.open("xb") as handle:
                        async for chunk in request.stream():
                            next_size = size + len(chunk)
                            if next_size > MAX_FILE_BYTES:
                                raise UploadError("upload file-byte quota exceeded", 413)
                            manager.reserve_chunk(state["reservation_id"], len(chunk))
                            handle.write(chunk)
                            size = next_size
                        handle.flush()
                        os.fsync(handle.fileno())
                    digest = manager.finish_put(
                        session_dir,
                        temp,
                        state["relative"],
                        size,
                        state["reservation_id"],
                    )
                finally:
                    manager.abort_put(temp, state["reservation_id"])
                return Response(status_code=201, headers={"ETag": f'"{digest}"'})
            if method == "HEAD":
                row = manager.head(upload_id, rel_path, authorization)
                headers = {"ETag": f'"{row["etag"]}"'}
                if not row["collection"]:
                    headers["Content-Length"] = str(row["byte_count"])
                return Response(status_code=200, headers=headers)
            if method == "PROPFIND":
                body = manager.propfind(upload_id, rel_path, authorization, request.headers.get("depth", "0"))
                return Response(body, status_code=207, media_type="application/xml")
            raise UploadError("method is not allowed for upload sessions", 405)
        except UploadError as exc:
            headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
            return Response(str(exc), status_code=exc.status_code, media_type="text/plain", headers=headers)

    routes = getattr(getattr(starlette_app, "router"), "routes")
    methods = ["OPTIONS", "MKCOL", "PUT", "HEAD", "PROPFIND", "MOVE", "COPY", "DELETE", "GET"]
    routes.append(Route(f"{UPLOAD_ROUTE}/{{upload_id}}", endpoint, methods=methods))
    routes.append(Route(f"{UPLOAD_ROUTE}/{{upload_id}}/", endpoint, methods=methods))
    routes.append(Route(f"{UPLOAD_ROUTE}/{{upload_id}}/{{path:path}}", endpoint, methods=methods))


def _expected_files(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or not rows or len(rows) > MAX_FILES:
        raise UploadError(f"expected_files must contain 1 through {MAX_FILES} rows")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    total = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "content_hash", "byte_count"}:
            raise UploadError("expected_files rows require only path, content_hash, and byte_count")
        path = _safe_relpath(str(row["path"]), allow_empty=False)
        folded = path.casefold()
        if folded in seen:
            raise UploadError("expected_files contains duplicate or case-colliding paths")
        seen.add(folded)
        digest = str(row["content_hash"])
        if not SHA256_RE.fullmatch(digest):
            raise UploadError("expected_files content_hash must be lowercase sha256")
        size = row["byte_count"]
        if not isinstance(size, int) or isinstance(size, bool) or size < 0 or size > MAX_FILE_BYTES:
            raise UploadError("expected_files byte_count is outside the per-file limit")
        total += size
        result.append({"path": path, "content_hash": digest, "byte_count": size})
    if total > MAX_TOTAL_BYTES:
        raise UploadError("expected_files total-byte quota exceeded")
    return sorted(result, key=lambda row: row["path"].casefold())


def _tree(root: Path) -> list[dict[str, Any]]:
    _assert_safe_node(root)
    if not root.is_dir():
        raise UploadError("upload tree is unavailable", 409)
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        _assert_safe_node(path)
        relative = path.relative_to(root).as_posix()
        folded = relative.casefold()
        if folded in seen:
            raise UploadError("upload tree contains a case-colliding path", 422)
        seen.add(folded)
        if path.is_dir():
            result.append({"path": relative + "/", "kind": "directory", "byte_count": 0})
        elif path.is_file():
            size = path.stat().st_size
            if size > MAX_FILE_BYTES:
                raise UploadError("upload file-byte quota exceeded", 413)
            result.append({"path": relative, "kind": "file", "byte_count": size})
        else:
            raise UploadError("upload tree contains an unsupported filesystem entry", 422)
    files = [row for row in result if row["kind"] == "file"]
    directories = [row for row in result if row["kind"] == "directory"]
    if len(files) > MAX_FILES or sum(int(row["byte_count"]) for row in files) > MAX_TOTAL_BYTES:
        raise UploadError("upload tree exceeds quota", 413)
    if len(directories) > MAX_COLLECTIONS:
        raise UploadError("upload tree exceeds collection quota", 413)
    return result


def _expected_tree(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    directories: set[str] = set()
    result = []
    for row in files:
        parts = PurePosixPath(row["path"]).parts
        for length in range(1, len(parts)):
            directories.add("/".join(parts[:length]) + "/")
        result.append({"path": row["path"], "kind": "file", "byte_count": row["byte_count"]})
    result.extend({"path": path, "kind": "directory", "byte_count": 0} for path in directories)
    return sorted(result, key=lambda row: row["path"].casefold())


def _safe_relpath(value: str, *, allow_empty: bool) -> str:
    raw = urllib.parse.unquote(str(value), errors="strict")
    if raw.startswith("/") or raw.endswith("/") or "//" in raw:
        raise UploadError("ambiguous upload path separators")
    if unicodedata.normalize("NFC", raw) != raw:
        raise UploadError("upload path must use NFC Unicode normalization")
    if not raw and allow_empty:
        return ""
    if not raw or "\\" in raw or "\x00" in raw or len(raw.encode("utf-8")) > MAX_PATH_BYTES:
        raise UploadError("invalid upload path")
    parts = PurePosixPath(raw).parts
    if len(parts) > MAX_PATH_DEPTH:
        raise UploadError("upload path exceeds depth limit")
    for part in parts:
        if part in {"", ".", ".."} or any(ord(char) < 32 for char in part):
            raise UploadError("invalid upload path segment")
        if part.endswith((" ", ".")) or ":" in part or part.upper().split(".", 1)[0] in WINDOWS_RESERVED_NAMES:
            raise UploadError("upload path is not portable")
    return "/".join(parts)


def _contained(root: Path, rel_path: str) -> Path:
    target = root.joinpath(*PurePosixPath(rel_path).parts)
    try:
        target.resolve(strict=False).relative_to(root.resolve())
    except ValueError as exc:
        raise UploadError("upload path escapes staging") from exc
    return target


def _assert_safe_chain(root: Path, target: Path) -> None:
    root = root.resolve()
    current = target
    chain = []
    while current != root:
        chain.append(current)
        if current.parent == current:
            raise UploadError("filesystem path escapes upload root")
        current = current.parent
    _assert_safe_node(root)
    for path in reversed(chain):
        if path.exists():
            _assert_safe_node(path)


def _assert_safe_node(path: Path) -> None:
    if not path.exists():
        return
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or int(getattr(info, "st_file_attributes", 0)) & 0x400:
        raise UploadError("symlink or reparse point is forbidden in upload storage", 422)
    if getattr(info, "st_nlink", 1) > 1 and path.is_file():
        raise UploadError("hard-linked files are forbidden in upload storage", 422)


def _tree_etag(root: Path) -> str:
    rows = []
    for row in _tree(root):
        digest = _sha256_file(root / row["path"]) if row["kind"] == "file" else None
        rows.append({**row, "content_hash": digest})
    return _canonical_hash(rows)


def _ttl(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not MIN_TTL_SECONDS <= value <= MAX_TTL_SECONDS:
        raise ValueError(f"upload session TTL must be {MIN_TTL_SECONDS} through {MAX_TTL_SECONDS} seconds")
    return value


def _declared_content_length(value: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise UploadError("invalid Content-Length", 400) from exc
    if result < 0:
        raise UploadError("invalid Content-Length", 400)
    return result


def _base_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(str(value).strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("inbound WebDAV public base URL must be an absolute HTTP(S) URL without credentials, query, or fragment")
    return str(value).strip().rstrip("/")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UploadError(f"invalid upload state: {path.name}", 500) from exc
    if not isinstance(value, dict):
        raise UploadError(f"invalid upload state: {path.name}", 500)
    return value


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        with temp.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _write_json_once(path: Path, value: dict[str, Any]) -> None:
    temp = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        _atomic_json(temp, value)
        try:
            os.link(temp, path)
        except FileExistsError as exc:
            raise UploadError(f"immutable upload event already exists: {path.name}", 409) from exc
    finally:
        temp.unlink(missing_ok=True)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_hash(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _iso(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="seconds")


def _store_bytes(root: Path) -> int:
    total = 0
    for path in root.glob("*/files/**/*"):
        if path.is_file():
            total += path.stat().st_size
    for path in root.glob("*/frozen/**/*"):
        if path.is_file():
            total += path.stat().st_size
    return total


def _reserved_bytes(root: Path) -> int:
    total = 0
    for path in (root / ".reservations").glob("*.json"):
        try:
            total += int(_read_json(path).get("byte_count", 0))
        except (ValueError, TypeError) as exc:
            raise UploadError("invalid upload reservation state", 500) from exc
    return total


def _reservation_rows(root: Path) -> list[dict[str, Any]]:
    rows = []
    for path in (root / ".reservations").glob("*.json"):
        try:
            rows.append(_read_json(path))
        except ValueError as exc:
            raise UploadError("invalid upload reservation state", 500) from exc
    return rows

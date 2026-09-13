"""Server-owned transports for promoting reviewed contribution returns."""

from __future__ import annotations

import base64
import ctypes
import errno
import hashlib
import hmac
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Protocol


@dataclass(frozen=True)
class AdoptionFile:
    bundle_path: str
    content: str
    content_hash: str


class CanonicalAdoptionTransport(Protocol):
    name: str

    def adopt(
        self,
        *,
        root: Path,
        record_dir: Path,
        contribution_id: str,
        adoption_id: str,
        kind: str,
        target_path: str,
        files: list[AdoptionFile],
        recovery_allowed: bool,
    ) -> dict[str, Any]: ...


class HumanApprovalVerifier(Protocol):
    def verify(self, assertion: str, expected_claims: dict[str, Any]) -> dict[str, Any]: ...

    def seal_event(self, event: dict[str, Any]) -> str: ...

    def verify_event(self, event: dict[str, Any], signature: str) -> None: ...


class HmacHumanApprovalVerifier:
    """Verify an approval assertion issued outside the AI/MCP tool boundary."""

    def __init__(self, secret: str) -> None:
        if len(secret.encode("utf-8")) < 32:
            raise ValueError("contribution approval secret must be at least 32 UTF-8 bytes")
        self._secret = secret.encode("utf-8")

    def verify(self, assertion: str, expected_claims: dict[str, Any]) -> dict[str, Any]:
        try:
            payload_text, supplied_signature = str(assertion).split(".", 1)
            payload = _base64url_decode(payload_text)
            signature = _base64url_decode(supplied_signature)
            claims = json.loads(payload.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid human approval assertion") from exc
        expected_signature = hmac.new(self._secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("invalid human approval assertion signature")
        if not isinstance(claims, dict):
            raise ValueError("human approval assertion claims must be an object")
        for key, value in expected_claims.items():
            if claims.get(key) != value:
                raise ValueError(f"human approval assertion claim mismatch: {key}")
        expires_at = claims.get("expires_at")
        if not isinstance(expires_at, int) or expires_at < int(time.time()):
            raise ValueError("human approval assertion is expired or missing expires_at")
        return claims

    def seal_event(self, event: dict[str, Any]) -> str:
        payload = _canonical_json_bytes(event)
        return _base64url_encode(hmac.new(self._secret, payload, hashlib.sha256).digest())

    def verify_event(self, event: dict[str, Any], signature: str) -> None:
        try:
            supplied = _base64url_decode(signature)
        except ValueError as exc:
            raise ValueError("invalid contribution event signature") from exc
        expected = hmac.new(self._secret, _canonical_json_bytes(event), hashlib.sha256).digest()
        if not hmac.compare_digest(supplied, expected):
            raise ValueError("invalid contribution event signature")


def issue_hmac_approval_assertion(
    secret: str,
    claims: dict[str, Any],
    *,
    expires_at: int | None = None,
) -> str:
    """Issuer helper for a trusted UI/identity-provider adapter and tests."""
    key = secret.encode("utf-8")
    if len(key) < 32:
        raise ValueError("contribution approval secret must be at least 32 UTF-8 bytes")
    payload = json.dumps(
        {**claims, "expires_at": expires_at or int(time.time()) + 300},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    signature = hmac.new(key, payload, hashlib.sha256).digest()
    return f"{_base64url_encode(payload)}.{_base64url_encode(signature)}"


class LocalCanonicalAdoptionTransport:
    """Filesystem equivalent of a conditional WebDAV MOVE."""

    name = "local_atomic_move"

    def adopt(
        self,
        *,
        root: Path,
        record_dir: Path,
        contribution_id: str,
        adoption_id: str,
        kind: str,
        target_path: str,
        files: list[AdoptionFile],
        recovery_allowed: bool,
    ) -> dict[str, Any]:
        repo = root.resolve()
        staging = record_dir / "adoption-staging" / f"{adoption_id}.tmp"
        staging.parent.mkdir(parents=True, exist_ok=True)
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir()
        try:
            if _is_single_file_kind(kind):
                target = _inside(repo, target_path)
                if target.exists():
                    return _recover_or_collide(
                        repo,
                        kind,
                        target_path,
                        files,
                        recovery_allowed=recovery_allowed,
                    )
                staged_file = staging / "payload"
                _write_fsynced(staged_file, files[0].content)
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    os.link(staged_file, target)
                except FileExistsError as exc:
                    raise FileExistsError(f"canonical target already exists: {target_path}") from exc
                return {
                    "transport": self.name,
                    "precondition": "exclusive_hard_link",
                    "source_etag": files[0].content_hash,
                    "target_paths": [target_path],
                    "recovered": False,
                }

            target_dir = _inside(repo, target_path)
            if target_dir.exists():
                return _recover_or_collide(
                    repo,
                    "deterministic_tool",
                    target_path,
                    files,
                    recovery_allowed=recovery_allowed,
                )
            payload = staging / "payload"
            payload.mkdir()
            for item in files:
                destination = payload.joinpath(*PurePosixPath(item.bundle_path).parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                _write_fsynced(destination, item.content)
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            try:
                _rename_directory_no_replace(payload, target_dir)
            except FileExistsError as exc:
                raise FileExistsError(
                    f"canonical target already exists: {target_path}"
                ) from exc
            return {
                "transport": self.name,
                "precondition": "destination_absent",
                "source_etag": _tree_etag(files),
                "target_paths": [
                    f"{target_path}/{item.bundle_path}" for item in files
                ],
                "recovered": False,
            }
        finally:
            shutil.rmtree(staging, ignore_errors=True)


class WebDavCanonicalAdoptionTransport:
    """Stage with restricted credentials, then MOVE with server credentials."""

    name = "webdav_conditional_move"

    def __init__(
        self,
        *,
        staging_base_url: str,
        canonical_base_url: str,
        staging_username: str,
        staging_password: str,
        adoption_username: str,
        adoption_password: str,
        opener: Any = None,
    ) -> None:
        self.staging_base_url = _base_url(staging_base_url, "staging_base_url")
        self.canonical_base_url = _base_url(canonical_base_url, "canonical_base_url")
        self.staging_auth = _basic_auth(staging_username, staging_password, "staging")
        self.adoption_auth = _basic_auth(adoption_username, adoption_password, "adoption")
        self._opener = opener or urllib.request.urlopen

    @classmethod
    def from_environment(
        cls,
        *,
        staging_base_url: str | None = None,
        canonical_base_url: str | None = None,
    ) -> "WebDavCanonicalAdoptionTransport":
        return cls(
            staging_base_url=staging_base_url
            or os.environ.get("XREFKIT_ADOPTION_WEBDAV_STAGING_URL", ""),
            canonical_base_url=canonical_base_url
            or os.environ.get("XREFKIT_ADOPTION_WEBDAV_CANONICAL_URL", ""),
            staging_username=os.environ.get("XREFKIT_ADOPTION_WEBDAV_STAGING_USERNAME", ""),
            staging_password=os.environ.get("XREFKIT_ADOPTION_WEBDAV_STAGING_PASSWORD", ""),
            adoption_username=os.environ.get("XREFKIT_ADOPTION_WEBDAV_USERNAME", ""),
            adoption_password=os.environ.get("XREFKIT_ADOPTION_WEBDAV_PASSWORD", ""),
        )

    def adopt(
        self,
        *,
        root: Path,
        record_dir: Path,
        contribution_id: str,
        adoption_id: str,
        kind: str,
        target_path: str,
        files: list[AdoptionFile],
        recovery_allowed: bool,
    ) -> dict[str, Any]:
        del root, record_dir
        target_urls = _target_urls(self.canonical_base_url, kind, target_path, files)
        if recovery_allowed and self._remote_files_match(
            target_urls,
            files,
            collection_url=(
                _url_join(self.canonical_base_url, target_path)
                if kind == "deterministic_tool"
                else None
            ),
        ):
            return {
                "transport": self.name,
                "precondition": "prepared_event_and_matching_remote_hashes",
                "source_etag": None,
                "target_paths": [path for path, _url in target_urls],
                "recovered": True,
            }
        if any(self._exists(url, self.adoption_auth) for _path, url in target_urls):
            raise FileExistsError(f"canonical target already exists: {target_path}")

        contribution_url = _url_join(self.staging_base_url, contribution_id)
        self._ensure_collection(contribution_url)
        operation_url = _url_join(contribution_url, adoption_id)
        self._ensure_collection(operation_url)
        if _is_single_file_kind(kind):
            source_url = _url_join(operation_url, "payload")
            self._put(
                source_url,
                files[0],
                allow_existing=recovery_allowed,
            )
            staged_file_urls = [(files[0].bundle_path, source_url)]
        else:
            source_url = _url_join(operation_url, "payload")
            self._ensure_collection(source_url)
            created: set[str] = {source_url}
            staged_file_urls = []
            for item in files:
                parts = PurePosixPath(item.bundle_path).parts
                for length in range(1, len(parts)):
                    collection = _url_join(source_url, *parts[:length])
                    if collection not in created:
                        self._ensure_collection(collection)
                        created.add(collection)
                staged_url = _url_join(source_url, *parts)
                self._put(
                    staged_url,
                    item,
                    allow_existing=recovery_allowed,
                )
                staged_file_urls.append((item.bundle_path, staged_url))

        self._assert_remote_files(
            staged_file_urls,
            files,
            collection_url=source_url if kind == "deterministic_tool" else None,
            auth=self.staging_auth,
        )

        source_etag = self._etag(source_url, self.staging_auth)
        if not source_etag:
            raise RuntimeError("WebDAV staging resource did not provide an ETag")
        destination_url = _url_join(self.canonical_base_url, target_path)
        response = self._request(
            "MOVE",
            source_url,
            auth=self.adoption_auth,
            headers={
                "Destination": destination_url,
                "Overwrite": "F",
                "If-Match": source_etag,
            },
            expected={201, 204},
        )
        response.close()
        return {
            "transport": self.name,
            "precondition": "If-Match and Overwrite:F",
            "source_etag": source_etag,
            "target_paths": [path for path, _url in target_urls],
            "recovered": False,
        }

    def _ensure_collection(self, url: str) -> None:
        try:
            response = self._request("MKCOL", url, auth=self.staging_auth, expected={201})
            response.close()
        except urllib.error.HTTPError as exc:
            if exc.code != 405:
                raise

    def _put(self, url: str, item: AdoptionFile, *, allow_existing: bool) -> None:
        try:
            response = self._request(
                "PUT",
                url,
                auth=self.staging_auth,
                data=item.content.encode("utf-8"),
                headers={
                    "Content-Type": "text/plain; charset=utf-8",
                    "If-None-Match": "*",
                },
                expected={201, 204},
            )
            response.close()
        except urllib.error.HTTPError as exc:
            if exc.code != 412 or not allow_existing:
                raise
            response = self._request("GET", url, auth=self.staging_auth, expected={200})
            body = response.read()
            response.close()
            if hashlib.sha256(body).hexdigest() != item.content_hash:
                raise FileExistsError("WebDAV staging resource has different content") from exc

    def _etag(self, url: str, auth: str) -> str | None:
        response = self._request("HEAD", url, auth=auth, expected={200, 204})
        etag = response.headers.get("ETag")
        response.close()
        return etag

    def _exists(self, url: str, auth: str) -> bool:
        try:
            response = self._request("HEAD", url, auth=auth, expected={200, 204})
            response.close()
            return True
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return False
            raise

    def _remote_files_match(
        self,
        targets: list[tuple[str, str]],
        files: list[AdoptionFile],
        *,
        collection_url: str | None,
    ) -> bool:
        if collection_url is not None:
            try:
                actual = self._collection_files(collection_url, self.adoption_auth)
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    return False
                raise
            if actual != _expected_tree_entries(files):
                return False
        for (_path, url), item in zip(targets, files, strict=True):
            try:
                response = self._request("GET", url, auth=self.adoption_auth, expected={200})
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    return False
                raise
            body = response.read()
            response.close()
            if hashlib.sha256(body).hexdigest() != item.content_hash:
                return False
        return True

    def _assert_remote_files(
        self,
        targets: list[tuple[str, str]],
        files: list[AdoptionFile],
        *,
        collection_url: str | None,
        auth: str,
    ) -> None:
        if collection_url is not None:
            actual = self._collection_files(collection_url, auth)
            expected = _expected_tree_entries(files)
            if actual != expected:
                raise ValueError("WebDAV staged collection tree does not match contribution")
        for (_path, url), item in zip(targets, files, strict=True):
            response = self._request("GET", url, auth=auth, expected={200})
            body = response.read()
            response.close()
            if hashlib.sha256(body).hexdigest() != item.content_hash:
                raise ValueError(f"WebDAV staged file hash mismatch: {item.bundle_path}")

    def _collection_files(self, collection_url: str, auth: str) -> set[str]:
        response = self._request(
            "PROPFIND",
            collection_url,
            auth=auth,
            headers={"Depth": "infinity"},
            expected={207},
        )
        body = response.read()
        response.close()
        try:
            root = ET.fromstring(body)
        except ET.ParseError as exc:
            raise ValueError("invalid WebDAV PROPFIND response") from exc
        base_path = urllib.parse.unquote(urllib.parse.urlsplit(collection_url).path).rstrip("/")
        result: set[str] = set()
        for row in root.findall("{DAV:}response"):
            href = row.findtext("{DAV:}href")
            if not href:
                continue
            path = urllib.parse.unquote(urllib.parse.urlsplit(href).path)
            prefix = base_path + "/"
            if path.rstrip("/") == base_path:
                continue
            if not path.startswith(prefix):
                raise ValueError("WebDAV PROPFIND returned a resource outside staging")
            relative = path[len(prefix):].strip("/")
            if not relative:
                continue
            is_collection = row.find(".//{DAV:}collection") is not None
            result.add(relative + "/" if is_collection else relative)
        return result

    def _request(
        self,
        method: str,
        url: str,
        *,
        auth: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        expected: set[int],
    ) -> Any:
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Authorization", auth)
        for name, value in (headers or {}).items():
            request.add_header(name, value)
        response = self._opener(request, timeout=30)
        if response.status not in expected:
            response.close()
            raise RuntimeError(f"WebDAV {method} returned HTTP {response.status}")
        return response


def _inside(root: Path, rel_path: str) -> Path:
    target = root.joinpath(*PurePosixPath(rel_path).parts).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"canonical target escapes repository: {rel_path}") from exc
    return target


def _recover_or_collide(
    root: Path,
    kind: str,
    target_path: str,
    files: list[AdoptionFile],
    *,
    recovery_allowed: bool,
) -> dict[str, Any]:
    targets = _target_paths(target_path, files)
    expected_paths = {_inside(root, value) for value in targets}
    if _is_single_file_kind(kind):
        actual_paths = {_inside(root, target_path)} if _inside(root, target_path).is_file() else set()
        exact_tree = actual_paths == expected_paths
    else:
        target_root = _inside(root, target_path)
        actual_entries = {
            path.relative_to(target_root).as_posix() + ("/" if path.is_dir() else "")
            for path in target_root.rglob("*")
        }
        exact_tree = actual_entries == _expected_tree_entries(files)
    hashes_match = all(
        path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == item.content_hash
        for path, item in zip((_inside(root, value) for value in targets), files, strict=True)
    )
    if recovery_allowed and exact_tree and hashes_match:
        return {
            "transport": LocalCanonicalAdoptionTransport.name,
            "precondition": "prepared_event_and_matching_target_hashes",
            "source_etag": _tree_etag(files),
            "target_paths": targets,
            "recovered": True,
        }
    raise FileExistsError(f"canonical target already exists: {target_path}")


def _rename_directory_no_replace(source: Path, target: Path) -> None:
    if os.name == "nt":
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        move_file_ex = kernel32.MoveFileExW
        move_file_ex.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        move_file_ex.restype = ctypes.c_int
        # MOVEFILE_WRITE_THROUGH keeps the publish durable; omitting
        # MOVEFILE_REPLACE_EXISTING provides the no-replace guarantee.
        if not move_file_ex(str(source), str(target), 0x00000008):
            error = ctypes.get_last_error()
            if error in {80, 183}:  # ERROR_FILE_EXISTS / ERROR_ALREADY_EXISTS
                raise FileExistsError(f"canonical target already exists: {target.as_posix()}")
            raise OSError(error, ctypes.FormatError(error), str(target))
        return
    source_bytes = os.fsencode(source)
    target_bytes = os.fsencode(target)
    if sys.platform.startswith("linux"):
        libc = ctypes.CDLL(None, use_errno=True)
        renameat2 = getattr(libc, "renameat2", None)
        if renameat2 is None:
            raise RuntimeError("atomic no-overwrite directory rename is unavailable")
        result = renameat2(-100, source_bytes, -100, target_bytes, 1)
    elif sys.platform == "darwin":
        libc = ctypes.CDLL(None, use_errno=True)
        renamex_np = getattr(libc, "renamex_np", None)
        if renamex_np is None:
            raise RuntimeError("atomic no-overwrite directory rename is unavailable")
        result = renamex_np(source_bytes, target_bytes, 0x00000004)
    else:
        raise RuntimeError("atomic no-overwrite directory rename is unavailable")
    if result != 0:
        error = ctypes.get_errno()
        if error in {errno.EEXIST, errno.ENOTEMPTY}:
            raise FileExistsError(f"canonical target already exists: {target.as_posix()}")
        raise OSError(error, os.strerror(error), str(target))


def _target_paths(target_path: str, files: list[AdoptionFile]) -> list[str]:
    if len(files) == 1 and target_path.lower().endswith(".md"):
        return [target_path]
    return [f"{target_path}/{item.bundle_path}" for item in files]


def _target_urls(
    base_url: str, kind: str, target_path: str, files: list[AdoptionFile]
) -> list[tuple[str, str]]:
    paths = [target_path] if _is_single_file_kind(kind) else _target_paths(target_path, files)
    return [(path, _url_join(base_url, path)) for path in paths]


def _is_single_file_kind(kind: str) -> bool:
    return kind in {"knowledge", "skill_observation"}


def _tree_etag(files: list[AdoptionFile]) -> str:
    payload = json.dumps(
        [(item.bundle_path, item.content_hash) for item in files],
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _expected_tree_entries(files: list[AdoptionFile]) -> set[str]:
    result: set[str] = set()
    for item in files:
        parts = PurePosixPath(item.bundle_path).parts
        result.add("/".join(parts))
        for length in range(1, len(parts)):
            result.add("/".join(parts[:length]) + "/")
    return result


def _write_fsynced(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _base_url(value: str, field: str) -> str:
    parsed = urllib.parse.urlsplit(str(value).strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field} must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(f"{field} must not contain credentials, query, or fragment")
    return str(value).strip().rstrip("/")


def _basic_auth(username: str, password: str, label: str) -> str:
    if not username or not password:
        raise ValueError(f"WebDAV {label} username and password are required")
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def _url_join(base: str, *parts: str) -> str:
    encoded = [urllib.parse.quote(piece, safe="") for part in parts for piece in PurePosixPath(part).parts]
    return base.rstrip("/") + "/" + "/".join(encoded)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

from __future__ import annotations

import json
import re
import tempfile
from collections.abc import Awaitable, Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .repository import stable_hash


XID_PATTERN = re.compile(r"^[A-Za-z0-9]+$")
NAMESPACE_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


class DocumentCacheProtocolError(RuntimeError):
    pass


class XidDocumentCache:
    def __init__(
        self,
        cache_root: str | Path,
        repository_fingerprint: str,
    ) -> None:
        if not NAMESPACE_PATTERN.fullmatch(repository_fingerprint):
            raise ValueError(
                f"invalid repository fingerprint: {repository_fingerprint!r}"
            )
        self.cache_root = Path(cache_root)
        self.repository_fingerprint = repository_fingerprint
        self.cache_dir = self.cache_root / repository_fingerprint

    def load(self, xid: str) -> dict[str, Any] | None:
        path = self._entry_path(xid)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            document = payload["document"]
            content_hash = payload["content_hash"]
            if payload["repository_fingerprint"] != self.repository_fingerprint:
                raise ValueError("cached repository fingerprint does not match")
            if document["xid"] != xid:
                raise ValueError("cached XID does not match the cache key")
            if (
                document["repository_fingerprint"]
                != self.repository_fingerprint
            ):
                raise ValueError("document repository fingerprint does not match")
            if document["content_hash"] != content_hash:
                raise ValueError("cached content_hash does not match document")
            if stable_hash(document["content"]) != content_hash:
                raise ValueError("cached content hash is invalid")
            return document
        except FileNotFoundError:
            return None
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            self.evict(xid)
            return None

    def known_versions(
        self,
        xids: Iterable[str] | None = None,
    ) -> dict[str, str]:
        if xids is not None:
            versions: dict[str, str] = {}
            for xid in xids:
                document = self.load(xid)
                if document is not None:
                    versions[xid] = document["content_hash"]
            return versions
        if not self.cache_dir.exists():
            return {}
        versions: dict[str, str] = {}
        for path in sorted(self.cache_dir.glob("*.json")):
            xid = path.stem
            if not XID_PATTERN.fullmatch(xid):
                continue
            document = self.load(xid)
            if document is not None:
                versions[xid] = document["content_hash"]
        return versions

    def store(self, document: dict[str, Any]) -> bool:
        xid = str(document.get("xid", ""))
        self._validate_xid(xid)
        if (
            document.get("repository_fingerprint")
            != self.repository_fingerprint
        ):
            raise DocumentCacheProtocolError(
                "document repository fingerprint does not match cache namespace"
            )
        policy = document.get("cache_policy") or {}
        if policy.get("cache_recommended") is not True:
            self.evict(xid)
            return False
        content = document.get("content")
        version = document.get("content_hash")
        if not isinstance(content, str) or not isinstance(version, str):
            raise DocumentCacheProtocolError(
                "cacheable document must include content and content_hash"
            )
        if stable_hash(content) != version:
            raise DocumentCacheProtocolError(
                "document content does not match content_hash"
            )

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        target = self._entry_path(xid)
        payload = {
            "schema_version": 1,
            "repository_fingerprint": self.repository_fingerprint,
            "xid": xid,
            "content_hash": version,
            "document": document,
        }
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        self._write_atomic(target, serialized)
        return True

    def startup_versions(self) -> dict[str, str]:
        try:
            payload = json.loads(
                self._startup_index_path().read_text(encoding="utf-8")
            )
            if payload["repository_fingerprint"] != self.repository_fingerprint:
                raise ValueError("startup repository fingerprint does not match")
            xids = payload["xids"]
            if not isinstance(xids, list) or not all(
                isinstance(xid, str) for xid in xids
            ):
                raise ValueError("invalid startup XID index")
        except (
            FileNotFoundError,
            OSError,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            return {}
        return self.known_versions(xids)

    async def resolve_startup(
        self,
        fetch_startup: Callable[
            [dict[str, str]],
            Awaitable[dict[str, Any]],
        ],
    ) -> dict[str, Any]:
        known_versions = self.startup_versions()
        response = await fetch_startup(known_versions)
        try:
            references = [
                self.materialize(reference)
                for reference in response["references"]
            ]
        except (DocumentCacheProtocolError, KeyError, TypeError):
            known_versions = {}
            response = await fetch_startup(known_versions)
            references = [
                self.materialize(reference)
                for reference in response["references"]
            ]
        result = dict(response)
        result["references"] = references
        self._append_startup_decision_log(response, references, known_versions)
        self._store_startup_index(
            [str(reference["xid"]) for reference in references]
        )
        return result

    def startup_decision_log_path(self) -> Path:
        return self.cache_dir / "_startup_decisions.jsonl"

    def startup_decision_log_entries(self) -> list[dict[str, Any]]:
        try:
            lines = self.startup_decision_log_path().read_text(
                encoding="utf-8"
            ).splitlines()
        except FileNotFoundError:
            return []
        entries: list[dict[str, Any]] = []
        for line in lines:
            if not line.strip():
                continue
            entries.append(json.loads(line))
        return entries

    def _append_startup_decision_log(
        self,
        response: dict[str, Any],
        references: list[dict[str, Any]],
        known_versions: dict[str, str],
    ) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        startup_contract_pack = response.get("startup_contract_pack")
        source_xids = _string_list(
            startup_contract_pack.get("source_xids")
            if isinstance(startup_contract_pack, dict)
            else None
        )
        load_order_xids = _string_list(response.get("load_order"))
        entry = {
            "schema_version": 1,
            "event": "startup_xid_decision",
            "logged_at": datetime.now(UTC).isoformat(),
            "repository_fingerprint": self.repository_fingerprint,
            "known_version_xids": sorted(known_versions),
            "load_order_xids": load_order_xids,
            "startup_contract_pack_source_xids": source_xids,
            "reference_xids": [str(reference["xid"]) for reference in references],
            "client_decision_xids": _unique_strings(
                [
                    *load_order_xids,
                    *source_xids,
                    *(str(reference["xid"]) for reference in references),
                ]
            ),
        }
        with self.startup_decision_log_path().open(
            mode="a",
            encoding="utf-8",
        ) as log_file:
            log_file.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
            log_file.write("\n")

    def _store_startup_index(self, xids: list[str]) -> None:
        for xid in xids:
            self._validate_xid(xid)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(
            {
                "schema_version": 1,
                "repository_fingerprint": self.repository_fingerprint,
                "xids": xids,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        self._write_atomic(self._startup_index_path(), serialized)

    def _write_atomic(self, target: Path, serialized: str) -> None:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.cache_dir,
                prefix=f".{target.stem}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(serialized)
                temporary_path = Path(temporary.name)
            temporary_path.replace(target)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    def evict(self, xid: str) -> None:
        path = self._entry_path(xid)
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    async def resolve(
        self,
        xid: str,
        fetch_document: Callable[[str, str | None], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        cached = self.load(xid)
        known_version = cached["content_hash"] if cached else None
        response = await fetch_document(xid, known_version)

        if response.get("cache_status") == "not_modified":
            try:
                return self.materialize(response)
            except DocumentCacheProtocolError:
                response = await fetch_document(xid, None)

        return self.materialize(response)

    def materialize(self, response: dict[str, Any]) -> dict[str, Any]:
        xid = str(response.get("xid", ""))
        self._validate_xid(xid)
        if (
            response.get("repository_fingerprint")
            != self.repository_fingerprint
        ):
            raise DocumentCacheProtocolError(
                "response repository fingerprint does not match cache namespace"
            )
        if response.get("included_in_startup_contract_pack") is True:
            result = dict(response)
            result["client_cache_status"] = "startup_contract_pack"
            return result
        if response.get("cache_status") == "not_modified":
            cached = self.load(xid)
            if cached is None:
                raise DocumentCacheProtocolError(
                    "document response omitted content without a usable cache entry"
                )
            result = dict(cached)
            result.update(response)
            result["content"] = cached["content"]
            result["content_omitted"] = False
            result["client_cache_status"] = "hit"
            return result

        if "content" not in response:
            raise DocumentCacheProtocolError(
                "document response omitted content without a usable cache entry"
            )
        stored = self.store(response)
        result = dict(response)
        result["client_cache_status"] = "refreshed" if stored else "bypassed"
        return result

    def _entry_path(self, xid: str) -> Path:
        self._validate_xid(xid)
        return self.cache_dir / f"{xid}.json"

    def _startup_index_path(self) -> Path:
        return self.cache_dir / "_startup.json"

    @staticmethod
    def _validate_xid(xid: str) -> None:
        if not XID_PATTERN.fullmatch(xid):
            raise ValueError(f"invalid XID for cache key: {xid!r}")


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _unique_strings(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result

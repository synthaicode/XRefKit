from __future__ import annotations

import fnmatch
import json
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .repository import stable_hash


class OwnershipError(ValueError):
    pass


@dataclass(frozen=True)
class Zone:
    id: str
    owner: str
    paths: tuple[str, ...]
    catalog: bool
    distribution: bool
    base_sync: bool
    shadowing: bool

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["paths"] = list(self.paths)
        return data


@dataclass(frozen=True)
class Ownership:
    zones: tuple[Zone, ...]

    @property
    def content_hash(self) -> str:
        return stable_hash(json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")))

    def zone_for(self, rel_path: str) -> Zone | None:
        normalized = _normalize_rel_path(rel_path)
        for zone in self.zones:
            if any(_matches(pattern, normalized) for pattern in zone.paths):
                return zone
        return None

    def catalog_enabled(self, rel_path: str) -> bool:
        zone = self.zone_for(rel_path)
        return True if zone is None else zone.catalog

    def distribution_enabled(self, rel_path: str) -> bool:
        zone = self.zone_for(rel_path)
        return True if zone is None else zone.distribution

    def metadata_for(self, rel_path: str) -> dict[str, Any]:
        zone = self.zone_for(rel_path)
        if zone is None:
            return {
                "zone": None,
                "owner": None,
                "pack_id": _pack_id(rel_path),
                "local_only": False,
                "catalog": True,
                "distribution": True,
                "shadowing": False,
            }
        return {
            "zone": zone.id,
            "owner": zone.owner,
            "pack_id": _pack_id(rel_path),
            "local_only": zone.owner == "local" or zone.id == "local-packs",
            "catalog": zone.catalog,
            "distribution": zone.distribution,
            "shadowing": zone.shadowing,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"zones": [zone.to_dict() for zone in self.zones]}


def load_ownership(root: str | Path, filename: str = "ownership.yaml") -> Ownership | None:
    path = Path(root) / filename
    if not path.exists():
        return None
    parsed = _parse_simple_yaml(path.read_text(encoding="utf-8"))
    zones = parsed.get("zones")
    if not isinstance(zones, list):
        raise OwnershipError("ownership.yaml must contain a zones list")
    result: list[Zone] = []
    seen: set[str] = set()
    for index, raw in enumerate(zones):
        if not isinstance(raw, dict):
            raise OwnershipError(f"zone {index} must be a mapping")
        zone = _zone_from_mapping(raw, index)
        if zone.id in seen:
            raise OwnershipError(f"duplicate zone id: {zone.id}")
        seen.add(zone.id)
        result.append(zone)
    return Ownership(tuple(result))


def validate_ownership(root: str | Path, ownership: Ownership) -> list[str]:
    errors: list[str] = []
    repo = Path(root).resolve()
    for zone in ownership.zones:
        for pattern in zone.paths:
            if not pattern or pattern.startswith("/") or "\\" in pattern:
                errors.append(f"{zone.id}: invalid path pattern `{pattern}`")
                continue
            literal_prefix = pattern.split("*", 1)[0]
            target = (repo / literal_prefix).resolve()
            try:
                target.relative_to(repo)
            except ValueError:
                errors.append(f"{zone.id}: path escapes repository `{pattern}`")
    return errors


def _zone_from_mapping(raw: dict[str, Any], index: int) -> Zone:
    required = ("id", "owner", "paths", "catalog", "distribution", "base_sync", "shadowing")
    missing = [key for key in required if key not in raw]
    if missing:
        raise OwnershipError(f"zone {index} missing fields: {', '.join(missing)}")
    paths = raw["paths"]
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        raise OwnershipError(f"zone {raw.get('id', index)} paths must be a list of strings")
    return Zone(
        id=_as_str(raw["id"], "id"),
        owner=_as_str(raw["owner"], "owner"),
        paths=tuple(_normalize_pattern(path) for path in paths),
        catalog=_as_bool(raw["catalog"], "catalog"),
        distribution=_as_bool(raw["distribution"], "distribution"),
        base_sync=_as_bool(raw["base_sync"], "base_sync"),
        shadowing=_as_bool(raw["shadowing"], "shadowing"),
    )


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    current_list_name: str | None = None
    current_item: dict[str, Any] | None = None
    current_item_list_name: str | None = None
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0:
            if not stripped.endswith(":"):
                raise OwnershipError(f"line {line_number}: top-level value must be a mapping key")
            current_list_name = stripped[:-1]
            root[current_list_name] = []
            current_item = None
            current_item_list_name = None
            continue
        if current_list_name is None:
            raise OwnershipError(f"line {line_number}: nested value before top-level key")
        if indent == 2 and stripped.startswith("- "):
            key, raw_value = _split_key_value(stripped[2:], line_number)
            current_item = {key: _parse_scalar(raw_value)}
            root[current_list_name].append(current_item)
            current_item_list_name = None
            continue
        if indent == 4:
            if current_item is None:
                raise OwnershipError(f"line {line_number}: mapping value before list item")
            key, raw_value = _split_key_value(stripped, line_number)
            if raw_value == "":
                current_item[key] = []
                current_item_list_name = key
            else:
                current_item[key] = _parse_scalar(raw_value)
                current_item_list_name = None
            continue
        if indent == 6 and stripped.startswith("- "):
            if current_item is None or current_item_list_name is None:
                raise OwnershipError(f"line {line_number}: list value without parent key")
            current_item[current_item_list_name].append(_parse_scalar(stripped[2:]))
            continue
        raise OwnershipError(f"line {line_number}: unsupported indentation or syntax")
    return root


def _split_key_value(value: str, line_number: int) -> tuple[str, str]:
    if ":" not in value:
        raise OwnershipError(f"line {line_number}: expected key: value")
    key, raw = value.split(":", 1)
    key = key.strip()
    if not key:
        raise OwnershipError(f"line {line_number}: empty key")
    return key, raw.strip()


def _parse_scalar(value: str) -> str | bool:
    if value == "true":
        return True
    if value == "false":
        return False
    return value.strip("'\"")


def _as_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise OwnershipError(f"{field} must be a non-empty string")
    return value


def _as_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise OwnershipError(f"{field} must be true or false")
    return value


def _normalize_pattern(pattern: str) -> str:
    normalized = pattern.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized and not normalized.endswith("/"):
        normalized += "/"
    return normalized


def _normalize_rel_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    parts = PurePosixPath(normalized).parts
    if any(part == ".." for part in parts):
        return normalized
    return normalized


def _matches(pattern: str, rel_path: str) -> bool:
    if "*" not in pattern:
        return rel_path == pattern.rstrip("/") or rel_path.startswith(pattern)
    return fnmatch.fnmatch(rel_path, pattern + "*")


def _pack_id(rel_path: str) -> str | None:
    parts = PurePosixPath(rel_path.replace("\\", "/")).parts
    if len(parts) >= 2 and parts[0] == "packs":
        if parts[1] == "local" and len(parts) >= 3:
            return f"local/{parts[2]}"
        return parts[1]
    return None

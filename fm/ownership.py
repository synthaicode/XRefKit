from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


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
        return {
            "id": self.id,
            "owner": self.owner,
            "paths": list(self.paths),
            "catalog": self.catalog,
            "distribution": self.distribution,
            "base_sync": self.base_sync,
            "shadowing": self.shadowing,
        }


@dataclass(frozen=True)
class Ownership:
    zones: tuple[Zone, ...]

    def zone_for(self, rel_path: str) -> Zone | None:
        normalized = _normalize_rel_path(rel_path)
        for zone in self.zones:
            if any(_matches(pattern, normalized) for pattern in zone.paths):
                return zone
        return None

    def base_sync_enabled(self, rel_path: str) -> bool:
        zone = self.zone_for(rel_path)
        return True if zone is None else zone.base_sync

    def catalog_enabled(self, rel_path: str) -> bool:
        zone = self.zone_for(rel_path)
        return True if zone is None else zone.catalog

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
    result = []
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


def load_optional_ownership(root: str | Path) -> Ownership | None:
    ownership = load_ownership(root)
    if ownership is None:
        return None
    errors = validate_ownership(root, ownership)
    if errors:
        raise OwnershipError("; ".join(errors))
    return ownership


def content_files(
    root: str | Path,
    family: str,
    pattern: str,
    *,
    ownership: Ownership | None = None,
) -> list[Path]:
    repo = Path(root).resolve()
    paths: list[Path] = []
    base = repo / family
    if base.exists():
        paths.extend(
            path
            for path in sorted(base.glob(f"**/{pattern}"))
            if _catalog_enabled(repo, ownership, path)
        )
    packs_root = repo / "packs"
    if ownership is not None and packs_root.exists():
        paths.extend(
            path
            for path in sorted(packs_root.glob(f"*/{family}/**/{pattern}"))
            if _catalog_enabled(repo, ownership, path)
        )
        paths.extend(
            path
            for path in sorted(packs_root.glob(f"local/*/{family}/**/{pattern}"))
            if _catalog_enabled(repo, ownership, path)
        )
    return sorted(set(paths))


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
            value = stripped[2:]
            if ":" not in value:
                raise OwnershipError(f"line {line_number}: list item must start a mapping")
            key, raw_value = _split_key_value(value, line_number)
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
            value = _parse_scalar(stripped[2:])
            if not isinstance(current_item[current_item_list_name], list):
                raise OwnershipError(f"line {line_number}: parent is not a list")
            current_item[current_item_list_name].append(value)
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


def _catalog_enabled(root: Path, ownership: Ownership | None, path: Path) -> bool:
    if ownership is None:
        return True
    rel = path.relative_to(root).as_posix()
    return ownership.catalog_enabled(rel)

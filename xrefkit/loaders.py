"""Filesystem loaders for XRefKit v2 MVP assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

from .models import LocalDomainSkill, LocalManifest, PackageManifest, SkillDefinition, XRefKitServerConfig

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - used on Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]


ModelT = TypeVar("ModelT", bound=BaseModel)


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    return data


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain an object")
    return data


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a table")
    return data


def _load_model(path: Path, model_type: type[ModelT]) -> ModelT:
    suffix = path.suffix.lower()
    if suffix == ".toml":
        data = _read_toml(path)
    elif suffix in {".yaml", ".yml"}:
        data = _read_yaml(path)
    elif suffix == ".json":
        data = _read_json(path)
    else:
        raise ValueError(f"unsupported file extension for {path}")
    return model_type.model_validate(data)


def load_server_config(path: str | Path) -> XRefKitServerConfig:
    return _load_model(Path(path), XRefKitServerConfig)


def load_package_manifest(path: str | Path) -> PackageManifest:
    return _load_model(Path(path), PackageManifest)


def load_skill_definition(path: str | Path) -> SkillDefinition:
    return _load_model(Path(path), SkillDefinition)


def load_local_manifest(path: str | Path) -> LocalManifest:
    return _load_model(Path(path), LocalManifest)


def load_local_domain_skill(path: str | Path) -> LocalDomainSkill:
    return _load_model(Path(path), LocalDomainSkill)

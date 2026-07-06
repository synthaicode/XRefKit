"""Python entry point discovery for installed XRefKit Skill Packages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from importlib import metadata

from .loaders import load_package_manifest
from .models import PackageManifest


ENTRY_POINT_GROUP = "xrefkit.skill_packages"


@dataclass(frozen=True)
class DiscoveredSkillPackage:
    entry_point_name: str
    package_root: Path
    manifest_path: Path
    manifest: PackageManifest

    @property
    def package_id(self) -> str:
        return self.manifest.package_id

    @property
    def version(self) -> str:
        return self.manifest.version


def _select_entry_points(group: str) -> Iterable[metadata.EntryPoint]:
    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        return entry_points.select(group=group)
    return entry_points.get(group, [])  # type: ignore[union-attr]


def discover_skill_packages(group: str = ENTRY_POINT_GROUP) -> list[DiscoveredSkillPackage]:
    discovered: list[DiscoveredSkillPackage] = []
    for entry_point in _select_entry_points(group):
        package_root_factory = entry_point.load()
        if not callable(package_root_factory):
            raise ValueError(f"entry point {entry_point.name} did not load a callable")
        package_root = Path(package_root_factory())
        manifest_path = package_root / "package_manifest.yaml"
        manifest = load_package_manifest(manifest_path)
        discovered.append(
            DiscoveredSkillPackage(
                entry_point_name=entry_point.name,
                package_root=package_root,
                manifest_path=manifest_path,
                manifest=manifest,
            )
        )
    return discovered


def enabled_discovered_packages(
    *,
    enabled_package_ids: set[str],
    discovered: list[DiscoveredSkillPackage] | None = None,
) -> list[DiscoveredSkillPackage]:
    candidates = discovered if discovered is not None else discover_skill_packages()
    return [candidate for candidate in candidates if candidate.package_id in enabled_package_ids]


def package_list_rows(
    *,
    enabled_package_ids: set[str],
    discovered: list[DiscoveredSkillPackage] | None = None,
) -> list[dict]:
    candidates = discovered if discovered is not None else discover_skill_packages()
    return [
        {
            "entry_point": candidate.entry_point_name,
            "package_id": candidate.package_id,
            "version": candidate.version,
            "manifest_path": str(candidate.manifest_path),
            "enabled": candidate.package_id in enabled_package_ids,
        }
        for candidate in candidates
    ]

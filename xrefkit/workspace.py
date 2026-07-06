"""Workspace assembly helpers for XRefKit v2 MVP."""

from __future__ import annotations

from pathlib import Path

from .discovery import enabled_discovered_packages
from .loaders import load_local_manifest
from .loaders import load_local_domain_skill, load_package_manifest, load_skill_definition
from .registry import XRefKitRegistry


def build_registry(
    *,
    package_manifests: list[str | Path],
    local_manifest_path: str | Path | None = None,
    discover_entry_points: bool = False,
    enabled_package_ids: set[str] | None = None,
) -> XRefKitRegistry:
    registry = XRefKitRegistry()
    manifest_paths = [Path(path) for path in package_manifests]
    if discover_entry_points:
        enabled = enabled_package_ids or set()
        manifest_paths.extend(candidate.manifest_path for candidate in enabled_discovered_packages(enabled_package_ids=enabled))

    for manifest_path in manifest_paths:
        manifest_path = Path(manifest_path)
        manifest = load_package_manifest(manifest_path)
        package_root = manifest_path.parent
        registry.add_package(manifest, package_root)
        for provided in manifest.provides.skills:
            skill_path = package_root / provided.path
            registry.add_package_skill(
                package_id=manifest.package_id,
                skill=load_skill_definition(skill_path),
                path=skill_path,
                root=package_root,
            )
        registry.add_package_knowledge_from_manifest(manifest, package_root)
    if local_manifest_path is not None:
        local_manifest_path = Path(local_manifest_path)
        local_manifest = load_local_manifest(local_manifest_path)
        local_root = local_manifest_path.parent
        registry.add_local_manifest_assets(local_root, local_manifest)
        for mount in local_manifest.mounts.skills:
            skill_path = local_root / mount.path
            registry.add_local_skill(
                skill=load_local_domain_skill(skill_path),
                path=skill_path,
                root=local_root,
                local_id=local_manifest.local_id,
            )
    return registry

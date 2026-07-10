"""Workspace assembly helpers for XRefKit v2 MVP."""

from __future__ import annotations

from pathlib import Path

from .discovery import enabled_discovered_packages
from .loaders import load_local_manifest
from .loaders import load_local_domain_skill, load_package_manifest, load_skill_definition
from .registry import XRefKitRegistry
from .models.common import version_satisfies


CORE_PROTOCOL_VERSION = "2.0.0"


def _contained_path(root: Path, relative_path: str, *, label: str) -> Path:
    root = root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes root: {relative_path}") from exc
    return candidate


def _validate_skill_paths(root: Path, skill) -> None:
    _contained_path(root, skill.entry.path, label="skill entry")
    for fragment in skill.required_fragments:
        _contained_path(root, fragment.path, label=f"skill fragment {fragment.id}")
    for branch in skill.branches:
        _contained_path(root, branch.path, label=f"skill branch {branch.id}")


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
        manifest_path = Path(manifest_path).resolve()
        manifest = load_package_manifest(manifest_path)
        package_root = manifest_path.parent.resolve()
        if not version_satisfies(CORE_PROTOCOL_VERSION, manifest.requires.xrefkit_core):
            raise ValueError(
                f"package {manifest.package_id} requires XRefKit core {manifest.requires.xrefkit_core}, "
                f"current core is {CORE_PROTOCOL_VERSION}"
            )
        for asset_group in (
            manifest.provides.skills,
            manifest.provides.fragments,
            manifest.provides.knowledge,
            manifest.provides.review_axes,
            manifest.provides.schemas,
            manifest.provides.templates,
        ):
            for asset in asset_group:
                _contained_path(package_root, asset.path, label=f"package asset {asset.id}")
        registry.add_package(manifest, package_root)
        for provided in manifest.provides.skills:
            skill_path = _contained_path(package_root, provided.path, label=f"package skill {provided.id}")
            skill = load_skill_definition(skill_path)
            _validate_skill_paths(package_root, skill)
            registry.add_package_skill(
                package_id=manifest.package_id,
                skill=skill,
                path=skill_path,
                root=package_root,
            )
        registry.add_package_knowledge_from_manifest(manifest, package_root)
    if local_manifest_path is not None:
        local_manifest_path = Path(local_manifest_path).resolve()
        local_manifest = load_local_manifest(local_manifest_path)
        local_root = local_manifest_path.parent.resolve()
        if not version_satisfies(CORE_PROTOCOL_VERSION, local_manifest.requires.xrefkit_core):
            raise ValueError(
                f"local manifest requires XRefKit core {local_manifest.requires.xrefkit_core}, "
                f"current core is {CORE_PROTOCOL_VERSION}"
            )
        for asset_group in (
            local_manifest.mounts.knowledge,
            local_manifest.mounts.templates,
            local_manifest.mounts.schemas,
            local_manifest.mounts.review_axes,
        ):
            for asset in asset_group:
                _contained_path(local_root, asset.path, label=f"local asset {asset.id}")
        for mount in local_manifest.mounts.skills:
            _contained_path(local_root, mount.path, label="local skill")
        for requirement in local_manifest.requires.skill_packages:
            package = registry.packages.get(requirement.package_id)
            if package is None:
                raise ValueError(f"required package is not loaded: {requirement.package_id}")
            if not version_satisfies(package.manifest.version, requirement.version):
                raise ValueError(
                    f"package {requirement.package_id} version {package.manifest.version} "
                    f"does not satisfy local requirement {requirement.version}"
                )
        registry.add_local_manifest_assets(local_root, local_manifest)
        for mount in local_manifest.mounts.skills:
            skill_path = _contained_path(local_root, mount.path, label="local skill")
            skill = load_local_domain_skill(skill_path)
            registry.add_local_skill(
                skill=skill,
                path=skill_path,
                root=local_root,
                local_id=local_manifest.local_id,
            )
    return registry

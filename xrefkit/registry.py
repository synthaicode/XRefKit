"""In-memory registries for XRefKit v2 MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import LocalDomainSkill, LocalManifest, PackageManifest, SkillDefinition


@dataclass(frozen=True)
class XidAssetRecord:
    xid: str
    path: Path
    root: Path
    source_type: str
    asset_type: str
    includeable: bool = False
    package_id: str | None = None
    local_id: str | None = None
    fragment_id: str | None = None


@dataclass(frozen=True)
class PackageRecord:
    manifest: PackageManifest
    root: Path


@dataclass(frozen=True)
class SkillRecord:
    package_id: str | None
    skill_id: str
    xid: str
    definition: SkillDefinition | LocalDomainSkill
    path: Path
    root: Path
    source_type: str
    local_id: str | None = None


@dataclass(frozen=True)
class KnowledgeRecord:
    id: str
    xid: str
    path: Path
    source_type: str
    package_id: str | None = None
    local_id: str | None = None


class XidRegistry:
    def __init__(self) -> None:
        self._items: dict[str, object] = {}

    def add(self, xid: str, record: object) -> None:
        if xid in self._items:
            raise ValueError(f"duplicate XID: {xid}")
        self._items[xid] = record

    def add_if_absent(self, xid: str, record: object) -> None:
        if xid not in self._items:
            self._items[xid] = record

    def get(self, xid: str) -> object | None:
        return self._items.get(xid)

    def require(self, xid: str) -> object:
        record = self.get(xid)
        if record is None:
            raise KeyError(f"unknown XID: {xid}")
        return record

    def require_asset(self, xid: str) -> XidAssetRecord:
        record = self.require(xid)
        if not isinstance(record, XidAssetRecord):
            raise TypeError(f"XID is not a file-backed asset: {xid}")
        return record

    def __contains__(self, xid: str) -> bool:
        return xid in self._items


class PackageRegistry:
    def __init__(self) -> None:
        self._packages: dict[str, PackageRecord] = {}

    def add(self, manifest: PackageManifest, root: str | Path) -> PackageRecord:
        if manifest.package_id in self._packages:
            raise ValueError(f"duplicate package_id: {manifest.package_id}")
        record = PackageRecord(manifest=manifest, root=Path(root))
        self._packages[manifest.package_id] = record
        return record

    def get(self, package_id: str) -> PackageRecord | None:
        return self._packages.get(package_id)

    def require(self, package_id: str) -> PackageRecord:
        record = self.get(package_id)
        if record is None:
            raise KeyError(f"unknown package_id: {package_id}")
        return record

    def list(self) -> list[PackageRecord]:
        return list(self._packages.values())


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, SkillRecord] = {}

    def add(self, record: SkillRecord) -> None:
        if record.skill_id in self._skills:
            raise ValueError(f"duplicate skill_id: {record.skill_id}")
        self._skills[record.skill_id] = record

    def get(self, skill_id: str) -> SkillRecord | None:
        return self._skills.get(skill_id)

    def require(self, skill_id: str) -> SkillRecord:
        record = self.get(skill_id)
        if record is None:
            raise KeyError(f"unknown skill_id: {skill_id}")
        return record

    def list(self) -> list[SkillRecord]:
        return list(self._skills.values())


class KnowledgeRegistry:
    def __init__(self) -> None:
        self._knowledge: dict[str, KnowledgeRecord] = {}

    def add(self, record: KnowledgeRecord) -> None:
        if record.id in self._knowledge:
            raise ValueError(f"duplicate knowledge id: {record.id}")
        self._knowledge[record.id] = record

    def list(self) -> list[KnowledgeRecord]:
        return list(self._knowledge.values())


class XRefKitRegistry:
    def __init__(self) -> None:
        self.packages = PackageRegistry()
        self.skills = SkillRegistry()
        self.knowledge = KnowledgeRegistry()
        self.xids = XidRegistry()

    def add_package(self, manifest: PackageManifest, root: str | Path) -> PackageRecord:
        root = Path(root)
        package = self.packages.add(manifest, root)
        package_assets = (
            ("skill", manifest.provides.skills),
            ("fragment", manifest.provides.fragments),
            ("knowledge", manifest.provides.knowledge),
            ("review_axis", manifest.provides.review_axes),
            ("schema", manifest.provides.schemas),
            ("template", manifest.provides.templates),
        )
        for asset_type, assets in package_assets:
            for asset in assets:
                self.xids.add(
                    asset.xid,
                    XidAssetRecord(
                        xid=asset.xid,
                        path=root / asset.path,
                        root=root,
                        source_type="package",
                        asset_type=asset_type,
                        includeable=asset_type == "fragment",
                        package_id=manifest.package_id,
                        fragment_id=asset.id,
                    ),
                )
        return package

    def add_package_skill(self, *, package_id: str, skill: SkillDefinition, path: str | Path, root: str | Path) -> None:
        root = Path(root)
        package = self.packages.require(package_id)
        if package.root != root:
            raise ValueError(f"package root mismatch for {package_id}")
        self.xids.add_if_absent(
            skill.xid,
            XidAssetRecord(
                xid=skill.xid,
                path=Path(path),
                root=root,
                source_type="package",
                asset_type="skill",
                includeable=False,
                package_id=package_id,
                fragment_id=skill.skill_id,
            ),
        )
        self.xids.add_if_absent(
            skill.entry.xid,
            XidAssetRecord(
                xid=skill.entry.xid,
                path=root / skill.entry.path,
                root=root,
                source_type="package",
                asset_type="fragment",
                includeable=False,
                package_id=package_id,
                fragment_id="entry",
            ),
        )
        for fragment in skill.required_fragments:
            self.xids.add_if_absent(
                fragment.xid,
                XidAssetRecord(
                    xid=fragment.xid,
                    path=root / fragment.path,
                    root=root,
                    source_type="package",
                    asset_type="fragment",
                    includeable=False,
                    package_id=package_id,
                    fragment_id=fragment.id,
                ),
            )
        for branch in skill.branches:
            self.xids.add_if_absent(
                branch.xid,
                XidAssetRecord(
                    xid=branch.xid,
                    path=root / branch.path,
                    root=root,
                    source_type="package",
                    asset_type="fragment",
                    includeable=False,
                    package_id=package_id,
                    fragment_id=branch.id,
                ),
            )
        record = SkillRecord(
            package_id=package_id,
            skill_id=skill.skill_id,
            xid=skill.xid,
            definition=skill,
            path=Path(path),
            root=root,
            source_type="package",
        )
        self.skills.add(record)

    def add_package_knowledge_from_manifest(self, manifest: PackageManifest, root: str | Path) -> None:
        root = Path(root)
        for asset in manifest.provides.knowledge:
            self.knowledge.add(
                KnowledgeRecord(
                    id=asset.id,
                    xid=asset.xid,
                    path=root / asset.path,
                    source_type="package",
                    package_id=manifest.package_id,
                )
            )

    def add_local_manifest_assets(self, local_root: str | Path, manifest: LocalManifest) -> None:
        local_root = Path(local_root)
        local_assets = (
            ("knowledge", manifest.mounts.knowledge),
            ("template", manifest.mounts.templates),
            ("schema", manifest.mounts.schemas),
            ("review_axis", manifest.mounts.review_axes),
        )
        for asset_type, assets in local_assets:
            for asset in assets:
                self.xids.add(
                    asset.xid,
                    XidAssetRecord(
                        xid=asset.xid,
                        path=local_root / asset.path,
                        root=local_root,
                        source_type="local",
                        asset_type=asset_type,
                        includeable=False,
                        local_id=manifest.local_id,
                        fragment_id=asset.id,
                    ),
                )
        for asset in manifest.mounts.knowledge:
            self.knowledge.add(
                KnowledgeRecord(
                    id=asset.id,
                    xid=asset.xid,
                    path=local_root / asset.path,
                    source_type="local",
                    local_id=manifest.local_id,
                )
            )

    def add_local_skill(self, *, skill: LocalDomainSkill, path: str | Path, root: str | Path, local_id: str) -> None:
        root = Path(root)
        self.xids.add(
            skill.xid,
            XidAssetRecord(
                xid=skill.xid,
                path=Path(path),
                root=root,
                source_type="local",
                asset_type="skill",
                includeable=False,
                local_id=local_id,
                fragment_id="local_skill",
            ),
        )
        self.skills.add(
            SkillRecord(
                package_id=None,
                skill_id=skill.skill_id,
                xid=skill.xid,
                definition=skill,
                path=Path(path),
                root=root,
                source_type="local",
                local_id=local_id,
            )
        )

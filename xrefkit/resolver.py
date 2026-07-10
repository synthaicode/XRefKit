"""Effective Skill Bundle resolver for XRefKit v2 MVP."""

from __future__ import annotations

from pathlib import Path

from .hashing import sha256_file
from .models import (
    BundleReferences,
    ConflictEntry,
    DomainKnowledgeCatalogEntry,
    EffectiveSkillBundle,
    LoadReason,
    LoadedTexts,
    LocalDomainSkill,
    SkillDefinition,
    SourceTraceEntry,
    SourceType,
    XidLoadedRef,
)
from .registry import SkillRecord, XidAssetRecord, XRefKitRegistry
from .models.common import version_satisfies


def _split_skill_ref(ref: str) -> tuple[str, str]:
    if "::" not in ref:
        raise ValueError(f"skill ref must use package::skill format: {ref}")
    package_id, skill_id = ref.split("::", 1)
    if not package_id or not skill_id:
        raise ValueError(f"invalid skill ref: {ref}")
    return package_id, skill_id


def _loaded(path: Path, xid: str, reason: LoadReason) -> XidLoadedRef:
    return XidLoadedRef(xid=xid, content_hash=sha256_file(path), load_reason=reason)


def _trace(
    *,
    path: Path,
    root: Path,
    xid: str,
    source_type: SourceType,
    package_id: str | None = None,
    local_id: str | None = None,
    fragment_id: str | None = None,
) -> SourceTraceEntry:
    try:
        rel_path = path.relative_to(root).as_posix()
    except ValueError:
        rel_path = path.as_posix()
    return SourceTraceEntry(
        source_type=source_type,
        xid=xid,
        path=rel_path,
        content_hash=sha256_file(path),
        package_id=package_id,
        local_id=local_id,
        fragment_id=fragment_id,
    )


def _trace_asset(asset: XidAssetRecord) -> SourceTraceEntry:
    return _trace(
        path=asset.path,
        root=asset.root,
        xid=asset.xid,
        source_type=SourceType(asset.source_type),
        package_id=asset.package_id,
        local_id=asset.local_id,
        fragment_id=asset.fragment_id,
    )


class EffectiveSkillResolver:
    def __init__(self, registry: XRefKitRegistry) -> None:
        self.registry = registry

    def resolve_entry(self, skill_id: str) -> EffectiveSkillBundle:
        local_record = self.registry.skills.require(skill_id)
        if not isinstance(local_record.definition, LocalDomainSkill):
            raise ValueError("resolve_entry expects a LocalDomainSkill")

        local_skill = local_record.definition
        extends = local_skill.xrefkit.extends[0]
        package_id, base_skill_id = _split_skill_ref(extends.ref)
        base_record = self.registry.skills.require(base_skill_id)
        if base_record.package_id != package_id:
            raise ValueError(f"extends package mismatch for {extends.ref}")
        if base_record.xid != extends.xid:
            raise ValueError(f"extends XID mismatch for {extends.ref}")
        if not isinstance(base_record.definition, SkillDefinition):
            raise ValueError("extends target must be a package SkillDefinition")

        base_skill = base_record.definition
        package = self.registry.packages.require(package_id)
        if not version_satisfies(package.manifest.version, extends.version):
            raise ValueError(
                f"package version {package.manifest.version} does not satisfy {extends.version}"
            )
        if not package.manifest.contract.can_be_extended_by_local_skill:
            raise ValueError(f"package does not allow local extension: {package_id}")
        if not base_skill.extension_policy.can_be_extended_by_local_skill:
            raise ValueError(f"Skill does not allow local extension: {base_skill.skill_id}")
        loaded_texts = LoadedTexts()
        source_trace: list[SourceTraceEntry] = []
        conflicts: list[ConflictEntry] = []

        self._load_includes(local_skill, loaded_texts, source_trace, conflicts)
        self._load_base_required_texts(base_record, base_skill, loaded_texts, source_trace)
        self._load_local_skill(local_record, local_skill, loaded_texts, source_trace)

        required_outputs = self._merge_required_outputs(base_skill, local_skill)
        references = BundleReferences(
            supporting_skill_refs=[use.ref for use in local_skill.xrefkit.uses],
            knowledge=list(dict.fromkeys(base_skill.required_knowledge + (local_skill.xrefkit.injects.knowledge if local_skill.xrefkit.injects else []))),
            templates=list(dict.fromkeys([local_skill.xrefkit.output.template_xid] if local_skill.xrefkit.output and local_skill.xrefkit.output.template_xid else [])),
            schemas=list(dict.fromkeys(base_skill.schemas + ([local_skill.xrefkit.output.schema_xid] if local_skill.xrefkit.output and local_skill.xrefkit.output.schema_xid else []))),
            review_axes=list(dict.fromkeys(base_skill.review_axes + local_skill.xrefkit.review_axes)),
            branches=[branch.xid for branch in base_skill.branches],
        )
        available_domain_knowledge = self._build_available_domain_knowledge(set(references.knowledge))

        return EffectiveSkillBundle(
            effective_skill_id=local_skill.skill_id,
            resolution_mode="entry",
            base_contracts=[extends.ref],
            loaded_texts=loaded_texts,
            references=references,
            available_domain_knowledge=available_domain_knowledge,
            branches_available=[
                {
                    "id": branch.id,
                    "xid": branch.xid,
                    "load_policy": branch.load_policy,
                    "condition_summary": ", ".join(branch.condition.any_intent),
                }
                for branch in base_skill.branches
            ],
            required_outputs=required_outputs,
            load_policy_applied="entry",
            source_trace=source_trace,
            conflicts=conflicts,
        )

    def _load_includes(
        self,
        local_skill: LocalDomainSkill,
        loaded_texts: LoadedTexts,
        source_trace: list[SourceTraceEntry],
        conflicts: list[ConflictEntry],
    ) -> None:
        seen: set[str] = set()
        for include in local_skill.xrefkit.includes:
            if include.xid in seen:
                conflicts.append(
                    ConflictEntry(
                        severity="info",
                        code="include_skipped_duplicate",
                        message=f"duplicate include skipped: {include.xid}",
                        xids=[include.xid],
                    )
                )
                continue
            seen.add(include.xid)
            asset = self.registry.xids.require_asset(include.xid)
            if asset.asset_type != "fragment" or not asset.includeable:
                raise ValueError(f"includes only accepts fragment assets; xid={include.xid}, actual asset_type={asset.asset_type}")
            loaded_texts.included.append(_loaded(asset.path, include.xid, LoadReason.INCLUDE_FRAGMENT))
            source_trace.append(_trace_asset(asset))

    def _load_base_required_texts(
        self,
        base_record: SkillRecord,
        base_skill: SkillDefinition,
        loaded_texts: LoadedTexts,
        source_trace: list[SourceTraceEntry],
    ) -> None:
        package_id = base_record.package_id
        if package_id is None:
            raise ValueError("base SkillDefinition must belong to a package")

        entry_path = base_record.root / base_skill.entry.path
        loaded_texts.inherited.append(_loaded(entry_path, base_skill.entry.xid, LoadReason.SKILL_ENTRY))
        source_trace.append(
            _trace(
                path=entry_path,
                root=base_record.root,
                xid=base_skill.entry.xid,
                source_type=SourceType.PACKAGE,
                package_id=package_id,
                fragment_id="entry",
            )
        )

        for fragment in base_skill.required_fragments:
            fragment_path = base_record.root / fragment.path
            loaded_texts.inherited.append(_loaded(fragment_path, fragment.xid, LoadReason.REQUIRED_FRAGMENT))
            source_trace.append(
                _trace(
                    path=fragment_path,
                    root=base_record.root,
                    xid=fragment.xid,
                    source_type=SourceType.PACKAGE,
                    package_id=package_id,
                    fragment_id=fragment.id,
                )
            )

    def _load_local_skill(
        self,
        local_record: SkillRecord,
        local_skill: LocalDomainSkill,
        loaded_texts: LoadedTexts,
        source_trace: list[SourceTraceEntry],
    ) -> None:
        loaded_texts.local.append(_loaded(local_record.path, local_skill.xid, LoadReason.LOCAL_SKILL))
        source_trace.append(
            _trace(
                path=local_record.path,
                root=local_record.root,
                xid=local_skill.xid,
                source_type=SourceType.LOCAL,
                local_id=local_record.local_id or local_record.root.name,
                fragment_id="local_skill",
            )
        )

    def _merge_required_outputs(self, base_skill: SkillDefinition, local_skill: LocalDomainSkill) -> list[str]:
        merged = list(dict.fromkeys(base_skill.required_outputs + local_skill.xrefkit.required_outputs))
        missing = set(base_skill.required_outputs) - set(merged)
        if missing:
            raise ValueError(f"local skill weakened required_outputs: {sorted(missing)}")
        return merged

    def _build_available_domain_knowledge(self, selected_xids: set[str]) -> list[DomainKnowledgeCatalogEntry]:
        entries: list[DomainKnowledgeCatalogEntry] = []
        for record in self.registry.knowledge.list():
            selected = record.xid in selected_xids
            entries.append(
                DomainKnowledgeCatalogEntry(
                    id=record.id,
                    xid=record.xid,
                    source_type=SourceType(record.source_type),
                    content_hash=sha256_file(record.path),
                    selected=selected,
                    package_id=record.package_id,
                    local_id=record.local_id,
                    selection_reason="referenced_by_effective_skill" if selected else None,
                )
            )
        return entries

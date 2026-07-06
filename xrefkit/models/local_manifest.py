"""Pydantic models for Project Local manifests and domain skill wrappers."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .common import StrictModel, validate_non_empty, validate_package_id, validate_xid


class RequiredSkillPackage(StrictModel):
    package_id: str
    version: str

    @field_validator("package_id")
    @classmethod
    def _validate_package_id(cls, value: str) -> str:
        return validate_package_id(value)

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        return validate_non_empty(value, "version")


class LocalRequires(StrictModel):
    xrefkit_core: str
    skill_packages: list[RequiredSkillPackage]

    @field_validator("xrefkit_core")
    @classmethod
    def _validate_core_constraint(cls, value: str) -> str:
        return validate_non_empty(value, "xrefkit_core")

    @field_validator("skill_packages")
    @classmethod
    def _validate_skill_packages(cls, values: list[RequiredSkillPackage]) -> list[RequiredSkillPackage]:
        if not values:
            raise ValueError("requires.skill_packages must not be empty")
        package_ids = [item.package_id for item in values]
        if len(package_ids) != len(set(package_ids)):
            raise ValueError("requires.skill_packages contains duplicate package_id values")
        return values


class LocalSkillMount(StrictModel):
    path: str

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        return validate_non_empty(value, "path")


class LocalAssetMount(StrictModel):
    id: str
    xid: str
    path: str

    @field_validator("id", "path")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return validate_non_empty(value, "value")

    @field_validator("xid")
    @classmethod
    def _validate_xid(cls, value: str) -> str:
        return validate_xid(value)


class LocalMounts(StrictModel):
    skills: list[LocalSkillMount] = Field(default_factory=list)
    knowledge: list[LocalAssetMount] = Field(default_factory=list)
    templates: list[LocalAssetMount] = Field(default_factory=list)
    schemas: list[LocalAssetMount] = Field(default_factory=list)
    review_axes: list[LocalAssetMount] = Field(default_factory=list)


class LocalMergePolicy(StrictModel):
    can_extend_core: bool = True
    can_weaken_core: bool = False
    can_weaken_pack_contract: bool = False

    @model_validator(mode="after")
    def _enforce_mvp_policy(self) -> "LocalMergePolicy":
        if self.can_weaken_core:
            raise ValueError("Project Local cannot weaken Core")
        if self.can_weaken_pack_contract:
            raise ValueError("Project Local cannot weaken Pack contracts")
        return self


class LocalManifest(StrictModel):
    local_id: str
    version: str
    type: Literal["project_local"]
    requires: LocalRequires
    mounts: LocalMounts
    merge_policy: LocalMergePolicy
    metadata: dict[str, Any] | None = None
    default_skill: str | None = None

    @field_validator("local_id", "version")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return validate_non_empty(value, "value")

    @model_validator(mode="after")
    def _validate_unique_local_xids(self) -> "LocalManifest":
        assets = self.mounts.knowledge + self.mounts.templates + self.mounts.schemas + self.mounts.review_axes
        xids = [asset.xid for asset in assets]
        if len(xids) != len(set(xids)):
            raise ValueError("LocalManifest contains duplicate local XIDs")
        return self


class ExtendsRef(StrictModel):
    ref: str
    xid: str
    version: str
    mode: Literal["contract_inheritance"]

    @field_validator("ref", "version")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return validate_non_empty(value, "value")

    @field_validator("xid")
    @classmethod
    def _validate_xid(cls, value: str) -> str:
        return validate_xid(value)


class UsesRef(StrictModel):
    ref: str
    version: str
    mode: Literal["supporting_skill"]

    @field_validator("ref", "version")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return validate_non_empty(value, "value")


class InjectsSpec(StrictModel):
    knowledge: list[str] = Field(default_factory=list)

    @field_validator("knowledge")
    @classmethod
    def _validate_knowledge_xids(cls, values: list[str]) -> list[str]:
        return [validate_xid(value) for value in values]


class OutputSpec(StrictModel):
    template_xid: str | None = None
    schema_xid: str | None = None

    @field_validator("template_xid", "schema_xid")
    @classmethod
    def _validate_optional_xid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_xid(value)


class LocalSkillBinding(StrictModel):
    extends: list[ExtendsRef]
    uses: list[UsesRef] = Field(default_factory=list)
    injects: InjectsSpec | None = None
    output: OutputSpec | None = None
    review_axes: list[str] = Field(default_factory=list)
    required_outputs: list[str] = Field(default_factory=list)

    @field_validator("extends")
    @classmethod
    def _validate_single_inheritance(cls, values: list[ExtendsRef]) -> list[ExtendsRef]:
        if len(values) != 1:
            raise ValueError("MVP supports exactly one extends entry")
        return values

    @field_validator("review_axes")
    @classmethod
    def _validate_review_axes(cls, values: list[str]) -> list[str]:
        return [validate_xid(value) for value in values]

    @field_validator("required_outputs")
    @classmethod
    def _validate_required_outputs(cls, values: list[str]) -> list[str]:
        return [validate_non_empty(value, "required_output") for value in values]


class LocalDomainSkill(StrictModel):
    skill_id: str
    xid: str
    type: Literal["domain_skill_wrapper"]
    xrefkit: LocalSkillBinding

    @field_validator("skill_id")
    @classmethod
    def _validate_skill_id(cls, value: str) -> str:
        return validate_non_empty(value, "skill_id")

    @field_validator("xid")
    @classmethod
    def _validate_xid(cls, value: str) -> str:
        return validate_xid(value)

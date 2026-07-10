"""Pydantic model for package_manifest.yaml."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .common import StrictModel, validate_non_empty, validate_package_id, validate_xid


class PackageRequires(StrictModel):
    xrefkit_core: str

    @field_validator("xrefkit_core")
    @classmethod
    def _validate_constraint(cls, value: str) -> str:
        return validate_non_empty(value, "xrefkit_core")


class ProvidedAsset(StrictModel):
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


class ProvidedSkill(ProvidedAsset):
    contract_role: str | None = None
    required_outputs: list[str] = Field(default_factory=list)
    required_knowledge: list[str] = Field(default_factory=list)
    required_review_axes: list[str] = Field(default_factory=list)
    must_not: list[str] = Field(default_factory=list)

    @field_validator("required_outputs", "required_knowledge", "required_review_axes", "must_not")
    @classmethod
    def _validate_string_list(cls, values: list[str]) -> list[str]:
        return [validate_non_empty(value, "list item") for value in values]


class PackageProvides(StrictModel):
    skills: list[ProvidedSkill]
    fragments: list[ProvidedAsset] = Field(default_factory=list)
    knowledge: list[ProvidedAsset] = Field(default_factory=list)
    review_axes: list[ProvidedAsset] = Field(default_factory=list)
    schemas: list[ProvidedAsset] = Field(default_factory=list)
    templates: list[ProvidedAsset] = Field(default_factory=list)

    @field_validator("skills")
    @classmethod
    def _require_skills(cls, values: list[ProvidedSkill]) -> list[ProvidedSkill]:
        if not values:
            raise ValueError("provides.skills must not be empty")
        return values

    @model_validator(mode="after")
    def _validate_asset_ids(self) -> "PackageProvides":
        for name in ("skills", "fragments", "knowledge", "review_axes", "schemas", "templates"):
            assets = getattr(self, name)
            ids = [asset.id for asset in assets]
            if len(ids) != len(set(ids)):
                raise ValueError(f"provides.{name} contains duplicate ids")
        return self


class PackageContract(StrictModel):
    can_be_extended_by_local_skill: bool = True
    local_skill_can_weaken_contract: bool = False
    local_can_weaken_required_outputs: bool = False
    local_can_override_must_not: bool = False
    requires_unknown_declaration: bool = True
    requires_traceability: bool = True

    @model_validator(mode="after")
    def _enforce_mvp_policy(self) -> "PackageContract":
        if self.local_skill_can_weaken_contract:
            raise ValueError("MVP does not allow local skills to weaken package contracts")
        if self.local_can_weaken_required_outputs:
            raise ValueError("MVP does not allow local skills to weaken required outputs")
        if self.local_can_override_must_not:
            raise ValueError("MVP does not allow local skills to override must_not")
        return self


class PackageManifest(StrictModel):
    package_id: str
    package_type: Literal["skill_package"]
    version: str
    requires: PackageRequires
    provides: PackageProvides
    contract: PackageContract
    metadata: dict[str, Any] | None = None

    @field_validator("package_id")
    @classmethod
    def _validate_package_id(cls, value: str) -> str:
        return validate_package_id(value)

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        return validate_non_empty(value, "version")

    @model_validator(mode="after")
    def _validate_unique_xids(self) -> "PackageManifest":
        assets = (
            self.provides.skills
            + self.provides.fragments
            + self.provides.knowledge
            + self.provides.review_axes
            + self.provides.schemas
            + self.provides.templates
        )
        xids = [asset.xid for asset in assets]
        if len(xids) != len(set(xids)):
            raise ValueError("package manifest contains duplicate XIDs")
        return self

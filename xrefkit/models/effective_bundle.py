"""Pydantic model for resolved effective skill bundles."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from .common import ConflictEntry, SourceTraceEntry, SourceType, StrictModel, XidLoadedRef, validate_non_empty, validate_xid


class LoadedTexts(StrictModel):
    core: list[XidLoadedRef] = Field(default_factory=list)
    included: list[XidLoadedRef] = Field(default_factory=list)
    inherited: list[XidLoadedRef] = Field(default_factory=list)
    local: list[XidLoadedRef] = Field(default_factory=list)
    branch: list[XidLoadedRef] = Field(default_factory=list)
    knowledge: list[XidLoadedRef] = Field(default_factory=list)
    output: list[XidLoadedRef] = Field(default_factory=list)

    def all_loaded(self) -> list[XidLoadedRef]:
        return self.core + self.included + self.inherited + self.local + self.branch + self.knowledge + self.output


class BundleReferences(StrictModel):
    supporting_skill_refs: list[str] = Field(default_factory=list)
    knowledge: list[str] = Field(default_factory=list)
    templates: list[str] = Field(default_factory=list)
    schemas: list[str] = Field(default_factory=list)
    review_axes: list[str] = Field(default_factory=list)
    branches: list[str] = Field(default_factory=list)

    @field_validator("knowledge", "templates", "schemas", "review_axes", "branches")
    @classmethod
    def _validate_xids(cls, values: list[str]) -> list[str]:
        return [validate_xid(value) for value in values]

    @field_validator("supporting_skill_refs")
    @classmethod
    def _validate_skill_refs(cls, values: list[str]) -> list[str]:
        return [validate_non_empty(value, "supporting_skill_ref") for value in values]


class BranchSummary(StrictModel):
    id: str
    xid: str
    load_policy: Literal["on_demand"]
    condition_summary: str | None = None

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        return validate_non_empty(value, "id")

    @field_validator("xid")
    @classmethod
    def _validate_xid(cls, value: str) -> str:
        return validate_xid(value)


class DomainKnowledgeCatalogEntry(StrictModel):
    id: str
    xid: str
    source_type: SourceType
    content_hash: str
    selected: bool = False
    package_id: str | None = None
    local_id: str | None = None
    selection_reason: str | None = None

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        return validate_non_empty(value, "id")

    @field_validator("xid")
    @classmethod
    def _validate_xid(cls, value: str) -> str:
        return validate_xid(value)


class EffectiveSkillBundle(StrictModel):
    effective_skill_id: str
    resolution_mode: Literal["entry", "branch", "full"]
    base_contracts: list[str]
    loaded_texts: LoadedTexts
    references: BundleReferences = Field(default_factory=BundleReferences)
    available_domain_knowledge: list[DomainKnowledgeCatalogEntry] = Field(default_factory=list)
    branches_available: list[BranchSummary] = Field(default_factory=list)
    required_outputs: list[str]
    load_policy_applied: str
    source_trace: list[SourceTraceEntry]
    conflicts: list[ConflictEntry] = Field(default_factory=list)
    warnings: list[ConflictEntry] = Field(default_factory=list)

    @field_validator("effective_skill_id", "load_policy_applied")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return validate_non_empty(value, "value")

    @field_validator("base_contracts")
    @classmethod
    def _validate_base_contracts(cls, values: list[str]) -> list[str]:
        if not values:
            raise ValueError("base_contracts must not be empty")
        return [validate_non_empty(value, "base_contract") for value in values]

    @field_validator("required_outputs")
    @classmethod
    def _validate_required_outputs(cls, values: list[str]) -> list[str]:
        if not values:
            raise ValueError("required_outputs must not be empty")
        return [validate_non_empty(value, "required_output") for value in values]

    @field_validator("source_trace")
    @classmethod
    def _validate_source_trace_not_empty(cls, values: list[SourceTraceEntry]) -> list[SourceTraceEntry]:
        if not values:
            raise ValueError("source_trace must not be empty")
        return values

    @model_validator(mode="after")
    def _validate_loaded_xids_are_traced(self) -> "EffectiveSkillBundle":
        traced_xids = {entry.xid for entry in self.source_trace}
        loaded_xids = [entry.xid for entry in self.loaded_texts.all_loaded()]
        missing = sorted(set(loaded_xids) - traced_xids)
        if missing:
            raise ValueError(f"loaded XIDs missing from source_trace: {missing}")
        if self.resolution_mode == "entry" and self.loaded_texts.branch:
            raise ValueError("resolution_mode='entry' must not include loaded branch bodies")
        return self

"""Pydantic model for reusable *.skill.yaml files."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from .common import StrictModel, validate_non_empty, validate_xid


class SkillEntry(StrictModel):
    xid: str
    path: str
    load_policy: Literal["required_inline"]

    @field_validator("xid")
    @classmethod
    def _validate_xid(cls, value: str) -> str:
        return validate_xid(value)

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        return validate_non_empty(value, "path")


class SkillFragment(StrictModel):
    id: str
    xid: str
    path: str
    load_policy: Literal["required_inline"]

    @field_validator("id", "path")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return validate_non_empty(value, "value")

    @field_validator("xid")
    @classmethod
    def _validate_xid(cls, value: str) -> str:
        return validate_xid(value)


class BranchCondition(StrictModel):
    any_intent: list[str]

    @field_validator("any_intent")
    @classmethod
    def _validate_any_intent(cls, values: list[str]) -> list[str]:
        if not values:
            raise ValueError("branch condition any_intent must not be empty")
        return [validate_non_empty(value, "intent") for value in values]


class SkillBranch(StrictModel):
    id: str
    xid: str
    path: str
    condition: BranchCondition
    load_policy: Literal["on_demand"]

    @field_validator("id", "path")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return validate_non_empty(value, "value")

    @field_validator("xid")
    @classmethod
    def _validate_xid(cls, value: str) -> str:
        return validate_xid(value)


class SkillExtensionPolicy(StrictModel):
    can_be_extended_by_local_skill: bool = True
    local_can_weaken_required_outputs: bool = False
    local_can_override_must_not: bool = False

    @model_validator(mode="after")
    def _enforce_mvp_policy(self) -> "SkillExtensionPolicy":
        if self.local_can_weaken_required_outputs:
            raise ValueError("MVP does not allow local skills to weaken required outputs")
        if self.local_can_override_must_not:
            raise ValueError("MVP does not allow local skills to override must_not")
        return self


class SkillDefinition(StrictModel):
    skill_id: str
    xid: str
    role: str | None = None
    entry: SkillEntry
    required_fragments: list[SkillFragment] = Field(default_factory=list)
    branches: list[SkillBranch] = Field(default_factory=list)
    required_outputs: list[str]
    required_knowledge: list[str] = Field(default_factory=list)
    review_axes: list[str] = Field(default_factory=list)
    schemas: list[str] = Field(default_factory=list)
    must_not: list[str] = Field(default_factory=list)
    extension_policy: SkillExtensionPolicy

    @field_validator("skill_id")
    @classmethod
    def _validate_skill_id(cls, value: str) -> str:
        return validate_non_empty(value, "skill_id")

    @field_validator("xid")
    @classmethod
    def _validate_xid(cls, value: str) -> str:
        return validate_xid(value)

    @field_validator("required_outputs")
    @classmethod
    def _validate_required_outputs(cls, values: list[str]) -> list[str]:
        if not values:
            raise ValueError("required_outputs must not be empty")
        return [validate_non_empty(value, "required_output") for value in values]

    @field_validator("required_knowledge", "review_axes", "schemas", "must_not")
    @classmethod
    def _validate_string_list(cls, values: list[str]) -> list[str]:
        return [validate_non_empty(value, "list item") for value in values]

    @model_validator(mode="after")
    def _validate_unique_xids(self) -> "SkillDefinition":
        xids = [self.xid, self.entry.xid]
        xids.extend(fragment.xid for fragment in self.required_fragments)
        xids.extend(branch.xid for branch in self.branches)
        if len(xids) != len(set(xids)):
            raise ValueError("SkillDefinition contains duplicate XIDs")
        return self

"""Common Pydantic model primitives for XRefKit v2 MVP."""

from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


XID_PATTERN = re.compile(r"^\S+$")
PACKAGE_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+$")
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


class StrictModel(BaseModel):
    """Base model that rejects unexpected fields."""

    model_config = ConfigDict(extra="forbid")


class CoreProtocol(str, Enum):
    UNKNOWN_PROTOCOL = "unknown_protocol"
    WORKFLOW_PROTOCOL = "workflow_protocol"
    CONTEXT_DIRECTION_SECURITY_GUARD = "context_direction_security_guard"
    STARTUP_XREF_ROUTING = "startup_xref_routing"
    XREFKIT_STARTUP_CONTRACT = "xrefkit_startup_contract"


class LoadReason(str, Enum):
    CORE_CONTRACT = "core_contract"
    INHERITED_CONTRACT = "inherited_contract"
    SKILL_ENTRY = "skill_entry"
    REQUIRED_FRAGMENT = "required_fragment"
    BRANCH = "branch"
    LOCAL_SKILL = "local_skill"
    OUTPUT_TEMPLATE = "output_template"
    SCHEMA = "schema"
    KNOWLEDGE_ON_DEMAND = "knowledge_on_demand"
    HUMAN_FULL_MATERIALIZE = "human_full_materialize"


class SourceType(str, Enum):
    CORE = "core"
    PACKAGE = "package"
    LOCAL = "local"


class ConflictSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


def validate_xid(value: str) -> str:
    if not value or not XID_PATTERN.match(value):
        raise ValueError("XID must be a non-empty string without whitespace")
    return value


def validate_package_id(value: str) -> str:
    if not value or not PACKAGE_ID_PATTERN.match(value):
        raise ValueError("package_id must be a dot-separated stable package id")
    return value


def validate_content_hash(value: str) -> str:
    if not SHA256_PATTERN.match(value):
        raise ValueError("content_hash must use sha256:<64 hex chars> format")
    return value


def validate_non_empty(value: str, field_name: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    return value


class XidRef(StrictModel):
    xid: str

    @field_validator("xid")
    @classmethod
    def _validate_xid(cls, value: str) -> str:
        return validate_xid(value)


class XidLoadedRef(XidRef):
    content_hash: str
    load_reason: LoadReason

    @field_validator("content_hash")
    @classmethod
    def _validate_content_hash(cls, value: str) -> str:
        return validate_content_hash(value)


class SourceTraceEntry(XidRef):
    source_type: SourceType
    path: str
    content_hash: str
    package_id: str | None = None
    local_id: str | None = None
    fragment_id: str | None = None

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        return validate_non_empty(value, "path")

    @field_validator("content_hash")
    @classmethod
    def _validate_content_hash(cls, value: str) -> str:
        return validate_content_hash(value)

    @field_validator("package_id")
    @classmethod
    def _validate_package_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_package_id(value)

    @model_validator(mode="after")
    def _require_source_identity(self) -> "SourceTraceEntry":
        if self.source_type == SourceType.PACKAGE and not self.package_id:
            raise ValueError("package source_trace entries require package_id")
        if self.source_type == SourceType.LOCAL and not self.local_id:
            raise ValueError("local source_trace entries require local_id")
        return self


class ConflictEntry(StrictModel):
    severity: ConflictSeverity
    code: str
    message: str
    xids: list[str] = Field(default_factory=list)

    @field_validator("code", "message")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return validate_non_empty(value, "value")

    @field_validator("xids")
    @classmethod
    def _validate_xids(cls, values: list[str]) -> list[str]:
        return [validate_xid(value) for value in values]


class WarningEntry(ConflictEntry):
    severity: Literal[ConflictSeverity.WARNING] = ConflictSeverity.WARNING

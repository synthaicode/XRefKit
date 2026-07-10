"""Pydantic models for canonical JSONL run log events."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import Field, field_validator, model_validator

from .common import SourceTraceEntry, StrictModel, XidLoadedRef, validate_content_hash, validate_non_empty, validate_xid


class Requester(StrictModel):
    type: Literal["client_ip", "user_id"]
    client_ip: str | None = None
    user_id: str | None = None
    identity_assurance: str

    @field_validator("identity_assurance")
    @classmethod
    def _validate_identity_assurance(cls, value: str) -> str:
        return validate_non_empty(value, "identity_assurance")

    @model_validator(mode="after")
    def _validate_identity(self) -> "Requester":
        if self.type == "client_ip" and not self.client_ip:
            raise ValueError("requester.client_ip is required when requester.type='client_ip'")
        if self.type == "user_id" and not self.user_id:
            raise ValueError("requester.user_id is required when requester.type='user_id'")
        return self


class Actor(StrictModel):
    type: str
    client_name: str | None = None
    session_id: str | None = None

    @field_validator("type")
    @classmethod
    def _validate_type(cls, value: str) -> str:
        return validate_non_empty(value, "type")


class RunRequest(StrictModel):
    operation: str
    skill_id: str | None = None

    @field_validator("operation")
    @classmethod
    def _validate_operation(cls, value: str) -> str:
        return validate_non_empty(value, "operation")


class RunLogEventBase(StrictModel):
    run_id: str
    event_type: str
    timestamp: datetime

    @field_validator("run_id")
    @classmethod
    def _validate_run_id(cls, value: str) -> str:
        return validate_non_empty(value, "run_id")


class RunStartEvent(RunLogEventBase):
    event_type: Literal["run.start"]
    requester: Requester
    actor: Actor | None = None
    request: RunRequest


class ContextResolvedEvent(RunLogEventBase):
    event_type: Literal["context.resolved"]
    effective_skill_id: str
    resolution_mode: Literal["entry", "branch", "full"]
    source_trace: list[SourceTraceEntry]
    bundle_hash: str | None = None

    @field_validator("effective_skill_id")
    @classmethod
    def _validate_effective_skill_id(cls, value: str) -> str:
        return validate_non_empty(value, "effective_skill_id")

    @field_validator("bundle_hash")
    @classmethod
    def _validate_bundle_hash(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_content_hash(value)


class XidsReferencedEvent(RunLogEventBase):
    event_type: Literal["xids.referenced"]
    referenced_xids: list[str]

    @field_validator("referenced_xids")
    @classmethod
    def _validate_xids(cls, values: list[str]) -> list[str]:
        return [validate_xid(value) for value in values]


class XidsLoadedEvent(RunLogEventBase):
    event_type: Literal["xids.loaded"]
    loaded_xids: list[XidLoadedRef]


class XidsUsedEvent(RunLogEventBase):
    event_type: Literal["xids.used"]
    used_xids: list[str]

    @field_validator("used_xids")
    @classmethod
    def _validate_xids(cls, values: list[str]) -> list[str]:
        return [validate_xid(value) for value in values]


class UnknownsReportedEvent(RunLogEventBase):
    event_type: Literal["unknowns.reported"]
    unknowns: list[str]

    @field_validator("unknowns")
    @classmethod
    def _validate_unknowns(cls, values: list[str]) -> list[str]:
        return [validate_non_empty(value, "unknown") for value in values]


class AssumptionsReportedEvent(RunLogEventBase):
    event_type: Literal["assumptions.reported"]
    assumptions: list[str]

    @field_validator("assumptions")
    @classmethod
    def _validate_assumptions(cls, values: list[str]) -> list[str]:
        return [validate_non_empty(value, "assumption") for value in values]


class BranchLoadedEvent(RunLogEventBase):
    event_type: Literal["branch.loaded"]
    branch_xid: str
    loaded_xids: list[XidLoadedRef] = Field(default_factory=list)

    @field_validator("branch_xid")
    @classmethod
    def _validate_branch_xid(cls, value: str) -> str:
        return validate_xid(value)


class ConflictDetectedEvent(RunLogEventBase):
    event_type: Literal["conflict.detected"]
    severity: Literal["error", "warning", "info"]
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


class RunResult(StrictModel):
    status: Literal["completed", "completed_with_unknowns", "failed", "blocked"]
    contract_passed: bool
    required_outputs_present: bool | None = None
    unknowns_count: int | None = None
    assumptions_count: int | None = None
    message: str | None = None

    @field_validator("unknowns_count", "assumptions_count")
    @classmethod
    def _validate_counts(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("counts must be zero or greater")
        return value


class RunCompleteEvent(RunLogEventBase):
    event_type: Literal["run.complete"]
    result: RunResult


RunLogEvent = Annotated[
    Union[
        RunStartEvent,
        ContextResolvedEvent,
        XidsReferencedEvent,
        XidsLoadedEvent,
        XidsUsedEvent,
        UnknownsReportedEvent,
        AssumptionsReportedEvent,
        BranchLoadedEvent,
        ConflictDetectedEvent,
        RunCompleteEvent,
    ],
    Field(discriminator="event_type"),
]


class RunLogAggregate(StrictModel):
    run_id: str
    events: list[RunLogEvent]

    @field_validator("run_id")
    @classmethod
    def _validate_run_id(cls, value: str) -> str:
        return validate_non_empty(value, "run_id")

    @field_validator("events")
    @classmethod
    def _validate_events_not_empty(cls, values: list[RunLogEvent]) -> list[RunLogEvent]:
        if not values:
            raise ValueError("events must not be empty")
        return values

    @model_validator(mode="after")
    def _validate_run_consistency(self) -> "RunLogAggregate":
        for event in self.events:
            if event.run_id != self.run_id:
                raise ValueError("all run log events must share the aggregate run_id")

        if not any(isinstance(event, RunStartEvent) for event in self.events):
            raise ValueError("run.start event is required")

        complete_count = sum(1 for event in self.events if isinstance(event, RunCompleteEvent))
        if complete_count > 1:
            raise ValueError("run.complete may appear at most once")

        timestamps = [event.timestamp for event in self.events]
        if timestamps != sorted(timestamps):
            raise ValueError("run log events must be ordered by timestamp")

        loaded_xids: set[str] = set()
        used_xids: set[str] = set()
        for event in self.events:
            if isinstance(event, XidsLoadedEvent):
                loaded_xids.update(item.xid for item in event.loaded_xids)
            elif isinstance(event, BranchLoadedEvent):
                loaded_xids.update(item.xid for item in event.loaded_xids)
            elif isinstance(event, XidsUsedEvent):
                used_xids.update(event.used_xids)

        missing = sorted(used_xids - loaded_xids)
        if missing:
            raise ValueError(f"used_xids must be a subset of loaded_xids; missing: {missing}")
        return self

    @property
    def referenced_xids(self) -> set[str]:
        values: set[str] = set()
        for event in self.events:
            if isinstance(event, XidsReferencedEvent):
                values.update(event.referenced_xids)
        return values

    @property
    def loaded_xids(self) -> set[str]:
        values: set[str] = set()
        for event in self.events:
            if isinstance(event, XidsLoadedEvent):
                values.update(item.xid for item in event.loaded_xids)
            elif isinstance(event, BranchLoadedEvent):
                values.update(item.xid for item in event.loaded_xids)
        return values

    @property
    def used_xids(self) -> set[str]:
        values: set[str] = set()
        for event in self.events:
            if isinstance(event, XidsUsedEvent):
                values.update(event.used_xids)
        return values

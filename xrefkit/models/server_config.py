"""Pydantic model for xrefkit.server.toml."""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from .common import CoreProtocol, StrictModel, validate_non_empty, validate_package_id


class CoreConfig(StrictModel):
    package: str
    version_constraint: str
    startup_contract: str
    protocols: list[CoreProtocol]

    @field_validator("package", "version_constraint", "startup_contract")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        return validate_non_empty(value, "value")

    @field_validator("protocols")
    @classmethod
    def _validate_protocols(cls, values: list[CoreProtocol]) -> list[CoreProtocol]:
        if not values:
            raise ValueError("core.protocols must not be empty")
        if len(set(values)) != len(values):
            raise ValueError("core.protocols must not contain duplicates")
        return values


class DiscoveryConfig(StrictModel):
    python_entry_points: bool = True
    filesystem_mounts: bool = True


class EnabledPackagesConfig(StrictModel):
    enabled: list[str] = Field(default_factory=list)

    @field_validator("enabled")
    @classmethod
    def _validate_enabled(cls, values: list[str]) -> list[str]:
        if len(set(values)) != len(values):
            raise ValueError("packages.enabled must not contain duplicates")
        return [validate_package_id(value) for value in values]


class LocalMountConfig(StrictModel):
    path: str | None = None
    required: bool = False

    @model_validator(mode="after")
    def _require_path_when_required(self) -> "LocalMountConfig":
        if self.required and not self.path:
            raise ValueError("local.path is required when local.required is true")
        return self


class MergePolicyConfig(StrictModel):
    local_can_weaken_core: bool = False
    local_can_weaken_pack_contract: bool = False
    conflict_as_error: bool = True
    require_source_trace: bool = True

    @model_validator(mode="after")
    def _enforce_mvp_policy(self) -> "MergePolicyConfig":
        if self.local_can_weaken_core:
            raise ValueError("MVP does not allow Project Local to weaken Core")
        if self.local_can_weaken_pack_contract:
            raise ValueError("MVP does not allow Project Local to weaken Pack contracts")
        return self


class ServerLoadPolicyConfig(StrictModel):
    default_knowledge: str = "reference_then_inline"
    default_branch: str = "on_demand"
    human_full_materialize: bool = True

    @field_validator("default_knowledge")
    @classmethod
    def _validate_default_knowledge(cls, value: str) -> str:
        allowed = {"reference_then_inline", "startup_reference", "on_demand", "required_inline"}
        if value not in allowed:
            raise ValueError(f"default_knowledge must be one of {sorted(allowed)}")
        return value

    @field_validator("default_branch")
    @classmethod
    def _validate_default_branch(cls, value: str) -> str:
        if value != "on_demand":
            raise ValueError("MVP only supports default_branch='on_demand'")
        return value


class LoggingConfig(StrictModel):
    run_log_enabled: bool = True
    include_loaded_xids: bool = True
    include_used_xids: bool = True
    include_source_trace: bool = True
    include_text_body: bool = False


class McpServerConfig(StrictModel):
    host: str = "127.0.0.1"
    port: int = 7331

    @field_validator("host")
    @classmethod
    def _validate_host(cls, value: str) -> str:
        return validate_non_empty(value, "host")

    @field_validator("port")
    @classmethod
    def _validate_port(cls, value: int) -> int:
        if value < 1 or value > 65535:
            raise ValueError("mcp.port must be between 1 and 65535")
        return value


class IdentityConfig(StrictModel):
    mode: str = "client_ip"

    @field_validator("mode")
    @classmethod
    def _validate_mode(cls, value: str) -> str:
        if value not in {"client_ip", "user_id"}:
            raise ValueError("identity.mode must be 'client_ip' or 'user_id'")
        return value


class FmConfig(StrictModel):
    mode: str = "client_context"
    require_used_xids: bool = True
    require_unknowns: bool = True
    require_applied_skills: bool = True
    validate_output_contract: bool = True


class ExecutionConfig(StrictModel):
    allow_package_code: bool = False
    allowed_tools: dict[str, bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _enforce_mvp_execution(self) -> "ExecutionConfig":
        if self.allow_package_code:
            raise ValueError("MVP does not allow package code execution")
        return self


class XRefKitServerConfig(StrictModel):
    core: CoreConfig
    discovery: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    packages: EnabledPackagesConfig = Field(default_factory=EnabledPackagesConfig)
    local: LocalMountConfig = Field(default_factory=LocalMountConfig)
    merge: MergePolicyConfig = Field(default_factory=MergePolicyConfig)
    load_policy: ServerLoadPolicyConfig = Field(default_factory=ServerLoadPolicyConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    mcp: McpServerConfig = Field(default_factory=McpServerConfig)
    identity: IdentityConfig | None = None
    fm: FmConfig | None = None
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)

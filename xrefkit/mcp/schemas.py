from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


ExecutionLocation = Literal["server", "client"]
SideEffects = Literal["none", "audit_write", "repo_write", "external_write", "unknown"]
ResponseEnvelope = Literal["direct_object", "mcp_result_array"]


@dataclass(frozen=True)
class ToolContract:
    tool_id: str
    provider: str
    version: str
    execution_location: ExecutionLocation
    side_effects: SideEffects
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    requires_workspace: bool
    required_when: str
    enforced_fields: tuple[str, ...] = ("execution_location", "side_effects")
    response_envelope: ResponseEnvelope = "direct_object"

    def validate(self) -> None:
        if self.execution_location == "server" and self.side_effects not in {"none", "audit_write"}:
            raise ValueError(
                f"server tool {self.tool_id!r} may declare only side_effects='none' or 'audit_write'"
            )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["input_json_schema"] = _json_schema_object(self.input_schema)
        data["output_json_schema"] = _json_schema_object(self.output_schema)
        data["schema_format"] = "json_schema"
        return data


@dataclass(frozen=True)
class KnowledgeCatalogEntry:
    xid: str
    version: int
    content_hash: str
    revised_at: str | None
    title: str
    domain: str
    summary: str
    applies_when: list[str]
    requires_knowledge: list[str]
    related_skills: list[str]
    related_capabilities: list[str]
    path: str
    expandable: bool = True
    missing: list[str] = field(default_factory=list)
    zone_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("path", None)
        return data


@dataclass(frozen=True)
class ClosureContract:
    closure_conditions: list[str]
    exit_enum: list[str]
    handoff_policy: str
    worklist_policy: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SkillCatalogEntry:
    skill_id: str
    title: str
    summary: str
    maturity: str
    intent: list[str]
    target_artifacts: list[str]
    applies_when: list[str]
    not_for: list[str]
    required_knowledge: list[dict[str, Any]]
    required_tools: list[dict[str, Any]]
    inputs: list[str]
    outputs: list[str]
    closure_contract: ClosureContract
    meta_content: str
    meta_links: list[dict[str, str]]
    skill_content: str
    skill_links: list[dict[str, str]]
    path: str
    meta_path: str
    context_size: dict[str, Any]
    # Skill-centric consolidation (design 083/084): the capability/tuning/
    # responsibility triad is the Skill meta identity and routing vocabulary,
    # and preconditions/knowledge_slots are the declared needs that replace
    # capability_refs binding and static knowledge_refs. Surfaced as an additive
    # superset; empty until skill metas migrate to the new fields.
    capability: str = ""
    tuning: str = ""
    responsibility: str = ""
    preconditions: list[str] = field(default_factory=list)
    knowledge_slots: list[dict[str, Any]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    zone_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["closure_contract"] = self.closure_contract.to_dict()
        return data


@dataclass(frozen=True)
class SkillRankResult:
    skill_id: str
    summary: str
    maturity: str
    matched_facets: list[str]
    matched_categories: dict[str, list[str]]
    closure_preview: ClosureContract
    required_knowledge: list[dict[str, Any]]
    execution_readiness: dict[str, Any]
    score: float

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["closure_preview"] = self.closure_preview.to_dict()
        return data


@dataclass(frozen=True)
class StartupReference:
    xid: str
    title: str
    layer: Literal["base_control", "xref_routing"]
    required_at_init: bool
    summary: str
    content: str | None
    links: list[dict[str, str]]
    content_hash: str | None = None
    cache_status: Literal["miss", "modified", "not_modified", "bypassed"] = "miss"
    content_omitted: bool = False
    included_in_startup_contract_pack: bool = False
    cache_policy: dict[str, Any] = field(default_factory=dict)
    repository_fingerprint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class XRefDocument:
    xid: str
    title: str
    path: str
    summary: str
    content: str
    links: list[dict[str, str]]
    content_hash: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("path", None)
        return data


@dataclass(frozen=True)
class RuntimeRoleContract:
    roles: dict[str, str]
    phases: list[str]
    statuses: list[str]
    invariants: list[str]
    required_commands: list[str]
    source_xids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClientObligation:
    id: str
    level: Literal["must", "should", "may"]
    applies_when: str
    statement: str
    enforcement_owner: Literal["client", "server", "human"]
    verification: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClientToolFile:
    path: str
    kind: Literal["python", "support", "documentation"]
    content: str
    content_hash: str
    size_bytes: int
    run_hint: str | None
    imports: list[str] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClientToolManifestEntry:
    path: str
    kind: Literal["python", "support", "documentation"]
    content_hash: str
    size_bytes: int
    run_hint: str | None
    resolver_tool: str
    resolver_argument: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClientToolDistribution:
    package_id: str
    version: str
    execution_location: Literal["client"]
    server_executes_tools: bool
    install_layout: str
    required_package_ids: list[str]
    package_versions: dict[str, str]
    file_hash_algorithm: str
    version_check_tool: str
    materialization: dict[str, Any]
    update_policy: dict[str, Any]
    files: list[ClientToolManifestEntry]
    instructions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "version": self.version,
            "execution_location": self.execution_location,
            "server_executes_tools": self.server_executes_tools,
            "install_layout": self.install_layout,
            "required_package_ids": self.required_package_ids,
            "package_versions": self.package_versions,
            "file_hash_algorithm": self.file_hash_algorithm,
            "version_check_tool": self.version_check_tool,
            "materialization": self.materialization,
            "update_policy": self.update_policy,
            "files": [file.to_dict() for file in self.files],
            "instructions": self.instructions,
        }


@dataclass(frozen=True)
class ClientToolPipPackage:
    filename: str
    package_id: str
    version: str
    package_format: Literal["zip-sdist"]
    install_command: str
    content_base64: str
    content_hash: str
    size_bytes: int
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StartupContext:
    catalog_version: str
    repository_identity: dict[str, str]
    access_policy: dict[str, Any]
    context_injection_policy: dict[str, Any]
    session_context_deduplication: dict[str, Any]
    core_runtime_distribution: dict[str, Any]
    repository_zones: dict[str, Any]
    client_instructions: list[str]
    client_obligations: list[ClientObligation]
    link_resolution: dict[str, str]
    load_order: list[str]
    startup_contract_pack: dict[str, Any]
    references: list[StartupReference]
    semantic_routing_references: list[dict[str, Any]]
    missing: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_version": self.catalog_version,
            "repository_identity": self.repository_identity,
            "access_policy": self.access_policy,
            "context_injection_policy": self.context_injection_policy,
            "session_context_deduplication": self.session_context_deduplication,
            "core_runtime_distribution": self.core_runtime_distribution,
            "repository_zones": self.repository_zones,
            "client_instructions": self.client_instructions,
            "client_obligations": [
                obligation.to_dict() for obligation in self.client_obligations
            ],
            "link_resolution": self.link_resolution,
            "load_order": self.load_order,
            "startup_contract_pack": self.startup_contract_pack,
            "references": [reference.to_dict() for reference in self.references],
            "semantic_routing_references": self.semantic_routing_references,
            "missing": self.missing,
        }


def _json_schema_object(schema: dict[str, Any]) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    for name, descriptor in schema.items():
        optional = isinstance(descriptor, str) and descriptor.endswith("?")
        if not optional:
            required.append(name)
        properties[name] = _json_schema_for_descriptor(descriptor)
    result: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        result["required"] = required
    return result


def _json_schema_for_descriptor(descriptor: Any) -> dict[str, Any]:
    if isinstance(descriptor, dict):
        return descriptor
    if not isinstance(descriptor, str):
        return {"description": str(descriptor)}
    base = descriptor.removesuffix("?")
    if base == "string":
        return {"type": "string"}
    if base == "integer":
        return {"type": "integer"}
    if base == "boolean":
        return {"type": "boolean"}
    if base == "object":
        return {"type": "object"}
    if base == "array":
        return {"type": "array"}
    return {"description": base}

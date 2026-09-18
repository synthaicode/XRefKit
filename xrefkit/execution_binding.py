"""Build and validate inert execution bindings for workflow runs."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from xrefkit.skillrun import (
    _LogFileLock,
    _has_opened_run_gate,
    _log_field,
    _parse_work_items,
    _section_status,
    _validate_observation_log,
)

MAX_REQUEST_BYTES = 256_000
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_XID = re.compile(r"[0-9A-F]{12}\Z")
_FIELDS = (
    "run_id", "flow_id", "root_run_id", "parent_run_id", "work_item_id",
    "node_id", "skill_id", "skill_doc", "task", "authority", "executor",
    "checker", "quality_reviewer", "handoff_owner",
    "capability", "tuning", "responsibility", "definition_xid",
    "definition_path", "definition_sha256",
)
_REQUIRED_REQUEST = {
    "work_item_id", "source_mode", "purpose", "capability", "tuning",
    "responsibility", "instruction_basis", "scope_in", "scope_out",
    "stop_conditions", "protocols", "knowledge_access",
}
_OPTIONAL_REQUEST = {"references", "repository_fingerprint"}
_MCP_KNOWLEDGE = {
    "mode": "on_demand",
    "catalog_tool": "search_knowledge_catalog",
    "resolve_tool": "get_document_by_xid",
}


def _fail(message: str) -> None:
    raise ValueError(message)


def _strings(value: Any, name: str, *, empty: bool = False) -> list[str]:
    if (not isinstance(value, list) or (not empty and not value)
            or any(type(item) is not str or not item.strip() for item in value)):
        _fail(f"{name} must be a list of nonempty strings")
    return value


def _json_snapshot(value: Any) -> tuple[str, dict[str, Any]]:
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False)
        frozen = json.loads(encoded)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("request must be strict JSON") from exc
    if len(encoded.encode("utf-8")) > MAX_REQUEST_BYTES:
        _fail("request or generated binding exceeds 256000 UTF-8 bytes")
    return encoded, frozen


def _validate_request(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        _fail("request must be an object")
    unknown = set(request) - _REQUIRED_REQUEST - _OPTIONAL_REQUEST
    missing = _REQUIRED_REQUEST - set(request)
    if unknown:
        _fail(f"unknown request keys: {', '.join(sorted(unknown))}")
    if missing:
        _fail(f"missing request keys: {', '.join(sorted(missing))}")
    for key in ("work_item_id", "source_mode", "purpose", "capability",
                "tuning", "responsibility", "instruction_basis"):
        if type(request[key]) is not str or not request[key].strip():
            _fail(f"{key} must be a nonempty string")
    _strings(request["scope_in"], "scope_in")
    _strings(request["scope_out"], "scope_out", empty=True)
    _strings(request["stop_conditions"], "stop_conditions")
    protocols = _strings(request["protocols"], "protocols")
    if len(set(protocols)) != len(protocols):
        _fail("protocols contains duplicates")
    if "workflow" not in protocols or set(protocols) - {"workflow", "reporting"}:
        _fail("protocols must include workflow and contain only workflow/reporting")
    if not isinstance(request["knowledge_access"], dict):
        _fail("knowledge_access must be an object")
    source = request["source_mode"]
    refs = request.get("references", [])
    if not isinstance(refs, list) or len(refs) > 32:
        _fail("references must contain at most 32 entries")
    if source == "filesystem":
        access = request["knowledge_access"]
        if (set(access) != {"mode", "catalog"}
                or access.get("mode") != "on_demand"
                or not isinstance(access.get("catalog"), str)
                or not access["catalog"].strip()):
            _fail("filesystem knowledge_access must be {mode:on_demand,catalog:<path>}")
        if "repository_fingerprint" in request:
            _fail("filesystem binding cannot include repository_fingerprint")
        for ref in refs:
            if (not isinstance(ref, dict) or set(ref) != {"path", "sha256"}
                    or type(ref.get("path")) is not str or not ref["path"].strip()
                    or type(ref.get("sha256")) is not str or _HASH.fullmatch(ref["sha256"]) is None):
                _fail("filesystem references require path and lowercase sha256")
    elif source == "mcp":
        if type(request.get("repository_fingerprint")) is not str or not request["repository_fingerprint"].strip():
            _fail("MCP binding requires repository_fingerprint")
        if request["knowledge_access"] != _MCP_KNOWLEDGE:
            _fail("invalid MCP knowledge_access")
        for ref in refs:
            if (not isinstance(ref, dict) or set(ref) != {"xid", "content_hash"}
                    or type(ref.get("xid")) is not str
                    or type(ref.get("content_hash")) is not str
                    or _XID.fullmatch(ref["xid"]) is None
                    or _HASH.fullmatch(ref["content_hash"]) is None):
                _fail("MCP references require XID and content_hash")
    else:
        _fail("source_mode must be filesystem or mcp")
    request.setdefault("references", [])
    return request


def _run_snapshot(run_text: str, work_item_id: str) -> dict[str, Any]:
    if type(run_text) is not str:
        _fail("run text must be a string")
    if not _has_opened_run_gate(run_text):
        _fail("run log is missing an opened load gate")
    run_id = _log_field(run_text, "run_id")
    if not run_id:
        _fail("run log is missing run_id")
    closure = _section_status(run_text, "Closure Gate")
    if closure in {"done", "escalated"}:
        _fail("binding requires an open workflow run")
    item = next((item for item in _parse_work_items(run_text)
                 if item.get("item_id") == work_item_id), None)
    if not item or item.get("status") not in {"pending", "in_progress"} or not item.get("criterion"):
        _fail("selected work item must be pending/in_progress with a criterion")
    fields = {key: _log_field(run_text, key) for key in _FIELDS}
    # Workflow logs keep the task as readable Markdown rather than a token.
    match = re.search(
        r"^- task: (.*?)(?=^- report_language:)",
        run_text, re.MULTILINE | re.DOTALL,
    )
    fields["task"] = match.group(1).rstrip() if match else None
    for key in ("run_id", "flow_id", "root_run_id", "skill_id", "task", "executor",
                "checker", "quality_reviewer", "handoff_owner"):
        if not fields[key]:
            _fail(f"run log is missing {key}")
    return {"fields": fields, "work_item": item, "closure": closure}


def build_execution_binding(log: Path, request: dict) -> dict:
    """Validate a request and return a frozen, inert workflow binding."""
    _, request = _json_snapshot(request)
    _validate_request(request)
    log_path = Path(log).resolve()
    with _LogFileLock(log_path.with_name(f".{log_path.name}.lock")):
        run_text, error = _validate_observation_log(log_path)
        if error is not None:
            _fail("; ".join(error.errors))
        assert run_text is not None
        snap = _run_snapshot(run_text, request["work_item_id"])
        fields = snap["fields"]
        captured = {"xid": fields["definition_xid"],
                    "path": fields["definition_path"],
                    "sha256": fields["definition_sha256"]}
        present = [value is not None for value in captured.values()]
        if any(present) and not all(present):
            _fail("run has an incomplete definition identity")
        if all(present):
            if (_XID.fullmatch(captured["xid"]) is None
                    or _HASH.fullmatch(captured["sha256"]) is None
                    or not captured["path"].strip()):
                _fail("run has an invalid definition identity")
            for key in ("capability", "tuning", "responsibility"):
                if fields[key] != request[key]:
                    _fail(f"{key} does not match definition-backed Skill Run")
        if request["source_mode"] == "filesystem" and _log_field(run_text, "mcp_session_id"):
            _fail("filesystem binding cannot use an MCP session")
        if request["source_mode"] == "mcp" and fields["skill_id"] == "general_skill":
            _fail("general_skill is unsupported")
        if request["source_mode"] == "mcp" and _log_field(run_text, "repository_fingerprint") not in (None, request["repository_fingerprint"]):
            _fail("run already belongs to another repository")
        result = dict(request)
        result.update({"schema_version": 1, "run_id": fields["run_id"],
                       "binding_origin": "workflow_builder", "run_snapshot": snap})
        if all(present):
            result["definition_identity"] = captured
        return _json_snapshot(result)[1]


def validate_binding_context(run_text: str, binding: dict) -> None:
    """Reject generated bindings whose captured workflow context has changed."""
    if type(binding) is not dict:
        _fail("binding must be an object")
    if "binding_origin" not in binding and "run_snapshot" not in binding:
        return
    if binding.get("binding_origin") != "workflow_builder" or not isinstance(binding.get("run_snapshot"), dict):
        _fail("malformed workflow binding markers")
    current = _run_snapshot(run_text, binding.get("work_item_id"))
    if current != binding["run_snapshot"]:
        _fail("workflow run context changed")
    if current["fields"].get("run_id") != binding.get("run_id"):
        _fail("binding run_id does not match workflow run")

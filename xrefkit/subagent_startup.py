"""Bounded, read-only local context materialization for an opened workflow run.

This adapter does not spawn agents, execute instructions, accept output quality,
or resolve MCP-only governance through the filesystem.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from xrefkit.skillrun import (
    _LogFileLock, _append_observation_event, _atomic_write_text,
    _log_field, _parse_work_items, _validate_observation_log,
)

STARTUP_SOURCES = (
    ("docs/core/contracts/080_xrefkit_startup_contract.md", "C3A1F78D9B22"),
    ("agent/000_agent_entry.md", "0B5C58B5E5B2"),
    ("docs/core/models/017_base_and_xref_layering.md", "5A1C8E4D2F90"),
    ("docs/core/contracts/011_startup_xref_routing.md", "6C0B62D6366A"),
    ("docs/core/contracts/016_uncertainty_protocol.md", "8A666C1FD121"),
    ("docs/core/contracts/053_context_direction_security_guard.md", "A7F3C92D4E11"),
    ("docs/core/contracts/015_shared_memory_operations.md", "4A423E72D2ED"),
)
PROTOCOL_SOURCES = {
    "workflow": ("docs/guides/088_instruction_workflow_protocol.md", "9F4C2A7D1B60"),
    "reporting": ("docs/core/contracts/081_skill_reporting_contract.md", "6B2D9F4A1C73"),
}
MAX_FILE_BYTES = 256_000
MAX_TOTAL_BYTES = 1_000_000


def _path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("a nonempty file path is required")
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError("startup input must remain within --root")
    if not path.is_file():
        raise ValueError(f"startup file not found: {value}")
    return path


def _read(root: Path, value: str, *, xid: str | None = None,
          sha256: str | None = None) -> dict:
    path = _path(root, value)
    with path.open("rb") as source:
        raw = source.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError(f"startup file exceeds byte limit: {value}")
    digest = hashlib.sha256(raw).hexdigest()
    if sha256 is not None and digest != sha256:
        raise ValueError(f"startup revision mismatch: {value}")
    body = raw.decode("utf-8-sig")
    if xid and not re.search(r"<!--\s*xid:\s*" + re.escape(xid) + r"\s*-->", body):
        raise ValueError(f"startup XID mismatch: {value}")
    return {"path": path.relative_to(root).as_posix(), "xid": xid,
            "sha256": digest, "bytes": len(raw), "body": body}


def _strings(binding: dict, key: str, *, allow_empty: bool = False) -> list[str]:
    values = binding.get(key)
    if (not isinstance(values, list) or (not values and not allow_empty)
            or any(not isinstance(v, str) or not v.strip() for v in values)):
        raise ValueError(f"{key} must be a list of nonempty strings")
    return values


def read_subagent_startup(root: Path, log: Path, binding_path: Path) -> dict:
    root = root.resolve()
    log = _path(root, str(log))
    binding_doc = _read(root, str(binding_path))
    binding = json.loads(binding_doc["body"])
    if not isinstance(binding, dict) or type(binding.get("schema_version")) is not int or binding["schema_version"] != 1:
        raise ValueError("unsupported subagent binding schema_version")
    if binding.get("source_mode") != "filesystem":
        raise ValueError("this local reader requires filesystem mode; use the MCP provider for MCP governance")
    for key in ("run_id", "work_item_id", "purpose", "capability", "tuning", "responsibility"):
        if not isinstance(binding.get(key), str) or not binding[key].strip():
            raise ValueError(f"binding requires {key}")
    _strings(binding, "scope_in")
    _strings(binding, "scope_out", allow_empty=True)
    _strings(binding, "stop_conditions")
    protocols = _strings(binding, "protocols")
    if "workflow" not in protocols or len(protocols) != len(set(protocols)) or set(protocols) - PROTOCOL_SOURCES.keys():
        raise ValueError("an opened workflow requires workflow; only workflow/reporting protocols are supported")
    access = binding.get("knowledge_access")
    if not isinstance(access, dict) or access.get("mode") != "on_demand" or not isinstance(access.get("catalog"), str):
        raise ValueError("knowledge_access requires on_demand mode and a catalog locator")
    catalog = _path(root, access["catalog"])
    references = binding.get("references", [])
    if not isinstance(references, list) or len(references) > 32:
        raise ValueError("references must be a list with at most 32 entries")
    for reference in references:
        if (not isinstance(reference, dict) or set(reference) - {"path", "sha256"}
                or not isinstance(reference.get("path"), str)
                or not isinstance(reference.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", reference["sha256"])):
            raise ValueError("each task reference requires path and SHA-256")
    with _LogFileLock(log.with_name(f".{log.name}.lock")):
        run_text, error = _validate_observation_log(log)
        if error:
            raise ValueError("; ".join(error.errors))
        assert run_text is not None
        if _log_field(run_text, "mcp_session_id"):
            raise ValueError("MCP-bound runs must resolve governance through the MCP provider")
        if _log_field(run_text, "run_id") != binding["run_id"]:
            raise ValueError("binding run_id does not match opened run")
        items = _parse_work_items(run_text)
        item = next((v for v in items if v["item_id"] == binding["work_item_id"]), None)
        if not item or item["status"] not in {"pending", "in_progress"} or not item.get("criterion"):
            raise ValueError("startup requires a pending/in_progress work item with a completion criterion")
        documents = [_read(root, "AGENTS.md")]
        documents.extend(_read(root, path, xid=xid) for path, xid in STARTUP_SOURCES)
        documents.extend(_read(root, PROTOCOL_SOURCES[p][0], xid=PROTOCOL_SOURCES[p][1]) for p in protocols)
        skill_doc = _log_field(run_text, "skill_doc")
        if skill_doc:
            documents.append(_read(root, skill_doc))
        documents.extend(_read(root, r["path"], sha256=r["sha256"]) for r in references)
        if sum(d["bytes"] for d in documents) + binding_doc["bytes"] > MAX_TOTAL_BYTES:
            raise ValueError("startup context exceeds total byte limit")
        # Recheck inputs before recording success; never acknowledge partial reads.
        for doc in [binding_doc, *documents]:
            _read(root, doc["path"], sha256=doc["sha256"])
        receipt = [{k: d[k] for k in ("path", "xid", "sha256", "bytes")} for d in documents]
        event = {"event": "subagent.startup.read", "run_id": binding["run_id"],
                 "work_item_id": binding["work_item_id"], "binding_sha256": binding_doc["sha256"],
                 "source_mode": "filesystem", "protocols": protocols, "reads": receipt,
                 "meaning": "materialized by reader; not model comprehension or execution evidence"}
        _atomic_write_text(log, _append_observation_event(run_text, section="Subagent Startup", event=event))
    return {"ok": True, "schema_version": 1, "state": "materialized",
            "binding": binding, "work_item": item,
            "correlation": {key: _log_field(run_text, key) for key in
                            ("run_id", "flow_id", "root_run_id", "parent_run_id", "node_id")},
            "roles": {key: _log_field(run_text, key) for key in
                      ("executor", "checker", "quality_reviewer", "handoff_owner")},
            "knowledge_access": {"mode": "on_demand", "catalog": catalog.relative_to(root).as_posix(),
                                 "body_loaded": False},
            "documents": documents, "receipt": event,
            "boundary": "Host must deliver these bodies to the subagent. No agent was started; verify/close remain required."}


def cmd_subagent_read(args) -> int:
    try:
        result = read_subagent_startup(Path(args.root), Path(args.log), Path(args.binding))
    except (OSError, UnicodeError, ValueError, TimeoutError) as exc:
        result = {"ok": False, "state": "blocked", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1

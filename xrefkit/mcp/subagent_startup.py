"""Materialize bounded MCP context for an existing subagent work item.

The host owns transport initialization and dispatch. Local access is restricted
to the run log; server paths and returned shell commands are never followed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, NoReturn

from xrefkit.skillrun import (
    _LogFileLock, _append_observation_event, _atomic_write_text, _log_field,
    _parse_work_items, _section_status, _valid_log_token,
    _validate_observation_log, correlate_skill_run,
)

MAX_FILE_BYTES = 256_000
MAX_TOTAL_BYTES = 1_000_000
XID = re.compile(r"[0-9A-F]{12}")
HASH = re.compile(r"[0-9a-f]{64}")
CORRELATION_FIELDS = (
    "run_id", "flow_id", "root_run_id", "parent_run_id", "work_item_id", "node_id",
)
ROLE_FIELDS = ("executor", "checker", "quality_reviewer", "handoff_owner")
KNOWLEDGE_ACCESS = {
    "mode": "on_demand", "catalog_tool": "search_knowledge_catalog",
    "resolve_tool": "get_document_by_xid",
}


class McpSubagentStartupError(ValueError):
    """Inputs cannot establish a complete, consistent startup context."""


def _bad(message: str) -> NoReturn:
    raise McpSubagentStartupError(message)


def _object(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        _bad(f"{name} must be an object")
    return value


def _json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise McpSubagentStartupError("context must be JSON serializable") from exc


def _digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _strings(value: Any, name: str, *, empty: bool = False) -> list[str]:
    if (not isinstance(value, list) or (not empty and not value)
            or any(not isinstance(v, str) or not v.strip() for v in value)):
        _bad(f"{name} must be a list of nonempty strings")
    return value


def _unique(value: Any, name: str) -> list[str]:
    values = _strings(value, name)
    if len(set(values)) != len(values):
        _bad(f"{name} contains duplicates")
    return values


def _matches(pattern: re.Pattern, value: Any) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _validate_binding(binding: dict) -> None:
    if type(binding.get("schema_version")) is not int or binding["schema_version"] != 1:
        _bad("unsupported binding schema_version")
    if binding.get("source_mode") != "mcp":
        _bad("MCP binding requires source_mode=mcp")
    for key in ("run_id", "work_item_id", "purpose", "capability", "tuning",
                "responsibility", "repository_fingerprint"):
        if not isinstance(binding.get(key), str) or not binding[key].strip():
            _bad(f"binding requires {key}")
    for key in ("scope_in", "scope_out", "stop_conditions"):
        _strings(binding.get(key), key, empty=key == "scope_out")
    protocols = _unique(binding.get("protocols"), "protocols")
    if "workflow" not in protocols or set(protocols) - {"workflow", "reporting"}:
        _bad("opened workflow requires workflow; only workflow/reporting are supported")
    if binding.get("knowledge_access") != KNOWLEDGE_ACCESS:
        _bad("invalid MCP knowledge_access")
    refs = binding.get("references", [])
    if not isinstance(refs, list) or len(refs) > 32:
        _bad("references must contain at most 32 entries")
    for ref in refs:
        if (not isinstance(ref, dict) or set(ref) != {"xid", "content_hash"}
                or not _matches(XID, ref.get("xid"))
                or not _matches(HASH, ref.get("content_hash"))):
            _bad("each reference requires an XID and content_hash")


def _run_state(log: Path, binding: dict) -> tuple[str, dict]:
    # Caller holds the log lock; never hold this lock across a transport await.
    text, error = _validate_observation_log(log)
    if error:
        _bad("; ".join(error.errors))
    assert text is not None
    closure = _section_status(text, "Closure Gate")
    if closure in {"done", "escalated"}:
        _bad("startup requires an open workflow run")
    if _log_field(text, "run_id") != binding["run_id"]:
        _bad("binding run_id does not match opened run")
    item = next((v for v in _parse_work_items(text)
                 if v["item_id"] == binding["work_item_id"]), None)
    if not item or item["status"] not in {"pending", "in_progress"} or not item.get("criterion"):
        _bad("startup requires a pending/in_progress work item with a completion criterion")
    fields = {k: _log_field(text, k) for k in (
        *CORRELATION_FIELDS, *ROLE_FIELDS, "skill_id", "skill_doc",
        "mcp_session_id", "repository_fingerprint",
    )}
    for key in ("run_id", "flow_id", "root_run_id", "skill_id", *ROLE_FIELDS):
        if not fields[key]:
            _bad(f"run is missing {key}")
    return text, {"fields": fields, "item": item, "closure": closure}


def _check_state(log: Path, binding: dict, expected: dict) -> str:
    text, current = _run_state(log, binding)
    if current != expected:
        _bad("run changed during startup")
    return text


async def read_mcp_subagent_startup(
    log: Path, binding: dict, call_tool: Callable[[str, dict], Awaitable[dict]],
) -> dict:
    """Return inert bodies and an audit receipt; no agent or procedure is run.

    call_tool uses an already initialized session and returns structured dicts.
    The host handles MCP errors, timeouts, and HTTP context-token propagation.
    A failure after binding can leave a factual correlation, never a read receipt.
    """
    # Freeze caller-owned data before any await so callbacks cannot redirect it.
    binding_json = _json(_object(binding, "binding"))
    binding = json.loads(binding_json)
    _validate_binding(binding)
    total = len(binding_json.encode("utf-8"))
    if total > MAX_TOTAL_BYTES:
        _bad("binding exceeds total byte limit")
    log = Path(log).resolve()
    lock_path = log.with_name(f".{log.name}.lock")
    with _LogFileLock(lock_path):
        _, expected = _run_state(log, binding)
    fields = expected["fields"]
    skill_id = fields["skill_id"]
    if skill_id == "general_skill":
        _bad("general_skill has no remote managed Skill identity")
    fingerprint = binding["repository_fingerprint"]
    if fields["repository_fingerprint"] not in (None, fingerprint):
        _bad("run already belongs to another repository")
    correlation = {k: fields[k] for k in CORRELATION_FIELDS}
    roles = {k: fields[k] for k in ROLE_FIELDS}
    documents = []

    def add_body(body: Any, kind: str, xid: str | None = None,
                 content_hash: str | None = None) -> None:
        nonlocal total
        if not isinstance(body, str) or not body:
            _bad(f"{kind} requires a body")
        size = len(body.encode("utf-8"))
        if size > MAX_FILE_BYTES or total + size > MAX_TOTAL_BYTES:
            _bad("startup context exceeds byte limit")
        actual = _digest(body)
        if content_hash is not None and actual != content_hash:
            _bad(f"{kind} content hash mismatch")
        total += size
        documents.append({"xid": xid, "content_hash": actual,
                          "bytes": size, "body": body, "kind": kind})

    async def call(name: str, args: dict) -> dict:
        # The snapshot also prevents a callback retaining and mutating a reply.
        return json.loads(_json(_object(await call_tool(name, args), name)))

    startup = await call("get_startup_context", {"known_document_versions": {}})
    identity = _object(startup.get("repository_identity"), "repository_identity")
    if identity.get("repository_fingerprint") != fingerprint:
        _bad("repository fingerprint mismatch")
    policy = _object(startup.get("access_policy"), "access_policy")
    if policy.get("mode") != "mcp_only" or startup.get("missing") != []:
        _bad("invalid or incomplete MCP startup")
    selection = _object(startup.get("initial_protocol_selection"), "protocol selection")
    selected = _unique(selection.get("selected"), "selected protocols")
    if set(selected) != set(binding["protocols"]):
        _bad("protocol selection mismatch")
    pack = _object(startup.get("startup_contract_pack"), "startup_contract_pack")
    if pack.get("stale") is not False or pack.get("stale_sources") != []:
        _bad("stale startup contract pack; refresh server pack")
    sources = _unique(pack.get("source_xids"), "pack source_xids")
    load_order = _unique(startup.get("load_order"), "load_order")
    if any(not _matches(XID, v) for v in sources + load_order) or set(load_order) - set(sources):
        _bad("invalid startup load_order or pack source_xids")
    if not _matches(HASH, pack.get("pack_hash")):
        _bad("invalid startup pack hash")
    add_body(pack.get("body"), "startup_contract_pack",
             content_hash=pack["pack_hash"])
    for name in ("prompt_flow_protocol", "workflow_protocol", "reporting_protocol"):
        protocol = startup.get(name)
        if name == "reporting_protocol" and "reporting" not in selected:
            if protocol is not None:
                _bad("unselected reporting protocol present")
            continue
        protocol = _object(protocol, name)
        if protocol.get("version") != "1":
            _bad(f"unsupported {name} version")
        if name == "prompt_flow_protocol":
            reconciliation = _object(protocol.get("reconciliation"), "reconciliation")
            if reconciliation.get("default") != "report_only":
                _bad("invalid prompt reconciliation default")
        add_body(_json(protocol), name)

    with _LogFileLock(lock_path):
        _check_state(log, binding, expected)
    bind_args = {k: v for k, v in correlation.items() if v is not None}
    bind_args["skill_id"] = skill_id
    bound = await call("bind_skill_run", bind_args)
    for key, value in {**correlation, "skill_id": skill_id,
                       "repository_fingerprint": fingerprint}.items():
        if bound.get(key) != value:
            _bad(f"bind response mismatch: {key}")
    session_id = bound.get("mcp_session_id")
    if (not isinstance(session_id, str) or not session_id.strip()
            or not _valid_log_token(session_id) or bound.get("audit_enabled") is not True):
        _bad("invalid bind session or audit response")
    with _LogFileLock(lock_path):
        _check_state(log, binding, expected)
        # Reuse trusted correlation validation/write under the lock already held.
        # __wrapped__ bypasses only its locking decorator, avoiding a nested lock.
        result = correlate_skill_run.__wrapped__(argparse.Namespace(
            log=str(log), run_id=fields["run_id"], mcp_session_id=session_id,
            repository_fingerprint=fingerprint,
        ))
        if not result.ok:
            _bad("trusted local correlation failed: " + "; ".join(result.errors))
        _, expected = _run_state(log, binding)
    correlation.update(mcp_session_id=session_id, repository_fingerprint=fingerprint)

    def add_document(value: Any, kind: str, ref: dict | None = None) -> None:
        doc = _object(value, kind)
        if not _matches(XID, doc.get("xid")) or doc.get("repository_fingerprint") != fingerprint:
            _bad(f"invalid {kind} document identity")
        if not _matches(HASH, doc.get("content_hash")):
            _bad(f"invalid {kind} document hash")
        if ref and (doc["xid"] != ref["xid"] or doc["content_hash"] != ref["content_hash"]):
            _bad("referenced document revision mismatch")
        add_body(doc.get("content"), kind, doc["xid"], doc["content_hash"])

    if skill_id != "instruction":
        skill = await call("get_skill", {"skill_id": skill_id, "known_document_versions": {}})
        docs = skill.get("documents")
        if skill.get("skill_id") != skill_id or not isinstance(docs, list) or len(docs) != 2:
            _bad("managed Skill requires its meta and procedure documents")
        for doc in docs:
            add_document(doc, "skill")
        if docs[0]["xid"] == docs[1]["xid"]:
            _bad("Skill meta and procedure must have distinct XIDs")
    for ref in binding.get("references", []):
        add_document(await call("get_document_by_xid", {"xid": ref["xid"]}), "reference", ref)
    with _LogFileLock(lock_path):
        current = _check_state(log, binding, expected)
        event = {
            "event": "subagent.startup.read", "run_id": binding["run_id"],
            "work_item_id": binding["work_item_id"], "binding_sha256": _digest(binding_json),
            "source_mode": "mcp", "protocols": binding["protocols"],
            "selection": selection, "correlation": correlation,
            "reads": [{k: d[k] for k in ("xid", "content_hash", "bytes", "kind")}
                      for d in documents],
            "meaning": "materialized by reader; not model comprehension or execution evidence",
        }
        _atomic_write_text(log, _append_observation_event(
            current, section="Subagent Startup", event=event,
        ))
    return {
        "ok": True, "schema_version": 1, "state": "materialized", "binding": binding,
        "work_item": expected["item"], "roles": roles, "correlation": correlation,
        "initial_protocol_selection": selection,
        "knowledge_access": {**KNOWLEDGE_ACCESS, "body_loaded": False},
        "documents": documents, "receipt": event,
        "boundary": "Host must deliver these bodies to the subagent. No agent was started; verify/close remain required.",
    }

"""Bounded governance entries; host dispatch and human authority stay external."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Callable

from .execution_binding import build_execution_binding, validate_binding_context
from .mcp.contribution_adoption import HumanApprovalVerifier
from .skillrun import _LogFileLock, _log_field, _parse_artifacts, _section_status

SCHEMA = "xrefkit.governance_entry/v1"
MAX_BYTES = 512_000
CORE_CHECKS = {"authority", "candidate_identity", "external_references", "specialist_evidence", "handoff"}
RULE_SOURCES = {"docs/core/contracts/115_shared_asset_update_gate.md", "docs/reference/020_sources.md"}


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _inside(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("use a nonempty portable repository-relative path")
    path = Path(relative)
    if path.is_absolute() or ":" in relative or ".." in path.parts or path.as_posix() != relative:
        raise ValueError("path must remain inside repository")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("path escapes repository")
    return resolved


def snapshot(root: Path, relative: str) -> dict:
    path = _inside(root, relative)
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("governance material exceeds size limit")
    return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest()}


def _current(root: Path, relative: str) -> str | None:
    path = _inside(root, relative)
    return snapshot(root, relative)["sha256"] if path.exists() else None


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be explicit nonempty text")
    return value


def _strings(value: object, name: str, *, empty: bool = False) -> list:
    if (not isinstance(value, list) or (not value and not empty)
            or any(not isinstance(item, str) or not item.strip() for item in value)
            or len(set(value)) != len(value)):
        raise ValueError(f"{name} must be unique nonempty strings")
    return value


def _payload(root: Path, kind: str, payload: dict, materials: list[str], *, frozen: bool) -> None:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if kind == "asset_update":
        required = {"candidate", "target", "rules", "specialist_evidence", "checks"}
        if frozen:
            required.add("expected_target_hash")
        if set(payload) != required:
            raise ValueError("asset update payload fields mismatch")
        target = _text(payload["target"], "target")
        _inside(root, target)
        _inside(root, payload["candidate"])
        if (Path(target).parts[0] not in {"skills", "skills_private", "knowledge"}
                or _inside(root, target).relative_to(root.resolve()).parts[0] not in {"skills", "skills_private", "knowledge"}
                or not target.endswith(".md")):
            raise ValueError("trial target must be Skill or Knowledge Markdown")
        if _inside(root, target) == _inside(root, payload["candidate"]):
            raise ValueError("candidate must be separate from target")
        _strings(payload["rules"], "rules")
        if not RULE_SOURCES <= set(payload["rules"]):
            raise ValueError("governing shared management and source-storage rules required")
        _strings(payload["specialist_evidence"], "specialist evidence", empty=True)
        _strings(payload["checks"], "checks")
        if not CORE_CHECKS <= set(payload["checks"]):
            raise ValueError("applicable rules and mandatory common checks required")
        if not {payload["candidate"], *payload["rules"], *payload["specialist_evidence"]} <= set(materials):
            raise ValueError("candidate, rules and specialist evidence must be frozen materials")
    elif kind == "correction_retrospective":
        if set(payload) != {"scope", "reason", "consent", "task_basis", "correction_evidence"}:
            raise ValueError("retrospective payload fields mismatch")
        for field in ("scope", "reason", "task_basis"):
            _text(payload[field], field)
        consent = payload["consent"]
        if (not isinstance(consent, dict) or set(consent) != {"intent", "scope", "evidence"}
                or consent["intent"] != "execute_retrospective"
                or consent["scope"] != payload["scope"] or consent["evidence"] not in materials):
            raise ValueError("explicit scope-bound human execution instruction is required")
        _strings(payload["correction_evidence"], "correction evidence")
        if not set(payload["correction_evidence"]) <= set(materials):
            raise ValueError("correction evidence must be frozen")
    else:
        raise ValueError("unsupported governance entry kind")


def prepare(root: Path, *, kind: str, log: str, binding_request: dict,
            materials: list[str], payload: dict) -> dict:
    """Freeze scoped work, materials and an existing workflow execution binding."""
    root = root.resolve()
    if kind not in {"asset_update", "correction_retrospective"}:
        raise ValueError("unsupported governance entry kind")
    _strings(materials, "bounded material paths")
    binding = build_execution_binding(_inside(root, log), binding_request)
    _payload(root, kind, payload, materials, frozen=False)
    if kind == "asset_update":
        payload = {**payload, "expected_target_hash": _current(root, payload["target"])}
    body = {"schema": SCHEMA, "kind": kind, "log": log, "binding": binding,
            "materials": [snapshot(root, name) for name in sorted(materials)], "payload": payload,
            "dispatch_owner": "client_host", "parent_execution": "prohibited"}
    return {**body, "packet_hash": digest(body)}


def revalidate(root: Path, packet: dict) -> None:
    if not isinstance(packet, dict) or set(packet) != {"schema", "kind", "log", "binding", "materials", "payload", "dispatch_owner", "parent_execution", "packet_hash"}:
        raise ValueError("invalid governance packet fields")
    materials = packet["materials"]
    if (not isinstance(materials, list) or not materials
            or any(not isinstance(row, dict) or set(row) != {"path", "sha256"} for row in materials)):
        raise ValueError("invalid material snapshot list")
    names = _strings([row["path"] for row in materials], "material paths")
    _payload(root, packet["kind"], packet["payload"], names, frozen=True)
    if not isinstance(packet["binding"], dict) or packet["binding"].get("binding_origin") != "workflow_builder":
        raise ValueError("workflow-built binding required")
    body = {key: value for key, value in packet.items() if key != "packet_hash"}
    if (packet.get("schema") != SCHEMA or packet.get("packet_hash") != digest(body)
            or packet.get("dispatch_owner") != "client_host"
            or packet.get("parent_execution") != "prohibited"):
        raise ValueError("invalid governance packet identity/authority")
    log = _inside(root, packet["log"]).read_text(encoding="utf-8")
    validate_binding_context(log, packet["binding"])
    for material in packet["materials"]:
        if snapshot(root, material["path"]) != material:
            raise ValueError("governance material changed")
    if packet["kind"] == "asset_update":
        payload = packet["payload"]
        if not CORE_CHECKS <= set(payload["checks"]):
            raise ValueError("mandatory common check coverage missing")
        if _current(root, payload["target"]) != payload["expected_target_hash"]:
            raise ValueError("target baseline changed")


def dispatch(root: Path, packet: dict, host_dispatch: Callable[[dict], dict],
             host_verifier: HumanApprovalVerifier) -> dict:
    """Invoke the configured trusted host adapter, not a Python agent spawner."""
    revalidate(root, packet)
    result = host_dispatch(json.loads(json.dumps(packet)))
    validate_result(root, packet, result, host_verifier)
    return result


def validate_result(root: Path, packet: dict, receipt: dict,
                    host_verifier: HumanApprovalVerifier) -> dict:
    revalidate(root, packet)
    if not isinstance(receipt, dict) or set(receipt) != {"event", "signature"}:
        raise ValueError("trusted host execution receipt required")
    event = receipt["event"]
    if not isinstance(event, dict):
        raise ValueError("host execution event must be an object")
    host_verifier.verify_event(event, receipt["signature"])
    if (set(event) != {"schema", "packet_hash", "execution_id", "child_log", "child_log_hash",
                      "skill_id", "result", "result_hash"}
            or event["schema"] != "xrefkit.governance_execution/v1"
            or event["packet_hash"] != packet["packet_hash"]):
        raise ValueError("host execution receipt scope mismatch")
    _text(event["execution_id"], "host execution ID")
    child = _inside(root, event["child_log"])
    if snapshot(root, event["child_log"])["sha256"] != event["child_log_hash"]:
        raise ValueError("child execution log changed")
    text = child.read_text(encoding="utf-8")
    if (_log_field(text, "run_id") == packet["binding"]["run_id"]
            or not _log_field(text, "run_id")
            or _log_field(text, "parent_run_id") != packet["binding"]["run_id"]
            or _log_field(text, "root_run_id") != packet["binding"]["run_snapshot"]["fields"]["root_run_id"]
            or _log_field(text, "work_item_id") != packet["binding"]["work_item_id"]
            or _log_field(text, "skill_id") != event["skill_id"]
            or _section_status(text, "Closure Gate") != "done"):
        raise ValueError("separate completed child Skill run required")
    expected_skill = "shared_asset_update_gate" if packet["kind"] == "asset_update" else "correction_retrospective_analyst"
    if event["skill_id"] != expected_skill:
        raise ValueError("wrong analyst Skill")
    result = event["result"]
    if (not isinstance(result, dict) or result.get("packet_hash") != packet["packet_hash"]
            or event["result_hash"] != digest(result)):
        raise ValueError("analysis result binding mismatch")
    output = result.get("output")
    if not isinstance(output, dict) or set(output) != {"path", "sha256"} or snapshot(root, output["path"]) != output:
        raise ValueError("analysis output identity mismatch")
    try:
        saved = json.loads(_inside(root, output["path"]).read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("analysis output must be saved structured body") from exc
    if saved != {key: value for key, value in result.items() if key != "output"}:
        raise ValueError("saved analysis and host result differ")
    artifacts = _parse_artifacts(text)
    if not any(item["kind"] == "output" and item["status"] == "done"
               and item["target"] == output["path"] for item in artifacts):
        raise ValueError("child run must record the returned output")
    if packet["kind"] == "asset_update":
        if set(result) != {"packet_hash", "output", "findings", "unknowns", "reference_roles", "external_reference_disposition"}:
            raise ValueError("invalid gate result fields")
        findings = result["findings"]
        if (not isinstance(findings, list) or any(not isinstance(row, dict) or not isinstance(row.get("id"), str) for row in findings)
                or {row.get("id") for row in findings} != set(packet["payload"]["checks"])
                or len(findings) != len(packet["payload"]["checks"])):
            raise ValueError("gate findings must cover exactly applicable checks")
        for row in findings:
            if (set(row) != {"id", "result", "reason", "evidence"}
                    or not isinstance(row["result"], str)
                    or row["result"] not in {"pass", "fail", "unknown", "not_applicable"}
                    or not isinstance(row["evidence"], list)):
                raise ValueError("each finding requires scoped evidence and result")
            _strings(row["evidence"], "finding evidence")
            if not set(row["evidence"]) <= {m["path"] for m in packet["materials"]}:
                raise ValueError("finding evidence must be scoped")
            _text(row["reason"], "finding reason")
            if row["id"] in {"authority", "candidate_identity", "handoff"} and row["result"] == "not_applicable":
                raise ValueError("identity, authority and handoff checks cannot be waived")
        if not isinstance(result["unknowns"], list) or not isinstance(result["reference_roles"], list):
            raise ValueError("explicit unknowns/reference roles required")
        disposition = result["external_reference_disposition"]
        roles = result["reference_roles"]
        if not isinstance(disposition, str) or disposition not in {"no_external_refs", "classified"} or (disposition == "classified") != bool(roles):
            raise ValueError("explicit external reference disposition must match classified roles")
        for role in roles:
            if (not isinstance(role, dict) or set(role) != {"role", "source_locator", "used_for", "acquired_at",
                    "stored_source", "fixed_identifier", "refresh_condition", "source_exception", "exception_evidence"}
                    or not isinstance(role["role"], str)
                    or role["role"] not in {"fixed_basis", "current_information", "navigation"}
                    or (role["source_exception"] is not None and not isinstance(role["source_exception"], str))
                    or role["source_exception"] not in {None, "xddp"}):
                raise ValueError("invalid structured external reference role")
            _text(role["source_locator"], "source locator")
            _text(role["used_for"], "reference use")
            for field in ("acquired_at", "stored_source", "fixed_identifier", "refresh_condition", "exception_evidence"):
                if role[field] is not None:
                    _text(role[field], field)
            if role["stored_source"] is not None and role["stored_source"] not in {m["path"] for m in packet["materials"]}:
                raise ValueError("stored reference source must be a frozen material")
            if role["source_exception"] == "xddp":
                if role["exception_evidence"] not in {m["path"] for m in packet["materials"]}:
                    raise ValueError("xddp source exception requires frozen evidence")
            if role["role"] == "fixed_basis":
                if role["stored_source"] is None and role["source_exception"] is None:
                    raise ValueError("fixed basis requires source storage")
                _text(role["acquired_at"], "source acquisition date")
                date.fromisoformat(role["acquired_at"])
                _text(role["fixed_identifier"], "fixed source identifier")
            if role["role"] == "current_information":
                _text(role["refresh_condition"], "current-information confirmation condition")
    else:
        if set(result) != {"packet_hash", "output", "findings", "unknowns"}:
            raise ValueError("invalid retrospective result fields")
        if not isinstance(result["findings"], list) or not isinstance(result["unknowns"], list):
            raise ValueError("retrospective findings and unknowns must be explicit lists")
        for row in result["findings"]:
            if (not isinstance(row, dict) or set(row) != {"classification", "reason", "evidence", "disposition"}
                    or not isinstance(row["classification"], str) or not isinstance(row["disposition"], str)
                    or row["classification"] not in {"application_failure", "requirement_change", "local_condition", "common_candidate", "unknown"}
                    or row["disposition"] not in {"stay_in_work", "human_review"}
                    or not isinstance(row["evidence"], list)):
                raise ValueError("retrospective findings require scoped evidence and proposal-only disposition")
            _strings(row["evidence"], "retrospective evidence")
            if not set(row["evidence"]) <= {m["path"] for m in packet["materials"]}:
                raise ValueError("retrospective evidence must be scoped")
            _text(row["reason"], "retrospective finding reason")
    return result


def apply_update(root: Path, packet: dict, receipt: dict, *,
                 host_verifier: HumanApprovalVerifier, approval_verifier: HumanApprovalVerifier,
                 approval_assertion: str) -> dict:
    """Apply one expressly approved target with cooperating-writer CAS and lock."""
    revalidate(root, packet)
    if packet["kind"] != "asset_update":
        raise ValueError("analysis consent cannot authorize publication")
    payload = packet["payload"]
    target = _inside(root, payload["target"])
    lock = root / ".xrefkit" / "governance-locks" / (digest(str(target).casefold()) + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    with _LogFileLock(lock):
        result = validate_result(root, packet, receipt, host_verifier)
        if result["unknowns"] or any(row["result"] not in {"pass", "not_applicable"} for row in result["findings"]):
            raise ValueError("unresolved or failed gate findings block application")
        claims = {"action": "apply_governed_asset", "packet_hash": packet["packet_hash"],
                  "target": payload["target"], "result_hash": digest(result)}
        approval_verifier.verify(approval_assertion, claims)
        candidate = _inside(root, payload["candidate"]).read_bytes()
        expected_candidate = next(row["sha256"] for row in packet["materials"] if row["path"] == payload["candidate"])
        if hashlib.sha256(candidate).hexdigest() != expected_candidate:
            raise ValueError("bytes selected for application differ from frozen candidate")
        revalidate(root, packet)
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".governance-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(candidate)
                stream.flush()
                os.fsync(stream.fileno())
            if payload["expected_target_hash"] is None:
                os.link(temporary, target)
            else:
                if _current(root, payload["target"]) != payload["expected_target_hash"]:
                    raise ValueError("target baseline changed before replacement")
                os.replace(temporary, target)
            reflected = snapshot(root, payload["target"])
            if reflected["sha256"] != hashlib.sha256(candidate).hexdigest():
                raise ValueError("reflection verification failed")
            return {"schema": "xrefkit.governance_reflection/v1", "packet_hash": packet["packet_hash"],
                    "target": reflected, "gate_result_hash": digest(result),
                    "adoption": "separate_human_assertion_verified", "runtime_activation": "not_performed"}
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def retrospective_suggestion(root: Path, state_path: str, *, scope: str, reason: str,
                             evidence: list[str], response: str | None = None) -> dict:
    """Persist semantic suppression; request IDs are deliberately not the key."""
    _text(scope, "scope")
    _text(reason, "reason")
    if not evidence:
        raise ValueError("substantive correction evidence required")
    if response not in {None, "declined", "deferred", "unanswered", "accepted", "human_request"}:
        raise ValueError("response must be an explicit scoped interaction")
    state = _inside(root, state_path)
    parts = state.relative_to(root.resolve()).parts
    if parts[0] != "work" and parts[:2] != (".xrefkit", "governance-entries"):
        raise ValueError("suggestion state must remain non-canonical")
    state.parent.mkdir(parents=True, exist_ok=True)
    fingerprint = digest({"scope": scope, "reason": reason,
                          "evidence": [snapshot(root, name) for name in sorted(set(evidence))]})
    with _LogFileLock(state.with_suffix(".lock")):
        records = json.loads(state.read_text(encoding="utf-8")) if state.exists() else {}
        if not isinstance(records, dict):
            raise ValueError("invalid suppression state")
        prior = records.get(fingerprint)
        suggest = prior is None and response is None
        if prior is None or response is not None:
            records[fingerprint] = {"scope": scope, "reason": reason, "response": response or "unanswered"}
        state.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return {"suggest": suggest, "scope": scope, "reason": reason,
            "analysis_authorized": response in {"accepted", "human_request"},
            "adoption_authorized": False}

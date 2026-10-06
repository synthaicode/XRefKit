"""Strict external maturity and promotion records for SkillDefinition v1."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

MAX_RECORD_BYTES = 128 * 1024
MATURITIES = {"draft", "trial", "stable", "governed", "deprecated"}
DECISIONS = {"not_requested", "approved", "rejected"}
XID_RE = re.compile(r"^[A-F0-9]{12}$")
HASH_RE = re.compile(r"^[a-f0-9]{64}$")
SKILL_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
TOP_KEYS = {"schema_version", "skill_id", "definition_xid", "definition_content_hash", "maturity", "observation_refs", "governance_refs", "promotion"}
PROMOTION_KEYS = {"decision", "target_maturity", "authority", "decided_at", "basis_refs"}

def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate governance record key: {key}")
        result[key] = value
    return result

def _strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a string list")
    if any(not item.strip() for item in value):
        raise ValueError(f"{field} items must be nonempty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} must not contain duplicates")
    return value

def _validate_iso(value: Any, field: str) -> None:
    if value is not None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be string or null")
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{field} must be ISO-8601") from exc

def validate_governance_record(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != TOP_KEYS:
        raise ValueError("governance record must have exact required keys")
    if value["schema_version"] != 1 or isinstance(value["schema_version"], bool):
        raise ValueError("schema_version must be 1")
    if not isinstance(value["skill_id"], str) or not SKILL_ID_RE.fullmatch(value["skill_id"]):
        raise ValueError("skill_id must match lowercase snake ID format")
    if not isinstance(value["definition_xid"], str) or not XID_RE.fullmatch(value["definition_xid"]):
        raise ValueError("definition_xid must be 12 uppercase hexadecimal characters")
    if not isinstance(value["definition_content_hash"], str) or not HASH_RE.fullmatch(value["definition_content_hash"]):
        raise ValueError("definition_content_hash must be 64 lowercase hexadecimal characters")
    if value["maturity"] not in MATURITIES:
        raise ValueError("invalid maturity")
    observations = _strings(value["observation_refs"], "observation_refs")
    governance = _strings(value["governance_refs"], "governance_refs")
    promotion = value["promotion"]
    if not isinstance(promotion, dict) or set(promotion) != PROMOTION_KEYS:
        raise ValueError("promotion must have exact required keys")
    if promotion["decision"] not in DECISIONS:
        raise ValueError("invalid promotion decision")
    target = promotion["target_maturity"]
    if target is not None and target not in MATURITIES:
        raise ValueError("invalid promotion target_maturity")
    if promotion["authority"] is not None and not isinstance(promotion["authority"], str):
        raise ValueError("promotion authority must be string or null")
    _validate_iso(promotion["decided_at"], "promotion decided_at")
    basis = _strings(promotion["basis_refs"], "promotion basis_refs")
    decision = promotion["decision"]
    if decision == "not_requested":
        if value["maturity"] != "draft" or target is not None or promotion["authority"] is not None or promotion["decided_at"] is not None or basis:
            raise ValueError("not_requested requires draft and null/empty promotion fields")
    elif decision == "approved":
        if target != value["maturity"]:
            raise ValueError("approved target_maturity must equal maturity")
    else:
        if target is None or target == value["maturity"]:
            raise ValueError("rejected target_maturity must differ from maturity")
    if value["maturity"] in {"trial", "stable", "governed"} and not observations:
        raise ValueError("trial/stable/governed requires observation_refs")
    if value["maturity"] == "governed" and not governance:
        raise ValueError("governed requires governance_refs")
    if promotion["decision"] in {"approved", "rejected"}:
        if not promotion["authority"] or not promotion["decided_at"] or not basis:
            raise ValueError("approved/rejected promotion requires authority, decided_at, and basis_refs")
    return value

def load_governance_record(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) > MAX_RECORD_BYTES:
        raise ValueError("governance record exceeds 128KB")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid governance JSON: {exc}") from exc
    result = dict(validate_governance_record(value))
    result["_path"] = path.as_posix()
    result["_content_hash"] = hashlib.sha256(raw).hexdigest()
    return result

def match_definition(record: dict[str, Any], definition: dict[str, Any]) -> None:
    metadata = definition["metadata"]
    if record["skill_id"] != metadata["skill_id"] or record["definition_xid"] != metadata["xid"]:
        raise ValueError("governance record identity does not match definition")
    if record["definition_content_hash"] != definition["content_hash"]:
        raise ValueError("governance record definition_content_hash does not match definition")


def governance_projection(record: dict[str, Any]) -> dict[str, Any]:
    """Return catalog-safe governance state without the bound definition body."""
    return {
        "record_ref": {
            "path": record["_path"],
            "content_hash": record["_content_hash"],
        },
        "maturity": record["maturity"],
        "observation_refs": list(record["observation_refs"]),
        "governance_refs": list(record["governance_refs"]),
        "promotion": dict(record["promotion"]),
    }


__all__ = [
    "governance_projection",
    "load_governance_record",
    "match_definition",
    "validate_governance_record",
]

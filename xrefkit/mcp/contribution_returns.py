"""Inert MCP inbox for Knowledge, deterministic tools, and Skill observations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .audit import SessionRunBinding, _process_lock
from .contribution_adoption import (
    AdoptionFile,
    CanonicalAdoptionTransport,
    HumanApprovalVerifier,
    LocalCanonicalAdoptionTransport,
)
from .ownership import Ownership, load_ownership
from .repository import first_xid

SCHEMA = "xrefkit.contribution_return/v1"
REVIEW_SCHEMA = "xrefkit.contribution_review/v1"
ADOPTION_PREPARED_SCHEMA = "xrefkit.contribution_adoption_prepared/v1"
ADOPTION_SCHEMA = "xrefkit.contribution_adoption/v1"
STORE_RELATIVE = Path(".xrefkit") / "contribution-returns"
ALLOWED_KINDS = {"knowledge", "deterministic_tool", "skill_observation"}
VALID_MATURITIES = {"draft", "trial", "stable", "governed", "deprecated"}
VALID_OBSERVATION_OUTCOMES = {"success", "failure"}
VALID_HUMAN_EVALUATIONS = {"accepted", "rejected", "needs_revision"}
MAX_FILES = 64
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 5 * 1024 * 1024
MAX_METADATA_BYTES = 256 * 1024
MAX_TITLE_BYTES = 256
MAX_SUMMARY_BYTES = 4096
MAX_RUNTIME_BYTES = 256
MAX_IDENTIFIER_BYTES = 256
MAX_OBSERVATION_RETRIES = 1000
MAX_EVIDENCE_ROWS = 64
MAX_EVIDENCE_TEXT_BYTES = 4096
MAX_KNOWLEDGE_VERSIONS = 128
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 4096
MAX_JSON_STRING_BYTES = 64 * 1024
MAX_JSON_KEY_BYTES = 1024
MAX_PATH_BYTES = 1024
MAX_REVIEWER_BYTES = 512
MAX_DECISION_EVIDENCE_BYTES = 16 * 1024
MAX_NETWORK_REQUEST_BYTES = 8 * 1024 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}")
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


def contribution_return_contract() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "status": "pending_review",
        "allowed_kinds": sorted(ALLOWED_KINDS),
        "hash_algorithm": "sha256",
        "limits": {
            "max_files": MAX_FILES,
            "max_file_bytes": MAX_FILE_BYTES,
            "max_total_bytes": MAX_TOTAL_BYTES,
            "max_metadata_bytes": MAX_METADATA_BYTES,
            "max_title_bytes": MAX_TITLE_BYTES,
            "max_summary_bytes": MAX_SUMMARY_BYTES,
            "max_runtime_bytes": MAX_RUNTIME_BYTES,
            "max_evidence_rows": MAX_EVIDENCE_ROWS,
            "max_evidence_text_bytes": MAX_EVIDENCE_TEXT_BYTES,
            "max_knowledge_versions": MAX_KNOWLEDGE_VERSIONS,
            "max_json_depth": MAX_JSON_DEPTH,
            "max_json_nodes": MAX_JSON_NODES,
            "max_json_string_bytes": MAX_JSON_STRING_BYTES,
            "max_json_key_bytes": MAX_JSON_KEY_BYTES,
            "max_path_bytes": MAX_PATH_BYTES,
            "max_network_request_bytes": MAX_NETWORK_REQUEST_BYTES,
        },
        "file_schema": {
            "path": "safe relative POSIX path",
            "content": "UTF-8 text",
            "content_hash": "lowercase SHA-256 hex of UTF-8 content",
        },
        "knowledge_schema": {"xid": "string", "files": "exactly one Markdown file"},
        "deterministic_tool_schema": {
            "runtime": "non-empty string",
            "entrypoint": "path of a submitted file",
            "input_contract": "object",
            "output_contract": "object",
            "verification_evidence": "non-empty array of {kind, command, result, content_hash?}",
        },
        "skill_observation_schema": {
            "skill_id": "selected MCP Skill identity",
            "skill_content_hash": "exact selected Skill SHA-256",
            "skill_version": "optional package/source version used",
            "maturity_at_use": "draft|trial|stable|governed|deprecated",
            "run_id": "bound Skill Run UUID",
            "client_id": "bounded non-secret client installation identifier",
            "execution_environment": "bounded non-secret environment identifier",
            "model_id": "bounded non-secret model identifier",
            "outcome": "success|failure",
            "retry_count": f"integer from 0 through {MAX_OBSERVATION_RETRIES}",
            "evaluation_evidence": "non-empty array of evidence identity/reference/hash rows",
            "ambiguities": "array of bounded observations; empty is allowed",
            "human_evaluation": "optional explicit human evaluation record",
            "proposed_maturity": "optional client proposal without authority",
            "sensitive_data": "prompt bodies, credentials, tokens, secrets, and secret-bearing fields are prohibited",
            "files": "exactly one inert Markdown observation",
        },
        "source_schema": {
            "skill_content_hash": "current selected Skill SHA-256",
            "knowledge_versions": "array of {xid, content_hash} actually used",
            "package_id": "optional package identity used to disambiguate the Skill",
        },
        "review_schema": {
            "decision_id": "UUID",
            "decision": "accepted|rejected",
            "reviewer": "explicit human reviewer identity",
            "decision_evidence": "non-empty human decision basis",
            "approved_target_path": "required for accepted; validated canonical repository path",
            "approval_token": "one-time secret returned only when acceptance is first recorded",
        },
        "canonical_target_policy": {
            "proposal": "proposed_target_path is AI-supplied evidence only, never authority",
            "knowledge": "one Markdown file under a catalog-enabled knowledge family",
            "deterministic_tool": "one complete directory below tools/ in the kernel-code ownership zone",
            "skill_observation": "one Markdown record under observations/; transport grants no maturity authority",
            "collision": "never overwrite an existing canonical target",
        },
        "adoption_transport": {
            "local": "atomic file publication or directory move",
            "webdav": "server-side conditional MOVE with ETag, If-Match, and Overwrite:F",
            "credentials": "server configuration only; never returned to the MCP client",
        },
        "ordering": [
            "get_startup_context",
            "get_skill or get_skill_requirements",
            "bind_skill_run",
            "get_contribution_return_contract",
            "submit_contribution_return",
            "list_contribution_returns or export_contribution_return",
            "review_contribution_return (explicit human decision)",
            "adopt_contribution_return (accepted records only)",
            "commit the adopted observation so Git tracks it",
            "assess, propose, review, and apply maturity as a separate human-approved flow",
        ],
        "activation": "never automatic; adoption is explicit and does not execute tools",
        "later_lifecycle": {
            "publication": "not_performed",
            "distribution": "not_performed",
            "live_verification": "not_performed",
        },
    }


def submit_contribution_return(
    root: Path,
    *,
    binding: SessionRunBinding,
    source_snapshot: dict[str, Any],
    contribution_id: str,
    kind: str,
    title: str,
    summary: str,
    files: list[dict[str, Any]],
    proposed_target_path: str | None = None,
    knowledge: dict[str, Any] | None = None,
    deterministic_tool: dict[str, Any] | None = None,
    skill_observation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_id = _uuid(contribution_id)
    normalized_files = _validate_files(files)
    normalized_kind = str(kind).strip()
    if normalized_kind not in ALLOWED_KINDS:
        raise ValueError(f"unsupported contribution kind: {kind}")
    normalized_title = _required_text(title, "title", MAX_TITLE_BYTES)
    normalized_summary = _required_text(summary, "summary", MAX_SUMMARY_BYTES)
    kind_metadata = _validate_kind_metadata(
        normalized_kind,
        normalized_files,
        knowledge,
        deterministic_tool,
        skill_observation,
    )
    if normalized_kind == "skill_observation":
        _validate_skill_observation_source(kind_metadata, source_snapshot, binding)
    normalized_proposed_target = (
        _safe_path(proposed_target_path) if proposed_target_path is not None else None
    )
    payload = {
        "contribution_id": normalized_id,
        "kind": normalized_kind,
        "title": normalized_title,
        "summary": normalized_summary,
        "files": normalized_files,
        "kind_metadata": kind_metadata,
        "proposed_target_path": normalized_proposed_target,
        "source": source_snapshot,
        "binding": binding.to_dict(),
    }
    metadata_payload = {
        **payload,
        "files": [
            {key: item[key] for key in ("path", "content_hash", "byte_count")}
            for item in normalized_files
        ],
    }
    _validate_json_shape(metadata_payload)
    metadata_bytes = len(_canonical_json(metadata_payload))
    if metadata_bytes > MAX_METADATA_BYTES:
        raise ValueError(f"contribution metadata exceeds byte limit {MAX_METADATA_BYTES}")
    payload_hash = _canonical_hash(payload)
    store = root.resolve() / STORE_RELATIVE
    store.mkdir(parents=True, exist_ok=True)
    final_dir = store / normalized_id
    lock_path = store / "inbox"
    with _process_lock(lock_path):
        if final_dir.exists():
            return _existing_result(final_dir, payload_hash)
        temp_dir = store / f".{normalized_id}.{uuid.uuid4().hex}.tmp"
        try:
            temp_dir.mkdir()
            content_dir = temp_dir / "files"
            content_dir.mkdir()
            for item in normalized_files:
                target = content_dir.joinpath(*PurePosixPath(item["path"]).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                _write_fsynced(target, item["content"])
            manifest = {
                "schema": SCHEMA,
                "contribution_id": normalized_id,
                "status": "pending_review",
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "payload_hash": payload_hash,
                "kind": normalized_kind,
                "title": normalized_title,
                "summary": normalized_summary,
                "files": [
                    {key: item[key] for key in ("path", "content_hash", "byte_count")}
                    for item in normalized_files
                ],
                "kind_metadata": kind_metadata,
                "proposed_target_path": normalized_proposed_target,
                "source": source_snapshot,
                "binding": binding.to_dict(),
                "limits_version": 1,
            }
            _write_fsynced(
                temp_dir / "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
            os.replace(temp_dir, final_dir)
        except Exception:
            shutil.rmtree(temp_dir, ignore_errors=True)
            if final_dir.exists():
                return _existing_result(final_dir, payload_hash)
            raise
    return {**manifest, "created": True, "idempotent_replay": False}


def list_contribution_returns(
    root: Path,
    approval_verifier: HumanApprovalVerifier | None = None,
) -> list[dict[str, Any]]:
    store = root.resolve() / STORE_RELATIVE
    if not store.exists():
        return []
    result = []
    for path in sorted(store.iterdir()):
        if not path.is_dir() or path.name.startswith("."):
            continue
        manifest_path = path / "manifest.json"
        if manifest_path.is_file():
            manifest = _read_manifest(manifest_path)
            _verify_manifest_payload(path, manifest)
            result.append(
                _record_summary(
                    path,
                    manifest,
                    approval_verifier=approval_verifier,
                )
            )
    return result


def export_contribution_return(
    root: Path,
    contribution_id: str,
    approval_verifier: HumanApprovalVerifier | None = None,
) -> dict[str, Any]:
    normalized_id = _uuid(contribution_id)
    record_dir = root.resolve() / STORE_RELATIVE / normalized_id
    manifest = _read_manifest(record_dir / "manifest.json")
    _verify_manifest_payload(record_dir, manifest)
    _verify_manifest_payload(record_dir, manifest)
    exported_files = []
    for item in manifest["files"]:
        content = (record_dir / "files").joinpath(*PurePosixPath(item["path"]).parts).read_text(
            encoding="utf-8"
        )
        if _sha256(content) != item["content_hash"]:
            raise ValueError(f"stored contribution file hash mismatch: {item['path']}")
        exported_files.append({**item, "content": content})
    return {
        "schema": SCHEMA,
        "review_bundle": {
            **_record_summary(
                record_dir,
                manifest,
                approval_verifier=approval_verifier,
            ),
            "files": exported_files,
            "events": _record_events(record_dir, approval_verifier=approval_verifier),
        },
        "activation_performed": False,
        "adoption_performed": (record_dir / "events" / "adoption.json").is_file(),
        "next_step": _next_step(record_dir, approval_verifier=approval_verifier),
    }


def review_contribution_return(
    root: Path,
    *,
    contribution_id: str,
    decision_id: str,
    decision: str,
    reviewer: str,
    decision_evidence: str,
    approval_assertion: str,
    approved_target_path: str | None = None,
    approval_verifier: HumanApprovalVerifier | None = None,
    ownership: Ownership | None = None,
    existing_knowledge_xids: set[str] | None = None,
) -> dict[str, Any]:
    """Record one immutable human review decision without canonical mutation."""
    normalized_id = _uuid(contribution_id)
    normalized_decision_id = _uuid(decision_id, "decision_id")
    normalized_decision = str(decision).strip().lower()
    if normalized_decision not in {"accepted", "rejected"}:
        raise ValueError("decision must be accepted or rejected")
    normalized_reviewer = _required_text(reviewer, "reviewer", MAX_REVIEWER_BYTES)
    normalized_evidence = _required_text(
        decision_evidence, "decision_evidence", MAX_DECISION_EVIDENCE_BYTES
    )
    record_dir = root.resolve() / STORE_RELATIVE / normalized_id
    manifest = _read_manifest(record_dir / "manifest.json")
    _verify_manifest_payload(record_dir, manifest)
    proposed = manifest.get("proposed_target_path")
    if normalized_decision == "accepted":
        if approved_target_path is None:
            raise ValueError("approved_target_path is required for an accepted decision")
        target = approved_target_path
        normalized_target = _validate_canonical_target(
            root.resolve(),
            manifest,
            target,
            ownership=ownership,
            existing_knowledge_xids=existing_knowledge_xids,
        )
    else:
        if approved_target_path is not None:
            raise ValueError("approved_target_path is not allowed for a rejected decision")
        normalized_target = None
    if approval_verifier is None:
        raise RuntimeError("trusted human approval verifier is not configured")
    normalized_assertion = _required_text(
        approval_assertion, "approval_assertion", MAX_DECISION_EVIDENCE_BYTES
    )
    request_basis = {
        "schema": REVIEW_SCHEMA,
        "event": "review_decided",
        "contribution_id": normalized_id,
        "decision_id": normalized_decision_id,
        "decision": normalized_decision,
        "reviewer": normalized_reviewer,
        "decision_evidence": normalized_evidence,
        "payload_hash": manifest["payload_hash"],
        "proposed_target_path": proposed,
        "proposed_target_path_hash": _optional_path_hash(proposed),
        "approved_target_path": normalized_target,
        "approved_target_path_hash": _optional_path_hash(normalized_target),
    }
    approval_claims = approval_verifier.verify(
        normalized_assertion,
        {
            "contribution_id": normalized_id,
            "decision_id": normalized_decision_id,
            "decision": normalized_decision,
            "reviewer": normalized_reviewer,
            "payload_hash": manifest["payload_hash"],
            "proposed_target_path": proposed,
            "proposed_target_path_hash": _optional_path_hash(proposed),
            "approved_target_path": normalized_target,
            "approved_target_path_hash": _optional_path_hash(normalized_target),
        },
    )
    request_basis["approval_assertion_id"] = str(
        approval_claims.get("assertion_id") or ""
    )
    if not request_basis["approval_assertion_id"]:
        raise ValueError("human approval assertion is missing assertion_id")
    events = record_dir / "events"
    with _process_lock(record_dir / "review"):
        review_path = events / "review.json"
        if review_path.exists():
            existing = _read_event(
                review_path,
                REVIEW_SCHEMA,
                approval_verifier=approval_verifier,
            )
            existing_request = {
                key: value
                for key, value in existing.items()
                if key not in {
                    "approval_token_hash",
                    "review_binding_hash",
                    "decided_at",
                    "event_hash",
                    "server_signature",
                }
            }
            if existing_request != request_basis:
                raise ValueError("contribution already has a different immutable review decision")
            return {
                **existing,
                "created": False,
                "idempotent_replay": True,
                "approval_token": None,
            }
        token = secrets.token_urlsafe(32) if normalized_decision == "accepted" else None
        event_basis = {
            **request_basis,
            "approval_token_hash": _sha256(token) if token else None,
        }
        event_basis["review_binding_hash"] = _canonical_hash(event_basis)
        event = _seal_event(
            {**event_basis, "decided_at": _now()},
            approval_verifier,
        )
        _write_json_once(review_path, event)
    return {
        **event,
        "created": True,
        "idempotent_replay": False,
        "approval_token": token,
    }


def adopt_contribution_return(
    root: Path,
    *,
    contribution_id: str,
    adoption_id: str,
    reviewer: str,
    decision_evidence: str,
    approval_token: str,
    approval_verifier: HumanApprovalVerifier | None = None,
    transport: CanonicalAdoptionTransport | None = None,
    ownership: Ownership | None = None,
    existing_knowledge_xids: set[str] | None = None,
    existing_knowledge_xid_locations: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    """Promote an accepted contribution through a server-owned transport."""
    repo = root.resolve()
    normalized_id = _uuid(contribution_id)
    normalized_adoption_id = _uuid(adoption_id, "adoption_id")
    normalized_reviewer = _required_text(reviewer, "reviewer", MAX_REVIEWER_BYTES)
    normalized_evidence = _required_text(
        decision_evidence, "decision_evidence", MAX_DECISION_EVIDENCE_BYTES
    )
    normalized_token = _required_text(approval_token, "approval_token", 1024)
    record_dir = repo / STORE_RELATIVE / normalized_id
    manifest = _read_manifest(record_dir / "manifest.json")
    _verify_manifest_payload(record_dir, manifest)
    if approval_verifier is None:
        raise RuntimeError("trusted human approval verifier is not configured")
    review = _read_event(
        record_dir / "events" / "review.json",
        REVIEW_SCHEMA,
        approval_verifier=approval_verifier,
    )
    if review.get("decision") != "accepted":
        raise ValueError("only an accepted contribution can be adopted")
    _verify_review_binding(manifest, review)
    if not secrets.compare_digest(
        str(review.get("approval_token_hash", "")), _sha256(normalized_token)
    ):
        raise ValueError("approval_token does not match the accepted human review")
    with _process_lock(repo / STORE_RELATIVE / "canonical-adoption"):
        # Re-read every persisted binding under the repository-wide publish
        # lock. The earlier validation gives fast feedback; this one closes the
        # mutation window immediately before canonical target validation and
        # transport promotion.
        manifest = _read_manifest(record_dir / "manifest.json")
        _verify_manifest_payload(record_dir, manifest)
        review = _read_event(
            record_dir / "events" / "review.json",
            REVIEW_SCHEMA,
            approval_verifier=approval_verifier,
        )
        if review.get("decision") != "accepted":
            raise ValueError("only an accepted contribution can be adopted")
        _verify_review_binding(manifest, review)
        if not secrets.compare_digest(
            str(review.get("approval_token_hash", "")), _sha256(normalized_token)
        ):
            raise ValueError("approval_token does not match the accepted human review")
        repository_xid_paths = _repository_xid_paths(repo, ownership)
        unlocated_existing_xids = set(existing_knowledge_xids or set()).difference(
            existing_knowledge_xid_locations or {}
        )
        known_xids = set(existing_knowledge_xids or set())
        known_xids.update(existing_knowledge_xid_locations or {})
        known_xids.update(repository_xid_paths)
        target = _validate_canonical_target(
            repo,
            manifest,
            review.get("approved_target_path"),
            ownership=ownership,
            existing_knowledge_xids=known_xids,
            existing_knowledge_xid_locations=existing_knowledge_xid_locations,
            unlocated_existing_knowledge_xids=unlocated_existing_xids,
            repository_xid_paths=repository_xid_paths,
            allow_same_xid_after_prepare=(
                record_dir / "events" / "adoption-prepared.json"
            ).is_file(),
        )
        files = _stored_files(record_dir, manifest)
        adapter = transport or LocalCanonicalAdoptionTransport()
        prepared_basis = {
            "schema": ADOPTION_PREPARED_SCHEMA,
            "event": "adoption_prepared",
            "contribution_id": normalized_id,
            "adoption_id": normalized_adoption_id,
            "reviewer": normalized_reviewer,
            "decision_evidence": normalized_evidence,
            "payload_hash": manifest["payload_hash"],
            "review_binding_hash": review["review_binding_hash"],
            "approved_target_path": target,
            "approved_target_path_hash": _optional_path_hash(target),
            "transport": adapter.name,
        }
        with _process_lock(record_dir / "adoption"):
            adoption_path = record_dir / "events" / "adoption.json"
            if adoption_path.exists():
                existing = _read_event(
                    adoption_path,
                    ADOPTION_SCHEMA,
                    approval_verifier=approval_verifier,
                )
                if existing.get("prepared_binding_hash") != _canonical_hash(prepared_basis):
                    raise ValueError("contribution already has a different immutable adoption")
                return {**existing, "created": False, "idempotent_replay": True}
            prepared_path = record_dir / "events" / "adoption-prepared.json"
            prepared_existed = prepared_path.exists()
            if prepared_existed:
                prepared = _read_event(
                    prepared_path,
                    ADOPTION_PREPARED_SCHEMA,
                    approval_verifier=approval_verifier,
                )
                if _event_comparison(prepared) != prepared_basis:
                    raise ValueError("contribution has a different immutable prepared adoption")
            else:
                prepared = _seal_event(
                    {**prepared_basis, "prepared_at": _now()},
                    approval_verifier,
                )
                _write_json_once(prepared_path, prepared)
            result = adapter.adopt(
                root=repo,
                record_dir=record_dir,
                contribution_id=normalized_id,
                adoption_id=normalized_adoption_id,
                kind=manifest["kind"],
                target_path=target,
                files=files,
                recovery_allowed=prepared_existed,
            )
            event = _seal_event({
                "schema": ADOPTION_SCHEMA,
                "event": "adopted",
                "contribution_id": normalized_id,
                "adoption_id": normalized_adoption_id,
                "status": "adopted",
                "adopted_at": _now(),
                "payload_hash": manifest["payload_hash"],
                "review_binding_hash": review["review_binding_hash"],
                "prepared_binding_hash": _canonical_hash(prepared_basis),
                "canonical_target": target,
                "canonical_files": [
                    {
                        "path": path,
                        "content_hash": item.content_hash,
                    }
                    for path, item in zip(result["target_paths"], files, strict=True)
                ],
                "transport": result,
                "publication": "not_performed",
                "distribution": "not_performed",
                "live_verification": "not_performed",
                "tool_execution_performed": False,
            }, approval_verifier)
            _write_json_once(adoption_path, event)
    return {**event, "created": True, "idempotent_replay": False}


def _validate_files(files: object) -> list[dict[str, Any]]:
    if not isinstance(files, list) or not files:
        raise ValueError("files must be a non-empty array")
    if len(files) > MAX_FILES:
        raise ValueError(f"file count exceeds limit {MAX_FILES}")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    total = 0
    for raw in files:
        if not isinstance(raw, dict):
            raise ValueError("each file must be an object")
        path = _safe_path(raw.get("path"))
        path_key = path.casefold()
        if path_key in seen:
            raise ValueError(f"duplicate contribution path: {path}")
        seen.add(path_key)
        content = raw.get("content")
        if not isinstance(content, str):
            raise ValueError(f"file content must be UTF-8 text: {path}")
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_FILE_BYTES:
            raise ValueError(f"file exceeds byte limit: {path}")
        total += len(encoded)
        supplied_hash = str(raw.get("content_hash", ""))
        if not SHA256_RE.fullmatch(supplied_hash) or supplied_hash != hashlib.sha256(encoded).hexdigest():
            raise ValueError(f"content_hash mismatch: {path}")
        result.append({
            "path": path,
            "content": content,
            "content_hash": supplied_hash,
            "byte_count": len(encoded),
        })
    if total > MAX_TOTAL_BYTES:
        raise ValueError(f"total contribution bytes exceed limit {MAX_TOTAL_BYTES}")
    return sorted(result, key=lambda item: item["path"])


def _validate_kind_metadata(
    kind: str,
    files: list[dict[str, Any]],
    knowledge: dict[str, Any] | None,
    deterministic_tool: dict[str, Any] | None,
    skill_observation: dict[str, Any] | None,
) -> dict[str, Any]:
    if kind == "knowledge":
        if deterministic_tool is not None or skill_observation is not None or not isinstance(knowledge, dict):
            raise ValueError("knowledge metadata is required only for knowledge contributions")
        if len(files) != 1 or not files[0]["path"].lower().endswith(".md"):
            raise ValueError("Knowledge contribution requires exactly one Markdown file")
        xid = _required_text(knowledge.get("xid"), "knowledge.xid")
        if first_xid(files[0]["content"]) != xid:
            raise ValueError("Knowledge XID must match the first XID marker")
        return {"xid": xid}
    if kind == "skill_observation":
        if knowledge is not None or deterministic_tool is not None or not isinstance(skill_observation, dict):
            raise ValueError("skill_observation metadata is required only for skill_observation contributions")
        if len(files) != 1 or not files[0]["path"].lower().endswith(".md"):
            raise ValueError("Skill observation requires exactly one Markdown file")
        return _validate_skill_observation_metadata(skill_observation)
    if knowledge is not None or skill_observation is not None or not isinstance(deterministic_tool, dict):
        raise ValueError("deterministic_tool metadata is required only for deterministic_tool contributions")
    runtime = _required_text(
        deterministic_tool.get("runtime"), "deterministic_tool.runtime", MAX_RUNTIME_BYTES
    )
    entrypoint = _safe_path(deterministic_tool.get("entrypoint"))
    if entrypoint not in {item["path"] for item in files}:
        raise ValueError("deterministic_tool.entrypoint must name a submitted file")
    input_contract = deterministic_tool.get("input_contract")
    output_contract = deterministic_tool.get("output_contract")
    if not isinstance(input_contract, dict) or not isinstance(output_contract, dict):
        raise ValueError("deterministic tool input_contract and output_contract must be objects")
    evidence = deterministic_tool.get("verification_evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("deterministic tool verification_evidence must be non-empty")
    if len(evidence) > MAX_EVIDENCE_ROWS:
        raise ValueError(f"verification evidence exceeds row limit {MAX_EVIDENCE_ROWS}")
    normalized_evidence = []
    for row in evidence:
        if not isinstance(row, dict):
            raise ValueError("verification evidence rows must be objects")
        item = {
            "kind": _required_text(
                row.get("kind"), "verification_evidence.kind", MAX_EVIDENCE_TEXT_BYTES
            ),
            "command": _required_text(
                row.get("command"), "verification_evidence.command", MAX_EVIDENCE_TEXT_BYTES
            ),
            "result": _required_text(
                row.get("result"), "verification_evidence.result", MAX_EVIDENCE_TEXT_BYTES
            ),
        }
        if row.get("content_hash") is not None:
            value = str(row["content_hash"])
            if not SHA256_RE.fullmatch(value):
                raise ValueError("verification evidence content_hash must be lowercase SHA-256")
            item["content_hash"] = value
        normalized_evidence.append(item)
    return {
        "runtime": runtime,
        "entrypoint": entrypoint,
        "input_contract": input_contract,
        "output_contract": output_contract,
        "verification_evidence": normalized_evidence,
    }


def _validate_skill_observation_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "skill_id", "skill_content_hash", "skill_version", "maturity_at_use",
        "run_id", "client_id", "execution_environment", "model_id", "outcome",
        "retry_count", "evaluation_evidence", "ambiguities", "human_evaluation",
        "proposed_maturity",
    }
    unknown = sorted(set(raw).difference(allowed))
    if unknown:
        raise ValueError(f"skill_observation contains unsupported or sensitive fields: {unknown}")
    result: dict[str, Any] = {
        "skill_id": _safe_identifier(raw.get("skill_id"), "skill_observation.skill_id"),
        "skill_content_hash": _sha256_value(
            raw.get("skill_content_hash"), "skill_observation.skill_content_hash"
        ),
        "maturity_at_use": _maturity(raw.get("maturity_at_use"), "maturity_at_use"),
        "run_id": _uuid(raw.get("run_id"), "skill_observation.run_id"),
        "client_id": _safe_identifier(raw.get("client_id"), "skill_observation.client_id"),
        "execution_environment": _safe_identifier(
            raw.get("execution_environment"), "skill_observation.execution_environment"
        ),
        "model_id": _safe_identifier(raw.get("model_id"), "skill_observation.model_id"),
    }
    outcome = str(raw.get("outcome") or "").strip().lower()
    if outcome not in VALID_OBSERVATION_OUTCOMES:
        raise ValueError("skill_observation.outcome must be success or failure")
    result["outcome"] = outcome
    retry_count = raw.get("retry_count")
    if isinstance(retry_count, bool) or not isinstance(retry_count, int) or not 0 <= retry_count <= MAX_OBSERVATION_RETRIES:
        raise ValueError(
            f"skill_observation.retry_count must be an integer from 0 through {MAX_OBSERVATION_RETRIES}"
        )
    result["retry_count"] = retry_count
    version = raw.get("skill_version")
    result["skill_version"] = (
        _safe_identifier(version, "skill_observation.skill_version")
        if version is not None else None
    )
    evidence = raw.get("evaluation_evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("skill_observation.evaluation_evidence must be a non-empty array")
    if len(evidence) > MAX_EVIDENCE_ROWS:
        raise ValueError(f"skill_observation evidence exceeds row limit {MAX_EVIDENCE_ROWS}")
    normalized_evidence: list[dict[str, Any]] = []
    evidence_ids: set[str] = set()
    for row in evidence:
        if not isinstance(row, dict) or set(row).difference({"evidence_id", "kind", "reference", "content_hash"}):
            raise ValueError("skill_observation evidence rows contain unsupported fields")
        item = {
            "evidence_id": _safe_identifier(row.get("evidence_id"), "evaluation_evidence.evidence_id"),
            "kind": _safe_identifier(row.get("kind"), "evaluation_evidence.kind"),
            "reference": _required_text(
                row.get("reference"), "evaluation_evidence.reference", MAX_EVIDENCE_TEXT_BYTES
            ),
        }
        if item["evidence_id"] in evidence_ids:
            raise ValueError("skill_observation evidence_id values must be unique")
        evidence_ids.add(item["evidence_id"])
        if row.get("content_hash") is not None:
            item["content_hash"] = _sha256_value(
                row.get("content_hash"), "evaluation_evidence.content_hash"
            )
        normalized_evidence.append(item)
    result["evaluation_evidence"] = normalized_evidence
    ambiguities = raw.get("ambiguities", [])
    if not isinstance(ambiguities, list) or len(ambiguities) > MAX_EVIDENCE_ROWS:
        raise ValueError("skill_observation.ambiguities must be a bounded array")
    result["ambiguities"] = [
        _required_text(item, "skill_observation.ambiguities", MAX_EVIDENCE_TEXT_BYTES)
        for item in ambiguities
    ]
    human = raw.get("human_evaluation")
    if human is not None:
        if not isinstance(human, dict) or set(human).difference(
            {"evaluation_id", "evaluator", "result", "evidence"}
        ):
            raise ValueError("skill_observation.human_evaluation contains unsupported fields")
        human_result = str(human.get("result") or "").strip().lower()
        if human_result not in VALID_HUMAN_EVALUATIONS:
            raise ValueError("human_evaluation.result is invalid")
        result["human_evaluation"] = {
            "evaluation_id": _safe_identifier(human.get("evaluation_id"), "human_evaluation.evaluation_id"),
            "evaluator": _safe_identifier(human.get("evaluator"), "human_evaluation.evaluator"),
            "result": human_result,
            "evidence": _required_text(
                human.get("evidence"), "human_evaluation.evidence", MAX_EVIDENCE_TEXT_BYTES
            ),
        }
    else:
        result["human_evaluation"] = None
    proposed = raw.get("proposed_maturity")
    result["proposed_maturity"] = (
        _maturity(proposed, "proposed_maturity") if proposed is not None else None
    )
    return result


def _validate_skill_observation_source(
    metadata: dict[str, Any], source: dict[str, Any], binding: SessionRunBinding
) -> None:
    if metadata["skill_id"] != source.get("skill_id") or metadata["skill_id"] != binding.skill_id:
        raise ValueError("skill_observation.skill_id must match the bound MCP Skill")
    if metadata["skill_content_hash"] != source.get("skill_content_hash"):
        raise ValueError("skill_observation.skill_content_hash must match the verified MCP Skill body")
    if source.get("skill_maturity") is not None and metadata["maturity_at_use"] != source.get("skill_maturity"):
        raise ValueError("skill_observation.maturity_at_use must match the verified MCP Skill maturity")
    if metadata["run_id"] != binding.run_id:
        raise ValueError("skill_observation.run_id must match the bound Skill Run")
    source_version = source.get("package_version")
    if metadata.get("skill_version") is not None and source_version is not None and metadata["skill_version"] != source_version:
        raise ValueError("skill_observation.skill_version does not match the verified MCP package version")


def _safe_identifier(value: object, field: str) -> str:
    text = _required_text(value, field, MAX_IDENTIFIER_BYTES)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/@+ -]*", text):
        raise ValueError(f"{field} must be a bounded identifier without prompt or secret content")
    sensitive = ("secret", "password", "credential", "bearer ", "api_key", "api-key")
    if any(marker in text.casefold() for marker in sensitive):
        raise ValueError(f"{field} must not contain credentials or secrets")
    return text


def _sha256_value(value: object, field: str) -> str:
    text = str(value or "")
    if not SHA256_RE.fullmatch(text):
        raise ValueError(f"{field} must be lowercase SHA-256")
    return text


def _maturity(value: object, field: str) -> str:
    text = str(value or "").strip().lower()
    if text not in VALID_MATURITIES:
        raise ValueError(f"skill_observation.{field} has an invalid maturity")
    return text


def _safe_path(value: object) -> str:
    raw = str(value or "")
    if len(raw) > MAX_PATH_BYTES or len(raw.encode("utf-8")) > MAX_PATH_BYTES:
        raise ValueError(f"contribution path exceeds byte limit {MAX_PATH_BYTES}")
    if (
        not raw
        or "\\" in raw
        or "\0" in raw
        or any(character in raw for character in '<>:"|?*')
        or any(ord(character) < 32 for character in raw)
        or re.match(r"^[A-Za-z]:", raw)
    ):
        raise ValueError(f"unsafe contribution path: {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe contribution path: {raw!r}")
    for part in path.parts:
        if part.endswith((".", " ")) or part.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
            raise ValueError(f"unsafe contribution path: {raw!r}")
    normalized = path.as_posix()
    if normalized != raw:
        raise ValueError(f"contribution path must be normalized POSIX form: {raw!r}")
    return normalized


def _required_text(value: object, field: str, max_bytes: int | None = None) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} is required")
    if max_bytes is not None and (
        len(text) > max_bytes or len(text.encode("utf-8")) > max_bytes
    ):
        raise ValueError(f"{field} exceeds byte limit {max_bytes}")
    return text


def _uuid(value: object, field: str = "contribution_id") -> str:
    try:
        return str(uuid.UUID(str(value)))
    except ValueError as exc:
        raise ValueError(f"{field} must be a UUID: {value}") from exc


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _canonical_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _canonical_json(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _validate_json_shape(value: object) -> None:
    stack: list[tuple[object, int]] = [(value, 1)]
    nodes = 0
    text_bytes = 0
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES:
            raise ValueError(f"contribution metadata exceeds JSON node limit {MAX_JSON_NODES}")
        if depth > MAX_JSON_DEPTH:
            raise ValueError(f"contribution metadata exceeds JSON depth limit {MAX_JSON_DEPTH}")
        if isinstance(current, dict):
            for key, child in current.items():
                if not isinstance(key, str):
                    raise ValueError("contribution metadata object keys must be strings")
                if len(key) > MAX_JSON_KEY_BYTES:
                    raise ValueError(f"contribution metadata key exceeds byte limit {MAX_JSON_KEY_BYTES}")
                encoded_key_bytes = len(key.encode("utf-8"))
                if encoded_key_bytes > MAX_JSON_KEY_BYTES:
                    raise ValueError(f"contribution metadata key exceeds byte limit {MAX_JSON_KEY_BYTES}")
                text_bytes += encoded_key_bytes
                stack.append((child, depth + 1))
        elif isinstance(current, list):
            stack.extend((child, depth + 1) for child in current)
        elif isinstance(current, str):
            if len(current) > MAX_JSON_STRING_BYTES:
                raise ValueError(
                    f"contribution metadata string exceeds byte limit {MAX_JSON_STRING_BYTES}"
                )
            encoded_string_bytes = len(current.encode("utf-8"))
            if encoded_string_bytes > MAX_JSON_STRING_BYTES:
                raise ValueError(
                    f"contribution metadata string exceeds byte limit {MAX_JSON_STRING_BYTES}"
                )
            text_bytes += encoded_string_bytes
        elif current is not None and not isinstance(current, (str, int, float, bool)):
            raise ValueError("contribution metadata must contain only JSON values")
        if text_bytes > MAX_METADATA_BYTES:
            raise ValueError(f"contribution metadata exceeds byte limit {MAX_METADATA_BYTES}")


def _write_fsynced(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json_once(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        _write_fsynced(
            temp,
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )
        try:
            os.link(temp, path)
        except FileExistsError as exc:
            raise ValueError(f"immutable event already exists: {path.name}") from exc
    finally:
        temp.unlink(missing_ok=True)


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise KeyError(f"contribution return not found: {path.parent.name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"invalid contribution return manifest: {path}")
    return data


def _existing_result(final_dir: Path, payload_hash: str) -> dict[str, Any]:
    manifest = _read_manifest(final_dir / "manifest.json")
    if manifest.get("payload_hash") != payload_hash:
        raise ValueError("contribution_id already exists with a different payload")
    return {**manifest, "created": False, "idempotent_replay": True}


def _read_event(
    path: Path,
    schema: str,
    *,
    approval_verifier: HumanApprovalVerifier | None = None,
) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"required contribution event not found: {path.name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != schema:
        raise ValueError(f"invalid contribution event: {path}")
    if approval_verifier is None:
        raise RuntimeError("trusted human approval verifier is required to read signed events")
    signature = data.get("server_signature")
    event_hash = data.get("event_hash")
    if not isinstance(signature, str) or not signature:
        raise ValueError("contribution event is missing server signature")
    if not isinstance(event_hash, str) or not SHA256_RE.fullmatch(event_hash):
        raise ValueError("contribution event is missing a valid event hash")
    unsigned = {key: value for key, value in data.items() if key != "server_signature"}
    approval_verifier.verify_event(unsigned, signature)
    hash_basis = {key: value for key, value in unsigned.items() if key != "event_hash"}
    if event_hash != _canonical_hash(hash_basis):
        raise ValueError("invalid contribution event hash")
    return data


def _event_comparison(event: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in event.items()
        if key
        not in {
            "decided_at",
            "prepared_at",
            "adopted_at",
            "event_hash",
            "server_signature",
        }
    }


def _record_events(
    record_dir: Path,
    *,
    approval_verifier: HumanApprovalVerifier | None,
) -> list[dict[str, Any]]:
    events_dir = record_dir / "events"
    result = []
    for name, schema in (
        ("review.json", REVIEW_SCHEMA),
        ("adoption-prepared.json", ADOPTION_PREPARED_SCHEMA),
        ("adoption.json", ADOPTION_SCHEMA),
    ):
        path = events_dir / name
        if path.is_file():
            result.append(
                _read_event(path, schema, approval_verifier=approval_verifier)
            )
    return result


def _record_summary(
    record_dir: Path,
    manifest: dict[str, Any],
    *,
    approval_verifier: HumanApprovalVerifier | None,
) -> dict[str, Any]:
    _verify_manifest_payload(record_dir, manifest)
    verified_events = _record_events(record_dir, approval_verifier=approval_verifier)
    by_name = {str(event["event"]): event for event in verified_events}
    review = by_name.get("review_decided")
    prepared = by_name.get("adoption_prepared")
    adoption = by_name.get("adopted")
    if prepared is not None and review is None:
        raise ValueError("adoption-prepared event exists without a review event")
    if adoption is not None and prepared is None:
        raise ValueError("adoption event exists without a prepared event")
    if review is not None:
        _verify_review_binding(manifest, review)
    if adoption is not None:
        status = "adopted"
    elif prepared is not None:
        status = "adoption_pending"
    elif review is not None:
        status = str(review["decision"])
    else:
        status = "pending_review"
    result = {**manifest, "status": status}
    if review is not None:
        result["review"] = {
            key: value
            for key, value in review.items()
            if key != "approval_token_hash"
        }
    if adoption is not None:
        result["adoption"] = adoption
    return result


def _next_step(
    record_dir: Path,
    *,
    approval_verifier: HumanApprovalVerifier | None,
) -> str:
    if (record_dir / "events" / "adoption.json").is_file():
        return "publication, distribution, and live verification remain separate governed steps"
    if (record_dir / "events" / "adoption-prepared.json").is_file():
        return "retry the same adoption_id and approval token to complete or reconcile promotion"
    review_path = record_dir / "events" / "review.json"
    if not review_path.is_file():
        return "record an explicit human review decision"
    review = _read_event(
        review_path,
        REVIEW_SCHEMA,
        approval_verifier=approval_verifier,
    )
    if review.get("decision") == "accepted":
        return "use the returned approval token to request server-side adoption"
    return "rejected; canonical adoption is not permitted"


def _stored_files(record_dir: Path, manifest: dict[str, Any]) -> list[AdoptionFile]:
    result = []
    for item in manifest["files"]:
        content = (record_dir / "files").joinpath(
            *PurePosixPath(item["path"]).parts
        ).read_text(encoding="utf-8")
        if _sha256(content) != item["content_hash"]:
            raise ValueError(f"stored contribution file hash mismatch: {item['path']}")
        result.append(
            AdoptionFile(
                bundle_path=item["path"],
                content=content,
                content_hash=item["content_hash"],
            )
        )
    return result


def _verify_manifest_payload(record_dir: Path, manifest: dict[str, Any]) -> None:
    """Rebuild the submission payload from persisted bytes and verify its identity."""
    required = {
        "contribution_id",
        "kind",
        "title",
        "summary",
        "files",
        "kind_metadata",
        "proposed_target_path",
        "source",
        "binding",
        "payload_hash",
    }
    if not required.issubset(manifest):
        raise ValueError("contribution manifest is missing canonical payload fields")
    rows = manifest.get("files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("contribution manifest files must be a non-empty array")
    content_root = record_dir / "files"
    actual_entries = {
        path.relative_to(content_root).as_posix()
        for path in content_root.rglob("*")
        if path.is_file()
    } if content_root.is_dir() else set()
    rebuilt_files: list[dict[str, Any]] = []
    expected_entries: set[str] = set()
    for raw in rows:
        if not isinstance(raw, dict):
            raise ValueError("contribution manifest file entry must be an object")
        path = _safe_path(raw.get("path"))
        expected_entries.add(path)
        stored = content_root.joinpath(*PurePosixPath(path).parts)
        if not stored.is_file():
            raise ValueError(f"stored contribution file is missing: {path}")
        content = stored.read_text(encoding="utf-8")
        encoded = content.encode("utf-8")
        content_hash = hashlib.sha256(encoded).hexdigest()
        if raw.get("content_hash") != content_hash:
            raise ValueError(f"stored contribution file hash mismatch: {path}")
        if raw.get("byte_count") != len(encoded):
            raise ValueError(f"stored contribution file byte_count mismatch: {path}")
        rebuilt_files.append({
            "path": path,
            "content": content,
            "content_hash": content_hash,
            "byte_count": len(encoded),
        })
    if actual_entries != expected_entries:
        raise ValueError("stored contribution file tree does not match the manifest")
    payload = {
        "contribution_id": manifest["contribution_id"],
        "kind": manifest["kind"],
        "title": manifest["title"],
        "summary": manifest["summary"],
        "files": rebuilt_files,
        "kind_metadata": manifest["kind_metadata"],
        "proposed_target_path": manifest["proposed_target_path"],
        "source": manifest["source"],
        "binding": manifest["binding"],
    }
    _validate_json_shape(payload)
    if manifest.get("payload_hash") != _canonical_hash(payload):
        raise ValueError("contribution payload hash does not match persisted content")


def _repository_xid_paths(
    root: Path, ownership: Ownership | None
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    candidates: list[Path] = []
    for family in ("agent", "docs", "knowledge", "skills"):
        base = root / family
        if base.exists():
            candidates.extend(path for path in base.glob("**/*") if path.is_file())
    packs = root / "packs"
    if packs.exists():
        candidates.extend(path for path in packs.glob("**/*") if path.is_file())
    for path in candidates:
        if path.suffix.lower() not in {".md", ".yaml", ".yml"}:
            continue
        rel_path = path.resolve().relative_to(root).as_posix()
        if ownership is not None and not ownership.catalog_enabled(rel_path):
            continue
        xid = first_xid(path.read_text(encoding="utf-8"))
        if xid:
            result.setdefault(xid, set()).add(rel_path)
    return result


def _validate_canonical_target(
    root: Path,
    manifest: dict[str, Any],
    target_path: object,
    *,
    ownership: Ownership | None,
    existing_knowledge_xids: set[str] | None,
    existing_knowledge_xid_locations: dict[str, set[str]] | None = None,
    unlocated_existing_knowledge_xids: set[str] | None = None,
    repository_xid_paths: dict[str, set[str]] | None = None,
    allow_same_xid_after_prepare: bool = False,
) -> str:
    normalized = _safe_path(target_path)
    policy = ownership if ownership is not None else load_ownership(root)
    if policy is None:
        raise ValueError("ownership.yaml is required for canonical contribution adoption")
    zone = policy.zone_for(normalized)
    if zone is None:
        raise ValueError(f"canonical target has no ownership zone: {normalized}")
    parts = PurePosixPath(normalized).parts
    kind = manifest["kind"]
    if kind == "knowledge":
        if not normalized.lower().endswith(".md") or not _is_knowledge_family(parts):
            raise ValueError("Knowledge target must be a Markdown file in a canonical knowledge family")
        if not zone.catalog:
            raise ValueError("Knowledge target ownership zone is not catalog-enabled")
        xid = str(manifest["kind_metadata"]["xid"])
        if xid in (existing_knowledge_xids or set()):
            target = root.joinpath(*parts)
            expected_hash = str(manifest["files"][0]["content_hash"])
            known_locations = set(
                (existing_knowledge_xid_locations or {}).get(xid, set())
            )
            prepared_target_matches = (
                allow_same_xid_after_prepare
                and (repository_xid_paths or {}).get(xid) == {normalized}
                and known_locations.issubset({normalized})
                and xid not in (unlocated_existing_knowledge_xids or set())
                and target.is_file()
                and _sha256(target.read_text(encoding="utf-8")) == expected_hash
            )
            if not prepared_target_matches:
                raise ValueError(f"Knowledge XID already exists in the canonical catalog: {xid}")
        return normalized
    if kind == "skill_observation":
        if len(parts) < 2 or parts[0] != "observations" or not normalized.lower().endswith(".md"):
            raise ValueError("Skill observation target must be a Markdown file below observations/")
        if zone.id != "records" or zone.owner != "operational" or zone.distribution:
            raise ValueError("Skill observation target is not permitted by records ownership")
        return normalized
    if len(parts) < 2 or parts[0] != "tools":
        raise ValueError("deterministic tool target must be a new directory below tools/")
    if zone.id != "kernel-code" or zone.owner != "base" or not zone.distribution:
        raise ValueError("deterministic tool target is not permitted by kernel-code ownership")
    return normalized.rstrip("/")


def _is_knowledge_family(parts: tuple[str, ...]) -> bool:
    if len(parts) >= 2 and parts[0] == "knowledge":
        return True
    if len(parts) >= 4 and parts[0] == "packs" and parts[2] == "knowledge":
        return True
    return (
        len(parts) >= 5
        and parts[0] == "packs"
        and parts[1] == "local"
        and parts[3] == "knowledge"
    )


def _verify_review_binding(manifest: dict[str, Any], review: dict[str, Any]) -> None:
    proposed = manifest.get("proposed_target_path")
    if review.get("payload_hash") != manifest.get("payload_hash"):
        raise ValueError("review payload_hash no longer matches the contribution manifest")
    if review.get("proposed_target_path") != proposed:
        raise ValueError("review proposed_target_path no longer matches the contribution manifest")
    if review.get("proposed_target_path_hash") != _optional_path_hash(proposed):
        raise ValueError("review proposed_target_path_hash is invalid")
    basis = {
        key: value
        for key, value in review.items()
        if key not in {"review_binding_hash", "decided_at", "event_hash", "server_signature"}
    }
    if review.get("review_binding_hash") != _canonical_hash(basis):
        raise ValueError("review binding hash is invalid")


def _optional_path_hash(value: object) -> str | None:
    return _sha256(str(value)) if value is not None else None


def _seal_event(
    event: dict[str, Any], approval_verifier: HumanApprovalVerifier
) -> dict[str, Any]:
    sealed = {**event, "event_hash": _canonical_hash(event)}
    return {**sealed, "server_signature": approval_verifier.seal_event(sealed)}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

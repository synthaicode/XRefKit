"""Quality observations over the existing inert Contribution Return inbox.

The host supplies explicit feedback and a transfer policy. This module neither
observes conversations nor grants Knowledge/Skill adoption authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Callable, Literal

from pydantic import Field, field_validator, model_validator

from .gateway import Feedback, Record, evaluate
from .mcp.audit import _process_lock
from .mcp.contribution_adoption import HumanApprovalVerifier

Text = Annotated[str, Field(min_length=1, max_length=4096)]
Identifier = Annotated[str, Field(min_length=1, max_length=256)]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
STATUSES = ("reported", "triaged", "under_review", "approved_for_improvement",
            "resolved", "closed", "rejected", "deferred")
DECISION_SCHEMA = "xrefkit.quality_issue_decision/v1"
QUALITY_REASONS = {"instruction_miss", "scope_error", "dissatisfaction"}
_SENSITIVE = re.compile(
    r"(?i)(?:bearer\s+\S+|(?:password|passwd|api[_-]?key|secret|access[_-]?token)[\s\\\"']*[:=][\s\\\"']*\S+"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----|\bsk-[a-zA-Z0-9]{16,}"
    r"|[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}|\b\d{3}-\d{2}-\d{4}\b)"
)


def reject_sensitive(value: object) -> None:
    """Defense in depth, not a PII classifier or permission substitute."""
    if _SENSITIVE.search(json.dumps(value, ensure_ascii=False)):
        raise ValueError("quality issue contains potentially sensitive data; sanitize locally")


class EvidenceRef(Record):
    evidence_id: Identifier
    summary: Text
    content_hash: Digest


class QualityReport(Record):
    version: Literal[1]
    occurred_at: Text
    classification: Literal["instruction_miss", "scope_error", "dissatisfaction"]
    common_rule_relation: Text
    observed_facts: Annotated[list[Text], Field(min_length=1, max_length=64)]
    correction_evidence: Annotated[list[EvidenceRef], Field(min_length=1, max_length=64)]
    output_before: EvidenceRef
    output_after: EvidenceRef | None
    diff_summary: Text
    inferred_causes: Annotated[list[Text], Field(max_length=64)]
    unknowns: Annotated[list[Text], Field(max_length=64)]
    impact: Text
    similarity_key: Identifier | None
    feedback: dict[str, Any]
    transfer: Literal["sanitized_nonconfidential"]

    @field_validator("occurred_at")
    @classmethod
    def timezone_required(cls, value: str) -> str:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("occurred_at requires a timezone")
        return value

    @model_validator(mode="after")
    def feedback_basis(self):
        result = evaluate(Feedback.model_validate(self.feedback))
        if not result["quality_retries"]:
            raise ValueError("quality issue requires explicit quality feedback")
        if self.classification not in {a["reason"] for a in result["feedback"]["attempts"]}:
            raise ValueError("classification must match observed feedback")
        reject_sensitive(self.model_dump())
        return self


class TransferPolicy(Record):
    destination: Identifier
    allowed: bool
    data_classification: Literal["sanitized_nonconfidential", "confidential", "personal", "unknown"]
    authorization_reference: Text


def validate_quality_report(raw: object) -> dict[str, Any]:
    return QualityReport.model_validate(raw).model_dump()


def prepare_quality_issue(*, report: dict, observation: dict, contribution_id: str,
                          title: str, summary: str, policy: dict,
                          destination: str, knowledge_versions: list[dict] | None = None,
                          package_id: str | None = None) -> dict:
    """Host callback: evaluate locally before returning a sendable MCP argument set.

    Host redaction and destination authorization precede this call. Prompt bodies
    and original output bodies must stay local; evidence uses hashes and summaries.
    """
    transfer = TransferPolicy.model_validate(policy)
    if (not transfer.allowed or transfer.destination != destination
            or transfer.data_classification != "sanitized_nonconfidential"):
        raise ValueError("quality issue transfer is not authorized for this destination/data")
    quality = validate_quality_report(report)
    metadata = {**observation, "quality_issue": quality}
    from .mcp.contribution_returns import _uuid, _validate_skill_observation_metadata
    metadata = _validate_skill_observation_metadata(metadata)
    reject_sensitive({"metadata": metadata, "title": title, "summary": summary,
                      "knowledge_versions": knowledge_versions, "package_id": package_id})
    # A deterministic inert file avoids raw conversation or business-output uploads.
    content = "# Quality observation\n\n" + json.dumps(quality, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return {
        "contribution_id": _uuid(contribution_id), "kind": "skill_observation",
        "title": title, "summary": summary,
        "files": [{"path": "quality-observation.md", "content": content,
                   "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest()}],
        "skill_content_hash": metadata["skill_content_hash"],
        "package_id": package_id,
        "knowledge_versions": knowledge_versions or [], "skill_observation": metadata,
    }


async def submit_quality_feedback(*, call_tool: Callable, **kwargs) -> dict:
    """Invoke from the client's correction hook; transport errors remain observable.

    The host owns continuing its current task after recording an intake failure.
    No global hook is installed, no conversation access is inferred.
    """
    payload = prepare_quality_issue(**kwargs)
    return await call_tool("submit_contribution_return", payload)


def quality_issue_contract() -> dict:
    return {
        "version": 1, "contribution_kind": "skill_observation",
        "metadata_field": "quality_issue", "report_schema": QualityReport.model_json_schema(),
        "transfer_policy_schema": TransferPolicy.model_json_schema(),
        "states": list(STATUSES), "initial_state": "reported",
        "issue_identity": "contribution_id; reports remain individually immutable",
        "human_decisions": "existing trusted HumanApprovalVerifier; no adoption authority",
        "host_trigger": "client correction callback; server cannot monitor conversations",
        "privacy": "host sanitization and configured destination permission required before network; unknown data denied",
        "automatic_actions": "none; no Skill, Knowledge, workflow or maturity mutation",
    }


def _record(root: Path, issue_id: str) -> tuple[Path, dict]:
    from .mcp.contribution_returns import STORE_RELATIVE, _uuid, _read_manifest, _verify_manifest_payload
    directory = root.resolve() / STORE_RELATIVE / _uuid(issue_id)
    manifest = _read_manifest(directory / "manifest.json")
    _verify_manifest_payload(directory, manifest)
    if manifest["kind"] != "skill_observation" or not manifest["kind_metadata"].get("quality_issue"):
        raise ValueError("contribution is not a quality issue")
    return directory, manifest


def _history(directory: Path, manifest: dict, verifier: HumanApprovalVerifier | None) -> list[dict]:
    from .mcp.contribution_returns import _read_event
    history = []
    for path in sorted((directory / "quality-decisions").glob("*.json")):
        event = _read_event(path, DECISION_SCHEMA, approval_verifier=verifier)
        if (event["issue_id"] != manifest["contribution_id"]
                or event["payload_hash"] != manifest["payload_hash"]
                or event["expected_revision"] != len(history)
                or event["previous_event_hash"] != (history[-1]["event_hash"] if history else None)):
            raise ValueError("quality decision history integrity mismatch")
        history.append(event)
    return history


def _quality_issue_detail(root: Path, issue_id: str,
                          approval_verifier: HumanApprovalVerifier | None = None) -> dict:
    directory, manifest = _record(root, issue_id)
    with _process_lock(directory / "quality-review"):
        history = _history(directory, manifest, approval_verifier)
    last = history[-1] if history else None
    row = {
        "issue_id": manifest["contribution_id"], "title": manifest["title"],
        "summary": manifest["summary"], "created_at": manifest["created_at"],
        "status": last["status"] if last else "reported", "revision": len(history),
        "payload_hash": manifest["payload_hash"], "source": manifest["source"],
        "binding": manifest["binding"], "observation": manifest["kind_metadata"],
        "report": manifest["kind_metadata"]["quality_issue"], "history": history,
        "related_issue_ids": last["related_issue_ids"] if last else [],
        "report_count": 1,
    }
    return row


def get_quality_issue(root: Path, issue_id: str,
                      approval_verifier: HumanApprovalVerifier | None = None) -> dict:
    from .mcp.contribution_returns import STORE_RELATIVE, _read_manifest, _verify_manifest_payload
    row = _quality_issue_detail(root, issue_id, approval_verifier)
    directory = root.resolve() / STORE_RELATIVE / row["issue_id"]
    similar = []
    key = row["report"]["similarity_key"]
    if key is not None:
        for path in sorted(directory.parent.iterdir()):
            if path == directory or path.name.startswith(".") or not (path / "manifest.json").is_file():
                continue
            other = _read_manifest(path / "manifest.json")
            quality = other.get("kind_metadata", {}).get("quality_issue")
            if other["kind"] == "skill_observation" and quality and quality["similarity_key"] == key:
                _verify_manifest_payload(path, other)
                similar.append(other["contribution_id"])
    row["similar_issue_ids"] = similar
    row["report_count"] = 1 + len(similar)
    return row


def list_quality_issues(root: Path, approval_verifier: HumanApprovalVerifier | None = None,
                       *, status: str | None = None, skill_id: str | None = None) -> list[dict]:
    from .mcp.contribution_returns import STORE_RELATIVE, _read_manifest
    if status is not None and status not in STATUSES:
        raise ValueError("invalid quality issue status")
    rows = []
    store = root.resolve() / STORE_RELATIVE
    if not store.exists():
        return rows
    for path in sorted(store.iterdir()):
        if path.name.startswith(".") or not path.is_dir() or not (path / "manifest.json").is_file():
            continue
        manifest = _read_manifest(path / "manifest.json")
        if manifest["kind"] == "skill_observation" and manifest["kind_metadata"].get("quality_issue"):
            rows.append(_quality_issue_detail(root, manifest["contribution_id"], approval_verifier))
    groups: dict[str, list[str]] = {}
    for row in rows:
        key = row["report"]["similarity_key"]
        if key is not None:
            groups.setdefault(key, []).append(row["issue_id"])
    for row in rows:
        key = row["report"]["similarity_key"]
        row["similar_issue_ids"] = [identity for identity in groups.get(key, [])
                                    if identity != row["issue_id"]]
        row["report_count"] = 1 + len(row["similar_issue_ids"])
    return [row for row in rows if (status is None or row["status"] == status)
            and (skill_id is None or row["source"]["skill_id"] == skill_id)]


def quality_decision_claims(root: Path, *, issue_id: str, decision_id: str, status: str,
                            reviewer: str, decision_evidence: str, expected_revision: int,
                            verification_evidence: list[str] | None = None,
                            related_issue_ids: list[str] | None = None) -> dict:
    """Exact claim basis for an external trusted human-approval issuer."""
    from .mcp.contribution_returns import _uuid, _required_text
    for field, value in (("issue_id", issue_id), ("decision_id", decision_id),
                         ("status", status), ("reviewer", reviewer),
                         ("decision_evidence", decision_evidence)):
        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string")
    _, manifest = _record(root, issue_id)
    if status not in STATUSES or status == "reported":
        raise ValueError("invalid human decision status")
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError("expected_revision must be a nonnegative integer")
    if verification_evidence is None:
        verification_evidence = []
    if related_issue_ids is None:
        related_issue_ids = []
    if not isinstance(verification_evidence, list) or not isinstance(related_issue_ids, list):
        raise ValueError("verification evidence and related issues must be arrays")
    if len(verification_evidence) > 64 or len(related_issue_ids) > 64:
        raise ValueError("decision lists exceed limit")
    if any(not isinstance(value, str) for value in verification_evidence):
        raise ValueError("verification_evidence items must be strings")
    if any(not isinstance(value, str) for value in related_issue_ids):
        raise ValueError("related_issue_ids items must be strings")
    evidence = [_required_text(value, "verification_evidence", 4096) for value in verification_evidence]
    related = sorted({_uuid(value) for value in related_issue_ids})
    for related_id in related:
        if related_id == manifest["contribution_id"]:
            raise ValueError("issue cannot relate to itself")
        _record(root, related_id)
    if status == "resolved" and not evidence:
        raise ValueError("resolved requires verification evidence")
    return {
        "schema": DECISION_SCHEMA, "issue_id": manifest["contribution_id"],
        "decision_id": _uuid(decision_id, "decision_id"), "status": status,
        "reviewer": _required_text(reviewer, "reviewer", 512),
        "decision_evidence": _required_text(decision_evidence, "decision_evidence", 16384),
        "expected_revision": expected_revision, "payload_hash": manifest["payload_hash"],
        "verification_evidence": evidence, "related_issue_ids": related,
    }


def decide_quality_issue(root: Path, *, approval_assertion: str,
                         approval_verifier: HumanApprovalVerifier | None = None, **kwargs) -> dict:
    from .mcp.contribution_returns import _seal_event, _write_json_once, _now
    if approval_verifier is None:
        raise RuntimeError("trusted human approval verifier is not configured")
    if not isinstance(approval_assertion, str):
        raise ValueError("approval_assertion must be a string")
    claims = quality_decision_claims(root, **kwargs)
    approval = approval_verifier.verify(approval_assertion, claims)
    if not approval.get("assertion_id"):
        raise ValueError("human approval assertion is missing assertion_id")
    directory, manifest = _record(root, claims["issue_id"])
    with _process_lock(directory / "quality-review"):
        history = _history(directory, manifest, approval_verifier)
        for event in history:
            if event["decision_id"] == claims["decision_id"]:
                if any(event[key] != value for key, value in claims.items()):
                    raise ValueError("decision ID already exists with different content")
                return {**event, "created": False, "idempotent_replay": True}
        if claims["expected_revision"] != len(history):
            raise ValueError("stale issue revision; reload before deciding")
        event = _seal_event({**claims, "approval_assertion_id": approval["assertion_id"],
                             "previous_event_hash": history[-1]["event_hash"] if history else None,
                             "decided_at": _now()}, approval_verifier)
        _write_json_once(directory / "quality-decisions" / f"{len(history):08d}.json", event)
    return {**event, "created": True, "idempotent_replay": False}

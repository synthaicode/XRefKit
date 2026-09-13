"""Governed Skill maturity reassessment from adopted MCP observations."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path, PurePosixPath
from typing import Any

from xrefkit.skillmeta import _parse_meta_lines

from .audit import _process_lock
from .contribution_adoption import HumanApprovalVerifier
from .contribution_returns import (
    ADOPTION_SCHEMA,
    STORE_RELATIVE,
    VALID_MATURITIES,
    _canonical_hash,
    _now,
    _read_event,
    _read_manifest,
    _required_text,
    _seal_event,
    _sha256,
    _uuid,
    _verify_manifest_payload,
    _write_json_once,
)
from .ownership import Ownership, load_ownership
from .repository import stable_hash

ASSESSMENT_SCHEMA = "xrefkit.skill_maturity_assessment/v1"
PROPOSAL_SCHEMA = "xrefkit.skill_maturity_proposal/v1"
REVIEW_SCHEMA = "xrefkit.skill_maturity_review/v1"
APPLY_PREPARED_SCHEMA = "xrefkit.skill_maturity_apply_prepared/v1"
APPLY_SCHEMA = "xrefkit.skill_maturity_apply/v1"
STORE = Path(".xrefkit") / "skill-maturity"
PROMOTION_NEXT = {"draft": "trial", "trial": "stable", "stable": "governed"}
MAX_CONTRIBUTIONS = 128
MAX_REFS = 256
MAX_TEXT = 16 * 1024


def maturity_return_contract() -> dict[str, Any]:
    return {
        "schemas": {
            "assessment": ASSESSMENT_SCHEMA,
            "proposal": PROPOSAL_SCHEMA,
            "review": REVIEW_SCHEMA,
            "apply": APPLY_SCHEMA,
        },
        "authority": {
            "client_proposed_maturity": "evidence_only",
            "webdav": "observation_transport_only",
            "human_review": "required_before_meta_mutation",
        },
        "ordering": [
            "submit/review/adopt skill_observation",
            "commit the canonical observations/ record to Git",
            "assess_skill_maturity",
            "propose_skill_maturity",
            "review_skill_maturity_proposal",
            "apply_skill_maturity_proposal",
        ],
        "transitions": PROMOTION_NEXT,
        "rejected_transitions": ["same maturity", "skipped promotion", "downgrade", "deprecated"],
        "canonical_skill": "one repository-owned public/shared Skill meta.md; local packs and overlays are excluded",
        "duplicate_policy": "run_id, evidence_id, and evidence content_hash must be unique and unused by an earlier applied proposal",
        "verification": "candidate and apply-time xrefkit Skill metadata validation at the exact target level",
        "later_lifecycle": {
            "publication": "not_performed",
            "distribution": "not_performed",
            "live_verification": "not_performed",
        },
    }


def assess_skill_maturity(
    root: Path,
    *,
    assessment_id: str,
    skill_id: str,
    observation_contribution_ids: list[str],
    approval_verifier: HumanApprovalVerifier,
    ownership: Ownership | None = None,
) -> dict[str, Any]:
    repo = root.resolve()
    normalized_id = _uuid(assessment_id, "assessment_id")
    normalized_skill_id = _identifier(skill_id, "skill_id")
    if not isinstance(observation_contribution_ids, list) or not observation_contribution_ids:
        raise ValueError("observation_contribution_ids must be a non-empty array")
    if len(observation_contribution_ids) > MAX_CONTRIBUTIONS:
        raise ValueError(f"observation_contribution_ids exceeds limit {MAX_CONTRIBUTIONS}")
    contribution_ids = [_uuid(value) for value in observation_contribution_ids]
    if len(set(contribution_ids)) != len(contribution_ids):
        raise ValueError("observation_contribution_ids must be unique")
    skill = _resolve_canonical_skill(repo, normalized_skill_id, ownership)
    observations = [
        _load_adopted_observation(repo, item, approval_verifier)
        for item in contribution_ids
    ]
    _validate_observation_set(skill, observations)
    used = _used_observation_identities(repo, approval_verifier)
    _reject_used_identities(observations, used)
    basis = {
        "schema": ASSESSMENT_SCHEMA,
        "event": "maturity_assessed",
        "assessment_id": normalized_id,
        "skill_id": normalized_skill_id,
        "canonical_meta_path": skill["meta_path"],
        "current_maturity": skill["maturity"],
        "skill_content_hash": skill["skill_content_hash"],
        "meta_content_hash": skill["meta_content_hash"],
        "observations": observations,
        "aggregation": _aggregate(observations),
        "eligibility": "eligible_for_proposal",
        "authority": "none",
    }
    path = repo / STORE / "assessments" / f"{normalized_id}.json"
    return _write_or_replay_signed(path, basis, "assessed_at", approval_verifier)


def propose_skill_maturity(
    root: Path,
    *,
    proposal_id: str,
    assessment_id: str,
    target_maturity: str,
    governance_refs: list[str] | None,
    approval_verifier: HumanApprovalVerifier,
    ownership: Ownership | None = None,
) -> dict[str, Any]:
    repo = root.resolve()
    normalized_id = _uuid(proposal_id, "proposal_id")
    assessment = _read_signed(
        repo / STORE / "assessments" / f"{_uuid(assessment_id, 'assessment_id')}.json",
        ASSESSMENT_SCHEMA,
        approval_verifier,
    )
    target = str(target_maturity or "").strip().lower()
    if target not in VALID_MATURITIES:
        raise ValueError("target_maturity is invalid")
    expected = PROMOTION_NEXT.get(str(assessment["current_maturity"]))
    if target != expected:
        raise ValueError(
            "maturity proposals permit only one-step promotion; downgrade, deprecation, same-state, and skipped transitions require a separate governance process"
        )
    skill = _resolve_canonical_skill(repo, str(assessment["skill_id"]), ownership)
    _verify_assessment_current(repo, assessment, skill, approval_verifier)
    observation_refs = [
        _relative_ref(repo, Path(str(skill["meta_path"])).parent, str(row["canonical_path"]))
        for row in assessment["observations"]
    ]
    parsed_meta = _parse_meta_lines(str(skill["meta_text"]))
    existing_governance = parsed_meta.get("governance_refs", [])
    if not isinstance(existing_governance, list):
        existing_governance = []
    normalized_governance = _validate_governance_refs(
        repo,
        Path(str(skill["meta_path"])).parent,
        [str(value) for value in existing_governance] + list(governance_refs or []),
    )
    if target == "governed" and not normalized_governance:
        raise ValueError("governed promotion requires at least one committed governance_ref")
    candidate = _update_meta(
        str(skill["meta_text"]),
        target,
        observation_refs,
        normalized_governance,
    )
    check = _check_candidate(repo, repo / str(skill["meta_path"]), candidate, target)
    basis = {
        "schema": PROPOSAL_SCHEMA,
        "event": "maturity_proposed",
        "proposal_id": normalized_id,
        "assessment_id": assessment["assessment_id"],
        "assessment_hash": assessment["event_hash"],
        "skill_id": assessment["skill_id"],
        "canonical_meta_path": skill["meta_path"],
        "current_maturity": assessment["current_maturity"],
        "target_maturity": target,
        "skill_content_hash": skill["skill_content_hash"],
        "original_meta_content_hash": skill["meta_content_hash"],
        "candidate_meta_content_hash": stable_hash(candidate),
        "observation_refs": observation_refs,
        "governance_refs": normalized_governance,
        "governance_ref_hashes": _reference_hashes(
            repo, Path(str(skill["meta_path"])).parent, normalized_governance
        ),
        "observation_identities": _observation_identities(assessment["observations"]),
        "client_proposed_maturities": sorted(
            {
                str(row["metadata"].get("proposed_maturity"))
                for row in assessment["observations"]
                if row["metadata"].get("proposed_maturity") is not None
            }
        ),
        "deterministic_check": check,
        "readiness": "passed" if check["ok"] else "failed",
        "authority": "none",
    }
    path = repo / STORE / "proposals" / normalized_id / "proposal.json"
    return _write_or_replay_signed(path, basis, "proposed_at", approval_verifier)


def review_skill_maturity_proposal(
    root: Path,
    *,
    proposal_id: str,
    decision_id: str,
    decision: str,
    reviewer: str,
    decision_evidence: str,
    approval_assertion: str,
    approval_verifier: HumanApprovalVerifier,
) -> dict[str, Any]:
    repo = root.resolve()
    normalized_proposal_id = _uuid(proposal_id, "proposal_id")
    proposal_dir = repo / STORE / "proposals" / normalized_proposal_id
    proposal = _read_signed(proposal_dir / "proposal.json", PROPOSAL_SCHEMA, approval_verifier)
    normalized_decision = str(decision or "").strip().lower()
    if normalized_decision not in {"accepted", "rejected"}:
        raise ValueError("decision must be accepted or rejected")
    if normalized_decision == "accepted" and proposal.get("readiness") != "passed":
        raise ValueError("a failed maturity proposal cannot be accepted")
    normalized_decision_id = _uuid(decision_id, "decision_id")
    normalized_reviewer = _required_text(reviewer, "reviewer", 512)
    normalized_evidence = _required_text(decision_evidence, "decision_evidence", MAX_TEXT)
    claims = {
        "proposal_id": normalized_proposal_id,
        "decision_id": normalized_decision_id,
        "decision": normalized_decision,
        "reviewer": normalized_reviewer,
        "decision_evidence_hash": _sha256(normalized_evidence),
        "proposal_hash": proposal["event_hash"],
        "skill_id": proposal["skill_id"],
        "target_maturity": proposal["target_maturity"],
        "candidate_meta_content_hash": proposal["candidate_meta_content_hash"],
    }
    verified = approval_verifier.verify(_required_text(approval_assertion, "approval_assertion", MAX_TEXT), claims)
    assertion_id = _required_text(verified.get("assertion_id"), "approval_assertion.assertion_id", 512)
    basis = {
        "schema": REVIEW_SCHEMA,
        "event": "maturity_review_decided",
        **claims,
        "decision_evidence": normalized_evidence,
        "approval_assertion_id": assertion_id,
    }
    path = proposal_dir / "review.json"
    with _process_lock(proposal_dir / "review"):
        if path.exists():
            existing = _read_signed(path, REVIEW_SCHEMA, approval_verifier)
            comparable = {
                key: value for key, value in existing.items()
                if key not in {"approval_token_hash", "review_binding_hash", "reviewed_at", "event_hash", "server_signature"}
            }
            if comparable != basis:
                raise ValueError("maturity proposal already has a different immutable review")
            return {**existing, "created": False, "idempotent_replay": True, "approval_token": None}
        token = secrets.token_urlsafe(32) if normalized_decision == "accepted" else None
        event_basis = {**basis, "approval_token_hash": _sha256(token) if token else None}
        event_basis["review_binding_hash"] = _canonical_hash(event_basis)
        event = _seal_event({**event_basis, "reviewed_at": _now()}, approval_verifier)
        _write_json_once(path, event)
    return {**event, "created": True, "idempotent_replay": False, "approval_token": token}


def apply_skill_maturity_proposal(
    root: Path,
    *,
    proposal_id: str,
    apply_id: str,
    reviewer: str,
    decision_evidence: str,
    approval_token: str,
    approval_verifier: HumanApprovalVerifier,
    ownership: Ownership | None = None,
) -> dict[str, Any]:
    repo = root.resolve()
    normalized_proposal_id = _uuid(proposal_id, "proposal_id")
    normalized_apply_id = _uuid(apply_id, "apply_id")
    normalized_reviewer = _required_text(reviewer, "reviewer", 512)
    normalized_evidence = _required_text(decision_evidence, "decision_evidence", MAX_TEXT)
    token = _required_text(approval_token, "approval_token", 1024)
    proposal_dir = repo / STORE / "proposals" / normalized_proposal_id
    with _process_lock(repo / STORE / "canonical-maturity-apply"):
        proposal = _read_signed(proposal_dir / "proposal.json", PROPOSAL_SCHEMA, approval_verifier)
        review = _read_signed(proposal_dir / "review.json", REVIEW_SCHEMA, approval_verifier)
        if review.get("decision") != "accepted" or review.get("proposal_hash") != proposal.get("event_hash"):
            raise ValueError("only the accepted review of this maturity proposal can be applied")
        if not secrets.compare_digest(str(review.get("approval_token_hash") or ""), _sha256(token)):
            raise ValueError("approval_token does not match the accepted maturity review")
        _verify_governance_refs_current(repo, proposal)
        apply_path = proposal_dir / "apply.json"
        if apply_path.exists():
            existing = _read_signed(apply_path, APPLY_SCHEMA, approval_verifier)
            if existing.get("apply_id") != normalized_apply_id:
                raise ValueError("maturity proposal already has a different immutable apply event")
            prepared = _read_signed(
                proposal_dir / "apply-prepared.json",
                APPLY_PREPARED_SCHEMA,
                approval_verifier,
            )
            if (
                prepared.get("reviewer") != normalized_reviewer
                or prepared.get("decision_evidence") != normalized_evidence
                or prepared.get("proposal_hash") != proposal.get("event_hash")
                or prepared.get("review_binding_hash") != review.get("review_binding_hash")
            ):
                raise ValueError("maturity proposal already has a different immutable apply request")
            current_skill = _resolve_canonical_skill(
                repo, str(proposal["skill_id"]), ownership
            )
            if (
                current_skill["meta_path"] != existing.get("canonical_meta_path")
                or current_skill["skill_content_hash"] != proposal.get("skill_content_hash")
                or current_skill["maturity"] != existing.get("maturity")
                or current_skill["meta_content_hash"] != existing.get("meta_content_hash")
            ):
                raise ValueError(
                    "canonical Skill changed after the recorded maturity apply"
                )
            return {**existing, "created": False, "idempotent_replay": True}
        assessment = _read_signed(
            repo / STORE / "assessments" / f"{proposal['assessment_id']}.json",
            ASSESSMENT_SCHEMA,
            approval_verifier,
        )
        skill = _resolve_canonical_skill(repo, str(proposal["skill_id"]), ownership)
        meta_path = repo / str(proposal["canonical_meta_path"])
        candidate = _update_meta(
            str(skill["meta_text"]),
            str(proposal["target_maturity"]),
            list(proposal["observation_refs"]),
            list(proposal["governance_refs"]),
        )
        current_hash = stable_hash(str(skill["meta_text"]))
        prepared_path = proposal_dir / "apply-prepared.json"
        recovery = prepared_path.exists() and current_hash == proposal["candidate_meta_content_hash"]
        _verify_assessment_evidence_current(repo, assessment, skill, approval_verifier)
        used = _used_observation_identities(
            repo, approval_verifier, exclude_proposal_id=normalized_proposal_id
        )
        _reject_used_identities(assessment["observations"], used)
        if not recovery:
            if current_hash != proposal["original_meta_content_hash"]:
                raise ValueError("canonical Skill meta.md changed after maturity proposal")
            _verify_assessment_current(repo, assessment, skill, approval_verifier)
            if stable_hash(candidate) != proposal["candidate_meta_content_hash"]:
                raise ValueError("candidate meta.md no longer matches the reviewed maturity proposal")
        check = _check_candidate(repo, meta_path, candidate, str(proposal["target_maturity"]))
        if not check["ok"]:
            raise ValueError("deterministic target maturity check failed: " + "; ".join(check["errors"]))
        prepared_basis = {
            "schema": APPLY_PREPARED_SCHEMA,
            "event": "maturity_apply_prepared",
            "proposal_id": normalized_proposal_id,
            "apply_id": normalized_apply_id,
            "reviewer": normalized_reviewer,
            "decision_evidence": normalized_evidence,
            "proposal_hash": proposal["event_hash"],
            "review_binding_hash": review["review_binding_hash"],
            "candidate_meta_content_hash": proposal["candidate_meta_content_hash"],
        }
        if prepared_path.exists():
            prepared = _read_signed(prepared_path, APPLY_PREPARED_SCHEMA, approval_verifier)
            comparable = {
                key: value for key, value in prepared.items()
                if key not in {"prepared_at", "event_hash", "server_signature"}
            }
            if comparable != prepared_basis:
                raise ValueError("maturity proposal has a different immutable prepared apply")
        else:
            prepared = _seal_event({**prepared_basis, "prepared_at": _now()}, approval_verifier)
            _write_json_once(prepared_path, prepared)
        if not recovery:
            _atomic_write(meta_path, candidate)
        if stable_hash(meta_path.read_text(encoding="utf-8")) != proposal["candidate_meta_content_hash"]:
            raise ValueError("canonical Skill meta.md hash mismatch after apply")
        event = _seal_event(
            {
                "schema": APPLY_SCHEMA,
                "event": "maturity_applied",
                "proposal_id": normalized_proposal_id,
                "apply_id": normalized_apply_id,
                "status": "applied",
                "applied_at": _now(),
                "skill_id": proposal["skill_id"],
                "canonical_meta_path": proposal["canonical_meta_path"],
                "previous_maturity": proposal["current_maturity"],
                "maturity": proposal["target_maturity"],
                "proposal_hash": proposal["event_hash"],
                "review_binding_hash": review["review_binding_hash"],
                "meta_content_hash": proposal["candidate_meta_content_hash"],
                "observation_identities": proposal["observation_identities"],
                "deterministic_check": check,
                "publication": "not_performed",
                "distribution": "not_performed",
                "live_verification": "not_performed",
            },
            approval_verifier,
        )
        _write_json_once(apply_path, event)
    return {**event, "created": True, "idempotent_replay": False}


def _resolve_canonical_skill(root: Path, skill_id: str, ownership: Ownership | None) -> dict[str, Any]:
    policy = ownership or load_ownership(root)
    candidates: list[Path] = []
    candidates.extend((root / "skills").glob("**/meta.md") if (root / "skills").exists() else [])
    packs = root / "packs"
    if packs.exists():
        candidates.extend(packs.glob("*/skills/**/meta.md"))
    matches = []
    for meta in candidates:
        rel = meta.resolve().relative_to(root).as_posix()
        zone = policy.zone_for(rel) if policy else None
        if zone is None or zone.owner not in {"base", "pack"} or not zone.catalog or not zone.distribution:
            continue
        text = meta.read_text(encoding="utf-8")
        parsed = _parse_meta_lines(text)
        if str(parsed.get("skill_id") or "").strip() == skill_id:
            matches.append((meta, rel, text, parsed))
    if len(matches) != 1:
        raise ValueError(
            "Skill maturity apply requires exactly one repository-owned canonical Skill; package-only, external, local-overlay, missing, or ambiguous identities fail closed"
        )
    meta, rel, text, parsed = matches[0]
    skill_doc = meta.parent / "SKILL.md"
    if not skill_doc.is_file():
        raise ValueError("canonical Skill is missing SKILL.md")
    maturity = str(parsed.get("maturity") or parsed.get("status") or "").strip().lower()
    if maturity not in VALID_MATURITIES:
        raise ValueError("canonical Skill maturity is missing or invalid")
    return {
        "meta_path": rel,
        "meta_text": text,
        "meta_content_hash": stable_hash(text),
        "skill_content_hash": stable_hash(skill_doc.read_text(encoding="utf-8")),
        "maturity": maturity,
    }


def _load_adopted_observation(root: Path, contribution_id: str, verifier: HumanApprovalVerifier) -> dict[str, Any]:
    record = root / STORE_RELATIVE / contribution_id
    manifest = _read_manifest(record / "manifest.json")
    _verify_manifest_payload(record, manifest)
    if manifest.get("kind") != "skill_observation":
        raise ValueError(f"contribution is not a skill_observation: {contribution_id}")
    adoption = _read_event(record / "events" / "adoption.json", ADOPTION_SCHEMA, approval_verifier=verifier)
    canonical = str(adoption.get("canonical_target") or "")
    if not canonical.startswith("observations/") or not canonical.endswith(".md"):
        raise ValueError("adopted Skill observation is outside observations/")
    committed_hash = _committed_file_hash(root, canonical)
    file_hash = str(manifest["files"][0]["content_hash"])
    expected_files = [{"path": canonical, "content_hash": file_hash}]
    if (
        adoption.get("status") != "adopted"
        or adoption.get("contribution_id") != contribution_id
        or adoption.get("payload_hash") != manifest.get("payload_hash")
        or adoption.get("canonical_files") != expected_files
    ):
        raise ValueError("Skill observation adoption event is not bound to its manifest and canonical file")
    current = root.joinpath(*PurePosixPath(canonical).parts)
    if (
        committed_hash != file_hash
        or not current.is_file()
        or not _file_matches_head(root, canonical)
    ):
        raise ValueError(
            f"Skill observation must be committed to Git and unchanged with its adopted hash before maturity assessment: {canonical}"
        )
    return {
        "contribution_id": contribution_id,
        "payload_hash": manifest["payload_hash"],
        "canonical_path": canonical,
        "content_hash": file_hash,
        "source": manifest["source"],
        "metadata": manifest["kind_metadata"],
        "adoption_event_hash": adoption["event_hash"],
    }


def _validate_observation_set(skill: dict[str, Any], observations: list[dict[str, Any]]) -> None:
    run_ids: set[str] = set()
    evidence_ids: set[str] = set()
    evidence_hashes: set[str] = set()
    for row in observations:
        metadata = row["metadata"]
        source = row["source"]
        if metadata["skill_id"] != source.get("skill_id"):
            raise ValueError("Skill observation identity differs from its verified source snapshot")
        if metadata["skill_content_hash"] != skill["skill_content_hash"]:
            raise ValueError("Skill observation is stale relative to the canonical Skill body")
        if source.get("skill_content_hash") != skill["skill_content_hash"]:
            raise ValueError("Skill observation source is stale relative to the canonical Skill body")
        if metadata["maturity_at_use"] != skill["maturity"]:
            raise ValueError("Skill observation maturity_at_use is stale relative to canonical meta.md")
        run_id = str(metadata["run_id"])
        if run_id in run_ids:
            raise ValueError("duplicate Skill observation run_id")
        run_ids.add(run_id)
        for evidence in metadata["evaluation_evidence"]:
            evidence_id = str(evidence["evidence_id"])
            if evidence_id in evidence_ids:
                raise ValueError("duplicate Skill observation evidence_id")
            evidence_ids.add(evidence_id)
            content_hash = evidence.get("content_hash")
            if content_hash is not None:
                if content_hash in evidence_hashes:
                    raise ValueError("duplicate Skill observation evidence content_hash")
                evidence_hashes.add(str(content_hash))


def _aggregate(observations: list[dict[str, Any]]) -> dict[str, Any]:
    metadata = [row["metadata"] for row in observations]
    return {
        "observation_count": len(observations),
        "client_count": len({row["client_id"] for row in metadata}),
        "environment_count": len({row["execution_environment"] for row in metadata}),
        "model_count": len({row["model_id"] for row in metadata}),
        "success_count": sum(row["outcome"] == "success" for row in metadata),
        "failure_count": sum(row["outcome"] == "failure" for row in metadata),
        "retry_total": sum(int(row["retry_count"]) for row in metadata),
        "ambiguity_count": sum(len(row["ambiguities"]) for row in metadata),
        "human_evaluation_count": sum(row["human_evaluation"] is not None for row in metadata),
        "minimum_sample_policy": "not_defined; human reviewer decides sufficiency",
    }


def _observation_identities(observations: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        "contribution_ids": sorted(str(row["contribution_id"]) for row in observations),
        "run_ids": sorted(str(row["metadata"]["run_id"]) for row in observations),
        "evidence_ids": sorted(
            str(item["evidence_id"])
            for row in observations for item in row["metadata"]["evaluation_evidence"]
        ),
        "evidence_content_hashes": sorted(
            str(item["content_hash"])
            for row in observations for item in row["metadata"]["evaluation_evidence"]
            if item.get("content_hash") is not None
        ),
    }


def _used_observation_identities(
    root: Path, verifier: HumanApprovalVerifier, exclude_proposal_id: str | None = None
) -> dict[str, set[str]]:
    used = {key: set() for key in ("contribution_ids", "run_ids", "evidence_ids", "evidence_content_hashes")}
    proposals = root / STORE / "proposals"
    if not proposals.exists():
        return used
    for path in proposals.glob("*/apply.json"):
        if path.parent.name == exclude_proposal_id:
            continue
        event = _read_signed(path, APPLY_SCHEMA, verifier)
        for key in used:
            used[key].update(str(value) for value in event.get("observation_identities", {}).get(key, []))
    return used


def _reject_used_identities(observations: list[dict[str, Any]], used: dict[str, set[str]]) -> None:
    current = _observation_identities(observations)
    for key, values in current.items():
        duplicate = sorted(set(values).intersection(used[key]))
        if duplicate:
            raise ValueError(f"Skill observation {key} already used by an applied maturity proposal: {duplicate}")


def _verify_assessment_current(
    root: Path, assessment: dict[str, Any], skill: dict[str, Any], verifier: HumanApprovalVerifier
) -> None:
    if skill["meta_path"] != assessment["canonical_meta_path"]:
        raise ValueError("canonical Skill identity changed after assessment")
    if skill["maturity"] != assessment["current_maturity"]:
        raise ValueError("canonical Skill maturity changed after assessment")
    if skill["skill_content_hash"] != assessment["skill_content_hash"]:
        raise ValueError("canonical Skill body changed after assessment")
    if skill["meta_content_hash"] != assessment["meta_content_hash"]:
        raise ValueError("canonical Skill meta.md changed after assessment")
    _verify_assessment_evidence_current(root, assessment, skill, verifier)


def _verify_assessment_evidence_current(
    root: Path, assessment: dict[str, Any], skill: dict[str, Any], verifier: HumanApprovalVerifier
) -> None:
    if skill["meta_path"] != assessment["canonical_meta_path"]:
        raise ValueError("canonical Skill identity changed after assessment")
    if skill["skill_content_hash"] != assessment["skill_content_hash"]:
        raise ValueError("canonical Skill body changed after assessment")
    refreshed = [
        _load_adopted_observation(root, str(row["contribution_id"]), verifier)
        for row in assessment["observations"]
    ]
    if refreshed != assessment["observations"]:
        raise ValueError("adopted Skill observation changed after assessment")


def _validate_governance_refs(root: Path, meta_parent: Path, refs: list[str]) -> list[str]:
    if not isinstance(refs, list) or len(refs) > MAX_REFS:
        raise ValueError(f"governance_refs must be an array with at most {MAX_REFS} entries")
    result = []
    for raw in refs:
        value = _required_text(raw, "governance_ref", 2048).replace("\\", "/")
        target_part = value.split("#", 1)[0]
        target = (root / meta_parent / target_part).resolve() if not PurePosixPath(target_part).is_absolute() else Path(target_part).resolve()
        try:
            rel = target.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError("governance_ref must resolve inside the repository") from exc
        committed_hash = _committed_file_hash(root, rel)
        if committed_hash is None or not target.is_file() or not _file_matches_head(root, rel):
            raise ValueError(f"governance_ref must resolve to a committed repository file: {value}")
        result.append(value)
    return sorted(set(result))


def _reference_hashes(root: Path, meta_parent: Path, refs: list[str]) -> list[dict[str, str]]:
    records = []
    for value in refs:
        target_part = value.split("#", 1)[0]
        target = (root / meta_parent / target_part).resolve()
        rel = target.relative_to(root).as_posix()
        content_hash = _committed_file_hash(root, rel)
        if content_hash is None:
            raise ValueError(f"governance_ref is no longer committed: {value}")
        records.append({"reference": value, "content_hash": content_hash})
    return records


def _verify_governance_refs_current(root: Path, proposal: dict[str, Any]) -> None:
    meta_parent = Path(str(proposal["canonical_meta_path"])).parent
    refs = [str(value) for value in proposal.get("governance_refs", [])]
    normalized = _validate_governance_refs(root, meta_parent, refs)
    if normalized != refs or _reference_hashes(root, meta_parent, normalized) != proposal.get(
        "governance_ref_hashes"
    ):
        raise ValueError("governance_refs changed after maturity proposal")


def _relative_ref(root: Path, meta_parent_rel: Path, target_rel: str) -> str:
    meta_parent = root / meta_parent_rel
    target = root / target_rel
    return Path(os.path.relpath(target, meta_parent)).as_posix()


def _update_meta(text: str, maturity: str, observation_refs: list[str], governance_refs: list[str]) -> str:
    lines = text.splitlines()
    maturity_fields = [
        index for index, line in enumerate(lines)
        if re.match(r"^- (?:maturity|status):", line)
    ]
    if not maturity_fields:
        raise ValueError("canonical Skill meta.md has no explicit maturity/status field")
    if len(maturity_fields) != 1:
        raise ValueError("canonical Skill meta.md has duplicate maturity/status fields")
    lines[maturity_fields[0]] = f"- maturity: `{maturity}`"
    lines = _merge_list_field(lines, "observation_refs", observation_refs)
    if governance_refs:
        lines = _merge_list_field(lines, "governance_refs", governance_refs)
    return "\n".join(lines) + "\n"


def _merge_list_field(lines: list[str], field: str, values: list[str]) -> list[str]:
    header = f"- {field}:"
    try:
        start = lines.index(header)
    except ValueError:
        insert = len(lines)
        while insert > 0 and not lines[insert - 1].strip():
            insert -= 1
        block = [header, *[f"  - `{value}`" for value in values]]
        return lines[:insert] + block + lines[insert:]
    end = start + 1
    existing: list[str] = []
    while end < len(lines) and (lines[end].startswith("  ") or not lines[end].strip()):
        match = re.match(r"^\s+-\s+`?(.+?)`?\s*$", lines[end])
        if match:
            existing.append(match.group(1))
        end += 1
    merged = existing + [value for value in values if value not in existing]
    return lines[: start + 1] + [f"  - `{value}`" for value in merged] + lines[end:]


def _check_candidate(root: Path, meta_path: Path, candidate: str, target: str) -> dict[str, Any]:
    temp = meta_path.parent / f".meta.maturity-check.{uuid.uuid4().hex}.md"
    try:
        temp.write_text(candidate, encoding="utf-8", newline="\n")
        relative_temp = temp.relative_to(root).as_posix()
        command = [
            sys.executable, "-m", "xrefkit", "skill", "check",
            "--root", str(root), "--meta", relative_temp,
            "--level", target, "--json",
        ]
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        try:
            payload = json.loads(process.stdout)
            result = payload[0]
            errors = list(result.get("errors", []))
            warnings = list(result.get("warnings", []))
            ok = process.returncode == 0 and bool(result.get("ok"))
        except (json.JSONDecodeError, IndexError, KeyError, TypeError):
            ok = False
            errors = [
                "xrefkit skill check did not return a valid JSON result: "
                + (process.stderr.strip() or process.stdout.strip() or f"exit {process.returncode}")
            ]
            warnings = []
        return {
            "command": f"python -m xrefkit skill check --meta {meta_path.relative_to(root).as_posix()} --level {target}",
            "ok": ok,
            "errors": errors,
            "warnings": warnings,
        }
    finally:
        temp.unlink(missing_ok=True)


def _committed_file_hash(root: Path, rel: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(root), "show", f"HEAD:{rel}"],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return hashlib.sha256(proc.stdout).hexdigest()


def _file_matches_head(root: Path, rel: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(root), "diff", "--quiet", "--no-ext-diff", "HEAD", "--", rel],
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0


def _identifier(value: object, field: str) -> str:
    text = _required_text(value, field, 256)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/@+ -]*", text):
        raise ValueError(f"{field} is not a safe identifier")
    return text


def _read_signed(path: Path, schema: str, verifier: HumanApprovalVerifier) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"required Skill maturity event not found: {path.name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != schema:
        raise ValueError(f"invalid Skill maturity event: {path}")
    signature = data.get("server_signature")
    event_hash = data.get("event_hash")
    if not isinstance(signature, str) or not isinstance(event_hash, str):
        raise ValueError("Skill maturity event is not sealed")
    unsigned = {key: value for key, value in data.items() if key != "server_signature"}
    verifier.verify_event(unsigned, signature)
    if event_hash != _canonical_hash({key: value for key, value in unsigned.items() if key != "event_hash"}):
        raise ValueError("invalid Skill maturity event hash")
    return data


def _write_or_replay_signed(
    path: Path,
    basis: dict[str, Any],
    timestamp_field: str,
    verifier: HumanApprovalVerifier,
) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _process_lock(path):
        if path.exists():
            existing = _read_signed(path, str(basis["schema"]), verifier)
            comparable = {
                key: value for key, value in existing.items()
                if key not in {timestamp_field, "event_hash", "server_signature"}
            }
            if comparable != basis:
                raise ValueError("event id already exists with different Skill maturity content")
            return {**existing, "created": False, "idempotent_replay": True}
        event = _seal_event({**basis, timestamp_field: _now()}, verifier)
        _write_json_once(path, event)
    return {**event, "created": True, "idempotent_replay": False}


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise

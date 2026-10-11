"""Deterministic endpoint intake builds a host-ready common-gate packet."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from .audit import _process_lock


def prepare_overlay_gate(root: Path, *, kind: str, identity: str, log: str,
                         binding_request: dict, specialist_evidence: list[str]) -> dict:
    from ..governance_entry import CORE_CHECKS, RULE_SOURCES, prepare
    from . import skill_edits, knowledge_edits
    module = skill_edits if kind == "skill" else knowledge_edits
    endpoint = "skill_overlay_activation" if kind == "skill" else "knowledge_overlay_activation"
    (root / ".xrefkit").mkdir(parents=True, exist_ok=True)
    with _process_lock(root / ".xrefkit" / "overlay-registry"):
        record = module.load_registry(root).get(identity)
        if record is None:
            raise ValueError("staged update not found")
        targets = sorted({record["overlay_meta_path"], record["overlay_skill_path"]} if kind == "skill" else {record["path"]})
        folder = root / "work" / "governance-intake" / str(uuid.uuid4())
        folder.mkdir(parents=True)
        rows = []
        for index, target in enumerate(targets):
            candidate = folder / f"candidate-{index}.md"
            candidate.write_bytes(module._local_path(root, target).read_bytes())
            rows.append({"candidate": candidate.relative_to(root).as_posix(), "target": target})
        manifest = folder / "bundle.md"
        manifest.write_text("# Final staged update bundle\n\n" + json.dumps({"endpoint": endpoint, "identity": identity, "files": rows}, indent=2) + "\n", encoding="utf-8")
        payload = {"endpoint": endpoint, "candidate_files": rows,
                   "candidate": manifest.relative_to(root).as_posix(), "target": targets[0],
                   "rules": sorted(RULE_SOURCES), "checks": sorted(CORE_CHECKS),
                   "specialist_evidence": specialist_evidence}
        packet = prepare(root, kind="asset_update", log=log, binding_request=binding_request,
                         materials=[payload["candidate"], module.registry_path(root).relative_to(root).as_posix(),
                                    *[r["candidate"] for r in rows], *sorted(RULE_SOURCES), *specialist_evidence], payload=payload)
        return {"packet": packet, "dispatch_required": True, "skill_id": "shared_asset_update_gate",
                "dispatch_owner": "client_host", "reflection": "blocked_until_verified_receipt_and_human_authority"}


def prepare_contribution_gate(root: Path, *, contribution_id: str, log: str,
                              binding_request: dict, specialist_evidence: list[str], approval_verifier) -> dict:
    from ..governance_entry import CORE_CHECKS, RULE_SOURCES, prepare
    from .contribution_returns import (_uuid, _read_manifest, _verify_manifest_payload,
        _read_event, _verify_review_binding, _stored_files, REVIEW_SCHEMA, STORE_RELATIVE)
    from .contribution_adoption import _target_paths
    if approval_verifier is None:
        raise RuntimeError("trusted human approval verifier is not configured")
    folder = root / STORE_RELATIVE / _uuid(contribution_id)
    with _process_lock(root / STORE_RELATIVE / "canonical-adoption"):
        manifest = _read_manifest(folder / "manifest.json")
        _verify_manifest_payload(folder, manifest)
        review = _read_event(folder / "events" / "review.json", REVIEW_SCHEMA, approval_verifier=approval_verifier)
        _verify_review_binding(manifest, review)
        if manifest["kind"] != "knowledge" or review.get("decision") != "accepted":
            raise ValueError("common canonical intake requires human-accepted Knowledge")
        files = _stored_files(folder, manifest)
        targets = _target_paths(review["approved_target_path"], files)
        staged = root / "work" / "governance-intake" / str(uuid.uuid4())
        staged.mkdir(parents=True)
        rows = []
        for index, (target, item) in enumerate(zip(targets, files, strict=True)):
            candidate = staged / f"candidate-{index}.md"
            candidate.write_bytes(item.content.encode("utf-8"))
            rows.append({"candidate": candidate.relative_to(root).as_posix(), "target": target})
        summary = staged / "bundle.md"
        summary.write_text("# Accepted Knowledge contribution bundle\n\n" + json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        payload = {"endpoint": "knowledge_canonical_adoption", "candidate_files": rows,
            "candidate": summary.relative_to(root).as_posix(), "target": targets[0], "rules": sorted(RULE_SOURCES),
            "checks": sorted(CORE_CHECKS), "specialist_evidence": specialist_evidence}
        fixed = [(folder / "manifest.json").relative_to(root).as_posix(),
                 (folder / "events" / "review.json").relative_to(root).as_posix()]
        packet = prepare(root, kind="asset_update", log=log, binding_request=binding_request,
            materials=[payload["candidate"], *[r["candidate"] for r in rows], *sorted(RULE_SOURCES), *fixed, *specialist_evidence], payload=payload)
        return {"packet": packet, "dispatch_required": True, "skill_id": "shared_asset_update_gate",
            "dispatch_owner": "client_host", "reflection": "blocked_until_verified_receipt_and_existing_human_approval"}

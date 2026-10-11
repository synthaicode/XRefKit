"""Final overlay activation: trusted execution and human authority are separate."""
from __future__ import annotations

import hashlib
from pathlib import Path

from .audit import _process_lock


def activate(root: Path, *, kind: str, identity: str, packet: dict, receipt: dict,
             host_verifier, approval_verifier, approval_assertion: str) -> dict:
    from ..governance_entry import digest, validate_endpoint
    from . import skill_edits, knowledge_edits

    if approval_verifier is None:
        raise RuntimeError("trusted human approval verifier is not configured")
    module = skill_edits if kind == "skill" else knowledge_edits
    endpoint = "skill_overlay_activation" if kind == "skill" else "knowledge_overlay_activation"
    (root / ".xrefkit").mkdir(parents=True, exist_ok=True)
    with _process_lock(root / ".xrefkit" / "overlay-registry"):
        registry = module.load_registry(root)
        if identity not in registry:
            raise ValueError("staged overlay not found")
        record = registry[identity]
        paths = {record["overlay_meta_path"], record["overlay_skill_path"]} if kind == "skill" else {record["path"]}
        candidates = {path: module._local_path(root, path).read_bytes() for path in paths}
        result = validate_endpoint(root, packet, receipt, endpoint=endpoint,
                                   candidates=candidates, host_verifier=host_verifier)
        approval_verifier.verify(approval_assertion, {
            "action": "activate_governed_overlay", "endpoint": endpoint,
            "identity": identity, "packet_hash": packet["packet_hash"], "result_hash": digest(result),
        })
        # Detect changes during host-result and human-authority verification.
        if any(module._local_path(root, path).read_bytes() != body for path, body in candidates.items()):
            raise ValueError("overlay changed before activation")
        record = {**record, "active": True,
                  "accepted_files": {path: hashlib.sha256(body).hexdigest() for path, body in candidates.items()},
                  "governance_packet_hash": packet["packet_hash"], "governance_receipt_hash": digest(receipt)}
        registry[identity] = record
        module._write_registry(root, registry)
        return {**record, "activated": True}

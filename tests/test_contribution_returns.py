from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

from xrefkit.mcp.audit import SessionRunBinding
from xrefkit.mcp.contribution_returns import (
    MAX_EVIDENCE_ROWS,
    MAX_METADATA_BYTES,
    adopt_contribution_return,
    export_contribution_return,
    list_contribution_returns,
    review_contribution_return,
    submit_contribution_return,
)
from xrefkit.mcp.catalog import XRefCatalog
from xrefkit.mcp.contribution_adoption import (
    AdoptionFile,
    HmacHumanApprovalVerifier,
    LocalCanonicalAdoptionTransport,
    issue_hmac_approval_assertion,
)


OWNERSHIP = """zones:
  - id: kernel-code
    owner: base
    paths:
      - tools/
    catalog: false
    distribution: true
    base_sync: true
    shadowing: false
  - id: kernel-content
    owner: base
    paths:
      - knowledge/
    catalog: true
    distribution: true
    base_sync: true
    shadowing: false
"""
APPROVAL_SECRET = "test-human-approval-secret-32-bytes-minimum"


def binding() -> SessionRunBinding:
    return SessionRunBinding(
        run_id=str(uuid.uuid4()),
        mcp_session_id=str(uuid.uuid4()),
        repository_fingerprint="a" * 32,
        skill_id="sample",
    )


def source() -> dict:
    return {
        "provider_id": "xrefkit-mcp",
        "provider_version": "test",
        "package_id": None,
        "package_version": None,
        "skill_id": "sample",
        "skill_content_hash": "b" * 64,
        "knowledge_versions": [],
        "verification": "matched_current_catalog",
    }


def file(path: str, content: str) -> dict:
    return {
        "path": path,
        "content": content,
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }


def adoption_repo(tmp_path: Path) -> Path:
    (tmp_path / "ownership.yaml").write_text(OWNERSHIP, encoding="utf-8")
    return tmp_path


def pending_knowledge(root: Path, *, target: str = "knowledge/adopted.md") -> tuple[str, str]:
    contribution_id = str(uuid.uuid4())
    content = "<!-- xid: ADOPT123 -->\n\n# Adopted rule\n\nBody.\n"
    submit_contribution_return(
        root,
        binding=binding(),
        source_snapshot=source(),
        contribution_id=contribution_id,
        kind="knowledge",
        title="Adopted rule",
        summary="Review this rule",
        files=[file("rule.md", content)],
        knowledge={"xid": "ADOPT123"},
        proposed_target_path=target,
    )
    return contribution_id, content


def approval_assertion(
    root: Path,
    contribution_id: str,
    *,
    decision_id: str,
    decision: str,
    reviewer: str,
    approved_target_path: str | None,
) -> str:
    manifest = json.loads(
        (
            root
            / ".xrefkit"
            / "contribution-returns"
            / contribution_id
            / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    proposed = manifest.get("proposed_target_path")
    path_hash = lambda value: (
        hashlib.sha256(str(value).encode("utf-8")).hexdigest()
        if value is not None
        else None
    )
    return issue_hmac_approval_assertion(
        APPROVAL_SECRET,
        {
            "assertion_id": str(uuid.uuid4()),
            "contribution_id": contribution_id,
            "decision_id": decision_id,
            "decision": decision,
            "reviewer": reviewer,
            "payload_hash": manifest["payload_hash"],
            "proposed_target_path": proposed,
            "proposed_target_path_hash": path_hash(proposed),
            "approved_target_path": approved_target_path,
            "approved_target_path_hash": path_hash(approved_target_path),
        },
    )


def approval_verifier() -> HmacHumanApprovalVerifier:
    return HmacHumanApprovalVerifier(APPROVAL_SECRET)


def signed_review(
    root: Path,
    *,
    contribution_id: str,
    decision_id: str,
    decision: str,
    reviewer: str,
    decision_evidence: str,
    approved_target_path: str | None = None,
    **kwargs,
) -> dict:
    return review_contribution_return(
        root,
        contribution_id=contribution_id,
        decision_id=decision_id,
        decision=decision,
        reviewer=reviewer,
        decision_evidence=decision_evidence,
        approved_target_path=approved_target_path,
        approval_assertion=approval_assertion(
            root,
            contribution_id,
            decision_id=decision_id,
            decision=decision,
            reviewer=reviewer,
            approved_target_path=approved_target_path,
        ),
        approval_verifier=approval_verifier(),
        **kwargs,
    )


def test_knowledge_submission_is_inert_idempotent_and_exportable(tmp_path: Path) -> None:
    contribution_id = str(uuid.uuid4())
    content = "<!-- xid: LOCAL123 -->\n\n# Local rule\n\nBody.\n"
    arguments = dict(
        binding=binding(), source_snapshot=source(), contribution_id=contribution_id,
        kind="knowledge", title="Local rule", summary="Review this rule",
        files=[file("knowledge/local_rule.md", content)], knowledge={"xid": "LOCAL123"},
    )

    created = submit_contribution_return(tmp_path, **arguments)
    replayed = submit_contribution_return(tmp_path, **arguments)
    listed = list_contribution_returns(tmp_path)
    exported = export_contribution_return(tmp_path, contribution_id)

    assert created["status"] == "pending_review"
    assert created["created"] is True
    assert replayed["idempotent_replay"] is True
    assert len(listed) == 1
    assert "content" not in listed[0]["files"][0]
    assert exported["activation_performed"] is False
    assert exported["review_bundle"]["files"][0]["content"] == content


def test_changed_retry_and_invalid_input_leave_original_unchanged(tmp_path: Path) -> None:
    contribution_id = str(uuid.uuid4())
    content = "<!-- xid: LOCAL123 -->\n\n# Local rule\n"
    common = dict(
        binding=binding(), source_snapshot=source(), contribution_id=contribution_id,
        kind="knowledge", title="Local rule", summary="Review this rule",
        knowledge={"xid": "LOCAL123"},
    )
    submit_contribution_return(tmp_path, files=[file("rule.md", content)], **common)

    with pytest.raises(ValueError, match="different payload"):
        submit_contribution_return(
            tmp_path, files=[file("rule.md", content + "changed\n")], **common
        )
    with pytest.raises(ValueError, match="unsafe contribution path"):
        submit_contribution_return(
            tmp_path,
            **{**common, "contribution_id": str(uuid.uuid4())},
            files=[file("../rule.md", content)],
        )
    assert len(list_contribution_returns(tmp_path)) == 1


@pytest.mark.parametrize(
    "unsafe_path",
    ["tools/check.py:stream", "CON", "tools/NUL.txt", "tools/check.py.", "tools/check.py "],
)
def test_windows_alias_paths_are_rejected(tmp_path: Path, unsafe_path: str) -> None:
    content = "<!-- xid: LOCAL123 -->\n\n# Local rule\n"
    with pytest.raises(ValueError, match="unsafe contribution path"):
        submit_contribution_return(
            tmp_path, binding=binding(), source_snapshot=source(),
            contribution_id=str(uuid.uuid4()), kind="knowledge", title="Local",
            summary="Review", files=[file(unsafe_path, content)],
            knowledge={"xid": "LOCAL123"},
        )


def test_case_alias_paths_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="duplicate contribution path"):
        submit_contribution_return(
            tmp_path, binding=binding(), source_snapshot=source(),
            contribution_id=str(uuid.uuid4()), kind="deterministic_tool", title="Tool",
            summary="Review", files=[file("tools/A.py", "a"), file("TOOLS/a.PY", "b")],
            deterministic_tool={
                "runtime": "python", "entrypoint": "tools/A.py",
                "input_contract": {}, "output_contract": {},
                "verification_evidence": [{"kind": "test", "command": "x", "result": "pass"}],
            },
        )


def test_metadata_limits_are_enforced_before_persistence(tmp_path: Path) -> None:
    content = "<!-- xid: LOCAL123 -->\n\n# Local rule\n"
    with pytest.raises(ValueError, match="summary exceeds byte limit"):
        submit_contribution_return(
            tmp_path, binding=binding(), source_snapshot=source(),
            contribution_id=str(uuid.uuid4()), kind="knowledge", title="Local",
            summary="x" * (MAX_METADATA_BYTES + 1), files=[file("rule.md", content)],
            knowledge={"xid": "LOCAL123"},
        )
    assert list_contribution_returns(tmp_path) == []


def test_evidence_row_limit_is_enforced(tmp_path: Path) -> None:
    evidence = [
        {"kind": "test", "command": "x", "result": "pass"}
        for _ in range(MAX_EVIDENCE_ROWS + 1)
    ]
    with pytest.raises(ValueError, match="evidence exceeds row limit"):
        submit_contribution_return(
            tmp_path, binding=binding(), source_snapshot=source(),
            contribution_id=str(uuid.uuid4()), kind="deterministic_tool", title="Tool",
            summary="Review", files=[file("tools/check.py", "pass\n")],
            deterministic_tool={
                "runtime": "python", "entrypoint": "tools/check.py",
                "input_contract": {}, "output_contract": {},
                "verification_evidence": evidence,
            },
        )


def test_contract_metadata_total_and_depth_are_bounded(tmp_path: Path) -> None:
    common = dict(
        binding=binding(), source_snapshot=source(), kind="deterministic_tool",
        title="Tool", summary="Review", files=[file("tools/check.py", "pass\n")],
    )
    base_tool = {
        "runtime": "python", "entrypoint": "tools/check.py", "output_contract": {},
        "verification_evidence": [{"kind": "test", "command": "x", "result": "pass"}],
    }
    with pytest.raises(ValueError, match="exceeds byte limit"):
        submit_contribution_return(
            tmp_path, contribution_id=str(uuid.uuid4()), **common,
            deterministic_tool={**base_tool, "input_contract": {"description": "x" * MAX_METADATA_BYTES}},
        )
    with pytest.raises(ValueError, match="metadata exceeds byte limit"):
        submit_contribution_return(
            tmp_path, contribution_id=str(uuid.uuid4()), **common,
            deterministic_tool={
                **base_tool,
                "input_contract": {f"field{index}": "x" * 60_000 for index in range(5)},
            },
        )
    nested: dict[str, object] = {}
    cursor = nested
    for _ in range(20):
        child: dict[str, object] = {}
        cursor["child"] = child
        cursor = child
    with pytest.raises(ValueError, match="JSON depth limit"):
        submit_contribution_return(
            tmp_path, contribution_id=str(uuid.uuid4()), **common,
            deterministic_tool={**base_tool, "input_contract": nested},
        )


def test_deterministic_tool_requires_contract_evidence_and_is_not_executed(tmp_path: Path) -> None:
    content = "raise RuntimeError('must not execute during intake')\n"
    result = submit_contribution_return(
        tmp_path,
        binding=binding(), source_snapshot=source(), contribution_id=str(uuid.uuid4()),
        kind="deterministic_tool", title="Checker", summary="Review the checker",
        files=[file("tools/check.py", content)],
        deterministic_tool={
            "runtime": "python>=3.11", "entrypoint": "tools/check.py",
            "input_contract": {"type": "object"},
            "output_contract": {"type": "object"},
            "verification_evidence": [
                {"kind": "test", "command": "pytest", "result": "passed"}
            ],
        },
    )
    assert result["kind"] == "deterministic_tool"
    assert result["status"] == "pending_review"


def test_human_review_then_local_adoption_is_catalog_visible_and_auditable(
    tmp_path: Path,
) -> None:
    root = adoption_repo(tmp_path)
    contribution_id, content = pending_knowledge(root)
    manifest_path = root / ".xrefkit" / "contribution-returns" / contribution_id / "manifest.json"
    original_manifest = manifest_path.read_bytes()

    decision_id = str(uuid.uuid4())
    review_arguments = {
        "root": root,
        "contribution_id": contribution_id,
        "decision_id": decision_id,
        "decision": "accepted",
        "reviewer": "human:alice@example.test",
        "decision_evidence": "Reviewed wording, scope, XID, and canonical ownership.",
        "approved_target_path": "knowledge/adopted.md",
    }
    review_arguments["approval_assertion"] = approval_assertion(
        root,
        contribution_id,
        decision_id=decision_id,
        decision="accepted",
        reviewer="human:alice@example.test",
        approved_target_path="knowledge/adopted.md",
    )
    review_arguments["approval_verifier"] = approval_verifier()
    review = review_contribution_return(**review_arguments)
    review_replay = review_contribution_return(**review_arguments)
    assert review["approval_token"]
    assert review_replay["idempotent_replay"] is True
    assert review_replay["approval_token"] is None
    assert review["payload_hash"]
    assert review["proposed_target_path_hash"] == hashlib.sha256(
        b"knowledge/adopted.md"
    ).hexdigest()
    assert not (root / "knowledge" / "adopted.md").exists()
    assert XRefCatalog.build(root).list_knowledge_catalog() == []

    adoption_id = str(uuid.uuid4())
    adoption_arguments = {
        "root": root,
        "contribution_id": contribution_id,
        "adoption_id": adoption_id,
        "reviewer": "human:alice@example.test",
        "decision_evidence": "Approve server-side canonical move.",
        "approval_token": review["approval_token"],
    }
    adopted = adopt_contribution_return(**adoption_arguments, approval_verifier=approval_verifier())
    replayed = adopt_contribution_return(**adoption_arguments, approval_verifier=approval_verifier())

    assert (root / "knowledge" / "adopted.md").read_text(encoding="utf-8") == content
    assert manifest_path.read_bytes() == original_manifest
    assert adopted["status"] == "adopted"
    assert adopted["publication"] == "not_performed"
    assert adopted["distribution"] == "not_performed"
    assert adopted["live_verification"] == "not_performed"
    assert adopted["tool_execution_performed"] is False
    assert replayed["idempotent_replay"] is True
    assert {entry["xid"] for entry in XRefCatalog.build(root).list_knowledge_catalog()} == {
        "ADOPT123"
    }
    listed = list_contribution_returns(root, approval_verifier())[0]
    assert listed["status"] == "adopted"
    assert listed["adoption"]["canonical_target"] == "knowledge/adopted.md"
    exported = export_contribution_return(root, contribution_id, approval_verifier())
    assert exported["adoption_performed"] is True
    assert [event["event"] for event in exported["review_bundle"]["events"]] == [
        "review_decided",
        "adoption_prepared",
        "adopted",
    ]


def test_review_requires_trusted_assertion_and_accepted_target(tmp_path: Path) -> None:
    root = adoption_repo(tmp_path)
    contribution_id, _content = pending_knowledge(root)
    common = {
        "contribution_id": contribution_id,
        "decision_id": str(uuid.uuid4()),
        "decision": "accepted",
        "reviewer": "human:reviewer",
        "decision_evidence": "Reviewed.",
    }
    with pytest.raises(ValueError, match="approved_target_path is required"):
        review_contribution_return(
            root,
            **common,
            approval_assertion="invalid",
            approval_verifier=approval_verifier(),
        )
    with pytest.raises(RuntimeError, match="trusted human approval verifier"):
        review_contribution_return(
            root,
            **common,
            approved_target_path="knowledge/adopted.md",
            approval_assertion="invalid",
        )
    with pytest.raises(ValueError, match="assertion"):
        review_contribution_return(
            root,
            **common,
            approved_target_path="knowledge/adopted.md",
            approval_assertion="invalid",
            approval_verifier=approval_verifier(),
        )


def test_manifest_and_signed_event_tampering_fail_closed(tmp_path: Path) -> None:
    root = adoption_repo(tmp_path)
    contribution_id, _content = pending_knowledge(root)
    review = signed_review(
        root,
        contribution_id=contribution_id,
        decision_id=str(uuid.uuid4()),
        decision="accepted",
        reviewer="human:reviewer",
        decision_evidence="Reviewed.",
        approved_target_path="knowledge/adopted.md",
    )
    record = root / ".xrefkit" / "contribution-returns" / contribution_id
    review_path = record / "events" / "review.json"
    original_review = review_path.read_bytes()
    signed = json.loads(review_path.read_text(encoding="utf-8"))
    signed["decision_evidence"] = "tampered"
    review_path.write_text(json.dumps(signed), encoding="utf-8")
    with pytest.raises(ValueError, match="signature"):
        list_contribution_returns(root, approval_verifier())
    review_path.write_bytes(original_review)
    manifest_path = record / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source"]["provider_version"] = "tampered"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="payload hash"):
        adopt_contribution_return(
            root,
            contribution_id=contribution_id,
            adoption_id=str(uuid.uuid4()),
            reviewer="human:reviewer",
            decision_evidence="Adopt.",
            approval_token=review["approval_token"],
            approval_verifier=approval_verifier(),
        )


def test_adoption_rescans_repository_xids_after_review(tmp_path: Path) -> None:
    root = adoption_repo(tmp_path)
    contribution_id, _content = pending_knowledge(root)
    review = signed_review(
        root,
        contribution_id=contribution_id,
        decision_id=str(uuid.uuid4()),
        decision="accepted",
        reviewer="human:reviewer",
        decision_evidence="Reviewed.",
        approved_target_path="knowledge/adopted.md",
    )
    existing = root / "knowledge" / "won-race.md"
    existing.parent.mkdir()
    existing.write_text("<!-- xid: ADOPT123 -->\n\n# Existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="XID already exists"):
        adopt_contribution_return(
            root,
            contribution_id=contribution_id,
            adoption_id=str(uuid.uuid4()),
            reviewer="human:reviewer",
            decision_evidence="Adopt.",
            approval_token=review["approval_token"],
            approval_verifier=approval_verifier(),
            existing_knowledge_xids=set(),
        )


def test_adoption_recovery_rejects_a_parallel_duplicate_xid(tmp_path: Path) -> None:
    root = adoption_repo(tmp_path)
    contribution_id, _content = pending_knowledge(root)
    review = signed_review(
        root,
        contribution_id=contribution_id,
        decision_id=str(uuid.uuid4()),
        decision="accepted",
        reviewer="human:reviewer",
        decision_evidence="Reviewed.",
        approved_target_path="knowledge/adopted.md",
    )

    class InterruptAfterMove:
        name = LocalCanonicalAdoptionTransport.name
        def adopt(self, **kwargs):
            result = LocalCanonicalAdoptionTransport().adopt(**kwargs)
            raise RuntimeError(f"interrupt after move: {result['target_paths']}")

    adoption_id = str(uuid.uuid4())
    arguments = dict(
        root=root,
        contribution_id=contribution_id,
        adoption_id=adoption_id,
        reviewer="human:reviewer",
        decision_evidence="Adopt.",
        approval_token=review["approval_token"],
        approval_verifier=approval_verifier(),
    )
    with pytest.raises(RuntimeError, match="interrupt after move"):
        adopt_contribution_return(**arguments, transport=InterruptAfterMove())
    with pytest.raises(ValueError, match="XID already exists"):
        adopt_contribution_return(
            **arguments,
            transport=LocalCanonicalAdoptionTransport(),
            existing_knowledge_xids={"ADOPT123"},
        )
    duplicate = root / "knowledge" / "parallel.md"
    duplicate.write_text("<!-- xid: ADOPT123 -->\n\n# Parallel\n", encoding="utf-8")
    with pytest.raises(ValueError, match="XID already exists"):
        adopt_contribution_return(
            **arguments, transport=LocalCanonicalAdoptionTransport()
        )


def test_rejected_contribution_cannot_be_adopted(tmp_path: Path) -> None:
    root = adoption_repo(tmp_path)
    contribution_id, _content = pending_knowledge(root)
    review = signed_review(
        root,
        contribution_id=contribution_id,
        decision_id=str(uuid.uuid4()),
        decision="rejected",
        reviewer="human:reviewer",
        decision_evidence="The rule duplicates an existing policy.",
    )
    assert review["approval_token"] is None
    with pytest.raises(ValueError, match="only an accepted contribution"):
        adopt_contribution_return(
            root,
            contribution_id=contribution_id,
            adoption_id=str(uuid.uuid4()),
            reviewer="human:reviewer",
            decision_evidence="Must remain rejected.",
            approval_token="not-valid",
            approval_verifier=approval_verifier(),
        )
    assert list_contribution_returns(root, approval_verifier())[0]["status"] == "rejected"
    assert not (root / "knowledge" / "adopted.md").exists()


@pytest.mark.parametrize(
    "target",
    ["../knowledge/escape.md", "docs/not-knowledge.md", "tools/not-knowledge.md"],
)
def test_review_rejects_unsafe_or_noncanonical_knowledge_target(
    tmp_path: Path, target: str
) -> None:
    root = adoption_repo(tmp_path)
    contribution_id, _content = pending_knowledge(root)
    with pytest.raises(ValueError, match="unsafe|canonical knowledge|ownership zone"):
            signed_review(
            root,
            contribution_id=contribution_id,
            decision_id=str(uuid.uuid4()),
            decision="accepted",
            reviewer="human:reviewer",
            decision_evidence="Target review.",
            approved_target_path=target,
        )


def test_adoption_never_overwrites_a_canonical_collision(tmp_path: Path) -> None:
    root = adoption_repo(tmp_path)
    contribution_id, _content = pending_knowledge(root)
    review = signed_review(
        root,
        contribution_id=contribution_id,
        decision_id=str(uuid.uuid4()),
        decision="accepted",
        reviewer="human:reviewer",
        decision_evidence="Accept target.",
        approved_target_path="knowledge/adopted.md",
    )
    target = root / "knowledge" / "adopted.md"
    target.parent.mkdir()
    target.write_text("existing\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        adopt_contribution_return(
            root,
            contribution_id=contribution_id,
            adoption_id=str(uuid.uuid4()),
            reviewer="human:reviewer",
            decision_evidence="Move accepted content.",
            approval_token=review["approval_token"],
            approval_verifier=approval_verifier(),
        )
    assert target.read_text(encoding="utf-8") == "existing\n"


def test_existing_knowledge_xid_blocks_review(tmp_path: Path) -> None:
    root = adoption_repo(tmp_path)
    contribution_id, _content = pending_knowledge(root)
    with pytest.raises(ValueError, match="XID already exists"):
        signed_review(
            root,
            contribution_id=contribution_id,
            decision_id=str(uuid.uuid4()),
            decision="accepted",
            reviewer="human:reviewer",
            decision_evidence="Accept target.",
            approved_target_path="knowledge/adopted.md",
            existing_knowledge_xids={"ADOPT123"},
        )


def test_review_binding_tamper_and_wrong_token_block_adoption(tmp_path: Path) -> None:
    root = adoption_repo(tmp_path)
    contribution_id, _content = pending_knowledge(root)
    review = signed_review(
        root,
        contribution_id=contribution_id,
        decision_id=str(uuid.uuid4()),
        decision="accepted",
        reviewer="human:reviewer",
        decision_evidence="Accept target.",
        approved_target_path="knowledge/adopted.md",
    )
    with pytest.raises(ValueError, match="approval_token"):
        adopt_contribution_return(
            root,
            contribution_id=contribution_id,
            adoption_id=str(uuid.uuid4()),
            reviewer="human:reviewer",
            decision_evidence="Adopt.",
            approval_token="wrong-token",
            approval_verifier=approval_verifier(),
        )
    review_path = root / ".xrefkit" / "contribution-returns" / contribution_id / "events" / "review.json"
    tampered = json.loads(review_path.read_text(encoding="utf-8"))
    tampered["proposed_target_path"] = "knowledge/changed.md"
    review_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="signature|proposed_target_path"):
        adopt_contribution_return(
            root,
            contribution_id=contribution_id,
            adoption_id=str(uuid.uuid4()),
            reviewer="human:reviewer",
            decision_evidence="Adopt.",
            approval_token=review["approval_token"],
            approval_verifier=approval_verifier(),
        )


def test_deterministic_tool_is_published_as_one_directory_and_never_executed(
    tmp_path: Path,
) -> None:
    root = adoption_repo(tmp_path)
    contribution_id = str(uuid.uuid4())
    marker = root / "executed.txt"
    program = f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n"
    submit_contribution_return(
        root,
        binding=binding(),
        source_snapshot=source(),
        contribution_id=contribution_id,
        kind="deterministic_tool",
        title="Returned checker",
        summary="Review this checker",
        files=[file("check.py", program), file("README.md", "# Checker\n")],
        deterministic_tool={
            "runtime": "python>=3.11",
            "entrypoint": "check.py",
            "input_contract": {"type": "object"},
            "output_contract": {"type": "object"},
            "verification_evidence": [
                {"kind": "test", "command": "pytest", "result": "passed"}
            ],
        },
        proposed_target_path="tools/returned-checker",
    )
    review = signed_review(
        root,
        contribution_id=contribution_id,
        decision_id=str(uuid.uuid4()),
        decision="accepted",
        reviewer="human:reviewer",
        decision_evidence="Contracts and evidence reviewed.",
        approved_target_path="tools/returned-checker",
    )
    adopted = adopt_contribution_return(
        root,
        contribution_id=contribution_id,
        adoption_id=str(uuid.uuid4()),
        reviewer="human:reviewer",
        decision_evidence="Approve complete tool directory move.",
        approval_token=review["approval_token"],
        approval_verifier=approval_verifier(),
    )
    assert {item["path"] for item in adopted["canonical_files"]} == {
        "tools/returned-checker/README.md",
        "tools/returned-checker/check.py",
    }
    assert (root / "tools" / "returned-checker" / "check.py").is_file()
    assert not marker.exists()


def test_local_tool_recovery_rejects_extra_tree_entries(tmp_path: Path) -> None:
    target = tmp_path / "tools" / "returned"
    target.mkdir(parents=True)
    content = "print('ok')\n"
    (target / "check.py").write_text(content, encoding="utf-8")
    (target / "extra").mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        LocalCanonicalAdoptionTransport().adopt(
            root=tmp_path,
            record_dir=tmp_path,
            contribution_id=str(uuid.uuid4()),
            adoption_id=str(uuid.uuid4()),
            kind="deterministic_tool",
            target_path="tools/returned",
            files=[AdoptionFile(
                bundle_path="check.py",
                content=content,
                content_hash=hashlib.sha256(content.encode()).hexdigest(),
            )],
            recovery_allowed=True,
        )


def test_contribution_return_over_real_mcp_stdio(tmp_path: Path) -> None:
    anyio = pytest.importorskip("anyio")
    pytest.importorskip("mcp")
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    root = Path(__file__).resolve().parents[1]
    contribution_id = str(uuid.uuid4())
    xid = f"RETURN{uuid.uuid4().hex[:12].upper()}"
    target_rel = f"knowledge/mcp-adoption-test-{uuid.uuid4().hex}.md"
    adopted_path = root / target_rel
    record_dir = root / ".xrefkit" / "contribution-returns" / contribution_id

    async def scenario(errlog) -> None:
        parameters = StdioServerParameters(
            command=sys.executable,
            cwd=str(root),
            args=["-m", "xrefkit.mcp.server", "--repo", str(root),
                  "--audit-log", str(tmp_path / "audit.jsonl"),
                  "--contribution-approval-secret", APPROVAL_SECRET],
        )
        async with stdio_client(parameters, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                startup = await session.call_tool("get_startup_context", {})
                assert not startup.isError
                rejected_maturity = await session.call_tool(
                    "assess_skill_maturity",
                    {
                        "assessment_id": str(uuid.uuid4()),
                        "skill_id": "python_review",
                        "observation_contribution_ids": [str(uuid.uuid4())],
                    },
                )
                assert rejected_maturity.isError
                assert "XREFKIT_SKILL_RUN_REQUIRED" in rejected_maturity.content[0].text
                rejected = await session.call_tool("submit_contribution_return", {
                    "contribution_id": contribution_id, "kind": "knowledge",
                    "title": "Returned", "summary": "Review", "files": [],
                    "skill_content_hash": "0" * 64, "knowledge": {"xid": xid}})
                assert rejected.isError
                assert "XREFKIT_SKILL_RUN_REQUIRED" in rejected.content[0].text

                skill = await session.call_tool("get_skill", {"skill_id": "python_review"})
                skill_body = skill.structuredContent["skill_content"]
                skill_hash = hashlib.sha256(skill_body.encode("utf-8")).hexdigest()
                run_id = str(uuid.uuid4())
                bound = await session.call_tool(
                    "bind_skill_run", {"run_id": run_id, "skill_id": "python_review"}
                )
                assert not bound.isError
                contract = await session.call_tool("get_contribution_return_contract", {})
                assert contract.structuredContent["status"] == "pending_review"
                body = f"<!-- xid: {xid} -->\n\n# Returned Knowledge\n\nBody.\n"
                args = {
                    "contribution_id": contribution_id,
                    "kind": "knowledge",
                    "title": "Returned Knowledge",
                    "summary": "Review this local learning",
                    "files": [file("knowledge/returned.md", body)],
                    "skill_content_hash": skill_hash,
                    "knowledge_versions": [],
                    "knowledge": {"xid": xid},
                    "proposed_target_path": target_rel,
                }
                stale_source = await session.call_tool(
                    "submit_contribution_return", {**args, "skill_content_hash": "0" * 64}
                )
                assert stale_source.isError
                assert "does not match the current MCP Skill body" in stale_source.content[0].text
                submitted = await session.call_tool("submit_contribution_return", args)
                replayed = await session.call_tool("submit_contribution_return", args)
                assert not submitted.isError
                assert submitted.structuredContent["status"] == "pending_review"
                assert replayed.structuredContent["idempotent_replay"] is True
                listed = await session.call_tool("list_contribution_returns", {})
                rows = listed.structuredContent["result"]
                assert any(row["contribution_id"] == contribution_id for row in rows)
                exported = await session.call_tool(
                    "export_contribution_return", {"contribution_id": contribution_id}
                )
                assert exported.structuredContent["activation_performed"] is False
                knowledge = await session.call_tool("list_knowledge_catalog", {})
                assert xid not in {
                    row["xid"] for row in knowledge.structuredContent["result"]
                }
                decision_id = str(uuid.uuid4())
                reviewed = await session.call_tool(
                    "review_contribution_return",
                    {
                        "contribution_id": contribution_id,
                        "decision_id": decision_id,
                        "decision": "accepted",
                        "reviewer": "human:mcp-integration-test",
                        "decision_evidence": "Integration fixture approval.",
                        "approved_target_path": target_rel,
                        "approval_assertion": approval_assertion(
                            root,
                            contribution_id,
                            decision_id=decision_id,
                            decision="accepted",
                            reviewer="human:mcp-integration-test",
                            approved_target_path=target_rel,
                        ),
                    },
                )
                assert not reviewed.isError
                token = reviewed.structuredContent["approval_token"]
                adopted = await session.call_tool(
                    "adopt_contribution_return",
                    {
                        "contribution_id": contribution_id,
                        "adoption_id": str(uuid.uuid4()),
                        "reviewer": "human:mcp-integration-test",
                        "decision_evidence": "Move the reviewed fixture.",
                        "approval_token": token,
                    },
                )
                assert not adopted.isError
                assert adopted.structuredContent["status"] == "adopted"
                knowledge = await session.call_tool("list_knowledge_catalog", {})
                assert xid in {
                    row["xid"] for row in knowledge.structuredContent["result"]
                }

    try:
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
            anyio.run(scenario, errlog)
        audit_events = [
            json.loads(line)["event_type"]
            for line in (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        assert "contribution.review_decided" in audit_events
        assert "contribution.adopted" in audit_events
    finally:
        adopted_path.unlink(missing_ok=True)
        shutil.rmtree(record_dir, ignore_errors=True)
        inbox = record_dir.parent
        for lock_file in (
            inbox / "inbox.lock",
            inbox / "inbox.lock.lock",
            inbox / "canonical-adoption.lock",
        ):
            lock_file.unlink(missing_ok=True)
        try:
            inbox.rmdir()
            inbox.parent.rmdir()
        except OSError:
            pass

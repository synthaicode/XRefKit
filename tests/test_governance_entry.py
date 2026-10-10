import json
import copy

import pytest

from test_subagent_startup import startup
from xrefkit.governance_entry import (
    CORE_CHECKS, RULE_SOURCES, apply_update, digest, dispatch, prepare, revalidate,
    retrospective_suggestion, snapshot, validate_result,
)
from xrefkit.mcp.contribution_adoption import HmacHumanApprovalVerifier, issue_hmac_approval_assertion

HOST_KEY = "test-host-" * 8
HUMAN_KEY = "test-human-" * 8


@pytest.fixture
def case(startup):
    root, log, _, manual = startup
    request = {k: v for k, v in manual.items() if k not in {"schema_version", "run_id"}}
    request["instruction_basis"] = "User-authorized bounded update trial"
    for path, content in (("work/candidate.md", "<!-- xid: A123456789B0 -->\n# New\n"),
                          ("work/rule.md", "source storage and role rules"),
                          ("work/specialist.md", "specialist checks complete")):
        (root / path).write_text(content)
    for path in RULE_SOURCES:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text("Governing common rule")
    payload = {"candidate": "work/candidate.md", "target": "knowledge/item.md",
               "rules": sorted(RULE_SOURCES) + ["work/rule.md"], "specialist_evidence": ["work/specialist.md"],
               "checks": sorted(CORE_CHECKS)}
    packet = prepare(root, kind="asset_update", log="work/run.md", binding_request=request,
                     materials=[*sorted(RULE_SOURCES), "work/candidate.md", "work/rule.md", "work/specialist.md"], payload=payload)
    return root, packet, request


def host_receipt(root, packet, *, failed=False):
    """Test-only trusted-host fixture, not a claim of live agent execution."""
    output = root / "work/analysis.md"
    body = {"packet_hash": packet["packet_hash"],
              "findings": [{"id": check, "result": "fail" if failed else "pass",
                            "reason": "Reviewed scoped evidence", "evidence": ["work/specialist.md"]}
                           for check in packet["payload"]["checks"]],
              "unknowns": [], "reference_roles": [], "external_reference_disposition": "no_external_refs"}
    output.write_text(json.dumps(body))
    result = {**body, "output": snapshot(root, "work/analysis.md")}
    child = root / "work/child.md"
    child.write_text("""# Skill Run Log
- run_id: `child-test-run`
- skill_id: `shared_asset_update_gate`
## Closure Gate
- status: `done`
## Runtime Artifacts
- [x] OUT kind=`output` status=`done` role=`shared_asset_update_gate:executor` target=`work/analysis.md` item=`WI-1`: packet output
""")
    child.write_text(child.read_text().replace("## Closure Gate", "- parent_run_id: `" + packet["binding"]["run_id"] + "`\n"
                    + "- root_run_id: `" + packet["binding"]["run_snapshot"]["fields"]["root_run_id"] + "`\n"
                    + "- work_item_id: `" + packet["binding"]["work_item_id"] + "`\n## Closure Gate"))
    event = {"schema": "xrefkit.governance_execution/v1", "packet_hash": packet["packet_hash"],
             "execution_id": "trusted-host-test", "child_log": "work/child.md",
             "child_log_hash": snapshot(root, "work/child.md")["sha256"],
             "skill_id": "shared_asset_update_gate", "result": result, "result_hash": digest(result)}
    verifier = HmacHumanApprovalVerifier(HOST_KEY)
    return {"event": event, "signature": verifier.seal_event(event)}


def approval(packet, receipt):
    return issue_hmac_approval_assertion(HUMAN_KEY, {
        "action": "apply_governed_asset", "packet_hash": packet["packet_hash"],
        "target": packet["payload"]["target"], "result_hash": digest(receipt["event"]["result"]),
    })


def test_trusted_host_dispatch_then_separate_human_application(case):
    root, packet, _ = case
    called = []
    def host(frozen):
        called.append(frozen["packet_hash"])
        return host_receipt(root, frozen)
    receipt = dispatch(root, packet, host, HmacHumanApprovalVerifier(HOST_KEY))
    assert called == [packet["packet_hash"]]
    assert not (root / "knowledge/item.md").exists()
    result = apply_update(root, packet, receipt, host_verifier=HmacHumanApprovalVerifier(HOST_KEY),
                          approval_verifier=HmacHumanApprovalVerifier(HUMAN_KEY),
                          approval_assertion=approval(packet, receipt))
    assert result["runtime_activation"] == "not_performed"
    assert (root / "knowledge/item.md").read_bytes() == (root / "work/candidate.md").read_bytes()
    with pytest.raises(ValueError, match="target baseline"):
        apply_update(root, packet, receipt, host_verifier=HmacHumanApprovalVerifier(HOST_KEY),
                     approval_verifier=HmacHumanApprovalVerifier(HUMAN_KEY),
                     approval_assertion=approval(packet, receipt))


@pytest.mark.parametrize("path", ["work/candidate.md", "work/rule.md", "work/specialist.md"])
def test_changed_dependencies_block_final_application(case, path):
    root, packet, _ = case
    receipt = host_receipt(root, packet)
    (root / path).write_text("changed")
    with pytest.raises(ValueError, match="material changed"):
        validate_result(root, packet, receipt, HmacHumanApprovalVerifier(HOST_KEY))


def test_plan_or_forged_signature_is_not_execution(case):
    root, packet, _ = case
    with pytest.raises(ValueError, match="execution receipt"):
        validate_result(root, packet, {"dispatch_owner": "client_host"}, HmacHumanApprovalVerifier(HOST_KEY))
    receipt = host_receipt(root, packet)
    receipt["event"]["execution_id"] = "forged"
    with pytest.raises(ValueError, match="signature"):
        validate_result(root, packet, receipt, HmacHumanApprovalVerifier(HOST_KEY))


def test_failed_gate_or_wrong_human_authority_cannot_write(case):
    root, packet, _ = case
    receipt = host_receipt(root, packet, failed=True)
    with pytest.raises(ValueError, match="failed gate"):
        apply_update(root, packet, receipt, host_verifier=HmacHumanApprovalVerifier(HOST_KEY),
                     approval_verifier=HmacHumanApprovalVerifier(HUMAN_KEY),
                     approval_assertion=approval(packet, receipt))
    receipt = host_receipt(root, packet)
    with pytest.raises(ValueError, match="signature"):
        apply_update(root, packet, receipt, host_verifier=HmacHumanApprovalVerifier(HOST_KEY),
                     approval_verifier=HmacHumanApprovalVerifier(HOST_KEY),
                     approval_assertion=approval(packet, receipt))
    assert not (root / "knowledge/item.md").exists()


def test_existing_target_changed_under_review_is_not_overwritten(case):
    root, packet, request = case
    (root / "knowledge/item.md").write_text("old")
    payload = {k: v for k, v in packet["payload"].items() if k != "expected_target_hash"}
    packet = prepare(root, kind="asset_update", log="work/run.md", binding_request=request,
                     materials=[m["path"] for m in packet["materials"]], payload=payload)
    receipt = host_receipt(root, packet)
    (root / "knowledge/item.md").write_text("another writer")
    with pytest.raises(ValueError, match="target baseline"):
        apply_update(root, packet, receipt, host_verifier=HmacHumanApprovalVerifier(HOST_KEY),
                     approval_verifier=HmacHumanApprovalVerifier(HUMAN_KEY),
                     approval_assertion=approval(packet, receipt))
    assert (root / "knowledge/item.md").read_text() == "another writer"


def test_suppression_is_semantic_persistent_and_direct_request_can_override(case):
    root, _, _ = case
    kwargs = {"scope": "comparison interval one", "reason": "corrected responsibility",
              "evidence": ["work/specialist.md"]}
    assert retrospective_suggestion(root, "work/retro-state.json", **kwargs)["suggest"]
    retrospective_suggestion(root, "work/retro-state.json", **kwargs, response="declined")
    assert not retrospective_suggestion(root, "work/retro-state.json", **kwargs)["suggest"]
    direct = retrospective_suggestion(root, "work/retro-state.json", **kwargs, response="human_request")
    assert direct["analysis_authorized"] and not direct["adoption_authorized"]
    (root / "work/specialist.md").write_text("new substantive correction")
    assert retrospective_suggestion(root, "work/retro-state.json", **kwargs)["suggest"]


def test_retrospective_requires_scoped_consent_and_cannot_apply(case):
    root, _, request = case
    payload = {"scope": "interval one", "reason": "explicit correction",
               "consent": {"intent": "OK", "scope": "interval one", "evidence": "work/specialist.md"},
               "task_basis": "comparison", "correction_evidence": ["work/specialist.md"]}
    with pytest.raises(ValueError, match="human execution"):
        prepare(root, kind="correction_retrospective", log="work/run.md", binding_request=request,
                materials=["work/specialist.md"], payload=payload)
    payload["consent"]["intent"] = "execute_retrospective"
    packet = prepare(root, kind="correction_retrospective", log="work/run.md", binding_request=request,
                     materials=["work/specialist.md"], payload=payload)
    with pytest.raises(ValueError, match="analysis consent"):
        apply_update(root, packet, {}, host_verifier=HmacHumanApprovalVerifier(HOST_KEY),
                     approval_verifier=HmacHumanApprovalVerifier(HUMAN_KEY), approval_assertion="unused")


def test_mandatory_checks_and_target_scope_cannot_be_removed(case):
    root, packet, request = case
    payload = {k: v for k, v in packet["payload"].items() if k != "expected_target_hash"}
    payload["checks"] = ["external_references"]
    with pytest.raises(ValueError, match="applicable rules"):
        prepare(root, kind="asset_update", log="work/run.md", binding_request=request,
                materials=[m["path"] for m in packet["materials"]], payload=payload)


@pytest.mark.parametrize("mutation", [
    lambda p: p["payload"].update(target="docs/not-allowed.md"),
    lambda p: p["payload"].update(candidate=p["payload"]["target"]),
    lambda p: p["payload"].update(checks=["external_references"]),
    lambda p: p.update(binding={}),
    lambda p: p.update(materials=["bad"]),
])
def test_recomputed_packet_digest_cannot_bypass_structural_scope(case, mutation):
    root, original, _ = case
    packet = copy.deepcopy(original)
    mutation(packet)
    packet["packet_hash"] = digest({k: v for k, v in packet.items() if k != "packet_hash"})
    with pytest.raises(ValueError):
        revalidate(root, packet)


def test_child_linkage_and_saved_result_must_match(case):
    root, packet, _ = case
    receipt = host_receipt(root, packet)
    child = root / "work/child.md"
    child.write_text(child.read_text().replace(packet["binding"]["run_id"], "unrelated-parent"))
    receipt["event"]["child_log_hash"] = snapshot(root, "work/child.md")["sha256"]
    receipt["signature"] = HmacHumanApprovalVerifier(HOST_KEY).seal_event(receipt["event"])
    with pytest.raises(ValueError, match="separate completed child"):
        validate_result(root, packet, receipt, HmacHumanApprovalVerifier(HOST_KEY))
    receipt = host_receipt(root, packet)
    receipt["event"]["result"]["unknowns"] = ["not in saved output"]
    receipt["event"]["result_hash"] = digest(receipt["event"]["result"])
    receipt["signature"] = HmacHumanApprovalVerifier(HOST_KEY).seal_event(receipt["event"])
    with pytest.raises(ValueError, match="saved analysis"):
        validate_result(root, packet, receipt, HmacHumanApprovalVerifier(HOST_KEY))


def test_existing_target_approved_replacement(case):
    root, packet, request = case
    (root / "knowledge/item.md").write_text("old target")
    payload = {k: v for k, v in packet["payload"].items() if k != "expected_target_hash"}
    packet = prepare(root, kind="asset_update", log="work/run.md", binding_request=request,
                     materials=[m["path"] for m in packet["materials"]], payload=payload)
    receipt = host_receipt(root, packet)
    apply_update(root, packet, receipt, host_verifier=HmacHumanApprovalVerifier(HOST_KEY),
                 approval_verifier=HmacHumanApprovalVerifier(HUMAN_KEY),
                 approval_assertion=approval(packet, receipt))
    assert (root / "knowledge/item.md").read_bytes() == (root / "work/candidate.md").read_bytes()


def test_cli_does_not_overwrite_parent_log_or_suppression_state(case, tmp_path):
    from xrefkit.governance_entry_cli import main
    root, packet, _ = case
    request = root / "work/request.json"
    request.write_text(json.dumps({"state_path": "work/state.json", "scope": "one", "reason": "correction",
                                   "evidence": ["work/specialist.md"]}))
    assert main(["--root", str(root), "suggest", "--request", str(request), "--out", str(root / "work/state.json")]) == 2
    assert not (root / "work/state.json").exists()
    request.write_text("[]")
    assert main(["--root", str(root), "prepare", "--request", str(request), "--out", str(root / "work/out.json")]) == 2


def test_retrospective_result_validation_uses_same_scoped_host_boundary(case):
    root, _, request = case
    payload = {"scope": "interval one", "reason": "explicit correction",
               "consent": {"intent": "execute_retrospective", "scope": "interval one", "evidence": "work/specialist.md"},
               "task_basis": "fixed inline requirement", "correction_evidence": ["work/specialist.md"]}
    packet = prepare(root, kind="correction_retrospective", log="work/run.md", binding_request=request,
                     materials=["work/specialist.md"], payload=payload)
    # Reuse trusted-host fixture provenance, replacing only the declared method/result.
    gate_packet = copy.deepcopy(packet)
    gate_packet["payload"]["checks"] = []
    receipt = host_receipt(root, gate_packet)
    result = {"packet_hash": packet["packet_hash"], "findings": [{"classification": "local_condition",
              "reason": "bounded case only", "evidence": ["work/specialist.md"], "disposition": "stay_in_work"}], "unknowns": []}
    (root / "work/analysis.md").write_text(json.dumps(result))
    result["output"] = snapshot(root, "work/analysis.md")
    child = root / "work/child.md"
    child.write_text(child.read_text().replace("shared_asset_update_gate", "correction_retrospective_analyst"))
    receipt["event"].update(skill_id="correction_retrospective_analyst", result=result, result_hash=digest(result),
                             child_log_hash=snapshot(root, "work/child.md")["sha256"])
    receipt["signature"] = HmacHumanApprovalVerifier(HOST_KEY).seal_event(receipt["event"])
    assert validate_result(root, packet, receipt, HmacHumanApprovalVerifier(HOST_KEY))["findings"][0]["disposition"] == "stay_in_work"


def test_cli_reserves_evidence_before_application_and_reports_partial_save_failure(case, monkeypatch, capsys):
    from pathlib import Path
    from xrefkit.governance_entry_cli import main
    root, packet, _ = case
    receipt = host_receipt(root, packet)
    request_path, receipt_path, human_path = [root / ("work/" + name) for name in ("packet.json", "receipt.json", "human.txt")]
    request_path.write_text(json.dumps(packet))
    receipt_path.write_text(json.dumps(receipt))
    human_path.write_text(approval(packet, receipt))
    monkeypatch.setenv("XREFKIT_GOVERNANCE_HOST_SECRET", HOST_KEY)
    monkeypatch.setenv("XREFKIT_GOVERNANCE_HUMAN_SECRET", HUMAN_KEY)
    out = root / "work/reflection.json"
    out.mkdir()
    argv = ["--root", str(root), "apply", "--request", str(request_path), "--receipt", str(receipt_path),
            "--approval-file", str(human_path), "--out", str(out)]
    assert main(argv) == 2
    assert not (root / "knowledge/item.md").exists()
    out.rmdir()
    original = Path.write_text
    def fail_evidence(self, *args, **kwargs):
        if self == out:
            raise OSError("test evidence save unavailable")
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "write_text", fail_evidence)
    assert main(argv) == 3
    assert (root / "knowledge/item.md").exists()
    assert "application completed but reflection evidence save failed" in capsys.readouterr().out

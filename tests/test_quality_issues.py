"""Synthetic quality corrections; no real conversations or business data."""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from xrefkit.gateway import Feedback, evaluate
from xrefkit.mcp.audit import SessionRunBinding
from xrefkit.mcp.contribution_adoption import HmacHumanApprovalVerifier, issue_hmac_approval_assertion
from xrefkit.mcp.contribution_returns import submit_contribution_return, list_contribution_returns
from xrefkit.quality_issues import (
    decide_quality_issue, get_quality_issue, list_quality_issues, prepare_quality_issue,
    quality_decision_claims, submit_quality_feedback, validate_quality_report,
)

SECRET = "synthetic-quality-approval-secret-32-bytes"


def report():
    attempt = {"id": "a1", "goal_id": "example", "scope_revision": 0,
               "model": "test", "route_ref": "route-1", "reason": "initial"}
    corrected = {**attempt, "id": "a2", "reason": "instruction_miss", "retry_of": "a1",
                 "reason_evidence": "human-correction-1: requested missing heading"}
    return {
        "version": 1, "occurred_at": "2026-11-15T10:00:00Z", "classification": "instruction_miss",
        "common_rule_relation": "Approved output headings were omitted",
        "observed_facts": ["The requested heading was absent from the first output"],
        "correction_evidence": [{"evidence_id": "human-correction-1", "summary": "Add the agreed heading",
                                 "content_hash": "a" * 64}],
        "output_before": {"evidence_id": "output-1", "summary": "Heading omitted", "content_hash": "b" * 64},
        "output_after": None, "diff_summary": "unknown: revised output not yet available",
        "inferred_causes": [], "unknowns": ["cause unknown", "revised output unavailable"],
        "impact": "One synthetic output", "similarity_key": "missing-heading",
        "feedback": {"version": 1, "cost_unit": "unknown", "attempts": [attempt, corrected]},
        "transfer": "sanitized_nonconfidential",
    }


def fixture_args():
    run_id = str(uuid.uuid4())
    return {
        "report": report(), "observation": {
            "skill_id": "sample", "skill_content_hash": "c" * 64, "maturity_at_use": "trial",
            "run_id": run_id, "client_id": "test-client-1", "execution_environment": "test",
            "model_id": "test-model", "outcome": "failure", "retry_count": 1,
            "evaluation_evidence": [{"evidence_id": "human-correction-1", "kind": "human_correction",
                                     "reference": "sanitized-correction-1", "content_hash": "a" * 64}],
            "ambiguities": ["cause unknown"],
        }, "contribution_id": str(uuid.uuid4()), "title": "Missing agreed heading",
        "summary": "Synthetic human correction", "destination": "test-server",
        "policy": {"destination": "test-server", "allowed": True,
                   "data_classification": "sanitized_nonconfidential",
                   "authorization_reference": "test host configuration"},
        "knowledge_versions": [{"xid": "ABCDEF123456", "content_hash": "d" * 64}],
    }


def save(root, args=None):
    args = args or fixture_args()
    payload = prepare_quality_issue(**args)
    binding = SessionRunBinding(run_id=args["observation"]["run_id"], mcp_session_id=str(uuid.uuid4()),
                                repository_fingerprint="a" * 32, skill_id="sample")
    source = {"skill_id": "sample", "skill_content_hash": "c" * 64,
              "skill_maturity": "trial", "knowledge_versions": args["knowledge_versions"]}
    payload.pop("skill_content_hash")
    payload.pop("knowledge_versions")
    result = submit_contribution_return(root, binding=binding, source_snapshot=source, **payload)
    return result, {"binding": binding, "source_snapshot": source, **payload}


def decision(root, issue_id, **changes):
    args = {"issue_id": issue_id, "decision_id": str(uuid.uuid4()), "status": "triaged",
            "reviewer": "human:test", "decision_evidence": "Reviewed synthetic report", "expected_revision": 0}
    args.update(changes)
    claims = quality_decision_claims(root, **args)
    assertion = issue_hmac_approval_assertion(SECRET, {**claims, "assertion_id": str(uuid.uuid4())})
    return {**args, "approval_assertion": assertion, "approval_verifier": HmacHumanApprovalVerifier(SECRET)}


def test_explicit_first_correction_repetition_and_unknown():
    data = report()
    assert validate_quality_report(data)["output_after"] is None
    assert evaluate(Feedback.model_validate(data["feedback"]))["quality_retries"] == 1
    attempt = data["feedback"]["attempts"][-1]
    data["feedback"]["attempts"].append({**attempt, "id": "a3", "retry_of": "a2"})
    assert evaluate(Feedback.model_validate(data["feedback"]))["quality_retries"] == 2
    data["feedback"]["attempts"].append({**attempt, "id": "a4", "retry_of": "a3", "reason": "unknown",
                                       "reason_evidence": None})
    result = validate_quality_report(data)
    assert result["unknowns"] == data["unknowns"]
    assert evaluate(Feedback.model_validate(result["feedback"]))["unknown_retries"] == 1


@pytest.mark.parametrize("reason", ["requirement_change", "unknown"])
def test_requirement_change_or_unclassified_repetition_not_issue(reason):
    data = report()
    data["feedback"]["attempts"][1]["reason"] = reason
    if reason == "requirement_change":
        data["feedback"]["attempts"][1]["scope_revision"] = 1
    with pytest.raises(ValueError, match="explicit quality feedback"):
        validate_quality_report(data)


@pytest.mark.parametrize("classification", ["confidential", "personal", "unknown"])
def test_transfer_denied_before_network(classification):
    args = fixture_args()
    args["policy"]["data_classification"] = classification
    calls = []
    async def call_tool(*values):
        calls.append(values)
    with pytest.raises(ValueError, match="not authorized"):
        asyncio.run(submit_quality_feedback(call_tool=call_tool, **args))
    assert calls == []


@pytest.mark.parametrize("location", ["report", "title", "file"])
def test_sensitive_data_rejected_on_both_boundaries(tmp_path, location):
    args = fixture_args()
    if location == "report":
        args["report"]["observed_facts"] = ["password=synthetic-credential"]
    elif location == "title":
        args["title"] = "Contact synthetic.person@example.invalid"
    if location != "file":
        with pytest.raises(ValueError, match="sensitive"):
            prepare_quality_issue(**args)
        return
    _, payload = save(tmp_path, args)
    payload["contribution_id"] = str(uuid.uuid4())
    payload["files"][0]["content"] = "api_key=synthetic-credential"
    payload["files"][0]["content_hash"] = hashlib.sha256(payload["files"][0]["content"].encode()).hexdigest()
    with pytest.raises(ValueError, match="sensitive"):
        submit_contribution_return(tmp_path, **payload)
    assert not (tmp_path / ".xrefkit/contribution-returns" / payload["contribution_id"]).exists()


def test_optional_metadata_old_observation_and_inert_storage(tmp_path):
    result, payload = save(tmp_path)
    issue = get_quality_issue(tmp_path, result["contribution_id"])
    assert issue["status"] == "reported"
    assert issue["binding"]["run_id"] == payload["binding"].run_id
    assert issue["source"]["knowledge_versions"][0]["xid"] == "ABCDEF123456"
    assert issue["source"]["skill_content_hash"] == "c" * 64
    assert not (tmp_path / "knowledge").exists()
    assert not (tmp_path / "skills").exists()
    payload["contribution_id"] = str(uuid.uuid4())
    del payload["skill_observation"]["quality_issue"]
    submit_contribution_return(tmp_path, **payload)
    assert len(list_contribution_returns(tmp_path)) == 2
    assert len(list_quality_issues(tmp_path)) == 1


def test_duplicate_and_concurrent_intake_preserve_reports(tmp_path):
    result, payload = save(tmp_path)
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(lambda _: submit_contribution_return(tmp_path, **payload), range(3)))
    assert all(row["idempotent_replay"] for row in rows)
    changed = copy.deepcopy(payload)
    changed["summary"] = "Different content"
    with pytest.raises(ValueError, match="different payload"):
        submit_contribution_return(tmp_path, **changed)
    args = fixture_args()
    args["observation"]["client_id"] = "test-client-2"
    other, _ = save(tmp_path, args)
    listed = list_quality_issues(tmp_path, status="reported", skill_id="sample")
    assert len(listed) == 2 and all(row["report_count"] == 2 for row in listed)
    assert {row["issue_id"] for row in listed} == {result["contribution_id"], other["contribution_id"]}
    assert len({row["observation"]["client_id"] for row in listed}) == 2


def test_signed_human_decision_history_and_no_adoption(tmp_path):
    result, _ = save(tmp_path)
    issue_id = result["contribution_id"]
    args = decision(tmp_path, issue_id)
    first = decide_quality_issue(tmp_path, **args)
    assert first["created"]
    assert decide_quality_issue(tmp_path, **args)["idempotent_replay"]
    with pytest.raises(ValueError, match="claim mismatch"):
        decide_quality_issue(tmp_path, **{**args, "decision_evidence": "substituted evidence"})
    with pytest.raises(ValueError, match="stale issue revision"):
        decide_quality_issue(tmp_path, **decision(tmp_path, issue_id))
    with pytest.raises(ValueError, match="verification evidence"):
        decision(tmp_path, issue_id, status="resolved", expected_revision=1)
    decide_quality_issue(tmp_path, **decision(tmp_path, issue_id, status="approved_for_improvement", expected_revision=1))
    decide_quality_issue(tmp_path, **decision(tmp_path, issue_id, status="resolved", expected_revision=2,
                                            verification_evidence=["synthetic regression verified"]))
    issue = get_quality_issue(tmp_path, issue_id, HmacHumanApprovalVerifier(SECRET))
    assert issue["status"] == "resolved" and issue["revision"] == 3
    assert issue["report"]["inferred_causes"] == []
    assert not (tmp_path / "knowledge").exists()
    assert list_contribution_returns(tmp_path)[0]["status"] == "pending_review"
    with pytest.raises(RuntimeError, match="verifier"):
        get_quality_issue(tmp_path, issue_id)


def test_human_auth_and_tamper_fail_closed(tmp_path):
    result, _ = save(tmp_path)
    args = decision(tmp_path, result["contribution_id"])
    with pytest.raises(RuntimeError, match="verifier"):
        decide_quality_issue(tmp_path, **{**args, "approval_verifier": None})
    with pytest.raises(ValueError, match="approval assertion"):
        decide_quality_issue(tmp_path, **{**args, "approval_assertion": "human says yes"})
    decide_quality_issue(tmp_path, **args)
    event_path = tmp_path / ".xrefkit/contribution-returns" / result["contribution_id"] / "quality-decisions/00000000.json"
    event = json.loads(event_path.read_text())
    event["status"] = "closed"
    event_path.write_text(json.dumps(event))
    with pytest.raises(ValueError, match="signature"):
        get_quality_issue(tmp_path, result["contribution_id"], args["approval_verifier"])


def test_quality_client_to_real_mcp(tmp_path):
    anyio = pytest.importorskip("anyio")
    pytest.importorskip("mcp")
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from xrefkit.mcp.catalog import XRefCatalog
    code_root = Path(__file__).resolve().parents[1]
    root = tmp_path / "repository"
    root.mkdir()
    for directory in ("docs", "agent", "skills", "knowledge", "governance", "observations"):
        shutil.copytree(code_root / directory, root / directory)
    shutil.copy2(code_root / "ownership.yaml", root / "ownership.yaml")
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True)
    catalog = XRefCatalog.build(root)
    skill = catalog.get_skill("python_review")
    skill_hash = hashlib.sha256(skill["skill_content"].encode()).hexdigest()
    async def scenario(errlog):
        parameters = StdioServerParameters(command=sys.executable, cwd=str(code_root), args=[
            "-m", "xrefkit.mcp.server", "--repo", str(root), "--profile", "admin",
            "--audit-log", str(tmp_path / "audit.jsonl"), "--contribution-approval-secret", SECRET])
        async with stdio_client(parameters, errlog=errlog) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                assert (await session.call_tool("list_quality_issues", {})).isError
                assert not (await session.call_tool("get_startup_context", {})).isError
                assert not (await session.call_tool("get_quality_issue_contract", {})).isError
                args = fixture_args()
                args["observation"].update(skill_id="python_review", skill_content_hash=skill_hash,
                                            maturity_at_use=skill["maturity"])
                args["knowledge_versions"] = []
                await session.call_tool("get_skill", {"skill_id": "python_review"})
                assert not (await session.call_tool("bind_skill_run", {
                    "run_id": args["observation"]["run_id"], "skill_id": "python_review"})).isError
                result = await submit_quality_feedback(call_tool=session.call_tool, **args)
                assert not result.isError, result
                replay = await submit_quality_feedback(call_tool=session.call_tool, **args)
                assert replay.structuredContent["idempotent_replay"]
                rows = await session.call_tool("list_quality_issues", {})
                assert len(rows.structuredContent["result"]) == 1
                dargs = decision(root, args["contribution_id"])
                dargs.pop("approval_verifier")
                decided = await session.call_tool("decide_quality_issue", dargs)
                assert not decided.isError, decided
                detail = await session.call_tool("get_quality_issue", {"issue_id": args["contribution_id"]})
                assert detail.structuredContent["status"] == "triaged"
                assert len(detail.structuredContent["history"]) == 1
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as errlog:
        anyio.run(scenario, errlog)

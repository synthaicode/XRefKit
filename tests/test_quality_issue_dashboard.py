"""Local HTTP tests with synthetic corrections and a test-only trusted issuer."""
from __future__ import annotations

import http.client
import json
import threading
import uuid
from contextlib import contextmanager

import pytest

from xrefkit.dashboard import DashboardHandler, DashboardServer, _html_page, build_payload
from xrefkit.mcp.contribution_adoption import HmacHumanApprovalVerifier, issue_hmac_approval_assertion
from test_quality_issues import SECRET, save, fixture_args


@contextmanager
def server(root, *, trusted=True):
    instance = DashboardServer(("127.0.0.1", 0), DashboardHandler, root=root,
                               sessions_dir=root / "work/sessions", mcp_audit_log=root / "work/mcp/audit.jsonl",
                               approval_verifier=HmacHumanApprovalVerifier(SECRET) if trusted else None)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    try:
        yield instance
    finally:
        instance.shutdown()
        instance.server_close()
        thread.join(timeout=5)


def request(instance, path, body=None, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", instance.server_port, timeout=10)
    try:
        base = {"Content-Type": "application/json", "X-XRefKit-CSRF": instance.csrf_token}
        base.update(headers or {})
        conn.request("GET" if body is None else "POST", path, json.dumps(body) if body is not None else None, base)
        response = conn.getresponse()
        data = response.read().decode("utf-8")
        return response.status, dict(response.getheaders()), data
    finally:
        conn.close()


def test_console_keeps_all_runtime_panels_and_backward_payload(tmp_path):
    payload = build_payload(tmp_path, tmp_path / "work/sessions")
    page = _html_page(payload)
    for label in ("Quality Issues", "Governance", "Runtime Diagnostics", "Quality Evaluation"):
        assert label in page
    for panel in ("plans", "overview", "flows", "recovery", "attention", "closure", "evidence", "handoff", "xids", "analysis", "missing-information", "decision-trace"):
        assert f'data-panel="{panel}"' in page
        assert f'id="{panel}"' in page
    with server(tmp_path) as instance:
        status, _, body = request(instance, "/api/runs")
        assert status == 200
        assert json.loads(body)["runs"] == payload["runs"]
        status, headers, body = request(instance, "/?panel=closure&run_id=synthetic")
        assert 'data-console-area="runtime"' in body
        assert headers["Cache-Control"] == "no-store"
        assert headers["X-Frame-Options"] == "DENY"


def test_list_filter_detail_and_governance(tmp_path):
    saved, _ = save(tmp_path)
    issue_id = saved["contribution_id"]
    with server(tmp_path) as instance:
        status, _, body = request(instance, "/api/quality-issues?status=reported&skill_id=sample")
        assert status == 200
        assert json.loads(body)["issues"][0]["issue_id"] == issue_id
        assert json.loads(request(instance, "/api/quality-issues?status=closed")[2])["issues"] == []
        detail = json.loads(request(instance, f"/api/quality-issues/{issue_id}")[2])
        assert detail["report"]["unknowns"]
        assert detail["binding"]["run_id"]
        assert request(instance, f"/api/quality-issues/{issue_id}/source?xid=UNRELATED")[0] == 400
        assert request(instance, f"/api/quality-issues/{uuid.uuid4()}")[0] == 404
        assert json.loads(request(instance, "/api/contributions")[2])["contributions"][0]["contribution_id"] == issue_id
        assert request(instance, f"/api/contributions/{issue_id}")[0] == 200


def test_human_decision_assertion_history_replay_and_stale_revision(tmp_path):
    saved, _ = save(tmp_path)
    issue_id = saved["contribution_id"]
    fields = {"issue_id": issue_id, "decision_id": str(uuid.uuid4()), "status": "triaged",
              "reviewer": "human:test", "decision_evidence": "Reviewed synthetic correction", "expected_revision": 0}
    with server(tmp_path) as instance:
        status, _, body = request(instance, "/api/quality-issues/decision-claims", fields)
        assert status == 200
        claims = json.loads(body)
        fields["approval_assertion"] = issue_hmac_approval_assertion(SECRET, {**claims, "assertion_id": str(uuid.uuid4())})
        assert request(instance, "/api/quality-issues/decisions", fields)[0] == 200
        assert json.loads(request(instance, "/api/quality-issues/decisions", fields)[2])["idempotent_replay"]
        detail = json.loads(request(instance, f"/api/quality-issues/{issue_id}")[2])
        assert detail["status"] == "triaged"
        assert len(detail["history"]) == 1
        stale = {**fields, "decision_id": str(uuid.uuid4())}
        stale.pop("approval_assertion")
        claims = json.loads(request(instance, "/api/quality-issues/decision-claims", stale)[2])
        stale["approval_assertion"] = issue_hmac_approval_assertion(SECRET, {**claims, "assertion_id": str(uuid.uuid4())})
        status, _, body = request(instance, "/api/quality-issues/decisions", stale)
        assert status == 400 and "stale" in body
    assert not (tmp_path / "knowledge").exists()


@pytest.mark.parametrize("headers", [{"X-XRefKit-CSRF": "wrong"}, {"Origin": "https://foreign.invalid"}, {"Host": "foreign.invalid"}])
def test_browser_cross_origin_or_missing_token_cannot_decide(tmp_path, headers):
    with server(tmp_path) as instance:
        assert request(instance, "/api/quality-issues/decisions", {}, headers)[0] == 403


def test_assertion_not_reviewer_name_and_readonly_default(tmp_path):
    saved, _ = save(tmp_path)
    body = {"issue_id": saved["contribution_id"], "decision_id": str(uuid.uuid4()), "status": "triaged",
            "reviewer": "human:test", "decision_evidence": "explicit synthetic choice", "expected_revision": 0,
            "approval_assertion": "self-declared"}
    with server(tmp_path) as instance:
        assert request(instance, "/api/quality-issues/decisions", body)[0] == 400
        assert request(instance, "/", headers={"Host": "foreign.invalid"})[0] == 403
    with server(tmp_path, trusted=False) as instance:
        assert request(instance, "/api/quality-issues/decisions", body)[0] == 403
        assert "Read-only: a trusted human approval verifier is not configured" in request(instance, "/")[2]


def test_untrusted_report_is_only_rendered_as_text(tmp_path):
    args = fixture_args()
    args["title"] = '<img src=x onerror="alert(1)">'
    save(tmp_path, args)
    with server(tmp_path) as instance:
        page = request(instance, "/")[2]
        assert args["title"] not in page
        assert "e.textContent = value" in page
        assert "detail.replaceChildren" in page
        assert "innerHTML" not in page[page.index('document.addEventListener("DOMContentLoaded"'):page.index("<div id=\"console-runtime\"")]


def test_bad_request_is_bounded_and_unknown_fields_refused(tmp_path):
    with server(tmp_path) as instance:
        assert request(instance, "/api/quality-issues/decision-claims", {"unexpected": "field"})[0] == 400
        assert request(instance, "/api/quality-issues/decisions", {}, {"Content-Type": "text/plain"})[0] == 400
        assert request(instance, "/api/quality-issues?status=not-a-state")[0] == 400
        missing = {"issue_id": str(uuid.uuid4()), "decision_id": str(uuid.uuid4()), "status": "triaged", "reviewer": "human:test", "decision_evidence": "synthetic", "expected_revision": 0}
        assert request(instance, "/api/quality-issues/decision-claims", missing)[0] == 404
        assert request(instance, "/api/quality-issues/decisions", {**missing, "approval_assertion": "synthetic"})[0] == 404


@pytest.mark.parametrize("value", [False, 0, {}, [123]])
def test_decision_evidence_types_are_not_coerced(tmp_path, value):
    saved, _ = save(tmp_path)
    fields = {"issue_id": saved["contribution_id"], "decision_id": str(uuid.uuid4()), "status": "triaged",
              "reviewer": "human:test", "decision_evidence": "synthetic", "expected_revision": 0,
              "verification_evidence": value}
    with server(tmp_path) as instance:
        assert request(instance, "/api/quality-issues/decision-claims", fields)[0] == 400


def test_governance_reuses_review_and_separate_adoption(tmp_path):
    (tmp_path / "ownership.yaml").write_text("""zones:
  - id: records
    owner: operational
    paths:
      - observations/
    catalog: false
    distribution: false
    base_sync: false
    shadowing: false
""", encoding="utf-8")
    saved, _ = save(tmp_path)
    fields = {"contribution_id": saved["contribution_id"], "decision_id": str(uuid.uuid4()),
              "decision": "accepted", "reviewer": "human:test", "decision_evidence": "Reviewed inert observation",
              "approved_target_path": "observations/synthetic-quality.md"}
    target = tmp_path / fields["approved_target_path"]
    with server(tmp_path) as instance:
        status, _, body = request(instance, "/api/contributions/review-claims", fields)
        assert status == 200, body
        claims = json.loads(body)
        assert not target.exists()
        assert request(instance, "/api/contributions/review", {**fields, "approval_assertion": "self-declared"})[0] == 400
        assertion = issue_hmac_approval_assertion(SECRET, {**claims, "assertion_id": str(uuid.uuid4())})
        status, _, body = request(instance, "/api/contributions/review", {**fields, "approval_assertion": assertion})
        assert status == 200, body
        assert not target.exists()
        adoption = {"contribution_id": fields["contribution_id"], "adoption_id": str(uuid.uuid4()),
                    "reviewer": "human:test", "decision_evidence": "Publish accepted observation",
                    "approval_token": json.loads(body)["approval_token"]}
        assert request(instance, "/api/contributions/adopt", {**adoption, "approval_token": "wrong"})[0] == 400
        status, _, body = request(instance, "/api/contributions/adopt", adoption)
        assert status == 200, body
        assert target.is_file()
        assert json.loads(request(instance, f'/api/quality-issues/{fields["contribution_id"]}')[2])["status"] == "reported"
    assert not (tmp_path / "knowledge").exists()

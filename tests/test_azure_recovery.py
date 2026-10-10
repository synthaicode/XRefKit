import copy
import json
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

import pytest

from test_azure_writer import setup as writer_setup, import_setup, metadata
from test_azure_import import payload, Response, CANARY
from xrefkit import azure_import as importer
from xrefkit import azure_recovery as module
from xrefkit import azure_writer as writer
from xrefkit.work_management import read_json, record_plan

ITEM_URL = "https://dev.azure.com/example/Test%20Project/_apis/wit/workItems/21"


def publish_remote(setup, request=None, lost=False, intent_only=False, before=None):
    calls, captured = [], {}
    current = copy.deepcopy(before or payload(21, **{"System.State": "In Progress", "System.Description": "unchanged", "System.AssignedTo": {"id": "person"}, "Microsoft.VSTS.Scheduling.RemainingWork": 3, "Microsoft.VSTS.CMMI.Blocked": "No", "Custom.DueDate": "2026-10-12"}))
    current["url"] = ITEM_URL
    class Opener:
        def open(self, req, timeout):
            calls.append(req)
            assert timeout == 30
            if req.get_method() == "PATCH":
                if intent_only: raise KeyboardInterrupt()
                operations = json.loads(req.data)
                assert operations[0]["value"] == current["rev"]
                current["rev"] += 1
                for op in operations[1:]:
                    current["fields"][op["path"].removeprefix("/fields/")] = op["value"]
                captured["after"] = copy.deepcopy(current)
                if lost: raise TimeoutError("synthetic lost response")
            elif "workitemtypes" in req.full_url:
                return Response(req, metadata())
            elif "/workitems/10?" in req.full_url:
                return Response(req, payload(10))
            return Response(req, current)
    root, original, _, _ = setup
    with patch.dict("os.environ", {"IMPORT_TEST_PAT": CANARY}), patch.object(writer, "build_opener", return_value=Opener()):
        if intent_only:
            with pytest.raises(KeyboardInterrupt): writer.publish(root, "local", request or original)
            result = None
        else:
            result = writer.publish(root, "local", request or original)
    return result, copy.deepcopy(current), calls


@pytest.fixture
def setup(writer_setup):
    result, current, _ = publish_remote(writer_setup, lost=True)
    assert result["outcome"] == "unknown"
    request = {"schema_version": 1, "reconciliation_id": "recovery-1", "report_id": "write-1", "connection_id": "import-test", "source_connection_id": "write-test", "binding_id": "binding-1", "expected_observation_revision": 2, "approval_refs": ["recover.md"]}
    return writer_setup, request, current


def reads(current, historical=None, *, fail_phase=None, error=None, mutation=None):
    calls = []
    class Opener:
        def open(self, req, timeout):
            calls.append(req)
            assert req.get_method() == "GET" and req.data is None and timeout == 30
            assert "api-version=7.1" in req.full_url and "%24expand=Relations" in req.full_url
            phase = "revision" if "/revisions/" in req.full_url else "root" if "/workitems/10?" in req.full_url else "current"
            if phase == fail_phase: raise error or TimeoutError(CANARY)
            value = copy.deepcopy(payload(10) if phase == "root" else historical if phase == "revision" else current)
            if phase == "revision" and value is not None and "url" in value and "/revisions/" not in value["url"]:
                value["url"] += "/revisions/" + str(value["rev"])
            if mutation: value = mutation(phase, value)
            return Response(req, value)
    return patch.dict("os.environ", {"IMPORT_TEST_PAT": CANARY}), patch.object(writer, "build_opener", return_value=Opener()), calls


def reconcile(setup, request=None, current=None, historical=None, **kwargs):
    writer_setup, original, actual = setup
    env, opener, calls = reads(current or actual, historical, **kwargs)
    with env, opener:
        result = module.reconcile(writer_setup[0], "local", request or original)
    return result, calls


def advance(writer_setup):
    root, _, path, _ = writer_setup
    plan = read_json(path)
    expected = plan["observation_revision"]
    for key in ["observation_revision", "observation_history", "report_sha256"]: plan.pop(key)
    plan["report_id"] = "observation-" + str(expected + 1)
    record_plan(root, plan, expected)
    return expected + 1


def protected_bytes(root):
    return {path: path.read_bytes() for folder in ["work/plans", "work/integrations/connections", "work/integrations/imports", "work/integrations/bindings", "work/integrations/deliveries/intents", "work/integrations/deliveries/receipts"] for path in (root / folder).glob("*") if path.is_file()}


def test_positive_current_proof_preserves_original_and_replay_no_network(setup):
    writer_setup, request, _ = setup
    root = writer_setup[0]
    old = protected_bytes(root)
    result, calls = reconcile(setup)
    assert result["outcome"] == "confirmed_applied" and result["resume_ready"]
    assert result["after"] == {"revision": 3, "state": "In Progress"} and len(calls) == 2
    assert not result["remote_write_attempted"] and result["original_write_attempted"]
    assert protected_bytes(root) == old
    with patch.object(writer.os.environ, "get", side_effect=AssertionError("no credential on replay")), patch.object(writer, "build_opener") as http:
        replay = module.reconcile(root, "local", request)
        status = module.inspect_status(root, "local", "write-1")
    assert replay["replayed"] and not replay["network_attempted"] and replay["captured_network_attempted"]
    assert status["pending"] and status["reconciliations"][0]["resume_ready"]
    assert status["resume_guidance"] == "select_confirmed_reconciliation_and_new_observation"
    http.assert_not_called()


def test_historical_applied_current_changed_never_unlocks(setup):
    writer_setup, request, after = setup
    current = copy.deepcopy(after)
    current["rev"] = 4
    current["fields"]["System.History"] = "Later human change"
    result, calls = reconcile(setup, current=current, historical=after)
    assert result["outcome"] == "applied_remote_changed" and not result["resume_ready"] and len(calls) == 3
    assert "/revisions/3?" in calls[2].full_url
    saved = read_json(Path(result["output"]))
    assert saved["historical_url"] == ITEM_URL + "/revisions/3"
    assert "Later human change" not in Path(result["output"]).read_text(encoding="utf-8")
    new_obs = advance(writer_setup)
    with patch.object(writer.os.environ, "get", side_effect=AssertionError("no credential")):
        with pytest.raises(ValueError): writer.publish(writer_setup[0], "local", {**writer_setup[1], "report_id": "resume", "expected_observation_revision": new_obs, "previous_reconciliation_id": request["reconciliation_id"]})


@pytest.mark.parametrize("change", ["history_marker_only", "state", "description", "assigned", "remaining", "blocked", "due", "absent_null", "parent", "type", "project", "body_revision"])
def test_full_proof_mismatch_remains_unresolved(setup, change):
    current = copy.deepcopy(setup[2])
    fields = current["fields"]
    if change == "history_marker_only": fields["System.History"] = "XRefKit report=write-1"
    elif change == "state": fields["System.State"] = "Done"
    elif change == "description": fields["System.Description"] = "changed"
    elif change == "assigned": fields["System.AssignedTo"] = None
    elif change == "remaining": fields["Microsoft.VSTS.Scheduling.RemainingWork"] = 4
    elif change == "blocked": fields["Microsoft.VSTS.CMMI.Blocked"] = "Yes"
    elif change == "due": fields["Custom.DueDate"] = None
    elif change == "absent_null": fields.pop("System.Description")
    elif change == "parent": current["relations"][0]["url"] = "https://dev.azure.com/example/_apis/wit/workItems/11"
    elif change == "type": fields["System.WorkItemType"] = "Bug"
    elif change == "project": fields["System.TeamProject"] = "Other"
    else: current["rev"] = True
    result, calls = reconcile(setup, current=current)
    assert result["outcome"] == "unresolved" and not result["resume_ready"]
    assert all(call.get_method() == "GET" for call in calls)


@pytest.mark.parametrize("change", ["revision", "url_revision", "url_item", "url_host", "url_project", "url_suffix", "missing_url", "guid", "marker"])
def test_exact_historical_revision_url_and_identity_negative(setup, change):
    historical = copy.deepcopy(setup[2])
    historical["url"] += "/revisions/3"
    current = copy.deepcopy(setup[2])
    current["rev"] = 4
    if change == "revision": historical["rev"] = 4
    elif change == "url_revision": historical["url"] = ITEM_URL + "/revisions/4"
    elif change == "url_item": historical["url"] = ITEM_URL.replace("/21", "/22") + "/revisions/3"
    elif change == "url_host": historical["url"] = historical["url"].replace("dev.azure.com", "evil.invalid")
    elif change == "url_project": historical["url"] = historical["url"].replace("Test%20Project", "Other")
    elif change == "url_suffix": historical["url"] += "?secret=not-followed"
    elif change == "missing_url": historical.pop("url")
    elif change == "guid": historical["url"] = historical["url"].replace("Test%20Project", "11111111-2222-3333-4444-555555555555")
    else: historical["fields"]["System.History"] = "XRefKit report=write-1"
    result, calls = reconcile(setup, current=current, historical=historical)
    assert result["outcome"] == "unresolved" and not result["resume_ready"] and len(calls) == 3


@pytest.mark.parametrize("phase,code", [("root", 401), ("current", 403), ("revision", 404), ("root", 429), ("current", 500), ("revision", None)])
def test_expired_auth_partial_failure_and_later_explicit_read(setup, phase, code):
    current = copy.deepcopy(setup[2])
    current["rev"] = 4
    error = HTTPError("https://not-printed", code, CANARY, {}, None) if code else TimeoutError(CANARY)
    failed, calls = reconcile(setup, current=current, historical=setup[2], fail_phase=phase, error=error)
    assert failed["outcome"] == "unresolved" and failed["network_attempted"] and not failed["remote_write_attempted"]
    assert failed["phases"][-1]["outcome"] == "failed"
    assert len(calls) == {"root": 1, "current": 2, "revision": 3}[phase]
    assert CANARY not in json.dumps(failed) and CANARY not in Path(failed["output"]).read_text(encoding="utf-8")
    fresh, _ = reconcile(setup, request={**setup[1], "reconciliation_id": "fresh"})
    assert fresh["outcome"] == "confirmed_applied" and Path(failed["output"]).exists()


def test_missing_pat_no_network_and_original_unknown_still_blocks(setup):
    writer_setup, request, _ = setup
    with patch.dict("os.environ", {}, clear=True), patch.object(writer, "build_opener") as http:
        result = module.reconcile(writer_setup[0], "local", request)
    assert result["outcome"] == "unresolved" and not result["network_attempted"]
    assert result["phases"] == [{"phase": "root", "outcome": "not_attempted", "diagnostic_code": "credential_unavailable", "network_attempted": False}]
    http.assert_not_called()
    with pytest.raises(ValueError): writer.publish(writer_setup[0], "local", {**writer_setup[1], "report_id": "new"})


@pytest.mark.parametrize("change", ["source", "read_scope", "binding", "stale", "approval", "extra", "boolean"])
def test_reconciliation_preflight_rejects_before_credentials(setup, change):
    writer_setup, original, _ = setup
    request = copy.deepcopy(original)
    if change == "source": request["source_connection_id"] = "import-test"
    elif change == "read_scope": request["connection_id"] = "missing"
    elif change == "binding": request["binding_id"] = "other"
    elif change == "stale": request["expected_observation_revision"] = 1
    elif change == "approval": request["approval_refs"] = []
    elif change == "extra": request["patch"] = []
    else: request["expected_observation_revision"] = True
    with patch.object(writer.os.environ, "get", side_effect=AssertionError("credential read")), patch.object(writer, "build_opener") as http:
        with pytest.raises(ValueError): module.reconcile(writer_setup[0], "local", request)
        http.assert_not_called()


def test_explicit_recovered_successor_then_normal_chain_no_fork(setup):
    writer_setup, request, current = setup
    root = writer_setup[0]
    reconcile(setup)
    obs = advance(writer_setup)
    second_request = {**writer_setup[1], "report_id": "write-2", "expected_observation_revision": obs, "previous_reconciliation_id": "recovery-1"}
    second, current, _ = publish_remote(writer_setup, request=second_request, before=current)
    assert second["sent_confirmed"] and second["after"]["revision"] == 4
    status = module.inspect_status(root, "local", "write-1")
    assert not status["reconciliations"][0]["resume_ready"] and status["reconciliations"][0]["captured_resume_ready"]
    assert status["resume_guidance"] == "inspect_explicit_descendant_report"
    with patch.object(writer.os.environ, "get", side_effect=AssertionError("credential read")):
        with pytest.raises(ValueError): writer.publish(root, "local", {**second_request, "report_id": "fork"})
    obs = advance(writer_setup)
    third_request = {**writer_setup[1], "report_id": "write-3", "expected_observation_revision": obs, "previous_report_id": "write-2"}
    third, _, _ = publish_remote(writer_setup, request=third_request, before=current)
    assert third["sent_confirmed"]
    status = module.inspect_status(root, "local", "write-2")
    assert status["resume_guidance"] == "inspect_explicit_descendant_report"
    assert status["last_success"]["verified_at"] is None and status["last_success"]["receipt_recorded_at"] is not None


def test_nested_recovery_chain_retains_all_discharged_unknown_ancestors(setup):
    writer_setup, request, current = setup
    root = writer_setup[0]
    reconcile(setup)
    obs = advance(writer_setup)
    second_request = {**writer_setup[1], "report_id": "write-2", "expected_observation_revision": obs, "previous_reconciliation_id": "recovery-1"}
    second, current, _ = publish_remote(writer_setup, request=second_request, before=current, lost=True)
    assert second["outcome"] == "unknown"
    second_recovery_request = {**request, "report_id": "write-2", "reconciliation_id": "recovery-2", "expected_observation_revision": obs}
    second_recovery, _ = reconcile(setup, request=second_recovery_request, current=current)
    assert second_recovery["resume_ready"]
    obs = advance(writer_setup)
    third_request = {**writer_setup[1], "report_id": "write-3", "expected_observation_revision": obs, "previous_reconciliation_id": "recovery-2"}
    third, current, _ = publish_remote(writer_setup, request=third_request, before=current)
    assert third["sent_confirmed"]
    obs = advance(writer_setup)
    fourth_request = {**writer_setup[1], "report_id": "write-4", "expected_observation_revision": obs, "previous_report_id": "write-3"}
    fourth, _, _ = publish_remote(writer_setup, request=fourth_request, before=current)
    assert fourth["sent_confirmed"]


@pytest.mark.parametrize("field", ["summary", "protected", "applied_revision", "current_revision", "intent_hash", "terminal_hash", "source_hash", "truth_alias", "phase", "outcome", "history_url"])
def test_resealed_recovery_corruption_cannot_unlock_writer(setup, field):
    writer_setup, request, _ = setup
    result, _ = reconcile(setup)
    path = Path(result["output"])
    record = read_json(path)
    if field == "summary": record["applied"]["summary_sha256"] = "0" * 64
    elif field == "protected": record["applied"]["protected_fields"]["fields"] = {}
    elif field == "applied_revision": record["applied"]["revision"] = 9
    elif field == "current_revision": record["current"]["revision"] = True
    elif field == "intent_hash": record["intent_sha256"] = "0" * 64
    elif field == "terminal_hash": record["terminal_sha256"] = None
    elif field == "source_hash": record["source"]["plan_definition_sha256"] = "0" * 64
    elif field == "truth_alias": record["original_write_attempted"] = 1
    elif field == "phase": record["phases"][0]["diagnostic_code"] = "credential_unavailable"
    elif field == "outcome": record["outcome"] = "unresolved"
    else: record["historical_url"] = ITEM_URL + "/revisions/3"
    path.write_text(json.dumps(importer._seal({k: v for k, v in record.items() if k != "record_sha256"})), encoding="utf-8")
    with patch.object(writer.os.environ, "get", side_effect=AssertionError("credential read")):
        with pytest.raises(ValueError): module.reconcile(writer_setup[0], "local", request)
        with pytest.raises(ValueError): module.inspect_status(writer_setup[0], "local", "write-1")


def test_intent_only_crash_before_send_never_infers_not_sent(writer_setup):
    _, current, _ = publish_remote(writer_setup, intent_only=True)
    req = {"schema_version": 1, "reconciliation_id": "recover-crash", "report_id": "write-1", "connection_id": "import-test", "source_connection_id": "write-test", "binding_id": "binding-1", "expected_observation_revision": 2, "approval_refs": ["recover.md"]}
    setup = writer_setup, req, current
    result, _ = reconcile(setup, historical=payload(21, **{"System.State": "In Progress"}))
    assert result["outcome"] == "unresolved" and result["original_write_attempted"] is None
    assert module.inspect_status(writer_setup[0], "local", "write-1")["pending"]


def test_known_hold_retained_without_credential_or_remote_read(writer_setup):
    root = writer_setup[0]
    with patch.dict("os.environ", {}, clear=True):
        assert writer.publish(root, "local", writer_setup[1])["outcome"] == "hold"
    req = {"schema_version": 1, "reconciliation_id": "hold", "report_id": "write-1", "connection_id": "import-test", "source_connection_id": "write-test", "binding_id": "binding-1", "expected_observation_revision": 2, "approval_refs": ["recover.md"]}
    with patch.object(writer.os.environ, "get", side_effect=AssertionError("credential read")), patch.object(writer, "build_opener") as http:
        result = module.reconcile(root, "local", req)
    assert result["outcome"] == "retained_non_success" and not result["network_attempted"] and not result["resume_ready"]
    http.assert_not_called()


def test_save_failure_preserves_unknown_and_network_truth(setup, capsys):
    writer_setup, request, _ = setup
    root = writer_setup[0]
    input_path = root / "recover-input.json"
    input_path.write_text(json.dumps(request), encoding="utf-8")
    before = protected_bytes(root)
    env, http, calls = reads(setup[2])
    with env, http, patch.object(importer, "_save", side_effect=OSError(CANARY)):
        assert module.main(["reconcile", "--root", str(root), "--workspace-id", "local", "--input", str(input_path)]) == 1
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["network_attempted"] and not result["resume_ready"] and not result["remote_write_attempted"]
    assert CANARY not in captured.out + captured.err and len(calls) == 2
    assert protected_bytes(root) == before
    with pytest.raises(ValueError): writer.publish(root, "local", {**writer_setup[1], "report_id": "new"})


def test_duplicate_recovery_request_changed_input_refuses_no_network(setup):
    reconcile(setup)
    with patch.object(writer.os.environ, "get", side_effect=AssertionError("credential read")):
        with pytest.raises(ValueError): module.reconcile(setup[0][0], "local", {**setup[1], "approval_refs": ["other.md"]})


def test_recovery_lock_prevents_overlap_and_plan_change(setup):
    root = setup[0][0]
    def mutation(phase, value):
        with pytest.raises(OSError): module.reconcile(root, "local", {**setup[1], "reconciliation_id": "overlap"})
        with pytest.raises(OSError): advance(setup[0])
        return value
    result, _ = reconcile(setup, mutation=mutation)
    assert result["resume_ready"]


def test_cli_invalid_secret_argument_never_echoes(capsys):
    assert module.main(["reconcile", "--pat", CANARY]) == 1
    captured = capsys.readouterr()
    assert CANARY not in captured.out + captured.err and "Traceback" not in captured.err


def test_resealed_unknown_empty_phases_is_rejected(setup):
    result, _ = reconcile(setup, fail_phase="root")
    path = Path(result["output"])
    value = read_json(path)
    value["phases"] = []
    value["network_attempted"] = False
    path.write_text(json.dumps(importer._seal({k: v for k, v in value.items() if k != "record_sha256"})), encoding="utf-8")
    with pytest.raises(ValueError, match="reconciliation_record_invalid"):
        module.inspect_status(setup[0][0], "local", "write-1")


@pytest.mark.parametrize("field", ["System.History", "System.Description"])
def test_recovery_resume_requires_fresh_full_proof_without_patch(setup, field):
    writer_setup, _, current = setup
    reconcile(setup)
    obs = advance(writer_setup)
    current["fields"][field] = "concurrent change at captured revision"
    request = {**writer_setup[1], "report_id": "fresh-conflict", "expected_observation_revision": obs, "previous_reconciliation_id": "recovery-1"}
    result, _, calls = publish_remote(writer_setup, request=request, before=current)
    assert result["outcome"] == "conflict" and not result["remote_write_attempted"]
    assert all(call.get_method() == "GET" for call in calls)


def test_alternate_recovery_id_cannot_fork_consumed_origin(setup):
    writer_setup, request, current = setup
    reconcile(setup)
    reconcile(setup, request={**request, "reconciliation_id": "alternate"})
    obs = advance(writer_setup)
    resume = {**writer_setup[1], "report_id": "successor", "expected_observation_revision": obs, "previous_reconciliation_id": "recovery-1"}
    assert publish_remote(writer_setup, request=resume, before=current)[0]["sent_confirmed"]
    status = module.inspect_status(writer_setup[0], "local", "write-1")
    assert all(p["captured_resume_ready"] and not p["resume_ready"] for p in status["reconciliations"])
    with patch.object(writer.os.environ, "get", side_effect=AssertionError("credential read")):
        with pytest.raises(ValueError):
            writer.publish(writer_setup[0], "local", {**resume, "report_id": "fork", "previous_reconciliation_id": "alternate"})


def test_recovered_predecessor_is_not_reducer_initial_binding(setup):
    writer_setup, _, current = setup
    reconcile(setup)
    obs = advance(writer_setup)
    request = {**writer_setup[1], "report_id": "resumed", "expected_observation_revision": obs, "previous_reconciliation_id": "recovery-1"}
    reducer = writer.build_candidate
    captured = []
    def inspect(envelope):
        captured.append(envelope)
        return reducer(envelope)
    with patch.object(writer, "build_candidate", side_effect=inspect):
        assert publish_remote(writer_setup, request=request, before=current)[0]["sent_confirmed"]
    assert captured and captured[0]["binding"]["initial_binding"] is False


def test_other_unknown_blocks_captured_recovery_status_and_resume(setup):
    writer_setup, _, _ = setup
    root = writer_setup[0]
    reconcile(setup)
    directory = root / "work/integrations/deliveries/intents"
    original = read_json(next(directory.glob("*.json")))
    other = copy.deepcopy(original)
    other["record_id"] = "other-unknown"
    other["request"]["report_id"] = "other-unknown"
    other["request"]["expected_observation_revision"] = 3
    other["request_sha256"] = importer._hash(other["request"])
    other["source"]["observation_revision"] = 3
    other["candidate"]["summary"] = other["candidate"]["summary"].replace("report=write-1;", "report=other-unknown;")
    other["patch"] = writer._patch(other["before"], other["candidate"]["proposed_state"], other["candidate"]["summary"])
    importer._save(directory, importer._seal({k: v for k, v in other.items() if k != "record_sha256"}))
    status = module.inspect_status(root, "local", "write-1")
    assert status["resume_guidance"] == "investigate_other_unresolved_report"
    assert status["other_unresolved_reports"] == ["other-unknown"]
    assert status["reconciliations"][0]["captured_resume_ready"] and not status["reconciliations"][0]["resume_ready"]
    obs = advance(writer_setup)
    with patch.object(writer.os.environ, "get", side_effect=AssertionError("credential read")):
        with pytest.raises(ValueError):
            writer.publish(root, "local", {**writer_setup[1], "report_id": "blocked", "expected_observation_revision": obs, "previous_reconciliation_id": "recovery-1"})

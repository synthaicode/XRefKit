import copy
import json
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

import pytest

from test_azure_import import setup as import_setup, acquire, payload, Response, CANARY
from xrefkit import azure_writer as module
from xrefkit import azure_import as importer
from xrefkit.azure_connection import register_connection, validate_profile
from xrefkit.work_management import record_plan, read_json


def metadata():
    states = ["To Do", "In Progress", "Done", "Removed"]
    return {"name": "Task", "referenceName": "Microsoft.VSTS.WorkItemTypes.Task", "isDisabled": False, "states": [{"name": n} for n in states], "transitions": {n: [{"to": t, "actions": None} for t in states] for n in ["", *states]}, "fields": [{"referenceName": n} for n in ["System.State", "System.History"]]}


@pytest.fixture
def setup(import_setup):
    root, profile, _, binding, plan_path, plan = import_setup
    acquire(import_setup, values={10: payload(10), 19: payload(19), 21: payload(21, **{"System.State": "In Progress"})})
    importer.bind(root, "local", binding)
    plan = copy.deepcopy(plan)
    plan["steps"][2]["status"] = "in_progress"
    plan["report_id"] = "observation-2"
    record_plan(root, plan, 1)
    writer_profile = {**profile, "connection_id": "write-test", "allowed_operations": ["read_work_item", "update_task_state_history"], "allowed_item_ids": [10, 21]}
    register_connection(root, "local", writer_profile)
    request = {"schema_version": 1, "report_id": "write-1", "connection_id": "write-test", "source_connection_id": "import-test", "write_approval_refs": ["approval.md"], "binding_id": "binding-1", "item_id": 21, "expected_observation_revision": 2, "completion": {"confirmed": False, "evidence_refs": []}, "work_authorization": {"active": True, "rework": False, "evidence_refs": ["active.md"]}, "artifacts": [{"artifact_id": "design", "version": "v1", "availability": "local_only"}]}
    return root, request, plan_path, writer_profile


def network(*, mutation=None, patch_failure=None, readback_failure=None, patch_fields=None):
    calls = []
    before = payload(21, **{"System.State": "In Progress", "System.Description": "unchanged", "System.AssignedTo": {"id": "person"}, "Microsoft.VSTS.Scheduling.RemainingWork": 3, "Microsoft.VSTS.CMMI.Blocked": "No", "Custom.DueDate": "2026-10-12"})
    after = None

    class Opener:
        def open(self, request, timeout):
            nonlocal after
            assert timeout == 30
            calls.append(request)
            if request.get_method() == "PATCH":
                if patch_failure:
                    raise patch_failure
                operations = json.loads(request.data)
                assert operations[0] == {"op": "test", "path": "/rev", "value": before["rev"]}
                assert set(o["path"] for o in operations).issubset({"/rev", "/fields/System.State", "/fields/System.History"})
                assert "bypassRules=false" in request.full_url and "validateOnly=false" in request.full_url
                assert request.get_header("Content-type") == "application/json-patch+json"
                after = copy.deepcopy(before)
                after["rev"] += 1
                for operation in operations[1:]:
                    after["fields"][operation["path"].removeprefix("/fields/")] = operation["value"]
                if patch_fields:
                    after["fields"].update(patch_fields)
                value = after
            elif "workitemtypes/Task" in request.full_url:
                value = metadata()
            elif "/workitems/10?" in request.full_url:
                value = payload(10)
            else:
                if after is not None and readback_failure:
                    raise readback_failure
                value = copy.deepcopy(after or before)
            if mutation:
                value = mutation(request, copy.deepcopy(value))
            return Response(request, value)

    return patch.dict("os.environ", {"IMPORT_TEST_PAT": CANARY}), patch.object(module, "build_opener", return_value=Opener()), calls


def deliver(setup, request=None, **kwargs):
    root, original, _, _ = setup
    env, transport, calls = network(**kwargs)
    with env, transport:
        result = module.publish(root, "local", original if request is None else request)
    return result, calls


def test_success_exact_patch_local_preservation_and_replay(setup):
    root, request, plan_path, _ = setup
    before = plan_path.read_bytes(), plan_path.with_suffix(".md").read_bytes()
    old_files = {p: p.read_bytes() for folder in ["connections", "imports", "bindings"] for p in (root / "work/integrations" / folder).glob("*.json")}
    result, calls = deliver(setup)
    assert result["outcome"] == "success" and result["sent_confirmed"] and result["after"] == {"revision": 3, "state": "In Progress"}
    assert [r.get_method() for r in calls] == ["GET", "GET", "GET", "PATCH", "GET"]
    operations = json.loads(calls[3].data)
    assert len(operations) == 2 and "XRefKit report=write-1" in operations[-1]["value"]
    assert "Offline preview" not in operations[-1]["value"] and "design@v1" in operations[-1]["value"]
    assert "active.md" not in operations[-1]["value"] and "approval.md" not in operations[-1]["value"]
    assert before == (plan_path.read_bytes(), plan_path.with_suffix(".md").read_bytes())
    assert all(path.read_bytes() == data for path, data in old_files.items())
    with patch.object(module.os.environ, "get", side_effect=AssertionError("credential on replay")), patch.object(module, "build_opener") as http:
        replay = module.publish(root, "local", request)
        assert replay["replayed"] and replay["sent_confirmed"] and not replay["network_attempted"] and not replay["remote_write_attempted"]
        http.assert_not_called()


@pytest.mark.parametrize("change", ["pbi", "other_task", "old_profile", "source_profile", "stale", "approval", "unknown", "literal_token", "bool_revision"])
def test_preflight_denials_before_credentials(setup, change):
    root, original, _, _ = setup
    request = copy.deepcopy(original)
    if change == "pbi": request["item_id"] = 10
    elif change == "other_task": request["item_id"] = 19
    elif change == "old_profile": request["connection_id"] = "import-test"
    elif change == "source_profile": request["source_connection_id"] = "write-test"
    elif change == "stale": request["expected_observation_revision"] = 1
    elif change == "approval": request["write_approval_refs"] = []
    elif change == "unknown": request["desired_state"] = "Done"
    elif change == "literal_token": request["pat"] = CANARY
    else: request["expected_observation_revision"] = True
    with patch.object(module.os.environ, "get", side_effect=AssertionError("credential read")), patch.object(module, "build_opener") as http:
        with pytest.raises(ValueError): module.publish(root, "local", request)
        http.assert_not_called()


@pytest.mark.parametrize("change", ["production", "ids", "read_missing", "duplicate"])
def test_profile_write_authority_is_explicit_narrow_test_only(setup, change):
    profile = copy.deepcopy(setup[3])
    if change == "production": profile["environment"] = "production"
    elif change == "ids": profile["allowed_item_ids"].append(19)
    elif change == "read_missing": profile["allowed_operations"] = ["update_task_state_history"]
    else: profile["allowed_operations"] = ["read_work_item", "read_work_item"]
    with pytest.raises(ValueError): validate_profile(profile)


@pytest.mark.parametrize("change", ["revision", "state", "parent", "disabled", "missing_disabled", "history_field", "transition", "state_duplicate", "metadata_echo", "continuation", "root_type"])
def test_fresh_remote_and_metadata_failures_never_patch(setup, change):
    def mutate(request, value):
        is_type = "workitemtypes" in request.full_url
        if change == "revision" and "/workitems/21?" in request.full_url: value["rev"] = 8
        elif change == "state" and "/workitems/21?" in request.full_url: value["fields"]["System.State"] = "Done"
        elif change == "parent" and "/workitems/21?" in request.full_url: value["relations"][0]["url"] = "https://dev.azure.com/example/_apis/wit/workItems/11"
        elif change == "disabled" and is_type: value["isDisabled"] = True
        elif change == "missing_disabled" and is_type: value.pop("isDisabled")
        elif change == "history_field" and is_type: value["fields"] = [{"referenceName": "System.State"}]
        elif change == "transition" and is_type: value["transitions"]["In Progress"] = []
        elif change == "state_duplicate" and is_type: value["states"].append(value["states"][0])
        elif change == "metadata_echo" and is_type: value["description"] = CANARY
        elif change == "continuation" and is_type: value["continuationToken"] = "more"
        elif change == "root_type" and "/workitems/10?" in request.full_url: value["fields"]["System.WorkItemType"] = "Task"
        return value
    result, calls = deliver(setup, mutation=mutate)
    assert result["outcome"] in {"hold", "conflict"} and not result["remote_write_attempted"]
    assert all(r.get_method() == "GET" for r in calls)
    assert CANARY not in Path(result["output"]).read_text(encoding="utf-8")


@pytest.mark.parametrize("code,outcome", [(400, "rejected"), (401, "rejected"), (403, "rejected"), (404, "rejected"), (409, "conflict"), (412, "conflict"), (422, "rejected"), (429, "rejected"), (500, "unknown"), (302, "unknown")])
def test_http_patch_outcomes_truthful_no_retry(setup, code, outcome):
    error = HTTPError("https://not-logged", code, CANARY, {}, None)
    result, calls = deliver(setup, patch_failure=error)
    assert result["outcome"] == outcome and result["remote_write_attempted"] and not result["sent_confirmed"]
    assert sum(r.get_method() == "PATCH" for r in calls) == 1
    assert CANARY not in json.dumps(result)


@pytest.mark.parametrize("failure", ["timeout", "readback", "description", "assigned", "remaining", "blocked", "due", "missing_protected", "history", "revision", "state"])
def test_ambiguous_delivery_blocks_new_ids_and_replays_without_network(setup, failure):
    root, request, _, profile = setup
    kwargs = {}
    if failure == "timeout": kwargs["patch_failure"] = TimeoutError(CANARY)
    elif failure == "readback": kwargs["readback_failure"] = TimeoutError(CANARY)
    elif failure in {"description", "assigned", "remaining", "blocked", "due"}:
        key = {"description": "System.Description", "assigned": "System.AssignedTo", "remaining": "Microsoft.VSTS.Scheduling.RemainingWork", "blocked": "Microsoft.VSTS.CMMI.Blocked", "due": "Custom.DueDate"}[failure]
        kwargs["patch_fields"] = {key: "changed"}
    else:
        def mutate(req, value):
            if req.get_method() == "PATCH":
                if failure == "missing_protected": value["fields"].pop("System.Description")
                elif failure == "history": value["fields"].pop("System.History")
                elif failure == "revision": value["rev"] = 2
                elif failure == "state": value["fields"]["System.State"] = "Done"
            return value
        kwargs["mutation"] = mutate
    result, _ = deliver(setup, **kwargs)
    assert result["outcome"] == "unknown" and result["possibly_sent"] and not result["sent_confirmed"]
    register_connection(root, "local", {**profile, "connection_id": "another-write-profile"})
    with patch.object(module.os.environ, "get", side_effect=AssertionError("credential read")), patch.object(module, "build_opener") as http:
        assert module.publish(root, "local", request)["replayed"]
        with pytest.raises(ValueError, match="writer_target_unresolved"):
            module.publish(root, "local", {**request, "report_id": "write-2", "connection_id": "another-write-profile"})
        http.assert_not_called()


def test_intent_save_failure_prevents_patch_and_crash_replay_no_send(setup):
    root, request, _, _ = setup
    original = importer._save
    def refuse(directory, record):
        if record["kind"] == "intent": raise OSError("disk failure")
        return original(directory, record)
    env, transport, calls = network()
    with env, transport, patch.object(importer, "_save", side_effect=refuse):
        with pytest.raises(module.WriterError) as failure: module.publish(root, "local", request)
        assert failure.value.network_attempted and not failure.value.remote_write_attempted
    assert all(r.get_method() == "GET" for r in calls)
    env, transport, calls = network()
    actual = module._transport
    with env, transport, patch.object(module, "_transport", wraps=actual) as wire:
        def crash(profile, token, resource, **kw):
            if kw.get("method") == "PATCH": raise KeyboardInterrupt()
            return actual(profile, token, resource, **kw)
        wire.side_effect = crash
        with pytest.raises(KeyboardInterrupt): module.publish(root, "local", request)
    with patch.object(module.os.environ, "get", side_effect=AssertionError("credential read")):
        replay = module.publish(root, "local", request)
    assert replay["outcome"] == "unknown" and replay["replayed"] and replay["possibly_sent"]


def test_terminal_save_failure_preserves_unknown_intent(setup):
    root, request, _, _ = setup
    original = importer._save
    def refuse(directory, record):
        if record["kind"] == "terminal": raise OSError("disk failure")
        return original(directory, record)
    with patch.object(importer, "_save", side_effect=refuse):
        result, calls = deliver(setup)
    assert result["outcome"] == "unknown" and result["diagnostic_code"] == "receipt_persistence_failed"
    assert sum(r.get_method() == "PATCH" for r in calls) == 1
    assert module.publish(root, "local", request)["outcome"] == "unknown"


def test_success_chain_requires_explicit_predecessor_and_new_observation(setup):
    root, request, plan_path, _ = setup
    first, _ = deliver(setup)
    assert first["sent_confirmed"]
    with pytest.raises(ValueError): module.publish(root, "local", {**request, "report_id": "write-2"})
    plan = read_json(plan_path)
    for key in ["observation_revision", "observation_history", "report_sha256"]: plan.pop(key)
    plan["steps"][2]["status"] = "done"
    plan["report_id"] = "observation-3"
    record_plan(root, plan, 2)
    second = {**request, "report_id": "write-2", "expected_observation_revision": 3, "previous_report_id": "write-1", "completion": {"confirmed": True, "evidence_refs": ["accepted.md"]}}
    # The fixture's patch revision assertion is independent of this new baseline.
    sequence = [payload(10), payload(21, **{"System.State": "In Progress"}), metadata()]
    sequence[1]["rev"] = 3
    protected = sequence[1]
    after = copy.deepcopy(protected)
    after["rev"] = 4
    after["fields"]["System.State"] = "Done"
    calls = []
    class Opener:
        def open(self, req, timeout):
            calls.append(req)
            if req.get_method() == "PATCH":
                operations = json.loads(req.data)
                assert operations[0]["value"] == 3
                after["fields"]["System.History"] = operations[-1]["value"]
                return Response(req, after)
            return Response(req, sequence.pop(0) if sequence else after)
    with patch.dict("os.environ", {"IMPORT_TEST_PAT": CANARY}), patch.object(module, "build_opener", return_value=Opener()):
        result = module.publish(root, "local", second)
    assert result["sent_confirmed"] and result["after"] == {"revision": 4, "state": "Done"}
    with pytest.raises(ValueError): module.publish(root, "local", {**second, "report_id": "fork", "expected_observation_revision": 4})


@pytest.mark.parametrize("field", ["patch", "target", "success", "after", "pair", "boolean", "protected", "binding_hash", "definition_hash"])
def test_resealed_corruption_is_rejected(setup, field):
    root, request, _, _ = setup
    result, _ = deliver(setup)
    terminal_path = Path(result["output"])
    intent_path = next((root / "work/integrations/deliveries/intents").glob("*.json"))
    path = intent_path if field in {"patch", "target", "protected", "binding_hash", "definition_hash"} else terminal_path
    value = read_json(path)
    if field == "patch": value["patch"].append({"op": "add", "path": "/fields/System.Description", "value": "unsafe"})
    elif field == "target": value["target"]["item_id"] = 19
    elif field == "success": value["sent_confirmed"] = False
    elif field == "after": value["after"]["revision"] = 2
    elif field == "pair": value["intent_sha256"] = "0" * 64
    elif field == "protected": value["protected_fields"]["fields"] = {}
    elif field == "binding_hash": value["binding_sha256"] = "0" * 64
    elif field == "definition_hash": value["source"]["plan_definition_sha256"] = "0" * 64
    else: value["network_attempted"] = 1
    value = importer._seal({k: v for k, v in value.items() if k != "record_sha256"})
    path.write_text(json.dumps(value), encoding="utf-8")
    with patch.object(module.os.environ, "get", side_effect=AssertionError("credential read")):
        with pytest.raises(ValueError): module.publish(root, "local", request)


def test_cli_secret_arguments_and_cp932_output_do_not_echo(capsys):
    assert module.main(["publish", "--pat", CANARY]) == 1
    captured = capsys.readouterr()
    assert CANARY not in captured.out + captured.err and "Traceback" not in captured.err


def test_same_id_changed_request_refuses_before_credentials(setup):
    deliver(setup)
    root, request, _, _ = setup
    with patch.object(module.os.environ, "get", side_effect=AssertionError("credential read")):
        with pytest.raises(ValueError): module.publish(root, "local", {**request, "artifacts": []})


def test_resealed_unknown_without_intent_cannot_bypass_target_guard(setup):
    root, request, _, _ = setup
    with patch.dict("os.environ", {}, clear=True):
        result = module.publish(root, "local", request)
    path = Path(result["output"])
    record = read_json(path)
    record.update(outcome="unknown", diagnostic_code="dispatch_unconfirmed")
    record = importer._seal({k: v for k, v in record.items() if k != "record_sha256"})
    path.write_text(json.dumps(record), encoding="utf-8")
    with patch.object(module.os.environ, "get", side_effect=AssertionError("credential read")):
        with pytest.raises(ValueError): module.publish(root, "local", {**request, "report_id": "other"})


@pytest.mark.parametrize("kind", ["summary", "intent", "terminal"])
def test_cli_post_get_local_failure_reports_actual_network_truth(setup, kind, capsys):
    root, request, _, _ = setup
    input_path = root / "writer-input.json"
    input_path.write_text(json.dumps(request), encoding="utf-8")
    original = importer._save
    def refuse(directory, record):
        if record["kind"] == kind: raise OSError("not printed")
        return original(directory, record)
    env, transport, calls = network()
    mock = patch.object(module, "_summary", side_effect=ValueError("not printed")) if kind == "summary" else patch.object(importer, "_save", side_effect=refuse)
    with env, transport, mock:
        assert module.main(["publish", "--root", str(root), "--workspace-id", "local", "--input", str(input_path)]) == 1
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["network_attempted"] and result["remote_write_attempted"] == (kind == "terminal")
    assert "not printed" not in captured.out + captured.err
    assert sum(r.get_method() == "PATCH" for r in calls) == (1 if kind == "terminal" else 0)


@pytest.mark.parametrize("status,revalidation", [(None, None), ("unknown", False), ("blocked", False), ("escalated", False), ("unexpected", False), ("done", True), ("pending", None)])
def test_recorded_unknown_blockers_revalidation_and_unconfirmed_criteria_hold(setup, status, revalidation):
    root, request, plan_path, _ = setup
    plan = read_json(plan_path)
    for key in ["observation_revision", "observation_history", "report_sha256"]: plan.pop(key)
    plan["steps"][2].update(status=status, revalidation_needed=revalidation)
    plan["report_id"] = "new-observation"
    record_plan(root, plan, 2)
    result, calls = deliver(setup, {**request, "expected_observation_revision": 3})
    assert result["outcome"] == "hold" and not result["remote_write_attempted"]
    assert all(r.get_method() == "GET" for r in calls)


def test_plan_lock_held_across_remote_preflight_and_send(setup):
    root, _, plan_path, _ = setup
    def mutate(req, value):
        plan = read_json(plan_path)
        for key in ["observation_revision", "observation_history", "report_sha256"]: plan.pop(key)
        plan["report_id"] = "concurrent"
        with pytest.raises(OSError): record_plan(root, plan, 2)
        return value
    result, calls = deliver(setup, mutation=mutate)
    assert result["sent_confirmed"] and len(calls) == 5

import copy
import io
import json
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

import pytest

from xrefkit import azure_import as module
from xrefkit.azure_connection import register_connection
from xrefkit.work_management import record_plan, register_workspace, read_json

CANARY = "fake-PAT-canary-for-import-tests-only"


@pytest.fixture
def setup(tmp_path):
    root = tmp_path.resolve()
    register_workspace(root, {"schema_version": 1, "workspace_id": "local", "title": "Local", "workspace_root": "."})
    profile = {"schema_version": 1, "workspace_id": "local", "connection_id": "import-test", "service": "azure_devops_services", "organization": "example", "project": "Test Project", "environment": "test", "auth": {"kind": "pat_env", "env_var": "IMPORT_TEST_PAT"}, "allowed_operations": ["read_work_item"], "allowed_item_ids": [10, *range(19, 45)]}
    register_connection(root, "local", profile)
    request = {"schema_version": 1, "import_id": "capture-1", "connection_id": "import-test", "organization": "example", "project": "Test Project", "pbi_id": 10, "task_ids": [19, 21]}
    plan = {"schema_version": 2, "workspace_id": "local", "repository_root": str(root), "plan_id": "plan", "plan_revision": "v2", "title": "Plan", "source": "source.md", "report_id": "report-1", "recorded_at": "2026-10-10T10:00:00Z", "project": {"project_id": "project", "title": "Project"}, "change": {"change_id": "change", "title": "Change"}, "baseline": {"baseline_id": "baseline"}, "stages": [{"stage_id": "work", "title": "Work"}], "steps": [{"step_id": i, "title": i, "stage_id": "work", "pbi_ids": ["PBI10"], "status": "pending", "outputs": [], "runs": [], "dependencies": []} for i in ["a", "b", "c"]], "pbis": [{"pbi_id": "PBI10", "title": "PBI", "external_ref_ids": ["ado-10"]}], "confirmations": [], "external_refs": [{"external_ref_id": "ado-10", "service": "azure_devops_services", "organization": "example", "project": "Test Project", "item_id": "10", "type_mapping": "Product Backlog Item"}]}
    (root / "source.md").write_text("source", encoding="utf-8")
    saved = record_plan(root, plan, 0)
    binding = {"schema_version": 1, "binding_id": "binding-1", "import_id": "capture-1", "plan_id": "plan", "plan_revision": "v2", "expected_observation_revision": 1, "approval_refs": ["authorized-mapping.md"], "mapping": [{"item_id": 19, "included_step_ids": ["a", "b"], "completion_criterion": "Group one confirmed"}, {"item_id": 21, "included_step_ids": ["c"], "completion_criterion": "Group two confirmed"}]}
    return root, profile, request, binding, Path(saved["output"]), plan


def payload(item_id, **fields):
    return {"id": item_id, "rev": 2, "fields": {"System.TeamProject": "Test Project", "System.WorkItemType": "Product Backlog Item" if item_id == 10 else "Task", "System.Title": "Task title", "System.State": "Done", **fields}, "relations": [{"rel": "System.LinkTypes.Hierarchy-Reverse", "url": "https://dev.azure.com/example/_apis/wit/workItems/10"}]}


class Response:
    def __init__(self, request, value, **headers):
        self.url = request.full_url
        self.status = 200
        self.headers = {"Content-Type": "application/json", **headers}
        self.body = value if isinstance(value, bytes) else json.dumps(value).encode("utf-8")
    def geturl(self): return self.url
    def read(self, size): return self.body[:size]
    def __enter__(self): return self
    def __exit__(self, *args): pass


def network(values=None, headers=None):
    calls = []
    class Opener:
        def open(self, request, timeout):
            calls.append(request)
            assert timeout == 30 and request.get_method() == "GET"
            assert "%24expand=Relations" in request.full_url and "api-version=7.1" in request.full_url
            item_id = int(request.full_url.split("?")[0].rsplit("/", 1)[1])
            value = values.get(item_id, payload(item_id)) if values is not None else payload(item_id)
            if isinstance(value, BaseException): raise value
            return Response(request, value, **(headers or {}))
    return patch.dict("os.environ", {"IMPORT_TEST_PAT": CANARY}), patch.object(module, "build_opener", return_value=Opener()), calls


def acquire(setup, values=None, request=None, headers=None):
    root, _, original, _, _, _ = setup
    env, opener, calls = network(values, headers)
    with env, opener:
        result = module.capture(root, "local", original if request is None else request)
    return result, calls


def test_exact_import_binding_replay_preserves_all_local_sources(setup):
    root, _, request, binding, plan_path, _ = setup
    md = plan_path.with_suffix(".md")
    before = plan_path.read_bytes(), md.read_bytes()
    result, calls = acquire(setup)
    assert result["complete"] and len(calls) == 3 and not result["binding_saved"]
    receipt = read_json(Path(result["output"]))
    assert receipt["items"][0]["observation"]["acceptance_criteria"] is None
    assert receipt["items"][0]["observation"]["priority"] is None
    assert receipt["items"][1]["observation"]["parent_id"] == 10
    with patch.object(module.os.environ, "get", side_effect=AssertionError("no credential lookup on replay")), patch.object(module, "build_opener") as http:
        replay = module.capture(root, "local", request)
        assert replay["replayed"] and not replay["network_attempted"] and not replay["fresh_acquisition"]
        http.assert_not_called()
    bound = module.bind(root, "local", binding)
    assert bound["binding_saved"] and module.bind(root, "local", binding)["replayed"]
    stored = read_json(Path(bound["output"]))
    assert stored["source"]["observation_revision"] == 1
    assert stored["import_record_sha256"] == receipt["record_sha256"]
    assert before == (plan_path.read_bytes(), md.read_bytes())
    assert all(s["status"] == "pending" for s in read_json(plan_path)["steps"])


@pytest.mark.parametrize("mutation", ["old_profile", "production", "project", "organization", "duplicate", "pbi_in_tasks", "workspace"])
def test_preflight_scope_refuses_before_credentials_or_network(setup, mutation):
    root, profile, original, _, _, _ = setup
    request = copy.deepcopy(original)
    workspace = "local"
    if mutation in {"old_profile", "production"}:
        profile = {**profile, "connection_id": "other", "allowed_item_ids": [10] if mutation == "old_profile" else profile["allowed_item_ids"], "environment": "production" if mutation == "production" else "test"}
        register_connection(root, "local", profile)
        request["connection_id"] = "other"
    elif mutation == "project": request["project"] = "Elsewhere"
    elif mutation == "organization": request["organization"] = "elsewhere"
    elif mutation == "duplicate": request["task_ids"] = [19, 19]
    elif mutation == "pbi_in_tasks": request["task_ids"] = [10, 19]
    else: workspace = "missing"
    with patch.object(module.os.environ, "get", side_effect=AssertionError("credential read")), patch.object(module, "build_opener") as http:
        with pytest.raises(ValueError): module.capture(root, workspace, request)
        http.assert_not_called()


@pytest.mark.parametrize("mutation", ["wrong_id", "bool_rev", "wrong_project", "wrong_type", "wrong_parent", "duplicate_parent", "missing_parent", "host_spoof", "userinfo", "query", "encoded_separator", "other_project", "title_control", "wrong_optional_type", "pat_echo", "duplicate_json", "continuation"])
def test_remote_identity_hierarchy_secret_and_response_boundaries(setup, mutation):
    value = payload(19)
    headers = None
    if mutation == "wrong_id": value["id"] = 21
    elif mutation == "bool_rev": value["rev"] = True
    elif mutation == "wrong_project": value["fields"]["System.TeamProject"] = "Other"
    elif mutation == "wrong_type": value["fields"]["System.WorkItemType"] = "Bug"
    elif mutation == "wrong_parent": value["relations"][0]["url"] = "https://dev.azure.com/example/_apis/wit/workItems/11"
    elif mutation == "duplicate_parent": value["relations"] *= 2
    elif mutation == "missing_parent": value["relations"] = []
    elif mutation == "host_spoof": value["relations"][0]["url"] = "https://dev.azure.com.evil/example/_apis/wit/workItems/10"
    elif mutation == "userinfo": value["relations"][0]["url"] = "https://user@dev.azure.com/example/_apis/wit/workItems/10"
    elif mutation == "query": value["relations"][0]["url"] += "?x=1"
    elif mutation == "encoded_separator": value["relations"][0]["url"] = "https://dev.azure.com/example%2Fother/_apis/wit/workItems/10"
    elif mutation == "other_project": value["relations"][0]["url"] = "https://dev.azure.com/example/Other/_apis/wit/workItems/10"
    elif mutation == "title_control": value["fields"]["System.Title"] = "title\u007f"
    elif mutation == "wrong_optional_type": value["fields"]["System.Description"] = {"html": "wrong"}
    elif mutation == "pat_echo": value["fields"]["System.Description"] = CANARY
    elif mutation == "duplicate_json": value = b'{"id":19,"id":19}'
    else: headers = {"x-ms-continuationtoken": "unexpected"}
    result, _ = acquire(setup, {19: value}, headers=headers)
    assert not result["complete"]
    receipt_text = Path(result["output"]).read_text(encoding="utf-8")
    assert CANARY not in receipt_text and CANARY not in json.dumps(result)
    with pytest.raises(ValueError): module.bind(setup[0], "local", setup[3])


def test_partial_authentication_stops_remaining_without_discarding_success(setup):
    error = HTTPError("ignored", 401, CANARY, {}, io.BytesIO(CANARY.encode()))
    result, calls = acquire(setup, {19: error})
    assert result["outcome"] == "partial" and len(calls) == 2
    assert result["items"][0]["outcome"] == "read_verified"
    assert result["items"][2]["outcome"] == "not_attempted"
    assert CANARY not in Path(result["output"]).read_text(encoding="utf-8")


def test_explicit_baseline_unchanged_and_changed_imports_never_replace_it(setup):
    root, _, original, binding, plan_path, _ = setup
    first, _ = acquire(setup)
    bound = module.bind(root, "local", binding)
    initial = Path(first["output"]).read_bytes(), Path(bound["output"]).read_bytes(), plan_path.read_bytes()
    request = {**original, "import_id": "capture-2", "comparison_binding_id": "binding-1", "expected_observation_revision": 1}
    unchanged, _ = acquire(setup, request=request)
    assert unchanged["complete"] and not unchanged["needs_resolution"]
    changed_value = payload(19)
    changed_value["rev"] = 3
    changed_value["fields"]["System.State"] = "In Progress"
    changed, _ = acquire(setup, {19: changed_value}, request={**request, "import_id": "capture-3"})
    assert changed["outcome"] == "changed" and changed["needs_resolution"]
    changes = read_json(Path(changed["output"]))["comparison"]["changes"]
    assert {f["field"] for f in changes[0]["fields"]} == {"revision", "state"}
    assert initial == (Path(first["output"]).read_bytes(), Path(bound["output"]).read_bytes(), plan_path.read_bytes())


@pytest.mark.parametrize("mutation", ["wrong_obs", "wrong_revision", "missing_step", "step_duplicate", "missing_group", "no_approval", "wrong_pbi_ref"])
def test_binding_requires_exact_current_source_and_explicit_groups(setup, mutation):
    root, _, _, original, plan_path, _ = setup
    acquire(setup)
    request = copy.deepcopy(original)
    if mutation == "wrong_obs": request["expected_observation_revision"] = 2
    elif mutation == "wrong_revision": request["plan_revision"] = "v1"
    elif mutation == "missing_step": request["mapping"][0]["included_step_ids"] = ["missing"]
    elif mutation == "step_duplicate": request["mapping"][1]["included_step_ids"] = ["a"]
    elif mutation == "missing_group": request["mapping"] = request["mapping"][:1]
    elif mutation == "no_approval": request["approval_refs"] = []
    else:
        plan = read_json(plan_path)
        plan["external_refs"][0]["organization"] = "other"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
    before = plan_path.read_bytes()
    with pytest.raises(ValueError): module.bind(root, "local", request)
    assert before == plan_path.read_bytes()
    assert not list((root / "work/integrations/bindings").glob("*.json"))


def test_receipt_tamper_and_identity_conflicts_are_rejected(setup):
    root, _, request, binding, _, _ = setup
    result, _ = acquire(setup)
    before = Path(result["output"]).read_bytes()
    with pytest.raises(ValueError): module.capture(root, "local", {**request, "task_ids": [19]})
    assert before == Path(result["output"]).read_bytes()
    receipt = read_json(Path(result["output"]))
    receipt["items"][1]["observation"]["revision"] = 99
    Path(result["output"]).write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError): module.bind(root, "local", binding)


def test_aggregate_size_cap_precedes_publication_and_readable_roundtrip(setup):
    root, _, original, _, _, _ = setup
    request = {**original, "task_ids": list(range(19, 40))}
    values = {i: payload(i, **{"System.Description": "x" * 60000}) for i in [10, *request["task_ids"]]}
    with pytest.raises(ValueError, match="size_exceeded"):
        acquire(setup, values, request=request)
    assert not list((root / "work/integrations/imports").glob("*.json"))
    request["task_ids"] = list(range(19, 33))
    result, _ = acquire(setup, values, request=request)
    size = Path(result["output"]).stat().st_size
    assert 800000 < size < module.MAX_BYTES
    assert module.capture(root, "local", request)["replayed"]


def test_selected_project_parent_url_is_supported_and_unrelated_links_are_inert(setup):
    value = payload(19)
    value["relations"][0]["url"] = "https://dev.azure.com/example/Test%20Project/_apis/wit/workItems/10"
    value["relations"].append({"rel": "AttachedFile", "url": "https://evil.invalid/not-followed"})
    result, calls = acquire(setup, {19: value})
    assert result["complete"] and len(calls) == 3
    assert "evil.invalid" not in Path(result["output"]).read_text(encoding="utf-8")


@pytest.mark.parametrize("key", ["continuationToken", "continuation_token", "nextLink", "@odata.nextLink", "next_link"])
def test_unexpected_body_continuation_metadata_is_rejected(setup, key):
    value = {**payload(19), key: "unread-items"}
    result, _ = acquire(setup, {19: value})
    assert not result["complete"]
    assert result["items"][1]["diagnostic_code"] == "response_identity_invalid"


@pytest.mark.parametrize("mutation", ["attempted", "diagnostic", "failed_not_attempted", "bool_id", "outcome", "unknown_field"])
def test_resealed_contradictory_receipts_are_not_accepted(setup, mutation):
    root, _, request, _, _, _ = setup
    with patch.dict("os.environ", {}, clear=True):
        result = module.capture(root, "local", request)
    receipt = read_json(Path(result["output"]))
    if mutation == "attempted": receipt["items"][0]["network_attempted"] = True
    elif mutation == "diagnostic": receipt["items"][0]["diagnostic_code"] = "read_verified"
    elif mutation == "failed_not_attempted": receipt["items"][0]["outcome"] = "failed"
    elif mutation == "bool_id": receipt["items"][0]["item_id"] = True
    elif mutation == "outcome": receipt["outcome"] = "complete"
    else: receipt["arbitrary"] = "extra"
    receipt.pop("record_sha256")
    Path(result["output"]).write_text(json.dumps(module._seal(receipt)), encoding="utf-8")
    with pytest.raises(ValueError): module.capture(root, "local", request)


def test_shared_plan_writer_lock_order_and_updated_revision_reimport(setup):
    from contextlib import contextmanager
    root, _, request, binding, plan_path, plan = setup
    acquire(setup)
    original = module.writer_lock
    locks = []
    @contextmanager
    def observe(path):
        locks.append(path)
        with original(path): yield
    with patch.object(module, "writer_lock", observe):
        bound = module.bind(root, "local", binding)
    assert locks == [root / "work/plans/.records.lock", root / "work/integrations/bindings/.bindings.lock"]
    initial = Path(bound["output"]).read_bytes()
    plan = copy.deepcopy(plan)
    plan["report_id"] = "report-2"
    plan["steps"][0]["status"] = "in_progress"
    record_plan(root, plan, 1)
    compare = {**request, "import_id": "capture-2", "comparison_binding_id": "binding-1", "expected_observation_revision": 2}
    result, _ = acquire(setup, request=compare)
    assert result["complete"] and not result["needs_resolution"]
    assert Path(bound["output"]).read_bytes() == initial
    assert read_json(plan_path)["steps"][0]["status"] == "in_progress"
    compare["import_id"] = "capture-3"
    compare["expected_observation_revision"] = 1
    with patch.object(module.os.environ, "get", side_effect=AssertionError("credentials")):
        with pytest.raises(ValueError, match="revision_conflict"):
            module.capture(root, "local", compare)


def test_plan_change_during_read_cannot_publish_comparison(setup):
    root, _, request, binding, plan_path, plan_input = setup
    acquire(setup)
    module.bind(root, "local", binding)
    old_snapshot = plan_path.read_bytes()
    updated = copy.deepcopy(plan_input)
    updated["report_id"] = "report-2"
    updated["steps"][0]["status"] = "in_progress"
    record_plan(root, updated, 1)
    newer_snapshot = plan_path.read_bytes()
    plan_path.write_bytes(old_snapshot)
    compare = {**request, "import_id": "capture-2", "comparison_binding_id": "binding-1", "expected_observation_revision": 1}
    original = module._read
    def changed(*args):
        result = original(*args)
        plan_path.write_bytes(newer_snapshot)
        return result
    with patch.object(module, "_read", changed):
        with pytest.raises(ValueError, match="revision_conflict"):
            acquire(setup, request=compare)
    assert len(list((root / "work/integrations/imports").glob("*.json"))) == 1


def test_occupied_filename_is_never_overwritten_before_network(setup):
    root, _, request, binding, _, _ = setup
    result, _ = acquire(setup)
    directory = Path(result["output"]).parent
    target = module._target(directory, "other-import")
    target.write_bytes(Path(result["output"]).read_bytes())
    before = target.read_bytes()
    with patch.object(module, "build_opener") as http:
        with pytest.raises(ValueError): module.capture(root, "local", {**request, "import_id": "other-import"})
        http.assert_not_called()
    assert target.read_bytes() == before
    target.unlink()
    bound = module.bind(root, "local", binding)
    target = module._target(Path(bound["output"]).parent, "other-binding")
    target.write_bytes(Path(bound["output"]).read_bytes())
    before = target.read_bytes()
    with pytest.raises(ValueError): module.bind(root, "local", {**binding, "binding_id": "other-binding"})
    assert target.read_bytes() == before


def test_concurrent_same_import_has_one_publication_and_no_duplicate_network(setup):
    from concurrent.futures import ThreadPoolExecutor
    root, _, request, _, _, _ = setup
    env, opener, calls = network()
    def attempt():
        try: return module.capture(root, "local", request)
        except (ValueError, OSError): return {"saved": False}
    with env, opener, ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sum(bool(r.get("saved")) for r in results) == 1
    assert len(calls) == 3
    assert len(list((root / "work/integrations/imports").glob("*.json"))) == 1


def test_cli_secret_arguments_and_invalid_json_are_sanitized(setup, capsys):
    assert module.main(["capture", "--workspace-id", "local", "--input", "unused", "--pat", CANARY]) == 1
    captured = capsys.readouterr()
    assert CANARY not in captured.out + captured.err
    path = setup[0] / "bad.json"
    path.write_text(CANARY, encoding="utf-8")
    assert module.main(["capture", "--workspace-id", "local", "--input", str(path)]) == 1
    captured = capsys.readouterr()
    assert CANARY not in captured.out + captured.err


GUID = "12345678-1234-4321-9876-123456789abc"
OTHER_GUID = "abcdef12-1234-4321-9876-123456789abc"


def guid_values():
    result = {}
    for item_id in [10, 19, 21]:
        value = payload(item_id)
        value["url"] = f"https://dev.azure.com/example/{GUID}/_apis/wit/workItems/{item_id}"
        value["relations"][0]["url"] = f"https://dev.azure.com/example/{GUID}/_apis/wit/workItems/10"
        result[item_id] = value
    return result


def test_root_validated_guid_anchors_child_self_and_parent(setup):
    result, calls = acquire(setup, guid_values())
    assert result["complete"] and len(calls) == 3
    receipt = read_json(Path(result["output"]))
    assert all(i["observation"]["canonical_project_id"] == GUID for i in receipt["items"])
    assert receipt["items"][1]["observation"]["canonical_item_url"].endswith("/19")
    assert receipt["items"][1]["observation"]["canonical_parent_url"].endswith("/10")
    assert module.bind(setup[0], "local", setup[3])["binding_saved"]


@pytest.mark.parametrize("mutation", ["root_missing_url", "root_org", "root_id", "root_project", "root_type", "root_bad_url", "task_missing_url", "task_other_guid", "task_wrong_id", "parent_other_guid", "parent_wrong_id", "parent_host", "parent_encoded_separator"])
def test_guid_cannot_be_self_authorized_by_a_task(setup, mutation):
    values = guid_values()
    if mutation == "root_missing_url": values[10].pop("url")
    elif mutation == "root_org": values[10]["url"] = values[10]["url"].replace("/example/", "/elsewhere/")
    elif mutation == "root_id": values[10]["url"] = values[10]["url"].replace("/10", "/11")
    elif mutation == "root_project": values[10]["fields"]["System.TeamProject"] = "Other"
    elif mutation == "root_type": values[10]["fields"]["System.WorkItemType"] = "Task"
    elif mutation == "root_bad_url": values[10]["url"] += "?ambiguous=1"
    elif mutation == "task_missing_url": values[19].pop("url")
    elif mutation == "task_other_guid": values[19]["url"] = values[19]["url"].replace(GUID, OTHER_GUID)
    elif mutation == "task_wrong_id": values[19]["url"] = values[19]["url"].replace("/19", "/21")
    elif mutation == "parent_other_guid": values[19]["relations"][0]["url"] = values[19]["relations"][0]["url"].replace(GUID, OTHER_GUID)
    elif mutation == "parent_wrong_id": values[19]["relations"][0]["url"] = values[19]["relations"][0]["url"].replace("/10", "/11")
    elif mutation == "parent_host": values[19]["relations"][0]["url"] = values[19]["relations"][0]["url"].replace("dev.azure.com", "evil.invalid")
    else: values[19]["relations"][0]["url"] = values[19]["relations"][0]["url"].replace("/example/", "/example%2Fother/")
    result, _ = acquire(setup, values)
    assert not result["complete"]
    assert result["items"][1]["outcome"] == "failed"
    with pytest.raises(ValueError): module.bind(setup[0], "local", setup[3])


def test_pre_guid_receipts_remain_immutable_and_null_unknown_comparison_unchanged(setup):
    root, _, original, binding, _, _ = setup
    result, _ = acquire(setup)
    path = Path(result["output"])
    receipt = read_json(path)
    for item in receipt["items"]:
        for key in module.OPTIONAL_URL_FIELDS: item["observation"].pop(key, None)
    receipt.pop("record_sha256")
    path.write_text(json.dumps(module._seal(receipt)), encoding="utf-8")
    before = path.read_bytes()
    assert module.capture(root, "local", original)["replayed"]
    module.bind(root, "local", binding)
    compare = {**original, "import_id": "after-old-format", "comparison_binding_id": "binding-1", "expected_observation_revision": 1}
    current, _ = acquire(setup, request=compare)
    assert current["outcome"] == "complete" and not current["needs_resolution"]
    assert read_json(Path(current["output"]))["comparison"]["changes"] == []
    assert path.read_bytes() == before


@pytest.mark.parametrize("mutation", ["parent_missing", "parent_null", "self_missing", "root_anchor_missing"])
def test_guid_receipt_cannot_lose_required_correlation_proof_after_reseal(setup, mutation):
    root, _, request, binding, _, _ = setup
    result, _ = acquire(setup, guid_values())
    path = Path(result["output"])
    receipt = read_json(path)
    child = receipt["items"][1]["observation"]
    if mutation == "parent_missing": child.pop("canonical_parent_url")
    elif mutation == "parent_null": child["canonical_parent_url"] = None
    elif mutation == "self_missing": child.pop("canonical_item_url")
    else:
        receipt["items"][0]["observation"].pop("canonical_project_id")
        receipt["items"][0]["observation"].pop("canonical_item_url")
    receipt.pop("record_sha256")
    path.write_text(json.dumps(module._seal(receipt)), encoding="utf-8")
    with pytest.raises(ValueError): module.capture(root, "local", request)
    with pytest.raises(ValueError): module.bind(root, "local", binding)

"""Explicit test-only work-item capture and immutable local plan binding."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import unicodedata
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlencode, urlsplit
from urllib.request import ProxyHandler, Request, build_opener

from .azure_connection import ProfileError, TIMEOUT_SECONDS, _NoRedirect, _SafeParser, _http_code, _workspace, load_connection
from .work_management import MAX_BYTES, MAX_RECORDS, _publish, _unique, plan_definition, read_json, validate_plan_v2, writer_lock

DIAGNOSTICS = {"read_verified", "credential_unavailable", "authentication_failure_stop", "network_request_failed", "authentication_rejected", "access_forbidden", "unavailable_or_not_visible", "rate_limited", "server_failure", "http_response_rejected", "redirect_rejected", "response_destination_mismatch", "response_not_json", "response_continuation_rejected", "response_size_exceeded", "response_identity_invalid", "response_credential_echo_rejected", "response_fields_invalid", "response_relations_invalid", "response_parent_invalid", "parent_url_invalid", "response_optional_field_invalid", "response_priority_invalid", "response_root_parent_invalid", "response_invalid"}


class ImportError(ValueError):
    """Fixed diagnostics only, with no rejected input or credentials."""


def _fail(code):
    raise ImportError(code)


def _text(value, limit=128):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit and not any(unicodedata.category(c) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for c in value)


def _id(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value) is not None


def _number(value):
    return type(value) is int and 0 < value <= 2**31 - 1


def _hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _capture_request(value):
    required = {"schema_version", "import_id", "connection_id", "organization", "project", "pbi_id", "task_ids"}
    optional = {"comparison_binding_id", "expected_observation_revision"}
    if not isinstance(value, dict) or not required.issubset(value) or set(value) - required - optional or type(value["schema_version"]) is not int or value["schema_version"] != 1:
        _fail("import_request_invalid")
    if not _id(value["import_id"]) or not _id(value["connection_id"]) or not _text(value["organization"]) or not _text(value["project"]) or not _number(value["pbi_id"]):
        _fail("import_identity_invalid")
    ids = value["task_ids"]
    if not isinstance(ids, list) or not ids or len(ids) > MAX_RECORDS or any(not _number(i) for i in ids) or len(set(ids)) != len(ids) or value["pbi_id"] in ids:
        _fail("selected_item_set_invalid")
    if bool(optional.intersection(value)) and (not optional.issubset(value) or not _id(value["comparison_binding_id"]) or not _number(value["expected_observation_revision"])):
        _fail("comparison_input_invalid")


def _binding_request(value):
    keys = {"schema_version", "binding_id", "import_id", "plan_id", "plan_revision", "expected_observation_revision", "approval_refs", "mapping"}
    if not isinstance(value, dict) or set(value) != keys or type(value["schema_version"]) is not int or value["schema_version"] != 1:
        _fail("binding_request_invalid")
    if any(not _id(value[k]) for k in ["binding_id", "import_id", "plan_id", "plan_revision"]) or not _number(value["expected_observation_revision"]):
        _fail("binding_identity_invalid")
    refs = value["approval_refs"]
    if not isinstance(refs, list) or not refs or len(refs) > MAX_RECORDS or any(not _text(r, 2048) for r in refs) or len(set(refs)) != len(refs):
        _fail("mapping_approval_refs_invalid")
    mapping = value["mapping"]
    if not isinstance(mapping, list) or not mapping or len(mapping) > MAX_RECORDS:
        _fail("mapping_invalid")
    items, steps = set(), set()
    for group in mapping:
        if not isinstance(group, dict) or set(group) != {"item_id", "included_step_ids", "completion_criterion"} or not _number(group["item_id"]) or group["item_id"] in items or not _text(group["completion_criterion"], 4096):
            _fail("mapping_group_invalid")
        included = group["included_step_ids"]
        if not isinstance(included, list) or not included or len(included) > MAX_RECORDS or any(not _id(i) for i in included) or len(set(included)) != len(included) or steps.intersection(included):
            _fail("mapping_step_identity_invalid")
        items.add(group["item_id"])
        steps.update(included)


def _directory(workspace, kind, create=False):
    directory = workspace / "work/integrations" / kind
    try:
        directory.resolve().relative_to(workspace)
        if create:
            directory.mkdir(parents=True, exist_ok=True)
        return directory
    except (OSError, RuntimeError, ValueError):
        _fail("integration_directory_unavailable")


def _target(directory, identity):
    return directory / (hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24] + ".json")


def _load_record(directory, identity, workspace_id, kind):
    paths = list(directory.glob("*.json"))
    if len(paths) > MAX_RECORDS:
        _fail("integration_record_limit_exceeded")
    selected = []
    for path in paths:
        try:
            path.resolve().relative_to(directory.resolve())
            value = read_json(path)
            _validate_record(value, workspace_id, kind)
        except (OSError, RuntimeError, ValueError, UnicodeError, RecursionError, TypeError, KeyError):
            _fail("integration_record_invalid")
        if value["record_id"] == identity:
            selected.append((path, value))
    if len(selected) > 1:
        _fail("integration_identity_ambiguous")
    return selected[0] if selected else None


def _seal(value):
    return {**value, "record_sha256": _hash(value)}


def _validate_record(value, workspace_id, kind):
    if not isinstance(value, dict) or value.get("schema_version") != 1 or type(value.get("schema_version")) is not int or value.get("kind") != kind or value.get("workspace_id") != workspace_id or not _id(value.get("record_id")):
        _fail("integration_record_schema_invalid")
    if value.get("record_sha256") != _hash({k: v for k, v in value.items() if k != "record_sha256"}):
        _fail("integration_record_hash_invalid")
    try:
        if datetime.fromisoformat(value["captured_at"].replace("Z", "+00:00")).utcoffset() is None:
            _fail("integration_record_time_invalid")
    except (KeyError, AttributeError, TypeError, ValueError):
        _fail("integration_record_time_invalid")
    request = value.get("request")
    if kind == "azure_import":
        if set(value) != {"schema_version", "kind", "workspace_id", "record_id", "captured_at", "request", "items", "complete", "outcome", "network_attempted", "comparison", "record_sha256"}:
            _fail("import_record_schema_invalid")
        _capture_request(request)
        if request["import_id"] != value["record_id"]:
            _fail("import_record_identity_invalid")
        ids = [request["pbi_id"], *request["task_ids"]]
        items = value["items"]
        if not isinstance(items, list) or len(items) != len(ids) or [r.get("item_id") for r in items if isinstance(r, dict)] != ids:
            _fail("import_record_items_invalid")
        for item in items:
            if set(item) != {"item_id", "outcome", "diagnostic_code", "network_attempted", "observation"} or not _number(item["item_id"]) or type(item["network_attempted"]) is not bool or item["diagnostic_code"] not in DIAGNOSTICS:
                _fail("import_record_item_invalid")
            if item["outcome"] == "read_verified":
                _validate_observation(item["observation"], request, item["item_id"])
                if not item["network_attempted"] or item["diagnostic_code"] != "read_verified":
                    _fail("import_record_item_invalid")
            elif item["outcome"] not in {"failed", "not_attempted"} or item["observation"] is not None:
                _fail("import_record_outcome_invalid")
            elif item["outcome"] == "not_attempted" and (item["network_attempted"] or item["diagnostic_code"] not in {"credential_unavailable", "authentication_failure_stop"}):
                _fail("import_record_outcome_invalid")
            elif item["outcome"] == "failed" and (not item["network_attempted"] or item["diagnostic_code"] in {"read_verified", "credential_unavailable", "authentication_failure_stop"}):
                _fail("import_record_outcome_invalid")
        complete = all(r["outcome"] == "read_verified" for r in items)
        if type(value["complete"]) is not bool or value["complete"] != complete or type(value["network_attempted"]) is not bool or value["network_attempted"] != any(r["network_attempted"] for r in items) or value["outcome"] not in {"complete", "partial", "failed", "changed"}:
            _fail("import_record_completeness_invalid")
        comparison = value["comparison"]
        if "comparison_binding_id" in request:
            if not isinstance(comparison, dict) or set(comparison) != {"binding_id", "baseline_import_id", "baseline_record_sha256", "local_observation_revision", "changes", "needs_resolution"} or comparison["binding_id"] != request["comparison_binding_id"] or not _id(comparison["baseline_import_id"]) or not _digest(comparison["baseline_record_sha256"]) or comparison["local_observation_revision"] != request["expected_observation_revision"] or type(comparison["needs_resolution"]) is not bool:
                _fail("import_comparison_invalid")
            changes = comparison["changes"]
            if not isinstance(changes, list) or len(changes) > len(ids):
                _fail("import_comparison_invalid")
            changed_ids = set()
            for change in changes:
                if not isinstance(change, dict) or set(change) != {"item_id", "fields"} or change["item_id"] not in ids or change["item_id"] in changed_ids or not isinstance(change["fields"], list) or not change["fields"] or len(change["fields"]) > len(OBSERVATION_FIELDS):
                    _fail("import_comparison_invalid")
                changed_ids.add(change["item_id"])
                for field in change["fields"]:
                    if not isinstance(field, dict) or set(field) != {"field", "before", "after"} or field["field"] not in OBSERVATION_FIELDS or any(v is not None and type(v) not in {str, int} for v in [field["before"], field["after"]]):
                        _fail("import_comparison_invalid")
            if comparison["needs_resolution"] != (bool(changes) or not complete):
                _fail("import_comparison_invalid")
        elif comparison is not None:
            _fail("import_comparison_invalid")
        expected_outcome = "changed" if complete and comparison and comparison["changes"] else "complete" if complete else "partial" if any(r["outcome"] == "read_verified" for r in items) else "failed"
        if value["outcome"] != expected_outcome:
            _fail("import_record_outcome_invalid")
        root_anchor = items[0]["observation"].get("canonical_project_id") if items[0]["observation"] else None
        for item in items[1:]:
            observed = item["observation"]
            if observed and observed.get("canonical_project_id") and observed["canonical_project_id"] != root_anchor:
                _fail("import_record_project_anchor_invalid")
    else:
        if set(value) != {"schema_version", "kind", "workspace_id", "record_id", "captured_at", "request", "import_record_sha256", "target", "source", "record_sha256"}:
            _fail("binding_record_schema_invalid")
        _binding_request(request)
        target, source = value["target"], value["source"]
        if request["binding_id"] != value["record_id"] or not isinstance(target, dict) or set(target) != {"connection_id", "organization", "project", "pbi_id", "task_ids", "observed_items"} or not isinstance(source, dict) or set(source) != {"plan_definition_sha256", "plan_snapshot_sha256", "observation_revision"} or not _digest(value["import_record_sha256"]) or not _digest(source["plan_definition_sha256"]) or not _digest(source["plan_snapshot_sha256"]) or source["observation_revision"] != request["expected_observation_revision"] or type(source["observation_revision"]) is not int:
            _fail("binding_record_identity_invalid")
        _capture_request({"schema_version": 1, "import_id": request["import_id"], **{k: v for k, v in target.items() if k != "observed_items"}})
        if {g["item_id"] for g in request["mapping"]} != set(target["task_ids"]):
            _fail("binding_record_target_invalid")
        observed = target["observed_items"]
        if not isinstance(observed, list) or [r.get("item_id") for r in observed if isinstance(r, dict)] != [target["pbi_id"], *target["task_ids"]]:
            _fail("binding_record_observations_invalid")
        for item in observed:
            if set(item) != {"item_id", "revision", "type", "parent_id"} or not _number(item["item_id"]) or not _number(item["revision"]) or item["type"] != ("Product Backlog Item" if item["item_id"] == target["pbi_id"] else "Task") or item["parent_id"] != (None if item["item_id"] == target["pbi_id"] else target["pbi_id"]):
                _fail("binding_record_observations_invalid")


def _url_identity(url, request):
    if not isinstance(url, str) or any(ord(c) < 33 or unicodedata.category(c) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for c in url):
        _fail("parent_url_invalid")
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != "dev.azure.com" or parts.query or parts.fragment:
        _fail("parent_url_invalid")
    raw = parts.path.split("/")
    path = [unquote(p) for p in raw]
    if any("/" in p or "\\" in p or any(unicodedata.category(c) in {"Cc", "Cf", "Cs"} for c in p) for p in path):
        _fail("parent_url_invalid")
    prefix = path[:-4]
    if path[-4:-1] != ["_apis", "wit", "workItems"] or not re.fullmatch(r"[1-9][0-9]*", path[-1]) or prefix[:2] != ["", request["organization"]] or len(prefix) not in {2, 3}:
        _fail("parent_url_invalid")
    segment = prefix[2] if len(prefix) == 3 else None
    guid = segment.lower() if segment and re.fullmatch(r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}", segment) else None
    if segment is not None and segment != request["project"] and not guid:
        _fail("parent_url_invalid")
    item_id = int(path[-1])
    if not _number(item_id):
        _fail("parent_url_invalid")
    normalized = "https://dev.azure.com/" + quote(request["organization"], safe="") + ("/" + quote(guid or segment, safe="") if segment is not None else "") + "/_apis/wit/workItems/" + str(item_id)
    return guid, item_id, normalized


def _parent(url, request, project_anchor=None, self_guid=None):
    guid, item_id, normalized = _url_identity(url, request)
    if guid and (guid != project_anchor or guid != self_guid):
        _fail("parent_url_invalid")
    return item_id, normalized


OPTIONAL_URL_FIELDS = {"canonical_project_id", "canonical_item_url", "canonical_parent_url"}
OBSERVATION_FIELDS = {"item_id", "revision", "project", "type", "title", "state", "description", "acceptance_criteria", "priority", "parent_id", "parent_relation"} | OPTIONAL_URL_FIELDS


def _digest(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _validate_observation(observation, request, item_id):
    keys = OBSERVATION_FIELDS
    expected_type = "Product Backlog Item" if item_id == request["pbi_id"] else "Task"
    if not isinstance(observation, dict) or set(observation) - OPTIONAL_URL_FIELDS != keys - OPTIONAL_URL_FIELDS or observation["item_id"] != item_id or type(observation["item_id"]) is not int or not _number(observation["revision"]) or observation["project"] != request["project"] or observation["type"] != expected_type or not _text(observation["title"], 512) or not _text(observation["state"]):
        _fail("response_fields_invalid")
    for key in ["description", "acceptance_criteria"]:
        text = observation[key]
        if text is not None and (not isinstance(text, str) or len(text) > 65536 or any(unicodedata.category(c) in {"Cs", "Cf"} or (unicodedata.category(c) == "Cc" and c not in "\r\n\t") for c in text)):
            _fail("response_optional_field_invalid")
    priority = observation["priority"]
    if priority is not None and not _number(priority):
        _fail("response_priority_invalid")
    if item_id != request["pbi_id"] and (type(observation["parent_id"]) is not int or observation["parent_id"] != request["pbi_id"] or observation["parent_relation"] != "System.LinkTypes.Hierarchy-Reverse"):
        _fail("response_parent_invalid")
    if item_id == request["pbi_id"] and (observation["parent_id"] is not None or observation["parent_relation"] is not None):
        _fail("response_root_parent_invalid")
    guid = observation.get("canonical_project_id")
    self_url, parent_url = observation.get("canonical_item_url"), observation.get("canonical_parent_url")
    if guid is not None and (not isinstance(guid, str) or re.fullmatch(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", guid) is None or self_url is None):
        _fail("response_fields_invalid")
    if guid is not None and item_id != request["pbi_id"] and parent_url is None:
        _fail("response_fields_invalid")
    if self_url is not None:
        observed_guid, observed_id, normalized = _url_identity(self_url, request)
        if observed_id != item_id or observed_guid != guid or normalized != self_url:
            _fail("response_fields_invalid")
    if parent_url is not None:
        observed_id, normalized = _parent(parent_url, request, guid, guid)
        if item_id == request["pbi_id"] or observed_id != request["pbi_id"] or normalized != parent_url:
            _fail("response_fields_invalid")


def _project(value, request, item_id, token, encoded, project_anchor=None):
    if not isinstance(value, dict) or any(k in value for k in {"value", "count", "continuationToken", "continuation_token", "nextLink", "@odata.nextLink", "next_link"}) or type(value.get("id")) is not int or value["id"] != item_id or not _number(value.get("rev")):
        _fail("response_identity_invalid")
    if token in json.dumps(value, ensure_ascii=False) or encoded in json.dumps(value, ensure_ascii=False):
        _fail("response_credential_echo_rejected")
    fields = value.get("fields")
    if not isinstance(fields, dict):
        _fail("response_fields_invalid")
    if fields.get("System.TeamProject") != request["project"]:
        _fail("response_fields_invalid")
    guid = self_url = parent_url = None
    if "url" in value:
        guid, self_id, self_url = _url_identity(value["url"], request)
        if self_id != item_id or (item_id != request["pbi_id"] and guid and guid != project_anchor):
            _fail("parent_url_invalid")
    parent_id = parent_relation = None
    if item_id != request["pbi_id"]:
        relations = value.get("relations")
        if not isinstance(relations, list) or len(relations) > MAX_RECORDS:
            _fail("response_relations_invalid")
        parents = [r for r in relations if isinstance(r, dict) and r.get("rel") == "System.LinkTypes.Hierarchy-Reverse"]
        if len(parents) != 1:
            _fail("response_parent_invalid")
        parent_id, parent_url = _parent(parents[0].get("url"), request, project_anchor, guid)
        parent_relation = "System.LinkTypes.Hierarchy-Reverse"
    observation = {"item_id": item_id, "revision": value["rev"], "project": fields.get("System.TeamProject"), "type": fields.get("System.WorkItemType"), "title": fields.get("System.Title"), "state": fields.get("System.State"), "description": fields.get("System.Description"), "acceptance_criteria": fields.get("Microsoft.VSTS.Common.AcceptanceCriteria") if item_id == request["pbi_id"] else None, "priority": fields.get("Microsoft.VSTS.Common.Priority") if item_id == request["pbi_id"] else None, "parent_id": parent_id, "parent_relation": parent_relation}
    observation.update(canonical_project_id=guid, canonical_item_url=self_url, canonical_parent_url=parent_url)
    _validate_observation(observation, request, item_id)
    return observation


def _read(profile, request, item_id, token, project_anchor=None):
    result = {"item_id": item_id, "outcome": "failed", "diagnostic_code": "network_request_failed", "network_attempted": True, "observation": None}
    encoded = base64.b64encode((":" + token).encode("ascii")).decode("ascii")
    target = "https://dev.azure.com/" + quote(profile["organization"], safe="") + "/" + quote(profile["project"], safe="") + "/_apis/wit/workitems/" + str(item_id) + "?" + urlencode({"$expand": "Relations", "api-version": "7.1"})
    api_request = Request(target, headers={"Authorization": "Basic " + encoded, "Accept": "application/json"}, method="GET")
    try:
        with build_opener(ProxyHandler({}), _NoRedirect()).open(api_request, timeout=TIMEOUT_SECONDS) as response:
            if response.geturl() != target:
                _fail("response_destination_mismatch")
            if response.status != 200:
                _fail(_http_code(response.status))
            if response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                _fail("response_not_json")
            if any(k.lower() in {"x-ms-continuationtoken", "x-ms-continuation-token"} for k in response.headers):
                _fail("response_continuation_rejected")
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                _fail("response_size_exceeded")
            value = json.loads(body.decode("utf-8"), object_pairs_hook=_unique)
            observation = _project(value, request, item_id, token, encoded, project_anchor)
    except HTTPError as exc:
        result["diagnostic_code"] = _http_code(exc.code)
        exc.close()
        return result
    except ImportError as exc:
        result["diagnostic_code"] = str(exc)
        return result
    except (URLError, TimeoutError, OSError):
        return result
    except (ValueError, UnicodeError, RecursionError):
        result["diagnostic_code"] = "response_invalid"
        return result
    return {**result, "outcome": "read_verified", "diagnostic_code": "read_verified", "observation": observation}


def _plan(workspace, workspace_id, plan_id, revision, expected, root):
    directory = workspace / "work/plans"
    try:
        directory.resolve().relative_to(workspace)
        paths = list(directory.glob("*.json"))
        if len(paths) > MAX_RECORDS:
            _fail("plan_record_limit_exceeded")
        matches = []
        for path in paths:
            path.resolve().relative_to(directory.resolve())
            value = read_json(path)
            if isinstance(value, dict) and value.get("workspace_id") == workspace_id and value.get("plan_id") == plan_id and value.get("plan_revision") == revision:
                if validate_plan_v2(value, stored=True):
                    _fail("plan_snapshot_invalid")
                if not Path(value["repository_root"]).is_absolute() or Path(value["repository_root"]).resolve() != root:
                    _fail("plan_repository_identity_mismatch")
                matches.append(value)
        if len(matches) != 1:
            _fail("plan_missing_or_ambiguous")
        plan = matches[0]
        if plan["observation_revision"] != expected or type(expected) is not int:
            _fail("plan_observation_revision_conflict")
        return plan
    except (OSError, RuntimeError, UnicodeError, RecursionError):
        _fail("plan_snapshot_unavailable")


def _mapping(plan, receipt, request):
    capture = receipt["request"]
    if {g["item_id"] for g in request["mapping"]} != set(capture["task_ids"]):
        _fail("mapping_selected_set_mismatch")
    refs = [r for r in plan.get("external_refs", []) if r.get("service") == "azure_devops_services" and r.get("organization") == capture["organization"] and r.get("project") == capture["project"] and r.get("item_id") == str(capture["pbi_id"]) and r.get("type_mapping") == "Product Backlog Item"]
    pbis = [p for p in plan["pbis"] if set(p.get("external_ref_ids", [])).intersection(r["external_ref_id"] for r in refs)]
    if len(refs) != 1 or len(pbis) != 1:
        _fail("local_pbi_identity_mismatch")
    steps = {s["step_id"]: s for s in plan["steps"]}
    for group in request["mapping"]:
        if any(i not in steps or pbis[0]["pbi_id"] not in steps[i].get("pbi_ids", []) for i in group["included_step_ids"]):
            _fail("mapping_local_step_mismatch")


def _save(directory, record):
    if len((json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8")) > MAX_BYTES:
        _fail("integration_record_size_exceeded")
    path = _target(directory, record["record_id"])
    if path.exists():
        _fail("integration_output_path_conflict")
    if len(list(directory.glob("*.json"))) >= MAX_RECORDS:
        _fail("integration_record_limit_exceeded")
    _publish(path, record)
    return path


def _summary(record, path, replayed):
    result = {"saved": not replayed, "replayed": replayed, "record_id": record["record_id"], "record_sha256": record["record_sha256"], "output": str(path), "write_permission_verified": False, "remote_write_attempted": False}
    if record["kind"] == "azure_binding":
        return {**result, "binding_saved": not replayed, "network_attempted": False, "outcome": "bound"}
    return {**result, "binding_saved": False, "network_attempted": False if replayed else record["network_attempted"], "captured_network_attempted": record["network_attempted"], "fresh_acquisition": not replayed, "outcome": record["outcome"], "complete": record["complete"], "needs_resolution": record["comparison"]["needs_resolution"] if record["comparison"] else False, "items": [{k: item[k] for k in ["item_id", "outcome", "diagnostic_code"]} for item in record["items"]]}


def capture(root: Path, workspace_id: str, request: dict) -> dict:
    _capture_request(request)
    root = root.resolve()
    workspace = _workspace(root, workspace_id)
    profile = load_connection(root, workspace_id, request["connection_id"])
    ids = [request["pbi_id"], *request["task_ids"]]
    if profile["environment"] != "test" or "read_work_item" not in profile["allowed_operations"] or profile["organization"] != request["organization"] or profile["project"] != request["project"] or not set(ids).issubset(profile["allowed_item_ids"]):
        _fail("test_import_scope_rejected")
    directory = _directory(workspace, "imports", create=True)
    binding = baseline = None
    comparing = "comparison_binding_id" in request
    if comparing:
        row = _load_record(_directory(workspace, "bindings"), request["comparison_binding_id"], workspace_id, "azure_binding")
        if not row:
            _fail("comparison_binding_unavailable")
        binding = row[1]
        baseline_row = _load_record(directory, binding["request"]["import_id"], workspace_id, "azure_import")
        if not baseline_row or baseline_row[1]["record_sha256"] != binding["import_record_sha256"] or not baseline_row[1]["complete"]:
            _fail("comparison_baseline_invalid")
        baseline = baseline_row[1]
        expected_items = [{k: item["observation"][k] for k in ["item_id", "revision", "type", "parent_id"]} for item in baseline["items"]]
        if binding["target"]["observed_items"] != expected_items:
            _fail("comparison_binding_observation_mismatch")
        old = baseline["request"]
        if any(request[k] != old[k] for k in ["connection_id", "organization", "project", "pbi_id", "task_ids"]):
            _fail("comparison_target_mismatch")
    plan_lock = writer_lock(workspace / "work/plans/.records.lock") if comparing else nullcontext()
    with plan_lock, writer_lock(directory / ".imports.lock"):
        existing = _load_record(directory, request["import_id"], workspace_id, "azure_import")
        if existing:
            if existing[1]["request"] != request:
                _fail("import_identity_conflict")
            return _summary(existing[1], existing[0], True)
        if _target(directory, request["import_id"]).exists():
            _fail("integration_output_path_conflict")
        plan = None
        if comparing:
            source = binding["request"]
            plan = _plan(workspace, workspace_id, source["plan_id"], source["plan_revision"], request["expected_observation_revision"], root)
            if _hash(plan_definition(plan)) != binding["source"]["plan_definition_sha256"]:
                _fail("comparison_plan_definition_conflict")
            _mapping(plan, baseline, source)
        token = os.environ.get(profile["auth"]["env_var"])
        available = bool(token) and all(33 <= ord(c) <= 126 for c in token)
        items = []
        stopped = False
        project_anchor = None
        for item_id in ids:
            if not available or stopped:
                item = {"item_id": item_id, "outcome": "not_attempted", "diagnostic_code": "credential_unavailable" if not available else "authentication_failure_stop", "network_attempted": False, "observation": None}
            else:
                item = _read(profile, request, item_id, token, project_anchor)
                stopped = item["diagnostic_code"] == "authentication_rejected"
                if item_id == request["pbi_id"] and item["observation"]:
                    project_anchor = item["observation"].get("canonical_project_id")
            items.append(item)
        if comparing:
            _plan(workspace, workspace_id, source["plan_id"], source["plan_revision"], request["expected_observation_revision"], root)
        complete = all(i["outcome"] == "read_verified" for i in items)
        outcome = "complete" if complete else "partial" if any(i["outcome"] == "read_verified" for i in items) else "failed"
        comparison = None
        if comparing:
            changes = []
            for current, old in zip(items, baseline["items"]):
                if current["observation"] != old["observation"]:
                    before, after = old["observation"], current["observation"]
                    fields = [{"field": k, "before": before.get(k) if before else None, "after": after.get(k) if after else None} for k in sorted(set(before or {}) | set(after or {})) if k not in {"canonical_item_url", "canonical_parent_url"} and (before or {}).get(k) != (after or {}).get(k)]
                    if fields:
                        changes.append({"item_id": current["item_id"], "fields": fields})
            if changes:
                outcome = "changed" if complete else outcome
            comparison = {"binding_id": binding["record_id"], "baseline_import_id": baseline["record_id"], "baseline_record_sha256": baseline["record_sha256"], "local_observation_revision": plan["observation_revision"], "changes": changes, "needs_resolution": bool(changes) or not complete}
        record = _seal({"schema_version": 1, "kind": "azure_import", "workspace_id": workspace_id, "record_id": request["import_id"], "captured_at": datetime.now(timezone.utc).isoformat(), "request": request, "items": items, "complete": complete, "outcome": outcome, "network_attempted": any(i["network_attempted"] for i in items), "comparison": comparison})
        _validate_record(record, workspace_id, "azure_import")
        path = _save(directory, record)
        return _summary(record, path, False)


def bind(root: Path, workspace_id: str, request: dict) -> dict:
    _binding_request(request)
    root = root.resolve()
    workspace = _workspace(root, workspace_id)
    directory = _directory(workspace, "bindings", create=True)
    with writer_lock(workspace / "work/plans/.records.lock"), writer_lock(directory / ".bindings.lock"):
        existing = _load_record(directory, request["binding_id"], workspace_id, "azure_binding")
        if existing:
            if existing[1]["request"] != request:
                _fail("binding_identity_conflict")
            return _summary(existing[1], existing[0], True)
        row = _load_record(_directory(workspace, "imports"), request["import_id"], workspace_id, "azure_import")
        if not row or not row[1]["complete"]:
            _fail("complete_import_required")
        receipt = row[1]
        plan = _plan(workspace, workspace_id, request["plan_id"], request["plan_revision"], request["expected_observation_revision"], root)
        _mapping(plan, receipt, request)
        target = {k: receipt["request"][k] for k in ["connection_id", "organization", "project", "pbi_id", "task_ids"]}
        target["observed_items"] = [{k: item["observation"][k] for k in ["item_id", "revision", "type", "parent_id"]} for item in receipt["items"]]
        source = {"plan_definition_sha256": _hash(plan_definition(plan)), "plan_snapshot_sha256": _hash(plan), "observation_revision": plan["observation_revision"]}
        record = _seal({"schema_version": 1, "kind": "azure_binding", "workspace_id": workspace_id, "record_id": request["binding_id"], "captured_at": datetime.now(timezone.utc).isoformat(), "request": request, "import_record_sha256": receipt["record_sha256"], "target": target, "source": source})
        _validate_record(record, workspace_id, "azure_binding")
        path = _save(directory, record)
        return _summary(record, path, False)


def main(argv=None):
    parser = _SafeParser(description=__doc__)
    parser.add_argument("action", choices=["capture", "bind"])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--input", type=Path, required=True)
    try:
        args = parser.parse_args(argv)
        request = read_json(args.input)
        result = capture(args.root, args.workspace_id, request) if args.action == "capture" else bind(args.root, args.workspace_id, request)
        ok = result["outcome"] in {"complete", "bound"}
    except (ImportError, ProfileError) as exc:
        result, ok = {"saved": False, "outcome": "rejected", "diagnostic_code": str(exc), "write_permission_verified": False, "remote_write_attempted": False}, False
    except (OSError, RuntimeError, ValueError, UnicodeError, RecursionError, TypeError, KeyError):
        result, ok = {"saved": False, "outcome": "rejected", "diagnostic_code": "input_or_storage_unavailable", "write_permission_verified": False, "remote_write_attempted": False}, False
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

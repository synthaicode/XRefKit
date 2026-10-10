"""Workspace-owned Azure Services profiles and a bounded test-only read check."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from xrefkit.work_management import MAX_BYTES, MAX_RECORDS, _publish, _unique, confined_directory, load_workspaces, read_json, writer_lock

FIELDS = {"schema_version", "workspace_id", "connection_id", "service", "organization", "project", "environment", "auth", "allowed_operations", "allowed_item_ids", "description"}
REQUIRED = FIELDS - {"description"}
TIMEOUT_SECONDS = 30


class ProfileError(ValueError):
    """Only fixed diagnostic codes; never carries producer or credential values."""


class _SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise ProfileError("arguments_invalid")


def validate_profile(value: object) -> None:
    if not isinstance(value, dict) or not REQUIRED.issubset(value) or set(value) - FIELDS:
        raise ProfileError("profile_schema_invalid")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["service"] != "azure_devops_services":
        raise ProfileError("profile_version_or_service_invalid")
    for field in ("workspace_id", "connection_id", "organization", "project"):
        item = value[field]
        if not isinstance(item, str) or not item.strip() or len(item) > 128 or any(ord(char) < 32 for char in item):
            raise ProfileError("profile_identity_invalid")
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,63}", value["organization"]) is None:
        raise ProfileError("organization_segment_invalid")
    if value["project"] in {".", ".."} or any(char in "/\\?#" for char in value["project"]):
        raise ProfileError("project_segment_invalid")
    if value["environment"] not in ("test", "production"):
        raise ProfileError("environment_invalid")
    auth = value["auth"]
    if not isinstance(auth, dict) or set(auth) != {"kind", "env_var"} or auth["kind"] != "pat_env" or not isinstance(auth["env_var"], str) or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", auth["env_var"]) is None:
        raise ProfileError("credential_reference_invalid")
    operations = value["allowed_operations"]
    if not isinstance(operations, list) or len(operations) > 1 or any(operation != "read_work_item" for operation in operations):
        raise ProfileError("operation_scope_invalid")
    items = value["allowed_item_ids"]
    if not isinstance(items, list) or len(items) > MAX_RECORDS or any(type(item) is not int or item <= 0 for item in items) or len(set(items)) != len(items):
        raise ProfileError("item_scope_invalid")
    if "description" in value and (not isinstance(value["description"], str) or len(value["description"]) > 4096):
        raise ProfileError("description_invalid")


def _workspace(root: Path, workspace_id: str) -> Path:
    rows = [row for row in load_workspaces(root) if row["workspace"] and row["workspace"]["workspace_id"] == workspace_id]
    if len(rows) != 1 or rows[0]["issues"]:
        raise ProfileError("workspace_missing_or_ambiguous")
    directory = confined_directory(root, rows[0]["workspace"]["workspace_root"])
    if directory is None:
        raise ProfileError("workspace_unavailable")
    return directory


def _directory(root: Path, workspace_id: str, *, create: bool = False) -> Path:
    workspace = _workspace(root, workspace_id)
    directory = workspace / "work/integrations/connections"
    try:
        directory.resolve().relative_to(workspace)
        if create:
            directory.mkdir(parents=True, exist_ok=True)
        return directory
    except (OSError, RuntimeError, ValueError):
        raise ProfileError("connection_directory_unavailable") from None


def _profiles(directory: Path, workspace_id: str) -> list[tuple[Path, dict]]:
    paths = list(directory.glob("*.json"))
    if len(paths) > MAX_RECORDS:
        raise ProfileError("connection_record_limit_exceeded")
    rows = []
    for path in paths:
        try:
            path.resolve().relative_to(directory.resolve())
            if not path.is_file():
                raise ProfileError("profile_file_invalid")
            value = read_json(path)
            validate_profile(value)
            if value["workspace_id"] != workspace_id:
                raise ProfileError("profile_workspace_mismatch")
            rows.append((path, value))
        except ProfileError:
            raise
        except (OSError, ValueError, UnicodeError, RuntimeError, RecursionError):
            raise ProfileError("profile_file_invalid") from None
    ids = [value["connection_id"] for _, value in rows]
    if len(ids) != len(set(ids)):
        raise ProfileError("connection_identity_ambiguous")
    return rows


def register_connection(root: Path, workspace_id: str, profile: dict) -> dict:
    validate_profile(profile)
    if profile["workspace_id"] != workspace_id:
        raise ProfileError("selected_workspace_mismatch")
    directory = _directory(root, workspace_id, create=True)
    identity = workspace_id + "\0" + profile["connection_id"]
    target = directory / (hashlib.sha256(identity.encode()).hexdigest()[:24] + ".json")
    with writer_lock(directory / ".connections.lock"):
        rows = _profiles(directory, workspace_id)
        existing = next(((path, value) for path, value in rows if value["connection_id"] == profile["connection_id"]), None)
        if existing:
            if existing[1] != profile:
                raise ProfileError("connection_identity_conflict")
            return {"saved": False, "replayed": True, "output": str(existing[0]), "network_attempted": False}
        if target.exists():
            raise ProfileError("connection_output_path_conflict")
        if len(rows) >= MAX_RECORDS:
            raise ProfileError("connection_record_limit_exceeded")
        _publish(target, profile)
    return {"saved": True, "replayed": False, "output": str(target), "network_attempted": False}


def load_connection(root: Path, workspace_id: str, connection_id: str) -> dict:
    directory = _directory(root, workspace_id)
    matches = [value for _, value in _profiles(directory, workspace_id) if value["connection_id"] == connection_id]
    if len(matches) != 1:
        raise ProfileError("connection_missing_or_ambiguous")
    return matches[0]


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _http_code(status: int) -> str:
    if status in (301, 302, 303, 307, 308):
        return "redirect_rejected"
    return {401: "authentication_rejected", 403: "access_forbidden", 404: "unavailable_or_not_visible", 429: "rate_limited"}.get(status, "server_failure" if status >= 500 else "http_response_rejected")


def read_check(root: Path, workspace_id: str, connection_id: str, item_id: int) -> dict:
    result = {"configuration_valid": False, "credential_available": None, "network_attempted": False, "read_verified": False, "write_permission_verified": False, "checked_at": datetime.now(timezone.utc).isoformat(), "outcome": "failed"}
    try:
        profile = load_connection(root, workspace_id, connection_id)
    except (ProfileError, OSError, RuntimeError, ValueError):
        result["diagnostic_code"] = "configuration_unavailable"
        return result
    result.update(configuration_valid=True, workspace_id=workspace_id, connection_id=connection_id, organization=profile["organization"], project=profile["project"], environment=profile["environment"], operation="read_work_item")
    if profile["environment"] != "test" or "read_work_item" not in profile["allowed_operations"] or type(item_id) is not int or item_id not in profile["allowed_item_ids"]:
        result["diagnostic_code"] = "test_read_scope_rejected"
        return result
    result["item_id"] = item_id
    token = os.environ.get(profile["auth"]["env_var"])
    if not token or any(ord(char) < 33 or ord(char) > 126 for char in token):
        result["credential_available"] = False
        result["diagnostic_code"] = "credential_unavailable"
        return result
    result["credential_available"] = True
    encoded = base64.b64encode((":" + token).encode("ascii")).decode("ascii")
    target = "https://dev.azure.com/" + quote(profile["organization"], safe="") + "/" + quote(profile["project"], safe="") + "/_apis/wit/workitems/" + str(item_id)
    target += "?" + urlencode({"fields": "System.TeamProject,System.WorkItemType,System.State", "api-version": "7.1"})
    request = Request(target, headers={"Authorization": "Basic " + encoded, "Accept": "application/json"}, method="GET")
    result["network_attempted"] = True
    try:
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            if response.geturl() != target:
                result["diagnostic_code"] = "response_destination_mismatch"
                return result
            if response.status != 200:
                result["diagnostic_code"] = _http_code(response.status)
                result["http_status"] = response.status
                return result
            if response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                result["diagnostic_code"] = "response_not_json"
                return result
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                result["diagnostic_code"] = "response_size_exceeded"
                return result
            value = json.loads(body.decode("utf-8"), object_pairs_hook=_unique)
    except HTTPError as exc:
        result.update(http_status=exc.code, diagnostic_code=_http_code(exc.code))
        exc.close()
        return result
    except (URLError, TimeoutError, OSError):
        result["diagnostic_code"] = "network_request_failed"
        return result
    except (ValueError, UnicodeError, RecursionError):
        result["diagnostic_code"] = "response_invalid"
        return result
    if not isinstance(value, dict) or type(value.get("id")) is not int or value["id"] != item_id or type(value.get("rev")) is not int or value["rev"] <= 0:
        result["diagnostic_code"] = "response_identity_invalid"
        return result
    fields = value.get("fields")
    if not isinstance(fields, dict) or fields.get("System.TeamProject") != profile["project"]:
        result["diagnostic_code"] = "response_project_mismatch"
        return result
    observed = [fields.get("System.WorkItemType"), fields.get("System.State")]
    if any(not isinstance(item, str) or not item.strip() or len(item) > 128 or any(ord(char) < 32 for char in item) or token in item or encoded in item for item in observed):
        result["diagnostic_code"] = "response_fields_invalid"
        return result
    result.update(outcome="read_verified", read_verified=True, diagnostic_code="read_verified", observed_revision=value["rev"], observed_type=observed[0], observed_state=observed[1])
    return result


def main(argv=None) -> int:
    parser = _SafeParser(description="Workspace-owned connection registration and explicit test-only Azure read check")
    parser.add_argument("action", choices=("register", "read-check"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--connection-id")
    parser.add_argument("--item-id", type=int)
    try:
        args = parser.parse_args(argv)
        if args.action == "register":
            if args.input is None:
                raise ProfileError("input_required")
            result = register_connection(args.root, args.workspace_id, read_json(args.input))
            success = True
        else:
            if args.connection_id is None or args.item_id is None:
                raise ProfileError("explicit_connection_and_item_required")
            result = read_check(args.root, args.workspace_id, args.connection_id, args.item_id)
            success = result["read_verified"]
        print(json.dumps({"ok": success, **result}, ensure_ascii=False))
        return 0 if success else 1
    except ProfileError as exc:
        print(json.dumps({"ok": False, "diagnostic_code": str(exc)}))
    except (OSError, ValueError, UnicodeError, RuntimeError, RecursionError):
        print(json.dumps({"ok": False, "diagnostic_code": "local_operation_failed"}))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

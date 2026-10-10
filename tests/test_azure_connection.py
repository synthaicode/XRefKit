import base64
import copy
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from xrefkit.azure_connection import MAX_BYTES, _NoRedirect, load_connection, main, read_check, register_connection, validate_profile
from xrefkit.work_management import register_workspace

CANARY = "canary-PAT-not-a-real-credential-abc123"


class Response:
    def __init__(self, request, body=None, *, content_type="application/json", status=200, url=None):
        self.url = request.full_url if url is None else url
        self.headers = {"Content-Type": content_type}
        self.status = status
        self.body = json.dumps({"id": 10, "rev": 3, "fields": {"System.TeamProject": "AI01-Scrum", "System.WorkItemType": "Product Backlog Item", "System.State": "New"}}).encode() if body is None else body
        self.closed = False

    def geturl(self):
        return self.url

    def read(self, size):
        return self.body[:size]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True


class AzureConnectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        register_workspace(self.root, {"schema_version": 1, "workspace_id": "local", "title": "Local", "workspace_root": "."})
        self.profile = {"schema_version": 1, "workspace_id": "local", "connection_id": "test", "service": "azure_devops_services", "organization": "seijim0pattern01", "project": "AI01-Scrum", "environment": "test", "auth": {"kind": "pat_env", "env_var": "EXPLICIT_TEST_PAT"}, "allowed_operations": ["read_work_item"], "allowed_item_ids": [10]}

    def register(self, profile=None):
        return register_connection(self.root, "local", self.profile if profile is None else profile)

    def check(self):
        return read_check(self.root, "local", "test", 10)

    def test_registration_is_local_immutable_and_no_clobber(self):
        with patch("xrefkit.azure_connection.build_opener") as network:
            first = self.register()
            self.assertTrue(self.register()["replayed"])
            network.assert_not_called()
        before = Path(first["output"]).read_bytes()
        changed = {**self.profile, "project": "other"}
        with self.assertRaises(ValueError):
            self.register(changed)
        self.assertEqual(before, Path(first["output"]).read_bytes())
        other = {**self.profile, "connection_id": "next"}
        target = Path(first["output"]).parent / (hashlib.sha256(b"local\0next").hexdigest()[:24] + ".json")
        target.write_text(json.dumps({**other, "connection_id": "unrelated"}), encoding="utf-8")
        before = target.read_bytes()
        with self.assertRaises(ValueError):
            self.register(other)
        self.assertEqual(before, target.read_bytes())

    def test_strict_schema_scope_types_and_secret_fields(self):
        cases = [{**self.profile, "pat": CANARY}, {**self.profile, "schema_version": True}, {**self.profile, "allowed_item_ids": [True]}, {**self.profile, "allowed_item_ids": [10, 10]}, {**self.profile, "allowed_operations": ["update_work_item"]}, {**self.profile, "auth": {"kind": "pat_env", "env_var": "BAD-NAME"}}, {**self.profile, "project": "../elsewhere"}, {**self.profile, "organization": "example.test/path"}]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError) as error:
                validate_profile(value)
            self.assertNotIn(CANARY, str(error.exception))

    def test_selected_workspace_never_falls_back(self):
        child = self.root / "client"
        child.mkdir()
        register_workspace(self.root, {"schema_version": 1, "workspace_id": "client", "title": "Client", "workspace_root": "client"})
        self.register()
        with self.assertRaises(ValueError):
            load_connection(self.root, "client", "test")
        other = {**self.profile, "workspace_id": "client", "project": "other"}
        register_connection(self.root, "client", other)
        self.assertEqual("other", load_connection(self.root, "client", "test")["project"])
        self.assertEqual("AI01-Scrum", load_connection(self.root, "local", "test")["project"])
        with self.assertRaises(ValueError):
            self.register(other)

    def test_duplicate_malformed_and_oversize_profile_fail_closed(self):
        first = self.register()
        target = Path(first["output"])
        target.with_name("duplicate.json").write_bytes(target.read_bytes())
        with self.assertRaises(ValueError):
            load_connection(self.root, "local", "test")
        target.with_name("duplicate.json").unlink()
        for body in (b'{"secret":"' + CANARY.encode() + b'","secret":"duplicate"}', b"x" * (MAX_BYTES + 1)):
            target.write_bytes(body)
            result = self.check()
            self.assertFalse(result["configuration_valid"])
            self.assertNotIn(CANARY, json.dumps(result))

    def test_scope_checks_happen_before_env_lookup_and_network(self):
        for change in ({"environment": "production"}, {"allowed_operations": []}, {"allowed_item_ids": []}):
            self.profile.update(change)
            saved = self.register()
            with patch("xrefkit.azure_connection.os.environ.get") as env, patch("xrefkit.azure_connection.build_opener") as network:
                result = self.check()
            self.assertEqual("test_read_scope_rejected", result["diagnostic_code"])
            env.assert_not_called()
            network.assert_not_called()
            Path(saved["output"]).unlink()
            self.profile.update(environment="test", allowed_operations=["read_work_item"], allowed_item_ids=[10])

    def test_missing_named_credential_has_no_other_env_fallback(self):
        self.register()
        with patch.dict("os.environ", {"AZURE_DEVOPS_PAT": CANARY}, clear=True), patch("xrefkit.azure_connection.build_opener") as network:
            result = self.check()
        self.assertEqual("credential_unavailable", result["diagnostic_code"])
        self.assertFalse(result["network_attempted"])
        network.assert_not_called()

    def test_matching_read_sends_one_get_and_whitelists_only_safe_fields(self):
        self.register()
        response = None
        def request(req, timeout):
            nonlocal response
            self.assertEqual("GET", req.get_method())
            self.assertEqual(30, timeout)
            self.assertIn("https://dev.azure.com/seijim0pattern01/AI01-Scrum/_apis/wit/workitems/10?", req.full_url)
            self.assertIn("api-version=7.1", req.full_url)
            self.assertEqual("Basic " + base64.b64encode((":" + CANARY).encode()).decode(), req.get_header("Authorization"))
            response = Response(req)
            return response
        with patch.dict("os.environ", {"EXPLICIT_TEST_PAT": CANARY}), patch("xrefkit.azure_connection.build_opener") as builder:
            builder.return_value.open.side_effect = request
            result = self.check()
        builder.return_value.open.assert_called_once()
        self.assertTrue(response.closed)
        self.assertTrue(result["read_verified"])
        self.assertFalse(result["write_permission_verified"])
        self.assertEqual(3, result["observed_revision"])
        self.assertNotIn(CANARY, json.dumps(result))
        self.assertNotIn("Authorization", json.dumps(result))
        self.assertEqual({}, builder.call_args.args[0].proxies)
        self.assertIsInstance(builder.call_args.args[1], _NoRedirect)

    def test_http_failures_and_redirects_are_sanitized_without_retry(self):
        self.register()
        for status, code in ((401, "authentication_rejected"), (403, "access_forbidden"), (404, "unavailable_or_not_visible"), (302, "redirect_rejected"), (307, "redirect_rejected"), (429, "rate_limited"), (503, "server_failure")):
            with self.subTest(status=status), patch.dict("os.environ", {"EXPLICIT_TEST_PAT": CANARY}), patch("xrefkit.azure_connection.build_opener") as builder:
                builder.return_value.open.side_effect = HTTPError("https://evil.test/" + CANARY, status, CANARY, {}, io.BytesIO(CANARY.encode()))
                result = self.check()
            self.assertEqual(code, result["diagnostic_code"])
            self.assertNotIn(CANARY, json.dumps(result))
            builder.return_value.open.assert_called_once()
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.test/"))

    def test_malformed_mismatched_and_secret_echo_responses_are_not_verified(self):
        self.register()
        base = {"id": 10, "rev": 3, "fields": {"System.TeamProject": "AI01-Scrum", "System.WorkItemType": "Product Backlog Item", "System.State": "New"}}
        echo = copy.deepcopy(base)
        echo["fields"]["System.State"] = CANARY
        for body in (b"invalid " + CANARY.encode(), b"x" * (MAX_BYTES + 1), json.dumps({**base, "id": 11}).encode(), json.dumps({**base, "fields": {"System.TeamProject": "other"}}).encode(), json.dumps(echo).encode()):
            with self.subTest(size=len(body)), patch.dict("os.environ", {"EXPLICIT_TEST_PAT": CANARY}), patch("xrefkit.azure_connection.build_opener") as builder:
                builder.return_value.open.side_effect = lambda req, timeout: Response(req, body)
                result = self.check()
            self.assertFalse(result["read_verified"])
            self.assertNotIn(CANARY, json.dumps(result))

    def test_network_timeout_nonjson_and_unexpected_final_url_are_controlled(self):
        self.register()
        for error in (TimeoutError(CANARY), URLError(CANARY)):
            with patch.dict("os.environ", {"EXPLICIT_TEST_PAT": CANARY}), patch("xrefkit.azure_connection.build_opener") as builder:
                builder.return_value.open.side_effect = error
                self.assertEqual("network_request_failed", self.check()["diagnostic_code"])
        for changes, code in (({"content_type": "text/html"}, "response_not_json"), ({"url": "https://evil.test"}, "response_destination_mismatch")):
            with patch.dict("os.environ", {"EXPLICIT_TEST_PAT": CANARY}), patch("xrefkit.azure_connection.build_opener") as builder:
                builder.return_value.open.side_effect = lambda req, timeout: Response(req, **changes)
                self.assertEqual(code, self.check()["diagnostic_code"])

    def test_cli_never_echoes_secret_or_server_error_text(self):
        self.register()
        output = io.StringIO()
        with redirect_stdout(output), patch.dict("os.environ", {"EXPLICIT_TEST_PAT": CANARY}), patch("xrefkit.azure_connection.build_opener") as builder:
            builder.return_value.open.side_effect = HTTPError(CANARY, 401, CANARY, {}, io.BytesIO(CANARY.encode()))
            status = main(["read-check", "--root", str(self.root), "--workspace-id", "local", "--connection-id", "test", "--item-id", "10"])
        self.assertEqual(1, status)
        self.assertNotIn(CANARY, output.getvalue())
        self.assertEqual("authentication_rejected", json.loads(output.getvalue())["diagnostic_code"])

    def test_invalid_cli_arguments_never_echo_values_to_stdout_or_stderr(self):
        arguments = ["read-check", "--root", str(self.root), "--workspace-id", "local", "--connection-id", "test"]
        for suffix in (["--item-id", "10", "--pat", CANARY], ["--item-id", CANARY]):
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = main(arguments + suffix)
            self.assertEqual(1, status)
            self.assertNotIn(CANARY, stdout.getvalue() + stderr.getvalue())
            self.assertEqual("arguments_invalid", json.loads(stdout.getvalue())["diagnostic_code"])

    def test_escaping_connection_directory_is_rejected(self):
        directory = self.root / "work/integrations"
        directory.mkdir(parents=True)
        with tempfile.TemporaryDirectory() as outside:
            try:
                (directory / "connections").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("Windows symlink privileges unavailable")
            with self.assertRaises(ValueError):
                self.register()

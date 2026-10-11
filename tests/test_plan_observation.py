import copy
import json
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

from xrefkit.dashboard import DashboardHandler, DashboardServer, _html_page, build_payload
from xrefkit.plan_observation import (
    MAX_PLAN_BYTES, artifact_path, load_plans, main, plan_panel, validate_plan,
)


class PlanObservationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        (self.root / "work/plans").mkdir(parents=True)
        (self.root / "work/source.md").write_text("Plan source", encoding="utf-8")
        self.plan = {
            "schema_version": 1, "plan_id": "plan", "plan_revision": "v1",
            "repository_root": str(self.root), "title": "A plan", "source": "work/source.md",
            "approval_status": "draft", "approval_evidence": None,
            "steps": [
                {"step_id": "first", "title": "First", "depends_on": [], "outputs": [], "runs": []},
                {"step_id": "second", "title": "Second", "depends_on": ["first"], "outputs": [], "runs": []},
            ],
        }
        self.run = {
            "run_id": "run-1", "flow_id": "flow-1", "work_item_id": "item-1", "node_id": "node-1",
            "path": "work/sessions/run.md", "status": "closed", "closure_status": "done", "quality_status": "pending",
        }

    def write(self, plan=None, name="plan.json"):
        target = self.root / "work/plans" / name
        target.write_text(json.dumps(self.plan if plan is None else plan), encoding="utf-8")
        return target

    def test_unexecuted_plan_has_all_dependencies_and_unrecorded_metadata(self):
        self.write()
        rows = load_plans(self.root, [])
        self.assertEqual([], rows[0]["issues"])
        self.assertEqual(["first"], rows[0]["plan"]["steps"][1]["depends_on"])
        rendered = plan_panel(self.root, rows)
        self.assertIn("未実行（Run対応なし）", rendered)
        self.assertIn("未記録", rendered)
        self.assertIn('role="img"', rendered)
        self.assertNotIn('class="monitor-link"', rendered)

    def test_mapping_exact_correlation_and_status_separation(self):
        self.plan["steps"][0]["runs"] = [{"run_id": "run-1", "flow_id": "flow-1", "work_item_id": "item-1", "node_id": "node-1"}]
        self.write()
        row = load_plans(self.root, [self.run])[0]
        mapping = row["plan"]["steps"][0]["run_observations"][0]
        self.assertTrue(mapping["available"])
        self.assertIn("plan_revision=v1", mapping["monitor_url"])
        self.assertIn("run_id=run-1", mapping["monitor_url"])
        self.assertEqual("pending", mapping["quality_status"])
        self.assertNotIn("status", row["plan"]["steps"][0])
        rendered = plan_panel(self.root, [row])
        self.assertIn("承認状態（記録値）: draft", rendered)
        self.assertIn("品質: pending", rendered)

    def test_missing_invalid_conflicting_and_ambiguous_mappings_never_fallback(self):
        cases = [
            ({"run_id": None}, [], "未記録"),
            ({"run_id": "deleted"}, [self.run], "見つかりません"),
            ({"run_id": "run-1", "flow_id": "different"}, [self.run], "flow_id"),
            ({"run_id": "run-1", "work_item_id": "different"}, [{**self.run, "work_items": [{"item_id": "different"}]}], "work_item_id"),
            ({"run_id": "run-1", "node_id": "different"}, [self.run], "node_id"),
            ({"run_id": "run-1"}, [self.run, {**self.run, "path": "duplicate.md"}], "重複"),
        ]
        for source, runs, reason in cases:
            with self.subTest(reason=reason):
                self.plan["steps"][0]["runs"] = [source]
                self.write()
                mapping = load_plans(self.root, runs)[0]["plan"]["steps"][0]["run_observations"][0]
                self.assertFalse(mapping["available"])
                self.assertIsNone(mapping["monitor_url"])
                self.assertIn(reason, mapping["reason"])

    def test_repository_mismatch_disables_monitor_and_local_artifact_links(self):
        self.plan["repository_root"] = str(self.root.parent)
        self.plan["steps"][0]["runs"] = [{"run_id": "run-1"}]
        self.write()
        rows = load_plans(self.root, [self.run])
        self.assertFalse(rows[0]["plan"]["steps"][0]["run_observations"][0]["available"])
        rendered = plan_panel(self.root, rows)
        self.assertIn("別リポジトリ", rendered)
        self.assertNotIn('/artifact?', rendered)

    def test_revision_mappings_are_not_reused_and_duplicate_identity_is_unavailable(self):
        self.plan["steps"][0]["runs"] = [{"run_id": "run-1"}]
        self.write()
        newer = copy.deepcopy(self.plan)
        newer["plan_revision"] = "v2"
        newer["steps"][0]["runs"] = []
        self.write(newer, "newer.json")
        rows = load_plans(self.root, [self.run])
        by_revision = {row["plan"]["plan_revision"]: row for row in rows}
        self.assertEqual([], by_revision["v2"]["plan"]["steps"][0]["run_observations"])
        self.assertTrue(by_revision["v1"]["plan"]["steps"][0]["run_observations"][0]["available"])
        self.write(self.plan, "duplicate.json")
        rows = load_plans(self.root, [self.run])
        older = [row for row in rows if row["plan"]["plan_revision"] == "v1"]
        self.assertEqual(2, len(older))
        for row in older:
            self.assertIn("重複", row["issues"][0])
            self.assertFalse(row["plan"]["steps"][0]["run_observations"][0]["available"])

    def test_retries_keep_all_runs_and_sort_timezone_aware_time_with_missing_last(self):
        self.plan["steps"][0]["runs"] = [
            {"run_id": "run-2", "recorded_at": "2026-10-10T11:00:00+09:00"},
            {"run_id": "missing-time"},
            {"run_id": "run-1", "recorded_at": "2026-10-10T01:00:00+00:00"},
        ]
        self.write()
        runs = [self.run, {**self.run, "run_id": "run-2", "path": "later.md"}]
        history = load_plans(self.root, runs)[0]["plan"]["steps"][0]["run_observations"]
        self.assertEqual(["run-1", "run-2", "missing-time"], [item["run_id"] for item in history])
        self.assertEqual(3, len(history))

    def test_schema_errors_and_dependency_cycles_are_controlled(self):
        mutations = [
            lambda p: p.update(schema_version=True),
            lambda p: p.update(schema_version=2),
            lambda p: p.update(steps={}),
            lambda p: p.update(extra="unsupported"),
            lambda p: p["steps"][0].update(step_id="second"),
            lambda p: p["steps"][0].update(depends_on=["missing"]),
            lambda p: p["steps"][0].update(depends_on=["second"]),
            lambda p: p["steps"][0].update(outputs="not-list"),
            lambda p: p["steps"][0].update(runs=[42]),
            lambda p: p["steps"][0].update(runs=[{"run_id": "run-1", "recorded_at": "2026-10-10"}]),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                invalid = copy.deepcopy(self.plan)
                mutation(invalid)
                self.write(invalid)
                rows = load_plans(self.root, [])
                self.assertTrue(rows[0]["issues"])
                self.assertIsNone(rows[0]["plan"])
                self.assertIn("計画表示不可", plan_panel(self.root, rows))

    def test_malformed_json_duplicate_keys_and_large_file_do_not_hide_valid_plan(self):
        self.write()
        for text in ("{", '{"schema_version":1,"schema_version":2}', " " * (MAX_PLAN_BYTES + 1)):
            (self.root / "work/plans/broken.json").write_text(text, encoding="utf-8")
            rows = load_plans(self.root, [])
            self.assertEqual(2, len(rows))
            self.assertTrue(rows[0]["issues"])
            self.assertEqual([], rows[1]["issues"])

    def test_empty_directory_and_empty_steps_are_human_readable(self):
        self.assertIn("計画がありません", plan_panel(self.root, load_plans(self.root, [])))
        self.plan["steps"] = []
        self.write()
        self.assertIn("工程がありません", plan_panel(self.root, load_plans(self.root, [])))

    def test_escape_untrusted_labels_and_urls(self):
        self.plan["title"] = '<script>alert("x")</script>'
        self.plan["steps"][0]["step_id"] = 'a"<b>'
        self.plan["steps"][1]["depends_on"] = ['a"<b>']
        self.plan["steps"][0]["runs"] = [{"run_id": "run-1"}]
        self.write()
        rendered = plan_panel(self.root, load_plans(self.root, [self.run]))
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("step_id=a%22%3Cb%3E", rendered)

    def test_serializer_validates_then_atomic_writes_and_refuses_invalid_payload(self):
        source = self.root / "input.json"
        source.write_text(json.dumps(self.plan), encoding="utf-8")
        self.assertEqual(0, main(["--root", str(self.root), "--input", str(source), "--name", "written.json"]))
        target = self.root / "work/plans/written.json"
        self.assertEqual([], validate_plan(json.loads(target.read_text(encoding="utf-8"))))
        before = target.read_bytes()
        source.write_text('{"schema_version":2}', encoding="utf-8")
        self.assertEqual(1, main(["--root", str(self.root), "--input", str(source), "--name", "written.json"]))
        self.assertEqual(before, target.read_bytes())
        self.assertEqual(["written.json"], [path.name for path in target.parent.iterdir()])

    def test_artifact_paths_refuse_escape_absolute_missing_and_directory(self):
        self.assertIsNotNone(artifact_path(self.root, "work/source.md"))
        for value in ("../outside.md", str(self.root / "work/source.md"), "C:\\outside.md", "work", "absent.md", "\\\\server\\share\\file"):
            self.assertIsNone(artifact_path(self.root, value))

    def test_serializer_close_failure_cleans_temp_and_preserves_existing_target(self):
        source = self.root / "input.json"
        source.write_text(json.dumps(self.plan), encoding="utf-8")
        target = self.write(name="written.json")
        before = target.read_bytes()
        real_temporary_file = tempfile.NamedTemporaryFile
        class CloseFailure:
            def __init__(self, *args, **kwargs):
                self.stream = real_temporary_file(*args, **kwargs)
            def __enter__(self):
                return self.stream
            def __exit__(self, *args):
                self.stream.close()
                raise OSError("simulated flush failure")
        with patch("xrefkit.plan_observation.tempfile.NamedTemporaryFile", CloseFailure):
            self.assertEqual(1, main(["--root", str(self.root), "--input", str(source), "--name", "written.json"]))
        self.assertEqual(before, target.read_bytes())
        self.assertEqual(["written.json"], [path.name for path in target.parent.iterdir()])

    def test_artifact_symlink_escape_when_platform_supports_it(self):
        with tempfile.TemporaryDirectory() as outside:
            source = Path(outside) / "secret.txt"
            source.write_text("secret", encoding="utf-8")
            try:
                (self.root / "link.txt").symlink_to(source)
            except OSError:
                self.skipTest("OS does not permit symlink creation")
            self.assertIsNone(artifact_path(self.root, "link.txt"))

    def test_http_artifact_download_is_safe_and_read_only(self):
        (self.root / "work/source.md").write_text("<script>execute()</script>", encoding="utf-8")
        server = DashboardServer(("127.0.0.1", 0), DashboardHandler, root=self.root,
                                 sessions_dir=self.root / "work/sessions", mcp_audit_log=self.root / "absent.jsonl")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with urlopen(base + "/artifact?" + urlencode({"path": "work/source.md"})) as response:
                self.assertEqual("text/plain", response.headers.get_content_type())
                self.assertIn("attachment", response.headers["Content-Disposition"])
                self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])
                self.assertEqual(b"<script>execute()</script>", response.read())
            for query in ("path=../outside.md", "path=work", "path=work/source.md&path=work/source.md"):
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + "/artifact?" + query)
                self.assertEqual(404, error.exception.code)
                error.exception.close()
            self.assertEqual([], list((self.root / "work/plans").iterdir()))
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()

    def test_dashboard_projects_plan_and_has_navigation_guards(self):
        self.write()
        payload = build_payload(self.root, self.root / "work/sessions")
        self.assertEqual(1, len(payload["plans"]))
        rendered = _html_page(payload)
        self.assertIn('data-panel="plans"', rendered)
        self.assertIn('id="refresh-plans"', rendered)
        self.assertIn("originValid", rendered)
        self.assertIn("nextRunId !== requestedRunId", rendered)
        self.assertIn("restoreNavigation();", rendered)
        self.assertIn("requestedRunId !== null", rendered)


if __name__ == "__main__":
    unittest.main()

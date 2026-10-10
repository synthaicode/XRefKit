import copy
import hashlib
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from xrefkit.dashboard import _html_page, build_payload
from xrefkit.plan_observation import load_plans
from xrefkit.work_management import (
    MAX_BYTES, load_workspaces, read_json, record_plan, register_workspace,
    safe_external_url, task_counts, validate_plan_v2,
)


class WorkManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = {"schema_version": 1, "workspace_id": "local", "title": "Local", "workspace_root": "."}
        self.plan = {
            "schema_version": 2, "workspace_id": "local", "repository_root": str(self.root),
            "plan_id": "plan", "plan_revision": "v1", "title": "Work plan", "source": "source.md",
            "report_id": "report-1", "recorded_at": "2026-10-10T10:00:00+09:00",
            "project": {"project_id": "project", "title": "Project"},
            "change": {"change_id": "change", "title": "Change"},
            "baseline": {"baseline_id": "baseline", "code_revision": "old"},
            "stages": [{"stage_id": "design", "title": "Design"}, {"stage_id": "test", "title": "Test"}],
            "steps": [
                {"step_id": "a", "title": "Task A", "stage_id": "design", "dependencies": [], "status": "done", "outputs": [], "runs": [], "pbi_ids": ["p1", "p2"]},
                {"step_id": "b", "title": "Task B", "stage_id": "test", "dependencies": [{"step_id": "a", "kind": "mandatory"}], "status": "done", "revalidation_needed": True, "outputs": [], "runs": [], "pbi_ids": ["p1"]},
            ],
            "pbis": [{"pbi_id": "p1", "title": "PBI 1"}, {"pbi_id": "p2", "title": "PBI 2"}],
            "confirmations": [], "external_refs": [], "initial_task_ids": ["a", "removed"],
        }
        (self.root / "source.md").write_text("baseline source", encoding="utf-8")
        register_workspace(self.root, self.workspace)

    def save(self, plan=None, expected=0):
        return record_plan(self.root, self.plan if plan is None else plan, expected)

    def test_registered_workspace_is_portable_and_confined(self):
        rows = load_workspaces(self.root)
        self.assertEqual([], rows[0]["issues"])
        self.assertEqual(".", rows[0]["workspace"]["workspace_root"])
        self.assertTrue(register_workspace(self.root, self.workspace)["replayed"])
        with self.assertRaises(ValueError):
            register_workspace(self.root, {**self.workspace, "title": "Other"})
        with self.assertRaises(ValueError):
            register_workspace(self.root, {**self.workspace, "workspace_root": "..", "workspace_id": "outside"})

    def test_counts_are_unique_source_recorded_and_revalidation_separate(self):
        counts = task_counts(self.plan)
        self.assertEqual({"current": 2, "completed": 1, "remaining": 1, "initial": 2, "added": 1, "removed": 1, "revalidation": 1, "unrecorded": 0, "unrecognized": 0}, counts)
        self.plan["steps"][0]["runs"] = [{"run_id": "retry-1"}, {"run_id": "retry-2"}]
        self.assertEqual(2, task_counts(self.plan)["current"])
        self.plan["steps"][0]["revalidation_needed"] = None
        self.assertEqual(1, task_counts(self.plan)["completed"])
        self.plan["steps"][0]["status"] = "unrecognized"
        self.assertEqual(1, task_counts(self.plan)["unrecognized"])
        self.plan.pop("initial_task_ids")
        self.assertIsNone(task_counts(self.plan)["initial"])
        self.plan["initial_task_ids"] = []
        self.assertEqual(0, task_counts(self.plan)["initial"])

    def test_target_filename_cannot_overwrite_another_identity(self):
        identity = "local\0plan\0v1"
        directory = self.root / "work/plans"
        directory.mkdir(parents=True)
        target = directory / (hashlib.sha256(identity.encode()).hexdigest()[:24] + ".json")
        unrelated = copy.deepcopy(self.plan)
        unrelated["plan_id"] = "other"
        target.write_text(json.dumps(unrelated), encoding="utf-8")
        before = target.read_bytes()
        with self.assertRaisesRegex(ValueError, "another record"):
            self.save()
        self.assertEqual(before, target.read_bytes())
        other_directory = self.root / "other"
        other_directory.mkdir()
        workspace = {**self.workspace, "workspace_id": "new", "workspace_root": "other"}
        workspace_target = self.root / "work/workspaces" / (hashlib.sha256(b"new").hexdigest()[:24] + ".json")
        workspace_target.write_text(json.dumps({**workspace, "workspace_id": "unrelated"}), encoding="utf-8")
        before = workspace_target.read_bytes()
        with self.assertRaises(ValueError):
            register_workspace(self.root, workspace)
        self.assertEqual(before, workspace_target.read_bytes())

    def test_empty_plan_counts_do_not_infer_effort_or_acceptance(self):
        self.plan["steps"] = []
        counts = task_counts(self.plan)
        self.assertEqual(0, counts["remaining"])
        self.assertEqual(0, counts["completed"])
        self.save()
        rendered = _html_page(build_payload(self.root, self.root / "work/sessions"))
        self.assertIn("受入状態（記録値）: 未記録", rendered)
        self.assertIn("件数は工数・残日数・品質承認ではありません", rendered)

    def test_update_retains_prior_observations_and_exact_retry_does_not_rollback(self):
        first = self.save()
        second = copy.deepcopy(self.plan)
        second["report_id"] = "report-2"
        second["steps"][1]["revalidation_needed"] = False
        second["steps"][1]["candidate_version"] = "new"
        result = self.save(second, 1)
        self.assertEqual(2, result["observation_revision"])
        current = read_json(Path(result["output"]))
        self.assertEqual([], validate_plan_v2(current, stored=True))
        self.assertTrue(current["observation_history"][0]["payload"]["steps"][1]["revalidation_needed"])
        before = Path(result["output"]).read_bytes()
        retry = self.save(self.plan, 0)
        self.assertTrue(retry["replayed"])
        self.assertEqual(2, retry["observation_revision"])
        self.assertEqual(before, Path(first["output"]).read_bytes())
        altered_retry = copy.deepcopy(self.plan)
        altered_retry["steps"][0]["status"] = "pending"
        with self.assertRaisesRegex(ValueError, "report_id"):
            self.save(altered_retry, 2)

    def test_stale_revision_and_topology_conflict_do_not_overwrite_or_reserve_report(self):
        initial = self.save()
        before = Path(initial["output"]).read_bytes()
        update = copy.deepcopy(self.plan)
        update["report_id"] = "new-report"
        with self.assertRaisesRegex(ValueError, "stale"):
            self.save(update, 0)
        update["steps"][0]["title"] = "Changed topology"
        with self.assertRaisesRegex(ValueError, "definition"):
            self.save(update, 1)
        self.assertEqual(before, Path(initial["output"]).read_bytes())
        update["steps"][0]["title"] = "Task A"
        self.assertEqual(2, self.save(update, 1)["observation_revision"])

    def test_new_plan_revision_preserves_previous_and_baseline_bytes(self):
        first = self.save()
        baseline = (self.root / "source.md").read_bytes()
        next_plan = copy.deepcopy(self.plan)
        next_plan.update(plan_revision="v2", previous_plan_revision="v1", report_id="v2-first")
        next_plan["steps"][0]["title"] = "Scope changed"
        second = self.save(next_plan, 0)
        self.assertNotEqual(first["output"], second["output"])
        self.assertTrue(Path(first["output"]).is_file())
        self.assertEqual(baseline, (self.root / "source.md").read_bytes())

    def test_two_concurrent_writers_same_expected_revision_have_one_winner(self):
        first = self.save()
        barrier = threading.Barrier(2)
        def publish(number):
            update = copy.deepcopy(self.plan)
            update["report_id"] = f"concurrent-{number}"
            update["steps"][0]["status"] = "pending" if number == 1 else "in_progress"
            barrier.wait()
            try:
                return self.save(update, 1)
            except (OSError, ValueError) as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(publish, [1, 2]))
        self.assertEqual(1, sum(isinstance(result, dict) for result in results))
        current = read_json(Path(first["output"]))
        self.assertEqual(2, current["observation_revision"])
        self.assertEqual(1, len(current["observation_history"]))

    def test_interrupted_publication_preserves_snapshot_cleans_temporary_and_retries(self):
        first = self.save()
        before = Path(first["output"]).read_bytes()
        update = copy.deepcopy(self.plan)
        update["report_id"] = "retry-after-failure"
        with patch("xrefkit.work_management.os.replace", side_effect=OSError("publish failed")):
            with self.assertRaises(OSError):
                self.save(update, 1)
        self.assertEqual(before, Path(first["output"]).read_bytes())
        self.assertEqual([Path(first["output"]).name], [path.name for path in Path(first["output"]).parent.iterdir()])
        self.assertEqual(2, self.save(update, 1)["observation_revision"])

    def test_stale_lock_is_explicit_refusal(self):
        first = self.save()
        lock = Path(first["output"]).parent / ".records.lock"
        lock.write_text("stale", encoding="utf-8")
        update = copy.deepcopy(self.plan)
        update["report_id"] = "locked"
        with self.assertRaises(FileExistsError):
            self.save(update, 1)
        self.assertEqual("stale", lock.read_text(encoding="utf-8"))

    def test_corrupted_history_and_huge_counter_are_controlled(self):
        result = self.save()
        snapshot = read_json(Path(result["output"]))
        snapshot["observation_revision"] = 10 ** 20
        self.assertTrue(validate_plan_v2(snapshot, stored=True))
        snapshot["observation_revision"] = 2
        snapshot["observation_history"] = [{"observation_revision": 1, "report_id": "bogus", "report_sha256": "wrong", "payload": {}}]
        self.assertTrue(validate_plan_v2(snapshot, stored=True))

    def test_missing_null_writer_fields_are_rejected_by_stored_reader(self):
        result = self.save()
        path = Path(result["output"])
        original = read_json(path)
        for field in ("observation_revision", "report_sha256", "observation_history"):
            for remove in (False, True):
                with self.subTest(field=field, remove=remove):
                    invalid = copy.deepcopy(original)
                    if remove:
                        invalid.pop(field)
                    else:
                        invalid[field] = None
                    path.write_text(json.dumps(invalid), encoding="utf-8")
                    rows = load_plans(self.root, [], workspace_id="local")
                    self.assertTrue(rows[0]["issues"])
                    self.assertIsNone(rows[0]["plan"])

    def test_null_optional_arrays_and_malformed_identity_never_crash(self):
        mutations = [
            lambda p: p["steps"][0].update(stage_id=[]),
            lambda p: p["steps"][0].update(dependencies=[{"kind": [], "step_id": []}]),
            lambda p: p["steps"][0].update(validation_records=None),
            lambda p: p["steps"][0].update(artifact_refs=None),
            lambda p: p["steps"][0].update(pbi_ids=None),
            lambda p: p["baseline"].update(artifacts=None),
            lambda p: p.update(observation_history=None),
            lambda p: p.update(confirmations=[{"confirmation_id": "c", "question": "Q", "step_ids": None}]),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                invalid = copy.deepcopy(self.plan)
                mutation(invalid)
                self.assertTrue(validate_plan_v2(invalid))
                with self.assertRaises(ValueError):
                    self.save(invalid)

    def test_dangling_pbi_task_stage_and_cycles_reject(self):
        for mutation in (
            lambda p: p["steps"][0].update(pbi_ids=["missing"]),
            lambda p: p["steps"][0].update(stage_id="missing"),
            lambda p: p["steps"][0].update(dependencies=[{"step_id": "b", "kind": "mandatory"}]),
            lambda p: p.update(confirmations=[{"confirmation_id": "c", "question": "Q", "step_ids": ["missing"]}]),
        ):
            invalid = copy.deepcopy(self.plan)
            mutation(invalid)
            self.assertTrue(validate_plan_v2(invalid))

    def test_confirmation_answer_and_application_remain_distinct_and_judgment_referenced(self):
        self.plan["confirmations"] = [{"confirmation_id": "c", "question": "Check source", "step_ids": ["b"], "answer": {"text": "Answer", "responder": "User"}, "judgment_refs": ["work/judgments/existing.md"]}]
        self.save()
        rendered = _html_page(build_payload(self.root, self.root / "work/sessions"))
        self.assertIn("回答記録あり・反映未記録", rendered)
        self.assertIn("work/judgments/existing.md", rendered)
        self.assertNotIn("ADR files", rendered)

    def test_typed_optional_external_and_version_evidence_are_not_auto_acceptance(self):
        self.plan["external_refs"] = [{"external_ref_id": "ext", "service": "Azure Boards", "item_id": "123", "url": "https://dev.azure.com/org/project/_workitems/edit/123", "sync_status": "unrecorded"}]
        self.plan["steps"][1]["dependencies"] = [{"kind": "optional", "step_id": "a"}, {"kind": "external", "external_ref_id": "ext"}]
        self.plan["steps"][0].update(candidate_version="new", validation_records=[{"validation_id": "old-test", "target_version": "old", "result": "pass", "environment": "test", "evidence_refs": []}])
        self.save()
        rendered = _html_page(build_payload(self.root, self.root / "work/sessions"))
        self.assertIn('stroke-dasharray="5 4"', rendered)
        self.assertIn("別対象版の記録（有効性を引き継ぎません）", rendered)
        self.assertIn("記録された外部参照・未照合", rendered)
        self.assertIn("受入状態（記録値）: 未記録", rendered)

    def test_script_urls_and_unknown_keys_are_rejected_and_strings_are_escaped(self):
        for url in ("javascript:alert(1)", "https://user:password@example.com/", "file:///C:/secret", "https://host/\nheader"):
            self.assertFalse(safe_external_url(url))
        invalid = copy.deepcopy(self.plan)
        invalid["external_refs"] = [{"external_ref_id": "ext", "service": "Boards", "item_id": "1", "url": "javascript:alert(1)"}]
        self.assertTrue(validate_plan_v2(invalid))
        self.plan["title"] = "<script>inert</script>"
        self.save()
        rendered = _html_page(build_payload(self.root, self.root / "work/sessions"))
        self.assertIn("&lt;script&gt;inert&lt;/script&gt;", rendered)
        self.assertNotIn("<script>inert", rendered)

    def test_same_run_id_in_two_workspaces_links_only_exact_scope(self):
        for workspace_id, directory in (("one", "changes/one"), ("two", "changes/two")):
            workspace_root = self.root / directory
            (workspace_root / "work/sessions").mkdir(parents=True)
            (workspace_root / "work/sessions/run.md").write_text("# Skill Run Log\n- run_id: `same`\n- skill_id: `sample`\n- maturity: `trial`\n", encoding="utf-8")
            register_workspace(self.root, {"schema_version": 1, "workspace_id": workspace_id, "title": workspace_id, "workspace_root": directory})
            plan = copy.deepcopy(self.plan)
            plan["workspace_id"] = workspace_id
            plan["steps"][0]["runs"] = [{"run_id": "same"}]
            self.save(plan)
        payload = build_payload(self.root, self.root / "work/sessions")
        scoped = [row for row in payload["plans"] if row["plan"] and row["plan"]["workspace_id"] in {"one", "two"}]
        self.assertEqual(2, len(scoped))
        for row in scoped:
            mapping = row["plan"]["steps"][0]["run_observations"][0]
            self.assertTrue(mapping["available"])
            self.assertIn("workspace_id=" + row["plan"]["workspace_id"], mapping["monitor_url"])
            self.assertIn(row["plan"]["workspace_id"], mapping["run_path"])

    def test_workspace_session_overlap_is_visible_not_order_dependent(self):
        nested = self.root / "work/sessions/nested"
        nested.mkdir(parents=True)
        with self.assertRaises(ValueError):
            register_workspace(self.root, {"schema_version": 1, "workspace_id": "nested", "title": "Nested", "workspace_root": "work/sessions/nested"})
        self.assertEqual(1, len(load_workspaces(self.root)))
        self.assertEqual([], load_workspaces(self.root)[0]["issues"])

    def test_workspace_child_symlink_escape_when_supported(self):
        nested = self.root / "changes/nested"
        (nested / "work").mkdir(parents=True)
        with tempfile.TemporaryDirectory() as outside:
            try:
                (nested / "work/sessions").symlink_to(Path(outside), target_is_directory=True)
            except OSError:
                self.skipTest("OS does not permit symlink creation")
            register_workspace(self.root, {"schema_version": 1, "workspace_id": "nested", "title": "Nested", "workspace_root": "changes/nested"})
            payload = build_payload(self.root, self.root / "work/sessions")
            nested_row = next(row for row in payload["workspaces"] if row["workspace"] and row["workspace"]["workspace_id"] == "nested")
            self.assertTrue(nested_row["issues"])

    def test_snapshot_size_limit_refuses_and_retains_old_bytes(self):
        first = self.save()
        before = Path(first["output"]).read_bytes()
        update = copy.deepcopy(self.plan)
        update["report_id"] = "oversized"
        update["steps"][0]["status_evidence"] = "x" * MAX_BYTES
        with self.assertRaises(ValueError):
            self.save(update, 1)
        self.assertEqual(before, Path(first["output"]).read_bytes())


if __name__ == "__main__":
    unittest.main()

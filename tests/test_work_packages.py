import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from xrefkit.work_management import (
    package_task_counts, plan_definition, read_json, record_plan,
    register_workspace, validate_plan_v2,
)


class WorkPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "source.md").write_text("approved scope", encoding="utf-8")
        register_workspace(self.root, {"schema_version": 1, "workspace_id": "local", "title": "Local", "workspace_root": "."})
        self.plan = {
            "schema_version": 2, "workspace_id": "local", "repository_root": str(self.root),
            "plan_id": "p", "plan_revision": "v1", "title": "Plan", "source": "source.md", "report_id": "r1",
            "project": {"project_id": "p", "title": "Project"}, "change": {"change_id": "c", "title": "Change"}, "baseline": {"baseline_id": "b"},
            "stages": [{"stage_id": "design", "title": "Design"}, {"stage_id": "test", "title": "Test"}],
            "steps": [{"step_id": "a", "title": "A", "stage_id": "design", "dependencies": [], "status": "done", "outputs": [], "runs": []},
                      {"step_id": "b", "title": "B", "stage_id": "test", "dependencies": [{"step_id": "a", "kind": "mandatory"}], "status": "done", "outputs": [], "runs": []},
                      {"step_id": "c", "title": "C", "stage_id": "test", "dependencies": [{"step_id": "b", "kind": "optional"}], "status": "pending", "outputs": [], "runs": []}],
            "pbis": [{"pbi_id": "pbi", "title": "Outcome"}], "confirmations": [], "external_refs": [],
            "work_packages": [self.package("one", ["a", "b"]), self.package("two", ["c"], ["one"])],
        }

    def package(self, identity, members, dependencies=None):
        return {"work_package_id": identity, "title": identity, "pbi_id": "pbi", "purpose": "One purpose", "expected_output": "Output", "step_ids": members,
                "completion_criterion": "Evidence reviewed", "depends_on": dependencies or [], "review_owner": "Reviewer"}

    def verified(self):
        return {"status": "verified", "reviewer": "Reviewer", "recorded_at": "2026-10-11T09:00:00+09:00", "evidence_refs": ["source.md"]}

    def test_legacy_definition_fingerprint_is_unchanged_and_packages_optional(self):
        legacy = copy.deepcopy(self.plan)
        legacy.pop("work_packages")
        original_static = {key: legacy[key] for key in ("workspace_id", "repository_root", "plan_id", "plan_revision", "title", "source", "project", "change", "baseline", "stages")}
        original_static["steps"] = [{key: value for key, value in step.items() if key in {"step_id", "title", "stage_id", "dependencies", "completion_criterion", "planned_skill", "pbi_ids", "predecessor_step_ids"}} for step in legacy["steps"]]
        original_static["pbis"] = legacy["pbis"]
        digest = lambda obj: hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest(original_static), digest(plan_definition(legacy)))
        self.assertEqual([], validate_plan_v2(legacy))
        self.assertEqual("generated", record_plan(self.root, legacy, 0)["projection"]["status"])

    def test_strict_package_boundaries(self):
        edits = [
            lambda p: p.update(work_packages=None),
            lambda p: p.update(work_packages=[]),
            lambda p: p["work_packages"][0].update(step_ids=[]),
            lambda p: p["work_packages"][0].update(step_ids=["a", "a", "b"]),
            lambda p: p["work_packages"][1].update(step_ids=["b", "c"]),
            lambda p: p["work_packages"][1].update(step_ids=["missing"]),
            lambda p: p["work_packages"][0].update(pbi_id="missing"),
            lambda p: p["work_packages"][0].update(pbi_id=[]),
            lambda p: p["work_packages"][0].update(extra="silent"),
            lambda p: p["work_packages"][0].update(review_owner=None),
            lambda p: p["work_packages"][1].update(work_package_id="one"),
            lambda p: p["work_packages"][0].update(depends_on=["two"]),
            lambda p: p["work_packages"][0].update(depends_on=["one"]),
            lambda p: p["work_packages"][1].update(depends_on=["one", "one"]),
            lambda p: p["work_packages"][1].update(depends_on=["missing"]),
            lambda p: p["work_packages"][0].update(verification=None),
            lambda p: p["work_packages"][0].update(verification={"status": []}),
            lambda p: p["work_packages"][0].update(verification={"status": "verified"}),
            lambda p: p["work_packages"][0].update(verification={**self.verified(), "reviewer": "Other"}),
            lambda p: p["work_packages"][0].update(verification={**self.verified(), "recorded_at": "2026-10-11"}),
            lambda p: p["steps"][0].update(pbi_ids=["other"]),
        ]
        for index, edit in enumerate(edits):
            with self.subTest(index=index):
                plan = copy.deepcopy(self.plan)
                edit(plan)
                self.assertTrue(validate_plan_v2(plan))
                with self.assertRaises(ValueError):
                    record_plan(self.root, plan, 0)
        empty = copy.deepcopy(self.plan)
        empty.update(steps=[], work_packages=[])
        self.assertEqual([], validate_plan_v2(empty))

    def test_verified_observations_regenerate_without_revision_change_and_replay_current(self):
        first = record_plan(self.root, self.plan, 0)
        output = Path(first["projection"]["output"])
        self.assertIn("所属Taskすべて完了: はい ／ 成果確認（記録値）: 未記録", output.read_text(encoding="utf-8"))
        update = copy.deepcopy(self.plan)
        update["report_id"] = "r2"
        update["work_packages"][0]["verification"] = self.verified()
        self.assertEqual(plan_definition(self.plan), plan_definition(update))
        second = record_plan(self.root, update, 1)
        self.assertEqual(2, second["observation_revision"])
        self.assertIn("成果確認（記録値）: 確認済み", output.read_text(encoding="utf-8"))
        update["report_id"] = "r3"
        update["steps"][1]["revalidation_needed"] = True
        record_plan(self.root, update, 2)
        self.assertEqual(1, package_task_counts(update, update["work_packages"][0])["remaining"])
        self.assertIn("現在の成果確認済みとは読み替えません", output.read_text(encoding="utf-8"))
        replay = record_plan(self.root, self.plan, 0)
        self.assertTrue(replay["replayed"])
        self.assertIn("観測版: 3", output.read_text(encoding="utf-8"))
        snapshot = read_json(Path(first["output"]))
        self.assertEqual("verified", snapshot["work_packages"][0]["verification"]["status"])
        self.assertEqual(2, len(snapshot["observation_history"]))

    def test_package_structure_requires_new_plan_revision(self):
        first = record_plan(self.root, self.plan, 0)
        before = Path(first["output"]).read_bytes()
        for field, value in (("title", "Changed"), ("review_owner", "Other"), ("completion_criterion", "Changed"), ("depends_on", [])):
            update = copy.deepcopy(self.plan)
            update["report_id"] = "r2"
            update["work_packages"][1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                record_plan(self.root, update, 1)
            self.assertEqual(before, Path(first["output"]).read_bytes())
        update["plan_revision"] = "v2"
        self.assertEqual("generated", record_plan(self.root, update, 0)["projection"]["status"])

    def test_groups_span_stages_and_diagrams_do_not_invent_dependencies(self):
        self.plan["work_packages"][0]["title"] = 'Result"\nend\nclick w0 "javascript:bad"'
        result = record_plan(self.root, self.plan, 0)
        body = Path(result["projection"]["output"]).read_text(encoding="utf-8")
        self.assertIn("p0 --- w0", body)
        self.assertIn('w0 --- m0["a"]', body)
        self.assertIn('w0 --- m1["b"]', body)
        self.assertIn("w0 --> w1", body)
        self.assertIn("n0 -->|必須| n1", body)
        self.assertIn("n1 -.->|任意| n2", body)
        self.assertNotIn("n0 -->|必須| n2", body)
        self.assertNotIn('\nclick w0', body)
        self.assertIn("#34;", body)
        self.assertIn("### Design", body)
        self.assertIn("### Test", body)
        self.assertIn("予定（現行） **3**", body)


if __name__ == "__main__":
    unittest.main()

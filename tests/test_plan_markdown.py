import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from xrefkit.plan_markdown import monitor_base, regenerate
from xrefkit.work_management import record_plan, register_workspace, writer_lock


class PlanMarkdownTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        register_workspace(self.root, {"schema_version": 1, "workspace_id": "local", "title": "Local", "workspace_root": "."})
        (self.root / "source 日本.md").write_text("source", encoding="utf-8")
        sessions = self.root / "work/sessions"
        sessions.mkdir(parents=True)
        (sessions / "run 日本.md").write_text("# Skill Run Log\n\n- run_id: `run-1`\n- flow_id: `flow-1`\n- skill_id: `python_implementation_flow`\n", encoding="utf-8")
        self.plan = {
            "schema_version": 2, "workspace_id": "local", "repository_root": str(self.root),
            "plan_id": "p", "plan_revision": "v1", "title": "日本語の計画", "source": "source 日本.md", "report_id": "r1",
            "project": {"project_id": "p", "title": "Project"}, "change": {"change_id": "c", "title": "Change"}, "baseline": {"baseline_id": "b"},
            "stages": [{"stage_id": "s", "title": "設計"}],
            "steps": [{"step_id": "a", "title": "作業A", "stage_id": "s", "dependencies": [], "status": "done", "outputs": ["source 日本.md"], "runs": [{"run_id": "run-1", "flow_id": "flow-1"}]},
                      {"step_id": "b", "title": "作業B", "stage_id": "s", "dependencies": [{"step_id": "a", "kind": "optional"}], "status": "done", "revalidation_needed": True, "outputs": [], "runs": []}],
            "pbis": [], "confirmations": [], "external_refs": [],
        }

    def save(self, plan=None, expected=0, **kwargs):
        return record_plan(self.root, self.plan if plan is None else plan, expected, **kwargs)

    def body(self, result):
        return Path(result["projection"]["output"]).read_text(encoding="utf-8")

    def test_default_projection_exact_counts_and_portable_links(self):
        result = self.save()
        self.assertEqual("generated", result["projection"]["status"])
        body = self.body(result)
        self.assertIn("現行） **2** ／ 記録上の完了 **1** ／ 残り **1**", body)
        self.assertIn("[作業A](#task-0)", body)
        self.assertIn("../sessions/run%20%E6%97%A5%E6%9C%AC.md", body)
        self.assertIn("../../source%20%E6%97%A5%E6%9C%AC.md", body)
        self.assertIn("n0 -.->|任意| n1", body)
        self.assertNotIn("localhost", body)
        self.assertNotIn("補助モニタ", body)
        self.assertIn("- 観測版: 1", body)
        self.assertIn("- 記録日時: 未記録", body)

    def test_explicit_monitor_base_preserves_deployment_path_and_exact_origin(self):
        result = self.save(monitor_base="https://example.test/dashboard")
        body = self.body(result)
        self.assertIn("https://example.test/dashboard/?panel=closure&workspace_id=local&plan_id=p&plan_revision=v1&step_id=a&run_id=run-1", body)
        for base in ("javascript:alert(1)", "https://user:pass@example.test", "https://example.test/?x=1", "https://example.test/#x"):
            with self.subTest(base=base), self.assertRaises(ValueError):
                monitor_base(base)
        encoded = monitor_base("https://example.test/a [x](https://other.test/)")
        self.assertNotIn(" ", encoded)
        self.assertNotIn("(", encoded)
        self.assertNotIn(")", encoded)
        self.assertIn("%20", encoded)
        self.assertEqual("https://[::1]/", monitor_base("https://[::1]"))

    def test_all_evidence_and_artifact_records_are_ordinary_links(self):
        self.plan["steps"][0].update(status_evidence="source 日本.md", artifact_refs=[{"path": "source 日本.md", "revision": "old"}], validation_records=[{"validation_id": "v", "target_version": "old", "evidence_refs": ["source 日本.md"]}])
        self.plan["baseline"]["artifacts"] = [{"path": "source 日本.md", "revision": "base"}]
        self.plan["confirmations"] = [{"confirmation_id": "c", "question": "Question", "answer": {"text": "Answer", "evidence_refs": ["source 日本.md"]}, "application": {"target_refs": ["source 日本.md"], "evidence_refs": ["source 日本.md"]}}]
        body = self.body(self.save())
        self.assertGreaterEqual(body.count("../../source%20%E6%97%A5%E6%9C%AC.md"), 8)
        self.assertIn("状態の証跡", body)
        self.assertIn("版: old", body)
        self.assertIn("異なる版", body)

    def test_replay_and_manual_regenerate_use_current_snapshot(self):
        first = self.save()
        update = copy.deepcopy(self.plan)
        update["report_id"] = "r2"
        update["steps"][1]["revalidation_needed"] = False
        second = self.save(update, 1)
        target = Path(second["projection"]["output"])
        target.unlink()
        replay = self.save()
        self.assertTrue(replay["replayed"])
        self.assertIn("- 観測版: 2", self.body(replay))
        before = Path(first["output"]).read_bytes()
        result = regenerate(self.root, Path(first["output"]))
        self.assertEqual("generated", result["projection"]["status"])
        self.assertEqual(before, Path(first["output"]).read_bytes())

    def test_human_and_edited_generated_markdown_are_preserved(self):
        result = self.save()
        target = Path(result["projection"]["output"])
        for contents in ("# Human document\n", target.read_text(encoding="utf-8") + "human edit\n"):
            target.write_text(contents, encoding="utf-8")
            replay = self.save()
            self.assertEqual("failed", replay["projection"]["status"])
            self.assertTrue(replay["replayed"])
            self.assertEqual(contents, target.read_text(encoding="utf-8"))

    def test_projection_failure_keeps_committed_source_and_old_complete_view(self):
        first = self.save()
        target = Path(first["projection"]["output"])
        before = target.read_bytes()
        update = copy.deepcopy(self.plan)
        update["report_id"] = "r2"
        import os
        replace = os.replace
        def fail_markdown(source, destination):
            if Path(destination).suffix == ".md":
                raise OSError("derived write failed")
            return replace(source, destination)
        with patch("xrefkit.plan_markdown.os.replace", side_effect=fail_markdown):
            result = self.save(update, 1)
        self.assertTrue(result["saved"])
        self.assertEqual("failed", result["projection"]["status"])
        self.assertEqual(2, json.loads(Path(result["output"]).read_text(encoding="utf-8"))["observation_revision"])
        self.assertEqual(before, target.read_bytes())
        self.assertEqual({target.name, Path(result["output"]).name}, {path.name for path in target.parent.iterdir()})
        self.assertEqual("generated", self.save(update, 1)["projection"]["status"])

    def test_rejected_source_does_not_touch_projection(self):
        first = self.save()
        target = Path(first["projection"]["output"])
        before = target.read_bytes()
        update = copy.deepcopy(self.plan)
        update["report_id"] = "r2"
        with self.assertRaises(ValueError):
            self.save(update, 0)
        self.assertEqual(before, target.read_bytes())

    def test_adversarial_labels_cannot_escape_mermaid_or_markdown(self):
        hostile = '\"]\n```mermaid\nclick n0 \"javascript:alert(1)\"\n%%{init: {}}%%<script>|[x](evil)'
        self.plan["steps"][0]["title"] = hostile
        self.plan["stages"][0]["title"] = hostile
        result = self.save()
        body = self.body(result)
        self.assertEqual(1, body.count("```mermaid"))
        self.assertEqual(2, body.count("```"))
        self.assertNotIn("<script>", body)
        self.assertNotIn("\nclick n0", body)
        self.assertNotIn("%%{init", body)

    def test_all_typed_edges_and_external_nodes_are_rendered_without_added_tasks(self):
        self.plan["external_refs"] = [{"external_ref_id": "e", "service": "Azure", "item_id": "1", "url": "https://example.test/item"}]
        self.plan["steps"][1]["dependencies"] += [{"step_id": "a", "kind": "mandatory"}, {"external_ref_id": "e", "kind": "external"}]
        result = self.save()
        body = self.body(result)
        self.assertIn("n0 -->|必須| n1", body)
        self.assertIn("e0 -.->|外部| n1", body)
        self.assertIn("現行） **2**", body)

    def test_external_destination_preserves_authority_query_and_fragment(self):
        self.plan["external_refs"] = [{"external_ref_id": "e", "service": "Azure", "item_id": "1", "url": "https://[::1]/item(a)?q=x(y)#section"}]
        body = self.body(self.save())
        self.assertIn("[外部参照](https://[::1]/item%28a%29?q=x%28y%29#section)", body)
        self.plan["external_refs"][0]["url"] = "https://example.test/item#section"
        self.plan["report_id"] = "r2"
        self.assertIn("https://example.test/item#section", self.body(self.save(expected=1)))

    def test_duplicate_or_tuple_mismatched_runs_do_not_produce_local_link(self):
        self.plan["steps"][0]["runs"][0]["flow_id"] = "other"
        result = self.save()
        self.assertNotIn("../sessions/run%20", self.body(result))
        self.assertIn("flow", self.body(result))
        self.plan["steps"][0]["runs"][0]["flow_id"] = "flow-1"
        self.plan["report_id"] = "r2"
        source = self.root / "work/sessions/run 日本.md"
        source.with_name("duplicate.md").write_bytes(source.read_bytes())
        self.assertNotIn("../sessions/run%20", self.body(self.save(expected=1)))

    def test_empty_projection_is_human_readable(self):
        self.plan["steps"] = []
        self.plan["stages"] = []
        self.assertIn("作業の記録なし", self.body(self.save()))

    def test_manual_render_uses_writer_lock_and_never_modifies_current_view_on_conflict(self):
        result = self.save()
        target = Path(result["projection"]["output"])
        before = target.read_bytes()
        with writer_lock(target.parent / ".records.lock"):
            with self.assertRaises(FileExistsError):
                regenerate(self.root, Path(result["output"]))
        self.assertEqual(before, target.read_bytes())

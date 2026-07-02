import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fm.flowengine import apply_answer, apply_label, initial_position, run_flow

FLOW_YAML = """\
flow_id: FLOW-STATE-TEST
entry: work

global_handback:
  uncertainty:
    to: coordinator
    ask: "resolve blocking unknown"
    resume:
      resolved: work
      rejected: ABORT

steps:
  work:
    facets: [worker_persona]
    permission: { edit: false }
    capability: CAP-DSN-004
    skill: test_flow
    on:
      Go: review
      _invalid_or_absent: ABORT
  review:
    facets: [reviewer_persona]
    permission: { edit: false }
    capability: CAP-QA-001
    on:
      Go: COMPLETE
      Recycle: work
      Hold:
        handback:
          to: coordinator
          reason: blocked
          ask: "review blocked"
          resume:
            resolved: review
            rejected: ABORT
      _invalid_or_absent: ABORT
"""

LOAD_GATE = "## Skill Load Gate\n\n- status: `opened_by_fm_skill_run`\n"


def _closed_log(status: str) -> str:
    return (
        "# Skill Run Log\n\n"
        f"{LOAD_GATE}\n"
        "## Phase Events\n\n"
        f"- 2026-07-03 `closure` -> `{status}` role=`closure_gate`\n"
    )


def _fm(root: Path, *argv: str) -> subprocess.CompletedProcess:
    import os

    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "fm", *argv],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
        env=env,
    )


class FlowCoreEquivalenceTests(unittest.TestCase):
    """The incremental core replayed step-by-step must match run_flow."""

    def _incremental(self, flow: dict, labels: list[str], answers: list[str]):
        position, err = initial_position(flow)
        self.assertIsNone(err)
        label_q, answer_q = list(labels), list(answers)
        while position["kind"] != "done":
            if position["kind"] == "step":
                if not label_q:
                    return None
                position, _, err = apply_label(flow, position, label_q.pop(0))
            else:
                if not answer_q:
                    return None
                position, _, err = apply_answer(flow, position, answer_q.pop(0))
            self.assertIsNone(err)
        return position["outcome"]

    def test_equivalence_across_paths(self) -> None:
        import yaml

        flow = yaml.safe_load(FLOW_YAML.replace("on:", "'on':"))
        scripts = [
            (["Go", "Go"], []),
            (["Go", "Recycle", "Go", "Go"], []),
            (["Go", "Hold"], ["resolved"]),
            (["Go", "Hold"], ["rejected"]),
            (["uncertainty"], ["rejected"]),
            (["uncertainty", "Go", "Go"], ["resolved"]),
            (["Nope"], []),
        ]
        for labels, answers in scripts:
            one_shot = run_flow(flow, labels=list(labels), answers=list(answers))
            incremental = self._incremental(flow, labels, answers)
            if one_shot.ok:
                self.assertEqual(one_shot.outcome, incremental, f"script {labels}/{answers}")


class FlowStateCliTests(unittest.TestCase):
    def _setup_repo(self, tmp: str) -> Path:
        root = Path(tmp)
        (root / "flows").mkdir()
        (root / "flows" / "state_test.yaml").write_text(FLOW_YAML, encoding="utf-8")
        # minimal skills tree so the G4 binding resolves
        meta_dir = root / "skills" / "test_flow"
        meta_dir.mkdir(parents=True)
        (meta_dir / "meta.md").write_text(
            "# Skill Meta: test_flow\n\n"
            "- skill_id: `test_flow`\n"
            "- capability_refs:\n"
            "  - `../../capabilities/design/130_cap_dsn_004_test_plan_structuring.md#xid-X`\n",
            encoding="utf-8",
        )
        cap_dir = root / "capabilities" / "design"
        cap_dir.mkdir(parents=True)
        (cap_dir / "130_cap_dsn_004_test_plan_structuring.md").write_text(
            "- capability_id: `CAP-DSN-004`\n", encoding="utf-8"
        )
        (root / "capabilities" / "quality").mkdir(parents=True)
        (root / "capabilities" / "quality" / "100_cap_qa_001_code_review.md").write_text(
            "- capability_id: `CAP-QA-001`\n", encoding="utf-8"
        )
        return root

    def test_start_next_advance_with_bridged_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._setup_repo(tmp)
            state = "work/flows/FLOW-STATE-TEST.state.json"

            r = _fm(root, "flow", "start", "--root", str(root), "--flow", "flows/state_test.yaml", "--json")
            self.assertEqual(0, r.returncode, r.stdout + r.stderr)
            report = json.loads(r.stdout)
            self.assertEqual("awaiting_label", report["status"])
            self.assertEqual("work", report["current"]["step"])
            self.assertEqual("test_flow", report["current"]["skill"])
            self.assertEqual("skills/test_flow/meta.md", report["current"]["skill_meta"])

            r = _fm(root, "flow", "next", "--root", str(root), "--state", state, "--json")
            self.assertEqual(0, r.returncode, r.stdout + r.stderr)
            self.assertEqual("work", json.loads(r.stdout)["current"]["step"])

            log = root / "run_log.md"
            log.write_text(_closed_log("done"), encoding="utf-8")
            r = _fm(root, "flow", "advance", "--root", str(root), "--state", state,
                    "--label", "log:run_log.md", "--json")
            self.assertEqual(0, r.returncode, r.stdout + r.stderr)
            # a bridged line precedes the JSON; parse the JSON tail
            text = r.stdout
            self.assertIn("closure=done -> label=Go", text)
            report = json.loads(text[text.index("{"):])
            self.assertEqual("awaiting_label", report["status"])
            self.assertEqual("review", report["current"]["step"])

            r = _fm(root, "flow", "advance", "--root", str(root), "--state", state,
                    "--label", "Hold", "--json")
            self.assertEqual(0, r.returncode, r.stdout + r.stderr)
            report = json.loads(r.stdout[r.stdout.index("{"):])
            self.assertEqual("awaiting_answer", report["status"])
            self.assertEqual("review blocked", report["suspended"]["ask"])

            r = _fm(root, "flow", "advance", "--root", str(root), "--state", state,
                    "--answer", "resolved", "--json")
            self.assertEqual(0, r.returncode, r.stdout + r.stderr)
            report = json.loads(r.stdout[r.stdout.index("{"):])
            self.assertEqual("awaiting_label", report["status"])
            self.assertEqual("review", report["current"]["step"])

            r = _fm(root, "flow", "advance", "--root", str(root), "--state", state,
                    "--label", "Go", "--json")
            report = json.loads(r.stdout[r.stdout.index("{"):])
            self.assertEqual("complete", report["status"])
            self.assertEqual("COMPLETE", report["outcome"])

            r = _fm(root, "flow", "advance", "--root", str(root), "--state", state,
                    "--label", "Go")
            self.assertEqual(1, r.returncode)
            self.assertIn("already terminated", r.stdout)

    def test_advance_refuses_unclosed_bridge_and_keeps_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._setup_repo(tmp)
            state = "work/flows/FLOW-STATE-TEST.state.json"
            _fm(root, "flow", "start", "--root", str(root), "--flow", "flows/state_test.yaml")

            log = root / "open_log.md"
            log.write_text("# Skill Run Log\n\n" + LOAD_GATE, encoding="utf-8")
            r = _fm(root, "flow", "advance", "--root", str(root), "--state", state,
                    "--label", "log:open_log.md")
            self.assertEqual(1, r.returncode)
            self.assertIn("could not be bridged", r.stdout)

            r = _fm(root, "flow", "next", "--root", str(root), "--state", state, "--json")
            self.assertEqual("work", json.loads(r.stdout)["current"]["step"])

    def test_flow_change_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._setup_repo(tmp)
            state = "work/flows/FLOW-STATE-TEST.state.json"
            _fm(root, "flow", "start", "--root", str(root), "--flow", "flows/state_test.yaml")
            flow_file = root / "flows" / "state_test.yaml"
            flow_file.write_text(flow_file.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
            r = _fm(root, "flow", "next", "--root", str(root), "--state", state)
            self.assertEqual(1, r.returncode)
            self.assertIn("flow file changed", r.stdout)


class FlowDoctorSkillBindingTests(unittest.TestCase):
    def test_g4_binding_validated(self) -> None:
        from fm.flowdoctor import validate_flow, _SKILL_BINDING_CACHE

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "flows").mkdir()
            flow = root / "flows" / "f.yaml"
            (root / "capabilities" / "design").mkdir(parents=True)
            (root / "capabilities" / "design" / "130_cap_dsn_004_x.md").write_text(
                "- capability_id: `CAP-DSN-004`\n", encoding="utf-8"
            )
            meta_dir = root / "skills" / "some_skill"
            meta_dir.mkdir(parents=True)
            (meta_dir / "meta.md").write_text(
                "- skill_id: `some_skill`\n"
                "- capability_refs:\n"
                "  - `../../capabilities/design/130_cap_dsn_004_x.md#xid-X`\n",
                encoding="utf-8",
            )

            def write_flow(skill_line: str) -> None:
                _SKILL_BINDING_CACHE.clear()
                flow.write_text(
                    "flow_id: F\n"
                    "entry: s\n"
                    "steps:\n"
                    "  s:\n"
                    "    facets: []\n"
                    "    permission: { edit: false }\n"
                    "    capability: CAP-DSN-004\n"
                    f"{skill_line}"
                    "    'on':\n"
                    "      Go: COMPLETE\n"
                    "      _invalid_or_absent: ABORT\n",
                    encoding="utf-8",
                )

            write_flow("    skill: some_skill\n")
            self.assertTrue(validate_flow(flow).ok, validate_flow(flow).errors)

            write_flow("    skill: missing_skill\n")
            self.assertTrue(any("G4" in e for e in validate_flow(flow).errors))

            (meta_dir / "meta.md").write_text(
                "- skill_id: `some_skill`\n"
                "- capability_refs:\n"
                "  - `../../capabilities/quality/100_cap_qa_001_y.md#xid-Y`\n",
                encoding="utf-8",
            )
            write_flow("    skill: some_skill\n")
            errors = validate_flow(flow).errors
            self.assertTrue(any("does not declare capability" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()

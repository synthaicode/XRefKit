import unittest
from pathlib import Path

from fm.flowdoctor import _load_flow
from fm.flowengine import run_flow

CAB_V2 = Path(__file__).resolve().parents[1] / "flows" / "cab_workflow.v2.yaml"


def _small_flow() -> dict:
    return {
        "flow_id": "FLOW-T",
        "name": "t",
        "entry": "draft",
        "global_handback": {
            "uncertainty": {"to": "coordinator", "ask": "unknown", "resume": "draft"}
        },
        "steps": {
            "draft": {
                "facets": ["planner"],
                "capability": "CAP-DRAFT",
                "on": {
                    "complete": "verify",
                    "_invalid_or_absent": {
                        "handback": {
                            "to": "coordinator",
                            "ask": "blocked",
                            "resume": {"resolved": "draft", "rejected": "ABORT"},
                        }
                    },
                },
            },
            "verify": {
                "result_map": {"complete": "COMPLETE", "needs_fix": "draft"},
                "on": {"complete": "COMPLETE", "needs_fix": "draft", "_invalid_or_absent": "ABORT"},
            },
        },
    }


class FlowEngineTests(unittest.TestCase):
    def test_happy_path_completes(self):
        result = run_flow(_small_flow(), labels=["complete", "complete"], answers=[])
        self.assertTrue(result.ok)
        self.assertEqual("COMPLETE", result.outcome)
        self.assertEqual(2, result.steps_executed)

    def test_fallback_to_handback_then_loop(self):
        # draft emits an unknown label -> _invalid_or_absent handback -> resolved
        # loops back to draft, then completes.
        result = run_flow(
            _small_flow(),
            labels=["ghost", "complete", "complete"],
            answers=["resolved"],
        )
        self.assertTrue(result.ok)
        self.assertEqual("COMPLETE", result.outcome)
        self.assertTrue(any(e.get("fallback") for e in result.trace if e["event"] == "emit"))
        self.assertTrue(any(e["event"] == "suspend" for e in result.trace))

    def test_handback_rejected_aborts(self):
        result = run_flow(_small_flow(), labels=["ghost"], answers=["rejected"])
        self.assertTrue(result.ok)
        self.assertEqual("ABORT", result.outcome)

    def test_invalid_resume_answer_aborts(self):
        result = run_flow(_small_flow(), labels=["ghost"], answers=["nonsense"])
        self.assertTrue(result.ok)
        self.assertEqual("ABORT", result.outcome)

    def test_global_handback_resumes(self):
        result = run_flow(
            _small_flow(),
            labels=["uncertainty", "complete", "complete"],
            answers=["acknowledged"],
        )
        self.assertTrue(result.ok)
        self.assertEqual("COMPLETE", result.outcome)
        self.assertTrue(any(e["event"] == "global_handback" for e in result.trace))

    def test_script_exhaustion_is_engine_error(self):
        result = run_flow(_small_flow(), labels=["complete"], answers=[])
        self.assertFalse(result.ok)
        self.assertIsNone(result.outcome)
        self.assertIsNotNone(result.error)

    def test_max_steps_guard(self):
        loop = {
            "flow_id": "FLOW-LOOP",
            "entry": "a",
            "steps": {"a": {"on": {"go": "a", "_invalid_or_absent": "a"}}},
        }
        result = run_flow(loop, labels=["go"] * 50, answers=[], max_steps=10)
        self.assertFalse(result.ok)
        self.assertIn("max_steps", result.error)

    def test_cab_v2_approved_path(self):
        data = _load_flow(CAB_V2)
        result = run_flow(
            data,
            labels=["Go", "Go", "Go", "no_feedback", "ready_for_decision"],
            answers=["approved"],
        )
        self.assertTrue(result.ok, result.error)
        self.assertEqual("COMPLETE", result.outcome)

    def test_cab_v2_reevaluation_loop(self):
        data = _load_flow(CAB_V2)
        result = run_flow(
            data,
            labels=[
                "Go", "Go", "Go", "feedback_needed", "Go",
                "ready_for_decision",
                "Go", "Go", "Go", "no_feedback", "ready_for_decision",
            ],
            answers=["needs_reevaluation", "approved"],
        )
        self.assertTrue(result.ok, result.error)
        self.assertEqual("COMPLETE", result.outcome)
        # the loop re-entered the first evaluation
        enters = [e["step"] for e in result.trace if e["event"] == "enter"]
        self.assertGreater(enters.count("release_plan_suitability_review"), 1)


if __name__ == "__main__":
    unittest.main()

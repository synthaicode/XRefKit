import contextlib
import copy
import io
import tempfile
import unittest
from pathlib import Path

import yaml

from fm.__main__ import main
from fm.flowdoctor import validate_flow


def _valid_flow() -> dict:
    return {
        "flow_id": "FLOW-T",
        "name": "t_workflow",
        "entry": "draft",
        "invariants": ["draft_only"],
        "global_handback": {
            "uncertainty": {"to": "coordinator", "ask": "resolve unknown", "resume": "draft"}
        },
        "steps": {
            "draft": {
                "facets": ["planner"],
                "permission": {"edit": True, "paths": ["docs/**"]},
                "capability": "CAP-DRAFT",
                "acceptance": [{"tool": "python tools/check.py"}],
                "on": {
                    "complete": "verify",
                    "_invalid_or_absent": {
                        "handback": {
                            "to": "coordinator",
                            "ask": "draft blocked",
                            "resume": {"resolved": "draft", "rejected": "ABORT"},
                        }
                    },
                },
            },
            "verify": {
                "facets": ["verify_policy"],
                "permission": {"edit": False},
                "result_map": {"complete": "COMPLETE", "needs_fix": "draft"},
                "on": {
                    "complete": "COMPLETE",
                    "needs_fix": "draft",
                    "_invalid_or_absent": "ABORT",
                },
            },
        },
    }


class FlowDoctorTests(unittest.TestCase):
    def _check(self, data: dict):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "flow.yaml"
            path.write_text(yaml.safe_dump(data), encoding="utf-8")
            return validate_flow(path)

    def test_valid_flow_passes(self):
        result = self._check(_valid_flow())
        self.assertTrue(result.ok, result.errors)
        self.assertEqual("deterministic", result.schema)

    def test_missing_fallback_edge_fails_d2(self):
        data = _valid_flow()
        del data["steps"]["verify"]["on"]["_invalid_or_absent"]
        result = self._check(data)
        self.assertFalse(result.ok)
        self.assertTrue(any(FALLBACK in e for e in result.errors for FALLBACK in ["_invalid_or_absent"]))

    def test_branch_without_producer_fails_k4(self):
        data = _valid_flow()
        # verify branches but loses its result_map producer
        del data["steps"]["verify"]["result_map"]
        result = self._check(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("hidden consolidation (K4)" in e for e in result.errors))

    def test_capability_and_result_map_conflict_fails(self):
        data = _valid_flow()
        data["steps"]["verify"]["capability"] = "CAP-X"
        result = self._check(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("K3/K5" in e for e in result.errors))

    def test_handback_without_resume_fails_h1(self):
        data = _valid_flow()
        data["steps"]["draft"]["on"]["_invalid_or_absent"] = {
            "handback": {"to": "coordinator", "ask": "blocked"}
        }
        result = self._check(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("missing 'resume'" in e for e in result.errors))

    def test_unreachable_step_fails_c2(self):
        data = _valid_flow()
        data["steps"]["orphan"] = {
            "on": {"complete": "COMPLETE", "_invalid_or_absent": "ABORT"}
        }
        result = self._check(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("unreachable" in e for e in result.errors))

    def test_inescapable_loop_fails_c3(self):
        data = {
            "flow_id": "FLOW-LOOP",
            "name": "loop",
            "entry": "a",
            "steps": {
                "a": {"on": {"go": "b", "_invalid_or_absent": "b"}},
                "b": {"on": {"go": "a", "_invalid_or_absent": "a"}},
            },
        }
        result = self._check(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("inescapable loop (C3)" in e for e in result.errors))

    def test_entry_not_a_step_fails_c4(self):
        data = _valid_flow()
        data["entry"] = "nope"
        result = self._check(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("entry missing" in e for e in result.errors))

    def test_unknown_target_fails_c1(self):
        data = _valid_flow()
        data["steps"]["draft"]["on"]["complete"] = "ghost"
        result = self._check(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("not a known step or terminal" in e for e in result.errors))

    def test_legacy_flow_passes_with_warning(self):
        data = {
            "flow_id": "FLOW-LEGACY",
            "name": "legacy",
            "sequence": ["a", "b"],
            "control_rules": ["x"],
        }
        result = self._check(data)
        self.assertTrue(result.ok)
        self.assertEqual("legacy", result.schema)
        self.assertTrue(any("legacy flow" in w for w in result.warnings))

    def test_tool_gate_without_result_map_warns_g1(self):
        data = _valid_flow()
        # draft declares a tool gate but has no result_map
        data["steps"]["draft"]["acceptance"] = [{"tool": "python tools/x.py"}]
        result = self._check(data)
        self.assertTrue(result.ok, result.errors)  # warning, not error
        self.assertTrue(any("(G1)" in w for w in result.warnings))

    def test_canonical_verdict_inconsistent_target_fails_g2(self):
        data = _valid_flow()
        # use a canonical verdict but route it wrongly: Kill must go to ABORT
        data["steps"]["verify"]["on"] = {
            "Kill": "draft",  # wrong: Kill must route to ABORT
            "_invalid_or_absent": "ABORT",
        }
        data["steps"]["verify"]["result_map"] = {"complete": "draft"}
        result = self._check(data)
        self.assertFalse(result.ok)
        self.assertTrue(any("(G2)" in e for e in result.errors))

    def test_canonical_verdicts_consistent_targets_pass_g2(self):
        data = _valid_flow()
        data["steps"]["verify"]["result_map"] = {"complete": "COMPLETE", "needs_fix": "draft"}
        data["steps"]["verify"]["on"] = {
            "Go": "COMPLETE",
            "Recycle": "draft",
            "Kill": "ABORT",
            "Hold": {"handback": {"to": "x", "ask": "y", "resume": "draft"}},
            "_invalid_or_absent": "ABORT",
        }
        result = self._check(data)
        self.assertTrue(result.ok, result.errors)

    def test_bare_on_key_is_not_a_yaml_bool(self):
        # Authored flows use bare `on:`; under YAML 1.1 that would parse as a
        # boolean key. The loader must keep it a string so the exit map is read.
        raw = (
            "flow_id: FLOW-RAW\n"
            "name: raw\n"
            "entry: only\n"
            "steps:\n"
            "  only:\n"
            "    on:\n"
            "      complete: COMPLETE\n"
            "      _invalid_or_absent: ABORT\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "flow.yaml"
            path.write_text(raw, encoding="utf-8")
            result = validate_flow(path)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual("deterministic", result.schema)

    def test_cli_exit_code_on_valid_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            flow_dir = root / "flows"
            flow_dir.mkdir()
            (flow_dir / "t.yaml").write_text(yaml.safe_dump(_valid_flow()), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                rc = main(["flow", "doctor", "--root", str(root), "--json"])
            self.assertEqual(0, rc)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from fm.flowbridge import derive_flow_label, resolve_label_arg
from fm.flowengine import run_flow

LOAD_GATE = "## Skill Load Gate\n\n- status: `opened_by_fm_skill_run`\n"


def _log(*, closure_events: list[str]) -> str:
    body = (
        "# Skill Run Log\n\n"
        "- skill_id: `sample_skill`\n\n"
        f"{LOAD_GATE}\n"
        "## Phase Events\n\n"
    )
    for event in closure_events:
        body += event + "\n"
    return body


def _closure_event(status: str, role: str = "closure_gate") -> str:
    return f"- 2026-07-03 `closure` -> `{status}` role=`{role}`"


class FlowBridgeTests(unittest.TestCase):
    def _write(self, tmp: str, text: str) -> Path:
        p = Path(tmp) / "run_log.md"
        p.write_text(text, encoding="utf-8")
        return p

    def test_closure_done_maps_to_go(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = self._write(tmp, _log(closure_events=[_closure_event("done")]))
            result = derive_flow_label(log)
            self.assertTrue(result.ok)
            self.assertEqual("done", result.closure)
            self.assertEqual("Go", result.label)

    def test_closure_escalated_maps_to_uncertainty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = self._write(tmp, _log(closure_events=[_closure_event("escalated")]))
            result = derive_flow_label(log)
            self.assertTrue(result.ok)
            self.assertEqual("uncertainty", result.label)

    def test_last_closure_event_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = self._write(
                tmp,
                _log(closure_events=[_closure_event("escalated"), _closure_event("done")]),
            )
            result = derive_flow_label(log)
            self.assertTrue(result.ok)
            self.assertEqual("Go", result.label)

    def test_unclosed_run_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = self._write(tmp, _log(closure_events=[]))
            result = derive_flow_label(log)
            self.assertFalse(result.ok)
            self.assertIn("no closure_gate phase event", result.error)

    def test_closure_event_without_closure_gate_role_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = self._write(
                tmp,
                _log(closure_events=[_closure_event("done", role="executor")]),
            )
            result = derive_flow_label(log)
            self.assertFalse(result.ok)

    def test_log_without_load_gate_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = self._write(tmp, "# Not a run log\n")
            result = derive_flow_label(log)
            self.assertFalse(result.ok)
            self.assertIn("Skill Load Gate", result.error)

    def test_missing_log_is_refused(self) -> None:
        result = derive_flow_label(Path("does/not/exist.md"))
        self.assertFalse(result.ok)
        self.assertIn("not found", result.error)

    def test_resolve_label_arg_passthrough_and_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            label, bridge = resolve_label_arg("Go", Path(tmp))
            self.assertEqual("Go", label)
            self.assertIsNone(bridge)

            self._write(tmp, _log(closure_events=[_closure_event("done")]))
            label, bridge = resolve_label_arg("log:run_log.md", Path(tmp))
            self.assertEqual("Go", label)
            self.assertTrue(bridge.ok)

            label, bridge = resolve_label_arg("log:missing.md", Path(tmp))
            self.assertIsNone(label)
            self.assertFalse(bridge.ok)

    def test_bridged_label_drives_engine_transition(self) -> None:
        flow = {
            "flow_id": "FLOW-BRIDGE-TEST",
            "entry": "work",
            "global_handback": {
                "uncertainty": {
                    "to": "coordinator",
                    "ask": "resolve",
                    "resume": {"resolved": "work", "rejected": "ABORT"},
                }
            },
            "steps": {
                "work": {
                    "facets": [],
                    "permission": {"edit": False},
                    "capability": "CAP-TEST-001",
                    "on": {"Go": "COMPLETE", "_invalid_or_absent": "ABORT"},
                }
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            log = self._write(tmp, _log(closure_events=[_closure_event("done")]))
            label, bridge = resolve_label_arg(f"log:{log.name}", Path(tmp))
            self.assertTrue(bridge.ok)
            result = run_flow(flow, labels=[label], answers=[])
            self.assertTrue(result.ok)
            self.assertEqual("COMPLETE", result.outcome)

        with tempfile.TemporaryDirectory() as tmp:
            log = self._write(tmp, _log(closure_events=[_closure_event("escalated")]))
            label, _ = resolve_label_arg(f"log:{log.name}", Path(tmp))
            result = run_flow(flow, labels=[label], answers=["rejected"])
            self.assertTrue(result.ok)
            self.assertEqual("ABORT", result.outcome)


if __name__ == "__main__":
    unittest.main()

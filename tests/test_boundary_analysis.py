import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from xrefkit.__main__ import main
from xrefkit.boundary_analysis import analyze_dashboard_payload, render_markdown


class BoundaryAnalysisTests(unittest.TestCase):
    def _run(
        self,
        skill_id: str,
        path: str,
        xids: list[str],
        *,
        feedback: list[dict[str, str]] | None = None,
    ) -> dict[str, object]:
        return {
            "path": path,
            "name": Path(path).name,
            "skill_id": skill_id,
            "run_id": f"run-{path}",
            "mcp_session_id": f"mcp-{path}",
            "repository_fingerprint": "repo-001",
            "status": "closed",
            "closure_status": "done",
            "quality_required": True,
            "quality_status": "done",
            "selected_xids": xids,
            "queried_xids": xids,
            "loaded_xids": xids,
            "used_xids": xids,
            "unused_xids": [],
            "available_xids": xids,
            "queried_not_loaded_xids": [],
            "loaded_not_applied_xids": [],
            "missing_information": [],
            "observation_events": feedback or [],
            "mcp_events": [],
        }

    def _payload(self) -> dict[str, object]:
        xid_a = "XID-A-001"
        xid_b = "XID-B-001"
        return {
            "schema": "xrefkit.dashboard/v1",
            "audit_errors": [],
            "runs": [
                self._run(
                    "alpha",
                    "work/sessions/alpha-a-1.md",
                    [xid_a],
                    feedback=[
                        {"event": "human.feedback", "status": "corrected", "target": xid_a, "note": "wrong fact"},
                        {"event": "human.feedback", "status": "corrected", "target": "OUT-001", "note": "wrong procedure"},
                    ],
                ),
                self._run(
                    "alpha",
                    "work/sessions/alpha-a-2.md",
                    [xid_a],
                    feedback=[
                        {"event": "human.feedback", "status": "rejected", "target": xid_a, "note": "stale fact"},
                        {"event": "human.feedback", "status": "rejected", "target": "OUT-002", "note": "wrong decision"},
                    ],
                ),
                self._run("alpha", "work/sessions/alpha-b-1.md", [xid_b]),
                self._run("alpha", "work/sessions/alpha-b-2.md", [xid_b]),
                self._run("beta", "work/sessions/beta-1.md", [xid_a, xid_b]),
                self._run("beta", "work/sessions/beta-2.md", [xid_a, xid_b]),
            ],
        }

    def test_analysis_emits_conservative_boundary_candidates(self) -> None:
        report = analyze_dashboard_payload(self._payload(), source_hash="source-001", min_samples=2)

        self.assertEqual("xrefkit.boundary_observation/v1", report["schema"])
        self.assertEqual("proposal_only", report["status"])
        self.assertEqual(6, report["sample_count"])
        self.assertEqual(6, report["correlation"]["exact"])
        categories = {item["category"] for item in report["proposals"]}
        self.assertIn("split", categories)
        self.assertIn("merge", categories)
        self.assertIn("knowledge_correction", categories)
        self.assertIn("skill_correction", categories)
        self.assertTrue(all(item["decision"]["status"] == "pending" for item in report["proposals"]))

        xid_row = next(item for item in report["xid_usage"] if item["xid"] == "XID-A-001")
        self.assertEqual(4, xid_row["run_count"])
        self.assertEqual(4, xid_row["used_count"])

    def test_markdown_explains_proposal_only_boundary(self) -> None:
        markdown = render_markdown(analyze_dashboard_payload(self._payload(), source_hash="source-001"))

        self.assertIn("Proposal-only output", markdown)
        self.assertIn("## Proposals", markdown)
        self.assertIn("Counterevidence", markdown)
        self.assertIn("## Decision", markdown)
        self.assertIn("XID-A-001", markdown)

    def test_cli_writes_markdown_and_can_emit_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "dashboard.json"
            output = root / "reports" / "boundary.md"
            source.write_text(json.dumps(self._payload()), encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = main(
                    [
                        "analysis",
                        "boundary",
                        "report",
                        "--input",
                        str(source),
                        "--out",
                        str(output),
                        "--json",
                    ]
                )

            self.assertEqual(0, result)
            self.assertTrue(output.exists())
            self.assertIn("Proposal-only output", output.read_text(encoding="utf-8"))
            response = json.loads(stdout.getvalue())
            self.assertEqual("proposal_only", response["status"])
            self.assertEqual(4, response["summary"]["proposals"])

    def test_invalid_dashboard_input_fails_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "invalid.json"
            output = Path(tmp) / "boundary.md"
            source.write_text(json.dumps({"runs": "not-a-list"}), encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = main(
                    [
                        "analysis",
                        "boundary",
                        "report",
                        "--input",
                        str(source),
                        "--out",
                        str(output),
                    ]
                )

            self.assertEqual(1, result)
            self.assertFalse(output.exists())
            self.assertIn("runs array", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

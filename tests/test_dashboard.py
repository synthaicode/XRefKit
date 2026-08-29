import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from xrefkit.__main__ import main
from xrefkit.dashboard import _html_page, _load_mcp_audit, build_payload
from xrefkit.skillmeta import GUARD_CAPABILITY_REF, GUARD_KNOWLEDGE_REF, REQUIRED_OS_CONTRACT, SKILL_RUNTIME_CAPABILITY_REF


class DashboardTests(unittest.TestCase):
    def _valid_meta_text(self, model_tier: str | None = None) -> str:
        os_contract = "".join(
            f"  - {key}: `{value}`\n" for key, value in REQUIRED_OS_CONTRACT.items()
        )
        tier_line = f"- model_tier: `{model_tier}`\n" if model_tier else ""
        return (
            "# Skill Meta: sample\n\n"
            "- skill_id: `sample_skill`\n"
            "- summary: sample summary\n"
            "- use_when: sample use\n"
            "- input: sample input\n"
            "- output: sample output\n"
            "- maturity: `stable`\n"
            "- execution_mode: `local_default`\n"
            "- guard_policy: `required`\n"
            "- capability_layering: `required`\n"
            "- workflow_protocol: `required`\n"
            "- tuning: sample specialization\n"
            "- role_responsibilities:\n"
            "  - executor: sample execution responsibility\n"
            f"{tier_line}"
            "- os_contract:\n"
            f"{os_contract}"
            "- constraints: keep observed boundary explicit\n"
            "- skill_doc: `./SKILL.md`\n"
            "- capability_refs:\n"
            f"  - `{SKILL_RUNTIME_CAPABILITY_REF}`\n"
            f"  - `{GUARD_CAPABILITY_REF}`\n"
            "- knowledge_refs:\n"
            f"  - `{GUARD_KNOWLEDGE_REF}`\n"
            "- observation_refs:\n"
            "  - `../../observations/sample.md`\n"
        )

    def _write_valid_skill(self, root: Path, model_tier: str | None = None) -> None:
        meta = root / "skills" / "sample" / "meta.md"
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text(self._valid_meta_text(model_tier=model_tier), encoding="utf-8")
        (meta.parent / "SKILL.md").write_text("# Sample Skill\n", encoding="utf-8")

    def _run_main(self, argv: list[str]) -> str:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(0, main(argv))
        return stdout.getvalue()

    def _write_closed_run(self, root: Path) -> Path:
        self._write_valid_skill(root, model_tier="standard")
        local_knowledge = root / "packs" / "local" / "acme" / "knowledge" / "service_map.md"
        local_knowledge.parent.mkdir(parents=True, exist_ok=True)
        local_knowledge.write_text(
            "<!-- xid: local-service-map-001 -->\n"
            "<a id=\"xid-local-service-map-001\"></a>\n\n"
            "# Local Service Map\n",
            encoding="utf-8",
        )
        catalog = root / "domain_catalog.json"
        catalog.write_text(
            json.dumps(
                {
                    "entries": [
                        {
                            "xid": "local-service-map-001",
                            "kind": "source-structure",
                            "title": "Local pack service map",
                            "summary": "Local pack knowledge selected by the Skill run.",
                        },
                        {
                            "xid": "LOCAL-KNOWLEDGE-UNUSED-001",
                            "kind": "source-structure",
                            "title": "Unused knowledge",
                            "summary": "Available but not selected.",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        out = root / "work" / "sessions" / "run.md"
        self._run_main(
            [
                "skill",
                "run",
                "--root",
                str(root),
                "--meta",
                "skills/sample/meta.md",
                "--task",
                "Create a controlled output",
                "--out",
                str(out),
                "--domain-knowledge-catalog",
                str(catalog),
                "--knowledge-input",
                "source_structure=local-service-map-001",
            ]
        )
        self._run_main(
            [
                "skill",
                "workitem",
                "--log",
                str(out),
                "--item",
                "WI-001",
                "--text",
                "Implement controlled output",
                "--completion-criterion",
                "output is written and validated",
                "--status",
                "done",
                "--role",
                "sample_skill:executor",
            ]
        )
        for artifact_id, kind, target, role in (
            ("OUT-001", "output", "docs/output.md", "sample_skill:executor"),
            ("EVD-001", "evidence", "local-service-map-001", "sample_skill:checker"),
            ("CHK-001", "check", "review accepted", "sample_skill:quality_reviewer"),
            ("HND-001", "handoff", "human review", "sample_skill:handoff_owner"),
        ):
            self._run_main(
                [
                    "skill",
                    "artifact",
                    "--log",
                    str(out),
                    "--artifact",
                    artifact_id,
                    "--kind",
                    kind,
                    "--target",
                    target,
                    "--item",
                    "WI-001",
                    "--status",
                    "done",
                    "--role",
                    role,
                ]
            )
        self._run_main(
            [
                "skill",
                "concern",
                "--log",
                str(out),
                "--concern",
                "UNK-001",
                "--kind",
                "unknown",
                "--status",
                "resolved",
                "--text",
                "Resolved by evidence",
                "--role",
                "sample_skill:checker",
            ]
        )
        for phase, role in (
            ("execution", "sample_skill:executor"),
            ("check", "sample_skill:checker"),
            ("quality", "sample_skill:quality_reviewer"),
            ("handoff", "sample_skill:handoff_owner"),
        ):
            self._run_main(
                [
                    "skill",
                    "phase",
                    "--log",
                    str(out),
                    "--phase",
                    phase,
                    "--status",
                    "done",
                    "--role",
                    role,
                ]
            )
        self._run_main(["skill", "verify", "--log", str(out)])
        self._run_main(["skill", "close", "--log", str(out)])
        return out

    def test_dashboard_payload_summarizes_skill_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_log = self._write_closed_run(root)

            payload = build_payload(root, root / "work" / "sessions")

            self.assertEqual(str(root.resolve()), payload["root"])
            self.assertEqual(1, payload["summary"]["runs"])
            self.assertEqual(1, payload["summary"]["closed"])
            self.assertEqual(0, payload["summary"]["blocked"])
            self.assertEqual(1, payload["summary"]["unknowns"])
            self.assertEqual(1, payload["summary"]["handoffs"])
            self.assertEqual("sample_skill", payload["runs"][0]["skill_id"])
            self.assertEqual("closed", payload["runs"][0]["status"])
            self.assertEqual("done", payload["runs"][0]["closure_status"])
            self.assertEqual([], payload["runs"][0]["used_xids"])
            self.assertIn("local-service-map-001", payload["runs"][0]["unused_xids"])
            self.assertIn("LOCAL-KNOWLEDGE-UNUSED-001", payload["runs"][0]["unused_xids"])
            self.assertGreaterEqual(len(payload["unused_xid_ranking"]), 2)
            self.assertEqual("LOCAL-KNOWLEDGE-UNUSED-001", payload["unused_xid_ranking"][0]["xid"])
            missing_codes = {item["code"] for item in payload["runs"][0]["missing_information"]}
            self.assertNotIn("run_id", missing_codes)
            self.assertIn("mcp_session_id", missing_codes)
            self.assertIn("skill_routing_trace", missing_codes)
            self.assertIn("loaded_xid_trace", missing_codes)
            self.assertIn("knowledge_search_trace", missing_codes)
            self.assertIn("human_feedback", missing_codes)
            self.assertIn("outcome_feedback", missing_codes)
            self.assertIn("token_usage", missing_codes)
            self.assertNotIn("knowledge_application_trace", missing_codes)
            self.assertEqual(1, payload["summary"]["runs_with_missing_information"])
            self.assertGreater(payload["summary"]["missing_information"], 0)
            self.assertTrue(payload["missing_information_ranking"])
            self.assertEqual(run_log.relative_to(root).as_posix(), payload["runs"][0]["path"])

    def test_dashboard_data_command_emits_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_closed_run(root)

            output = self._run_main(["dashboard", "data", "--root", str(root)])
            payload = json.loads(output)

            self.assertEqual(1, payload["summary"]["runs"])
            self.assertEqual("sample_skill", payload["runs"][0]["skill_id"])

    def test_dashboard_exposes_recovery_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_log = self._write_closed_run(root)
            common = [
                "workflow",
                "recovery",
                "--log",
                str(run_log),
                "--recovery-id",
                "REC-001",
                "--resume-location",
                "after reconcile",
                "--reason",
                "child status was not yet projected",
                "--next-action",
                "confirm and rerun reconcile",
            ]
            self._run_main([*common, "--status", "proposed"])
            self._run_main([*common, "--status", "confirmed", "--reviewer", "human@example.test"])

            payload = build_payload(root, root / "work" / "sessions")
            self.assertEqual(2, payload["summary"]["recoveries"])
            self.assertEqual(
                ["proposed", "confirmed"],
                [item["status"] for item in payload["recoveries"]],
            )
            html = _html_page(payload)
            self.assertIn('data-panel="recovery"', html)
            self.assertIn('id="recovery"', html)
            self.assertIn("Resume location", html)
            self.assertIn("after reconcile", html)
            self.assertIn("human@example.test", html)
            self.assertIn("Executable action", html)
            self.assertIn("Verification", html)
            self.assertIn("Max attempts", html)

    def test_dashboard_aggregates_runs_by_prompt_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "work" / "sessions" / "root.md"
            second = root / "work" / "sessions" / "child.md"
            for out, run_id, parent, work_item in (
                (first, "11111111-1111-4111-8111-111111111111", None, None),
                (second, "22222222-2222-4222-8222-222222222222", "11111111-1111-4111-8111-111111111111", "WI-002"),
            ):
                args = [
                    "workflow", "run", "--task", "Flow node", "--out", str(out),
                    "--run-id", run_id, "--flow-id", "FLOW-001",
                    "--root-run-id", "11111111-1111-4111-8111-111111111111",
                    "--use-default-completion-conditions",
                ]
                if parent:
                    args.extend(["--parent-run-id", parent, "--work-item-id", work_item])
                self._run_main(args)

            payload = build_payload(root, root / "work" / "sessions")
            assert payload["summary"]["flows"] == 1
            flow = payload["flows"][0]
            assert flow["flow_id"] == "FLOW-001"
            assert flow["root_run_id"] == "11111111-1111-4111-8111-111111111111"
            assert flow["state"] == "blocked"
            assert set(flow["run_ids"]) == {
                "11111111-1111-4111-8111-111111111111",
                "22222222-2222-4222-8222-222222222222",
            }
            child = next(run for run in payload["runs"] if run["run_id"] == "22222222-2222-4222-8222-222222222222")
            assert child["parent_run_id"] == "11111111-1111-4111-8111-111111111111"
            assert child["work_item_id"] == "WI-002"

    def test_workflow_delegate_starts_child_skill_and_records_parent_flow_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            parent = root / "work" / "sessions" / "parent.md"
            child = root / "work" / "sessions" / "child.md"
            self._run_main([
                "workflow", "run", "--task", "Delegate one item", "--out", str(parent),
                "--run-id", "11111111-1111-4111-8111-111111111111",
                "--flow-id", "FLOW-002", "--use-default-completion-conditions",
            ])
            self._run_main([
                "workflow", "delegate", "--root", str(root), "--parent-log", str(parent), "--meta", "skills/sample/meta.md",
                "--task", "Execute delegated item", "--out", str(child),
                "--run-id", "22222222-2222-4222-8222-222222222222", "--work-item-id", "WI-002",
            ])
            parent_text = parent.read_text(encoding="utf-8")
            child_text = child.read_text(encoding="utf-8")
            assert '"event":"child_run.started"' in parent_text
            assert "- flow_id: `FLOW-002`" in child_text
            assert "- parent_run_id: `11111111-1111-4111-8111-111111111111`" in child_text
            assert "- work_item_id: `WI-002`" in child_text

    def test_prompt_flow_supports_multiple_delegated_work_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            parent = root / "work" / "sessions" / "parent.md"
            children = [root / "work" / "sessions" / "child-a.md", root / "work" / "sessions" / "child-b.md"]
            self._run_main([
                "workflow", "run", "--task", "Mixed prompt", "--out", str(parent),
                "--run-id", "11111111-1111-4111-8111-111111111111", "--flow-id", "FLOW-MULTI",
                "--use-default-completion-conditions",
            ])
            for index, child in enumerate(children, start=1):
                self._run_main([
                    "workflow", "delegate", "--root", str(root), "--parent-log", str(parent),
                    "--meta", "skills/sample/meta.md", "--task", f"Execute item {index}",
                    "--out", str(child), "--run-id", f"{index + 1:08d}-2222-4222-8222-222222222222",
                    "--work-item-id", f"WI-00{index}",
                ])

            payload = build_payload(root, root / "work" / "sessions")
            flow = next(flow for flow in payload["flows"] if flow["flow_id"] == "FLOW-MULTI")
            assert len(flow["run_ids"]) == 3
            parent_run = next(run for run in flow["runs"] if run["run_id"] == "11111111-1111-4111-8111-111111111111")
            assert len([event for event in parent_run["observation_events"] if event.get("event") == "child_run.started"]) == 2
            assert {run["work_item_id"] for run in flow["runs"] if run["parent_run_id"]} == {"WI-001", "WI-002"}

    def test_quality_review_routes_selected_skill_and_starts_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            parent = root / "work" / "sessions" / "parent.md"
            child = root / "work" / "sessions" / "quality.md"
            self._run_main([
                "workflow", "run", "--task", "Review flow", "--out", str(parent),
                "--run-id", "11111111-1111-4111-8111-111111111111",
                "--flow-id", "FLOW-QUALITY", "--use-default-completion-conditions",
            ])
            self._run_main([
                "workflow", "quality-review", "--root", str(root), "--parent-log", str(parent),
                "--meta", "skills/sample/meta.md", "--selected-skill", "sample_skill",
                "--candidate", "sample_skill", "--reason", "The output requires the selected review capability",
                "--task", "Review the output", "--out", str(child), "--work-item-id", "WI-001",
            ])
            parent_text = parent.read_text(encoding="utf-8")
            child_text = child.read_text(encoding="utf-8")
            assert '"selection_mode":"quality_review"' in parent_text
            assert '"event":"child_run.started"' in parent_text
            assert "- flow_id: `FLOW-QUALITY`" in child_text
            assert "- work_item_id: `WI-001`" in child_text

    def test_dashboard_clears_missing_information_when_observability_is_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_log = self._write_closed_run(root)
            run_id = next(
                line.split("`")[1]
                for line in run_log.read_text(encoding="utf-8").splitlines()
                if line.startswith("- run_id:")
            )
            commands = [
                [
                    "skill", "correlate", "--log", str(run_log), "--run-id", run_id,
                    "--mcp-session-id", "mcp-001", "--repository-fingerprint", "repo-001",
                ],
                [
                    "skill", "routing", "--log", str(run_log), "--selected-skill", "sample_skill",
                    "--candidate", "sample_skill", "--reason", "best candidate",
                ],
                [
                    "skill", "knowledge", "--log", str(run_log), "--action", "search",
                    "--query", "service map", "--status", "hit", "--xid", "local-service-map-001",
                ],
                [
                    "skill", "knowledge", "--log", str(run_log), "--action", "load",
                    "--xid", "local-service-map-001", "--content-hash", "hash-001",
                ],
                [
                    "skill", "knowledge", "--log", str(run_log), "--action", "apply",
                    "--xid", "local-service-map-001", "--content-hash", "hash-001", "--target", "OUT-001",
                ],
                [
                    "skill", "feedback", "--log", str(run_log), "--kind", "human",
                    "--status", "accepted", "--note", "accepted",
                ],
                [
                    "skill", "feedback", "--log", str(run_log), "--kind", "outcome",
                    "--status", "successful", "--note", "successful",
                ],
                ["skill", "tokens", "--log", str(run_log), "--total", "120"],
            ]
            for command in commands:
                self._run_main(command)

            payload = build_payload(root, root / "work" / "sessions")

            self.assertEqual([], payload["runs"][0]["missing_information"])
            self.assertEqual(0, payload["summary"]["runs_with_missing_information"])
            self.assertEqual([], payload["missing_information_ranking"])

    def test_dashboard_merges_mcp_audit_events_by_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_log = self._write_closed_run(root)
            run_id = next(
                line.split("`")[1]
                for line in run_log.read_text(encoding="utf-8").splitlines()
                if line.startswith("- run_id:")
            )
            self._run_main([
                "skill", "correlate", "--log", str(run_log), "--run-id", run_id,
                "--mcp-session-id", "mcp-audit-1", "--repository-fingerprint", "repo-audit-1",
            ])
            audit_path = root / "work" / "mcp" / "xid_audit.jsonl"
            audit_path.parent.mkdir(parents=True)
            common = {
                "schema": "xrefkit.mcp_audit/v1",
                "run_id": run_id,
                "mcp_session_id": "mcp-audit-1",
                "repository_fingerprint": "repo-audit-1",
                "skill_id": "sample_skill",
            }
            events = [
                {**common, "event_type": "run.bound", "tool": "bind_skill_run"},
                {**common, "event_type": "skill.ranked", "candidates": ["sample_skill"]},
                {**common, "event_type": "knowledge.search", "query": "service map", "status": "hit"},
                {
                    **common,
                    "event_type": "xid.resolved",
                    "xid": "local-service-map-001",
                    "content_hash": "hash-audit-1",
                },
            ]
            audit_path.write_text(
                "\n".join(json.dumps(event) for event in events) + "\n",
                encoding="utf-8",
            )

            payload = build_payload(root, root / "work" / "sessions", audit_path)
            run = payload["runs"][0]
            missing_codes = {item["code"] for item in run["missing_information"]}

            self.assertEqual("mcp-audit-1", run["mcp_session_id"])
            self.assertEqual("repo-audit-1", run["repository_fingerprint"])
            self.assertEqual(["local-service-map-001"], run["queried_xids"])
            self.assertEqual([], run["loaded_xids"])
            self.assertEqual(4, len(run["mcp_events"]))
            self.assertNotIn("mcp_session_id", missing_codes)
            self.assertNotIn("repository_fingerprint", missing_codes)
            self.assertNotIn("skill_routing_trace", missing_codes)
            self.assertIn("loaded_xid_trace", missing_codes)
            self.assertNotIn("knowledge_search_trace", missing_codes)

    def test_dashboard_ignores_mismatched_audit_identity_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_log = self._write_closed_run(root)
            run_id = next(line.split("`")[1] for line in run_log.read_text(encoding="utf-8").splitlines() if line.startswith("- run_id:"))
            self._run_main([
                "skill", "correlate", "--log", str(run_log), "--run-id", run_id,
                "--mcp-session-id", "mcp-1", "--repository-fingerprint", "repo-1",
            ])
            self._run_main([
                "skill", "knowledge", "--log", str(run_log), "--action", "load",
                "--xid", "local-service-map-001", "--content-hash", "local-hash",
            ])
            audit_path = root / "work" / "mcp" / "xid_audit.jsonl"
            audit_path.parent.mkdir(parents=True)
            events = [
                {"schema": "xrefkit.mcp_audit/v1", "event_type": "run.bound", "run_id": run_id, "mcp_session_id": "mcp-1", "repository_fingerprint": "repo-1", "skill_id": "sample_skill"},
                {"schema": "xrefkit.mcp_audit/v1", "event_type": "xid.resolved", "run_id": run_id, "mcp_session_id": "mcp-1", "repository_fingerprint": "repo-1", "skill_id": "sample_skill", "xid": "local-service-map-001", "content_hash": "server-hash"},
                {"schema": "xrefkit.mcp_audit/v1", "event_type": "xid.resolved", "run_id": run_id, "mcp_session_id": "other-session", "repository_fingerprint": "repo-1", "skill_id": "sample_skill", "xid": "forged-xid", "content_hash": "forged-hash"},
            ]
            audit_path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")

            payload = build_payload(root, root / "work" / "sessions", audit_path)
            run = payload["runs"][0]
            self.assertEqual(["local-service-map-001"], run["queried_xids"])
            self.assertEqual(["local-service-map-001"], run["queried_not_loaded_xids"])
            self.assertIn("mismatched correlation identity", "\n".join(payload["audit_errors"]))

    def test_dashboard_reports_unreadable_audit_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audit-directory"
            path.mkdir()

            by_run, errors = _load_mcp_audit(path)

            self.assertEqual({}, by_run)
            self.assertIn("cannot read audit log", errors[0])

    def test_dashboard_payload_includes_proposal_only_boundary_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_closed_run(root)

            payload = build_payload(root, root / "work" / "sessions")
            analysis = payload["boundary_analysis"]

            self.assertIsInstance(analysis, dict)
            self.assertEqual("xrefkit.boundary_observation/v1", analysis["schema"])
            self.assertEqual("proposal_only", analysis["status"])
            self.assertEqual(1, analysis["sample_count"])
            self.assertEqual(0, analysis["summary"]["proposals"])

    def test_dashboard_html_splits_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_closed_run(root)

            html = _html_page(build_payload(root, root / "work" / "sessions"))

            self.assertIn('data-panel="overview"', html)
            self.assertIn('data-panel="flows"', html)
            self.assertIn('data-panel="attention"', html)
            self.assertIn('data-panel="closure"', html)
            self.assertIn('data-panel="evidence"', html)
            self.assertIn('data-panel="handoff"', html)
            self.assertIn('data-panel="xids"', html)
            self.assertIn('data-panel="analysis"', html)
            self.assertIn('data-panel="missing-information"', html)
            self.assertIn('id="overview"', html)
            self.assertIn('id="flows"', html)
            self.assertIn("Execution tree", html)
            self.assertIn("Flow details", html)
            self.assertIn("Work Item", html)
            self.assertIn("Minimum intake", html)
            self.assertIn("State", html)
            self.assertIn("Execution records", html)
            self.assertIn("Activity", html)
            self.assertIn("Evidence and concerns", html)
            self.assertIn('id="attention"', html)
            self.assertIn('id="closure"', html)
            self.assertIn('id="evidence"', html)
            self.assertIn('id="handoff"', html)
            self.assertIn('id="xids"', html)
            self.assertIn('id="analysis"', html)
            self.assertIn('id="missing-information"', html)
            self.assertIn("Proposal-only analysis", html)
            self.assertIn("No boundary proposals reached", html)
            self.assertIn("Missing Information Ranking", html)
            self.assertIn("Available Knowledge XIDs (base/local)", html)
            self.assertIn("local-service-map-001", html)
            self.assertIn("LOCAL-KNOWLEDGE-UNUSED-001", html)
            self.assertIn('id="run-search"', html)
            self.assertIn('data-status="blocked"', html)
            self.assertIn('id="refresh-runs"', html)
            self.assertIn("async function refreshDashboard()", html)
            self.assertIn("selectRun(run.dataset.runPath)", html)
            self.assertIn("data-run-path=", html)

    def test_dashboard_html_search_index_contains_run_correlation_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_closed_run(root)

            payload = build_payload(root, root / "work" / "sessions")
            run_id = payload["runs"][0]["run_id"]
            html = _html_page(payload)

            self.assertIsNotNone(run_id)
            self.assertIn(str(run_id).lower(), html)
            self.assertIn("sample_skill", html)

    def test_dashboard_html_escapes_boundary_proposal_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_closed_run(root)

            payload = build_payload(root, root / "work" / "sessions")
            payload["boundary_analysis"]["summary"]["proposals"] = 1
            payload["boundary_analysis"]["proposals"] = [
                {
                    "proposal_id": "bo-test",
                    "proposal": "investigate",
                    "category": "skill_correction",
                    "skill_ids": ["sample_skill"],
                    "subject_xids": ["xid-test"],
                    "support": 2,
                    "evidence_refs": ["<script>alert(1)</script>"],
                    "rationale": "<script>alert(2)</script>",
                    "counterevidence": ["counter"],
                    "unknowns": ["unknown"],
                    "verification_plan": ["verify"],
                    "decision": {"status": "pending", "owner": None},
                }
            ]

            html = _html_page(payload)

            self.assertIn("bo-test", html)
            self.assertIn("Counterevidence", html)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
            self.assertIn("&lt;script&gt;alert(2)&lt;/script&gt;", html)
            self.assertNotIn("<script>alert(1)", html)

    def test_dashboard_includes_decision_trace_panel_and_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / "work" / "decision-trace" / "events.jsonl"
            ledger.parent.mkdir(parents=True, exist_ok=True)
            ledger.write_text(
                json.dumps({
                    "recorded_by": "ai_protocol",
                    "event_id": "DEC-001",
                    "event_type": "decision-change",
                    "status": "provisional",
                    "resolution": None,
                    "reason": "try Y",
                    "depends_on": [],
                    "branch": "hypothesis/decision-Y",
                }) + "\n",
                encoding="utf-8",
            )
            payload = build_payload(root, root / "work" / "sessions")
            html = _html_page(payload)

            self.assertEqual(payload["decision_trace"]["summary"]["events"], 1)
            self.assertEqual(payload["decision_trace"]["summary"]["groups"], {"decision": 1})
            self.assertIn('data-panel="decision-trace"', html)
            self.assertIn('id="decision-trace"', html)
            self.assertIn("DEC-001", html)
            self.assertIn("hypothesis/decision-Y", html)
            self.assertIn("Dependency graph (Mermaid)", html)
            self.assertIn("Impact groups", html)

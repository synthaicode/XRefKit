import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fm.__main__ import main
from fm.dashboard import _html_page, build_payload
from fm.skillmeta import GUARD_CAPABILITY_REF, GUARD_KNOWLEDGE_REF, REQUIRED_OS_CONTRACT, SKILL_RUNTIME_CAPABILITY_REF


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
            self.assertEqual(["local-service-map-001"], payload["runs"][0]["used_xids"])
            self.assertEqual(["LOCAL-KNOWLEDGE-UNUSED-001"], payload["runs"][0]["unused_xids"])
            self.assertEqual("LOCAL-KNOWLEDGE-UNUSED-001", payload["unused_xid_ranking"][0]["xid"])
            self.assertEqual(run_log.relative_to(root).as_posix(), payload["runs"][0]["path"])

    def test_dashboard_data_command_emits_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_closed_run(root)

            output = self._run_main(["dashboard", "data", "--root", str(root)])
            payload = json.loads(output)

            self.assertEqual(1, payload["summary"]["runs"])
            self.assertEqual("sample_skill", payload["runs"][0]["skill_id"])

    def test_dashboard_html_splits_categories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_closed_run(root)

            html = _html_page(build_payload(root, root / "work" / "sessions"))

            self.assertIn('data-panel="overview"', html)
            self.assertIn('data-panel="attention"', html)
            self.assertIn('data-panel="closure"', html)
            self.assertIn('data-panel="evidence"', html)
            self.assertIn('data-panel="handoff"', html)
            self.assertIn('data-panel="xids"', html)
            self.assertIn('id="overview"', html)
            self.assertIn('id="attention"', html)
            self.assertIn('id="closure"', html)
            self.assertIn('id="evidence"', html)
            self.assertIn('id="handoff"', html)
            self.assertIn('id="xids"', html)
            self.assertIn("Available Knowledge XIDs (base/local)", html)
            self.assertIn("local-service-map-001", html)
            self.assertIn("LOCAL-KNOWLEDGE-UNUSED-001", html)

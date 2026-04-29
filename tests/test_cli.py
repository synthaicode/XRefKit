import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fm.__main__ import main
from fm.skillmeta import GUARD_CAPABILITY_REF, GUARD_KNOWLEDGE_REF, REQUIRED_OS_CONTRACT, SKILL_RUNTIME_CAPABILITY_REF


class CliTests(unittest.TestCase):
    def _valid_meta_text(self) -> str:
        os_contract = "".join(
            f"  - {key}: `{value}`\n" for key, value in REQUIRED_OS_CONTRACT.items()
        )
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
            "  - `../../work/sessions/sample.md`\n"
        )

    def _write_valid_skill(self, root: Path) -> Path:
        meta = root / "skills" / "sample" / "meta.md"
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text(self._valid_meta_text(), encoding="utf-8")
        (meta.parent / "SKILL.md").write_text("# Sample Skill\n", encoding="utf-8")
        return meta

    def _write_completed_skill_run(self, root: Path) -> Path:
        self._write_valid_skill(root)
        out = root / "work" / "sessions" / "run.md"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                0,
                main(
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
                    ]
                ),
            )
            self.assertEqual(
                0,
                main(
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
                ),
            )
            for artifact_id, kind, target, role in (
                ("OUT-001", "output", "docs/output.md", "sample_skill:executor"),
                ("EVD-001", "evidence", "python tools/run_quality_gate.py fm", "sample_skill:checker"),
            ):
                self.assertEqual(
                    0,
                    main(
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
                    ),
                )
            for phase, role in (
                ("execution", "sample_skill:executor"),
                ("check", "sample_skill:checker"),
                ("handoff", "sample_skill:handoff_owner"),
            ):
                self.assertEqual(
                    0,
                    main(
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
                    ),
                )
        return out

    def _write_second_valid_skill(self, root: Path) -> Path:
        meta = root / "skills" / "receiver" / "meta.md"
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text(self._valid_meta_text().replace("sample_skill", "receiver_skill"), encoding="utf-8")
        (meta.parent / "SKILL.md").write_text("# Receiver Skill\n", encoding="utf-8")
        return meta

    def test_main_xref_check_json_returns_zero_and_emits_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "docs" / "ok.md"
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text(
                "<!-- xid: OK1234567890 -->\n<a id=\"xid-OK1234567890\"></a>\n\n# Ok\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["xref", "check", "--root", str(root), "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertEqual(1, payload["index_size"])
            self.assertEqual([], payload["missing_xid"])
            self.assertEqual([], payload["issues"])

    def test_main_xref_show_json_returns_one_for_missing_xid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "docs" / "ok.md"
            doc.parent.mkdir(parents=True, exist_ok=True)
            doc.write_text(
                "<!-- xid: OK1234567890 -->\n<a id=\"xid-OK1234567890\"></a>\n\n# Ok\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["xref", "show", "--root", str(root), "--json", "MISSING12345"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertEqual("xid_not_found", payload["error"])

    def test_main_skill_check_json_reports_invalid_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta = root / "meta.md"
            meta.write_text(
                "# Skill Meta: broken\n\n"
                "- skill_id: `broken_skill`\n"
                "- execution_mode: `local_default`\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["skill", "check", "--root", str(root), "--meta", "meta.md", "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertEqual(1, len(payload))
            self.assertFalse(payload[0]["ok"])
            self.assertIn("missing skill_doc", payload[0]["errors"])

    def test_main_skill_check_draft_level_accepts_minimum_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta = root / "meta.md"
            meta.write_text(
                "# Skill Meta: draft\n\n"
                "- skill_id: `draft_skill`\n"
                "- summary: draft summary\n"
                "- use_when: early use hypothesis\n"
                "- input: rough input\n"
                "- output: rough output\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `draft`\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    ["skill", "check", "--root", str(root), "--meta", "meta.md", "--level", "draft", "--json"]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertTrue(payload[0]["ok"])
            self.assertEqual("draft", payload[0]["checked_level"])

    def test_main_skill_run_writes_runtime_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            out = root / "work" / "sessions" / "run.md"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
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
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertTrue(payload["ok"])
            self.assertTrue(str(payload["skill_doc"]).endswith("SKILL.md"))
            self.assertEqual("sample_skill:executor", payload["assigned_roles"]["executor"])
            self.assertEqual("sample_skill:checker", payload["assigned_roles"]["checker"])
            self.assertTrue(out.exists())
            text = out.read_text(encoding="utf-8")
            self.assertIn("## Skill Load Gate", text)
            self.assertIn("## Runtime Role Assignment", text)
            self.assertIn("## Worklist", text)
            self.assertIn("## Concrete Work Items", text)
            self.assertIn("## Runtime Artifacts", text)
            self.assertIn("## Execution Role", text)
            self.assertIn("## Check Role", text)
            self.assertIn("## Closure Gate", text)
            self.assertIn("Create a controlled output", text)
            self.assertIn("- maturity: `stable`", text)
            self.assertIn("## Startup Inputs", text)
            self.assertIn("- none", text)

    def test_main_skill_run_rejects_unclosed_handoff_source_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            self._write_second_valid_skill(root)
            source = root / "work" / "sessions" / "source.md"
            out = root / "work" / "sessions" / "receiver.md"

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
                        [
                            "skill",
                            "run",
                            "--root",
                            str(root),
                            "--meta",
                            "skills/sample/meta.md",
                            "--task",
                            "Produce a source handoff",
                            "--out",
                            str(source),
                        ]
                    ),
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "skill",
                        "run",
                        "--root",
                        str(root),
                        "--meta",
                        "skills/receiver/meta.md",
                        "--task",
                        "Consume the handoff",
                        "--out",
                        str(out),
                        "--handoff-source-log",
                        str(source),
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertIn("handoff source log must have Closure Gate done or escalated before startup", payload["errors"][0])

    def test_main_skill_run_accepts_closed_handoff_source_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_completed_skill_run(root)
            self._write_second_valid_skill(root)
            out = root / "work" / "sessions" / "receiver.md"

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["skill", "close", "--log", str(source)]))

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "skill",
                        "run",
                        "--root",
                        str(root),
                        "--meta",
                        "skills/receiver/meta.md",
                        "--task",
                        "Consume the closed handoff",
                        "--out",
                        str(out),
                        "--handoff-source-log",
                        str(source),
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertTrue(payload["ok"])
            self.assertEqual(1, len(payload["handoff_sources"]))
            text = out.read_text(encoding="utf-8")
            self.assertIn("## Startup Inputs", text)
            self.assertIn("source_log: `work/sessions/run.md`", text)
            self.assertIn("closure=`done`", text)

    def test_main_skill_run_rejects_invalid_meta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta = root / "skills" / "sample" / "meta.md"
            meta.parent.mkdir(parents=True, exist_ok=True)
            meta.write_text(
                "# Skill Meta: broken\n\n"
                "- skill_id: `broken_skill`\n"
                "- execution_mode: `local_default`\n",
                encoding="utf-8",
            )
            out = root / "work" / "sessions" / "run.md"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
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
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertFalse(out.exists())
            self.assertIn("missing skill_doc", payload["errors"])

    def test_main_skill_run_rejects_draft_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta = root / "skills" / "sample" / "meta.md"
            meta.parent.mkdir(parents=True, exist_ok=True)
            meta.write_text(
                "# Skill Meta: draft\n\n"
                "- skill_id: `draft_skill`\n"
                "- summary: draft summary\n"
                "- use_when: early use hypothesis\n"
                "- input: rough input\n"
                "- output: rough output\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `draft`\n",
                encoding="utf-8",
            )
            (meta.parent / "SKILL.md").write_text("# Draft Skill\n", encoding="utf-8")
            out = root / "work" / "sessions" / "run.md"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "skill",
                        "run",
                        "--root",
                        str(root),
                        "--meta",
                        "skills/sample/meta.md",
                        "--task",
                        "Try a draft skill",
                        "--out",
                        str(out),
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertIn("draft skills are not load-ready", payload["errors"][0])

    def test_main_skill_run_accepts_trial_skill_with_provisional_runtime_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta = root / "skills" / "sample" / "meta.md"
            meta.parent.mkdir(parents=True, exist_ok=True)
            meta.write_text(
                "# Skill Meta: trial\n\n"
                "- skill_id: `trial_skill`\n"
                "- summary: trial summary\n"
                "- use_when: observed use hypothesis\n"
                "- input: observed input hypothesis\n"
                "- output: observed output hypothesis\n"
                "- skill_doc: `./SKILL.md`\n"
                "- maturity: `trial`\n",
                encoding="utf-8",
            )
            (meta.parent / "SKILL.md").write_text("# Trial Skill\n", encoding="utf-8")
            out = root / "work" / "sessions" / "run.md"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "skill",
                        "run",
                        "--root",
                        str(root),
                        "--meta",
                        "skills/sample/meta.md",
                        "--task",
                        "Observe a trial skill",
                        "--out",
                        str(out),
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertTrue(payload["ok"])
            text = out.read_text(encoding="utf-8")
            self.assertIn("- maturity: `trial`", text)
            self.assertIn("- guard_policy: `required`", text)
            self.assertIn("- execution_mode: `local_default`", text)

    def test_main_skill_phase_updates_runtime_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            out = root / "work" / "sessions" / "run.md"

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
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
                        ]
                    ),
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "skill",
                        "phase",
                        "--log",
                        str(out),
                        "--phase",
                        "execution",
                        "--status",
                        "done",
                        "--role",
                        "sample_skill:executor",
                        "--note",
                        "executor completed work items",
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertTrue(payload["ok"])
            text = out.read_text(encoding="utf-8")
            self.assertIn("- [x] Execution:", text)
            self.assertIn("## Execution Role\n\n- status: `done`", text)
            self.assertIn("`execution` -> `done` role=`sample_skill:executor`: executor completed work items", text)

    def test_main_skill_phase_rejects_wrong_runtime_role(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            out = root / "work" / "sessions" / "run.md"

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
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
                        ]
                    ),
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "skill",
                        "phase",
                        "--log",
                        str(out),
                        "--phase",
                        "check",
                        "--status",
                        "done",
                        "--role",
                        "sample_skill:executor",
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertIn("check phase requires role sample_skill:checker", payload["errors"][0])

    def test_main_skill_run_rejects_missing_skill_doc_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            meta = root / "skills" / "sample" / "meta.md"
            meta.parent.mkdir(parents=True, exist_ok=True)
            meta.write_text(self._valid_meta_text(), encoding="utf-8")
            out = root / "work" / "sessions" / "run.md"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
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
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertFalse(out.exists())
            self.assertIn("skill_doc not found", payload["errors"][0])

    def test_main_skill_phase_rejects_missing_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.md"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "skill",
                        "phase",
                        "--log",
                        str(missing),
                        "--phase",
                        "execution",
                        "--status",
                        "done",
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertIn("log not found", payload["errors"][0])

    def test_main_skill_workitem_adds_and_updates_concrete_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            out = root / "work" / "sessions" / "run.md"

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
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
                        ]
                    ),
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
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
                        "in_progress",
                        "--role",
                        "sample_skill:executor",
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertTrue(payload["ok"])
            self.assertEqual("WI-001", payload["work_items"][0]["item_id"])

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
                        [
                            "skill",
                            "workitem",
                            "--log",
                            str(out),
                            "--item",
                            "WI-001",
                            "--status",
                            "done",
                            "--role",
                            "sample_skill:executor",
                        ]
                    ),
                )

            text = out.read_text(encoding="utf-8")
            self.assertIn("- [x] WI-001 status=`done` role=`sample_skill:executor`: Implement controlled output", text)

    def test_main_skill_close_rejects_pending_concrete_work_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            out = root / "work" / "sessions" / "run.md"

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
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
                        ]
                    ),
                )
                self.assertEqual(
                    0,
                    main(
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
                            "pending",
                            "--role",
                            "sample_skill:executor",
                        ]
                    ),
                )
                phase_roles = {
                    "execution": "sample_skill:executor",
                    "check": "sample_skill:checker",
                    "handoff": "sample_skill:handoff_owner",
                }
                for phase, role in phase_roles.items():
                    self.assertEqual(
                        0,
                        main(
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
                        ),
                    )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["skill", "close", "--log", str(out), "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertTrue(
                any("work item WI-001 must be done or escalated" in error for error in payload["errors"])
            )

    def test_main_skill_artifact_adds_structured_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            out = root / "work" / "sessions" / "run.md"

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
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
                        ]
                    ),
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "skill",
                        "artifact",
                        "--log",
                        str(out),
                        "--artifact",
                        "OUT-001",
                        "--kind",
                        "output",
                        "--target",
                        "docs/output.md",
                        "--item",
                        "WI-001",
                        "--status",
                        "done",
                        "--role",
                        "sample_skill:executor",
                        "--note",
                        "created output document",
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertTrue(payload["ok"])
            self.assertEqual("OUT-001", payload["artifacts"][0]["artifact_id"])
            text = out.read_text(encoding="utf-8")
            self.assertIn("- [x] OUT-001 kind=`output` status=`done` role=`sample_skill:executor` target=`docs/output.md` item=`WI-001`: created output document", text)

    def test_main_skill_close_rejects_missing_runtime_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            out = root / "work" / "sessions" / "run.md"

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
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
                        ]
                    ),
                )
                self.assertEqual(
                    0,
                    main(
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
                    ),
                )
                phase_roles = {
                    "execution": "sample_skill:executor",
                    "check": "sample_skill:checker",
                    "handoff": "sample_skill:handoff_owner",
                }
                for phase, role in phase_roles.items():
                    self.assertEqual(
                        0,
                        main(
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
                        ),
                    )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["skill", "close", "--log", str(out), "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertIn("at least one output artifact is required before closure", payload["errors"])
            self.assertIn("at least one evidence artifact is required before closure", payload["errors"])

    def test_main_skill_close_rejects_incomplete_runtime_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            out = root / "work" / "sessions" / "run.md"

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
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
                        ]
                    ),
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["skill", "close", "--log", str(out), "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertIn("Execution Role must be done or escalated", payload["errors"][0])

    def test_main_skill_close_rejects_unresolved_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._write_completed_skill_run(Path(tmp))

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
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
                            "open",
                            "--text",
                            "Source boundary is not confirmed",
                            "--role",
                            "sample_skill:checker",
                        ]
                    ),
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["skill", "close", "--log", str(out), "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertIn("unresolved unknowns block closure: UNK-001", payload["errors"])
            self.assertEqual("failed", payload["closure_checks"]["unknown"])

    def test_main_skill_close_allows_escalated_risk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._write_completed_skill_run(Path(tmp))

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
                        [
                            "skill",
                            "concern",
                            "--log",
                            str(out),
                            "--concern",
                            "RSK-001",
                            "--kind",
                            "risk",
                            "--status",
                            "escalated",
                            "--text",
                            "Residual schedule risk needs owner acceptance",
                            "--role",
                            "sample_skill:checker",
                        ]
                    ),
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["skill", "close", "--log", str(out), "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertTrue(payload["ok"])
            self.assertEqual("passed", payload["closure_checks"]["risk"])
            self.assertEqual("RSK-001", payload["closure_checks"]["escalated_risks"])

    def test_main_skill_close_rejects_unlinked_non_trivial_judgment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._write_completed_skill_run(Path(tmp))

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
                        [
                            "skill",
                            "concern",
                            "--log",
                            str(out),
                            "--concern",
                            "JDG-001",
                            "--kind",
                            "judgment",
                            "--status",
                            "resolved",
                            "--judgment",
                            "non_trivial",
                            "--text",
                            "Chose a minimal runtime register instead of broad schema redesign",
                            "--role",
                            "sample_skill:checker",
                        ]
                    ),
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["skill", "close", "--log", str(out), "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(1, exit_code)
            self.assertFalse(payload["ok"])
            self.assertIn(
                "non-trivial judgments require a judgment artifact or work/judgments/ reference before closure: JDG-001",
                payload["errors"],
            )
            self.assertEqual("failed", payload["closure_checks"]["judgment"])

    def test_main_skill_close_records_unknown_risk_judgment_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._write_completed_skill_run(Path(tmp))

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
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
                            "Source boundary confirmed",
                            "--role",
                            "sample_skill:checker",
                        ]
                    ),
                )
                self.assertEqual(
                    0,
                    main(
                        [
                            "skill",
                            "concern",
                            "--log",
                            str(out),
                            "--concern",
                            "JDG-001",
                            "--kind",
                            "judgment",
                            "--status",
                            "resolved",
                            "--judgment",
                            "non_trivial",
                            "--target",
                            "work/judgments/JDG-001.md",
                            "--text",
                            "Chose the closure linkage rule",
                            "--role",
                            "sample_skill:checker",
                        ]
                    ),
                )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["skill", "close", "--log", str(out), "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertTrue(payload["ok"])
            self.assertEqual(
                {
                    "unknown": "passed",
                    "risk": "passed",
                    "judgment": "passed",
                    "open_unknowns": "-",
                    "open_risks": "-",
                    "escalated_risks": "-",
                    "open_judgments": "-",
                    "non_trivial_judgments": "JDG-001",
                    "judgment_reference": "present",
                },
                payload["closure_checks"],
            )
            text = out.read_text(encoding="utf-8")
            self.assertIn("### Closure Checks", text)
            self.assertIn("- unknown: `passed` open=`-`", text)
            self.assertIn("- judgment: `passed` open=`-` non_trivial=`JDG-001` reference=`present`", text)

    def test_main_skill_close_accepts_completed_runtime_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            out = root / "work" / "sessions" / "run.md"

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
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
                        ]
                    ),
                )
                phase_roles = {
                    "execution": "sample_skill:executor",
                    "check": "sample_skill:checker",
                    "handoff": "sample_skill:handoff_owner",
                }
                self.assertEqual(
                    0,
                    main(
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
                    ),
                )
                for artifact_id, kind, target, role in (
                    ("OUT-001", "output", "docs/output.md", "sample_skill:executor"),
                    ("EVD-001", "evidence", "python tools/run_quality_gate.py fm", "sample_skill:checker"),
                ):
                    self.assertEqual(
                        0,
                        main(
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
                        ),
                    )
                for phase, role in phase_roles.items():
                    self.assertEqual(
                        0,
                        main(
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
                        ),
                    )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "skill",
                        "close",
                        "--log",
                        str(out),
                        "--note",
                        "closure gate accepted completed run",
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertTrue(payload["ok"])
            text = out.read_text(encoding="utf-8")
            self.assertIn("- [x] Closure:", text)
            self.assertIn("## Closure Gate\n\n- status: `done`", text)
            self.assertIn("`closure` -> `done` role=`closure_gate`: closure gate accepted completed run", text)


if __name__ == "__main__":
    unittest.main()

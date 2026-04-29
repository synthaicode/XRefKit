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
            "- execution_mode: `local_default`\n"
            "- guard_policy: `required`\n"
            "- os_contract:\n"
            f"{os_contract}"
            "- skill_doc: `./SKILL.md`\n"
            "- capability_refs:\n"
            f"  - `{SKILL_RUNTIME_CAPABILITY_REF}`\n"
            f"  - `{GUARD_CAPABILITY_REF}`\n"
            "- knowledge_refs:\n"
            f"  - `{GUARD_KNOWLEDGE_REF}`\n"
        )

    def _write_valid_skill(self, root: Path) -> Path:
        meta = root / "skills" / "sample" / "meta.md"
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text(self._valid_meta_text(), encoding="utf-8")
        (meta.parent / "SKILL.md").write_text("# Sample Skill\n", encoding="utf-8")
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
            self.assertTrue(out.exists())
            text = out.read_text(encoding="utf-8")
            self.assertIn("## Skill Load Gate", text)
            self.assertIn("## Worklist", text)
            self.assertIn("## Execution Role", text)
            self.assertIn("## Check Role", text)
            self.assertIn("## Closure Gate", text)
            self.assertIn("Create a controlled output", text)

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
            self.assertIn("`execution` -> `done`: executor completed work items", text)

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
                for phase in ("execution", "check", "handoff"):
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
            self.assertIn("`closure` -> `done`: closure gate accepted completed run", text)


if __name__ == "__main__":
    unittest.main()

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from fm.__main__ import main
from fm.skillmeta import GUARD_CAPABILITY_REF, GUARD_KNOWLEDGE_REF, REQUIRED_OS_CONTRACT, SKILL_RUNTIME_CAPABILITY_REF
from tools.audit_skill_runtime_logs import audit_skill_runtime_logs


class SkillRuntimeAuditTests(unittest.TestCase):
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
            "  - quality_reviewer: sample quality responsibility\n"
            "  - handoff_owner: sample handoff responsibility\n"
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
            "  - `../../work/sessions/sample.md`\n"
        )

    def _write_valid_skill(self, root: Path, model_tier: str | None = None) -> None:
        meta = root / "skills" / "sample" / "meta.md"
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text(self._valid_meta_text(model_tier=model_tier), encoding="utf-8")
        (meta.parent / "SKILL.md").write_text("# Sample Skill\n", encoding="utf-8")

    def _write_closed_skill_run(self, root: Path) -> Path:
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
            self.assertEqual(0, main(["skill", "close", "--log", str(out)]))
        return out

    def _open_run_through_execution(self, root: Path, *, with_artifacts: bool) -> Path:
        self._write_valid_skill(root)
        out = root / "work" / "sessions" / "run.md"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                0,
                main(
                    [
                        "skill", "run", "--root", str(root),
                        "--meta", "skills/sample/meta.md",
                        "--task", "Verify progression", "--out", str(out),
                    ]
                ),
            )
            self.assertEqual(
                0,
                main(
                    [
                        "skill", "workitem", "--log", str(out), "--item", "WI-001",
                        "--text", "Implement controlled output", "--status", "done",
                        "--role", "sample_skill:executor",
                    ]
                ),
            )
            if with_artifacts:
                for artifact_id, kind, target, role in (
                    ("OUT-001", "output", "docs/output.md", "sample_skill:executor"),
                    ("EVD-001", "evidence", "python tools/run_quality_gate.py fm", "sample_skill:checker"),
                ):
                    self.assertEqual(
                        0,
                        main(
                            [
                                "skill", "artifact", "--log", str(out),
                                "--artifact", artifact_id, "--kind", kind,
                                "--target", target, "--item", "WI-001",
                                "--status", "done", "--role", role,
                            ]
                        ),
                    )
            self.assertEqual(
                0,
                main(
                    [
                        "skill", "phase", "--log", str(out), "--phase", "execution",
                        "--status", "done", "--role", "sample_skill:executor",
                    ]
                ),
            )
        return out

    def test_verify_advances_check_when_progression_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = self._open_run_through_execution(root, with_artifacts=True)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["skill", "verify", "--log", str(out)]))

            log_text = out.read_text(encoding="utf-8")
            self.assertIn("`check` -> `done` role=`sample_skill:checker`", log_text)
            self.assertIn("## Check Role\n\n- status: `done`", log_text)

    def test_verify_blocks_when_artifact_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = self._open_run_through_execution(root, with_artifacts=False)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(1, main(["skill", "verify", "--log", str(out)]))

            log_text = out.read_text(encoding="utf-8")
            self.assertIn("`check` -> `blocked`", log_text)

    def _standard_run_ready_to_close(self, root: Path, *, with_quality: bool) -> Path:
        self._write_valid_skill(root, model_tier="standard")
        out = root / "work" / "sessions" / "run.md"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                0,
                main(
                    [
                        "skill", "run", "--root", str(root),
                        "--meta", "skills/sample/meta.md",
                        "--task", "Standard tier quality gate", "--out", str(out),
                    ]
                ),
            )
            self.assertEqual(
                0,
                main(
                    [
                        "skill", "workitem", "--log", str(out), "--item", "WI-001",
                        "--text", "do work", "--status", "done", "--role", "sample_skill:executor",
                    ]
                ),
            )
            artifacts = [
                ("OUT-001", "output", "docs/output.md", "sample_skill:executor"),
                ("EVD-001", "evidence", "python tools/run_quality_gate.py fm", "sample_skill:checker"),
            ]
            if with_quality:
                artifacts.append(("QC-001", "check", "output meets acceptance criteria", "sample_skill:quality_reviewer"))
            for artifact_id, kind, target, role in artifacts:
                self.assertEqual(
                    0,
                    main(
                        [
                            "skill", "artifact", "--log", str(out), "--artifact", artifact_id,
                            "--kind", kind, "--target", target, "--item", "WI-001",
                            "--status", "done", "--role", role,
                        ]
                    ),
                )
            phases = [
                ("execution", "sample_skill:executor"),
                ("check", "sample_skill:checker"),
            ]
            if with_quality:
                phases.append(("quality", "sample_skill:quality_reviewer"))
            phases.append(("handoff", "sample_skill:handoff_owner"))
            for phase, role in phases:
                self.assertEqual(
                    0,
                    main(
                        [
                            "skill", "phase", "--log", str(out), "--phase", phase,
                            "--status", "done", "--role", role,
                        ]
                    ),
                )
        return out

    def test_standard_tier_close_blocks_without_quality_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = self._standard_run_ready_to_close(root, with_quality=False)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(["skill", "close", "--log", str(out)])
            self.assertEqual(1, rc)
            output = buf.getvalue()
            self.assertIn("Quality Gate must be done or escalated", output)
            self.assertIn("acceptance check artifact is required", output)

    def test_standard_tier_close_passes_with_quality_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = self._standard_run_ready_to_close(root, with_quality=True)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["skill", "close", "--log", str(out)]))
            self.assertTrue(
                audit_skill_runtime_logs(root=root, sessions_dir=root / "work" / "sessions").ok
            )

    def test_audit_accepts_closed_skill_run_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_closed_skill_run(root)

            result = audit_skill_runtime_logs(root=root, sessions_dir=root / "work" / "sessions")

            self.assertTrue(result.ok)
            self.assertEqual(1, result.checked)
            self.assertEqual([], result.errors)

    def test_local_default_run_assigns_deterministic_checker(self) -> None:
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
                            "Checker context assignment",
                            "--out",
                            str(out),
                        ]
                    ),
                )

            log_text = out.read_text(encoding="utf-8")

            self.assertIn(
                "- checker_context: `deterministic_fm_verification`",
                log_text,
            )
            self.assertIn("- executor_context: `current_context_allowed`", log_text)

    def test_audit_rejects_skill_run_log_without_fm_load_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "work" / "sessions"
            sessions.mkdir(parents=True)
            bad = sessions / "bad.md"
            bad.write_text(
                "# Skill Run Log\n\n"
                "- skill_id: `sample_skill`\n\n"
                "## OS Contract\n\n"
                "- version: `1`\n\n"
                "## Closure Gate\n\n"
                "- status: `done`\n",
                encoding="utf-8",
            )

            result = audit_skill_runtime_logs(root=root, sessions_dir=sessions)

            self.assertFalse(result.ok)
            self.assertEqual(1, result.checked)
            self.assertIn("work/sessions/bad.md: missing fm skill run load gate", result.errors)

    def test_audit_rejects_unclosed_skill_run_log(self) -> None:
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
                            "Leave log open",
                            "--out",
                            str(out),
                        ]
                    ),
                )

            result = audit_skill_runtime_logs(root=root, sessions_dir=root / "work" / "sessions")

            self.assertFalse(result.ok)
            self.assertEqual(1, result.checked)
            self.assertIn(
                "work/sessions/run.md: Closure Gate must be done or escalated; current=pending",
                result.errors,
            )

    def test_audit_rejects_unresolved_concern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = self._write_closed_skill_run(root)
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
                            "Boundary is not confirmed",
                            "--role",
                            "sample_skill:checker",
                        ]
                    ),
                )

            result = audit_skill_runtime_logs(root=root, sessions_dir=root / "work" / "sessions")

            self.assertFalse(result.ok)
            self.assertEqual(1, result.checked)
            self.assertIn(
                "work/sessions/run.md: unresolved unknowns block closure: UNK-001",
                result.errors,
            )

    def _open_run(self, root: Path) -> Path:
        self._write_valid_skill(root)
        out = root / "work" / "sessions" / "run.md"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(
                0,
                main(
                    [
                        "skill", "run", "--root", str(root),
                        "--meta", "skills/sample/meta.md",
                        "--task", "Token usage", "--out", str(out),
                    ]
                ),
            )
        return out

    def test_skill_tokens_records_usage_and_defaults_total(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = self._open_run(root)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(["skill", "tokens", "--log", str(out), "--input", "1200", "--output", "3400"]),
                )

            log_text = out.read_text(encoding="utf-8")
            self.assertIn("## Token Usage\n\n- status: `recorded`", log_text)
            self.assertIn("- input: `1200`", log_text)
            self.assertIn("- output: `3400`", log_text)
            self.assertIn("- total: `4600`", log_text)
            self.assertIn("`tokens` -> `recorded`", log_text)

    def test_skill_tokens_requires_a_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = self._open_run(root)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(1, main(["skill", "tokens", "--log", str(out)]))
            self.assertIn("provide at least one of --input, --output, or --total", buf.getvalue())

    def test_skill_tokens_does_not_block_closure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # A closed run with no token usage recorded still passes the audit.
            self._write_closed_skill_run(root)
            self.assertTrue(
                audit_skill_runtime_logs(root=root, sessions_dir=root / "work" / "sessions").ok
            )


if __name__ == "__main__":
    unittest.main()

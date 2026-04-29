import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from fm.__main__ import main
from fm.skillmeta import GUARD_CAPABILITY_REF, GUARD_KNOWLEDGE_REF, REQUIRED_OS_CONTRACT, SKILL_RUNTIME_CAPABILITY_REF
from tools.audit_skill_runtime_logs import audit_skill_runtime_logs


class SkillRuntimeAuditTests(unittest.TestCase):
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

    def _write_valid_skill(self, root: Path) -> None:
        meta = root / "skills" / "sample" / "meta.md"
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text(self._valid_meta_text(), encoding="utf-8")
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

    def test_audit_accepts_closed_skill_run_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_closed_skill_run(root)

            result = audit_skill_runtime_logs(root=root, sessions_dir=root / "work" / "sessions")

            self.assertTrue(result.ok)
            self.assertEqual(1, result.checked)
            self.assertEqual([], result.errors)

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


if __name__ == "__main__":
    unittest.main()

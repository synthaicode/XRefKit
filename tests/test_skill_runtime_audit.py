import contextlib
import io
import re
import tempfile
import unittest
from pathlib import Path

from xrefkit.__main__ import main
from xrefkit.skillmeta import GUARD_CAPABILITY_REF, GUARD_KNOWLEDGE_REF, REQUIRED_OS_CONTRACT, SKILL_RUNTIME_CAPABILITY_REF
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
                        "--completion-criterion",
                        "output is written and validated",
                        "--status",
                        "done",
                        "--role",
                        "sample_skill:executor",
                    ]
                ),
            )
            for artifact_id, kind, target, role in (
                ("OUT-001", "output", "docs/output.md", "sample_skill:executor"),
                ("EVD-001", "evidence", "python tools/run_quality_gate.py xrefkit", "sample_skill:checker"),
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

    def test_skill_run_records_correlation_and_tuning_observations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            out = root / "work" / "sessions" / "run.md"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    0,
                    main(
                        [
                            "skill", "run", "--root", str(root),
                            "--meta", "skills/sample/meta.md",
                            "--task", "Record observations", "--out", str(out),
                        ]
                    ),
                )
            text = out.read_text(encoding="utf-8")
            run_id = re.search(r"^- run_id: `([^`]+)`", text, re.MULTILINE).group(1)

            commands = [
                [
                    "skill", "correlate", "--log", str(out), "--run-id", run_id,
                    "--mcp-session-id", "mcp-session-1",
                    "--repository-fingerprint", "repo-fingerprint-1",
                ],
                [
                    "skill", "routing", "--log", str(out),
                    "--selected-skill", "sample_skill", "--candidate", "sample_skill",
                    "--selection-mode", "semantic", "--reason", "best matching candidate",
                ],
                [
                    "skill", "knowledge", "--log", str(out), "--action", "search",
                    "--query", "service ownership", "--status", "hit", "--xid", "ABC123456789",
                    "--source", "mcp",
                ],
                [
                    "skill", "knowledge", "--log", str(out), "--action", "load",
                    "--xid", "ABC123456789", "--content-hash", "sha256-value", "--source", "mcp",
                ],
                [
                    "skill", "artifact", "--log", str(out), "--artifact", "OUT-001",
                    "--kind", "output", "--status", "done", "--target", "review.md",
                    "--role", "sample_skill:executor",
                ],
                [
                    "skill", "knowledge", "--log", str(out), "--action", "apply",
                    "--xid", "ABC123456789", "--content-hash", "sha256-value",
                    "--target", "OUT-001", "--decisive",
                ],
                [
                    "skill", "feedback", "--log", str(out), "--kind", "human",
                    "--status", "accepted", "--target", "OUT-001", "--note", "accepted by owner",
                ],
                [
                    "skill", "feedback", "--log", str(out), "--kind", "outcome",
                    "--status", "successful", "--target", "deployment-1", "--note", "no regression",
                ],
            ]
            for command in commands:
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(0, main(command))

            text = out.read_text(encoding="utf-8")
            self.assertIn(f'- run_id: `{run_id}`', text)
            self.assertIn('- mcp_session_id: `mcp-session-1`', text)
            self.assertIn('- repository_fingerprint: `repo-fingerprint-1`', text)
            self.assertIn('"event":"skill.routed"', text)
            self.assertIn('"event":"knowledge.search"', text)
            self.assertIn('"event":"knowledge.loaded"', text)
            self.assertIn('"event":"knowledge.applied"', text)
            self.assertIn('"event":"human.feedback"', text)
            self.assertIn('"event":"outcome.feedback"', text)

    def test_correlation_rejects_rebinding_and_routing_to_another_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = self._open_run(root)
            run_id = re.search(r"^- run_id: `([^`]+)`", out.read_text(encoding="utf-8"), re.MULTILINE).group(1)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main([
                    "skill", "correlate", "--log", str(out), "--run-id", run_id,
                    "--mcp-session-id", "mcp-1", "--repository-fingerprint", "repo-1",
                ]))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(1, main([
                    "skill", "correlate", "--log", str(out), "--run-id", run_id,
                    "--mcp-session-id", "mcp-2", "--repository-fingerprint", "repo-1",
                ]))
                self.assertEqual(1, main([
                    "skill", "routing", "--log", str(out), "--selected-skill", "other_skill",
                    "--candidate", "other_skill", "--reason", "incorrect run reuse",
                ]))
            self.assertIn("already correlated", output.getvalue())
            self.assertIn("must match the Skill Run skill_id", output.getvalue())

    def test_knowledge_apply_requires_loaded_hash_and_known_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = self._open_run(root)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main([
                    "skill", "artifact", "--log", str(out), "--artifact", "OUT-001",
                    "--kind", "output", "--status", "done", "--target", "review.md",
                    "--role", "sample_skill:executor",
                ]))
                self.assertEqual(0, main([
                    "skill", "knowledge", "--log", str(out), "--action", "load",
                    "--xid", "ABC123456789", "--content-hash", "hash-1",
                ]))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(1, main([
                    "skill", "knowledge", "--log", str(out), "--action", "apply",
                    "--xid", "ABC123456789", "--content-hash", "hash-2", "--target", "OUT-001",
                ]))
                self.assertEqual(1, main([
                    "skill", "knowledge", "--log", str(out), "--action", "apply",
                    "--xid", "ABC123456789", "--content-hash", "hash-1", "--target", "OUT-404",
                ]))
                self.assertEqual(0, main([
                    "skill", "knowledge", "--log", str(out), "--action", "apply",
                    "--xid", "ABC123456789", "--content-hash", "hash-1", "--target", "OUT-001",
                ]))
            self.assertIn("prior knowledge.loaded", output.getvalue())
            self.assertIn("existing artifact or concern", output.getvalue())

    def test_observation_commands_return_structured_error_for_unreadable_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "not-a-log"
            log_path.mkdir()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(1, main([
                    "skill", "correlate", "--log", str(log_path),
                    "--mcp-session-id", "mcp-1", "--repository-fingerprint", "repo-1",
                ]))
            self.assertIn("could not read skill run log", output.getvalue())

    def test_skill_run_rejects_duplicate_caller_supplied_run_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_valid_skill(root)
            run_id = "d4c0ca07-ec6c-48f9-b296-ec735323b088"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main([
                    "skill", "run", "--root", str(root), "--meta", "skills/sample/meta.md",
                    "--task", "first", "--out", str(root / "work" / "sessions" / "first.md"),
                    "--run-id", run_id,
                ]))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(1, main([
                    "skill", "run", "--root", str(root), "--meta", "skills/sample/meta.md",
                    "--task", "second", "--out", str(root / "work" / "sessions" / "second.md"),
                    "--run-id", run_id,
                ]))
            self.assertIn("run_id is already used", output.getvalue())

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
                        "--completion-criterion", "output is written and validated",
                        "--role", "sample_skill:executor",
                    ]
                ),
            )
            if with_artifacts:
                for artifact_id, kind, target, role in (
                    ("OUT-001", "output", "docs/output.md", "sample_skill:executor"),
                    ("EVD-001", "evidence", "python tools/run_quality_gate.py xrefkit", "sample_skill:checker"),
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
                        "--text", "do work", "--status", "done", "--completion-criterion", "work is verified", "--role", "sample_skill:executor",
                    ]
                ),
            )
            artifacts = [
                ("OUT-001", "output", "docs/output.md", "sample_skill:executor"),
                ("EVD-001", "evidence", "python tools/run_quality_gate.py xrefkit", "sample_skill:checker"),
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
                "- checker_context: `deterministic_xrefkit_verification`",
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
            self.assertIn("work/sessions/bad.md: missing xrefkit skill run load gate", result.errors)

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

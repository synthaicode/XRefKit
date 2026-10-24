import contextlib
import io
import re
import tempfile
import unittest
from pathlib import Path

from xrefkit import skillrun
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

    def test_quality_report_cli_posix_path_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = self._open_run_through_execution(Path(tmp), with_artifacts=True)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main([
                    "skill", "artifact", "--log", str(out),
                    "--artifact", "QC-POSIX", "--kind", "check",
                    "--target", "/tmp/quality report.md", "--item", "WI-001",
                    "--status", "done", "--role", "sample_skill:quality_reviewer",
                ]))
            self.assertIn("target=`/tmp/quality report.md`", out.read_text(encoding="utf-8"))

    def test_quality_report_cli_preserves_literal_paths_after_newline_read(self) -> None:
        targets = (
            r"C:\Users\Example\report.md",
            r"C:\Temp\test.md",
            r"C:\temp\report.md",
            r"C:\Users\Example\品質 レポート\report.md",
            "/tmp/quality report.md",
        )
        for target in targets:
            for newline in ("\n", "\r\n"):
                with self.subTest(target=target, newline=repr(newline)):
                    with tempfile.TemporaryDirectory() as tmp:
                        out = self._open_run_through_execution(Path(tmp), with_artifacts=True)
                        with contextlib.redirect_stdout(io.StringIO()):
                            self.assertEqual(0, main([
                                "skill", "artifact", "--log", str(out),
                                "--artifact", "QC-PRIOR", "--kind", "check",
                                "--target", "docs/prior-check.md", "--item", "WI-001",
                                "--status", "blocked", "--role", "sample_skill:quality_reviewer",
                                "--note", "Prior acceptance decision",
                            ]))
                        before = out.read_text(encoding="utf-8")
                        out.write_bytes(before.replace("\n", newline).encode("utf-8"))
                        with contextlib.redirect_stdout(io.StringIO()):
                            self.assertEqual(0, main([
                                "skill", "artifact", "--log", str(out),
                                "--artifact", "QC-LITERAL", "--kind", "check",
                                "--target", target, "--item", "WI-001",
                                "--status", "done", "--role", "sample_skill:quality_reviewer",
                                "--note", "Literal path acceptance",
                            ]))
                        # Path.read_text is the CLI's universal-newline input contract.
                        after = out.read_text(encoding="utf-8")
                        self.assertIn(f"target=`{target}`", after)
                        self.assertIn(
                            f"| QC-LITERAL | Literal path acceptance | {target} | pass | "
                            "[QC-LITERAL](#runtime-artifacts) |", after,
                        )
                        self.assertIn(
                            "| QC-PRIOR | Prior acceptance decision | docs/prior-check.md | fail | "
                            "[QC-PRIOR](#runtime-artifacts) |", after,
                        )
                        self.assertIn("\n\n## Unknowns And Risks\n", after)
                        self.assertEqual(before.count("\n## "), after.count("\n## "))
                        self.assertEqual(
                            before.split("## Runtime Artifacts\n", 1)[0],
                            after.split("## Runtime Artifacts\n", 1)[0],
                        )
                        self.assertEqual(
                            before.split("## Quality Gate\n", 1)[1].split("### Report\n", 1)[0],
                            after.split("## Quality Gate\n", 1)[1].split("### Report\n", 1)[0],
                        )
                        self.assertIn(
                            "QC-PRIOR kind=`check` status=`blocked` "
                            "role=`sample_skill:quality_reviewer` target=`docs/prior-check.md` "
                            "item=`WI-001`: Prior acceptance decision", after,
                        )
                        for artifact_id, target_ref in (
                            ("OUT-001", "docs/output.md"),
                            ("EVD-001", "python tools/run_quality_gate.py xrefkit"),
                        ):
                            self.assertIn(artifact_id, after)
                            self.assertIn(f"target=`{target_ref}`", after)
                        before_sections = dict(re.findall(
                            r"(?ms)(^## [^\n]+\n)(.*?)(?=^## |\Z)", before,
                        ))
                        after_sections = dict(re.findall(
                            r"(?ms)(^## [^\n]+\n)(.*?)(?=^## |\Z)", after,
                        ))
                        for heading, body in before_sections.items():
                            if heading == "## Operation Observations\n":
                                self.assertTrue(after_sections[heading].startswith(body), heading)
                            elif heading not in {"## Runtime Artifacts\n", "## Quality Gate\n", "## Phase Events\n"}:
                                self.assertEqual(body, after_sections[heading], heading)
                        self.assertEqual(after, skillrun._refresh_quality_report(after))

    def test_quality_report_multiple_markers_stay_in_bounded_section(self) -> None:
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                with tempfile.TemporaryDirectory() as tmp:
                    out = self._open_run_through_execution(Path(tmp), with_artifacts=True)
                    target = r"C:\Users\Example\品質 レポート\report.md"
                    with contextlib.redirect_stdout(io.StringIO()):
                        for artifact_id, status, path in (
                            ("QC-PRIOR", "blocked", "docs/prior-check.md"),
                            ("QC-LITERAL", "done", target),
                        ):
                            self.assertEqual(0, main([
                                "skill", "artifact", "--log", str(out),
                                "--artifact", artifact_id, "--kind", "check",
                                "--target", path, "--item", "WI-001", "--status", status,
                                "--role", "sample_skill:quality_reviewer", "--note", artifact_id,
                            ]))
                    log_text = out.read_text(encoding="utf-8")
                    prefix, boundary, suffix = log_text.partition("\n## Unknowns And Risks\n")
                    self.assertTrue(boundary)
                    fixture = (
                        "### Report\n\nOutside prefix marker\n\n" + prefix
                        + "### Report\n\nDuplicate report marker inside Quality Gate.\n\n"
                        + boundary + suffix
                        + "\n## Outside Report\n\n### Report\n\nOutside suffix marker\n"
                    )
                    # Exercise the CLI's existing universal-newline read contract.
                    out.write_bytes(fixture.replace("\n", newline).encode("utf-8"))
                    before = out.read_text(encoding="utf-8")
                    quality_before, start, end = skillrun._section_body(before, "Quality Gate")
                    self.assertIsNotNone(quality_before)
                    self.assertEqual(2, quality_before.count("### Report\n"))
                    updated = skillrun._refresh_quality_report(before)
                    quality_after, updated_start, updated_end = skillrun._section_body(updated, "Quality Gate")
                    self.assertIsNotNone(quality_after)
                    self.assertEqual(1, quality_after.count("### Report\n"))
                    self.assertEqual(before[:start], updated[:updated_start])
                    self.assertEqual(before[end:], updated[updated_end:])
                    self.assertEqual(
                        quality_before.split("### Report\n", 1)[0],
                        quality_after.split("### Report\n", 1)[0],
                    )
                    self.assertEqual(before.count("### Report\n") - 1, updated.count("### Report\n"))
                    self.assertIn("\n\n## Unknowns And Risks\n", updated)
                    self.assertNotIn("Duplicate report marker inside Quality Gate.", updated)
                    for artifact_id, path, result in (
                        ("QC-PRIOR", "docs/prior-check.md", "fail"),
                        ("QC-LITERAL", target, "pass"),
                    ):
                        self.assertIn(
                            f"| {artifact_id} | {artifact_id} | {path} | {result} | "
                            f"[{artifact_id}](#runtime-artifacts) |", quality_after,
                        )
                    self.assertEqual(updated, skillrun._refresh_quality_report(updated))

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




class OperationObservationTests(unittest.TestCase):
    _valid_meta_text = SkillRuntimeAuditTests._valid_meta_text
    _write_valid_skill = SkillRuntimeAuditTests._write_valid_skill

    def setUp(self):
        import json
        self.json = json
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self._write_valid_skill(self.root)
        self.log = self.root / "work/sessions/run.md"
        code, result = self.call("run", "--root", str(self.root), "--meta", "skills/sample/meta.md",
                                 "--task", "Observe existing operations", "--out", str(self.log))
        self.assertEqual(0, code, result)

    def call(self, operation, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["skill", operation, *args, "--json"])
        return code, self.json.loads(output.getvalue())

    def item(self, status="in_progress", key=None):
        args = ["--log", str(self.log), "--item", "WI-1", "--text", "Task", "--completion-criterion",
                "Evidence recorded", "--status", status, "--role", "sample_skill:executor"]
        if key:
            args += ["--operation-key", key]
        return self.call("workitem", *args)

    def check(self, status="blocked", target="evidence.txt", key=None, artifact="CHK-1"):
        args = ["--log", str(self.log), "--artifact", artifact, "--kind", "check", "--status", status,
                "--target", target, "--item", "WI-1", "--role", "sample_skill:checker"]
        if key:
            args += ["--operation-key", key]
        return self.call("artifact", *args)

    def events(self):
        return skillrun._operation_observations(self.log.read_text(encoding="utf-8"))

    def test_automatic_open_and_concern_with_null_onset(self):
        self.assertEqual("run.opened", self.events()[0]["operation"])
        code, result = self.call("concern", "--log", str(self.log), "--concern", "UNK-1", "--kind", "unknown",
                                 "--status", "open", "--text", "Occurred yesterday", "--role", "sample_skill:executor")
        self.assertEqual(0, code, result)
        event = self.events()[-1]
        self.assertEqual("concern.state_recorded", event["operation"])
        self.assertEqual("UNK-1", event["facts"]["subject_ref"])
        self.assertIsNone(event["facts"]["cognitive_onset_at"])
        self.assertIsNone(event["facts"]["occurred_at"])
        self.assertTrue(event["recorded_at"].endswith("+00:00"))
        self.assertEqual(event["event_id"], result["operation_receipt"]["event_id"])

    def test_stable_key_replay_preserves_bytes_receipt_and_rejects_mismatch(self):
        code, first = self.item(key="stable-1")
        self.assertEqual(0, code, first)
        before = self.log.read_bytes()
        code, second = self.item(key="stable-1")
        self.assertEqual(0, code, second)
        self.assertEqual(first["operation_receipt"], second["operation_receipt"])
        self.assertEqual(before, self.log.read_bytes())
        code, result = self.item(status="done", key="stable-1")
        self.assertEqual(1, code, result)
        self.assertIn("different payload", " ".join(result["errors"]))
        self.assertEqual(before, self.log.read_bytes())

    def test_invalid_key_and_missing_item_reject_before_native_mutation(self):
        before = self.log.read_bytes()
        code, _ = self.item(key="bad key")
        self.assertEqual(1, code)
        self.assertEqual(before, self.log.read_bytes())
        code, result = self.check(key="missing-item")
        self.assertEqual(1, code, result)
        self.assertEqual(before, self.log.read_bytes())

    def test_linked_concern_requires_existing_item(self):
        args = ["--log", str(self.log), "--concern", "UNK-1", "--kind", "unknown", "--status", "open",
                "--text", "Missing", "--role", "sample_skill:executor", "--item", "WI-1"]
        before = self.log.read_bytes()
        self.assertEqual(1, self.call("concern", *args)[0])
        self.assertEqual(before, self.log.read_bytes())
        self.item()
        self.assertEqual(0, self.call("concern", *args)[0])
        self.assertEqual("WI-1", self.events()[-1]["facts"]["work_item_id"])

    def test_work_state_intervals_and_reentry_are_operation_proxies(self):
        self.item()
        self.item(status="done")
        self.item()
        self.item(status="done")
        result = skillrun.summarize_observations(self.log)
        self.assertEqual("measured", result["status"])
        states = result["work_item_state_proxy"]
        self.assertEqual(1, states["first_cycle_count"])
        self.assertEqual(1, states["reentry_count"])
        self.assertEqual(3, states["known_interval_count"])
        self.assertEqual(1, states["missing_interval_count"])
        self.assertGreaterEqual(states["known_elapsed_seconds"], 0)
        self.assertIsNone(result["human_active_work_seconds"])
        self.assertIsNone(result["semantic_rework_count"])
        self.assertIsNone(result["concern_cognitive_onset"])
        self.assertNotIn("risk_rate", result)

    def test_check_snapshot_history_changed_evidence_and_check_set(self):
        import hashlib
        self.item()
        evidence = self.root / "evidence.txt"
        evidence.write_bytes(b"first")
        self.check(target=str(evidence))
        self.check(status="done", target=str(evidence))
        evidence.write_bytes(b"second")
        self.check(status="done", target=str(evidence))
        self.check(status="done", target=str(evidence), artifact="CHK-2")
        snapshots = [e for e in self.events() if e["operation"] == "check.result_recorded"]
        self.assertEqual(hashlib.sha256(b"first").hexdigest(), snapshots[0]["facts"]["evidence_hash"])
        self.assertIsNone(snapshots[0]["facts"]["source_hash"])
        self.assertEqual(["CHK-1"], snapshots[0]["facts"]["check_ids"])
        self.assertEqual(["CHK-1", "CHK-2"], snapshots[-1]["facts"]["check_ids"])
        self.assertNotEqual(snapshots[1]["facts"]["evidence_hash"], snapshots[2]["facts"]["evidence_hash"])
        groups = skillrun.summarize_observations(self.log)["declared_check_results"]
        group = next(g for g in groups if g["event_count"] == 2)
        self.assertEqual("blocked", group["first_declared_status"])
        self.assertEqual("done", group["final_declared_status"])
        self.assertTrue(all(e["facts"]["execution_verified"] is False for e in snapshots))

    def test_external_and_symlink_evidence_not_read(self):
        from unittest.mock import patch
        self.item()
        with tempfile.TemporaryDirectory() as external:
            evidence = Path(external) / "external.txt"
            evidence.write_bytes(b"external")
            self.check(target=str(evidence))
            self.assertIsNone(self.events()[-1]["facts"]["evidence_hash"])
        with patch.object(Path, "read_bytes", side_effect=AssertionError("network/path must not be read")):
            self.check(target="https://example.com/check")
        self.assertIsNone(self.events()[-1]["facts"]["evidence_hash"])

    def test_knowledge_hash_is_declared_and_apply_keeps_prior_load_check(self):
        args = ["--log", str(self.log), "--xid", "7A2F4C8D1201", "--content-hash", "declared"]
        before = self.log.read_bytes()
        code, _ = self.call("knowledge", *args, "--action", "apply", "--target", "MISSING")
        self.assertEqual(1, code)
        self.assertEqual(before, self.log.read_bytes())
        code, loaded = self.call("knowledge", *args, "--action", "load", "--operation-key", "load-1")
        self.assertEqual(0, code, loaded)
        self.assertEqual("caller_declared", self.events()[-1]["facts"]["content_hash_basis"])
        before = self.log.read_bytes()
        self.assertEqual(loaded["operation_receipt"], self.call("knowledge", *args, "--action", "load", "--operation-key", "load-1")[1]["operation_receipt"])
        self.assertEqual(before, self.log.read_bytes())

    def test_legacy_unmeasured_and_malformed_json_strict(self):
        self.log.write_text("# Legacy Run\n", encoding="utf-8")
        self.assertEqual("unmeasured", skillrun.summarize_observations(self.log)["status"])
        self.log.write_text("## Operation Observations\n\n- event: {broken}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Operation Observations"):
            skillrun.summarize_observations(self.log)
        code, result = self.call("observation-summary", "--log", str(self.log))
        self.assertEqual(1, code)
        self.assertEqual("invalid", result["status"])

    def test_malformed_history_warning_does_not_hide_native_success(self):
        with self.log.open("a", encoding="utf-8") as handle:
            handle.write("\n- event: {broken}\n")
        code, result = self.item()
        self.assertEqual(0, code, result)
        self.assertTrue(result["measurement_warnings"])
        self.assertEqual("in_progress", skillrun._parse_work_items(self.log.read_text(encoding="utf-8"))[0]["status"])
        before = self.log.read_bytes()
        code, result = self.item(status="done", key="cannot-safely-replay")
        self.assertEqual(1, code, result)
        self.assertEqual(before, self.log.read_bytes())

    def test_atomic_failure_preserves_log_and_native_failure(self):
        from unittest.mock import patch
        before = self.log.read_bytes()
        with patch("xrefkit.skillrun.os.replace", side_effect=OSError("disk write failed")):
            with self.assertRaisesRegex(OSError, "disk write failed"):
                self.item()
        self.assertEqual(before, self.log.read_bytes())

    def test_measurement_read_failure_warning_keeps_success(self):
        from unittest.mock import patch
        self.item()
        evidence = self.root / "evidence.txt"
        evidence.write_bytes(b"data")
        with patch("xrefkit.skillrun._local_evidence_hash", side_effect=OSError("evidence unavailable")):
            code, result = self.check(status="done", target=str(evidence))
        self.assertEqual(0, code, result)
        self.assertTrue(result["measurement_warnings"])
        self.assertEqual("done", skillrun._parse_artifacts(self.log.read_text(encoding="utf-8"))[0]["status"])


    def test_corruption_schema_run_and_reference_are_diagnosed(self):
        self.item()
        original = self.log.read_text(encoding="utf-8")
        events = self.events()
        for change in ({"schema_version": 77}, {"run_id": "another-run"}, {"facts": {"subject_ref": "MISSING", "status": "done"}}):
            event = dict(events[-1])
            event.update(change)
            old = self.json.dumps(events[-1], ensure_ascii=False, separators=(",", ":"))
            damaged = self.json.dumps(event, ensure_ascii=False, separators=(",", ":"))
            self.log.write_text(original.replace(old, damaged), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Operation Observations"):
                skillrun.summarize_observations(self.log)
        self.log.write_text(original, encoding="utf-8")

    def test_reverse_program_time_is_missing_not_cognitive_or_execution_order(self):
        self.item()
        self.item(status="done")
        events = self.events()
        event = dict(events[-1])
        event["recorded_at"] = "2000-01-01T00:00:00+00:00"
        original = self.log.read_text(encoding="utf-8")
        self.log.write_text(original.replace(self.json.dumps(events[-1], ensure_ascii=False, separators=(",", ":")),
                                           self.json.dumps(event, ensure_ascii=False, separators=(",", ":"))), encoding="utf-8")
        summary = skillrun.summarize_observations(self.log)
        proxy = summary["work_item_state_proxy"]
        self.assertEqual(0, proxy["known_interval_count"])
        self.assertEqual(2, proxy["missing_interval_count"])
        self.assertIsNone(proxy["intervals"][0]["elapsed_seconds"])
        self.assertEqual(events[-2]["event_id"], proxy["intervals"][0]["from_event_id"])
        self.assertIsNone(summary["problem_recognition_time"]["value"])

    def test_large_evidence_skips_hash_without_changing_native_result(self):
        self.item()
        evidence = self.root / "large.txt"
        evidence.write_bytes(b"a" * (1024 * 1024 + 1))
        code, result = self.check(status="done", target=str(evidence))
        self.assertEqual(0, code, result)
        self.assertIn("1 MiB", " ".join(result["measurement_warnings"]))
        self.assertIsNone(self.events()[-1]["facts"]["evidence_hash"])

    def test_coverage_denominators_are_only_recorded_objects(self):
        self.item()
        self.check()
        self.call("concern", "--log", str(self.log), "--concern", "UNK-1", "--kind", "unknown",
                  "--status", "open", "--text", "Missing", "--role", "sample_skill:executor")
        summary = skillrun.summarize_observations(self.log)
        coverage = summary["recorded_field_coverage"]
        self.assertEqual({"eligible_recorded_count": 1, "known_count": 0, "missing_count": 1, "coverage_fraction": 0.0}, coverage["check_evidence_hash"])
        self.assertEqual(1, coverage["check_source_hash"]["missing_count"])
        self.assertEqual(1, coverage["concern_cognitive_onset"]["missing_count"])
        self.assertEqual(1, coverage["concern_occurrence"]["missing_count"])
        for key in ("early_discovery_rate", "rework_effort", "quality_gate_pass_rate", "problem_recognition_time", "knowledge_collection_use_cost"):
            self.assertIsNone(summary[key]["value"])
            self.assertIsNone(summary[key]["missing_count"])

    def test_native_knowledge_xid_validation_remains_authoritative(self):
        code, result = self.call("knowledge", "--log", str(self.log), "--action", "load", "--xid", "legacy-reference",
                                 "--content-hash", "declared")
        self.assertEqual(0, code, result)
        self.assertEqual(["legacy-reference"], self.events()[-1]["facts"]["xids"])


    def test_native_read_error_result_is_preserved(self):
        import argparse
        from unittest.mock import patch
        with patch.object(Path, "read_text", side_effect=OSError("native read failed")):
            result = skillrun.update_knowledge_observation(argparse.Namespace(log=str(self.log)))
        self.assertFalse(result.ok)
        self.assertIn("could not read skill run log", " ".join(result.errors))

    def test_non_json_cli_exposes_measurement_warning(self):
        with self.log.open("a", encoding="utf-8") as handle:
            handle.write("\n- event: {broken}\n")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["skill", "workitem", "--log", str(self.log), "--item", "WI-1", "--text", "Task",
                         "--completion-criterion", "Evidence recorded", "--status", "done", "--role", "sample_skill:executor"])
        self.assertEqual(0, code)
        self.assertIn("measurement warning:", output.getvalue())


    def test_noncheck_artifact_keeps_legacy_missing_item_behavior(self):
        prior = len(self.events())
        code, result = self.call("artifact", "--log", str(self.log), "--artifact", "OUT-LEGACY",
                                 "--kind", "output", "--target", "docs/output.md", "--item", "WI-MISSING",
                                 "--status", "done", "--role", "sample_skill:executor")
        self.assertEqual(0, code, result)
        self.assertEqual(prior, len(self.events()))

    def test_unkeyed_check_missing_item_warns_without_new_native_gate(self):
        prior = len(self.events())
        code, result = self.check()
        self.assertEqual(0, code, result)
        self.assertTrue(result["measurement_warnings"])
        self.assertEqual(prior, len(self.events()))
        self.assertIn("CHK-1", self.log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

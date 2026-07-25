"""Prepare an XRefKit repository and client configuration for MCP use."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


AGENT_APPEND = """## XRefKit MCP Skill Routing

When the XRefKit MCP server is configured and available in this client, use
its Skill catalog and semantic routing for Skill selection.

The VS Code workspace MCP configuration is `.vscode/mcp.json`.

Do not manually import or select individual Skill files during normal task
execution. The administrator manages Skill registration; the client uses the
MCP catalog to select and execute Skills.
"""


def _vscode_config(root: Path) -> dict[str, object]:
    python_command = "python"
    venv_python = root / ".venv" / "Scripts" / "python.exe"
    if venv_python.is_file():
        python_command = "${workspaceFolder}\\.venv\\Scripts\\python.exe"
    return {
        "servers": {
            "xrefkit": {
                "type": "stdio",
                "command": python_command,
                "args": [
                    "-m",
                    "xrefkit",
                    "mcp",
                    "serve",
                    "--repo",
                    "${workspaceFolder}",
                    "--transport",
                    "stdio",
                ],
            }
        }
    }


def _run_xref_fix(root: Path) -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, "-m", "xrefkit", "xref", "fix", "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload: object = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    return {"returncode": proc.returncode, "result": payload}


def _run_skill_checks(root: Path, metas: list[Path]) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for meta in metas:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "xrefkit",
                "skill",
                "check",
                "--root",
                str(root),
                "--meta",
                str(meta),
                "--level",
                "trial",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            result: object = json.loads(proc.stdout)
        except json.JSONDecodeError:
            result = {"stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
        results.append({"meta": meta.relative_to(root).as_posix(), "returncode": proc.returncode, "result": result})
    return results


def _write_setup_files(
    output: Path,
    *,
    root: Path,
    import_report: dict[str, object] | None,
    xref_report: dict[str, object],
    checks: list[dict[str, object]],
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "vscode-mcp.json").write_text(
        json.dumps(_vscode_config(root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "AGENTS.md.append.md").write_text(AGENT_APPEND, encoding="utf-8")
    (output / "CLAUDE.md.append.md").write_text(AGENT_APPEND, encoding="utf-8")
    report = {"root": str(root), "import": import_report, "xref_fix": xref_report, "skill_checks": checks}
    (output / "import-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    guide = f"""# XRefKit MCP setup review

Generated setup files:

- `vscode-mcp.json`: copy to `{(root / '.vscode' / 'mcp.json').as_posix()}`.
- `AGENTS.md.append.md`: review and append to `AGENTS.md`.
- `CLAUDE.md.append.md`: review and append to `CLAUDE.md`.
- `import-report.json`: import, XID fix, and Skill validation results.

The setup command does not modify client instruction files or overwrite an
existing VS Code MCP configuration. Apply these files only after review.

After applying the files, open the repository in VS Code and start the
`xrefkit` MCP server from the MCP controls.
"""
    (output / "SETUP.md").write_text(guide, encoding="utf-8")


def setup(args: argparse.Namespace) -> int:
    root = Path(args.repo).resolve()
    root.mkdir(parents=True, exist_ok=True)
    output = Path(args.output).resolve() if args.output else Path(tempfile.mkdtemp(prefix="xrefkit-setup-"))
    import_report: dict[str, object] | None = None
    metas: list[Path] = []

    if args.import_source:
        from xrefkit.import_skill import convert_skill, convert_skill_tree

        source = Path(args.import_source).resolve()
        if (source / "skills").is_dir() or args.batch:
            result = convert_skill_tree(
                source_root=source,
                repo_root=root,
                skill_id_prefix=args.skill_id_prefix,
                target_skill_root=root / "skills",
                dry_run=False,
            )
            import_report = result.to_dict()
        else:
            if not args.skill_id:
                raise SystemExit("--skill-id is required when --import is a single Skill directory")
            result = convert_skill(
                source_dir=source,
                source_root=source.parent,
                repo_root=root,
                skill_id=args.skill_id,
                target_skill_dir=root / "skills" / args.skill_id,
                dry_run=False,
            )
            import_report = result.to_dict()

        if isinstance(import_report, dict):
            metas = [root / Path(item["meta_doc"]) for item in import_report.get("converted_skills", []) if item.get("meta_doc")]
            if not metas and import_report.get("meta_doc"):
                metas = [root / Path(import_report["meta_doc"])]

    xref_report = _run_xref_fix(root)
    checks = _run_skill_checks(root, metas)
    _write_setup_files(output, root=root, import_report=import_report, xref_report=xref_report, checks=checks)

    payload = {"ok": xref_report["returncode"] == 0 and all(item["returncode"] == 0 for item in checks), "output": str(output), "report": str(output / "import-report.json")}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"setup workspace: {output}")
        print(f"guide: {output / 'SETUP.md'}")
        print(f"report: {output / 'import-report.json'}")
    return 0 if payload["ok"] else 1


def apply_setup(args: argparse.Namespace) -> int:
    source = Path(args.source).resolve()
    root = Path(args.repo).resolve()
    if not source.is_dir():
        raise SystemExit(f"setup workspace does not exist: {source}")
    destinations = {
        source / "vscode-mcp.json": root / ".vscode" / "mcp.json",
        source / "AGENTS.md.append.md": root / "AGENTS.md",
        source / "CLAUDE.md.append.md": root / "CLAUDE.md",
    }
    for candidate, destination in destinations.items():
        if not candidate.is_file():
            raise SystemExit(f"missing setup artifact: {candidate}")
        if destination.name == "mcp.json":
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and destination.read_bytes() != candidate.read_bytes() and not args.force:
                raise SystemExit(f"refusing to overwrite {destination}; use --force after review")
            if not destination.exists() or destination.read_bytes() != candidate.read_bytes():
                shutil.copyfile(candidate, destination)
        else:
            existing = destination.read_text(encoding="utf-8") if destination.exists() else ""
            addition = candidate.read_text(encoding="utf-8")
            if addition.strip() not in existing:
                destination.write_text(existing.rstrip() + "\n\n" + addition, encoding="utf-8")
    print(f"applied setup artifacts from: {source}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit mcp")
    sub = parser.add_subparsers(dest="command", required=True)
    setup_parser = sub.add_parser("setup", help="import Skills and generate reviewable MCP setup artifacts")
    setup_parser.add_argument("--repo", required=True)
    setup_parser.add_argument("--import", dest="import_source", default=None, help="Skill directory or batch root")
    setup_parser.add_argument("--batch", action="store_true")
    setup_parser.add_argument("--skill-id-prefix", default="imported")
    setup_parser.add_argument("--skill-id", default=None)
    setup_parser.add_argument("--output", default=None, help="Setup workspace; defaults to a temporary folder")
    setup_parser.add_argument("--json", action="store_true")
    setup_parser.set_defaults(handler=setup)

    apply_parser = sub.add_parser("setup-apply", help="apply reviewed setup artifacts")
    apply_parser.add_argument("--source", required=True)
    apply_parser.add_argument("--repo", required=True)
    apply_parser.add_argument("--force", action="store_true")
    apply_parser.set_defaults(handler=apply_setup)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())

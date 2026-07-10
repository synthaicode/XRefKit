from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], *, cwd: Path) -> None:
    print(
        f"[quality-gate] cwd={cwd.relative_to(REPO_ROOT).as_posix() if cwd != REPO_ROOT else '.'}",
        flush=True,
    )
    print("[quality-gate] run:", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def _run_xrefkit_stage() -> None:
    _run([sys.executable, "-m", "pytest", "-q"], cwd=REPO_ROOT)
    _run(
        [
            sys.executable,
            "-m",
            "xrefkit",
            "xref",
            "check",
            "--include",
            "agent",
            "docs",
            "skills",
            "knowledge",
            "capabilities",
            "tools",
        ],
        cwd=REPO_ROOT,
    )
    _run([sys.executable, "-m", "xrefkit", "skill", "check", "--scope", "skills"], cwd=REPO_ROOT)
    _run([sys.executable, "-m", "xrefkit", "pack", "lint"], cwd=REPO_ROOT)
    _run([sys.executable, "tools/audit_skill_runtime_logs.py", "--tracked-only"], cwd=REPO_ROOT)
    _run([sys.executable, "tools/check_project_quality_baseline.py"], cwd=REPO_ROOT)


def _run_node_stage(project_dir: Path, *, install: bool) -> None:
    npm = shutil.which("npm")
    if npm is None:
        raise SystemExit("npm is required for node quality-gate stages")

    if install:
        _run([npm, "ci"], cwd=project_dir)
    _run([npm, "run", "check"], cwd=project_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run repository quality-gate stages")
    parser.add_argument(
        "stage",
        choices=["xrefkit", "slides-app", "all"],
        help="Quality-gate stage to run",
    )
    parser.add_argument(
        "--install-node-deps",
        action="store_true",
        help="Install node dependencies with npm ci before node stages",
    )
    args = parser.parse_args(argv)

    if args.stage in {"xrefkit", "all"}:
        _run_xrefkit_stage()

    if args.stage in {"slides-app", "all"}:
        _run_node_stage(REPO_ROOT / "projects" / "slides-app", install=args.install_node_deps)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

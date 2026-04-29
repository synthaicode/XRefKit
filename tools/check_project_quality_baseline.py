from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = REPO_ROOT / "projects"


def _iter_node_projects() -> list[Path]:
    if not PROJECTS_DIR.exists():
        return []
    return sorted(path for path in PROJECTS_DIR.iterdir() if (path / "package.json").exists())


def _load_package_json(project_dir: Path) -> dict[str, object]:
    return json.loads((project_dir / "package.json").read_text(encoding="utf-8"))


def validate_project(project_dir: Path) -> list[str]:
    package = _load_package_json(project_dir)
    errors: list[str] = []

    if not (project_dir / "README.md").exists():
        errors.append("missing README.md")

    scripts = package.get("scripts")
    if not isinstance(scripts, dict) or not isinstance(scripts.get("check"), str) or not scripts["check"].strip():
        errors.append("missing scripts.check")

    engines = package.get("engines")
    if not isinstance(engines, dict) or not isinstance(engines.get("node"), str) or not engines["node"].strip():
        errors.append("missing engines.node")

    has_dependencies = bool(package.get("dependencies")) or bool(package.get("devDependencies"))
    if has_dependencies and not (project_dir / "package-lock.json").exists():
        errors.append("missing package-lock.json for dependency-managed project")

    return errors


def main() -> int:
    failed = False
    for project_dir in _iter_node_projects():
        errors = validate_project(project_dir)
        rel = project_dir.relative_to(REPO_ROOT).as_posix()
        if errors:
            failed = True
            print(f"fail: {rel}")
            for error in errors:
                print(f"  error: {error}")
        else:
            print(f"ok: {rel}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Materialize the packaged Skill into the folder layout read by XRefKit MCP."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


DEFAULT_RELATIVE_TARGET = Path("skills") / "packs" / "batch-regression" / "batch-impact-regression"


def _copy_tree(source: Path, target: Path, *, force: bool) -> list[str]:
    if not source.is_dir():
        raise FileNotFoundError(f"MCP Skill asset directory does not exist: {source}")
    target.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for source_path in sorted(path for path in source.rglob("*") if path.is_file()):
        relative = source_path.relative_to(source)
        target_path = target / relative
        if target_path.exists() and not force:
            raise FileExistsError(
                f"target already exists: {target_path}; use --force only for an intentional replacement"
            )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        copied.append(str(target_path))
    return copied


def materialize(repo_root: Path, *, target: Path | None = None, force: bool = False) -> dict[str, object]:
    repo_root = repo_root.resolve()
    if not repo_root.is_dir():
        raise NotADirectoryError(f"repository root does not exist: {repo_root}")
    destination = (target or (repo_root / DEFAULT_RELATIVE_TARGET)).resolve()
    try:
        destination.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"target must be inside repository root: {destination}") from exc

    source = Path(__file__).parent / "skill_assets" / "mcp_skill"
    copied = _copy_tree(source, destination, force=force)
    return {
        "repository_root": str(repo_root),
        "skill_root": str(destination),
        "copied_files": copied,
        "skill_id": "batch-impact-regression",
        "mcp_reload_required": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit-batch-regression install-mcp-skill")
    parser.add_argument("--repo", required=True, type=Path, help="XRefKit repository passed to the MCP server")
    parser.add_argument("--target", type=Path, help="Optional Skill directory inside --repo")
    parser.add_argument("--force", action="store_true", help="Replace an existing materialized Skill intentionally")
    args = parser.parse_args(argv)
    result = materialize(args.repo, target=args.target, force=args.force)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

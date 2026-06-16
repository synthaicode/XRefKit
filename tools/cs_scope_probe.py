"""Deterministic content probe: is C# in scope for this work?

The Roslyn analyzer quality check (``collect_analyzer_sarif.py`` ->
``sarif_to_locator.py``) is content-conditional, not uniform. A skill declares
that it *can* apply the check (by referencing CAP-QA-011); this probe decides
whether it *actually* applies to one run by scanning the run's in-scope
content for C#.

Content signal (confirmed): C# is in scope when the target tree (or the
changed-file set) contains any ``*.cs`` file, or a ``*.csproj`` / ``*.sln``
build target.

Usage:

    python tools/cs_scope_probe.py --target <path> [--json]
    python tools/cs_scope_probe.py --target <path> --changed-from <git-ref> [--json]
    python tools/cs_scope_probe.py --target <path> --require-cs   # exit 1 if not in scope

This probe only decides applicability. It does not run the analyzer.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

_EXCLUDED_DIRS = {"bin", "obj", ".git", ".vs", "node_modules"}


def _is_excluded(rel_parts: tuple[str, ...]) -> bool:
    return any(part in _EXCLUDED_DIRS for part in rel_parts)


def _scan_tree(target: Path) -> tuple[list[str], list[str], list[str]]:
    cs_files: list[str] = []
    csproj: list[str] = []
    sln: list[str] = []
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(target)
        if _is_excluded(rel.parts):
            continue
        suffix = path.suffix.lower()
        rel_posix = rel.as_posix()
        if suffix == ".cs":
            cs_files.append(rel_posix)
        elif suffix == ".csproj":
            csproj.append(rel_posix)
        elif suffix == ".sln":
            sln.append(rel_posix)
    return sorted(cs_files), sorted(csproj), sorted(sln)


def _scan_changed(target: Path, changed_from: str) -> tuple[list[str], list[str], list[str]]:
    result = subprocess.run(
        ["git", "diff", "--name-only", changed_from, "--", "."],
        cwd=target,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git diff failed for {target} against {changed_from}: {result.stderr.strip()}")
    cs_files: list[str] = []
    csproj: list[str] = []
    sln: list[str] = []
    for line in result.stdout.splitlines():
        name = line.strip()
        if not name:
            continue
        parts = tuple(Path(name).parts)
        if _is_excluded(parts):
            continue
        lower = name.lower()
        if lower.endswith(".cs"):
            cs_files.append(name)
        elif lower.endswith(".csproj"):
            csproj.append(name)
        elif lower.endswith(".sln"):
            sln.append(name)
    return sorted(cs_files), sorted(csproj), sorted(sln)


def probe_cs_scope(target: str | Path, *, changed_from: str | None = None) -> dict[str, object]:
    target_path = Path(target).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"target not found: {target_path}")

    if changed_from:
        cs_files, csproj, sln = _scan_changed(target_path, changed_from)
        mode = f"changed-from:{changed_from}"
    else:
        cs_files, csproj, sln = _scan_tree(target_path)
        mode = "tree"

    has_build_target = bool(csproj or sln)
    cs_in_scope = bool(cs_files) or has_build_target
    return {
        "target": target_path.as_posix(),
        "mode": mode,
        "cs_in_scope": cs_in_scope,
        "cs_file_count": len(cs_files),
        "has_build_target": has_build_target,
        "build_targets": (sln + csproj)[:50],
        "roslyn_quality_check": "applicable" if cs_in_scope else "na",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe whether C# is in scope for the work")
    parser.add_argument("--target", default=".", help="Target path to scan (default: .)")
    parser.add_argument("--changed-from", default=None, help="Git ref; scan only files changed since this ref")
    parser.add_argument("--require-cs", action="store_true", help="Exit 1 when C# is not in scope")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    try:
        report = probe_cs_scope(args.target, changed_from=args.changed_from)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"error: {exc}")
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"cs_in_scope={report['cs_in_scope']} cs_files={report['cs_file_count']} "
            f"build_target={report['has_build_target']} roslyn_quality_check={report['roslyn_quality_check']}"
        )

    if args.require_cs and not report["cs_in_scope"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build an isolated evaluation plan from installed XRefKit Skill packages."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import yaml


def package_roots() -> list[Path]:
    roots: list[Path] = []
    entries = importlib.metadata.entry_points(group="xrefkit.skill_packages")
    for entry in sorted(entries, key=lambda item: item.name):
        root = Path(entry.load()())
        if root not in roots:
            roots.append(root)
    return roots


def load_package_plan(root: Path) -> list[dict[str, Any]]:
    package_manifest_path = root / "package_manifest.yaml"
    package_manifest = yaml.safe_load(package_manifest_path.read_text(encoding="utf-8"))
    relative_manifest = package_manifest.get("evaluation_manifest")
    if not relative_manifest:
        return []
    manifest_path = root / relative_manifest
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    package_id = manifest.get("package_id", package_manifest.get("package_id"))
    plan: list[dict[str, Any]] = []
    for case in manifest.get("cases", []):
        target = manifest_path.parent / case["target"]
        expected = manifest_path.parent / case["expected"]
        calibration = manifest_path.parent / case["calibration"]
        for path in (target, expected, calibration):
            if not path.exists():
                raise FileNotFoundError(path)
        plan.append(
            {
                "package_id": package_id,
                "package_root": str(root),
                "evaluation_id": manifest.get("evaluation_id"),
                "case_id": case["id"],
                "skill_id": case["skill_id"],
                "target": str(target),
                "expected": str(expected),
                "calibration": str(calibration),
                "expected_must_not_enter_target": True,
            }
        )
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discover", action="store_true")
    parser.add_argument("--package-root", action="append", type=Path, default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.discover and not args.package_root:
        parser.error("use --discover or --package-root")
    roots = args.package_root or package_roots()
    plan = [item for root in roots for item in load_package_plan(root)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"plan": plan}, indent=2), encoding="utf-8")
    print(json.dumps({"cases": len(plan), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Minimal CLI for XRefKit v2 MVP."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .discovery import discover_skill_packages, package_list_rows
from .loaders import load_server_config
from .resolver import EffectiveSkillResolver
from .workspace import build_registry


def _add_workspace_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--package-manifest", action="append", default=[], help="Path to package_manifest.yaml")
    parser.add_argument("--local-manifest", help="Path to xrefkit.local/local_manifest.yaml")
    parser.add_argument("--enable-entry-point-discovery", action="store_true", help="Load enabled packages from Python entry points")
    parser.add_argument("--enabled-package", action="append", default=[], help="Package id enabled for resolver use")


def _enabled_packages_from_args(args: argparse.Namespace) -> set[str]:
    enabled = set(args.enabled_package or [])
    server_config = getattr(args, "server_config", None)
    if server_config:
        config = load_server_config(server_config)
        enabled.update(config.packages.enabled)
    return enabled


def _bundle_tree(bundle: object) -> str:
    # Deliberately use model_dump so this function stays stable if the model
    # gains computed properties later.
    data = bundle.model_dump(mode="json")  # type: ignore[attr-defined]
    lines = [f"effective_skill: {data['effective_skill_id']}", f"mode: {data['resolution_mode']}"]
    lines.append("loaded:")
    for group, entries in data["loaded_texts"].items():
        if not entries:
            continue
        lines.append(f"  {group}:")
        for entry in entries:
            lines.append(f"    - {entry['xid']} ({entry['load_reason']})")
    lines.append("references:")
    for group, entries in data["references"].items():
        if entries:
            lines.append(f"  {group}: {', '.join(entries)}")
    lines.append("required_outputs:")
    for output in data["required_outputs"]:
        lines.append(f"  - {output}")
    return "\n".join(lines)


def cmd_show_effective_skill(args: argparse.Namespace) -> int:
    registry = build_registry(
        package_manifests=args.package_manifest,
        local_manifest_path=args.local_manifest,
        discover_entry_points=args.enable_entry_point_discovery,
        enabled_package_ids=_enabled_packages_from_args(args),
    )
    bundle = EffectiveSkillResolver(registry).resolve_entry(args.skill_id)
    if args.mode == "tree":
        print(_bundle_tree(bundle))
    elif args.mode == "resolved-json":
        print(json.dumps(bundle.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        raise NotImplementedError("true full materialize is not implemented in the MVP CLI")
    return 0


def cmd_package_discover(args: argparse.Namespace) -> int:
    rows = [
        {
            "entry_point": package.entry_point_name,
            "package_id": package.package_id,
            "version": package.version,
            "manifest_path": str(package.manifest_path),
        }
        for package in discover_skill_packages()
    ]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            print(f"{row['package_id']}\t{row['version']}\t{row['manifest_path']}")
    return 0


def cmd_package_list(args: argparse.Namespace) -> int:
    rows = package_list_rows(enabled_package_ids=_enabled_packages_from_args(args))
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            status = "enabled" if row["enabled"] else "disabled"
            print(f"{row['package_id']}\t{row['version']}\t{status}\t{row['manifest_path']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="xrefkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    package = subparsers.add_parser("package")
    package_sub = package.add_subparsers(dest="package_command", required=True)
    discover = package_sub.add_parser("discover")
    discover.add_argument("--json", action="store_true")
    discover.set_defaults(func=cmd_package_discover)

    package_list = package_sub.add_parser("list")
    package_list.add_argument("--json", action="store_true")
    package_list.add_argument("--server-config", help="Path to xrefkit.server.toml with enabled packages")
    package_list.add_argument("--enabled-package", action="append", default=[], help="Package id enabled for resolver use")
    package_list.set_defaults(func=cmd_package_list)

    show = subparsers.add_parser("show")
    show_sub = show.add_subparsers(dest="show_command", required=True)
    effective = show_sub.add_parser("effective-skill")
    effective.add_argument("skill_id")
    effective.add_argument("--mode", choices=["tree", "resolved-json"], default="tree")
    effective.add_argument("--server-config", help="Path to xrefkit.server.toml with enabled packages")
    _add_workspace_args(effective)
    effective.set_defaults(func=cmd_show_effective_skill)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)

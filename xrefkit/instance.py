"""XRefKit instance manifest and bootstrap support."""

from __future__ import annotations

import argparse
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path


MANIFEST_NAME = "xrefkit.toml"
VALID_AUTHORITIES = {
    "legacy_authoritative",
    "cutover_ready",
    "xrefkit_authoritative",
}
STARTUP_XID = "C3A1F78D9B22"


@dataclass(frozen=True)
class InstanceManifest:
    instance_id: str
    command_authority: str
    roots: tuple[str, ...]
    startup_xid: str = STARTUP_XID


def load_instance_manifest(path: str | Path) -> InstanceManifest:
    manifest_path = Path(path)
    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    instance = data.get("instance", {})
    runtime = data.get("runtime", {})
    roots = data.get("roots", {})
    authority = str(runtime.get("command_authority", ""))
    if authority not in VALID_AUTHORITIES:
        raise ValueError(f"invalid command_authority: {authority!r}")
    values = tuple(str(value) for value in roots.get("content", ["."]))
    return InstanceManifest(
        instance_id=str(instance.get("id", "")).strip(),
        command_authority=authority,
        roots=values,
        startup_xid=str(runtime.get("startup_xid", STARTUP_XID)),
    )


def _manifest_text(instance_id: str) -> str:
    return (
        "[instance]\n"
        f'id = "{instance_id}"\n\n'
        "[runtime]\n"
        'command_authority = "legacy_authoritative"\n'
        f'startup_xid = "{STARTUP_XID}"\n\n'
        "[roots]\n"
        'content = ["."]\n'
    )


def _startup_text(client: str) -> str:
    title = {"AGENTS.md": "AGENTS", "CLAUDE.md": "CLAUDE", "CHATGPT.md": "CHATGPT"}[client]
    return (
        f"# {title} Startup (XRefKit)\n\n"
        "**As your first action**, resolve and apply the XRefKit startup contract:\n\n"
        f"- `docs/core/contracts/080_xrefkit_startup_contract.md#xid-{STARTUP_XID}`\n"
    )


def initialize_instance(root: str | Path, *, instance_id: str, startup_files: bool) -> dict[str, object]:
    root_path = Path(root).resolve()
    root_path.mkdir(parents=True, exist_ok=True)
    manifest_path = root_path / MANIFEST_NAME
    created: list[str] = []
    preserved: list[str] = []
    if manifest_path.exists():
        preserved.append(MANIFEST_NAME)
    else:
        manifest_path.write_text(_manifest_text(instance_id), encoding="utf-8")
        created.append(MANIFEST_NAME)

    if startup_files:
        for name in ("AGENTS.md", "CLAUDE.md", "CHATGPT.md"):
            path = root_path / name
            if path.exists():
                preserved.append(name)
            else:
                path.write_text(_startup_text(name), encoding="utf-8")
                created.append(name)

    manifest = load_instance_manifest(manifest_path)
    if not manifest.instance_id:
        raise ValueError("instance.id must not be empty")
    return {
        "ok": True,
        "root": str(root_path),
        "manifest": str(manifest_path),
        "instance_id": manifest.instance_id,
        "command_authority": manifest.command_authority,
        "startup_xid": manifest.startup_xid,
        "roots": list(manifest.roots),
        "created": created,
        "preserved": preserved,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit init")
    parser.add_argument("--root", default=".")
    parser.add_argument("--instance-id")
    parser.add_argument("--no-startup-files", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    instance_id = args.instance_id or root.name.lower().replace(" ", "-")
    try:
        result = initialize_instance(
            root,
            instance_id=instance_id,
            startup_files=not args.no_startup_files,
        )
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        result = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"error: {exc}")
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"instance: {result['instance_id']}")
        print(f"manifest: {result['manifest']}")
        print(f"command_authority: {result['command_authority']}")
    return 0

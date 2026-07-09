"""Stable tool-ID registry and client-side execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ToolContract:
    tool_id: str
    xid: str
    path: str
    execution_location: str
    side_effects: str
    content_hash: str

    def to_dict(self) -> dict[str, str]:
        return {
            "tool_id": self.tool_id,
            "xid": self.xid,
            "path": self.path,
            "execution_location": self.execution_location,
            "side_effects": self.side_effects,
            "content_hash": self.content_hash,
        }


def load_tool_contracts(root: str | Path = ".", manifest: str = "tools/contracts.yaml") -> list[ToolContract]:
    root_path = Path(root).resolve()
    data = yaml.safe_load((root_path / manifest).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != "xrefkit.tool_contracts/v1":
        raise ValueError("unsupported tool contract manifest")
    contracts: list[ToolContract] = []
    ids: set[str] = set()
    xids: set[str] = set()
    for item in data.get("tools", []):
        tool_id = str(item["tool_id"])
        xid = str(item["xid"]).upper()
        if tool_id in ids:
            raise ValueError(f"duplicate tool_id: {tool_id}")
        if xid in xids:
            raise ValueError(f"duplicate tool XID: {xid}")
        path = root_path / str(item["path"])
        if not path.is_file():
            raise ValueError(f"tool path not found: {path}")
        ids.add(tool_id)
        xids.add(xid)
        contracts.append(
            ToolContract(
                tool_id=tool_id,
                xid=xid,
                path=str(item["path"]),
                execution_location=str(item["execution_location"]),
                side_effects=str(item["side_effects"]),
                content_hash=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    return contracts


def _find(contracts: list[ToolContract], identity: str) -> ToolContract:
    key = identity.upper()
    for contract in contracts:
        if contract.tool_id == identity or contract.xid == key:
            return contract
    raise KeyError(f"unknown tool: {identity}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit tools")
    parser.add_argument("--root", default=".")
    parser.add_argument("--manifest", default="tools/contracts.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    list_parser = sub.add_parser("list")
    list_parser.add_argument("--json", action="store_true")
    show = sub.add_parser("show")
    show.add_argument("tool")
    show.add_argument("--json", action="store_true")
    run = sub.add_parser("run")
    run.add_argument("tool")
    run.add_argument("tool_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        contracts = load_tool_contracts(args.root, args.manifest)
        if args.command == "list":
            payload: Any = [contract.to_dict() for contract in contracts]
        else:
            contract = _find(contracts, args.tool)
            if args.command == "show":
                payload = contract.to_dict()
            else:
                if contract.execution_location != "client":
                    raise ValueError(f"tool is not client executable: {contract.tool_id}")
                command = [sys.executable, str(Path(args.root) / contract.path), *args.tool_args]
                return subprocess.run(command, check=False).returncode
    except (OSError, KeyError, ValueError, yaml.YAMLError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    as_json = bool(getattr(args, "json", False))
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif isinstance(payload, list):
        for item in payload:
            print(f"{item['tool_id']}\t{item['xid']}\t{item['execution_location']}")
    else:
        print(f"{payload['tool_id']}\t{payload['xid']}\t{payload['path']}")
    return 0


__all__ = ["ToolContract", "load_tool_contracts", "main"]

"""Deterministic, metadata-only catalog for explicitly supplied SkillDefinitions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from collections.abc import Iterable

from xrefkit.skill_definition import load_skill_definition


def build_definition_catalog(paths: Iterable[Path]) -> dict:
    entries = []
    skill_ids = set()
    xid_index = {}
    for position, path in enumerate(paths):
        if position >= 2048:
            raise ValueError("catalog accepts at most 2048 definitions")
        definition = load_skill_definition(Path(path))
        metadata = definition["metadata"]
        skill_id = metadata["skill_id"]
        if skill_id in skill_ids:
            raise ValueError(f"duplicate skill_id: {skill_id}")
        skill_ids.add(skill_id)
        for xid in [metadata["xid"], *metadata.get("aliases", [])]:
            if xid in xid_index:
                raise ValueError(f"duplicate definition XID or alias: {xid}")
            xid_index[xid] = skill_id
        entries.append({**metadata, "definition_ref": {
            "path": Path(path).as_posix(), "content_hash": definition["content_hash"],
        }})
    if not entries:
        raise ValueError("catalog requires at least one definition")
    entries.sort(key=lambda entry: entry["skill_id"])
    serialized = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"schema_version": 1, "entries": entries,
            "xid_index": dict(sorted(xid_index.items())),
            "catalog_hash": hashlib.sha256(serialized.encode("utf-8")).hexdigest()}


def cmd_definition(args) -> int:
    try:
        if args.skill_cmd == "definition-check":
            value = load_skill_definition(Path(args.path))
            result = {"ok": True, "metadata": value["metadata"],
                      "source": value["source"], "content_hash": value["content_hash"],
                      "method_bytes": len(value["method"].encode("utf-8")),
                      "runtime_activated": False}
        else:
            result = build_definition_catalog(Path(path) for path in args.path)
    except (ValueError, OSError, UnicodeError) as exc:
        print(json.dumps({"ok": False, "state": "blocked", "errors": [str(exc)]}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

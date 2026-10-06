"""Deterministic, metadata-only catalog for explicitly supplied SkillDefinitions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from collections.abc import Iterable

from xrefkit.skill_definition import load_skill_definition
from xrefkit.skill_definition_governance import (
    governance_projection,
    load_governance_record,
    match_definition,
)


def build_definition_catalog(paths: Iterable[Path], governance_paths: Iterable[Path] = ()) -> dict:
    paths = [Path(path) for path in paths]
    governance_paths = [Path(path) for path in governance_paths]
    if len(governance_paths) != len(set(governance_paths)):
        raise ValueError("duplicate governance record path")
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
    governance_by_identity = {}
    for governance_path in governance_paths:
        record = load_governance_record(governance_path)
        key = (record["skill_id"], record["definition_xid"])
        if key in governance_by_identity:
            raise ValueError(f"duplicate governance record: {key[0]}")
        governance_by_identity[key] = record
    if not entries:
        raise ValueError("catalog requires at least one definition")
    definition_keys = {(entry["skill_id"], entry["xid"]) for entry in entries}
    unmatched = set(governance_by_identity) - definition_keys
    if unmatched:
        raise ValueError(f"unmatched governance record: {sorted(unmatched)[0][0]}")
    for entry, path in zip(entries, paths):
        definition = load_skill_definition(path)
        key = (entry["skill_id"], entry["xid"])
        record = governance_by_identity.get(key)
        if record is not None:
            match_definition(record, definition)
        entry["governance"] = governance_projection(record) if record else None
        entry["maturity"] = record["maturity"] if record else "unassessed"
    entries.sort(key=lambda entry: entry["skill_id"])
    serialized = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"schema_version": 1, "entries": entries,
            "xid_index": dict(sorted(xid_index.items())),
            "catalog_hash": hashlib.sha256(serialized.encode("utf-8")).hexdigest()}


def cmd_definition(args) -> int:
    try:
        if args.skill_cmd == "definition-check":
            value = load_skill_definition(Path(args.path))
            governance = None
            if args.governance:
                if len(args.governance) != 1:
                    raise ValueError("definition-check accepts exactly one --governance record")
                governance = load_governance_record(Path(args.governance[0]))
                match_definition(governance, value)
            result = {"ok": True, "metadata": value["metadata"],
                      "source": value["source"], "content_hash": value["content_hash"],
                      "method_bytes": len(value["method"].encode("utf-8")),
                      "runtime_activated": False,
                      "governance": governance_projection(governance) if governance else None,
                      "maturity": governance["maturity"] if governance else "unassessed"}
        else:
            result = build_definition_catalog((Path(path) for path in args.path), (Path(path) for path in (args.governance or [])))
    except (ValueError, OSError, UnicodeError) as exc:
        print(json.dumps({"ok": False, "state": "blocked", "errors": [str(exc)]}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

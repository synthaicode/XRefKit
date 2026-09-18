"""Reproducible, non-activating conversion of the representative .NET Skill.

The source stays authoritative until runtime integration and semantic migration
review. Candidate files are isolated under work/ and never installed by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from xrefkit.skillmeta import _parse_meta_lines
from xrefkit.skill_definition import parse_skill_definition
from xrefkit.skill_definition_catalog import build_definition_catalog


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def convert(root: Path, out: Path) -> dict:
    root = root.resolve()
    out = (root / out).resolve()
    if not out.is_relative_to(root / "work"):
        raise ValueError("migration candidates must stay below root/work")
    folder = root / "skills/dotnet_change_analysis"
    meta_raw = (folder / "meta.md").read_bytes()
    method_raw = (folder / "SKILL.md").read_bytes()
    meta_text = meta_raw.decode("utf-8-sig")
    method = method_raw.decode("utf-8")
    meta = _parse_meta_lines(meta_text)
    skill_xid = re.search(r"<!-- xid: ([A-F0-9]{12}) -->", method).group(1)
    meta_xid = re.search(r"<!-- xid: ([A-F0-9]{12}) -->", meta_text).group(1)
    needs = []
    for slot in meta["knowledge_slots"]:
        match = re.fullmatch(r"name=([^;]+); bind=([A-F0-9]{12})", slot)
        if not match:
            raise ValueError("representative knowledge slot format changed")
        name, xid = match.groups()
        needs.append({"id": name, "query": name.replace("_", " "),
                      "required_when": "Required by this Skill; resolve applicable material before claiming coverage",
                      "seed_xids": [xid]})
    closure = method.split("## Closure Gate", 1)[1].split("## Handoff", 1)[0]
    statements = [" ".join(part.strip().splitlines()) for part in re.findall(
        r"^- (.*(?:\n(?!- |## ).+)*)", closure, re.MULTILINE)]
    if len(statements) != 9:
        raise ValueError("representative closure conditions changed; review conversion")
    metadata = {
        "schema_version": 1, "skill_id": meta["skill_id"], "xid": skill_xid,
        "aliases": [meta_xid], "summary": meta["summary"],
        "applies_when": [meta["use_when"]],
        "exclusions": ["Defect-level review belongs to csharp_review",
                       "Vulnerability assessment belongs to security_review",
                       "Implementation policy is not decided unless explicitly requested"],
        "inputs": [meta["input"]], "outputs": [meta["output"]],
        "criteria": [{"id": f"closure_{i}", "statement": statement,
                      "verification": "Record evidence and apply the existing Workflow verification and closure gates"}
                     for i, statement in enumerate(statements, 1)],
        "knowledge_needs": needs,
        "control_refs": ["B7A2C94F0E61", "A7F3C92D4E11", "6B2D9F4A1C73"],
    }
    candidate = "---\n" + json.dumps(metadata, ensure_ascii=False, indent=2) + "\n---\n" + method
    parsed = parse_skill_definition(candidate)
    assert parsed["method"].encode("utf-8") == method_raw
    targets = {
        "skill_id": "header.skill_id", "summary": "header.summary", "use_when": "header.applies_when",
        "input": "header.inputs", "output": "header.outputs", "knowledge_slots": "header.knowledge_needs",
        "skill_doc": "inline method", "constraints": "method Purpose/Rules/Context Direction Guard",
        "lifecycle": "method Startup/Planning/Execution/Monitoring and Control/Closure Gate",
        "workflow_protocol": "header.control_refs -> existing Workflow Protocol",
        "os_contract": "header.control_refs -> Skill Operating Contract",
    }
    dynamic = {"tuning", "responsibility", "capability_layering", "execution_mode", "model_tier"}
    coverage = []
    for key, value in meta.items():
        destination = targets.get(key, "migration provenance (not active routing metadata)")
        state = "mapped" if key in targets else "retained_in_provenance"
        if key in dynamic:
            destination = "runtime binding/routing responsibility; legacy value retained only in provenance"
            state = "runtime_cutover_pending"
        coverage.append({"source_key": key, "source_value": value,
                         "destination": destination, "state": state})
    manifest = {
        "status": "migration_candidate", "runtime_activated": False,
        "source_skill": "skills/dotnet_change_analysis/SKILL.md",
        "source_meta": "skills/dotnet_change_analysis/meta.md",
        "source_method_sha256": digest(method_raw), "source_meta_sha256": digest(meta_raw),
        "method_preserved_byte_for_byte": True,
        "source_sections": re.findall(r"^## (.+)$", method, re.MULTILINE),
        "meta_coverage": coverage,
        "remaining": ["Review semantic ownership and remove copied common control only with coverage",
                      "Connect new definition to run/Skill resolution before replacing legacy source",
                      "Integrate runtime model requirements and Knowledge catalog selection"],
    }
    payloads = {"SKILL.md": candidate.encode("utf-8"),
                "migration.json": json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")}
    # Validate every replacement before any write; never overwrite an edited candidate.
    for name, raw in payloads.items():
        target = out / name
        if target.exists() and target.read_bytes() != raw:
            raise ValueError(f"candidate already exists with different content: {target}")
    out.mkdir(parents=True, exist_ok=True)
    for name, raw in payloads.items():
        (out / name).write_bytes(raw)
    catalog = build_definition_catalog([out / "SKILL.md"])
    return {"candidate": str(out / "SKILL.md"), "manifest": str(out / "migration.json"),
            "catalog": catalog, "runtime_activated": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=Path("work/skill-definition-candidate/dotnet_change_analysis"))
    args = parser.parse_args()
    try:
        result = convert(args.root, args.out)
    except (ValueError, OSError, KeyError, IndexError, AttributeError) as exc:
        parser.exit(1, f"conversion blocked: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

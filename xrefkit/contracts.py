"""Compile and verify model-facing base runtime contract resources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml


SCHEMA = "xrefkit.base_runtime/v1"
GENERATED_SCHEMA = "xrefkit.compiled_runtime/v1"
NORMATIVE_RE = re.compile(r"\bMUST(?:\s+NOT)?\b")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_manifest(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError(f"unsupported base runtime manifest: {path}")
    return data


def _estimate_tokens(text: str) -> int:
    return (len(text) + 3) // 4


def compile_base_runtime(
    repo_root: str | Path,
    manifest_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    manifest_file = Path(manifest_path)
    if not manifest_file.is_absolute():
        manifest_file = root / manifest_file
    manifest = _load_manifest(manifest_file)
    sources: dict[str, dict[str, Any]] = {}
    source_texts: dict[str, str] = {}
    for source in manifest.get("sources", []):
        xid = str(source["xid"])
        path = root / str(source["path"])
        body = path.read_text(encoding="utf-8")
        if f"xid: {xid}" not in body:
            raise ValueError(f"source XID mismatch: {path} expected {xid}")
        sources[xid] = {
            "xid": xid,
            "path": str(source["path"]),
            "source_hash": _sha256(body.encode("utf-8")),
        }
        source_texts[xid] = body

    obligations: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    covered_lines: dict[str, set[str]] = {xid: set() for xid in sources}
    for item in manifest.get("obligations", []):
        obligation_id = str(item["id"])
        if obligation_id in seen_ids:
            raise ValueError(f"duplicate obligation id: {obligation_id}")
        seen_ids.add(obligation_id)
        source_xid = str(item["source_xid"])
        if source_xid not in source_texts:
            raise ValueError(f"unknown obligation source XID: {source_xid}")
        source_match = str(item["source_match"])
        matching = [line.strip() for line in source_texts[source_xid].splitlines() if source_match in line]
        if not matching:
            raise ValueError(f"obligation source_match not found: {obligation_id}")
        covered_lines[source_xid].update(matching)
        obligations.append(
            {
                "id": obligation_id,
                "source_xid": source_xid,
                "level": str(item["level"]),
                "statement": str(item["statement"]),
            }
        )

    lint_candidates: list[dict[str, Any]] = []
    for xid, body in source_texts.items():
        for line_number, line in enumerate(body.splitlines(), start=1):
            stripped = line.strip()
            if NORMATIVE_RE.search(stripped) and stripped not in covered_lines[xid]:
                lint_candidates.append(
                    {
                        "source_xid": xid,
                        "line": line_number,
                        "text": stripped,
                        "status": "pending",
                    }
                )

    body_lines = ["# XRefKit Base Runtime Contract", ""]
    for item in obligations:
        body_lines.append(f"- [{item['level']}] {item['id']}: {item['statement']}")
    conditional = manifest.get("conditional_loads", [])
    if conditional:
        body_lines.extend(["", "Conditional loads:"])
        for item in conditional:
            body_lines.append(f"- {item['when']}: xid {item['xid']}")
    model_body = "\n".join(body_lines) + "\n"
    budgets = dict(manifest.get("budgets", {}))
    estimated_tokens = _estimate_tokens(model_body)
    approval = dict(manifest.get("approval", {}))
    result = {
        "schema": GENERATED_SCHEMA,
        "profile": manifest.get("profile", "model-compact"),
        "compiler_version": manifest.get("compiler_version", 1),
        "manifest_path": str(manifest_file.relative_to(root)),
        "manifest_hash": _sha256(manifest_file.read_bytes()),
        "approval": approval,
        "estimator": manifest.get("estimator", {}),
        "budgets": budgets,
        "sources": list(sources.values()),
        "obligations": obligations,
        "conditional_loads": conditional,
        "lint_candidates": lint_candidates,
        "model_body_hash": _sha256(model_body.encode("utf-8")),
        "estimated_tokens": estimated_tokens,
        "release_ready": approval.get("status") == "accepted" and not lint_candidates,
    }
    output = Path(output_dir)
    if not output.is_absolute():
        output = root / output
    output.mkdir(parents=True, exist_ok=True)
    (output / "contracts.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    (output / "model_body.md").write_text(model_body, encoding="utf-8")
    return result


def verify_base_runtime(
    repo_root: str | Path,
    manifest_path: str | Path,
    output_dir: str | Path,
    *,
    release: bool,
) -> dict[str, Any]:
    result = compile_base_runtime(repo_root, manifest_path, output_dir)
    errors: list[str] = []
    expected_ids = {item["id"] for item in result["obligations"]}
    generated_path = Path(output_dir)
    if not generated_path.is_absolute():
        generated_path = Path(repo_root) / generated_path
    generated = json.loads((generated_path / "contracts.json").read_text(encoding="utf-8"))
    generated_ids = {item["id"] for item in generated["obligations"]}
    if expected_ids != generated_ids:
        errors.append("compiled obligation ID set differs from manifest")
    l0_budget = int(result["budgets"].get("l0_tokens", 0))
    if not l0_budget or result["estimated_tokens"] > l0_budget:
        errors.append(
            f"L0 token budget exceeded: {result['estimated_tokens']} > {l0_budget}"
        )
    if release:
        if result["approval"].get("status") != "accepted":
            errors.append("runtime budget and manifest approval is not accepted")
        if result["lint_candidates"]:
            errors.append(f"pending normative lint candidates: {len(result['lint_candidates'])}")
    return {**result, "ok": not errors, "errors": errors, "release": release}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit pack")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("build-base", "verify-base"):
        command = sub.add_parser(name)
        command.add_argument("--root", default=".")
        command.add_argument("--manifest", default="docs/core/contracts/base_runtime_manifest.yaml")
        command.add_argument("--output", default="xrefkit/resources/base")
        command.add_argument("--json", action="store_true")
        if name == "verify-base":
            command.add_argument("--draft", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "build-base":
            result = compile_base_runtime(args.root, args.manifest, args.output)
            result = {**result, "ok": True}
        else:
            result = verify_base_runtime(
                args.root,
                args.manifest,
                args.output,
                release=not args.draft,
            )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        print("ok" if result.get("ok") else "failed")
        for error in result.get("errors", []):
            print(f"- {error}")
    return 0 if result.get("ok") else 1

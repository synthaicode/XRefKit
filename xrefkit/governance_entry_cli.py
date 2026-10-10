"""Portable governance packets; trusted host/UI adapters provide assertions."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .governance_entry import apply_update, prepare, retrospective_suggestion, validate_result
from .mcp.contribution_adoption import HmacHumanApprovalVerifier


def _read(path: str) -> dict:
    raw = Path(path).read_bytes()
    if len(raw) > 512_000:
        raise ValueError("governance JSON exceeds size limit")
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError("duplicate governance JSON key")
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=pairs)
    if not isinstance(value, dict):
        raise ValueError("governance JSON must be an object")
    return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit governance")
    parser.add_argument("--root", default=".")
    subs = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "validate", "apply", "suggest"):
        sub = subs.add_parser(name)
        sub.add_argument("--request", required=True)
        sub.add_argument("--out", required=True)
        if name in {"validate", "apply"}:
            sub.add_argument("--receipt", required=True)
        if name == "apply":
            sub.add_argument("--approval-file", required=True)
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve()
        request = _read(args.request)
        output = Path(args.out).resolve()
        parts = output.relative_to(root).parts if output.is_relative_to(root) else ()
        if not parts or (parts[0] != "work" and parts[:2] != (".xrefkit", "governance-entries")):
            raise ValueError("output must be non-canonical within root")
        protected = {Path(args.request).resolve()}
        for field in ("log", "state_path"):
            if isinstance(request.get(field), str):
                protected.add((root / request[field]).resolve())
        for row in request.get("materials", []):
            protected.add((root / (row["path"] if isinstance(row, dict) else row)).resolve())
        payload = request.get("payload", {})
        if "target" in payload:
            protected.add((root / payload["target"]).resolve())
        receipt = None
        if args.command in {"validate", "apply"}:
            protected.add(Path(args.receipt).resolve())
            receipt = _read(args.receipt)
            event = receipt.get("event", {})
            if not isinstance(event, dict) or not isinstance(event.get("result", {}), dict):
                raise ValueError("invalid host receipt structure")
            for name in (event.get("child_log"), event.get("result", {}).get("output", {}).get("path")):
                if name:
                    protected.add((root / name).resolve())
        if args.command == "apply":
            protected.add(Path(args.approval_file).resolve())
        if output in protected:
            raise ValueError("output would overwrite protected governance input")
        output.parent.mkdir(parents=True, exist_ok=True)
        # Reserve evidence destination before a canonical application can occur.
        # Existing/unwritable/directory destinations reject before any target write.
        with output.open("x", encoding="utf-8") as reserved:
            reserved.write('{"status":"entry_started"}\n')
        application_done = False
        if args.command == "prepare":
            result = prepare(root, **request)
        elif args.command == "suggest":
            result = retrospective_suggestion(root, **request)
        else:
            host = HmacHumanApprovalVerifier(os.environ.get("XREFKIT_GOVERNANCE_HOST_SECRET", ""))
            if args.command == "validate":
                result = validate_result(root, request, receipt, host)
            else:
                human = HmacHumanApprovalVerifier(os.environ.get("XREFKIT_GOVERNANCE_HUMAN_SECRET", ""))
                if os.environ["XREFKIT_GOVERNANCE_HOST_SECRET"] == os.environ["XREFKIT_GOVERNANCE_HUMAN_SECRET"]:
                    raise ValueError("host and human authority keys must be separate")
                result = apply_update(root, request, receipt, host_verifier=host,
                                      approval_verifier=human,
                                      approval_assertion=Path(args.approval_file).read_text().strip())
                application_done = True
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        if locals().get("application_done", False):
            print("canonical application completed but reflection evidence save failed")
            print(json.dumps(result, ensure_ascii=False))
            return 3
        print(f"governance entry rejected: {exc}")
        return 2

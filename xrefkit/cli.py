"""Unified command dispatcher for the XRefKit package."""

from __future__ import annotations

import sys
from collections.abc import Sequence


_OPERATIONS = {"xref", "ctx", "goal", "gate", "pack", "dashboard", "analysis", "skill", "workflow", "host", "trace"}
_V2 = {"package", "show"}


def _print_help() -> None:
    print(
        "usage: xrefkit <command> ...\n\n"
        "commands:\n"
        "  init       initialize or validate an XRefKit instance\n"
        "  xref       manage XIDs and references\n"
        "  wbs        validate and summarize a Markdown WBS\n"
        "  ctx        build compact context packs\n"
        "  gateway    prepare inputs, route model work, and evaluate retry feedback\n"
        "  skill      discover, validate, run, verify, and close Skills\n"
        "  workflow   run the generic protocol for instructions without a Skill\n"
        "  host       run host-compatibility evidence checks\n"
        "  tools      list and run XID-backed client tools\n"
        "  catalog    list and maintain Knowledge and structure catalogs\n"
        "  pack       validate and build runtime/content packs\n"
        "  gate       evaluate deterministic gates\n"
        "  goal       manage desired-state Goals and continuation state\n"
        "  dashboard  inspect runtime state\n"
        "  analysis   generate proposal-only observation reports\n"
        "  trace      AI protocol adapter for decision changes and Git checkpoints\n"
        "  attention-pet  run the local workload observability experiment\n"
        "  mcp        start the MCP server or initialize a client Prompt Flow\n"
        "  skills     synchronize released Skill and Knowledge bundles\n"
        "  package    inspect installed Skill packages\n"
        "  show       show effective Skill bundles"
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"-h", "--help"}:
        _print_help()
        return 0

    command = args[0]
    if args[:2] == ["skill", "reporting"]:
        from .reporting import main as reporting_main

        return reporting_main(args[2:])
    if command == "gateway":
        from .gateway import main as gateway_main

        return gateway_main(args[1:])
    if command == "pack" and len(args) > 1 and args[1] in {"build-base", "verify-base"}:
        from .contracts import main as contracts_main

        return contracts_main(args[1:])
    if command in _OPERATIONS:
        from .operations_cli import main as operations_main

        return operations_main(args)
    if command in _V2:
        from .v2_cli import main as v2_main

        return v2_main(args)
    if command == "init":
        from .instance import main as instance_main

        return instance_main(args[1:])
    if command == "tools":
        from .tools import main as tools_main

        return tools_main(args[1:])
    if command == "wbs":
        from .wbs import main as wbs_main

        return wbs_main(args[1:])
    if command == "catalog":
        from .catalog_cli import main as catalog_main

        return catalog_main(args[1:])
    if command == "mcp" and len(args) > 1 and args[1] == "flow-init":
        from .operations_cli import main as operations_main

        return operations_main(args)
    if command == "mcp":
        from .mcp import main as mcp_main

        return mcp_main(args[1:])
    if command == "attention-pet":
        from .attention_pet.__main__ import main as attention_pet_main

        return attention_pet_main(args[1:])
    if command == "skills":
        from .skills_sync import main as skills_main

        return skills_main(args[1:])

    print(f"xrefkit: unknown command: {command}", file=sys.stderr)
    _print_help()
    return 2

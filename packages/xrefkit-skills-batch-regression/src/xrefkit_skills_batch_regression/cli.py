"""Convenience entry point for the bundled deterministic batch tool."""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "install-mcp-skill":
        from .mcp_materialize import main as install

        return install(argv[1:])
    scripts = Path(__file__).parent / "skill_assets" / "scripts"
    sys.path.insert(0, str(scripts))
    from batch_regression import main as run  # type: ignore

    return run(argv)

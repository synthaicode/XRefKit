"""Convenience entry point for the bundled deterministic batch tool."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    scripts = Path(__file__).parent / "skill_assets" / "scripts"
    sys.path.insert(0, str(scripts))
    from batch_regression import main as run  # type: ignore

    return run()

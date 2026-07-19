"""XRefKit Skill Package for brownfield change workflow."""

from __future__ import annotations

from pathlib import Path


def package_root() -> Path:
    """Return the installed package root containing package_manifest.yaml."""

    return Path(__file__).parent

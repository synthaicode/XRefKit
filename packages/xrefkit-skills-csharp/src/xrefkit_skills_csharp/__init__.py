"""Text-only XRefKit Skill Package for C# and .NET analysis."""

from __future__ import annotations

from pathlib import Path


def package_root() -> Path:
    """Return the package asset root containing package_manifest.yaml."""

    return Path(__file__).parent

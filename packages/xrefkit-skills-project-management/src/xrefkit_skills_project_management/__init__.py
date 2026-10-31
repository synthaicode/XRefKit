"""Native Project Management Skill Package; discovery does not grant execution."""
from pathlib import Path


def package_root() -> Path:
    return Path(__file__).parent

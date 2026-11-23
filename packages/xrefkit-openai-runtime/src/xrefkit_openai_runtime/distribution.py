"""The reviewed Windows profile shipped with the optional Runtime."""

from pathlib import Path


PROFILE = Path(__file__).with_name("windows_profile")
CORE_LOCK = PROFILE / "core-lock.json"
STARTUP_CONTRACT = PROFILE / "startup-contract.md"
STARTUP_SHA256 = "30941d712838526a2767b7e1b80fde25c1e180135d4ace6fa370a26f7c5fbe95"

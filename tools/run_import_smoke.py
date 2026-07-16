"""Import an installed package while blocking common import-time side effects.

The caller must run this from a temporary working directory with ``python -B``
so the check does not create bytecode in the source checkout.  This is a smoke
test, not a sandbox: it catches common accidental writes, process starts, and
network connections made during import without claiming to prove that arbitrary
code is safe.
"""

from __future__ import annotations

import argparse
import builtins
import importlib
import importlib.metadata
import io
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from collections.abc import Callable
from typing import Any


class SideEffectError(RuntimeError):
    """Raised when imported code attempts a blocked external side effect."""


def _blocked(operation: str) -> Callable[..., Any]:
    def deny(*args: Any, **kwargs: Any) -> Any:
        raise SideEffectError(f"import attempted blocked {operation}")

    return deny


def _guard_open(original: Callable[..., Any]) -> Callable[..., Any]:
    def guarded(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            raise SideEffectError(f"import attempted blocked file write: {file}")
        return original(file, mode, *args, **kwargs)

    return guarded


def _guard_os_open(original: Callable[..., Any]) -> Callable[..., Any]:
    write_flags = (
        getattr(os, "O_WRONLY", 1)
        | getattr(os, "O_RDWR", 2)
        | getattr(os, "O_APPEND", 0)
        | getattr(os, "O_CREAT", 0)
        | getattr(os, "O_TRUNC", 0)
    )

    def guarded(path: Any, flags: int, *args: Any, **kwargs: Any) -> Any:
        if flags & write_flags:
            raise SideEffectError(f"import attempted blocked os.open write: {path}")
        return original(path, flags, *args, **kwargs)

    return guarded


def _guard_popen(original: type[subprocess.Popen]) -> type[subprocess.Popen]:
    class GuardedPopen(original):  # type: ignore[misc,valid-type]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise SideEffectError("import attempted blocked subprocess.Popen")

    GuardedPopen.__name__ = "Popen"
    GuardedPopen.__qualname__ = "Popen"
    return GuardedPopen


def install_guards() -> None:
    """Patch common process, network, and filesystem mutation entry points."""

    builtins.open = _guard_open(builtins.open)  # type: ignore[assignment]
    io.open = _guard_open(io.open)  # type: ignore[assignment]
    os.open = _guard_os_open(os.open)  # type: ignore[assignment]

    for module, names in (
        (
            os,
            (
                "system",
                "popen",
                "remove",
                "unlink",
                "rmdir",
                "mkdir",
                "makedirs",
                "rename",
                "replace",
                "chdir",
                "startfile",
            ),
        ),
        (
            subprocess,
            ("run", "call", "check_call", "check_output", "getoutput", "getstatusoutput"),
        ),
        (
            shutil,
            ("copy", "copy2", "copyfile", "copytree", "move", "rmtree"),
        ),
    ):
        for name in names:
            if hasattr(module, name):
                setattr(module, name, _blocked(f"{module.__name__}.{name}"))

    subprocess.Popen = _guard_popen(subprocess.Popen)  # type: ignore[assignment]

    if hasattr(os, "spawnv"):
        os.spawnv = _blocked("os.spawnv")  # type: ignore[assignment]
    if hasattr(os, "spawnve"):
        os.spawnve = _blocked("os.spawnve")  # type: ignore[assignment]
    if hasattr(os, "execv"):
        os.execv = _blocked("os.execv")  # type: ignore[assignment]
    if hasattr(os, "execve"):
        os.execve = _blocked("os.execve")  # type: ignore[assignment]

    for name in (
        "write_text",
        "write_bytes",
        "touch",
        "mkdir",
        "unlink",
        "rmdir",
        "rename",
        "replace",
    ):
        if hasattr(Path, name):
            setattr(Path, name, _blocked(f"pathlib.Path.{name}"))

    for name in ("connect", "connect_ex", "send", "sendall", "sendto"):
        setattr(socket.socket, name, _blocked(f"socket.socket.{name}"))
    for name in ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex"):
        if hasattr(socket, name):
            setattr(socket, name, _blocked(f"socket.{name}"))


def snapshot(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-name", required=True, help="installed distribution name")
    parser.add_argument("--import-module", action="append", required=True)
    parser.add_argument(
        "--version-module",
        help="module whose __version__ must match installed metadata, when present",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path.cwd()
    before = snapshot(root)
    install_guards()
    try:
        metadata_version = importlib.metadata.version(args.package_name)
        for module_name in args.import_module:
            importlib.import_module(module_name)
            print(f"import ok: {module_name}")
        if args.version_module:
            module = sys.modules[args.version_module]
            module_version = getattr(module, "__version__", None)
            if module_version is not None and module_version != metadata_version:
                raise RuntimeError(
                    f"version mismatch: metadata={metadata_version!r}, "
                    f"{args.version_module}.__version__={module_version!r}"
                )
            print(f"version ok: {args.package_name}={metadata_version}")
    except (ImportError, SideEffectError, RuntimeError) as exc:
        print(f"import smoke test failed: {exc}", file=sys.stderr)
        return 1
    after = snapshot(root)
    created = sorted(after - before)
    if created:
        print("import smoke test failed: import created files:", file=sys.stderr)
        for path in created:
            print(f"- {path}", file=sys.stderr)
        return 1
    print("import smoke test passed: imports, version, and side-effect guards succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

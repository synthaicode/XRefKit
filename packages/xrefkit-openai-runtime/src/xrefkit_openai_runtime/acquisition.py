"""Resolve the pinned Core Runtime before invoking a Core operation."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from contextlib import contextmanager
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import sysconfig
import time
import uuid


class AcquisitionError(RuntimeError):
    """Core could not be resolved from the selected source."""


class AcquisitionCancelled(AcquisitionError):
    """The Desktop origin was stopped during Core acquisition."""


def _check_stop(stop_requested: Callable[[], bool] | None) -> None:
    if stop_requested is not None and stop_requested():
        raise AcquisitionCancelled("Core acquisition stopped")


_PROBE = """
from contextlib import redirect_stdout
import importlib.metadata as metadata
import io, json, platform, re, sys, sysconfig
from pathlib import Path
import xrefkit.cli as cli
import xrefkit.execution_binding as binding
import xrefkit.operations_cli as operations

core = metadata.distribution('xrefkit')
declared = {Path(core.locate_file(file)).resolve() for file in core.files or ()}
if any(Path(module.__file__).resolve() not in declared for module in (cli, binding, operations)):
    raise SystemExit(1)
if not all(callable(f) for f in (cli.main, operations.main, binding.build_execution_binding,
                                 binding.validate_binding_context)):
    raise SystemExit(1)
for command in ('run', 'bind-execution'):
    with redirect_stdout(io.StringIO()) as output:
        try:
            status = cli.main(['workflow', command, '--help'])
        except SystemExit as exc:
            status = exc.code
    if status != 0 or not re.search(r'^usage: .*workflow ' + command + r'\\b', output.getvalue(), re.M):
        raise SystemExit(1)
# These reviewed public builds emit schema_version 1 and predate the constant.
legacy_revision = {'0.7.12': 1, '0.7.13': 1}.get(core.version)
revision = getattr(binding, 'BINDING_SCHEMA_VERSION', legacy_revision)
print(json.dumps({
    'version': core.version, 'binding_schema_version': revision,
    'target': f"{sys.implementation.name}-{platform.python_version()}-{sysconfig.get_platform()}",
    'packages': sorted((re.sub(r'[-_.]+', '-', dist.metadata['Name']).lower(), dist.version)
                       for dist in metadata.distributions()),
}))
"""
_PACKAGE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_VERSION = re.compile(r"[0-9][a-zA-Z0-9.+!]*")
_DIGEST = re.compile(r"[0-9a-f]{64}")


def _target() -> str:
    return f"{sys.implementation.name}-{platform.python_version()}-{sysconfig.get_platform()}"


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _read_lock(path: Path) -> tuple[str, str, str, dict[str, str]]:
    raw = path.read_bytes()
    lock = json.loads(raw)
    if not isinstance(lock, dict) or type(lock.get("schema")) is not int or lock["schema"] != 1 or lock.get("target") != _target():
        raise AcquisitionError(f"unsupported lock schema or Python target; expected {_target()}")
    packages = lock.get("packages")
    if not isinstance(packages, dict) or "xrefkit" not in packages:
        raise AcquisitionError("lock must include the xrefkit package")
    lines = []
    versions = {}
    for name, pin in sorted(packages.items()):
        if not isinstance(pin, dict):
            raise AcquisitionError(f"invalid lock pin for {name}")
        version, hashes = pin.get("version"), pin.get("sha256")
        if (
            not _PACKAGE.fullmatch(name)
            or not isinstance(version, str) or not _VERSION.fullmatch(version)
            or not isinstance(hashes, list) or not hashes
            or any(not isinstance(h, str) or not _DIGEST.fullmatch(h) for h in hashes)
        ):
            raise AcquisitionError(f"invalid lock pin for {name}")
        options = " ".join(f"--hash=sha256:{h}" for h in hashes)
        lines.append(f"{name}=={version} {options}")
        versions[name] = version
    return packages["xrefkit"]["version"], hashlib.sha256(raw).hexdigest(), "\n".join(lines) + "\n", versions


def _default_cache() -> Path:
    if os.name == "nt":
        return Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "xrefkit-openai-runtime" / "Cache"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "xrefkit-openai-runtime"
    return Path(os.getenv("XDG_CACHE_HOME") or Path.home() / ".cache") / "xrefkit-openai-runtime"


@contextmanager
def _population_lock(path: Path, stop_requested=None):
    # Keep the lock file in place. The OS releases the lock when its owner exits.
    with path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt

            deadline = time.monotonic() + 600
            while True:
                _check_stop(stop_requested)
                stream.seek(0)
                try:
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as exc:
                    if exc.errno != errno.EACCES or time.monotonic() >= deadline:
                        raise
                    time.sleep(0.1)
        else:
            import fcntl

            while True:
                _check_stop(stop_requested)
                try:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    time.sleep(0.1)
        yield


@contextmanager
def _cancellable_child(command, *, cwd, env):
    options = dict(cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if os.name != "nt":
        with subprocess.Popen(command, start_new_session=True, **options) as child:
            try:
                yield child
            except BaseException:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                raise
        return

    from ._windows_job import kill_on_close_job

    # The launcher cannot start the requested command before the parent assigns
    # it to the job. The non-inherited job handle also closes if the adapter dies.
    gate = (
        "import subprocess, sys; "
        "raise SystemExit(subprocess.call(sys.argv[1:], stdin=subprocess.DEVNULL) "
        "if sys.stdin.read(1) == '1' else 1)"
    )
    child = None
    try:
        with kill_on_close_job() as assign:
            child = subprocess.Popen([sys.executable, "-I", "-S", "-B", "-c", gate, *command],
                                     stdin=subprocess.PIPE, **options)
            with child.stdin:
                assign(child.pid)
                child.stdin.write("1")
            child.stdin = None
            yield child
    finally:
        if child is not None:
            with child:
                pass


def _run(python: Path, args: list[str], *, step: str, cwd: Path | None = None,
         stop_requested=None) -> str:
    env = {
        k: v for k, v in os.environ.items()
        if not k.upper().startswith(("PIP_", "PYTHON", "OPENAI_"))
    }
    env["PIP_CONFIG_FILE"] = os.devnull
    command = [str(python), "-I", "-B", *args]
    _check_stop(stop_requested)
    try:
        if stop_requested is None:
            result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=300)
            status, stdout = result.returncode, result.stdout
        else:
            with _cancellable_child(command, cwd=cwd, env=env) as child:
                deadline = time.monotonic() + 300
                while True:
                    _check_stop(stop_requested)
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(command, 300)
                    try:
                        stdout, _ = child.communicate(timeout=min(0.1, remaining))
                        status = child.returncode
                        break
                    except subprocess.TimeoutExpired:
                        continue
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AcquisitionError(f"{step}: {type(exc).__name__}") from exc
    _check_stop(stop_requested)
    if status:
        raise AcquisitionError(f"{step} failed (exit {status})")
    return stdout.strip()


def _probe(python: Path, version: str, *, pins: dict[str, str] | None = None, stop_requested=None) -> int:
    code = _PROBE
    if pins is not None:
        code = "import sys\nif sys.prefix == sys.base_prefix: raise SystemExit(1)\n" + code
    result = json.loads(_run(python, ["-c", code], step="Core identity/interface check", stop_requested=stop_requested))
    if result["version"] != version or result["target"] != _target():
        raise AcquisitionError(f"Core version or target mismatch; expected {version} on {_target()}")
    revision = result["binding_schema_version"]
    if type(revision) is not int or revision != 1:
        raise AcquisitionError("unsupported Core binding schema")
    if pins is not None and result["packages"] != [list(pin) for pin in sorted(pins.items())]:
        raise AcquisitionError("installed runtime dependencies do not match reviewed pins")
    return revision


def _python(generation: Path) -> Path:
    return generation / "env" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _wheel_hashes(directory: Path) -> dict[str, str]:
    return {wheel.name: _digest(wheel) for wheel in sorted(directory.glob("*.whl"))}


def _stage_wheels(source: Path, destination: Path, stop_requested=None) -> Path:
    if not source.is_dir():
        raise AcquisitionError("offline wheelhouse is not a directory")
    destination.mkdir()
    for path in source.glob("*.whl"):
        _check_stop(stop_requested)
        if path.is_file() and not path.is_symlink():
            shutil.copyfile(path, destination / path.name)
    return destination


def _environment_digest(generation: Path, stop_requested=None) -> str:
    # Check startup files and installed packages before running the cached Python.
    env = generation / "env"
    if not _python(generation).is_file() or not (env / "pyvenv.cfg").is_file():
        raise AcquisitionError("isolated interpreter is incomplete")
    entries = []
    for path in sorted(env.rglob("*")):
        _check_stop(stop_requested)
        relative = path.relative_to(env).as_posix()
        if path.is_symlink():
            # Python's POSIX venv creates this internal alias on some targets.
            if relative != "lib64" or path.readlink() != Path("lib"):
                raise AcquisitionError("unexpected link in managed environment")
            entries.append((relative, "link:lib"))
        elif path.is_file():
            entries.append((relative, _digest(path)))
    base_python = _digest(Path(sys._base_executable).resolve())
    return hashlib.sha256(json.dumps([base_python, entries]).encode()).hexdigest()


def _publish(staging: Path, destination: Path, record: dict) -> None:
    with staging.open("w", encoding="utf-8") as stream:
        json.dump(record, stream)
        stream.flush()
        os.fsync(stream.fileno())
    staging.replace(destination)


def resolve_core(
    lock_path: Path, *, local_python: Path | None = None, cache_dir: Path | None = None,
    offline: bool = False, wheelhouse: Path | None = None, refresh: bool = False,
    stop_requested: Callable[[], bool] | None = None,
) -> dict:
    """Resolve a reviewed lock supplied by the caller for this exact Python target."""
    _check_stop(stop_requested)
    version, lock_digest, requirements, versions = _read_lock(lock_path)
    evidence = {"schema": 1, "version": version, "target": _target(), "lock_sha256": lock_digest}
    if local_python is not None:
        # An explicit override is a pin. Fail closed rather than silently using another Runtime.
        python = local_python.absolute()
        revision = _probe(python, version, stop_requested=stop_requested)
        return {**evidence, "binding_schema_version": revision, "source": "local", "python": str(python)}

    entry = (cache_dir or _default_cache()).absolute() / version / lock_digest
    entry.mkdir(parents=True, exist_ok=True)
    ready = entry / "ready.json"
    with _population_lock(entry / "populate.lock", stop_requested):
        artifacts = entry / "artifacts.json"
        saved = None
        try:
            candidate = json.loads(artifacts.read_bytes())
            source_dir = entry / uuid.UUID(candidate["wheel_generation"]).hex / "wheels"
            if (source_dir.parent.name == candidate["wheel_generation"]
                    and candidate["wheels"] and _wheel_hashes(source_dir) == candidate["wheels"]):
                saved = candidate
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            pass

        if saved is not None and not refresh:
            try:
                record = json.loads(ready.read_bytes())
                generation = entry / uuid.UUID(record["generation"]).hex
                if (
                    all(record.get(key) == value for key, value in (evidence | saved).items())
                    and _environment_digest(generation, stop_requested) == record["environment_sha256"]
                ):
                    python = _python(generation)
                    revision = _probe(python, version, pins=versions, stop_requested=stop_requested)
                    if record.get("binding_schema_version") == revision:
                        return {**record, "source": "cache", "python": str(python)}
            except AcquisitionCancelled:
                raise
            except (OSError, ValueError, KeyError, TypeError, AttributeError, AcquisitionError):
                # Invalid or unpublished environments are never returned.
                pass

        if saved is None and wheelhouse is None and offline:
            raise AcquisitionError("offline cache miss: no verified wheels or offline wheelhouse")
        generation = entry / uuid.uuid4().hex
        generation.mkdir()
        pins = generation / "requirements.txt"
        pins.write_text(requirements, encoding="ascii")
        python = _python(generation)
        _run(Path(sys.executable), ["-m", "venv", "--copies", "--without-pip", str(generation / "env")],
             step="create isolated runtime", stop_requested=stop_requested)
        bootstrap_dir = generation / "installer"
        _run(Path(sys.executable), ["-m", "venv", str(bootstrap_dir)], step="create isolated installer",
             stop_requested=stop_requested)
        installer = bootstrap_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        pip = ["-m", "pip", "--disable-pip-version-check", "--no-cache-dir", "--no-input"]
        # The reviewed lock lists the entire dependency closure. Do not follow
        # dependency URLs from wheel metadata, including in offline mode.
        locked = ["--no-deps", "--require-hashes", "--only-binary=:all:", "-r", str(pins)]
        if saved is None:
            wheels = generation / "wheels"
            wheels.mkdir()
            index = ["--index-url", "https://pypi.org/simple"]
            if wheelhouse is not None:
                # pip parses HTML in find-links directories even with --no-index.
                staged = _stage_wheels(wheelhouse, generation / "source-wheels", stop_requested)
                index = ["--no-index", "--find-links", str(staged)]
            _run(installer, [*pip, "download", *locked, *index, "--dest", str(wheels)],
                 step="obtain compatible hash-pinned wheels", cwd=generation, stop_requested=stop_requested)
            saved = {
                "wheel_generation": generation.name,
                "artifact_source": "wheelhouse" if wheelhouse is not None else "pypi",
                "wheels": _wheel_hashes(wheels),
            }
            _check_stop(stop_requested)
            _publish(generation / "artifacts.json", artifacts, saved)
        else:
            wheels = _stage_wheels(entry / saved["wheel_generation"] / "wheels", generation / "source-wheels", stop_requested)
        target_pip = [*pip, "--python", str(python)]
        _run(installer, [*target_pip, "install", *locked, "--ignore-installed", "--no-index", "--no-compile", "--find-links", str(wheels)],
             step="install verified wheel set", cwd=generation, stop_requested=stop_requested)
        _run(installer, [*target_pip, "check"], step="check installed dependencies", cwd=generation, stop_requested=stop_requested)
        revision = _probe(python, version, pins=versions, stop_requested=stop_requested)
        record = {
            **evidence, **saved, "generation": generation.name, "binding_schema_version": revision,
            "environment_sha256": _environment_digest(generation, stop_requested),
        }
        _check_stop(stop_requested)
        _publish(generation / "ready.json", ready, record)
        return {**record, "source": saved["artifact_source"], "python": str(python)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    from .distribution import CORE_LOCK

    parser.add_argument("--lock", default=CORE_LOCK, type=Path,
                        help="reviewed target-specific Runtime lock JSON (default: bundled Windows lock)")
    parser.add_argument("--local-python", type=Path, help="explicit compatible Core interpreter")
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--offline", action="store_true", help="disable package index access")
    parser.add_argument("--refresh", action="store_true", help="rebuild the managed environment")
    parser.add_argument("--wheelhouse", type=Path, help="local source; disables index access")
    parser.add_argument("core_args", nargs=argparse.REMAINDER, help="optional Core CLI arguments after --")
    args = parser.parse_args(argv)
    try:
        result = resolve_core(args.lock, local_python=args.local_python, cache_dir=args.cache_dir,
                              offline=args.offline, wheelhouse=args.wheelhouse, refresh=args.refresh)
        core_args = args.core_args
        if core_args and core_args[0] == "--":
            core_args = core_args[1:]
        if core_args:
            # Preserve the Core operation's own output and exit status.
            return subprocess.run([result["python"], "-I", "-B", "-m", "xrefkit", *core_args]).returncode
        print(json.dumps(result))
        return 0
    except (AcquisitionError, OSError, ValueError) as exc:
        print(f"Runtime acquisition: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

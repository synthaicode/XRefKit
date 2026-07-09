"""Stdlib-only bootstrap client for XRefKit MCP artifact distribution.

This script is distributed by the XRefKit MCP server itself at
``GET <base-url>/dist/bootstrap.py``. It has no dependency on pip, PyPI, or
the ``mcp`` package: everything it needs is in the Python standard library,
so it works on networks where only the XRefKit MCP endpoint is reachable.

It downloads distributable artifacts (the xrefkit Skill-execution runtime and the
client-side tools) over plain HTTP GET from the server's ``/dist`` routes,
verifies their sha256 against the ``/dist/index.json`` manifest, and either
materializes the files into the target repository (default) or installs the
packages with ``pip --no-index``.

Package bytes never pass through an MCP tool result, so they never enter the
model context of an AI client driving this script.

Usage:

    python bootstrap.py --base-url https://host:8443 [--target .]
        [--mode materialize|pip] [--ca-file corp-ca.pem]
        [--startup-context startup.json]

``--startup-context`` additionally performs a minimal MCP handshake
(JSON-RPC over streamable HTTP, stdlib only) and saves the
``get_startup_context`` result, honoring the "startup context first"
ordering before artifacts are used.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import ssl
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


DIST_STATE_RELATIVE_PATH = ".xrefkit/dist-state.json"
MATERIALIZED_PACKAGE_KINDS = {"pip_package"}
# Package-metadata files at the archive root that describe the package
# itself and must not be materialized into the target repository root.
PACKAGE_METADATA_NAMES = {"pyproject.toml", "README.md"}


class BootstrapError(RuntimeError):
    pass


def _ssl_context(ca_file: str | None) -> ssl.SSLContext:
    if ca_file:
        return ssl.create_default_context(cafile=ca_file)
    return ssl.create_default_context()


def http_get(url: str, ca_file: str | None = None, headers: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, context=_ssl_context(ca_file)) as response:
        return response.read()


def http_post_json(
    url: str,
    payload: dict,
    ca_file: str | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[bytes, dict[str, str]]:
    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    request_headers.update(headers or {})
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    with urllib.request.urlopen(request, context=_ssl_context(ca_file)) as response:
        return response.read(), {key.lower(): value for key, value in response.headers.items()}


def parse_jsonrpc_response(raw: bytes) -> dict | None:
    """Parse a streamable-HTTP MCP response body (SSE or plain JSON)."""
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return None
    if not text.startswith("data:") and "\ndata:" not in text and "\rdata:" not in text:
        return json.loads(text)
    result: dict | None = None
    for line in text.splitlines():
        if not line.startswith("data:"):
            continue
        candidate = line[len("data:"):].strip()
        if not candidate:
            continue
        message = json.loads(candidate)
        if isinstance(message, dict) and ("result" in message or "error" in message):
            result = message
    return result


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def verify_sha256(content: bytes, expected: str, name: str) -> None:
    actual = sha256_hex(content)
    if actual != expected:
        raise BootstrapError(
            f"sha256 mismatch for {name}: expected {expected}, got {actual}. "
            "Do not use this artifact; the download is corrupt or the server "
            "content changed between the manifest read and the download."
        )


def fetch_index(base_url: str, ca_file: str | None) -> dict:
    raw = http_get(f"{base_url.rstrip('/')}/dist/index.json", ca_file)
    index = json.loads(raw.decode("utf-8"))
    if not isinstance(index, dict) or "artifacts" not in index:
        raise BootstrapError("unexpected /dist/index.json shape: missing 'artifacts'")
    return index


def _stripped_member_path(name: str) -> Path | None:
    """Strip the top-level package directory from an archive member name.

    Returns None for members that must not be materialized (package
    metadata, unsafe paths, directories).
    """
    normalized = name.replace("\\", "/")
    if normalized.endswith("/"):
        return None
    parts = [part for part in normalized.split("/") if part]
    if len(parts) < 2:
        return None
    stripped = parts[1:]
    if any(part in ("..", "") or ":" in part for part in stripped):
        return None
    if len(stripped) == 1 and stripped[0] in PACKAGE_METADATA_NAMES:
        return None
    return Path(*stripped)


def materialize_package_zip(content: bytes, target_root: Path) -> list[str]:
    """Extract a package zip into the target repo, stripping the package root.

    The archives are laid out as ``<package_root>/xrefkit/...`` or
    ``<package_root>/tools/...``; the returned relative paths are what was
    written under ``target_root``.
    """
    written: list[str] = []
    resolved_root = target_root.resolve()
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for member in archive.infolist():
            relative = _stripped_member_path(member.filename)
            if relative is None:
                continue
            destination = (resolved_root / relative).resolve()
            if resolved_root not in destination.parents and destination != resolved_root:
                raise BootstrapError(f"unsafe archive member path: {member.filename}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(member))
            written.append(relative.as_posix())
    return written


def pip_install(paths: list[Path]) -> None:
    if not paths:
        return
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-index",
        "--no-build-isolation",
        *[str(path) for path in paths],
    ]
    print(f"+ {' '.join(command)}")
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise BootstrapError(f"pip install failed with exit code {completed.returncode}")


def save_dist_state(target_root: Path, entries: list[dict]) -> Path:
    state_path = target_root / DIST_STATE_RELATIVE_PATH
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"artifacts": entries}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return state_path


def fetch_startup_context(base_url: str, mcp_path: str, ca_file: str | None) -> dict:
    """Minimal MCP streamable-HTTP handshake using only the stdlib."""
    endpoint = f"{base_url.rstrip('/')}{mcp_path}"
    raw, headers = http_post_json(
        endpoint,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "xrefkit-bootstrap", "version": "1"},
            },
        },
        ca_file,
    )
    initialize = parse_jsonrpc_response(raw)
    if not initialize or "result" not in initialize:
        raise BootstrapError(f"MCP initialize failed: {initialize!r}")
    session_id = headers.get("mcp-session-id")
    session_headers = {"mcp-session-id": session_id} if session_id else {}

    http_post_json(
        endpoint,
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        ca_file,
        session_headers,
    )
    raw, _headers = http_post_json(
        endpoint,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "get_startup_context", "arguments": {}},
        },
        ca_file,
        session_headers,
    )
    response = parse_jsonrpc_response(raw)
    if not response or "result" not in response:
        raise BootstrapError(f"get_startup_context failed: {response!r}")
    return response["result"]


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit-bootstrap", description=__doc__)
    parser.add_argument("--base-url", required=True, help="Server base URL, e.g. https://host:8443")
    parser.add_argument("--target", default=".", help="Client-side target repository root")
    parser.add_argument(
        "--mode",
        choices=["materialize", "pip"],
        default="materialize",
        help="materialize: write xrefkit/ and tools/ files into the target repo; "
        "pip: download packages and pip install them offline",
    )
    parser.add_argument("--ca-file", help="PEM CA bundle for a private/corporate CA")
    parser.add_argument(
        "--mcp-path",
        default="/mcp",
        help="Streamable HTTP MCP path on the same server",
    )
    parser.add_argument(
        "--startup-context",
        help="Also call get_startup_context over MCP JSON-RPC and save the result to this file",
    )
    args = parser.parse_args(argv)

    base_url = args.base_url.rstrip("/")
    target_root = Path(args.target)
    target_root.mkdir(parents=True, exist_ok=True)

    if args.startup_context:
        startup = fetch_startup_context(base_url, args.mcp_path, args.ca_file)
        Path(args.startup_context).write_text(
            json.dumps(startup, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"saved startup context to {args.startup_context}")

    index = fetch_index(base_url, args.ca_file)
    state_entries: list[dict] = []
    downloads: list[tuple[dict, bytes]] = []
    for artifact in index["artifacts"]:
        if artifact["kind"] not in MATERIALIZED_PACKAGE_KINDS | {"wheel"}:
            continue
        content = http_get(artifact["url"], args.ca_file)
        verify_sha256(content, artifact["sha256"], artifact["filename"])
        downloads.append((artifact, content))
        print(f"downloaded {artifact['filename']} ({len(content)} bytes, sha256 ok)")

    if args.mode == "materialize":
        for artifact, content in downloads:
            if artifact["kind"] != "pip_package":
                print(f"skipping {artifact['filename']}: wheels are pip-mode only")
                continue
            written = materialize_package_zip(content, target_root)
            print(f"materialized {len(written)} files from {artifact['filename']}")
            state_entries.append(
                {
                    "filename": artifact["filename"],
                    "package_id": artifact.get("package_id"),
                    "version": artifact.get("version"),
                    "sha256": artifact["sha256"],
                    "mode": "materialize",
                    "files": written,
                }
            )
    else:
        download_dir = target_root / ".xrefkit" / "dist"
        download_dir.mkdir(parents=True, exist_ok=True)
        saved_paths: list[Path] = []
        for artifact, content in downloads:
            path = download_dir / artifact["filename"]
            path.write_bytes(content)
            saved_paths.append(path)
            state_entries.append(
                {
                    "filename": artifact["filename"],
                    "package_id": artifact.get("package_id"),
                    "version": artifact.get("version"),
                    "sha256": artifact["sha256"],
                    "mode": "pip",
                }
            )
        pip_install(saved_paths)

    state_path = save_dist_state(target_root, state_entries)
    print(f"recorded dist state at {state_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except BootstrapError as error:
        print(f"bootstrap failed: {error}", file=sys.stderr)
        raise SystemExit(1)

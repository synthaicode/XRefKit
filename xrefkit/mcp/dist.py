"""Plain-HTTP artifact distribution routes served next to the MCP endpoint.

The MCP channel stays a context-distribution channel (small governance
text); executable artifacts (the xrefkit runtime package, client tools package,
optional third-party wheels, and the stdlib-only bootstrap script) are
served as ordinary HTTP downloads under ``/dist`` on the same server, so
package bytes never have to travel through an MCP tool result and therefore
never enter an AI client's model context.

Routes:

- ``GET /dist``            pip ``--find-links`` compatible HTML index
- ``GET /dist/index.json`` machine-readable manifest with sha256 hashes
- ``GET /dist/<filename>`` one artifact
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from .catalog import XRefCatalog


DIST_ROUTE_PATH = "/dist"
BOOTSTRAP_FILENAME = "bootstrap.py"


@dataclass(frozen=True)
class DistArtifact:
    filename: str
    kind: str  # "pip_package" | "bootstrap_script" | "wheel" | "extra_file"
    content: bytes
    sha256: str
    size_bytes: int
    package_id: str | None = None
    version: str | None = None
    install_command: str | None = None

    def manifest_entry(self, base_url: str) -> dict[str, object]:
        return {
            "filename": self.filename,
            "url": f"{base_url.rstrip('/')}{DIST_ROUTE_PATH}/{self.filename}",
            "kind": self.kind,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "package_id": self.package_id,
            "version": self.version,
            "install_command": self.install_command,
        }


class ArtifactDistribution:
    """Builds the artifact set live from the catalog's repository state."""

    def __init__(self, catalog: XRefCatalog, extra_dir: Path | None = None) -> None:
        self._catalog = catalog
        self._extra_dir = extra_dir
        self._bootstrap_source = (
            Path(__file__).parent / BOOTSTRAP_FILENAME
        ).read_text(encoding="utf-8")

    def artifacts(self) -> list[DistArtifact]:
        # Package artifacts are rebuilt from the live repository on each
        # request; the fixed zip timestamps in the catalog builders keep the
        # bytes (and therefore the sha256) stable for unchanged inputs.
        artifacts = [
            _package_artifact(self._catalog.get_xrefkit_runtime_pip_package()),
            _package_artifact(self._catalog.get_client_tool_pip_package()),
            _bootstrap_artifact(self._bootstrap_source),
        ]
        artifacts.extend(_extra_artifacts(self._extra_dir))
        return artifacts

    def get(self, filename: str) -> DistArtifact | None:
        for artifact in self.artifacts():
            if artifact.filename == filename:
                return artifact
        return None

    def index_manifest(self, base_url: str) -> dict[str, object]:
        return {
            "server": "xrefkit-mcp",
            "transport": "plain_http",
            "hash_algorithm": "sha256",
            "find_links_url": f"{base_url.rstrip('/')}{DIST_ROUTE_PATH}/",
            "bootstrap_url": (
                f"{base_url.rstrip('/')}{DIST_ROUTE_PATH}/{BOOTSTRAP_FILENAME}"
            ),
            "artifacts": [
                artifact.manifest_entry(base_url) for artifact in self.artifacts()
            ],
        }

    def index_html(self) -> str:
        # pip --find-links page: bare anchors with a sha256 fragment.
        links = "\n".join(
            f'<a href="{artifact.filename}#sha256={artifact.sha256}">{artifact.filename}</a><br/>'
            for artifact in self.artifacts()
        )
        return (
            "<!DOCTYPE html>\n<html><head><title>xrefkit-mcp dist</title></head>"
            f"<body>\n{links}\n</body></html>\n"
        )

    def describe_for_mcp(self, base_url: str) -> dict[str, object]:
        """The artifact_distribution block attached to get_startup_context."""
        base = base_url.rstrip("/")
        return {
            "transport": "plain_http",
            "base_url": base,
            "index_json_url": f"{base}{DIST_ROUTE_PATH}/index.json",
            "find_links_url": f"{base}{DIST_ROUTE_PATH}/",
            "bootstrap_url": f"{base}{DIST_ROUTE_PATH}/{BOOTSTRAP_FILENAME}",
            "bootstrap_run": (
                f"python {BOOTSTRAP_FILENAME} --base-url {base} --target ."
            ),
            "pip_install_example": (
                "python -m pip install --no-index --no-build-isolation "
                f"--find-links {base}{DIST_ROUTE_PATH}/ xrefkit"
            ),
            "artifacts": [
                {
                    key: value
                    for key, value in artifact.manifest_entry(base).items()
                }
                for artifact in self.artifacts()
            ],
            "instructions": [
                "Fetch artifacts out-of-band with plain HTTP GET (bootstrap "
                "script, curl, or pip --find-links), never through the "
                "get_*_bundle or get_*_pip_package MCP tools, so package "
                "bytes do not enter the model context.",
                "Verify each downloaded artifact against the sha256 in "
                "index.json before materializing or installing it.",
                f"First download {BOOTSTRAP_FILENAME} from bootstrap_url and "
                "run bootstrap_run in the client-side target repository; it "
                "verifies hashes and materializes xrefkit/ and tools/.",
                "These HTTP routes are outside MCP session ordering; the "
                "startup-context-first obligation still applies to the AI "
                "session driving the download.",
            ],
        }


def _package_artifact(package: dict[str, object]) -> DistArtifact:
    content = base64.b64decode(str(package["content_base64"]))
    return DistArtifact(
        filename=str(package["filename"]),
        kind="pip_package",
        content=content,
        sha256=str(package["content_hash"]),
        size_bytes=len(content),
        package_id=str(package["package_id"]),
        version=str(package["version"]),
        install_command=str(package["install_command"]),
    )


def _bootstrap_artifact(source: str) -> DistArtifact:
    from .repository import stable_hash

    content = source.encode("utf-8")
    return DistArtifact(
        filename=BOOTSTRAP_FILENAME,
        kind="bootstrap_script",
        content=content,
        sha256=stable_hash(source),
        size_bytes=len(content),
        install_command=f"python {BOOTSTRAP_FILENAME} --base-url <base-url> --target .",
    )


def _extra_artifacts(extra_dir: Path | None) -> list[DistArtifact]:
    """Operator-provided files (for example PyYAML wheels) mirrored as-is."""
    if extra_dir is None or not extra_dir.is_dir():
        return []
    from .catalog import hashlib_sha256_bytes

    artifacts: list[DistArtifact] = []
    for path in sorted(extra_dir.iterdir()):
        if not path.is_file():
            continue
        content = path.read_bytes()
        kind = "wheel" if path.suffix == ".whl" else "extra_file"
        artifacts.append(
            DistArtifact(
                filename=path.name,
                kind=kind,
                content=content,
                sha256=hashlib_sha256_bytes(content),
                size_bytes=len(content),
                install_command=(
                    f"python -m pip install --no-index {path.name}"
                    if kind == "wheel"
                    else None
                ),
            )
        )
    return artifacts


def add_dist_routes(starlette_app: object, dist: ArtifactDistribution, base_url: str) -> None:
    from starlette.responses import HTMLResponse, JSONResponse, Response
    from starlette.routing import Route

    async def index_html(_request: object) -> HTMLResponse:
        return HTMLResponse(dist.index_html())

    async def artifact_or_index(request: object) -> Response:
        filename = request.path_params["filename"]
        if filename == "index.json":
            return JSONResponse(dist.index_manifest(base_url))
        artifact = dist.get(filename)
        if artifact is None:
            return JSONResponse({"error": f"unknown artifact: {filename}"}, status_code=404)
        media_type = (
            "text/x-python" if artifact.filename.endswith(".py") else "application/zip"
        )
        return Response(
            artifact.content,
            media_type=media_type,
            headers={
                "X-Content-SHA256": artifact.sha256,
                "Content-Disposition": f'attachment; filename="{artifact.filename}"',
            },
        )

    routes = getattr(getattr(starlette_app, "router"), "routes")
    routes.append(Route(f"{DIST_ROUTE_PATH}", index_html, methods=["GET"]))
    routes.append(Route(f"{DIST_ROUTE_PATH}/", index_html, methods=["GET"]))
    routes.append(
        Route(f"{DIST_ROUTE_PATH}/{{filename}}", artifact_or_index, methods=["GET"])
    )

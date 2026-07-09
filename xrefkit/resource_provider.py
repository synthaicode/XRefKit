"""Mode-aware resource providers for XID resolution."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol
from importlib import resources


ProviderKind = Literal["repository", "instance", "content_pack", "package", "mcp"]
ResolverMode = Literal["repository", "installed", "mcp_only", "mcp_server"]
XID_RE = re.compile(r"<!--\s*xid:\s*([A-Fa-f0-9]{12})\s*-->")


def _hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@dataclass(frozen=True)
class Resource:
    xid: str
    body: str
    content_hash: str
    provider: str
    provider_kind: ProviderKind
    path: str | None = None


class ResourceProvider(Protocol):
    name: str
    kind: ProviderKind

    def get(self, xid: str) -> Resource | None: ...


class DirectoryProvider:
    def __init__(self, name: str, kind: ProviderKind, root: str | Path) -> None:
        self.name = name
        self.kind = kind
        self.root = Path(root).resolve()
        self._index: dict[str, Path] | None = None

    def _build(self) -> dict[str, Path]:
        index: dict[str, Path] = {}
        for path in sorted(self.root.rglob("*.md")):
            try:
                prefix = path.read_text(encoding="utf-8")[:512]
            except (OSError, UnicodeDecodeError):
                continue
            match = XID_RE.search(prefix)
            if not match:
                continue
            xid = match.group(1).upper()
            if xid in index:
                raise ValueError(f"duplicate XID in provider {self.name}: {xid}")
            index[xid] = path
        return index

    def get(self, xid: str) -> Resource | None:
        if self._index is None:
            self._index = self._build()
        path = self._index.get(xid.upper())
        if path is None:
            return None
        data = path.read_bytes()
        return Resource(
            xid=xid.upper(),
            body=data.decode("utf-8"),
            content_hash=_hash_bytes(data),
            provider=self.name,
            provider_kind=self.kind,
            path=str(path),
        )


class StaticProvider:
    def __init__(self, name: str, kind: ProviderKind, resources: dict[str, str]) -> None:
        self.name = name
        self.kind = kind
        self._resources = {xid.upper(): body for xid, body in resources.items()}

    def get(self, xid: str) -> Resource | None:
        body = self._resources.get(xid.upper())
        if body is None:
            return None
        return Resource(
            xid=xid.upper(),
            body=body,
            content_hash=_hash_bytes(body.encode("utf-8")),
            provider=self.name,
            provider_kind=self.kind,
        )


class CompiledContractProvider(StaticProvider):
    """Resolve compact base-runtime XIDs from installed package resources."""

    @classmethod
    def installed(cls) -> "CompiledContractProvider":
        contract_file = resources.files("xrefkit").joinpath("resources/base/contracts.json")
        compiled = json.loads(contract_file.read_text(encoding="utf-8"))
        obligations_by_xid: dict[str, list[dict[str, object]]] = {}
        for obligation in compiled.get("obligations", []):
            obligations_by_xid.setdefault(obligation["source_xid"], []).append(obligation)
        bodies: dict[str, str] = {}
        for source in compiled.get("sources", []):
            xid = source["xid"]
            bodies[xid] = json.dumps(
                {
                    "xid": xid,
                    "compiled": True,
                    "source_hash": source["source_hash"],
                    "obligations": obligations_by_xid.get(xid, []),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        return cls("package-base", "package", bodies)


class ProviderResolver:
    def __init__(
        self,
        mode: ResolverMode,
        providers: list[ResourceProvider],
        *,
        base_xids: set[str] | None = None,
        allowed_shadows: dict[str, str] | None = None,
    ) -> None:
        self.mode = mode
        self.providers = providers
        self.base_xids = {xid.upper() for xid in (base_xids or set())}
        self.allowed_shadows = {xid.upper(): provider for xid, provider in (allowed_shadows or {}).items()}
        self._validate_graph()

    def _validate_graph(self) -> None:
        kinds = [provider.kind for provider in self.providers]
        if self.mode == "mcp_server" and "mcp" in kinds:
            raise ValueError("MCP server resolver must not contain an MCP provider")
        if self.mode == "mcp_only" and any(kind != "mcp" for kind in kinds):
            raise ValueError("mcp_only resolver may contain only MCP providers")
        if self.mode != "mcp_only" and kinds.count("mcp") > 1:
            raise ValueError("at most one MCP fallback provider is allowed")
        if "mcp" in kinds and kinds[-1] != "mcp":
            raise ValueError("MCP provider must be the final fallback")

    def resolve(self, xid: str) -> Resource:
        key = xid.upper()
        matches = [resource for provider in self.providers if (resource := provider.get(key)) is not None]
        if not matches:
            raise KeyError(f"unknown XID: {key}")
        hashes = {match.content_hash for match in matches}
        if len(hashes) == 1:
            return matches[0]
        if key in self.base_xids:
            raise ValueError(f"base runtime XID conflict cannot be shadowed: {key}")
        winner = self.allowed_shadows.get(key)
        if winner:
            for match in matches:
                if match.provider == winner:
                    return match
            raise ValueError(f"declared shadow provider not active for {key}: {winner}")
        names = ", ".join(match.provider for match in matches)
        raise ValueError(f"conflicting XID {key} from providers: {names}")


def verify_compiled_source_freshness(compiled_path: str | Path, repo_root: str | Path) -> list[str]:
    compiled = json.loads(Path(compiled_path).read_text(encoding="utf-8"))
    root = Path(repo_root)
    stale: list[str] = []
    for source in compiled.get("sources", []):
        path = root / source["path"]
        if not path.is_file() or _hash_bytes(path.read_bytes()) != source["source_hash"]:
            stale.append(source["xid"])
    return stale

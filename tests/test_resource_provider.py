from __future__ import annotations

import json
from pathlib import Path

import pytest

from xrefkit.resource_provider import (
    CompiledContractProvider,
    ProviderResolver,
    StaticProvider,
    verify_compiled_source_freshness,
)


def test_equal_duplicate_resources_deduplicate_by_provider_order() -> None:
    repository = StaticProvider("repo", "repository", {"A1234567890B": "same"})
    package = StaticProvider("package", "package", {"A1234567890B": "same"})

    result = ProviderResolver("repository", [repository, package]).resolve("A1234567890B")

    assert result.provider == "repo"


def test_conflicting_duplicate_fails_without_explicit_shadow() -> None:
    repository = StaticProvider("repo", "repository", {"A1234567890B": "local"})
    package = StaticProvider("package", "package", {"A1234567890B": "base"})

    with pytest.raises(ValueError, match="conflicting XID"):
        ProviderResolver("repository", [repository, package]).resolve("A1234567890B")


def test_explicit_non_base_shadow_selects_declared_provider() -> None:
    repository = StaticProvider("repo", "repository", {"A1234567890B": "local"})
    package = StaticProvider("package", "package", {"A1234567890B": "base"})

    result = ProviderResolver(
        "repository",
        [repository, package],
        allowed_shadows={"A1234567890B": "repo"},
    ).resolve("A1234567890B")

    assert result.body == "local"


def test_base_runtime_xid_cannot_be_shadowed() -> None:
    repository = StaticProvider("repo", "repository", {"A1234567890B": "local"})
    package = StaticProvider("package", "package", {"A1234567890B": "base"})

    with pytest.raises(ValueError, match="cannot be shadowed"):
        ProviderResolver(
            "repository",
            [repository, package],
            base_xids={"A1234567890B"},
            allowed_shadows={"A1234567890B": "repo"},
        ).resolve("A1234567890B")


def test_mcp_server_rejects_mcp_provider() -> None:
    remote = StaticProvider("remote", "mcp", {})

    with pytest.raises(ValueError, match="must not contain"):
        ProviderResolver("mcp_server", [remote])


def test_mcp_fallback_must_be_last() -> None:
    remote = StaticProvider("remote", "mcp", {})
    package = StaticProvider("package", "package", {})

    with pytest.raises(ValueError, match="final fallback"):
        ProviderResolver("installed", [remote, package])


def test_compiled_source_freshness_detects_change(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("before", encoding="utf-8")
    import hashlib

    compiled = tmp_path / "contracts.json"
    compiled.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "xid": "A1234567890B",
                        "path": "source.md",
                        "source_hash": hashlib.sha256(b"before").hexdigest(),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert verify_compiled_source_freshness(compiled, tmp_path) == []
    source.write_text("after", encoding="utf-8")
    assert verify_compiled_source_freshness(compiled, tmp_path) == ["A1234567890B"]


def test_installed_contract_provider_resolves_startup_xid() -> None:
    resource = CompiledContractProvider.installed().get("C3A1F78D9B22")

    assert resource is not None
    assert resource.provider_kind == "package"
    assert '"compiled": true' in resource.body

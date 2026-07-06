"""Minimal MCP-tool-compatible facade for XRefKit v2 MVP.

This module intentionally avoids an MCP SDK dependency.  It exposes plain
Python callables with MCP-tool-shaped inputs/outputs so PR 7 can wire them to a
real MCP server without changing resolver behavior.
"""

from __future__ import annotations

from .resolver import EffectiveSkillResolver
from .workspace import build_registry


def startup_get_contract() -> dict:
    return {
        "protocols": [
            "unknown_protocol",
            "workflow_protocol",
            "context_direction_security_guard",
            "startup_xref_routing",
            "xrefkit_startup_contract",
        ],
        "mode": "xrefkit_v2_mvp",
    }


def skill_resolve_entry(
    *,
    skill_id: str,
    package_manifests: list[str],
    local_manifest: str,
) -> dict:
    registry = build_registry(package_manifests=package_manifests, local_manifest_path=local_manifest)
    bundle = EffectiveSkillResolver(registry).resolve_entry(skill_id)
    return bundle.model_dump(mode="json")


def effective_skill_get(
    *,
    skill_id: str,
    package_manifests: list[str],
    local_manifest: str,
    mode: str = "entry",
) -> dict:
    if mode != "entry":
        raise NotImplementedError("MVP MCP facade only returns AI execution entry bundles; true full materialize is not implemented")
    return skill_resolve_entry(skill_id=skill_id, package_manifests=package_manifests, local_manifest=local_manifest)

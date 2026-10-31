"""Probe a genuinely installed Skill with the candidate Core, outside the repo."""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from importlib import metadata
from pathlib import Path


def verify_installed(name: str, package_id: str, core_version: str,
                     enabled_ids: set[str] | None = None) -> dict:
    import yaml
    from xrefkit.discovery import discover_skill_packages
    from xrefkit.models import LocalDomainSkill
    from xrefkit.resolver import EffectiveSkillResolver
    from xrefkit.workspace import CORE_PROTOCOL_VERSION, build_registry
    from xrefkit.models.common import version_satisfies
    from xrefkit.mcp.catalog import _build_package_skills
    from xrefkit.skill_definition import load_skill_definition as load_native

    if metadata.version("xrefkit") != core_version:
        raise ValueError("installed Core does not match candidate wheel")
    distribution = metadata.distribution(name)
    own_entries = [e for e in distribution.entry_points if e.group == "xrefkit.skill_packages"]
    if len(own_entries) != 1:
        raise ValueError(f"{name}: expected one installed Skill package entry point")
    discovered = discover_skill_packages()
    candidates = [p for p in discovered if p.package_id == package_id]
    if len(candidates) != 1:
        raise ValueError(f"{name}: missing or ambiguous package ID {package_id}")
    package = candidates[0]
    if package.entry_point_name != own_entries[0].name:
        raise ValueError("discovered entry point does not belong to distribution")
    if package.version != distribution.version:
        raise ValueError("manifest version differs from installed distribution")
    enabled = enabled_ids or {package_id}
    selected = [p for p in discovered if p.package_id in enabled]
    if {p.package_id for p in selected} != enabled:
        raise ValueError("missing enabled package")
    # Native v1 is an MCP distribution format, not legacy v2 inheritance.
    # Check all enabled identities/protocols together before format-specific probes.
    seen_ids, seen_xids = set(), set()
    legacy_ids = set()
    for candidate in selected:
        if not version_satisfies(CORE_PROTOCOL_VERSION, candidate.manifest.requires.xrefkit_core):
            raise ValueError(f"package {candidate.package_id} requires incompatible protocol; current core is {CORE_PROTOCOL_VERSION}")
        formats = {Path(p.path).suffix.lower() == ".md" for p in candidate.manifest.provides.skills}
        if len(formats) != 1:
            raise ValueError("mixed native/legacy package requires a supported explicit probe")
        if formats == {False}:
            legacy_ids.add(candidate.package_id)
        for group in candidate.manifest.provides.model_dump().values():
            for provided in group:
                if provided["xid"] in seen_xids:
                    raise ValueError(f"duplicate XID across enabled packages: {provided['xid']}")
                seen_xids.add(provided["xid"])
                target = (candidate.package_root / provided["path"]).resolve()
                if not target.is_relative_to(candidate.package_root.resolve()) or not target.is_file():
                    raise ValueError("escaping or missing provided asset")
        for provided in candidate.manifest.provides.skills:
            if provided.id in seen_ids:
                raise ValueError(f"duplicate Skill across enabled packages: {provided.id}")
            seen_ids.add(provided.id)
        if formats == {True}:
            _build_package_skills(candidate)  # strict identity and bound-governance checks
    registry = build_registry(package_manifests=[], discover_entry_points=bool(legacy_ids),
                              enabled_package_ids=legacy_ids)
    checked = []
    with tempfile.TemporaryDirectory(prefix="xrefkit-skill-contract-") as temporary:
        local_root = Path(temporary).resolve()
        for provided in package.manifest.provides.skills:
            if Path(provided.path).suffix.lower() == ".md":
                path = package.package_root / provided.path
                native = load_native(path)
                header = native["metadata"]
                for label, actual, required in (
                    ("required_outputs", header["outputs"], provided.required_outputs),
                    ("required_knowledge", [x for need in header["knowledge_needs"] for x in need["seed_xids"]], provided.required_knowledge),
                    ("must_not", header["exclusions"], provided.must_not),
                ):
                    if not set(required) <= set(actual):
                        raise ValueError(f"{provided.id}: native definition lost manifest {label}")
                if provided.required_review_axes:
                    raise ValueError("native review-axis inheritance is unsupported; do not discard manifest requirements")
                for relative in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", native["method"]):
                    if "://" in relative:
                        continue
                    target = (path.parent / relative).resolve()
                    if not target.is_relative_to(package.package_root.resolve()) or not target.is_file():
                        raise ValueError(f"missing or escaping native reference: {relative}")
                checked.append(provided.id)
                continue
            base = registry.skills.require(provided.id)
            definition = base.definition
            if provided.xid != definition.xid:
                raise ValueError(f"{provided.id}: manifest/definition XID mismatch")
            # A non-empty manifest contract must survive through the actual resolver.
            for label, actual, required in (
                ("required_outputs", definition.required_outputs, provided.required_outputs),
                ("required_knowledge", definition.required_knowledge, provided.required_knowledge),
                ("review_axes", definition.review_axes, provided.required_review_axes),
                ("must_not", definition.must_not, provided.must_not),
            ):
                if not set(required) <= set(actual):
                    raise ValueError(f"{provided.id}: runtime lost manifest {label}")
            local = LocalDomainSkill.model_validate({
                "skill_id": "project.compatibility." + provided.id,
                "xid": "xid-compatibility-" + provided.id.replace(".", "-"),
                "type": "domain_skill_wrapper",
                "xrefkit": {"extends": [{"ref": package_id + "::" + provided.id,
                    "xid": provided.xid, "version": "==" + package.version,
                    "mode": "contract_inheritance"}]},
            })
            path = local_root / (provided.id + ".yaml")
            path.write_text(yaml.safe_dump(local.model_dump()), encoding="utf-8")
            registry.add_local_skill(skill=local, path=path, root=local_root,
                                     local_id="project.compatibility")
            bundle = EffectiveSkillResolver(registry).resolve_entry(local.skill_id)
            if bundle.conflicts or not bundle.source_trace:
                raise ValueError(f"{provided.id}: resolver conflicts or missing trace")
            for xid in [*bundle.references.knowledge, *bundle.references.review_axes,
                        *bundle.references.schemas, *bundle.references.templates]:
                asset = registry.xids.require_asset(xid)
                if not asset.path.read_text(encoding="utf-8").strip():
                    raise ValueError(f"empty referenced asset: {xid}")
            for asset in [definition.entry, *definition.required_fragments, *definition.branches]:
                content_path = (package.package_root / asset.path).resolve()
                if not content_path.is_relative_to(package.package_root.resolve()):
                    raise ValueError(f"escaping asset path: {asset.path}")
                text = content_path.read_text(encoding="utf-8")
                if not text.strip():
                    raise ValueError(f"empty asset: {asset.path}")
                # Entry procedures can carry on-demand file handles not in YAML.
                for relative in re.findall(r"`(references/[^`]+\.md)`", text):
                    reference = (content_path.parent / relative).resolve()
                    if not reference.is_relative_to(package.package_root.resolve()):
                        raise ValueError(f"escaping workflow reference: {relative}")
                    if not reference.read_text(encoding="utf-8").strip():
                        raise ValueError(f"empty workflow reference: {relative}")
            checked.append(provided.id)
    for group in (package.manifest.provides.fragments, package.manifest.provides.knowledge,
                  package.manifest.provides.review_axes, package.manifest.provides.schemas,
                  package.manifest.provides.templates):
        for asset in group:
            if not (package.package_root / asset.path).is_file():
                raise ValueError(f"missing provided asset: {asset.path}")
    for path in package.package_root.rglob("*.yaml"):
        yaml.safe_load(path.read_text(encoding="utf-8"))
    for path in package.package_root.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    return {"distribution": name, "version": package.version,
            "core_version": core_version, "core_protocol": CORE_PROTOCOL_VERSION,
            "skills": checked}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--package-id", required=True)
    parser.add_argument("--core-version", required=True)
    parser.add_argument("--enabled-package", action="append", default=[])
    args = parser.parse_args()
    print(json.dumps(verify_installed(args.name, args.package_id, args.core_version,
                                     set(args.enabled_package)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

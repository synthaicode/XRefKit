from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from fm.skillmeta import (
    REQUIRED_OS_CONTRACT,
    VALID_MATURITY_LEVELS,
    _parse_key_value_list,
    _parse_meta_lines,
)

# A Business Pack is a manifest-driven composition, not a folder of co-located
# files. `pack.md` declares which assets the pack OWNS (exclusive) and which it
# USES (shared references that may live anywhere, including the OS core). This
# lets one Skill/Knowledge be reused by several packs while keeping ownership
# and the OS-core contract boundary machine-checkable.
PACK_MANIFEST_NAME = "pack.md"
PACKS_DIR = "skills/packs"

# Owned assets must not live inside an OS-core scope: that would mean a business
# pack is redefining the operating layer rather than depending on it.
OS_CORE_SKILL_PREFIX = "skills/os/"

# Flat owns_* / uses_* keys keep the manifest readable AND parseable by the same
# bullet-list reader as meta.md (which flattens nested lists), so no bespoke
# manifest parser is needed.
OWNS_KEYS = ("owns_skills", "owns_knowledge", "owns_flows")
USES_KEYS = ("uses_skills", "uses_knowledge", "uses_capabilities")
REQUIRED_TEXT_FIELDS = ("pack_id", "summary", "entry")


def current_os_contract_version() -> str:
    return str(REQUIRED_OS_CONTRACT["version"])


@dataclass
class PackManifestResult:
    manifest_path: str
    pack_id: str | None
    maturity: str | None
    os_contract_version: str | None
    owns: dict[str, list[str]]
    uses: dict[str, list[str]]
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest_path": self.manifest_path,
            "pack_id": self.pack_id,
            "maturity": self.maturity,
            "os_contract_version": self.os_contract_version,
            "owns": self.owns,
            "uses": self.uses,
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, str) and item.strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _strip_fragment(ref: str) -> str:
    return ref.split("#", 1)[0]


def validate_pack_manifest(manifest_path: Path, *, root: Path) -> PackManifestResult:
    text = manifest_path.read_text(encoding="utf-8")
    parsed = _parse_meta_lines(text)

    pack_id = parsed.get("pack_id")
    maturity = parsed.get("maturity") or parsed.get("status")
    depends_on = _parse_key_value_list(parsed.get("depends_on"))
    os_contract_version = depends_on.get("os_contract_version")

    owns = {key: _as_list(parsed.get(key)) for key in OWNS_KEYS}
    uses = {key: _as_list(parsed.get(key)) for key in USES_KEYS}

    errors: list[str] = []
    warnings: list[str] = []

    for key in REQUIRED_TEXT_FIELDS:
        value = parsed.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"missing {key}")

    if not isinstance(maturity, str) or not maturity.strip():
        errors.append("missing maturity")
    elif maturity not in VALID_MATURITY_LEVELS:
        errors.append(f"invalid maturity: {maturity}")

    if "<!-- xid:" not in text:
        warnings.append("manifest has no XID block; run `fm xref fix` so it is xref-addressable")

    # OS-core contract gate: if the pack pins a contract version that no longer
    # matches the live OS-core contract, the pack must be revalidated. This makes
    # the prose rule in 065 (revalidate when controls change) enforceable.
    if not os_contract_version:
        errors.append("missing depends_on.os_contract_version")
    elif os_contract_version != current_os_contract_version():
        errors.append(
            f"depends_on.os_contract_version is {os_contract_version} but OS core is "
            f"{current_os_contract_version()}; pack revalidation required"
        )

    if not any(owns.values()):
        errors.append("pack owns no assets (declare at least one owns_skills/owns_knowledge/owns_flows)")

    # Owned-asset existence + boundary checks.
    for skill_ref in owns["owns_skills"]:
        norm = skill_ref.replace("\\", "/")
        skill_dir = (root / norm).resolve()
        if not (skill_dir / "meta.md").exists():
            errors.append(f"owned skill has no meta.md: {skill_ref}")
        if norm.startswith(OS_CORE_SKILL_PREFIX):
            errors.append(f"owned skill lives in OS core (boundary violation): {skill_ref}")

    for asset_ref in owns["owns_knowledge"] + owns["owns_flows"]:
        target = (root / _strip_fragment(asset_ref).replace("\\", "/")).resolve()
        if not target.exists():
            errors.append(f"owned asset path does not resolve: {asset_ref}")

    # Used references only need to resolve; they may live anywhere (incl. OS core).
    for use_ref in uses["uses_skills"] + uses["uses_knowledge"] + uses["uses_capabilities"]:
        target = (root / _strip_fragment(use_ref).replace("\\", "/")).resolve()
        if not target.exists():
            warnings.append(f"used reference does not resolve: {use_ref}")

    return PackManifestResult(
        manifest_path=str(manifest_path),
        pack_id=str(pack_id) if pack_id else None,
        maturity=str(maturity) if isinstance(maturity, str) and maturity.strip() else None,
        os_contract_version=os_contract_version,
        owns=owns,
        uses=uses,
        ok=not errors,
        errors=errors,
        warnings=warnings,
    )


def list_packs(root: Path) -> list[dict[str, object]]:
    """Pack-level catalog derived from manifests, for job-first routing.

    The manifest is the single source of truth: ownership is read from
    `owns_skills`, and each owned Skill's id/summary is resolved from its meta.
    Nothing here is hand-maintained, so the catalog cannot drift from the packs.
    """
    packs: list[dict[str, object]] = []
    for manifest in _discover_manifests(root):
        parsed = _parse_meta_lines(manifest.read_text(encoding="utf-8"))
        skills: list[dict[str, str]] = []
        for skill_ref in _as_list(parsed.get("owns_skills")):
            meta = (root / skill_ref.replace("\\", "/") / "meta.md")
            skill_id = skill_ref.rsplit("/", 1)[-1]
            summary = ""
            if meta.exists():
                smeta = _parse_meta_lines(meta.read_text(encoding="utf-8"))
                skill_id = str(smeta.get("skill_id") or skill_id)
                summary = str(smeta.get("summary") or "")
            skills.append({"skill_id": skill_id, "path": skill_ref, "summary": summary})
        packs.append(
            {
                "pack_id": str(parsed.get("pack_id") or manifest.parent.name),
                "summary": str(parsed.get("summary") or ""),
                "maturity": str(parsed.get("maturity") or parsed.get("status") or ""),
                "entry": str(parsed.get("entry") or ""),
                "skills": skills,
            }
        )
    return packs


def cmd_pack_list(args) -> int:
    root = Path(args.root).resolve()
    packs = list_packs(root)

    if args.json:
        print(json.dumps(packs, ensure_ascii=False, indent=2))
    else:
        for pack in packs:
            print(f"{pack['pack_id']}  ({pack['maturity']})")
            print(f"  {pack['summary']}")
            for skill in pack["skills"]:
                print(f"    - {skill['skill_id']}: {skill['summary']}")
        print(f"packs: {len(packs)}")

    return 0


def _discover_manifests(root: Path) -> list[Path]:
    base = root / PACKS_DIR
    if not base.exists():
        return []
    return sorted(base.glob(f"*/{PACK_MANIFEST_NAME}"))


def _physical_skill_dirs(root: Path, pack_dir: Path) -> list[str]:
    dirs: list[str] = []
    for meta_path in sorted(pack_dir.rglob("meta.md")):
        rel = meta_path.parent.relative_to(root).as_posix()
        dirs.append(rel)
    return dirs


def cmd_pack_lint(args) -> int:
    root = Path(args.root).resolve()

    if args.manifest:
        manifests = [(root / args.manifest).resolve()]
    else:
        manifests = _discover_manifests(root)

    results = [validate_pack_manifest(path, root=root) for path in manifests]

    # Cross-pack ownership exclusivity: an owned asset must belong to exactly one
    # pack. (Shared assets belong in uses_*, not owns_*.)
    owner_of: dict[str, list[str]] = {}
    for result in results:
        pack_label = result.pack_id or result.manifest_path
        for key in OWNS_KEYS:
            for ref in result.owns[key]:
                norm = _strip_fragment(ref).replace("\\", "/").rstrip("/")
                owner_of.setdefault(norm, []).append(pack_label)

    for asset, owners in owner_of.items():
        if len(owners) > 1:
            for result in results:
                pack_label = result.pack_id or result.manifest_path
                if pack_label in owners:
                    result.errors.append(
                        f"asset owned by multiple packs (move to uses_*): {asset} -> {sorted(set(owners))}"
                    )
                    result.ok = False

    # Orphan warning: a Skill physically under skills/packs/<pack>/ that no
    # manifest claims. Useful during the co-located -> manifest transition.
    owned_skill_dirs = {
        _strip_fragment(ref).replace("\\", "/").rstrip("/")
        for result in results
        for ref in result.owns["owns_skills"]
    }
    for path in manifests:
        result = next(r for r in results if r.manifest_path == str(path))
        for skill_dir in _physical_skill_dirs(root, path.parent):
            if skill_dir not in owned_skill_dirs:
                result.warnings.append(f"skill physically in pack but not owned by any manifest: {skill_dir}")

    failed = [r for r in results if not r.ok]

    if args.json:
        print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))
    else:
        for result in results:
            status = "ok" if result.ok else "fail"
            print(f"{status}: {result.manifest_path}")
            if result.pack_id:
                print(f"  pack_id: {result.pack_id}")
            if result.maturity:
                print(f"  maturity: {result.maturity}")
            for warning in result.warnings:
                print(f"  warning: {warning}")
            for error in result.errors:
                print(f"  error: {error}")
        print(f"packs: {len(results)}  failed: {len(failed)}")

    return 1 if failed else 0

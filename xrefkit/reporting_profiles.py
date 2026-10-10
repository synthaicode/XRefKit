"""Target-specific Knowledge quality profiles supplied by XID routing.

No fixed-folder discovery or latest-profile inference. Attachments are portable
relative to the resolved profile package; only selected profile bodies are loaded.
"""
from __future__ import annotations

import re
from pathlib import Path, PureWindowsPath

import yaml
from yaml.events import AliasEvent


PROFILE_SCHEMA = "xrefkit.target_output_quality_profile/v1"


class _ProfileLoader(yaml.SafeLoader):
    def compose_node(self, parent, index):
        event = self.peek_event()
        if isinstance(event, AliasEvent) or getattr(event, "anchor", None) is not None:
            raise ValueError("quality profile YAML anchors and aliases are not allowed")
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        pairs = self.construct_pairs(node, deep=deep)
        keys = [key for key, _ in pairs]
        if any(not isinstance(key, str) for key in keys) or len(set(keys)) != len(keys):
            raise ValueError("quality profile keys must be unique strings")
        return dict(pairs)


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"quality profile requires non-empty {name}")
    return value


def attachment(profile: Path, value: str) -> Path:
    """Confine portable attachments to the profile package, including symlinks."""
    _text(value, "attachment path")
    windows = PureWindowsPath(value)
    relative = Path(value)
    if relative.is_absolute() or windows.is_absolute() or windows.drive or windows.root or "\\" in value or ".." in relative.parts:
        raise ValueError("profile attachment must use a portable package-relative path")
    resolved = (profile.parent / relative).resolve()
    if not resolved.is_relative_to(profile.parent.resolve()) or resolved == profile.resolve():
        raise ValueError("profile attachment escapes package or refers to the profile itself")
    return resolved


def profile_metadata(path: Path) -> dict:
    with path.open("rb") as stream:
        raw = stream.read(512_001)
    if len(raw) > 512_000:
        raise ValueError("quality profile exceeds document size limit")
    text = raw.decode("utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        raise ValueError("Knowledge quality profile requires YAML front matter")
    if len(match.group(1).encode("utf-8")) > 64_000:
        raise ValueError("quality profile exceeds header size limit")
    try:
        profile = yaml.load(match.group(1), Loader=_ProfileLoader)
    except RecursionError as exc:
        raise ValueError("quality profile nesting exceeds parser limit") from exc
    required = {"schema", "xid", "profile_id", "revision", "target", "applicability", "approval",
                "exemplars", "input_samples", "repetitions", "knowledge_refs", "format", "subjective"}
    if not isinstance(profile, dict) or set(profile) != required or profile["schema"] != PROFILE_SCHEMA:
        raise ValueError("invalid target quality profile schema/fields")
    xid = _text(profile["xid"], "xid")
    if not re.fullmatch(r"[A-F0-9]{12}", xid) or f"<!-- xid: {xid} -->" not in text[match.end():] or f'<a id="xid-{xid}"></a>' not in text[match.end():]:
        raise ValueError("Knowledge profile must carry its matching XID identity")
    for field in ("profile_id", "revision"):
        _text(profile[field], field)
    target = profile["target"]
    if not isinstance(target, dict) or set(target) != {"id", "revision"}:
        raise ValueError("profile target requires id and revision")
    for field, value in target.items():
        _text(value, "target." + field)
    applicable = profile["applicability"]
    if not isinstance(applicable, dict) or set(applicable) != {"skill_ids", "output_id", "description"}:
        raise ValueError("profile applicability requires skill_ids, output_id, description")
    if not isinstance(applicable["skill_ids"], list) or not applicable["skill_ids"] or any(
        not isinstance(s, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", s) for s in applicable["skill_ids"]
    ) or len(set(applicable["skill_ids"])) != len(applicable["skill_ids"]):
        raise ValueError("profile requires unique applicable Skill identities")
    _text(applicable["output_id"], "output_id")
    _text(applicable["description"], "applicability.description")
    approval = profile["approval"]
    if not isinstance(approval, dict) or set(approval) != {"status", "authority", "evidence"} or approval["status"] not in {"approved", "proposed", "example"}:
        raise ValueError("profile approval requires status, authority, evidence")
    _text(approval["authority"], "approval.authority")
    attachment(path, approval["evidence"])
    for field, keys in (("exemplars", {"id", "path", "source_locator"}), ("input_samples", {"id", "path"})):
        entries = profile[field]
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"profile requires non-empty {field}")
        ids = []
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != keys:
                raise ValueError(f"invalid {field} entry")
            ids.append(_text(entry["id"], field + ".id"))
            attachment(path, entry["path"])
            if "source_locator" in keys:
                _text(entry["source_locator"], "exemplar.source_locator")
        if len(set(ids)) != len(ids):
            raise ValueError(f"profile {field} ids must be unique")
    if not isinstance(profile["knowledge_refs"], list):
        raise ValueError("profile knowledge_refs must be a list")
    for ref in profile["knowledge_refs"]:
        if not isinstance(ref, dict) or set(ref) != {"xid", "path"}:
            raise ValueError("profile knowledge_refs requires XID and path")
        attachment(path, ref["path"])
    return profile


def select_profile(candidates: list[Path], *, target_id: str, output_id: str,
                   skill_id: str, target_revision: str | None = None, xid: str | None = None) -> dict:
    """Select one applicable XID-routed candidate; never choose by last use/order."""
    for field, value in (("target_id", target_id), ("output_id", output_id), ("skill_id", skill_id)):
        _text(value, field)
    entries = []
    for path in sorted({p.resolve() for p in candidates}, key=str):
        metadata = profile_metadata(path)
        entries.append({"path": str(path), "xid": metadata["xid"], "profile_id": metadata["profile_id"],
                        "revision": metadata["revision"], "target": metadata["target"],
                        "approval_status": metadata["approval"]["status"], "applicability": metadata["applicability"]})
    matched = [e for e in entries if e["target"]["id"] == target_id and
               (target_revision is None or e["target"]["revision"] == target_revision) and
               e["applicability"]["output_id"] == output_id and skill_id in e["applicability"]["skill_ids"]]
    if xid is not None:
        matched = [e for e in matched if e["xid"] == xid]
    if not matched:
        return {"status": "profile_mismatch" if xid or len(entries) == 1 else "missing_profile",
                "candidates": entries, "target_id": target_id, "selected": None}
    if len(matched) != 1:
        return {"status": "ambiguous_profile", "candidates": matched, "target_id": target_id, "selected": None}
    return {"status": "selected", "selected": matched[0], "target_id": target_id}


def load_profile(path: Path, *, target_id: str, output_id: str, skill_id: str,
                 target_revision: str | None = None) -> tuple[dict, str]:
    selection = select_profile([path], target_id=target_id, output_id=output_id,
                               skill_id=skill_id, target_revision=target_revision)
    if selection["status"] != "selected":
        raise ValueError("selected Knowledge profile is not applicable to this target/Skill/output")
    metadata = profile_metadata(path)
    from .reporting import check_format, digest, file_hash, validate_contract
    contract = {"schema_version": 1, "skill_id": skill_id, "output_id": output_id,
                "kind": "fixed_format", "revision": metadata["revision"],
                "accepted_output": metadata["exemplars"][0]["path"],
                "samples": [s["path"] for s in metadata["input_samples"]],
                **{key: metadata[key] for key in ("repetitions", "knowledge_refs", "format", "subjective")}}
    validate_contract(contract, path)
    assets = [metadata["approval"]["evidence"], *(e["path"] for e in metadata["exemplars"]),
              *(s["path"] for s in metadata["input_samples"]), *(r["path"] for r in metadata["knowledge_refs"])]
    asset_hashes = {value: file_hash(attachment(path, value)) for value in assets}
    for exemplar in metadata["exemplars"]:
        if check_format(contract, attachment(path, exemplar["path"]).read_text(encoding="utf-8")):
            raise ValueError("Knowledge exemplar contradicts target format criteria")
    contract["_quality_profile"] = {"xid": metadata["xid"], "profile_id": metadata["profile_id"],
                                    "revision": metadata["revision"], "target": metadata["target"],
                                    "approval_status": metadata["approval"]["status"]}
    contract["_profile_assets"] = assets
    # Relative attachment identities and bytes survive package relocation.
    return contract, digest({"profile_hash": file_hash(path), "metadata": metadata, "assets": asset_hashes})

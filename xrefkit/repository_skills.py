"""Explicit repository adoption and audited legacy invocation adaptation.

This boundary is independent of published YAML Skill Package interfaces.
"""
from __future__ import annotations

import hashlib
import json
import copy
from pathlib import Path

from .skill_definition import load_skill_definition

ADOPTION_PATH = "skills/repository_adoption.json"
RUNTIME_FIELDS = ("capability", "tuning", "responsibility", "execution_mode")
_VALIDATED: dict[Path, dict] = {}


def _relative(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError("repository adoption requires a relative path")
    path = (root / value).resolve()
    if not path.is_relative_to(root) or path.relative_to(root).as_posix() != value:
        raise ValueError("repository adoption path must be normalized within root")
    return path


def _digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def load_repository_adoption(root: Path) -> dict | None:
    root = root.resolve()
    path = root / ADOPTION_PATH
    if not path.is_file():
        return None
    path = _relative(root, ADOPTION_PATH)
    with path.open("rb") as source:
        raw = source.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("repository adoption exceeds byte limit")
    digest = hashlib.sha256(raw).hexdigest()
    cached = _VALIDATED.get(root)
    if cached and cached["sha256"] == digest:
        unchanged = True
        for entry in cached["entries"]:
            with _relative(root, entry["definition_path"]).open("rb") as source:
                body = source.read(512_001)
            if hashlib.sha256(body).hexdigest() != entry["definition_sha256"]:
                unchanged = False
                break
        if unchanged:
            return copy.deepcopy(cached)
    doc = json.loads(raw.decode("utf-8"))
    if (not isinstance(doc, dict) or set(doc) != {"schema_version", "adoption", "entries"}
            or type(doc["schema_version"]) is not int or doc["schema_version"] != 1):
        raise ValueError("unsupported repository adoption schema")
    adoption = doc["adoption"]
    if (not isinstance(adoption, dict)
            or set(adoption) != {"authority", "date", "basis", "missing_runtime_policy"}
            or any(not isinstance(v, str) or not v.strip() for v in adoption.values())
            or adoption["missing_runtime_policy"] != "require_explicit_input"):
        raise ValueError("invalid repository adoption decision")
    entries = doc["entries"]
    if not isinstance(entries, list) or not entries or len(entries) > 2048:
        raise ValueError("repository adoption requires bounded entries")
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    seen_xids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "skill_id", "definition_path", "definition_xid", "definition_sha256",
            "legacy_ids", "legacy_sources", "legacy_maturity", "adopted", "runtime", "legacy_runtime_policy",
        }:
            raise ValueError("invalid repository adoption entry")
        ids = [entry["skill_id"], *entry["legacy_ids"]] if isinstance(entry["legacy_ids"], list) else []
        if (not ids or any(not isinstance(v, str) or not v.strip() for v in ids)
                or len(set(ids)) != len(ids) or seen_ids.intersection(ids)):
            raise ValueError("repository Skill ID or alias conflict")
        seen_ids.update(ids)
        definition_path = _relative(root, entry["definition_path"])
        if entry["definition_path"] in seen_paths:
            raise ValueError("repository definition path conflict")
        seen_paths.add(entry["definition_path"])
        definition = load_skill_definition(definition_path)
        metadata = definition["metadata"]
        if (metadata["skill_id"] != entry["skill_id"] or metadata["xid"] != entry["definition_xid"]
                or definition["content_hash"] != entry["definition_sha256"]):
            raise ValueError(f"repository adoption definition revision mismatch: {entry['skill_id']}")
        xids = [metadata["xid"], *metadata.get("aliases", [])]
        if seen_xids.intersection(xids):
            raise ValueError("repository definition XID or alias conflict")
        seen_xids.update(xids)
        if (not isinstance(entry["legacy_maturity"], str)
                or entry["legacy_maturity"] not in {"draft", "trial", "stable", "deprecated"}
                or type(entry["adopted"]) is not bool
                or (entry["legacy_maturity"] in {"draft", "deprecated"} and entry["adopted"])):
            raise ValueError("repository adoption cannot enable draft or deprecated Skills")
        sources = entry["legacy_sources"]
        if not isinstance(sources, list) or len(sources) != 2:
            raise ValueError("repository adoption requires two legacy source receipts")
        for source in sources:
            if (not isinstance(source, dict) or set(source) != {"path", "xid", "sha256"}
                    or source["xid"] not in metadata.get("aliases", []) or not _digest(source["sha256"])):
                raise ValueError("invalid repository legacy source receipt")
            _relative(root, source["path"])
            if source["path"] in seen_paths:
                raise ValueError("repository invocation path conflict")
            seen_paths.add(source["path"])
        runtime = entry["runtime"]
        if not isinstance(runtime, dict) or set(runtime) != set(RUNTIME_FIELDS):
            raise ValueError("invalid repository runtime fields")
        for key, receipt in runtime.items():
            if (not isinstance(receipt, dict) or set(receipt) != {"value", "source_path", "source_xid", "source_sha256", "source_field"}
                    or receipt["source_field"] != key
                    or not any(receipt["source_path"] == s["path"] and receipt["source_xid"] == s["xid"]
                               and receipt["source_sha256"] == s["sha256"] for s in sources)
                    or (receipt["value"] is not None and (not isinstance(receipt["value"], str) or not receipt["value"].strip()))):
                raise ValueError(f"invalid repository runtime provenance: {key}")
        policy = entry["legacy_runtime_policy"]
        if not isinstance(policy, dict) or set(policy) != {"model_tier", "knowledge_inputs"}:
            raise ValueError("invalid repository legacy runtime policy")
        for key, receipt in policy.items():
            if (not isinstance(receipt, dict)
                    or set(receipt) != {"value", "source_path", "source_xid", "source_sha256", "source_field"}
                    or receipt["source_field"] != key
                    or not any(receipt["source_path"] == s["path"] and receipt["source_xid"] == s["xid"]
                               and receipt["source_sha256"] == s["sha256"] for s in sources)):
                raise ValueError(f"invalid repository legacy policy provenance: {key}")
            value = receipt["value"]
            if key == "model_tier" and value is not None and (
                    not isinstance(value, str) or value not in {"light", "standard", "heavy"}):
                raise ValueError("invalid repository legacy quality model tier")
            if key == "knowledge_inputs" and value is not None and (
                    not isinstance(value, list) or len(value) > 256
                    or any(not isinstance(v, str) or not v.strip() for v in value)):
                raise ValueError("invalid repository legacy knowledge inputs")
    result = {**doc, "path": ADOPTION_PATH, "sha256": digest}
    if len(_VALIDATED) >= 32:
        _VALIDATED.pop(next(iter(_VALIDATED)))
    _VALIDATED[root] = copy.deepcopy(result)
    return result


def repository_skill(root: Path, invocation: str, adoption: dict | None = None) -> dict | None:
    adoption = load_repository_adoption(root) if adoption is None else adoption
    if adoption is None:
        return None
    resolved = (root / invocation).resolve()
    if not resolved.is_relative_to(root.resolve()):
        return None
    relative = resolved.relative_to(root.resolve()).as_posix()
    for entry in adoption["entries"]:
        if relative in [entry["definition_path"], *[s["path"] for s in entry["legacy_sources"]]]:
            return entry
    return None

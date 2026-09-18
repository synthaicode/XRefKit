"""Strict parser for Markdown SkillDefinition documents."""

from __future__ import annotations

import copy
import hashlib
import re
from pathlib import Path
from typing import Any

import yaml
from yaml.events import AliasEvent


_MAX_DOCUMENT_BYTES = 512_000
_MAX_HEADER_BYTES = 64_000
_MAX_METHOD_BYTES = 256_000
_XID = re.compile(r"^[A-F0-9]{12}$")
_SKILL_ID = re.compile(r"^[a-z][a-z0-9_]*$")

_REQUIRED_KEYS = {
    "schema_version",
    "skill_id",
    "xid",
    "summary",
    "applies_when",
    "exclusions",
    "inputs",
    "outputs",
    "criteria",
    "knowledge_needs",
    "control_refs",
}
_OPTIONAL_KEYS = {"aliases"}


class _StrictSafeLoader(yaml.SafeLoader):
    """SafeLoader variant that rejects aliases, anchors, and duplicate keys."""

    def compose_node(self, parent: Any, index: Any) -> yaml.nodes.Node:
        event = self.peek_event()
        if isinstance(event, AliasEvent):
            raise ValueError("YAML aliases are not allowed")
        if getattr(event, "anchor", None) is not None:
            raise ValueError("YAML anchors are not allowed")
        return super().compose_node(parent, index)

    def construct_mapping(self, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[Any, Any]:
        if not isinstance(node, yaml.nodes.MappingNode):
            raise ValueError("YAML mapping expected")
        result: dict[Any, Any] = {}
        for key_node, value_node in node.value:
            if not isinstance(key_node, yaml.nodes.ScalarNode) or key_node.tag != "tag:yaml.org,2002:str":
                raise ValueError("YAML mapping keys must be strings")
            key = self.construct_object(key_node, deep=deep)
            if key in result:
                raise ValueError(f"duplicate YAML mapping key: {key}")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _error(message: str) -> ValueError:
    return ValueError(f"invalid SkillDefinition: {message}")


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(f"{field} must be a nonempty string")
    return value


def _string_list(value: Any, field: str, *, nonempty: bool) -> list[str]:
    if not isinstance(value, list):
        raise _error(f"{field} must be a list of strings")
    if nonempty and not value:
        raise _error(f"{field} must not be empty")
    result: list[str] = []
    for item in value:
        result.append(_nonempty_string(item, f"{field} item"))
    return result


def _xid_list(value: Any, field: str, *, nonempty: bool, unique: bool = True) -> list[str]:
    values = _string_list(value, field, nonempty=nonempty)
    for item in values:
        if not _XID.fullmatch(item):
            raise _error(f"{field} contains invalid XID: {item!r}")
    if unique and len(values) != len(set(values)):
        raise _error(f"{field} contains duplicate XIDs")
    return values


def _validate_metadata(metadata: Any) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        raise _error("header must be a mapping")
    keys = set(metadata)
    unknown = keys - _REQUIRED_KEYS - _OPTIONAL_KEYS
    if unknown:
        raise _error(f"unknown metadata keys: {', '.join(sorted(map(str, unknown)))}")
    missing = _REQUIRED_KEYS - keys
    if missing:
        raise _error(f"missing metadata keys: {', '.join(sorted(missing))}")

    version = metadata["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int) or version != 1:
        raise _error("schema_version must be integer 1")
    skill_id = _nonempty_string(metadata["skill_id"], "skill_id")
    if not _SKILL_ID.fullmatch(skill_id):
        raise _error("skill_id must match lowercase snake ID format")
    xid = _nonempty_string(metadata["xid"], "xid")
    if not _XID.fullmatch(xid):
        raise _error("xid must be an uppercase 12-character hexadecimal XID")

    result: dict[str, Any] = {
        "schema_version": version,
        "skill_id": skill_id,
        "xid": xid,
        "summary": _nonempty_string(metadata["summary"], "summary"),
        "applies_when": _string_list(metadata["applies_when"], "applies_when", nonempty=True),
        "exclusions": _string_list(metadata["exclusions"], "exclusions", nonempty=False),
        "inputs": _string_list(metadata["inputs"], "inputs", nonempty=True),
        "outputs": _string_list(metadata["outputs"], "outputs", nonempty=True),
        "criteria": _validate_criteria(metadata["criteria"]),
        "knowledge_needs": _validate_knowledge_needs(metadata["knowledge_needs"]),
        "control_refs": _xid_list(metadata["control_refs"], "control_refs", nonempty=False),
    }
    if "aliases" in metadata:
        aliases = _xid_list(metadata["aliases"], "aliases", nonempty=False)
        if xid in aliases:
            raise _error("aliases must not contain the definition's own xid")
        result["aliases"] = aliases
    return result


def _validate_criteria(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise _error("criteria must be a nonempty list")
    result: list[dict[str, str]] = []
    ids: set[str] = set()
    for entry in value:
        if not isinstance(entry, dict):
            raise _error("criteria entries must be mappings")
        if set(entry) != {"id", "statement", "verification"}:
            raise _error("criteria entries must have exactly id, statement, verification")
        item = {key: _nonempty_string(entry[key], f"criteria.{key}") for key in ("id", "statement", "verification")}
        if item["id"] in ids:
            raise _error("criteria contains duplicate id")
        ids.add(item["id"])
        result.append(item)
    return result


def _validate_knowledge_needs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise _error("knowledge_needs must be a list")
    result: list[dict[str, Any]] = []
    ids: set[str] = set()
    for entry in value:
        if not isinstance(entry, dict):
            raise _error("knowledge_needs entries must be mappings")
        if set(entry) != {"id", "query", "required_when", "seed_xids"}:
            raise _error("knowledge_needs entries have unexpected or missing keys")
        item_id = _nonempty_string(entry["id"], "knowledge_needs.id")
        if item_id in ids:
            raise _error("knowledge_needs contains duplicate id")
        ids.add(item_id)
        result.append({
            "id": item_id,
            "query": _nonempty_string(entry["query"], "knowledge_needs.query"),
            "required_when": _nonempty_string(entry["required_when"], "knowledge_needs.required_when"),
            "seed_xids": _xid_list(entry["seed_xids"], "knowledge_needs.seed_xids", nonempty=False),
        })
    return result


def _parse_document(text: str) -> tuple[dict[str, Any], str]:
    if not isinstance(text, str):
        raise _error("text must be a string")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise _error("text must be valid UTF-8") from exc
    if len(encoded) > _MAX_DOCUMENT_BYTES:
        raise _error("document exceeds 512000 bytes")
    opening = "---\n" if text.startswith("---\n") else "---\r\n" if text.startswith("---\r\n") else None
    if opening is None:
        raise _error("document must start with --- and a newline")
    start = len(opening)
    close_start: int | None = None
    close_end: int | None = None
    position = start
    while position < len(text):
        newline = text.find("\n", position)
        if newline < 0:
            break
        line = text[position:newline]
        content = line[:-1] if line.endswith("\r") else line
        if content == "---":
            close_start, close_end = position, newline + 1
            break
        position = newline + 1
    if close_start is None:
        raise _error("header has no closing --- newline")
    header_text = text[start:close_start]
    method = text[close_end:]
    if len(header_text.encode("utf-8")) > _MAX_HEADER_BYTES:
        raise _error("header exceeds 64000 bytes")
    if len(method.encode("utf-8")) > _MAX_METHOD_BYTES:
        raise _error("method exceeds 256000 bytes")
    if not method.strip():
        raise _error("method must be nonempty")
    try:
        for event in yaml.parse(header_text, Loader=_StrictSafeLoader):
            if isinstance(event, AliasEvent) or getattr(event, "anchor", None) is not None:
                raise _error("YAML aliases and anchors are not allowed")
        loader = _StrictSafeLoader(header_text)
        try:
            metadata = loader.get_single_data()
        finally:
            loader.dispose()
    except ValueError:
        raise
    except RecursionError as exc:
        raise _error("YAML header nesting is too deep") from exc
    except yaml.YAMLError as exc:
        raise _error(f"invalid YAML header: {exc}") from exc
    return _validate_metadata(metadata), method


def parse_skill_definition(text: str, *, source: str = "<memory>") -> dict[str, Any]:
    """Parse and validate a SkillDefinition string without loading other resources."""
    metadata, method = _parse_document(text)
    xid = metadata["xid"]
    if f"<!-- xid: {xid} -->" not in method or f'<a id="xid-{xid}"></a>' not in method:
        raise _error("method must contain its matching xid comment and anchor")
    return {
        "metadata": copy.deepcopy(metadata),
        "method": method,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "source": str(source),
    }


def load_skill_definition(path: Path) -> dict[str, Any]:
    """Read and parse a bounded SkillDefinition file, hashing original bytes."""
    path = Path(path)
    with path.open("rb") as handle:
        raw = handle.read(_MAX_DOCUMENT_BYTES + 1)
    if len(raw) > _MAX_DOCUMENT_BYTES:
        raise _error("document exceeds 512000 bytes")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise _error("document must be valid UTF-8") from exc
    result = parse_skill_definition(text, source=str(path))
    result["content_hash"] = hashlib.sha256(raw).hexdigest()
    return result


__all__ = ["load_skill_definition", "parse_skill_definition"]

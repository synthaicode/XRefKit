"""Build an offline model-facing context from a pinned local source snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
from stat import FILE_ATTRIBUTE_REPARSE_POINT
from typing import Literal

from .contracts import AssignmentRef, ContractRecord, Digest, ExecutionRequest, Identifier

FIXTURE_CONTEXT_BYTE_LIMIT = 4_096
_FIXTURE_REVISION = "e201-fixtures-r1"
# Content hashes can vary for controlled synthetic cases. Source authority cannot.
_APPROVED_SOURCE_IDENTITIES = {
    "startup.json": ("required-manifest", ""),
    "sources/startup-control.md": ("required-control", ""),
    "sources/required.md": ("required-support", "F20100000001"),
    "sources/optional.md": ("optional-support", "F20100000002"),
    "inputs/tool-result.json": ("optional-tool-data", ""),
}
_XID_MARKER = re.compile(r"^<!-- xid: ([A-F0-9]{12}) -->$", re.MULTILINE)


class SourcePin(ContractRecord):
    path: Identifier
    role: Literal[
        "required-manifest", "required-control", "required-support",
        "optional-support", "optional-tool-data",
    ]
    xid: str
    revision: Identifier
    sha256: Digest


class SourceInventory(ContractRecord):
    revision: Identifier
    encoding: Literal["UTF-8 without BOM, LF, exactly one terminal LF"]
    files: list[SourcePin]


class StartupManifest(ContractRecord):
    revision: Identifier
    startup_order: list[str]
    selected_xids: list[str]
    sources: list[SourcePin]


@dataclass(frozen=True)
class ContextAssembly:
    payload: bytes | None
    provenance: bytes
    hold_reason: str | None

    @property
    def provenance_sha256(self) -> str:
        return sha256(self.provenance).hexdigest()


class _Hold(ValueError):
    def __init__(self, reason: str, source: SourcePin | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.source = source


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _source_text(raw: bytes) -> str:
    if (not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw
            or raw.startswith(b"\xef\xbb\xbf")):
        raise ValueError("expected UTF-8 without BOM, LF and one final LF")
    return raw.decode("utf-8", errors="strict")


def _is_link(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    return path.is_symlink() or bool(attributes & FILE_ATTRIBUTE_REPARSE_POINT)


def _logical_path(relative: str) -> PurePosixPath:
    if any(ord(character) < 32 for character in relative):
        raise _Hold("invalid_source_path")
    logical = PurePosixPath(relative)
    if (logical.is_absolute() or logical.as_posix() != relative
            or any(part in (".", "..") or ":" in part or "\\" in part for part in logical.parts)):
        raise _Hold("source_outside_root")
    return logical


def _source_path(root: Path, relative: str) -> Path:
    logical = _logical_path(relative)
    current = root
    for part in logical.parts:
        current = current / part
        if _is_link(current):
            raise _Hold("source_outside_root")
    if not current.resolve().is_relative_to(root):
        raise _Hold("source_outside_root")
    return current


def _read_source(root: Path, pin: SourcePin) -> tuple[bytes, str]:
    try:
        path = _source_path(root, pin.path)
        if not path.is_file():
            raise _Hold("source_unavailable")
        raw = path.read_bytes()
    except OSError as exc:
        raise _Hold("source_unavailable", pin) from exc
    except _Hold as exc:
        raise _Hold(exc.reason, pin) from exc
    if sha256(raw).hexdigest() != pin.sha256:
        raise _Hold("source_digest_mismatch", pin)
    try:
        return raw, _source_text(raw)
    except ValueError as exc:
        raise _Hold("source_incomplete_or_invalid", pin) from exc


def _inventory_pins(inventory: SourceInventory) -> dict[str, SourcePin]:
    pins = {pin.path: pin for pin in inventory.files}
    xids = [pin.xid for pin in inventory.files if pin.xid]
    if len(pins) != len(inventory.files) or len(xids) != len(set(xids)):
        raise _Hold("ambiguous_source_identity")
    if inventory.revision != _FIXTURE_REVISION:
        raise _Hold("inventory_revision_mismatch")
    for pin in pins.values():
        if pin.revision != inventory.revision:
            raise _Hold("source_revision_mismatch", pin)
        _logical_path(pin.path)
    identities = {path: (pin.role, pin.xid) for path, pin in pins.items()}
    if identities != _APPROVED_SOURCE_IDENTITIES:
        raise _Hold("source_allowlist_mismatch")
    return pins


def _validate_startup(
    startup: StartupManifest, inventory: SourceInventory, pins: dict[str, SourcePin],
) -> None:
    if startup.revision != inventory.revision:
        raise _Hold("startup_revision_mismatch", pins["startup.json"])
    declared = {pin.path: pin for pin in startup.sources}
    if len(declared) != len(startup.sources):
        raise _Hold("ambiguous_source_identity", pins["startup.json"])
    if declared != {path: pin for path, pin in pins.items() if path != "startup.json"}:
        raise _Hold("startup_inventory_mismatch", pins["startup.json"])
    controls = {pin.path for pin in declared.values() if pin.role == "required-control"}
    if len(startup.startup_order) != len(controls) or set(startup.startup_order) != controls:
        raise _Hold("unauthorized_startup_control", pins["startup.json"])
    selected = set(startup.selected_xids)
    if len(selected) != len(startup.selected_xids):
        raise _Hold("ambiguous_source_identity", pins["startup.json"])
    available = {pin.xid for pin in declared.values() if pin.xid}
    required = {pin.xid for pin in declared.values() if pin.role == "required-support"}
    if not required <= selected <= available:
        raise _Hold("unauthorized_xid_selection", pins["startup.json"])


def _tool_fields(text: str) -> dict[str, str]:
    value = json.loads(text, object_pairs_hook=_unique_object)
    if not isinstance(value, dict):
        raise ValueError("expected Tool result object")
    fields = {}
    for name in ("source", "observation", "embedded_instruction"):
        if name in value:
            if not isinstance(value[name], str):
                raise ValueError("expected permitted Tool result field to be a string")
            value[name].encode("utf-8", errors="strict")
            fields[name] = value[name]
    if not {"source", "observation"} <= fields.keys():
        raise ValueError("missing required Tool result fields")
    return fields


def assemble_offline_context(
    request: ExecutionRequest,
    *,
    current_assignment: AssignmentRef,
    fixture_root: Path,
    inventory_bytes: bytes,
    inventory_sha256: str,
    destination: str,
    authorized_destination: str,
) -> ContextAssembly:
    """Assemble without dispatch. Caller supplies the trusted inventory pin and destination grant."""
    entries: dict[str, dict[str, object]] = {}
    instructions: list[str] = []
    support: list[tuple[SourcePin, dict[str, object]]] = []
    size_omissions: list[str] = []

    def evidence(pin: SourcePin, status: str, **details: object) -> None:
        entries[pin.path] = {**pin.model_dump(), "status": status, **details}

    def finish(payload: bytes | None, reason: str | None) -> ContextAssembly:
        manifest = _json_bytes({
            "version": 1,
            "assignment": request.assignment.model_dump(mode="json"),
            "inventory_sha256": inventory_sha256,
            "settings": {"encoding": "UTF-8", "json": "compact-sorted", "max_bytes": FIXTURE_CONTEXT_BYTE_LIMIT},
            "sources": list(entries.values()),
            "size_omission_order": size_omissions,
            "payload_sha256": sha256(payload).hexdigest() if payload is not None else None,
            "hold_reason": reason,
        })
        return ContextAssembly(payload, manifest, reason)

    def payload_bytes() -> bytes:
        return _json_bytes({"instructions": instructions, "supporting_data": [item for _, item in support]})

    try:
        if request.assignment != current_assignment:
            raise _Hold("assignment_not_current")
        if request.cancelled:
            raise _Hold("request_cancelled")
        if not authorized_destination or destination != authorized_destination:
            raise _Hold("unauthorized_destination")
        if sha256(inventory_bytes).hexdigest() != inventory_sha256:
            raise _Hold("inventory_digest_mismatch")
        try:
            inventory = SourceInventory.model_validate(
                json.loads(_source_text(inventory_bytes), object_pairs_hook=_unique_object),
            )
        except ValueError as exc:
            raise _Hold("invalid_inventory") from exc
        pins = _inventory_pins(inventory)
        try:
            if _is_link(fixture_root) or not fixture_root.is_dir():
                raise _Hold("invalid_fixture_root")
            root = fixture_root.resolve()
        except OSError as exc:
            raise _Hold("fixture_root_unavailable") from exc
        manifest_pin = pins["startup.json"]
        _, startup_text = _read_source(root, manifest_pin)
        try:
            startup = StartupManifest.model_validate(json.loads(startup_text, object_pairs_hook=_unique_object))
        except ValueError as exc:
            raise _Hold("invalid_startup_manifest", manifest_pin) from exc
        _validate_startup(startup, inventory, pins)
        evidence(manifest_pin, "validated")

        for path in startup.startup_order:
            pin = pins[path]
            raw, text = _read_source(root, pin)
            if not text.strip():
                raise _Hold("source_incomplete_or_invalid", pin)
            instructions.append(text)
            evidence(pin, "retained", raw_byte_span=[0, len(raw)])

        by_xid = {pin.xid: pin for pin in pins.values() if pin.xid}
        for xid in startup.selected_xids:
            pin = by_xid[xid]
            try:
                raw, text = _read_source(root, pin)
                if _XID_MARKER.findall(text) != [xid]:
                    raise _Hold("source_xid_mismatch_or_ambiguous", pin)
                if pin.role == "required-support" and not _XID_MARKER.sub("", text, count=1).strip():
                    raise _Hold("source_incomplete_or_invalid", pin)
            except _Hold as exc:
                if pin.role == "required-support" or exc.reason in ("source_outside_root", "invalid_source_path"):
                    raise
                evidence(pin, "omitted", reason=exc.reason)
                continue
            support.append((pin, {"xid": xid, "text": text}))
            evidence(pin, "retained", raw_byte_span=[0, len(raw)])
        for xid, pin in by_xid.items():
            if xid not in startup.selected_xids:
                evidence(pin, "omitted", reason="not_selected")

        for pin in pins.values():
            if pin.role != "optional-tool-data":
                continue
            try:
                _, text = _read_source(root, pin)
                fields = _tool_fields(text)
            except _Hold as exc:
                if exc.reason in ("source_outside_root", "invalid_source_path"):
                    raise
                evidence(pin, "omitted", reason=exc.reason)
                continue
            except ValueError:
                evidence(pin, "omitted", reason="invalid_tool_data")
                continue
            support.append((pin, {"tool_result": fields}))
            evidence(pin, "retained", retained_fields=sorted(fields))

        payload = payload_bytes()
        for role in ("optional-tool-data", "optional-support"):
            for pin, item in reversed(support.copy()):
                if len(payload) <= FIXTURE_CONTEXT_BYTE_LIMIT:
                    break
                if pin.role == role:
                    support.remove((pin, item))
                    size_omissions.append(pin.path)
                    evidence(pin, "omitted", reason="context_byte_limit")
                    payload = payload_bytes()
        if len(payload) > FIXTURE_CONTEXT_BYTE_LIMIT:
            raise _Hold("required_context_byte_limit")
        return finish(payload, None)
    except _Hold as exc:
        if exc.source is not None:
            evidence(exc.source, "held", reason=exc.reason)
        return finish(None, exc.reason)

"""Record an offline, host-owned execution receipt for a delegated Run."""

from datetime import datetime
import hashlib
import json
from pathlib import Path

from xrefkit.skillrun import (
    _LogFileLock, _append_observation_event, _atomic_write_text, _log_field,
    _observation_events, _validate_observation_log,
)


IDENTITY = ("run_id", "flow_id", "root_run_id", "parent_run_id", "work_item_id")
EVENT = "child_run.host_completed"


def _read_receipt(path, text):
    with path.open("rb") as stream:
        raw = stream.read(64_001)
    if len(raw) > 64_000:
        raise ValueError("host receipt is too large")
    receipt = json.loads(raw)
    fields = {*IDENTITY, "schema_version", "invocation_id", "started_at", "completed_at", "outcome"}
    if (not isinstance(receipt, dict) or set(receipt) != fields
            or type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1
            or receipt["outcome"] != "succeeded"):
        raise ValueError("expected a successful host execution receipt")
    if any(not isinstance(receipt[key], str) or not receipt[key].strip() for key in fields - {"schema_version"}):
        raise ValueError("host receipt fields must be nonempty")
    if any(receipt[key] != _log_field(text, key) for key in IDENTITY):
        raise ValueError("host receipt does not match the child Run correlation")
    started = datetime.fromisoformat(receipt["started_at"])
    completed = datetime.fromisoformat(receipt["completed_at"])
    if started.utcoffset() is None or completed.utcoffset() is None or completed < started:
        raise ValueError("host receipt has invalid execution timestamps")
    return receipt, hashlib.sha256(raw).hexdigest()


def has_host_completion(text, log):
    for event in _observation_events(text):
        if event.get("event") != EVENT:
            continue
        try:
            path = (log.parent / event["receipt_path"]).resolve()
            if path.parent != log.parent or path == log:
                continue
            receipt, digest = _read_receipt(path, text)
            if (digest == event["sha256"] and receipt["invocation_id"] == event["invocation_id"]
                    and receipt["run_id"] == event["run_id"]):
                return True
        except (KeyError, TypeError, ValueError, OSError):
            continue
    return False


def cmd_record_child_execution(args) -> int:
    """The calling host authenticates the source of the original execution receipt."""
    try:
        root = Path(args.root).resolve()
        log = (root / args.log).resolve()
        path = (root / args.receipt).resolve()
        if not log.is_relative_to(root) or path.parent != log.parent or path == log:
            raise ValueError("receipt and child log must be distinct files in the same directory within --root")
        with _LogFileLock(log.with_name(f".{log.name}.lock")):
            text, error = _validate_observation_log(log)
            if error:
                raise ValueError("; ".join(error.errors))
            receipt, digest = _read_receipt(path, text)
            event = {
                "event": EVENT, "receipt_path": path.name, "sha256": digest,
                "invocation_id": receipt["invocation_id"], "run_id": receipt["run_id"],
            }
            existing = [item for item in _observation_events(text) if item.get("event") == EVENT]
            if existing and existing != [event]:
                raise ValueError("a different successful host execution receipt is already registered")
            if not existing:
                _atomic_write_text(log, _append_observation_event(text, section="Host Execution", event=event))
    except (ValueError, OSError, TimeoutError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, "receipt": event, "reused": bool(existing)}, ensure_ascii=False))
    return 0

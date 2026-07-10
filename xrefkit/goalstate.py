from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import time


VALID_PACKET_STATUSES = {"valid", "superseded", "blocked", "cancelled"}
VALID_WAKE_RECOVERY_TYPES = {"five_hour", "weekly", "unknown"}


class StateCorruptionError(ValueError):
    """Persisted goal state exists but cannot be trusted."""


@dataclass
class GoalStateResult:
    ok: bool
    action: str
    data: dict[str, object] | None = None
    errors: list[str] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "action": self.action,
            "data": self.data or {},
            "errors": self.errors or [],
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_goal_slug(value: str) -> str:
    chars = [ch.lower() if ch.isalnum() else "_" for ch in value]
    slug = "".join(chars).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    slug = slug or "goal"
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    return f"{slug}-{digest}"


def _goal_mode_dir(root: Path) -> Path:
    return root / "work" / "goal_mode"


def _packets_path(root: Path) -> Path:
    return _goal_mode_dir(root) / "continuation_packets.jsonl"


def _lease_events_path(root: Path) -> Path:
    return _goal_mode_dir(root) / "lease_events.jsonl"


def _wake_events_path(root: Path) -> Path:
    return _goal_mode_dir(root) / "wake_events.jsonl"


def _leases_dir(root: Path) -> Path:
    return _goal_mode_dir(root) / "leases"


def _goals_dir(root: Path) -> Path:
    return _goal_mode_dir(root) / "goals"


def _wake_dir(root: Path) -> Path:
    return _goal_mode_dir(root) / "wake"


def _goal_lease_path(root: Path, goal_id: str) -> Path:
    return _leases_dir(root) / f"{_safe_goal_slug(goal_id)}.json"


def _goal_wake_path(root: Path, goal_id: str) -> Path:
    return _wake_dir(root) / f"{_safe_goal_slug(goal_id)}.json"


def _goal_lock_path(root: Path, goal_id: str) -> Path:
    return _goal_mode_dir(root) / "locks" / f"{_safe_goal_slug(goal_id)}.lock"


def _goal_record_path(root: Path, goal_id: str) -> Path:
    return _goals_dir(root) / f"{_safe_goal_slug(goal_id)}.json"


def _ensure_goal_dirs(root: Path) -> None:
    _goal_mode_dir(root).mkdir(parents=True, exist_ok=True)
    _goals_dir(root).mkdir(parents=True, exist_ok=True)
    _leases_dir(root).mkdir(parents=True, exist_ok=True)
    _wake_dir(root).mkdir(parents=True, exist_ok=True)
    (_goal_mode_dir(root) / "locks").mkdir(parents=True, exist_ok=True)


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _read_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StateCorruptionError(f"corrupt persisted state: {path}") from exc
    if not isinstance(loaded, dict):
        raise StateCorruptionError(f"persisted state must be an object: {path}")
    return loaded


class _GoalLock:
    def __init__(self, path: Path, owner: str, timeout_seconds: float = 3.0) -> None:
        self.path = path
        self.owner = owner
        self.timeout_seconds = timeout_seconds
        self._acquired = False

    def __enter__(self) -> "_GoalLock":
        deadline = time.time() + self.timeout_seconds
        payload = json.dumps({"owner": self.owner, "acquired_at": _now_iso()}, ensure_ascii=False)
        while True:
            try:
                with self.path.open("x", encoding="utf-8") as fh:
                    fh.write(payload + "\n")
                self._acquired = True
                return self
            except FileExistsError:
                if time.time() >= deadline:
                    raise TimeoutError(f"timed out acquiring goal lock: {self.path}")
                time.sleep(0.05)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._acquired and self.path.exists():
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass


def _load_packets(root: Path) -> list[dict[str, object]]:
    path = _packets_path(root)
    if not path.exists():
        return []
    packets: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            packets.append(payload)
    return packets


def _latest_packet(root: Path, goal_id: str, *, valid_only: bool = False) -> dict[str, object] | None:
    packets = _load_packets(root)
    for packet in reversed(packets):
        if packet.get("goal_id") != goal_id:
            continue
        if valid_only and packet.get("packet_status") != "valid":
            continue
        return packet
    return None


def _parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_acceptance(values: list[str]) -> tuple[list[dict[str, object]], list[str]]:
    conditions: list[dict[str, object]] = []
    errors: list[str] = []
    seen: set[str] = set()
    for raw in values:
        condition_id, separator, text = str(raw).partition(":")
        condition_id = condition_id.strip()
        text = text.strip()
        if not separator or not condition_id or not text:
            errors.append(f"invalid acceptance condition: {raw!r}; expected id:text")
            continue
        if condition_id in seen:
            errors.append(f"duplicate acceptance condition: {condition_id}")
            continue
        seen.add(condition_id)
        conditions.append({"id": condition_id, "text": text, "status": "pending", "evidence": []})
    return conditions, errors


def define_goal(args) -> GoalStateResult:
    root = Path(args.root).resolve()
    _ensure_goal_dirs(root)
    goal_id = str(args.goal).strip()
    desired_state = str(args.state).strip()
    conditions, errors = _parse_acceptance(list(args.acceptance or []))
    if not goal_id:
        errors.append("missing --goal")
    if not desired_state:
        errors.append("missing --state")
    if not conditions:
        errors.append("at least one acceptance condition is required")
    if errors:
        return GoalStateResult(ok=False, action="goal.define", errors=errors)
    path = _goal_record_path(root, goal_id)
    previous = _read_json(path)
    now = _now_iso()
    record = {
        "schema": "xrefkit.goal/v1",
        "goal_id": goal_id,
        "desired_state": desired_state,
        "acceptance_conditions": conditions,
        "observed_state": "",
        "blockers": [],
        "risks": [],
        "status": "active",
        "acceptance_owner": str(args.owner or "").strip(),
        "created_at": previous.get("created_at", now) if previous else now,
        "updated_at": now,
        "completed_at": None,
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return GoalStateResult(ok=True, action="goal.define", data=record)


def show_goal(args) -> GoalStateResult:
    root = Path(args.root).resolve()
    goal_id = str(args.goal).strip()
    record = _read_json(_goal_record_path(root, goal_id))
    if record is None:
        return GoalStateResult(ok=False, action="goal.show", errors=[f"no goal found: {goal_id}"])
    return GoalStateResult(ok=True, action="goal.show", data=record)


def complete_goal(args) -> GoalStateResult:
    root = Path(args.root).resolve()
    _ensure_goal_dirs(root)
    goal_id = str(args.goal).strip()
    path = _goal_record_path(root, goal_id)
    record = _read_json(path)
    if record is None:
        return GoalStateResult(ok=False, action="goal.complete", errors=[f"no goal found: {goal_id}"])
    evidence: dict[str, list[str]] = {}
    errors: list[str] = []
    for raw in list(args.evidence or []):
        condition_id, separator, reference = str(raw).partition("=")
        if not separator or not condition_id.strip() or not reference.strip():
            errors.append(f"invalid evidence: {raw!r}; expected condition_id=reference")
            continue
        evidence.setdefault(condition_id.strip(), []).append(reference.strip())
    known = {str(item["id"]) for item in record.get("acceptance_conditions", [])}
    unknown = sorted(set(evidence) - known)
    if unknown:
        errors.append(f"unknown acceptance conditions: {unknown}")
    updated_conditions: list[dict[str, object]] = []
    missing: list[str] = []
    for item in record.get("acceptance_conditions", []):
        condition_id = str(item["id"])
        refs = evidence.get(condition_id, [])
        if not refs:
            missing.append(condition_id)
        updated_conditions.append({**item, "status": "met" if refs else "pending", "evidence": refs})
    if missing:
        errors.append(f"missing acceptance evidence: {missing}")
    observed = str(args.observed_state).strip()
    if not observed:
        errors.append("missing --observed-state")
    if errors:
        return GoalStateResult(
            ok=False,
            action="goal.complete",
            data={**record, "acceptance_conditions": updated_conditions},
            errors=errors,
        )
    now = _now_iso()
    completed = {
        **record,
        "acceptance_conditions": updated_conditions,
        "observed_state": observed,
        "status": "complete",
        "updated_at": now,
        "completed_at": now,
    }
    path.write_text(json.dumps(completed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return GoalStateResult(ok=True, action="goal.complete", data=completed)


def append_packet(args) -> GoalStateResult:
    root = Path(args.root).resolve()
    _ensure_goal_dirs(root)

    goal_id = str(args.goal).strip()
    summary = str(args.summary).strip()
    next_action = str(args.next_action).strip()
    packet_status = str(args.status).strip().lower()

    if not goal_id:
        return GoalStateResult(ok=False, action="packet.append", errors=["missing --goal"])
    if not summary:
        return GoalStateResult(ok=False, action="packet.append", errors=["missing --summary"])
    if not next_action:
        return GoalStateResult(ok=False, action="packet.append", errors=["missing --next-action"])
    if packet_status not in VALID_PACKET_STATUSES:
        return GoalStateResult(ok=False, action="packet.append", errors=[f"invalid packet status: {packet_status}"])

    created_at = _now_iso()
    packet = {
        "goal_id": goal_id,
        "packet_id": f"{_safe_goal_slug(goal_id)}-{created_at}",
        "created_at": created_at,
        "created_by": str(args.created_by or "").strip() or "xrefkit goal packet append",
        "continuation_log": str(args.continuation_log or "").strip(),
        "continuation_artifacts": [str(v).strip() for v in (args.artifact or []) if str(v).strip()],
        "goal_state_summary": summary,
        "next_first_action": next_action,
        "current_boundary": str(args.boundary or "").strip(),
        "stop_conditions": [str(v).strip() for v in (args.stop_condition or []) if str(v).strip()],
        "drift_check_points": [str(v).strip() for v in (args.drift_check or []) if str(v).strip()],
        "packet_status": packet_status,
        "source_run_key": str(args.source_run_key or "").strip(),
        "trace_id": str(args.trace_id or "").strip(),
        "parent_packet_id": str(args.parent_packet or "").strip(),
        "subgoal_id": str(args.subgoal or "").strip(),
        "resume_blockers": [str(v).strip() for v in (args.resume_blocker or []) if str(v).strip()],
        "expiry_hint": str(args.expiry_hint or "").strip(),
    }
    _append_jsonl(_packets_path(root), packet)
    return GoalStateResult(ok=True, action="packet.append", data=packet)


def latest_packet(args) -> GoalStateResult:
    root = Path(args.root).resolve()
    goal_id = str(args.goal).strip()
    if not goal_id:
        return GoalStateResult(ok=False, action="packet.latest", errors=["missing --goal"])
    packet = _latest_packet(root, goal_id, valid_only=bool(args.valid_only))
    if packet is None:
        return GoalStateResult(ok=False, action="packet.latest", errors=[f"no packet found for goal: {goal_id}"])
    return GoalStateResult(ok=True, action="packet.latest", data=packet)


def observe_wake(args) -> GoalStateResult:
    root = Path(args.root).resolve()
    _ensure_goal_dirs(root)

    goal_id = str(args.goal).strip()
    source = str(args.source).strip()
    recovery_type = str(args.recovery_type).strip().lower()
    if not goal_id:
        return GoalStateResult(ok=False, action="wake.observe", errors=["missing --goal"])
    if not source:
        return GoalStateResult(ok=False, action="wake.observe", errors=["missing --source"])
    if recovery_type not in VALID_WAKE_RECOVERY_TYPES:
        return GoalStateResult(ok=False, action="wake.observe", errors=[f"invalid recovery type: {recovery_type}"])

    try:
        with _GoalLock(_goal_lock_path(root, goal_id), owner=f"wake:{source}"):
            wake = {
                "goal_id": goal_id,
                "observed_at": _now_iso(),
                "source": source,
                "recovery_type": recovery_type,
                "note": str(args.note or "").strip(),
                "status": "wakeup_observed",
            }
            _goal_wake_path(root, goal_id).write_text(json.dumps(wake, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _append_jsonl(_wake_events_path(root), {"event": "observe", **wake})
    except TimeoutError as exc:
        return GoalStateResult(ok=False, action="wake.observe", errors=[str(exc)])
    return GoalStateResult(ok=True, action="wake.observe", data=wake)


def show_wake(args) -> GoalStateResult:
    root = Path(args.root).resolve()
    goal_id = str(args.goal).strip()
    if not goal_id:
        return GoalStateResult(ok=False, action="wake.show", errors=["missing --goal"])
    wake = _read_json(_goal_wake_path(root, goal_id))
    if wake is None:
        return GoalStateResult(ok=False, action="wake.show", errors=[f"no wake state found for goal: {goal_id}"])
    return GoalStateResult(ok=True, action="wake.show", data=wake)


def acquire_lease(args) -> GoalStateResult:
    root = Path(args.root).resolve()
    _ensure_goal_dirs(root)

    goal_id = str(args.goal).strip()
    owner = str(args.owner).strip()
    ttl_hours = int(args.ttl_hours)
    if not goal_id:
        return GoalStateResult(ok=False, action="lease.acquire", errors=["missing --goal"])
    if not owner:
        return GoalStateResult(ok=False, action="lease.acquire", errors=["missing --owner"])
    if ttl_hours < 1:
        return GoalStateResult(ok=False, action="lease.acquire", errors=["--ttl-hours must be >= 1"])

    try:
        with _GoalLock(_goal_lock_path(root, goal_id), owner=f"lease:{owner}"):
            wake = _read_json(_goal_wake_path(root, goal_id))
            if wake is None:
                return GoalStateResult(ok=False, action="lease.acquire", errors=[f"goal is not wakeup_observed: {goal_id}"])

            lease_path = _goal_lease_path(root, goal_id)
            active = _read_json(lease_path)
            now = datetime.now(timezone.utc)
            if active and active.get("lease_status") == "leased":
                expires_at = _parse_iso(active.get("lease_expires_at"))
                if expires_at and expires_at > now:
                    return GoalStateResult(
                        ok=False,
                        action="lease.acquire",
                        errors=[f"active lease already exists for goal {goal_id} owner={active.get('lease_owner', '')}"],
                    )

            source_packet_id = str(args.source_packet or "").strip()
            if not source_packet_id:
                latest = _latest_packet(root, goal_id, valid_only=True)
                if latest is None:
                    return GoalStateResult(ok=False, action="lease.acquire", errors=[f"no valid packet found for goal: {goal_id}"])
                source_packet_id = str(latest.get("packet_id") or "").strip()
                if not source_packet_id:
                    return GoalStateResult(ok=False, action="lease.acquire", errors=[f"latest packet missing packet_id for goal: {goal_id}"])

            lease = {
                "goal_id": goal_id,
                "lease_owner": owner,
                "lease_acquired_at": now.isoformat(),
                "lease_expires_at": (now + timedelta(hours=ttl_hours)).isoformat(),
                "lease_status": "leased",
                "source_packet_id": source_packet_id,
                "attempt_count": int(active.get("attempt_count", 0)) + 1 if active else 1,
            }
            lease_path.write_text(json.dumps(lease, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _append_jsonl(_lease_events_path(root), {"event": "acquire", **lease})
    except (TimeoutError, StateCorruptionError) as exc:
        return GoalStateResult(ok=False, action="lease.acquire", errors=[str(exc)])
    return GoalStateResult(ok=True, action="lease.acquire", data=lease)


def release_lease(args) -> GoalStateResult:
    root = Path(args.root).resolve()
    _ensure_goal_dirs(root)

    goal_id = str(args.goal).strip()
    owner = str(args.owner).strip()
    if not goal_id:
        return GoalStateResult(ok=False, action="lease.release", errors=["missing --goal"])
    if not owner and not bool(args.force):
        return GoalStateResult(ok=False, action="lease.release", errors=["missing --owner unless --force is used"])

    try:
        with _GoalLock(_goal_lock_path(root, goal_id), owner=f"release:{owner or 'force'}"):
            lease_path = _goal_lease_path(root, goal_id)
            active = _read_json(lease_path)
            if active is None:
                return GoalStateResult(ok=False, action="lease.release", errors=[f"no lease found for goal: {goal_id}"])
            current_owner = str(active.get("lease_owner") or "")
            if not bool(args.force) and owner != current_owner:
                return GoalStateResult(
                    ok=False,
                    action="lease.release",
                    errors=[f"lease owner mismatch for goal {goal_id}: current={current_owner} requested={owner}"],
                )

            released = {
                **active,
                "lease_status": "released",
                "released_at": _now_iso(),
                "released_by": owner or "force",
                "release_note": str(args.note or "").strip(),
            }
            lease_path.write_text(json.dumps(released, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _append_jsonl(_lease_events_path(root), {"event": "release", **released})
    except (TimeoutError, StateCorruptionError) as exc:
        return GoalStateResult(ok=False, action="lease.release", errors=[str(exc)])
    return GoalStateResult(ok=True, action="lease.release", data=released)


def show_lease(args) -> GoalStateResult:
    root = Path(args.root).resolve()
    goal_id = str(args.goal).strip()
    if not goal_id:
        return GoalStateResult(ok=False, action="lease.show", errors=["missing --goal"])
    try:
        lease = _read_json(_goal_lease_path(root, goal_id))
    except StateCorruptionError as exc:
        return GoalStateResult(ok=False, action="lease.show", errors=[str(exc)])
    if lease is None:
        return GoalStateResult(ok=False, action="lease.show", errors=[f"no lease found for goal: {goal_id}"])
    return GoalStateResult(ok=True, action="lease.show", data=lease)


def _print_result(result: GoalStateResult, as_json: bool) -> int:
    if as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.ok:
        print(f"ok: {result.action}")
        for key, value in (result.data or {}).items():
            if value in ("", [], None):
                continue
            if isinstance(value, list):
                print(f"  {key}:")
                for item in value:
                    print(f"    - {item}")
            else:
                print(f"  {key}: {value}")
    else:
        print(f"fail: {result.action}")
        for error in result.errors or []:
            print(f"  error: {error}")
    return 0 if result.ok else 1


def cmd_goal(args) -> int:
    if args.goal_cmd == "define":
        return _print_result(define_goal(args), bool(args.json))
    if args.goal_cmd == "show":
        return _print_result(show_goal(args), bool(args.json))
    if args.goal_cmd == "complete":
        return _print_result(complete_goal(args), bool(args.json))
    if args.goal_cmd == "packet":
        if args.packet_cmd == "append":
            return _print_result(append_packet(args), bool(args.json))
        if args.packet_cmd == "latest":
            return _print_result(latest_packet(args), bool(args.json))
    if args.goal_cmd == "lease":
        if args.lease_cmd == "acquire":
            return _print_result(acquire_lease(args), bool(args.json))
        if args.lease_cmd == "release":
            return _print_result(release_lease(args), bool(args.json))
        if args.lease_cmd == "show":
            return _print_result(show_lease(args), bool(args.json))
    if args.goal_cmd == "wake":
        if args.wake_cmd == "observe":
            return _print_result(observe_wake(args), bool(args.json))
        if args.wake_cmd == "show":
            return _print_result(show_wake(args), bool(args.json))
    print("fail: goal")
    print("  error: unsupported goal subcommand")
    return 1

"""Interactive Codex Desktop adapter for the bounded stub workflow."""

from __future__ import annotations

import argparse
from contextlib import closing, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
from time import monotonic, sleep
from uuid import UUID

from . import host
from .acquisition import AcquisitionCancelled, AcquisitionError, resolve_core
from .desktop_pilot import PILOT_CASES, STOP_FOLLOWUPS


_STARTUP_XID = "C3A1F78D9B22"


def _acquisition_stop(thread: str, turn: str):
    rollout = host._local_rollout(thread)
    offset = 0
    checked_at = float("-inf")
    stopped = False

    def stopped_by_host():
        nonlocal offset, checked_at, stopped
        now = monotonic()
        if not stopped and now - checked_at >= 0.1:
            stopped, offset = host._read_abort(rollout, turn, offset)
            checked_at = now
        return stopped

    return stopped_by_host


def _core_startup(args: argparse.Namespace, stop_requested) -> dict:
    with args.core_startup_file.open("rb") as stream:
        content = stream.read(20001)
    digest = hashlib.sha256(content).hexdigest()
    if (
        len(content) > 20000 or digest != args.core_startup_sha256
        or f"<!-- xid: {_STARTUP_XID} -->" not in content.decode("utf-8-sig").splitlines()
    ):
        raise AcquisitionError("Core startup contract does not match the reviewed source")
    ready = resolve_core(
        args.core_lock, local_python=args.core_python, cache_dir=args.core_cache_dir,
        wheelhouse=args.core_wheelhouse, offline=True, stop_requested=stop_requested,
    )
    return {
        "status": "core_runtime_ready",
        "source": ready["source"],
        "version": ready["version"],
        "target": ready["target"],
        "binding_schema_version": ready["binding_schema_version"],
        "lock_sha256": ready["lock_sha256"],
        "startup_xid": _STARTUP_XID,
        "startup_sha256": digest,
    }


def _emit(payload: dict) -> None:
    print(json.dumps(payload), flush=True)


def _origin(thread: str, turn: str) -> bool:
    _emit({"status": "verify_origin", "thread_id": thread, "turn_id": turn})
    try:
        snapshot = json.loads(input())
    except (EOFError, ValueError):
        return False
    return isinstance(snapshot, dict) and (
        snapshot.get("hostId"), snapshot.get("threadId"), snapshot.get("turnId"), snapshot.get("status")
    ) == ("local", thread, turn, "inProgress")


def _host(arguments: list[str], *, observer=None) -> dict:
    output = io.StringIO()
    with redirect_stdout(output):
        host.main(arguments, observer=observer)
    return json.loads(output.getvalue())


def _stop_observer(case):
    stdout = sys.stdout
    sent = False

    def check(execution):
        nonlocal sent
        if sent:
            return
        try:
            with closing(sqlite3.connect(host._profile_path().resolve().as_uri() + "?mode=ro",
                                         uri=True, timeout=0)) as db:
                row = db.execute(
                    "SELECT 1 FROM desktop_pilot_v1 WHERE execution=? AND scenario=? "
                    "AND status='in_progress' AND response_id IS NOT NULL", (execution, case),
                ).fetchone()
        except sqlite3.Error:
            return
        if row:
            print(json.dumps({"status": "stop_ready", "execution_id": execution,
                              "provider_status": "in_progress"}), file=stdout, flush=True)
            sent = True

    return check


def _resume(journal: Path, thread: str, turn: str, seconds: float, provider: str) -> dict:
    deadline = monotonic() + seconds
    try:
        rollout = host._local_rollout(thread)
    except (OSError, ValueError):
        rollout = None
    offset = 0
    with closing(sqlite3.connect(journal.resolve().as_uri() + "?mode=ro", uri=True)) as database:
        while True:
            record = database.execute(
                "SELECT s.execution, s.disposition, s.result IS NOT NULL, s.claimed, "
                "c.execution IS NOT NULL FROM smoke_turn s "
                "JOIN host_job j USING (execution) LEFT JOIN host_closed_turn c USING (execution) "
                "WHERE s.thread=? AND s.invocation=? AND j.provider=?",
                (thread, f"codex-turn:{turn}", provider),
            ).fetchone()
            if not record:
                return {"status": "execution_not_found"}
            execution, disposition, saved, claimed, closed = record
            if not closed and rollout is not None:
                try:
                    stopped, offset = host._read_abort(rollout, turn, offset)
                except OSError:
                    stopped = False
                if stopped:
                    closure = _host(["--journal", str(journal), "--turn-id", turn, "--origin-closed", execution])
                    if closure["status"] == "origin_closed":
                        continue
            if closed and disposition != "running":
                break
            remaining = deadline - monotonic()
            if remaining <= 0:
                return {"status": "hold_reconciliation", "execution_id": execution}
            sleep(min(0.1, remaining))
    outcome = _host(["--rollback"])
    return {"status": outcome["status"], "execution_id": execution, "origin_closed": True,
            "disposition": disposition, "result_saved": bool(saved), "result_claimed": bool(claimed)}


def offline_main() -> int:
    """Start the packaged Desktop workflow with the bundled offline profile."""
    return main(sys.argv[1:], packaged=True)


def main(argv: list[str], *, packaged: bool = False) -> int:
    from .distribution import CORE_LOCK, STARTUP_CONTRACT, STARTUP_SHA256

    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=not packaged)
    parser.add_argument("--journal", required=True, type=Path)
    parser.add_argument("--turn-id", required=True)
    parser.add_argument("--core-lock", type=Path, default=CORE_LOCK if packaged else None, help="reviewed Core lock for offline Desktop startup")
    parser.add_argument("--core-startup-file", type=Path, default=STARTUP_CONTRACT if packaged else None, help="explicit trusted startup contract")
    parser.add_argument("--core-startup-sha256", default=STARTUP_SHA256 if packaged else None, help="reviewed SHA-256 for the startup contract bytes")
    parser.add_argument("--core-python", type=Path, help="trusted local Core interpreter")
    parser.add_argument("--core-cache-dir", type=Path)
    parser.add_argument("--core-wheelhouse", type=Path, help="local source for the offline Core cache")
    parser.add_argument("--wait-seconds", type=float, default=5)
    parser.add_argument("--final-receipt-delay", type=float, default=0)
    parser.add_argument("--reconcile-seconds", type=float, default=35)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--resume-and-rollback", action="store_true")
    parser.set_defaults(pilot_case=None, reconcile_usage=False)
    if not packaged:
        action.add_argument("--reconcile-usage", action="store_true")
        parser.add_argument("--pilot-case", choices=PILOT_CASES)
    args = parser.parse_args(argv)
    if args.core_lock is None and any((args.core_python, args.core_cache_dir, args.core_wheelhouse,
                                     args.core_startup_file, args.core_startup_sha256)):
        parser.error("Core startup options require --core-lock")
    if args.core_lock is not None and not (args.resume_and_rollback or args.reconcile_usage):
        pin = args.core_startup_sha256
        if args.core_startup_file is None or pin is None or len(pin) != 64 or any(c not in "0123456789abcdef" for c in pin):
            parser.error("--core-lock requires --core-startup-file and a lowercase --core-startup-sha256")
    provider = "openai" if args.pilot_case else "stub"
    if not (0 < args.wait_seconds <= 60 and 0 < args.reconcile_seconds <= (120 if args.pilot_case else 60)
            and 0 <= args.final_receipt_delay <= 30):
        parser.error("wait and receipt delay must be within the bounded verification range")
    thread, turn = os.environ.get("CODEX_THREAD_ID", ""), args.turn_id
    try:
        if any(str(UUID(value)) != value for value in (thread, turn)):
            raise ValueError
    except ValueError:
        _emit({"status": "hold", "reason": "invalid_origin"})
        return 2
    if args.reconcile_usage:
        from .pilot_reconciliation import reconcile

        project = os.environ.get("XREFKIT_PILOT_PROJECT", "")
        if (not args.pilot_case or not project or os.environ.get("XREFKIT_PILOT_AUTHORIZED") != "yes"
                or not os.environ.get("OPENAI_API_KEY", "").strip()):
            _emit({"status": "hold_reconciliation", "reason": "pilot_configuration_unconfirmed"})
            return 2
        try:
            outcome = reconcile(
                args.journal, thread, turn, args.pilot_case, project, host._admission,
                lambda method, path, timeout, body: host._background_request(
                    method, path, timeout, body, project=project
                ),
            )
        except (OSError, sqlite3.Error):
            outcome = {"status": "hold_reconciliation", "reason": "journal_or_profile_unavailable"}
        _emit(outcome)
        return 0 if outcome["status"] in {"usage_settled", "already_settled"} else 2

    if args.resume_and_rollback:
        try:
            outcome = _resume(args.journal, thread, turn, args.reconcile_seconds,
                              "pilot:" + args.pilot_case if args.pilot_case else provider)
        except sqlite3.Error:
            outcome = {"status": "hold", "reason": "journal_unavailable"}
        _emit(outcome)
        return 0 if outcome["status"] == "rolled_back" else 2

    if not _origin(thread, turn):
        _emit({"status": "hold", "reason": "origin_unconfirmed"})
        return 2
    if args.core_lock is not None:
        try:
            stopped = _acquisition_stop(thread, turn)
            if stopped():
                raise AcquisitionCancelled("Core acquisition stopped")
            _emit(_core_startup(args, stopped))
        except AcquisitionCancelled:
            _emit({"status": "hold", "reason": "core_acquisition_stopped"})
            return 2
        except (AcquisitionError, OSError, ValueError, KeyError):
            _emit({"status": "hold", "reason": "core_startup_unavailable"})
            return 2
        # Acquisition can outlast the originating turn. Refresh host evidence before starting work.
        if not _origin(thread, turn):
            _emit({"status": "hold", "reason": "origin_unconfirmed_after_core_startup"})
            return 2
    base = ["--journal", str(args.journal), "--turn-id", turn, "--provider", provider]
    pilot = ["--pilot-case", args.pilot_case] if args.pilot_case else []
    observer = _stop_observer(args.pilot_case) if args.pilot_case in STOP_FOLLOWUPS else None
    started = _host([*base, "--defer-presentation", "--watch-local-stop",
                     "--wait-seconds", str(args.wait_seconds),
                     "--final-receipt-delay", str(args.final_receipt_delay), *pilot], observer=observer)
    _emit(started)
    execution = started.get("execution_id")
    if started["status"] in {"running", "wait_expired"}:
        started = _host([*base, "--await-candidate", execution,
                         "--reconcile-seconds", str(args.reconcile_seconds), *pilot], observer=observer)
        _emit(started)
    if started["status"] != "candidate" or started.get("result_claimed"):
        return 0 if started["status"] in {"candidate", "origin_closed", "fixture_completed", "fixture_incomplete"} else 2
    if not _origin(thread, turn):
        _emit({"status": "hold", "reason": "origin_unconfirmed", "execution_id": execution})
        return 2
    result = _host([*base, "--reconcile", execution])
    _emit(result)
    return 0 if result["status"] in {"candidate", "origin_closed"} else 2

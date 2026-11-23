"""Return a bounded synthetic API turn to its originating Codex command."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from contextlib import ExitStack, closing, contextmanager
from http.client import HTTPSConnection, HTTPException
import json
import os
import re
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Event, Thread
from time import monotonic, sleep
from uuid import UUID, uuid4

from .desktop_pilot import FOLLOWUP_AUTHORIZATION, PILOT_CASES
from .smoke import TurnStore, _execute, _openai, _stub


class HostProviderMismatch(ValueError):
    def __init__(self, existing: str, requested: str) -> None:
        super().__init__(f"existing host execution uses {existing}, requested {requested}")
        self.existing = existing
        self.requested = requested


class HostStore(TurnStore):
    def __init__(self, database: sqlite3.Connection) -> None:
        super().__init__(database)
        database.execute("""
            CREATE TABLE IF NOT EXISTS host_job (
                execution TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                deadline REAL NOT NULL,
                delay REAL NOT NULL,
                worker_started INTEGER NOT NULL DEFAULT 0
            )
        """)
        database.execute("""
            CREATE TABLE IF NOT EXISTS host_provider_event (
                execution TEXT NOT NULL,
                operation TEXT NOT NULL,
                status TEXT NOT NULL,
                http INTEGER NOT NULL
            )
        """)
        database.execute("""
            CREATE TABLE IF NOT EXISTS host_closed_turn (
                execution TEXT PRIMARY KEY
            )
        """)

    def start_turn(
        self, thread: str, turn: str, provider: str, deadline: float, delay: float,
    ) -> tuple[str, bool]:
        execution = uuid4().hex
        invocation = f"codex-turn:{turn}"
        with self.database:
            started = self.database.execute(
                "INSERT OR IGNORE INTO smoke_turn VALUES (?, ?, ?, 'running', NULL, 0)",
                (execution, thread, invocation),
            ).rowcount == 1
            if started:
                self.database.execute(
                    "INSERT INTO host_job (execution, provider, deadline, delay) VALUES (?, ?, ?, ?)",
                    (execution, provider, deadline, delay),
                )
            original, existing_provider = self.database.execute(
                "SELECT execution, provider FROM smoke_turn LEFT JOIN host_job USING (execution) "
                "WHERE thread = ? AND invocation = ?",
                (thread, invocation),
            ).fetchone()
            if existing_provider is None:
                raise sqlite3.IntegrityError("host execution has no job binding")
            if existing_provider != provider:
                raise HostProviderMismatch(existing_provider, provider)
        return original, started

    def start_worker(self, execution: str) -> tuple | None:
        with self.database:
            changed = self.database.execute(
                "UPDATE host_job SET worker_started = 1 WHERE execution = ? AND worker_started = 0",
                (execution,),
            ).rowcount
            if not changed:
                return None
            return self.database.execute(
                "SELECT thread, invocation, provider, deadline, delay FROM host_job "
                "JOIN smoke_turn USING (execution) WHERE execution = ?", (execution,),
            ).fetchone()

    def close_origin(self, thread: str, turn: str, execution: str) -> dict:
        with self.database:
            self.database.execute(
                "INSERT OR IGNORE INTO host_closed_turn (execution) "
                "SELECT execution FROM smoke_turn JOIN host_job USING (execution) "
                "WHERE execution = ? AND thread = ? AND invocation = ?",
                (execution, thread, f"codex-turn:{turn}"),
            )
        return self.host_result(thread, turn, execution, claim=False)

    def is_origin_closed(self, execution: str) -> bool:
        return self.database.execute(
            "SELECT 1 FROM host_closed_turn WHERE execution = ?", (execution,),
        ).fetchone() is not None

    def recover_result(self, thread: str, turn: str, execution: str) -> dict:
        """Register one private reference to the original, already claimed body."""
        with self.database:
            self.database.execute("BEGIN IMMEDIATE")
            row = self.database.execute(
                "SELECT disposition, claimed, result IS NOT NULL "
                "FROM smoke_turn JOIN host_job USING (execution) "
                "WHERE execution = ? AND thread = ? AND invocation = ?",
                (execution, thread, f"codex-turn:{turn}"),
            ).fetchone()
            if row is None:
                return {"status": "execution_not_found"}
            if self.is_origin_closed(execution):
                status = "origin_closed"
            elif row != ("candidate", 1, 1):
                status = "recovery_unavailable"
            else:
                self.database.execute(
                    "CREATE TABLE IF NOT EXISTS host_result_recovery (execution TEXT PRIMARY KEY)"
                )
                self.database.execute(
                    "INSERT INTO host_result_recovery VALUES (?) ON CONFLICT(execution) DO NOTHING",
                    (execution,),
                )
                status = "result_recovered"
        return {"execution_id": execution, "status": status}

    def host_result(self, thread: str, turn: str, execution: str, *, claim: bool) -> dict:
        with self.database:
            if claim:
                # Serialize the close fact and a competing result claim.
                self.database.execute("BEGIN IMMEDIATE")
            closed = self.is_origin_closed(execution)
            payload = self.read(thread, execution, claim=claim and not closed, invocation=f"codex-turn:{turn}")
        if closed and payload["status"] != "execution_not_found":
            payload["status"] = "origin_closed"
        if payload["status"] == "running":
            row = self.database.execute(
                "SELECT deadline FROM host_job WHERE execution = ?", (execution,),
            ).fetchone()
            if row is not None and monotonic() >= row[0]:
                payload["status"] = "wait_expired"
        return payload


def _local_rollout(thread: str) -> Path:
    if str(UUID(thread)) != thread:
        raise ValueError("invalid Codex thread identity")
    home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    matches = list((home / "sessions").rglob(f"rollout-*{thread}.jsonl"))
    if len(matches) != 1:
        raise ValueError("expected one local Codex rollout")
    return matches[0]


def _read_abort(path: Path, turn: str, offset: int) -> tuple[bool, int]:
    with path.open("rb") as stream:
        if stream.seek(0, os.SEEK_END) < offset:
            offset = 0
        stream.seek(offset)
        for line in stream:
            if not line.endswith(b"\n"):
                break
            offset += len(line)
            try:
                record = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if not isinstance(record, dict) or record.get("type") != "event_msg":
                continue
            payload = record.get("payload")
            if (isinstance(payload, dict) and payload.get("type") == "turn_aborted"
                    and payload.get("turn_id") == turn):
                return True, offset - len(line)
    return False, offset


def _watch_abort(
    path: Path, journal: Path, execution: str, thread: str, turn: str, finished: Event,
) -> None:
    offset = 0
    while True:
        try:
            stopped, offset = _read_abort(path, turn, offset)
            if stopped:
                with closing(sqlite3.connect(journal)) as database:
                    HostStore(database).close_origin(thread, turn, execution)
                return
        except (OSError, sqlite3.Error):
            # Source failure is not evidence of closure.
            pass
        if finished.wait(0.1):
            return


def _background_request(method: str, path: str, timeout: float, body: dict | None = None, *, project=None):
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError("missing provider credential")
    with closing(HTTPSConnection("api.openai.com", timeout=timeout)) as connection:
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        if project is not None:
            headers["OpenAI-Project"] = project
        connection.request(method, path, None if body is None else json.dumps(body).encode(), headers)
        response = connection.getresponse()
        raw = response.read(1_048_577)
        if len(raw) > 1_048_576:
            raise ValueError("background response exceeds limit")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("invalid background response")
        return response.status, payload


def _background_openai(store: HostStore, execution: str, body: dict, timeout: float, deadline: float):
    def record(operation, http, payload):
        status = payload.get("status")
        known = ("queued", "in_progress", "completed", "cancelled", "failed", "incomplete")
        status = status if http == 200 and status in known else "unknown"
        with store.database:
            store.database.execute("INSERT INTO host_provider_event VALUES (?, ?, ?, ?)",
                                   (execution, operation, status, http))
        return status

    def request(operation, method, path, timeout, body=None):
        try:
            http, payload = _background_request(method, path, timeout, body)
        except (HTTPException, OSError, ValueError):
            record(operation, 0, {})
            raise
        return record(operation, http, payload), payload

    if store.is_origin_closed(execution):
        raise ValueError("origin already closed")
    status, payload = request("create", "POST", "/v1/responses", timeout,
                              {**body, "background": True, "store": False})
    response_id = payload.get("id")
    if not isinstance(response_id, str) or not re.fullmatch(r"resp_[A-Za-z0-9]+", response_id):
        raise ValueError("missing background response identity")
    path = f"/v1/responses/{response_id}"
    while status in ("queued", "in_progress"):
        if store.is_origin_closed(execution):
            status, cancelled = request("cancel", "POST", path + "/cancel", 10)
            if cancelled.get("id") != response_id or status != "cancelled":
                raise ValueError("provider cancellation was not confirmed")
            return cancelled
        if monotonic() >= deadline:
            raise TimeoutError("background response pending at deadline")
        sleep(0.1)
        if store.is_origin_closed(execution):
            continue
        status, payload = request("poll", "GET", path, min(2, max(0.1, deadline - monotonic())))
        if payload.get("id") != response_id:
            raise ValueError("background response identity mismatch")
    if status != "completed":
        raise ValueError("background generation did not complete")
    return payload


def _worker(journal: Path, execution: str, rollout: Path | None = None,
            cancel_mode: str = "") -> None:
    with closing(sqlite3.connect(journal)) as database:
        store = HostStore(database)
        job = store.start_worker(execution)
        if job is None:
            return
        thread, turn, provider, deadline, delay = job
        finished = Event()
        watcher = None
        if rollout is not None:
            watcher = Thread(target=_watch_abort, args=(
                rollout, journal, execution, thread, turn.removeprefix("codex-turn:"), finished,
            ), daemon=True)
            watcher.start()

        def transport(body, send_timeout):
            if provider == "openai":
                if cancel_mode:
                    return _background_openai(store, execution, body, send_timeout, deadline)
                response = _openai(body, send_timeout, receipt_timeout=20)
                if "tools" not in body:
                    sleep(delay)
                return response
            # The final receipt can arrive after the host stops waiting.
            return _stub(body, 60, delay if "tools" not in body else 0)

        try:
            if cancel_mode.startswith("pilot:"):
                from .desktop_pilot import execute
                from .pilot_reconciliation import bind_owner

                project = os.environ.get("XREFKIT_PILOT_PROJECT", "")
                case = cancel_mode.removeprefix("pilot:")
                authorization = FOLLOWUP_AUTHORIZATION.get(case)
                if (provider != cancel_mode or not project or os.environ.get("XREFKIT_PILOT_AUTHORIZED") != "yes"
                        or (authorization and os.environ.get(authorization) != "yes")):
                    raise ValueError("pilot worker configuration unavailable")
                bind_owner(database, journal, execution, project)
                disposition, result = execute(
                    store, execution, case, _admission,
                    lambda method, path, timeout, body: _background_request(
                        method, path, timeout, body, project=project
                    ), deadline + 120,
                )
                store.finish(execution, disposition, result)
                return
            if cancel_mode == "fixture":
                response = _background_openai(store, execution, {
                    "model": "gpt-4.1-mini-2025-04-14",
                    "input": (
                        "This is a synthetic text transformation. Output every supplied record in order, "
                        "changing all letters to uppercase. Output the records only.\n"
                        + "\n".join(f"{i:04d}: amber river willow garden lantern meadow" for i in range(900))
                    ),
                    "max_output_tokens": 16384,
                }, min(10, max(0.1, deadline - monotonic())), deadline)
                store.finish(execution, "cancelled" if response.get("status") == "cancelled"
                             else "fixture_completed", None)
                return
            outcome = _execute(
                store, thread, turn, execution, transport, 0, deadline=deadline,
                stop_requested=lambda: store.is_origin_closed(execution),
            )
            store.finish(execution, outcome.disposition, outcome.result)
        except (HTTPException, OSError, ValueError, sqlite3.Error):
            store.finish(execution, "hold_reconciliation", None)
        finally:
            if watcher is not None:
                finished.set()
                watcher.join()


def _launch(journal: Path, execution: str, rollout: Path | None = None,
            cancel_mode: str = "") -> None:
    package_path = Path(__file__).resolve().parent.parent
    # Reuse exactly this package, including when invoked from a source checkout.
    code = (
        "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); "
        "from xrefkit_openai_runtime.host import _worker; "
        "_worker(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]) if len(sys.argv) > 4 else None, "
        "sys.argv[5] if len(sys.argv) > 5 else '')"
    )
    subprocess.Popen(
        [sys.executable, "-I", "-B", "-c", code, str(package_path), str(journal), execution,
         *([str(rollout), cancel_mode] if rollout is not None else [])],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        start_new_session=os.name != "nt",
    )


def _wait(
    store: HostStore, thread: str, turn: str, execution: str, deadline: float, *, claim: bool = True, observer=None,
) -> dict:
    while monotonic() < deadline:
        status = store.host_result(thread, turn, execution, claim=False)
        if observer is not None and status["status"] in {"running", "wait_expired"}:
            observer(execution)
        if status["status"] != "running":
            if monotonic() < deadline:
                return store.host_result(thread, turn, execution, claim=True) if claim else status
            break
        sleep(min(0.025, max(0, deadline - monotonic())))
    return {"execution_id": execution, "status": "wait_expired", "result_claimed": False}


def _await_candidate(store: HostStore, thread: str, turn: str, execution: str, seconds: float, observer=None) -> dict:
    deadline = monotonic() + seconds
    while True:
        status = store.host_result(thread, turn, execution, claim=False)
        if observer is not None and status["status"] in {"running", "wait_expired"}:
            observer(execution)
        remaining = deadline - monotonic()
        if status["status"] not in {"running", "wait_expired"} or remaining <= 0:
            return status
        sleep(min(0.025 if observer is not None else 0.1, remaining))


def _profile_path():
    root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "state")
    return root / "XRefKit" / "desktop-api-host.sqlite"


@contextmanager
def _admission():
    """Serialize rollback with Desktop Runtime admission across journals."""
    profile = _profile_path()
    profile.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(profile, timeout=10)) as database, database:
        database.execute("BEGIN IMMEDIATE")
        database.execute(
            "CREATE TABLE IF NOT EXISTS desktop_admission_v1 ("
            "id INTEGER PRIMARY KEY CHECK (id = 1), enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)))"
        )
        yield database


def _set_admission(enabled: bool) -> dict:
    with _admission() as database:
        database.execute(
            "INSERT INTO desktop_admission_v1 VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET enabled = excluded.enabled", (enabled,),
        )
    return {"status": "enabled" if enabled else "rolled_back"}


def main(argv: Sequence[str] | None = None, *, observer=None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    if args_list[:1] == ["desktop-flow"]:
        from .desktop_flow import main as desktop_flow_main

        return desktop_flow_main(args_list[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path)
    parser.add_argument("--turn-id", help="Originating turn ID supplied by the Codex host")
    parser.add_argument("--provider", choices=("stub", "openai"), default="stub")
    parser.add_argument("--wait-seconds", type=float, default=30)
    parser.add_argument("--final-receipt-delay", type=float, default=0, help="Delay receipt delivery for verification")
    parser.add_argument("--defer-presentation", action="store_true",
                        help="Start without claiming a result so the originating host can gate presentation")
    parser.add_argument("--watch-local-stop", action="store_true",
                        help="Observe Stop events in the originating local Codex rollout")
    parser.add_argument("--cancel-openai-on-stop", action="store_true",
                        help="Use background Responses and cancel on matching local Stop")
    parser.add_argument("--pilot-case", choices=PILOT_CASES, help=argparse.SUPPRESS)
    parser.add_argument("--cancel-fixture", action="store_true",
                        help="Use the fixed long output fixture for live Stop verification")
    existing = parser.add_mutually_exclusive_group()
    existing.add_argument("--rollback", action="store_true", help="Block new Desktop Runtime executions")
    existing.add_argument("--enable", action="store_true", help="Explicitly restore Desktop Runtime admission")
    existing.add_argument("--observe", metavar="EXECUTION_ID", help="Check result status without claiming its body")
    existing.add_argument("--await-candidate", metavar="EXECUTION_ID",
                          help="Wait for a late candidate without claiming its body or starting new work")
    existing.add_argument("--reconcile", metavar="EXECUTION_ID", help="Read an existing execution, without starting work")
    existing.add_argument("--recover-result", metavar="EXECUTION_ID",
                          help="Register a private reference to an already claimed result without presenting it")
    existing.add_argument("--origin-closed", metavar="EXECUTION_ID", help="Record closure observed by the trusted host")
    parser.add_argument("--reconcile-seconds", type=float, default=25, help="Bound for --await-candidate")
    parser.epilog = "Use api-host desktop-flow --help for the interactive Desktop workflow."
    args = parser.parse_args(args_list)
    if args.rollback or args.enable:
        if args.journal is not None or args.turn_id is not None:
            parser.error("Desktop admission controls do not take a journal or turn ID")
        try:
            payload = _set_admission(args.enable)
        except (OSError, sqlite3.Error):
            print('{"status":"hold_reconciliation","reason":"desktop_admission_unavailable"}')
            return 2
        print(json.dumps(payload))
        return 0
    if args.journal is None or args.turn_id is None:
        parser.error("--journal and --turn-id are required for execution and observation")
    if not 0 < args.wait_seconds <= 60 or not 0 <= args.final_receipt_delay <= 30:
        parser.error("wait and receipt delay must be within the bounded verification range")
    if not 0 < args.reconcile_seconds <= (120 if args.pilot_case else 60):
        parser.error("reconciliation wait outside host limit")
    thread = os.environ.get("CODEX_THREAD_ID", "").strip()
    turn = args.turn_id.strip()
    if not thread or not turn:
        print('{"status":"initialization_failed","reason":"missing_codex_origin"}', flush=True)
        return 2
    starts_work = all(option is None for option in
                      (args.reconcile, args.recover_result, args.origin_closed, args.observe, args.await_candidate))
    if args.defer_presentation and not starts_work:
        parser.error("--defer-presentation applies only when starting a turn")
    authorization = FOLLOWUP_AUTHORIZATION.get(args.pilot_case)
    if args.pilot_case and starts_work and (
        args.provider != "openai" or not args.watch_local_stop
        or args.cancel_openai_on_stop or args.final_receipt_delay
        or (authorization and os.environ.get(authorization) != "yes")
        or os.environ.get("XREFKIT_PILOT_AUTHORIZED") != "yes"
        or not re.fullmatch(r"proj_[A-Za-z0-9_-]+", os.environ.get("XREFKIT_PILOT_PROJECT", ""))
    ):
        print('{"status":"hold","reason":"pilot_configuration_unconfirmed"}')
        return 2
    if args.cancel_fixture and not args.cancel_openai_on_stop:
        parser.error("--cancel-fixture requires --cancel-openai-on-stop")
    if args.cancel_openai_on_stop and (not args.watch_local_stop or args.provider != "openai"
                                       or args.final_receipt_delay):
        parser.error("provider cancellation requires OpenAI, local Stop watch and no receipt delay")
    rollout = None
    if args.watch_local_stop:
        if not starts_work or not args.defer_presentation:
            parser.error("--watch-local-stop requires a new deferred-presentation turn")
        try:
            if str(UUID(turn)) != turn:
                raise ValueError("invalid Codex turn identity")
            rollout = _local_rollout(thread)
        except (OSError, ValueError):
            print('{"status":"initialization_failed","reason":"local_rollout_unavailable"}', flush=True)
            return 2
    if starts_work and args.provider == "openai" and not os.environ.get("OPENAI_API_KEY", "").strip():
        print('{"status":"initialization_failed","reason":"missing_openai_api_key"}', flush=True)
        return 2
    journal = args.journal.resolve()
    if not starts_work and not journal.is_file():
        print('{"status":"execution_not_found"}', flush=True)
        return 2
    try:
        with ExitStack() as admission, ExitStack() as resources:
            if starts_work:
                try:
                    profile = admission.enter_context(_admission())
                    disabled = profile.execute(
                        "SELECT enabled FROM desktop_admission_v1 WHERE id = 1"
                    ).fetchone() == (0,)
                except (OSError, sqlite3.Error):
                    print('{"status":"hold_reconciliation","reason":"desktop_admission_unavailable"}')
                    return 2
                if disabled:
                    print('{"status":"desktop_disabled"}')
                    return 2
            database = resources.enter_context(closing(sqlite3.connect(journal)))
            store = HostStore(database)
            if args.origin_closed is not None:
                payload = store.close_origin(thread, turn, args.origin_closed)
            elif args.observe is not None:
                payload = store.host_result(thread, turn, args.observe, claim=False)
            elif args.await_candidate is not None:
                payload = _await_candidate(store, thread, turn, args.await_candidate, args.reconcile_seconds, observer)
            elif args.reconcile is not None:
                payload = store.host_result(thread, turn, args.reconcile, claim=True)
            elif args.recover_result is not None:
                payload = store.recover_result(thread, turn, args.recover_result)
            else:
                deadline = monotonic() + args.wait_seconds
                execution, started = store.start_turn(
                    thread, turn, "pilot:" + args.pilot_case if args.pilot_case else args.provider,
                    deadline, args.final_receipt_delay,
                )
                if started:
                    try:
                        if rollout is None:
                            _launch(journal, execution)
                        elif args.pilot_case:
                            _launch(journal, execution, rollout, "pilot:" + args.pilot_case)
                        elif args.cancel_openai_on_stop:
                            _launch(journal, execution, rollout, "fixture" if args.cancel_fixture else "live")
                        else:
                            _launch(journal, execution, rollout)
                    except OSError:
                        store.finish(execution, "hold_reconciliation", None)
                admission.close()
                if started:
                    payload = _wait(store, thread, turn, execution, deadline, claim=not args.defer_presentation, observer=observer)
                else:
                    payload = store.host_result(thread, turn, execution, claim=False)
    except HostProviderMismatch as mismatch:
        print(json.dumps({"status": "provider_mismatch", "existing_provider": mismatch.existing,
                          "requested_provider": mismatch.requested}), flush=True)
        return 2
    except sqlite3.Error:
        print('{"status":"hold_reconciliation","reason":"journal_unavailable"}', flush=True)
        return 2
    print(json.dumps(payload), flush=True)
    if args.recover_result is not None:
        return 0 if payload["status"] == "result_recovered" else 2
    return 0 if payload["status"] in {"candidate", "running", "wait_expired", "origin_closed"} else 2

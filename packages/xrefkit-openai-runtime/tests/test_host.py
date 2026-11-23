import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from threading import Event, Thread
from time import monotonic

from xrefkit_openai_runtime import host, smoke


def test_recover_result_survives_process_crash_and_concurrent_retries(tmp_path, monkeypatch):
    launcher = """
import os, sqlite3, sys
from xrefkit_openai_runtime.host import HostStore, main
from contextlib import closing
mode, journal, execution = sys.argv[1:]
if mode == "before_commit":
    def intercept(action, subject, *args):
        if action == sqlite3.SQLITE_TRANSACTION and subject == "COMMIT":
            os._exit(73)
        return sqlite3.SQLITE_OK
    with closing(sqlite3.connect(journal)) as db:
        store = HostStore(db)
        db.set_authorizer(intercept)
        store.recover_result("thread", "turn", execution)
    raise AssertionError("expected interruption")
if mode == "after_commit":
    with closing(sqlite3.connect(journal)) as db:
        HostStore(db).recover_result("thread", "turn", execution)
        os._exit(74)
raise SystemExit(main(["--journal", journal, "--turn-id", "turn", "--recover-result", execution]))
"""
    monkeypatch.setenv("CODEX_THREAD_ID", "thread")
    package_root = str(Path(host.__file__).resolve().parent.parent)
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(filter(None, (package_root, os.getenv("PYTHONPATH")))))
    for mode, code in (("before_commit", 73), ("after_commit", 74)):
        journal = tmp_path / f"{mode}.sqlite"
        with closing(sqlite3.connect(journal)) as db:
            store = host.HostStore(db)
            execution, _ = store.start_turn("thread", "turn", "stub", monotonic() + 10, 0)
            store.finish(execution, "candidate", "private fixture body")
            assert store.recover_result("thread", "turn", execution)["status"] == "recovery_unavailable"
            assert store.host_result("thread", "turn", execution, claim=True)["result"] == "private fixture body"

        def command(phase):
            return [sys.executable, "-B", "-c", launcher, phase, str(journal), execution]

        failed = subprocess.run(command(mode), capture_output=True, timeout=15)
        assert failed.returncode == code
        assert failed.stdout == b""
        with closing(sqlite3.connect(journal)) as db:
            table_exists = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='host_result_recovery'"
            ).fetchone()
            if mode == "before_commit":
                assert table_exists is None
            else:
                assert db.execute("SELECT execution FROM host_result_recovery").fetchall() == [(execution,)]
        processes = [subprocess.Popen(command("retry"), stdout=subprocess.PIPE) for _ in range(3)]
        for process in processes:
            output, _ = process.communicate(timeout=15)
            assert process.returncode == 0
            assert json.loads(output) == {"execution_id": execution, "status": "result_recovered"}
        with closing(sqlite3.connect(journal)) as db:
            store = host.HostStore(db)
            assert db.execute(
                "SELECT result FROM host_result_recovery JOIN smoke_turn USING (execution)"
            ).fetchall() == [("private fixture body",)]
            assert db.execute("SELECT COUNT(*) FROM host_job").fetchone() == (1,)
            assert store.recover_result("other", "turn", execution)["status"] == "execution_not_found"
            assert store.recover_result("thread", "other", execution)["status"] == "execution_not_found"
            store.close_origin("thread", "turn", execution)
            assert store.recover_result("thread", "turn", execution)["status"] == "origin_closed"


def test_local_abort_watcher_retains_candidate_for_exact_origin(tmp_path):
    journal = tmp_path / "host.sqlite"
    rollout = tmp_path / "rollout.jsonl"
    finished = Event()
    turn = "origin"
    with sqlite3.connect(journal) as database:
        store = host.HostStore(database)
        execution, _ = store.start_turn("thread", turn, "stub", monotonic() + 10, 0)
        other, _ = store.start_turn("thread", "other", "stub", monotonic() + 10, 0)
        store.finish(execution, "candidate", "late result")
        rollout.write_text(
            '{"type":"event_msg","payload":{"type":"turn_aborted","turn_id":"other"}}\n'
            '{"type":"response_item","payload":{"type":"turn_aborted","turn_id":"origin"}}\n'
            '{"type":"event_msg","payload":{"type":"turn_aborted","turn_id":"origin"}}',
            encoding="utf-8",
        )
        watcher = Thread(target=host._watch_abort, args=(
            rollout, journal, execution, "thread", turn, finished,
        ))
        watcher.start()
        try:
            watcher.join(timeout=0.2)
            assert watcher.is_alive()
            assert not store.is_origin_closed(execution)
            with rollout.open("a", encoding="utf-8") as stream:
                stream.write("\n")
            watcher.join(timeout=3)
            assert not watcher.is_alive()
            assert not store.is_origin_closed(other)
            assert store.host_result("thread", turn, execution, claim=True) == {
                "execution_id": execution, "status": "origin_closed", "result_claimed": False,
            }
            assert database.execute("SELECT result FROM smoke_turn WHERE execution=?", (execution,)).fetchone() == (
                "late result",
            )
        finally:
            finished.set()
            watcher.join(timeout=3)


def test_desktop_rollback_holds_new_journals_and_preserves_late_result(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("CODEX_THREAD_ID", "thread")
    journal = tmp_path / "original.sqlite"
    rollout = tmp_path / "rollout.jsonl"
    finished = Event()
    with sqlite3.connect(journal) as database:
        store = host.HostStore(database)
        execution, _ = store.start_turn("thread", "origin", "stub", monotonic() + 10, 0)
        rollout.write_text(
            '{"type":"event_msg","payload":{"type":"turn_aborted","turn_id":"origin"}}\n',
            encoding="utf-8",
        )
        host._watch_abort(rollout, journal, execution, "thread", "origin", finished)
        assert store.is_origin_closed(execution)
        store.finish(execution, "candidate", "late result")

    assert host.main(["--rollback"]) == 0
    assert json.loads(capsys.readouterr().out) == {"status": "rolled_back"}
    blocked = tmp_path / "fresh.sqlite"
    assert host.main(["--journal", str(blocked), "--turn-id", "new"]) == 2
    assert json.loads(capsys.readouterr().out) == {"status": "desktop_disabled"}
    assert not blocked.exists()
    args = ["--journal", str(journal), "--turn-id", "origin"]
    assert host.main([*args, "--observe", execution]) == 0
    assert json.loads(capsys.readouterr().out) == {
        "status": "origin_closed", "execution_id": execution, "result_claimed": False,
    }
    with sqlite3.connect(journal) as database:
        assert database.execute("SELECT result, claimed FROM smoke_turn").fetchall() == [("late result", 0)]
    assert host.main(["--enable"]) == 0
    assert json.loads(capsys.readouterr().out) == {"status": "enabled"}


def test_host_requires_both_origin_identifiers(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    journal = tmp_path / "host.sqlite"
    assert host.main(["--journal", str(journal), "--turn-id", "origin"]) == 2
    assert json.loads(capsys.readouterr().out)["reason"] == "missing_codex_origin"
    assert not journal.exists()


def test_origin_thread_and_turn_scope_the_result_claim():
    with sqlite3.connect(":memory:") as database:
        store = host.HostStore(database)
        start = (monotonic() + 10, 0)
        original, started = store.start_turn("thread-a", "turn-1", "stub", *start)
        assert started
        assert store.start_turn("thread-a", "turn-1", "stub", *start) == (original, False)
        assert store.start_turn("thread-b", "turn-1", "stub", *start)[0] != original
        assert store.start_turn("thread-a", "turn-2", "stub", *start)[0] != original
        assert store.start_worker(original) is not None
        assert store.start_worker(original) is None
        store.finish(original, "candidate", smoke.EXPECTED)
        assert store.host_result("thread-b", "turn-1", original, claim=True)["status"] == "execution_not_found"
        assert store.host_result("thread-a", "turn-2", original, claim=True)["status"] == "execution_not_found"
        assert smoke.TurnStore(database).read("thread-a", original, claim=True)["status"] == "execution_not_found"
        assert store.host_result("thread-a", "turn-1", original, claim=True)["result"] == smoke.EXPECTED
        assert "result" not in store.host_result("thread-a", "turn-1", original, claim=True)


def test_wait_expiry_does_not_claim_a_late_result_and_reconcile_never_launches(
    tmp_path, monkeypatch, capsys,
):
    journal = tmp_path / "host.sqlite"
    monkeypatch.setenv("CODEX_THREAD_ID", "thread")
    with sqlite3.connect(journal) as database:
        store = host.HostStore(database)
        deadline = monotonic() - 1
        execution, _ = store.start_turn("thread", "turn", "stub", deadline, 0)
        assert host._wait(store, "thread", "turn", execution, deadline)["status"] == "wait_expired"
        store.finish(execution, "candidate", smoke.EXPECTED)
        assert "result" not in host._wait(store, "thread", "turn", execution, deadline)

    def unexpected_launch(*_args):
        raise AssertionError("Reconciliation must not launch a worker")

    monkeypatch.setattr(host, "_launch", unexpected_launch)
    args = ["--journal", str(journal), "--turn-id", "turn", "--reconcile", execution]
    assert host.main(args) == 0
    assert json.loads(capsys.readouterr().out)["result"] == smoke.EXPECTED
    assert host.main(args) == 0
    assert "result" not in json.loads(capsys.readouterr().out)


def test_close_during_final_receipt_retains_candidate_without_claim(tmp_path, monkeypatch, capsys):
    journal = tmp_path / "host.sqlite"
    monkeypatch.setenv("CODEX_THREAD_ID", "thread")
    with sqlite3.connect(journal) as database:
        store = host.HostStore(database)
        deadline = monotonic() + 30
        execution, _ = store.start_turn("thread", "turn", "stub", deadline, 0)
        args = ["--journal", str(journal), "--turn-id", "turn"]

        def transport(body, timeout):
            if "tools" not in body:
                assert host.main([*args, "--origin-closed", execution]) == 0
                assert json.loads(capsys.readouterr().out)["status"] == "origin_closed"
            return smoke._stub(body, timeout)

        outcome = smoke._execute(
            store, "thread", "codex-turn:turn", execution, transport, 0, deadline=deadline,
            stop_requested=lambda: store.is_origin_closed(execution),
        )
        assert outcome == smoke.TurnOutcome("candidate", smoke.EXPECTED)
        store.finish(execution, outcome.disposition, outcome.result)
        for arg in ("--reconcile", "--origin-closed"):
            assert host.main([*args, arg, execution]) == 0
            payload = json.loads(capsys.readouterr().out)
            assert payload == {"execution_id": execution, "status": "origin_closed", "result_claimed": False}
        assert database.execute("SELECT result, claimed FROM smoke_turn").fetchone() == (smoke.EXPECTED, 0)


def test_close_while_initial_provider_call_is_in_flight_stops_next_entries():
    with sqlite3.connect(":memory:") as database:
        store = host.HostStore(database)
        deadline = monotonic() + 30
        execution, _ = store.start_turn("thread", "turn", "stub", deadline, 0)

        def transport(body, timeout):
            assert "tools" in body
            assert store.close_origin("another-thread", "turn", execution)["status"] == "execution_not_found"
            assert store.close_origin("thread", "another-turn", execution)["status"] == "execution_not_found"
            assert not store.is_origin_closed(execution)
            assert store.close_origin("thread", "turn", execution)["status"] == "origin_closed"
            return smoke._stub(body, timeout)

        outcome = smoke._execute(
            store, "thread", "codex-turn:turn", execution, transport, 0, deadline=deadline,
            stop_requested=lambda: store.is_origin_closed(execution),
        )
        assert outcome == smoke.TurnOutcome("hold_reconciliation")
        events = [json.loads(event) for event, in database.execute("SELECT event FROM smoke_event")]
        assert sum("dispatch" in event for event in events) == 1
        assert not any(event.get("reason") == "synthetic_runner_entered" for event in events)


def test_host_can_defer_and_observe_before_claiming(tmp_path, monkeypatch, capsys):
    journal = tmp_path / "host.sqlite"
    monkeypatch.setenv("CODEX_THREAD_ID", "thread")
    monkeypatch.setattr(host, "_launch", host._worker)
    args = ["--journal", str(journal), "--turn-id", "turn"]
    assert host.main([*args, "--defer-presentation"]) == 0
    start = json.loads(capsys.readouterr().out)
    execution = start["execution_id"]
    assert start == {"execution_id": execution, "status": "candidate", "result_claimed": False}
    assert host.main([*args, "--observe", execution]) == 0
    assert json.loads(capsys.readouterr().out) == start
    assert host.main([*args, "--reconcile", execution]) == 0
    assert json.loads(capsys.readouterr().out)["result"] == smoke.EXPECTED
    assert host.main([*args, "--observe", execution]) == 0
    assert json.loads(capsys.readouterr().out) == {**start, "result_claimed": True}


def test_new_provider_cannot_reuse_the_same_turn_journal(tmp_path, monkeypatch, capsys):
    journal = tmp_path / "host.sqlite"
    monkeypatch.setenv("CODEX_THREAD_ID", "thread")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setattr(host, "_launch", host._worker)
    args = ["--journal", str(journal), "--turn-id", "turn", "--defer-presentation"]
    assert host.main([*args, "--provider", "stub"]) == 0
    stub = json.loads(capsys.readouterr().out)
    assert stub["status"] == "candidate"

    def unexpected_launch(*_args):
        raise AssertionError("Provider mismatch must be rejected before starting work")

    monkeypatch.setattr(host, "_launch", unexpected_launch)
    assert host.main([*args, "--provider", "openai"]) == 2
    assert json.loads(capsys.readouterr().out) == {
        "status": "provider_mismatch", "existing_provider": "stub", "requested_provider": "openai",
    }
    assert host.main([*args, "--provider", "stub"]) == 0
    assert json.loads(capsys.readouterr().out) == stub
    with sqlite3.connect(journal) as database:
        assert database.execute("SELECT execution, provider FROM host_job").fetchall() == [
            (stub["execution_id"], "stub"),
        ]

    # The same origin can run the second verification in a fresh journal.
    live_journal = tmp_path / "live.sqlite"
    monkeypatch.setattr(host, "_launch", host._worker)
    monkeypatch.setattr(host, "_openai", lambda body, timeout, **_options: smoke._stub(body, timeout))
    assert host.main(["--journal", str(live_journal), "--turn-id", "turn",
                      "--defer-presentation", "--provider", "openai"]) == 0
    live = json.loads(capsys.readouterr().out)
    assert live["status"] == "candidate"
    assert live["execution_id"] != stub["execution_id"]
    with sqlite3.connect(live_journal) as database:
        assert database.execute("SELECT execution, provider FROM host_job").fetchall() == [
            (live["execution_id"], "openai"),
        ]


def test_await_candidate_can_observe_late_completion_without_claim(monkeypatch):
    with sqlite3.connect(":memory:") as database:
        store = host.HostStore(database)
        execution, _ = store.start_turn("thread", "turn", "stub", monotonic() - 1, 0)

        def complete(_seconds):
            store.finish(execution, "candidate", smoke.EXPECTED)

        monkeypatch.setattr(host, "sleep", complete)
        assert host._await_candidate(store, "thread", "turn", execution, 1) == {
            "execution_id": execution, "status": "candidate", "result_claimed": False,
        }
        assert store.host_result("thread", "turn", execution, claim=True)["result"] == smoke.EXPECTED

def test_background_stop_cancels_exact_response_without_saving_payload(monkeypatch):
    from contextlib import closing
    from time import monotonic

    calls = []
    with closing(sqlite3.connect(":memory:")) as database:
        store = host.HostStore(database)
        execution, _ = store.start_turn("thread", "turn", "openai", monotonic() + 5, 0)

        def request(method, path, timeout, body=None):
            calls.append((method, path, body))
            if path == "/v1/responses":
                store.close_origin("thread", "turn", execution)
                return 200, {"status": "queued", "id": "resp_exact"}
            return 200, {"status": "cancelled", "id": "resp_exact", "output": ["private"]}

        monkeypatch.setattr(host, "_background_request", request)
        outcome = host._background_openai(store, execution, {"store": True}, 1, monotonic() + 5)
        assert outcome["status"] == "cancelled"
        assert calls == [
            ("POST", "/v1/responses", {"store": False, "background": True}),
            ("POST", "/v1/responses/resp_exact/cancel", None),
        ]
        assert database.execute(
            "SELECT operation, status, http FROM host_provider_event WHERE execution = ?", (execution,),
        ).fetchall() == [("create", "queued", 200), ("cancel", "cancelled", 200)]


def test_background_stop_does_not_treat_completed_as_cancelled(monkeypatch):
    from contextlib import closing
    from time import monotonic

    import pytest

    with closing(sqlite3.connect(":memory:")) as database:
        store = host.HostStore(database)
        execution, _ = store.start_turn("thread", "turn", "openai", monotonic() + 5, 0)

        def request(method, path, timeout, body=None):
            if path == "/v1/responses":
                store.close_origin("thread", "turn", execution)
                return 200, {"status": "queued", "id": "resp_exact"}
            return 200, {"status": "completed", "id": "resp_exact"}

        monkeypatch.setattr(host, "_background_request", request)
        with pytest.raises(ValueError, match="not confirmed"):
            host._background_openai(store, execution, {}, 1, monotonic() + 5)
        assert database.execute(
            "SELECT status FROM host_provider_event WHERE operation = 'cancel'",
        ).fetchall() == [("completed",)]

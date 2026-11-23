"""Exercise the pilot CLI and detached worker with an in-process fake HTTP boundary."""

from contextlib import closing
import json
import os
import sqlite3
import subprocess
import sys
from time import monotonic, sleep
from uuid import uuid4

import pytest


FAKE = '''
import json
import os
from pathlib import Path
import sys
from time import monotonic, sleep
from xrefkit_openai_runtime import desktop_pilot, host, pilot_reconciliation
pilot_reconciliation.authenticated_owner = lambda: os.environ.get('PILOT_TEST_OWNER', 'S-1-5-21-100')
desktop_pilot.POLL_INTERVAL = 0.25
from xrefkit_openai_runtime.desktop_pilot import EXPECTED, MODEL

fixture = Path(os.environ["PILOT_TEST_ROOT"])
scenario = os.environ["PILOT_TEST_SCENARIO"]
if scenario == "retry_deadline":
    original_execute = desktop_pilot.execute
    def short_execute(store, execution, case, admission, request, deadline):
        return original_execute(store, execution, case, admission, request, min(deadline, monotonic() + 4))
    desktop_pilot.execute = short_execute
worker = os.environ.get("PILOT_TEST_WORKER") == "yes"
if worker:
    assert "OPENAI_API_KEY" not in os.environ

class NetworkDenied(RuntimeError):
    pass

def deny_network(event, _args):
    if event in {"socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr",
                 "socket.connect", "socket.connect_ex", "socket.sendto", "socket.sendmsg"}:
        raise NetworkDenied("pilot test outbound network blocked")

sys.addaudithook(deny_network)
for event in ("socket.getaddrinfo", "socket.connect"):
    try:
        sys.audit(event)
    except NetworkDenied:
        pass
    else:
        raise RuntimeError("outbound network guard was not installed")
with (fixture / "network-guard.jsonl").open("a", encoding="utf-8") as log:
    log.write(json.dumps(["worker" if worker else "cli", scenario]) + "\\n")
if not worker:
    os.environ["OPENAI_API_KEY"] = "mock-placeholder"

def request(method, path, timeout, body, *, project):
    assert project == "proj_fixture"
    with (fixture / "calls.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps([scenario, method, path, body]) + "\\n")
    status = "in_progress"
    if scenario.startswith("reconcile_"):
        assert (method, path) == ("GET", "/v1/responses/resp_fixture")
        return 200, {"id": "resp_fixture", "model": MODEL, "status": "cancelled",
                     "usage": None if scenario == "reconcile_null" else {"input_tokens": 12, "output_tokens": 0}}
    if scenario == "lost_ack" and method == "POST":
        raise TimeoutError("simulated create acknowledgement loss")
    if scenario in {"normal", "unknown", "retry_fast"}:
        status = "completed"
    elif path.endswith("/cancel"):
        assert path == "/v1/responses/resp_fixture/cancel"
        status = "completed" if scenario == "retry_race" else "cancelled"
    elif scenario == "delayed" and method == "GET":
        sleep(1.3)
        status = "completed"
    elif scenario == "mismatch" and method == "GET":
        return 200, {"id": "resp_other", "status": "completed"}
    payload = {"id": "resp_fixture", "status": status, "model": MODEL,
               "output": [{"type": "message", "role": "assistant", "content": [
                   {"type": "output_text", "text": EXPECTED, "annotations": []}]}]}
    if scenario == "cancel_null" and status == "cancelled":
        payload["usage"] = None
    elif scenario != "unknown":
        payload["usage"] = {"input_tokens": 12, "output_tokens": 8}
    return 200, payload
host._background_request = request
if not os.environ.get("PILOT_TEST_WORKER"):
    import subprocess
    original_popen = subprocess.Popen

    def launch(args, *positional, **kwargs):
        if args[1:4] != ["-I", "-B", "-c"]:
            return original_popen(args, *positional, **kwargs)
        args = list(args)
        needle = "from xrefkit_openai_runtime.host import _worker;"
        assert needle in args[4]
        args[4] = args[4].replace(needle, "import runpy, os; runpy.run_path(os.environ['PILOT_TEST_PATCH']); " + needle)
        env = dict(os.environ, PILOT_TEST_WORKER="yes")
        env.pop("OPENAI_API_KEY", None)
        return original_popen(args, *positional, env=env, **kwargs)
    subprocess.Popen = launch
'''


@pytest.fixture
def pilot(tmp_path):
    patch = tmp_path / "pilot_transport.py"
    compile(FAKE, str(patch), "exec")
    patch.write_text(FAKE, encoding="utf-8")
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    thread = str(uuid4())
    rollout = sessions / f"rollout-test-{thread}.jsonl"
    rollout.touch()
    env = dict(os.environ, CODEX_THREAD_ID=thread, CODEX_HOME=str(tmp_path),
               LOCALAPPDATA=str(tmp_path),
               XREFKIT_PILOT_AUTHORIZED="yes", XREFKIT_PILOT_PROJECT="proj_fixture",
               PILOT_TEST_ROOT=str(tmp_path), PILOT_TEST_PATCH=str(patch))
    env.pop("OPENAI_API_KEY", None)
    roots = [root for root in env["PYTHONPATH"].split(os.pathsep) if root]
    bootstrap = (
        "import os, runpy, sys; "
        "sys.path[:0] = " + repr(roots) + "; "
        "runpy.run_path(os.environ['PILOT_TEST_PATCH']); "
        "from xrefkit_openai_runtime.host import main; raise SystemExit(main())"
    )

    def start(case, scenario=None, *, journal_name=None):
        turn = str(uuid4())
        journal = tmp_path / ((journal_name or case) + ".sqlite")
        command = [sys.executable, "-I", "-B", "-c", bootstrap, "desktop-flow",
                   "--journal", str(journal), "--turn-id", turn, "--pilot-case", case,
                   "--wait-seconds", "0.8", "--reconcile-seconds", "12"]
        current = dict(env, PILOT_TEST_SCENARIO=scenario or case)
        line = json.dumps(dict(hostId="local", threadId=thread, turnId=turn, status="inProgress")) + "\n"
        return turn, journal, command, current, line

    return rollout, start


def _calls(root):
    return [json.loads(line) for line in (root / "calls.jsonl").read_text().splitlines()]


def _run(command, env, line):
    result = subprocess.run(command, env=env, input=line, capture_output=True, text=True, timeout=20)
    return result.returncode, list(map(json.loads, result.stdout.splitlines()))


def test_pilot_limits_delayed_cancellation_and_rollback(tmp_path, pilot):
    rollout, start = pilot
    for case in ("normal", "delayed"):
        _, _, command, env, line = start(case)
        code, records = _run(command, env, line * 2)
        assert code == 0, records
        assert [item["result"] for item in records if "result" in item] == ["XREFKIT_PILOT_OK"]
        if case == "delayed":
            assert any(item["status"] == "wait_expired" for item in records)
        assert len({item["execution_id"] for item in records if "execution_id" in item}) == 1

    _, _, command, env, line = start("normal", journal_name="duplicate")
    assert _run(command, env, line)[1][-1]["status"] == "hold_reconciliation"
    turn, journal, command, env, line = start("stop")
    with subprocess.Popen(command, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) as child:
        child.stdin.write(line)
        child.stdin.flush()
        assert json.loads(child.stdout.readline())["status"] == "verify_origin"
        pending = json.loads(child.stdout.readline())
        assert pending["status"] == "wait_expired"
        _, _, other, other_env, other_line = start("stop", journal_name="concurrent")
        assert _run(other, other_env, other_line)[1][-1]["status"] == "hold_reconciliation"
        with rollout.open("a", encoding="utf-8") as out:
            out.write(json.dumps({"type": "event_msg", "payload": {"type": "turn_aborted", "turn_id": turn}}) + "\n")
        child.terminate()
        child.wait(timeout=10)
    code, records = _run([*command, "--resume-and-rollback"], env, "")
    assert code == 0, records
    assert records[-1] == {"status": "rolled_back", "execution_id": pending["execution_id"],
                           "origin_closed": True, "disposition": "cancelled",
                           "result_saved": False, "result_claimed": False}
    _, rejected, command, env, line = start("normal", journal_name="after-rollback")
    assert _run(command, env, line)[1][-1]["status"] == "desktop_disabled"
    assert not rejected.exists()
    calls = _calls(tmp_path)
    guards = [json.loads(line) for line in (tmp_path / "network-guard.jsonl").read_text().splitlines()]
    assert all([role, case] in guards for role in ("cli", "worker") for case in ("normal", "delayed", "stop"))
    creates = [body for _, method, path, body in calls if method == "POST" and path == "/v1/responses"]
    assert len(creates) == 3
    assert all(body["max_output_tokens"] == 512 and len(body["input"].encode()) < 2048
               and body["background"] and not body["store"] and "tools" not in body for body in creates)
    assert [path for _, method, path, _ in calls if method == "POST" and path.endswith("/cancel")] == [
        "/v1/responses/resp_fixture/cancel",
    ]
    with closing(sqlite3.connect(tmp_path / "XRefKit" / "desktop-api-host.sqlite")) as db:
        assert db.execute("SELECT sum(reservation),sum(settled) FROM desktop_pilot_v1").fetchone() == (76800, 3)
    with closing(sqlite3.connect(journal)) as db:
        assert db.execute("SELECT disposition,claimed FROM smoke_turn").fetchall() == [("cancelled", 0)]


@pytest.mark.parametrize("scenario, expected_polls", [("unknown", 0), ("mismatch", 1), ("pending", 12), ("lost_ack", 0)])
def test_pilot_uncertainty_and_poll_cap_hold_new_create(tmp_path, pilot, scenario, expected_polls):
    _, start = pilot
    _, _, command, env, line = start("normal", scenario)
    assert _run(command, env, line)[1][-1]["status"] == "hold_reconciliation"
    _, _, command, env, line = start("delayed")
    assert _run(command, env, line)[1][-1]["status"] == "hold_reconciliation"
    calls = _calls(tmp_path)
    assert sum(method == "POST" for _, method, _, _ in calls) == 1
    assert sum(method == "GET" for _, method, _, _ in calls) == expected_polls


@pytest.mark.parametrize("response_id,basis,http,changes,expected", [
    (None, "unknown", 200, {}, "response_id_unavailable"),
    ("resp_fixture", "cancelled", 404, {}, "retrieve_unavailable"),
    ("resp_fixture", "cancelled", 200, {"id": "resp_other"}, "response_mismatch"),
    ("resp_fixture", "cancelled", 200, {"model": "different"}, "response_mismatch"),
    ("resp_fixture", "cancelled", 200, {"status": "completed"}, "terminal_state_unverified"),
    ("resp_fixture", "in_progress", 200, {"status": "in_progress"}, "terminal_state_unverified"),
    ("resp_fixture", "cancelled", 200, {"usage": None}, "usage_unknown"),
    ("resp_fixture", "cancelled", 200, {"usage": {"input_tokens": 1, "output_tokens": 513}},
     "usage_outside_reservation"),
    ("resp_fixture", "cancelled", 200, {}, "usage_evidence_ready"),
])
def test_inspect_unsettled_response_is_read_only(response_id, basis, http, changes, expected):
    from xrefkit_openai_runtime.desktop_pilot import MODEL, inspect_unsettled_response

    calls = []

    def fake_retrieve(*request):
        calls.append(request)
        return http, {"id": "resp_fixture", "model": MODEL, "status": "cancelled",
                      "usage": {"input_tokens": 12, "output_tokens": 0}, **changes}

    result = inspect_unsettled_response(response_id, basis, fake_retrieve)
    assert result.get("reason", result["status"]) == expected
    assert calls == ([("GET", "/v1/responses/resp_fixture", 5, None)] if response_id else [])
    if expected == "usage_evidence_ready":
        assert result == {"status": "usage_evidence_ready", "provider_status": "cancelled",
                          "input_tokens": 12, "output_tokens": 0}


def test_owner_reconciliation_settles_only_with_exact_usage(tmp_path, pilot):
    rollout, start = pilot
    turn, journal, command, env, line = start("stop", "cancel_null")
    with subprocess.Popen(command, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) as child:
        child.stdin.write(line)
        child.stdin.flush()
        assert json.loads(child.stdout.readline())["status"] == "verify_origin"
        origin = json.loads(child.stdout.readline())
        assert origin["status"] == "wait_expired"
        rollout.write_text(json.dumps({"type": "event_msg", "payload": {
            "type": "turn_aborted", "turn_id": turn,
        }}) + "\n", encoding="utf-8")
        child.terminate()
        child.wait(timeout=10)
    assert _run([*command, "--resume-and-rollback"], env, "")[1][-1]["disposition"] == "hold_reconciliation"

    reconcile = [*command, "--reconcile-usage"]
    calls_before = _calls(tmp_path)
    denied = dict(env, PILOT_TEST_OWNER="S-1-5-21-200", PILOT_TEST_SCENARIO="reconcile_known")
    assert _run(reconcile, denied, "") == (
        2, [{"status": "hold_reconciliation", "reason": "owner_or_binding_unverified"}],
    )
    assert _calls(tmp_path) == calls_before
    null = dict(env, PILOT_TEST_SCENARIO="reconcile_null")
    assert _run(reconcile, null, "") == (2, [{"status": "hold_reconciliation",
                                               "reason": "usage_unknown", "provider_status": "cancelled"}])
    known = dict(env, PILOT_TEST_SCENARIO="reconcile_known")
    assert _run(reconcile, known, "") == (0, [{"status": "usage_settled", "provider_status": "cancelled"}])
    assert _run(reconcile, known, "") == (0, [{"status": "already_settled"}])
    assert [(method, path) for scenario, method, path, _ in _calls(tmp_path) if scenario.startswith("reconcile_")] == [
        ("GET", "/v1/responses/resp_fixture"), ("GET", "/v1/responses/resp_fixture"),
    ]
    with closing(sqlite3.connect(journal)) as db:
        assert db.execute(
            "SELECT outcome,input_tokens,output_tokens FROM desktop_pilot_reconciliation_v1 ORDER BY rowid"
        ).fetchall() == [("lookup_requested", None, None), ("usage_unknown", None, None),
                         ("lookup_requested", None, None), ("usage_evidence_ready", 12, 0)]
    with closing(sqlite3.connect(tmp_path / "XRefKit" / "desktop-api-host.sqlite")) as db:
        assert db.execute("SELECT settled,reservation FROM desktop_pilot_v1").fetchone() == (1, 25600)
        assert db.execute("SELECT enabled FROM desktop_admission_v1").fetchone() == (0,)
        # Recreate the crash boundary: journal evidence durable, settlement not committed.
        with db:
            db.execute("UPDATE desktop_pilot_v1 SET settled=0, reads=12")
    assert _run(reconcile, known, "") == (0, [{"status": "usage_settled", "provider_status": "cancelled"}])
    assert len([call for call in _calls(tmp_path) if call[0].startswith("reconcile_")]) == 2
    with closing(sqlite3.connect(tmp_path / "XRefKit" / "desktop-api-host.sqlite")) as db, db:
        db.execute("ALTER TABLE desktop_pilot_v1 DROP COLUMN reads")
    assert _run(reconcile, known, "") == (
        2, [{"status": "hold_reconciliation", "reason": "lookup_history_unverified"}],
    )
    assert len([call for call in _calls(tmp_path) if call[0].startswith("reconcile_")]) == 2
    _, disabled_journal, fresh, fresh_env, fresh_line = start("normal")
    assert _run(fresh, fresh_env, fresh_line)[1][-1]["status"] == "desktop_disabled"
    assert not disabled_journal.exists()


@pytest.mark.parametrize("case, scenario, disposition", [
    ("stop-retry", "retry_fast", "fixture_completed"),
    ("stop-retry", "retry_pending", "cancelled"),
    ("stop-retry", "retry_race", "fixture_completed"),
    ("stop-retry", "retry_after_reads", "cancelled"),
    ("stop-retry", "retry_deadline", "hold_reconciliation"),
    ("stop-final", "retry_after_reads", "cancelled"),
])
def test_stop_retry_e2e_preserves_ledger_and_target(tmp_path, pilot, case, scenario, disposition):
    rollout, start = pilot
    profile = tmp_path / "XRefKit" / "desktop-api-host.sqlite"
    profile.parent.mkdir()
    with closing(sqlite3.connect(profile)) as db, db:
        db.execute(
            """CREATE TABLE desktop_pilot_v1 (
                scenario TEXT PRIMARY KEY, execution TEXT UNIQUE, reservation INTEGER,
                settled INTEGER, response_id TEXT, status TEXT, input_tokens INTEGER,
                output_tokens INTEGER, reads INTEGER DEFAULT 0)"""
        )
        db.executemany(
            "INSERT INTO desktop_pilot_v1 VALUES(?,?,25600,1,?,'completed',18,8,2)",
            [(prior, prior, "resp_" + prior) for prior in ("normal", "delayed", "stop")],
        )
        if case == "stop-final":
            db.execute(
                "INSERT INTO desktop_pilot_v1 VALUES('stop-retry','prior',20480,1,'resp_prior','incomplete',44,512,12)"
            )
        before = db.execute("SELECT * FROM desktop_pilot_v1 ORDER BY rowid").fetchall()

    turn, journal, command, env, line = start(case, scenario)
    assert _run(command, env, line)[1][-1]["reason"] == "pilot_configuration_unconfirmed"
    assert not journal.exists()
    env["XREFKIT_PILOT_STOP_FINAL_AUTHORIZED" if case == "stop-final" else "XREFKIT_PILOT_STOP_RETRY_AUTHORIZED"] = "yes"
    if case == "stop-final":
        with closing(sqlite3.connect(profile)) as db, db:
            db.execute("UPDATE desktop_pilot_v1 SET settled=0 WHERE scenario='stop-retry'")
        _, _, blocked, blocked_env, blocked_line = start(case, scenario, journal_name="unsettled")
        blocked_env["XREFKIT_PILOT_STOP_FINAL_AUTHORIZED"] = "yes"
        assert _run(blocked, blocked_env, blocked_line)[1][-1]["status"] == "hold_reconciliation"
        assert not (tmp_path / "calls.jsonl").exists()
        with closing(sqlite3.connect(profile)) as db, db:
            db.execute("UPDATE desktop_pilot_v1 SET settled=1 WHERE scenario='stop-retry'")
    if scenario == "retry_deadline":
        _, records = _run(command, env, line)
        assert records[-1]["status"] == disposition
        rollout.write_text(json.dumps({"type": "event_msg", "payload": {
            "type": "turn_aborted", "turn_id": turn,
        }}) + "\n", encoding="utf-8")
        _, records = _run([*command, "--resume-and-rollback"], env, "")
        assert records[-1]["status"] == "rolled_back"
        assert records[-1]["disposition"] == disposition
    elif scenario == "retry_fast":
        _, records = _run(command, env, line)
        assert not any(row["status"] == "stop_ready" or "result" in row for row in records)
        assert records[-1]["status"] == disposition
    else:
        with subprocess.Popen(command, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) as child:
            child.stdin.write(line)
            child.stdin.flush()
            assert json.loads(child.stdout.readline())["status"] == "verify_origin"
            while True:
                raw = child.stdout.readline()
                assert raw, "Stop readiness was never emitted"
                ready = json.loads(raw)
                if ready["status"] == "stop_ready":
                    break
            assert ready["provider_status"] == "in_progress"
            with closing(sqlite3.connect(profile)) as db:
                assert db.execute(
                    "SELECT execution,status FROM desktop_pilot_v1 WHERE scenario=?", (case,),
                ).fetchone() == (ready["execution_id"], "in_progress")
            if scenario == "retry_after_reads":
                deadline = monotonic() + 8
                while sum(call[1] == "GET" for call in _calls(tmp_path)) < 12:
                    assert monotonic() < deadline, "status read limit not reached"
                    sleep(0.05)
                # Allow the final GET to be consumed before emitting the late abort.
                sleep(0.2)
                with closing(sqlite3.connect(journal)) as db:
                    assert db.execute("SELECT disposition FROM smoke_turn").fetchone() == ("running",)
            rollout.write_text(json.dumps({"type": "event_msg", "payload": {
                "type": "turn_aborted", "turn_id": turn,
            }}) + "\n", encoding="utf-8")
            child.terminate()
            child.wait(timeout=10)
        _, records = _run([*command, "--resume-and-rollback"], env, "")
        assert records[-1]["status"] == "rolled_back"
        assert records[-1]["execution_id"] == ready["execution_id"]
        assert records[-1]["disposition"] == disposition
        assert not records[-1]["result_claimed"]

    calls = _calls(tmp_path)
    creates = [body for _, method, path, body in calls if method == "POST" and path == "/v1/responses"]
    assert len(creates) == 1
    assert creates[0]["max_output_tokens"] == 512 and len(creates[0]["input"].encode()) < 1536
    assert "96 numbered lines" in creates[0]["input"]
    cancelled = [path for _, method, path, _ in calls if method == "POST" and path.endswith("/cancel")]
    assert cancelled == ([] if scenario in {"retry_fast", "retry_deadline"} else ["/v1/responses/resp_fixture/cancel"])
    if scenario in {"retry_after_reads", "retry_deadline"}:
        assert sum(method == "GET" for _, method, _, _ in calls) == 12
    with closing(sqlite3.connect(profile)) as db:
        assert db.execute("SELECT * FROM desktop_pilot_v1 WHERE scenario!=? ORDER BY rowid", (case,)).fetchall() == before
        total = 99840 if case == "stop-final" else 97280
        assert db.execute("SELECT sum(reservation) FROM desktop_pilot_v1").fetchone() == (total,)
    with closing(sqlite3.connect(journal)) as db:
        assert db.execute("SELECT disposition,result,claimed FROM smoke_turn").fetchone() == (disposition, None, 0)

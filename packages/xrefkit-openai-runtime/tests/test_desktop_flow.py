"""Exercise one Desktop CLI build from origin verification to terminal outcome."""

import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from time import sleep
from uuid import uuid4

import pytest

from xrefkit_openai_runtime.smoke import EXPECTED


@pytest.mark.parametrize("scenario", ["normal", "expired", "stopped", "stopped_before_presentation"])
def test_desktop_flow(tmp_path, scenario):
    thread, turn = str(uuid4()), str(uuid4())
    env = dict(os.environ, CODEX_THREAD_ID=thread, CODEX_HOME=str(tmp_path), LOCALAPPDATA=str(tmp_path))
    env.pop("OPENAI_API_KEY", None)
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    rollout = sessions / f"rollout-test-{thread}.jsonl"
    rollout.touch()
    journal = tmp_path / "original.sqlite"
    cli = [sys.executable, "-B", "-c", "from xrefkit_openai_runtime.host import main; raise SystemExit(main())"]
    delayed = scenario in {"expired", "stopped"}
    stopped = scenario.startswith("stopped")
    flow = [*cli, "desktop-flow", "--journal", str(journal), "--turn-id", turn,
            "--wait-seconds", "1" if delayed else "3",
            "--final-receipt-delay", "3" if delayed else "0"]
    snapshot = dict(hostId="local", threadId=thread, turnId=turn, status="inProgress")
    answer = json.dumps(snapshot) + "\n"

    if stopped:
        with subprocess.Popen(flow, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              text=True) as worker:
            worker.stdin.write(answer)
            worker.stdin.flush()
            prompt = json.loads(worker.stdout.readline())
            pending = json.loads(worker.stdout.readline())
            assert prompt["status"] == "verify_origin"
            assert pending["status"] == ("wait_expired" if delayed else "candidate")
            if not delayed:
                assert json.loads(worker.stdout.readline())["status"] == "verify_origin"
                worker.terminate()
                worker.wait(timeout=10)
                # Let the settled worker's watcher exit before publishing the event.
                sleep(0.3)
                with closing(sqlite3.connect(journal)) as db:
                    assert db.execute("SELECT disposition,claimed FROM smoke_turn").fetchone() == ("candidate", 0)
                    assert db.execute("SELECT count(*) FROM host_closed_turn").fetchone() == (0,)
                rollout.write_text(json.dumps({"type": "event_msg", "payload": {
                    "type": "turn_aborted", "turn_id": str(uuid4()),
                }}) + "\n", encoding="utf-8")
                unrelated = subprocess.run([*flow, "--resume-and-rollback", "--reconcile-seconds", "0.2"],
                                           env=env, capture_output=True, text=True, timeout=10)
                assert unrelated.returncode == 2
                assert json.loads(unrelated.stdout)["status"] == "hold_reconciliation"
            rollout.write_text(json.dumps({"type": "event_msg", "payload": {
                "type": "turn_aborted", "turn_id": turn,
            }}) + "\n", encoding="utf-8")
            if delayed:
                worker.terminate()
                worker.wait(timeout=10)
        resumed = subprocess.run([*flow, "--resume-and-rollback"], env=env,
                                 capture_output=True, text=True, timeout=45, check=True)
        result = json.loads(resumed.stdout)
        assert result == {"status": "rolled_back", "execution_id": pending["execution_id"],
                          "origin_closed": True, "disposition": "candidate",
                          "result_saved": True, "result_claimed": False}
        blocked = tmp_path / "blocked.sqlite"
        denial = subprocess.run([*cli, "--journal", str(blocked), "--turn-id", str(uuid4())],
                                env=env, capture_output=True, text=True, timeout=10)
        assert denial.returncode == 2
        assert json.loads(denial.stdout) == {"status": "desktop_disabled"}
        assert not blocked.exists()
    else:
        run = subprocess.run(flow, input=answer * 2, env=env, capture_output=True,
                             text=True, timeout=45, check=True)
        records = list(map(json.loads, run.stdout.splitlines()))
        assert [item["status"] for item in records] == (
            ["verify_origin", "candidate", "verify_origin", "candidate"] if scenario == "normal"
            else ["verify_origin", "wait_expired", "candidate", "verify_origin", "candidate"]
        )
        assert [item["result"] for item in records if "result" in item] == [EXPECTED]
        assert len({item["execution_id"] for item in records if "execution_id" in item}) == 1
        replay = subprocess.run(flow, input=answer, env=env, capture_output=True,
                                text=True, timeout=10, check=True)
        assert all("result" not in item for item in map(json.loads, replay.stdout.splitlines()))

    with closing(sqlite3.connect(journal)) as db:
        assert db.execute("SELECT disposition,result,claimed FROM smoke_turn").fetchall() == [
            ("candidate", EXPECTED, int(not stopped)),
        ]
        events = [json.loads(event) for event, in db.execute("SELECT event FROM smoke_event")]
        assert sum("dispatch" in event for event in events) == 2
        if delayed:
            assert sum(event.get("reason") == "matched_late_receipt" for event in events) == 1

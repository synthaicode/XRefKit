import json
import sqlite3

from xrefkit_openai_runtime import smoke


def _run(transport=None, clock=lambda: 0):
    with sqlite3.connect(":memory:") as database:
        store = smoke.TurnStore(database)
        execution, started = store.start("thread", "invocation")
        assert started
        return smoke._execute(
            store, "thread", "invocation", execution, transport or smoke._stub, 10, clock,
        )


def test_stub_uses_real_controller_for_single_tool_round_trip():
    observed = []

    def transport(body, timeout):
        observed.append(body)
        return smoke._stub(body, timeout)

    assert _run(transport) == smoke.TurnOutcome("candidate", smoke.EXPECTED)
    initial, continuation = observed
    assert initial["instructions"] == continuation["instructions"]
    assert continuation["input"][-1]["call_id"] == continuation["input"][-2]["call_id"]
    assert not initial["store"] and not continuation["store"]


def test_wait_expiry_blocks_new_tool_and_accepts_correlated_final_receipt():
    for expire_on, expected in ((1, "hold_reconciliation"), (2, "candidate")):
        now = 0
        count = 0

        def transport(body, timeout):
            nonlocal now, count
            count += 1
            if count == expire_on:
                now = 11
            return smoke._stub(body, timeout)

        assert _run(transport, lambda: now).disposition == expected
        assert count == expire_on


def test_missing_origin_never_initializes_or_sends(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
    journal = tmp_path / "turns.sqlite"
    assert smoke.main(["--journal", str(journal)]) == 2
    assert json.loads(capsys.readouterr().out)["reason"] == "missing_codex_thread_id"
    assert not journal.exists()


def test_result_claim_is_scoped_and_only_once():
    with sqlite3.connect(":memory:") as database:
        store = smoke.TurnStore(database)
        execution, started = store.start("thread", "invocation")
        assert started
        assert store.start("thread", "invocation") == (execution, False)
        assert store.start("thread", "another")[0] != execution
        assert store.start("other-thread", "invocation")[0] != execution
        store.finish(execution, "candidate", smoke.EXPECTED)
        assert store.read("other-thread", execution, claim=True)["status"] == "execution_not_found"
        assert store.read("thread", execution, claim=True)["result"] == smoke.EXPECTED
        assert "result" not in store.read("thread", execution, claim=True)

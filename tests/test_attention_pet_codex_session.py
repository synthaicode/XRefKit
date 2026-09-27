"""The live adapter observes one chat without persisting its message text."""
import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from xrefkit.attention_pet.codex_session import CodexSessionSource, find_rollout
from xrefkit.attention_pet.server import make_server
from xrefkit.attention_pet.store import Store


THREAD = "01a0dd3a-aead-7352-a2c4-10e36ffa84dc"


def append(path, timestamp, payload_type, payload):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"timestamp": timestamp, "type": payload_type,
                                 "payload": payload}, ensure_ascii=False) + "\n")


def user(path, timestamp, message_id, request):
    append(path, timestamp, "response_item", {"type": "message", "role": "user", "id": message_id,
           "content": [{"type": "input_text", "text":
                        "<in-app-browser-context>ambient text</in-app-browser-context>\n"
                        "## My request:\n" + request}]})


def test_one_bound_chat_updates_incrementally_without_saving_text(tmp_path):
    home = tmp_path / ".codex"
    log_dir = home / "sessions" / "2026" / "09" / "26"
    log_dir.mkdir(parents=True)
    log = log_dir / f"rollout-{THREAD}.jsonl"
    append(log, "2026-09-26T12:00:00Z", "turn_context", {"model": "gpt-6-sol", "effort": "medium"})
    user(log, "2026-09-26T12:00:00.5Z", "msg-startup", "# AGENTS.md instructions for a repository")
    user(log, "2026-09-26T12:00:01Z", "msg-first", "最初の依頼")
    source = CodexSessionSource(find_rollout(THREAD, home), THREAD)
    saved = tmp_path / "projected.json"
    store = Store(saved)
    source.sync(store)
    first = store.view()
    assert source.selection() == ("sol", "standard")
    assert source.status()["observedUserTurns"] == 1
    assert first["state"]["coverage"] == "partial"
    assert len(first["workingSet"]["items"]) == 1
    assert "最初の依頼" not in saved.read_text(encoding="utf-8")
    source.sync(store)
    assert store.view() == first
    user(log, "2026-09-26T12:00:02Z", "msg-second", "この修正は不要")
    source.sync(store)
    second = store.view()
    assert second["state"]["observedAt"] > first["state"]["observedAt"]
    assert second["state"]["features"]["active_items"] == 2
    assert second["state"]["features"]["dependency_edges"] == 1
    assert second["state"]["trajectoryEvidence"] == []
    assert "この修正は不要" not in saved.read_text(encoding="utf-8")
    append(log, "2026-09-26T12:00:03Z", "turn_context", {"model": "gpt-6-terra", "effort": "low"})
    source.sync(store)
    assert source.selection() == ("terra", "light")
    assert store.view() == second
    append(log, "2026-09-26T12:00:04Z", "turn_context", {"model": "unrecognized-model", "effort": "medium"})
    source.sync(store)
    assert source.selection() == ("", "standard")
    assert store.view() == second


def test_live_api_defaults_to_observed_model_allows_comparison_and_rejects_mutation(tmp_path):
    log = tmp_path / f"rollout-{THREAD}.jsonl"
    append(log, "2026-09-26T12:00:00Z", "turn_context", {"model": "gpt-6-sol", "effort": "medium"})
    user(log, "2026-09-26T12:00:01Z", "msg-first", "作業を確認する")
    source = CodexSessionSource(log, THREAD)
    store = Store(tmp_path / "projected.json")
    server, launch = make_server(store, source=source)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base, token = launch.rstrip("/"), server.write_token
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with urlopen(Request(base + "/api/state?model=astra&reasoning=high"), timeout=5) as response:
            value = json.load(response)
        assert value["source"]["mode"] == "codex-chat"
        assert value["source"]["observedUserTurns"] == 1
        assert value["source"]["profile"] == "sol"
        assert value["source"]["reasoning"] == "standard"
        assert value["fit"]["selected"]["model"] == "astra"
        assert value["fit"]["selected"]["reasoning"] == "high"
        with urlopen(Request(base + "/api/state?model=&reasoning=standard"), timeout=5) as response:
            defaulted = json.load(response)
        assert defaulted["fit"]["selected"]["model"] == "sol"
        before = store.view()
        req = Request(base + "/api/snapshot", b"{}", {**headers, "Content-Type": "application/json"})
        try:
            urlopen(req, timeout=5)
            assert False, "manual mutation should be blocked"
        except HTTPError as error:
            assert error.code == 409
        assert store.view() == before
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

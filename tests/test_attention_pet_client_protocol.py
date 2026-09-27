"""Same-host client protocol and session switching."""

import json
import subprocess
import sys
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from xrefkit.attention_pet.client_protocol import ClientStateSource, PROTOCOL_VERSION
from xrefkit.attention_pet.client_protocol import ClientState
from xrefkit.attention_pet.client import AttentionPetClient, ClientProtocolError
from xrefkit.attention_pet.evaluator import Weights
from xrefkit.attention_pet.server import make_server
from xrefkit.attention_pet.store import Store


def payload(session: str, revision: int, item_count: int = 1) -> dict:
    observed = float(100 + revision)
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "provider": "codex-desktop",
        "clientInstanceId": "window-1",
        "sessionId": session,
        "activationRevision": revision,
        "observedAt": observed,
        "model": "gpt-6-sol",
        "reasoning": "medium",
        "capabilities": {
            "activeSessionChanged": True,
            "promptSubmitted": True,
            "modelSelected": True,
            "fullConversationAccess": False,
        },
        "workingSet": {
            "schemaVersion": 1,
            "taskId": "task-" + session,
            "contextId": session,
            "observedAt": observed,
            "coverage": "partial",
            "items": [
                {"id": f"item-{index}", "kind": "goal", "text": "structured item",
                 "source": f"event-{index}"}
                for index in range(item_count)
            ],
            "dependencies": [],
            "observations": [],
        },
    }


def test_handshake_authentication_and_active_session_switching(tmp_path):
    source = ClientStateSource(tmp_path / "sessions", Weights())
    server, launch = make_server(Store(), source=source)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = launch.rstrip("/")
    auth = {"Authorization": f"Bearer {server.write_token}"}

    def get(path, headers=None):
        with urlopen(Request(base + path, headers=headers or {}), timeout=5) as response:
            return json.load(response)

    def post(path, value):
        request = Request(base + path, json.dumps(value).encode(),
                          {**auth, "Content-Type": "application/json"})
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    try:
        with pytest.raises(HTTPError) as error:
            get("/api/client/handshake")
        assert error.value.code == 401
        hello = get("/api/client/handshake", auth)
        assert hello == {
            "service": "xrefkit-attention-pet",
            "protocolVersion": PROTOCOL_VERSION,
            "instanceId": server.instance_id,
            "capabilities": ["active-session", "working-set-snapshot"],
            "writeAuthentication": "bearer",
            "hostScope": "loopback",
        }

        accepted = post("/api/active-session", payload("session-a", 1, 1))
        assert accepted["accepted"] is True
        assert accepted["instanceId"] == server.instance_id
        assert post("/api/active-session", payload("session-a", 1, 1)) == accepted
        first = get("/api/state")
        assert first["source"]["sessionId"] == "session-a"
        assert first["source"]["activationRevision"] == 1
        assert first["source"]["profile"] == "sol"
        assert first["state"]["features"]["active_items"] == 1
        english = get("/api/state?lang=en")
        assert english["fit"]["presentation"]["headline"].startswith("For the work currently visible")
        assert english["fit"]["presentation"]["coverageLabel"] == "Partial"

        with pytest.raises(HTTPError) as error:
            get("/api/state?lang=fr")
        assert error.value.code == 400

        post("/api/active-session", payload("session-b", 2, 2))
        second = get("/api/state")
        assert second["source"]["sessionId"] == "session-b"
        assert second["state"]["features"]["active_items"] == 2

        with pytest.raises(HTTPError) as error:
            post("/api/active-session", payload("session-a", 1, 1))
        assert error.value.code == 409
        assert get("/api/state")["source"]["sessionId"] == "session-b"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_client_contract_rejects_mismatched_session_and_manual_mode(tmp_path):
    source = ClientStateSource(tmp_path / "sessions", Weights())
    server, launch = make_server(Store(), source=source)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = launch.rstrip("/")
    auth = {"Authorization": f"Bearer {server.write_token}", "Content-Type": "application/json"}
    try:
        invalid = payload("session-a", 1)
        invalid["workingSet"]["contextId"] = "different"
        request = Request(base + "/api/active-session", json.dumps(invalid).encode(), auth)
        with pytest.raises(HTTPError) as error:
            urlopen(request, timeout=5)
        assert error.value.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_provider_client_verifies_loopback_identity_and_acknowledgement(tmp_path):
    source = ClientStateSource(tmp_path / "sessions", Weights())
    server, launch = make_server(Store(), source=source)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = AttentionPetClient(launch, server.write_token,
                                    instance_id=server.instance_id)
        assert client.handshake()["service"] == "xrefkit-attention-pet"
        state = ClientState.model_validate(payload("session-client", 3))
        assert client.activate(state)["activeSessionId"] == "session-client"

        with pytest.raises(ClientProtocolError, match="instance"):
            AttentionPetClient(launch, server.write_token,
                               instance_id="different").handshake()
        with pytest.raises(ClientProtocolError, match="request failed"):
            AttentionPetClient(launch, "wrong-token").handshake()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    for invalid in ["https://127.0.0.1:8769", "http://example.com:8769",
                    "http://127.0.0.1", "http://127.0.0.1:8769/?token=value"]:
        with pytest.raises(ValueError, match="127.0.0.1"):
            AttentionPetClient(invalid, "token")

    manual, manual_launch = make_server(Store())
    thread = threading.Thread(target=manual.serve_forever, daemon=True)
    thread.start()
    try:
        request = Request(manual_launch.rstrip("/") + "/api/active-session",
                          json.dumps(payload("session-a", 1)).encode(),
                          {"Authorization": f"Bearer {manual.write_token}",
                           "Content-Type": "application/json"})
        with pytest.raises(HTTPError) as error:
            urlopen(request, timeout=5)
        assert error.value.code == 409
    finally:
        manual.shutdown()
        manual.server_close()
        thread.join(timeout=5)


def test_client_schema_and_launch_record_are_machine_readable(tmp_path):
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "projects/attention-pet/schema/client-state.schema.json").read_text(encoding="utf-8"))
    assert schema == ClientState.model_json_schema()
    packaged = json.loads((root / "xrefkit/resources/attention_pet/client-state.schema.json").read_text(encoding="utf-8"))
    assert packaged == schema

    process = subprocess.Popen(
        [sys.executable, "-m", "xrefkit.attention_pet", "serve", "--client",
         "--port", "0", "--session", str(tmp_path / "sessions")],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding="utf-8",
    )
    try:
        launch = json.loads(process.stdout.readline())
        assert launch["service"] == "xrefkit-attention-pet"
        assert launch["protocolVersion"] == PROTOCOL_VERSION
        assert launch["endpoint"].startswith("http://127.0.0.1:")
        assert launch["writeToken"]
        client = AttentionPetClient(launch["endpoint"], launch["writeToken"],
                                    instance_id=launch["instanceId"])
        assert client.handshake()["instanceId"] == launch["instanceId"]
    finally:
        process.terminate()
        process.wait(timeout=10)

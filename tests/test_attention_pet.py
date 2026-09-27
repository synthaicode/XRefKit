import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from pydantic import ValidationError

from xrefkit.attention_pet.evaluator import Weights, evaluate
from xrefkit.attention_pet.model import Conversation, Edge, Item, WorkingSet, extract
from xrefkit.attention_pet.scenarios import scenario
from xrefkit.attention_pet.server import make_server
from xrefkit.attention_pet.store import Store


def fixture(name="A", step=1):
    return WorkingSet.model_validate(scenario(name, step)["workingSet"])


def test_scenario_a_independent_requests_grow_gradually():
    scores = [evaluate(fixture("A", s))["ral"] for s in range(1, 6)]
    assert scores == sorted(scores)
    assert max(b - a for a, b in zip(scores, scores[1:])) < 10


def test_scenario_b_relationships_cost_more_than_independent_items():
    a, b = evaluate(fixture("A", 5)), evaluate(fixture("B", 5))
    assert a["features"]["active_items"] == b["features"]["active_items"]
    assert b["ral"] > a["ral"] + 20
    assert b["features"]["dependency_edges"] > 0


def test_scenario_c_low_load_can_have_wrong_trajectory():
    states = [evaluate(fixture("C", s)) for s in range(1, 4)]
    assert len({s["ral"] for s in states}) == 1
    assert states[-1]["ral"] < 40
    assert states[-1]["trajectoryStability"] < states[0]["trajectoryStability"]
    assert states[-1]["state"] == "WRONG TRAJECTORY"
    assert states[-1]["expression"] == "wrong_trajectory"
    assert "restart" in states[-1]["recommendedActions"]


def test_scenario_d_summary_lowers_load_without_erasing_constraints():
    store = Store()
    before = store.submit(fixture("D"))
    result = store.recover("summarize", before["state"]["observedAt"])
    assert before["state"]["ral"] >= 75
    assert result["state"]["ral"] < before["state"]["ral"]
    assert result["state"]["deltaRal"] < 0
    assert result["state"]["features"]["constraint"] == before["state"]["features"]["constraint"]
    assert result["state"]["features"]["dependency_edges"] == before["state"]["features"]["dependency_edges"]
    assert len(result["workingSet"]["items"]) == len(before["workingSet"]["items"])


def test_scenario_e_restart_requires_fresh_validation_to_recover():
    store = Store()
    before = store.submit(fixture("E", 3))
    handoff = store.recover("restart", before["state"]["observedAt"])
    assert handoff["state"] == before["state"]  # Download is not a context restart.
    fresh = fixture("E", 4)
    fresh.observations = [o for o in fresh.observations if o.context != fresh.contextId]
    unknown = store.submit(fresh)
    assert unknown["state"]["trajectoryStability"] is None
    recovered = store.submit(fixture("E", 5))
    assert recovered["state"]["trajectoryStability"] > before["state"]["trajectoryStability"]
    assert recovered["state"]["ral"] == before["state"]["ral"]


def test_trend_uses_time_window_and_reports_feature_deltas():
    store = Store()
    a = store.submit(fixture("B", 1))
    b = store.submit(fixture("B", 4))
    assert b["state"]["deltaRal"] == b["state"]["ral"] - a["state"]["ral"]
    assert b["state"]["trend"] == "rapid_rise"
    assert {c["feature"] for c in b["state"]["changes"]} >= {"constraint", "dependency_edges"}
    ws = fixture("B", 5)
    ws.observedAt = 2000.0
    assert store.submit(ws)["state"]["trend"] != "rapid_rise"


def test_unknown_trajectory_does_not_override_load_and_task_switch_does_not_compare():
    ws = fixture()
    ws.observations = []
    assert evaluate(ws)["state"] == "UNKNOWN"
    assert evaluate(ws)["expression"] == "stable"
    store = Store()
    store.submit(ws)
    assert store.submit(fixture("B"))["state"]["deltaRal"] is None


@pytest.mark.parametrize("coverage", ["partial", "reviewed"])
@pytest.mark.parametrize("step,expression", [(1,"stable"),(3,"loaded"),(5,"strained")])
def test_structural_load_remains_visible_without_trajectory(coverage, step, expression):
    ws = fixture("B", step)
    ws.coverage = coverage
    ws.observations = []
    state = evaluate(ws)
    assert state["trajectoryStability"] is None
    assert state["state"] == "UNKNOWN"
    assert state["expression"] == expression


def test_fix_retains_relations_and_does_not_fake_lower_load():
    store = Store()
    before = store.submit(fixture("B", 3))
    fixed = store.recover("fix", before["state"]["observedAt"])
    assert fixed["state"]["ral"] == before["state"]["ral"]
    assert all(i["fixed"] for i in fixed["workingSet"]["items"] if i["kind"] == "decision")


def test_summary_preserves_history_referenced_by_active_items():
    ws = fixture("D")
    ws.dependencies.append(Edge(source="d0", target="h0-0", evidence="needed evidence"))
    store = Store()
    store.submit(ws)
    result = store.recover("summarize", ws.observedAt)
    assert next(i for i in result["workingSet"]["items"] if i["id"] == "h0-0")["status"] == "active"


@pytest.mark.parametrize("action", ["split", "externalize", "resolve", "rebase", "restart"])
def test_handoff_actions_do_not_claim_to_change_live_context(action):
    store = Store()
    before = store.submit(fixture())
    result = store.recover(action, before["state"]["observedAt"])
    assert result["recovery"]["effect"] == "handoff_created"
    assert result["recovery"]["handoff"]["workingSet"] == before["workingSet"]
    assert result["state"] == before["state"]


@pytest.mark.parametrize("mutation", [
    lambda d: d.update(unexpected="field"),
    lambda d: d.update(observedAt=float("nan")),
    lambda d: d.update(items=d["items"] * 2),
    lambda d: d.update(dependencies=[{"source":"absent","target":"d0","evidence":"bad"}]),
    lambda d: d["items"][0].update(depth=-1),
    lambda d: d["items"][0].update(fixed="true"),
])
def test_invalid_boundary_data_is_rejected(mutation):
    data = fixture().model_dump()
    mutation(data)
    with pytest.raises(ValidationError):
        WorkingSet.model_validate(data)


def test_timestamp_replay_and_stale_recovery():
    store = Store()
    ws = fixture()
    first = store.submit(ws)
    assert store.submit(ws) == first
    stale = ws.model_copy(deep=True)
    stale.observedAt = 1.0
    with pytest.raises(ValueError, match="timestamps"):
        store.submit(stale)
    with pytest.raises(ValueError, match="refresh"):
        store.recover("fix", 1.0)


def test_extract_upserts_status_and_marks_unannotated_turn_partial():
    data = scenario("A")["conversation"]
    updated = dict(data["turns"][0]["items"][0], status="done")
    data["turns"].append({"id":"update", "text":"Requirement complete", "items":[updated]})
    ws = extract(Conversation.model_validate(data))
    assert len(ws.items) == 5 and ws.items[0].status == "done"
    data["turns"].append({"id":"unannotated", "text":"A new unknown requirement"})
    assert extract(Conversation.model_validate(data)).coverage == "partial"
    data["turns"][0]["items"][0]["source"] = "missing"
    with pytest.raises(ValueError, match="supplied turn"):
        extract(Conversation.model_validate(data))


def test_persistence_restart_and_failed_write_do_not_mutate_state(tmp_path, monkeypatch):
    from pathlib import Path
    path = tmp_path / "session.json"
    store = Store(path)
    store.submit(fixture("B", 1))
    before = store.submit(fixture("B", 2))
    assert Store(path).view() == before
    def fail(*args):
        raise OSError("disk full")
    monkeypatch.setattr(Path, "replace", fail)
    with pytest.raises(OSError):
        store.submit(fixture("B", 3))
    assert store.view() == before


def test_weights_validation():
    with pytest.raises(ValueError):
        Weights(working_set=-1)
    with pytest.raises(ValueError):
        Weights(working_set=float("nan"))


def test_high_load_alone_never_recommends_restart():
    state = evaluate(fixture("D"))
    assert state["ral"] >= 75 and state["state"] == "HIGH LOAD"
    assert "restart" not in state["recommendedActions"]


@pytest.mark.parametrize("count,band", [(1,"stable"),(16,"loaded"),(24,"strained"),(30,"high_pressure"),(36,"unstable")])
def test_five_visual_bands_and_critical_override(count, band):
    ws = fixture()
    ws.items = [Item(id=f"g-{i}", kind="goal", text="goal", source="test") for i in range(count)]
    weights = Weights(working_set=100, dependency_complexity=0, constraint_density=0,
                      decision_depth=0, conflict_pressure=0, context_dispersion=0)
    assert evaluate(ws, weights=weights)["expression"] == band
    ws.observations = fixture("C", 3).observations
    result = evaluate(ws, weights=weights)
    assert result["state"] == ("CRITICAL" if count >= 30 else "WRONG TRAJECTORY")


def test_empty_partial_snapshot_stays_unknown_and_bounds_hold():
    ws = WorkingSet(taskId="empty",contextId="c",observedAt=1.0,items=[])
    result = evaluate(ws)
    assert result["ral"] == 0 and result["trajectoryStability"] is None
    assert result["state"] == "UNKNOWN"


def test_http_api_auth_origin_validation_recovery_and_assets():
    server, launch = make_server(Store())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base, token = launch.rstrip("/"), server.write_token
    def request(path, data=None, auth=True, origin=None):
        headers = {"Authorization":f"Bearer {token}"} if auth else {}
        if origin:
            headers["Origin"] = origin
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = Request(base + path, json.dumps(data).encode() if data is not None else None, headers)
        with urlopen(req, timeout=5) as response:
            return response.read()
    try:
        assert b"Attention Pet" in request("/", auth=False)
        for path in ("/pet.js", "/pet.css"):
            assert request(path, auth=False)
        assert json.loads(request("/api/state", auth=False))["state"] is None
        with pytest.raises(HTTPError) as error:
            request("/api/snapshot", fixture().model_dump(), auth=False)
        assert error.value.code == 401
        with pytest.raises(HTTPError) as error:
            request("/api/snapshot", fixture().model_dump(), origin="https://example.com")
        assert error.value.code == 403
        with pytest.raises(HTTPError) as error:
            request("/api/snapshot", {"ral":99})
        assert error.value.code == 400
        before = json.loads(request("/api/conversation", scenario("D")["conversation"]))
        after = json.loads(request("/api/recover", {"action":"summarize", "expectedObservedAt":before["state"]["observedAt"]}))
        assert after["state"]["ral"] < before["state"]["ral"]
        assert json.loads(request("/api/state"))["state"] == after["state"]
        with pytest.raises(HTTPError) as error:
            request("/api/demo", {"scenario":"C", "step":3})
        assert error.value.code == 404
        assert json.loads(request("/api/state"))["state"] == after["state"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

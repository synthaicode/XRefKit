"""Fit checks verify the experimental rules, not real model performance."""
import copy
import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from pydantic import ValidationError

from xrefkit.attention_pet.evaluator import evaluate, evaluate_fit, fit_candidate
from xrefkit.attention_pet.model import Capability, ModelProfile, WorkingSet
from xrefkit.attention_pet.profiles import DEPTHS, PROFILES
from xrefkit.attention_pet.scenarios import scenario
from xrefkit.attention_pet.server import make_server
from xrefkit.attention_pet.store import Store


def task(name="A", step=5):
    return WorkingSet.model_validate(scenario(name, step)["workingSet"])


@pytest.mark.parametrize("name,step,expected", [
    ("A", 5, ["Sufficient"] * 4),
    ("B", 3, ["Underpowered", "Sufficient", "Sufficient", "Sufficient"]),
    ("B", 5, ["Underpowered", "Underpowered", "Underpowered", "Sufficient"]),
    ("D", 5, ["Underpowered"] * 4),
])
def test_fit_is_task_dependent_not_monotonic_quality(name, step, expected):
    state = evaluate(task(name, step))
    assert [evaluate_fit(state, m)["modelFit"] for m in PROFILES] == expected


def test_behavior_changes_expansion_independently_of_capability():
    state = evaluate(task("B", 3))
    profile = PROFILES["sol"].model_copy(deep=True)
    normal = fit_candidate(state, profile, DEPTHS["standard"])
    profile.behavior.exploration = 1
    exploring = fit_candidate(state, profile, DEPTHS["standard"])
    assert exploring.expansion > normal.expansion
    assert exploring.capability == normal.capability
    profile.behavior.compression = 1
    assert fit_candidate(state, profile, DEPTHS["standard"]).expansion < exploring.expansion


def test_one_missing_capability_cannot_be_offset_by_other_axes():
    profile = PROFILES["astra"].model_copy(deep=True)
    profile.capability = Capability(reasoning=100, constraint_tracking=100, evidence_handling=0)
    result = fit_candidate(evaluate(task()), profile, DEPTHS["standard"])
    assert result.shortfalls == ["evidence_handling"]
    assert not result.meetsRequirements


def test_depth_changes_capability_exploration_and_cost():
    state = evaluate(task("B", 3))
    standard = fit_candidate(state, PROFILES["sol"], DEPTHS["standard"])
    deep = fit_candidate(state, PROFILES["sol"], DEPTHS["high"])
    assert deep.capability.reasoning > standard.capability.reasoning
    assert deep.effectiveRal > standard.effectiveRal
    assert deep.relativeInferenceCost > standard.relativeInferenceCost
    # A large task can still exceed a stronger profile with deeper reasoning.
    assert evaluate_fit(evaluate(task("D")), "astra", "high")["modelFit"] == "Underpowered"


def test_comparison_is_pure_and_total_cost_is_unknown():
    state = evaluate(task("B", 3))
    before = copy.deepcopy(state)
    results = [evaluate_fit(state, m) for m in PROFILES]
    assert state == before
    assert {r["baseRal"] for r in results} == {state["ral"]}
    for result in results:
        assert result["expectedTotalCost"] is None
        assert all(result[k] is None for k in ("inferenceCost", "retryCost", "correctionCost", "failureRiskCost"))
        assert result["calibration"] == "uncalibrated"
    assert results[0]["costFit"] == "RetryRisk"
    assert results[1]["costFit"] == "NoLowerCostCandidate"
    assert results[2]["costFit"] == "LowerCostCandidateAvailable"


def test_missing_selection_or_structure_is_unknown_and_partial_is_disclosed():
    assert evaluate_fit(None, "sol")["modelFit"] == "Unknown"
    assert evaluate_fit(evaluate(task()))["modelFit"] == "Unknown"
    empty = WorkingSet(taskId="empty", contextId="c", observedAt=1.0, items=[])
    assert evaluate_fit(evaluate(empty), "sol")["modelFit"] == "Unknown"
    partial = task()
    partial.coverage = "partial"
    fit = evaluate_fit(evaluate(partial), "luna")
    assert fit["modelFit"] == "Sufficient"
    assert fit["coverage"] == "partial"
    assert fit["evaluationConfidence"] == "Unknown"
    assert any("入力は作業の一部" in r for r in evaluate_fit(evaluate(partial), "luna")["reasons"])


def test_failure_evidence_flags_cost_without_inventing_model_causality():
    result = evaluate_fit(evaluate(task("C", 3)), "luna")
    assert result["modelFit"] == "Sufficient"
    assert result["costFit"] == "ReviewNeeded"
    assert result["presentation"]["petState"] == "Review"
    assert result["expectedTotalCost"] is None


def test_review_presentation_keeps_underpowered_model_fit_visible():
    state = evaluate(task("B", 5))
    state["trajectoryEvidence"] = evaluate(task("C", 3))["trajectoryEvidence"]
    fit = evaluate_fit(state, "luna")
    assert fit["modelFit"] == "Underpowered"
    assert fit["costFit"] == "ReviewNeeded"
    assert fit["presentation"]["petState"] == "Review"
    assert "Underpowered" in fit["presentation"]["modelFitLabel"]
    assert fit["presentation"]["modelGuideStatus"] == "HoldForReview"


def test_schema_matches_python_cost_fit_contract():
    from pathlib import Path
    from xrefkit.attention_pet.model import FitEvaluation
    schema = json.loads((Path(__file__).resolve().parents[1] /
                         "projects/attention-pet/schema/fit.schema.json").read_text(encoding="utf-8"))
    assert schema == FitEvaluation.model_json_schema()
    assert schema["properties"]["costFit"]["enum"] == [
        "RetryRisk", "NoLowerCostCandidate", "LowerCostCandidateAvailable", "ReviewNeeded", "Unknown"]


@pytest.mark.parametrize("name,step,costs,faces", [
    ("A", 5, ["NoLowerCostCandidate"] + ["LowerCostCandidateAvailable"] * 3, ["Balanced"] + ["Relaxed"] * 3),
    ("B", 3, ["RetryRisk", "NoLowerCostCandidate", "LowerCostCandidateAvailable", "LowerCostCandidateAvailable"], ["Strained", "Balanced", "Relaxed", "Relaxed"]),
    ("B", 5, ["RetryRisk"] * 3 + ["NoLowerCostCandidate"], ["Strained"] * 3 + ["Balanced"]),
    ("D", 5, ["RetryRisk"] * 4, ["Strained"] * 4),
    ("C", 3, ["ReviewNeeded"] * 4, ["Review"] * 4),
])
def test_scenarios_separate_cost_and_presentation(name, step, costs, faces):
    state = evaluate(task(name, step))
    fits = [evaluate_fit(state, m) for m in PROFILES]
    assert [f["costFit"] for f in fits] == costs
    assert [f["presentation"]["petState"] for f in fits] == faces
    for fit in fits:
        assert fit["modelFit"] in {"Unknown", "Underpowered", "Sufficient"}
        for candidate in fit["lowerCostCandidates"]:
            assert candidate["meetsRequirements"]
            assert candidate["relativeInferenceCost"] < fit["inferenceCostIndex"]


def test_other_prices_do_not_change_model_fit(monkeypatch):
    state = evaluate(task())
    before = evaluate_fit(state, "astra")
    assert before["costFit"] == "LowerCostCandidateAvailable"
    for name in ("luna", "terra", "sol"):
        monkeypatch.setitem(PROFILES, name, PROFILES[name].model_copy(update={"relative_inference_cost": 100.0}))
    after = evaluate_fit(state, "astra")
    assert before["modelFit"] == after["modelFit"] == "Sufficient"
    assert after["costFit"] == "NoLowerCostCandidate"
    assert after["lowerCostCandidates"] == []


@pytest.mark.parametrize("name,step,model,status,target", [
    ("A", 5, "astra", "Available", "Luna"),
    ("B", 3, "astra", "Available", "Terra"),
    ("B", 3, "sol", "Available", "Terra"),
    ("B", 3, "terra", "NoLowerCandidate", None),
    ("B", 3, "luna", "Underpowered", None),
    ("C", 3, "astra", "HoldForReview", None),
    ("D", 5, "astra", "Underpowered", None),
])
def test_lowest_sufficient_downgrade_guidance(name, step, model, status, target):
    state = evaluate(task(name, step))
    fit = evaluate_fit(state, model)
    guide = fit["presentation"]
    assert guide["modelGuideStatus"] == status
    if target:
        assert f"低コスト比較候補: {target}" in guide["modelGuide"]
        assert target in guide["modelGuideShort"]
        assert "同じ考える深さ" in guide["modelGuide"]
        assert "再試行・修正時間・失敗損失を含む総コストは未比較" in guide["modelGuideDetail"]
        assert "仮の必要能力3軸を満たす試算" in guide["modelGuideDetail"]
        lowest = min(fit["lowerCostCandidates"], key=lambda c: c["relativeInferenceCost"])
        assert lowest["model"].capitalize() == target
        assert lowest["meetsRequirements"]
    elif status == "NoLowerCandidate":
        assert "低コスト比較候補なし" in guide["modelGuideShort"]
    else:
        assert guide["modelGuideShort"] == ""
    assert fit["expectedTotalCost"] is None


def test_downgrade_guidance_preserves_unknown_and_partial_scope():
    assert evaluate_fit(None, "astra")["presentation"]["modelGuideStatus"] == "Unknown"
    partial = task("A", 5)
    partial.coverage = "partial"
    fit = evaluate_fit(evaluate(partial), "astra")
    assert fit["presentation"]["modelGuideStatus"] == "Available"
    assert "一部の作業" in fit["presentation"]["modelGuideDetail"]


@pytest.mark.parametrize("model_fit,cost_fit,expected", [
    ("Unknown", "Unknown", "Unknown"),
    ("Underpowered", "RetryRisk", "Strained"),
    ("Sufficient", "NoLowerCostCandidate", "Balanced"),
    ("Sufficient", "LowerCostCandidateAvailable", "Relaxed"),
    ("Unknown", "ReviewNeeded", "Review"),
    ("Underpowered", "ReviewNeeded", "Review"),
    ("Sufficient", "ReviewNeeded", "Review"),
])
def test_presentation_priority(model_fit, cost_fit, expected):
    from xrefkit.attention_pet.presentation import present_fit
    assert present_fit(model_fit, cost_fit).petState == expected


def test_ui_drops_old_evaluation_after_network_failure():
    import subprocess
    from pathlib import Path
    view = Store().submit(task("B", 3))
    view["fit"] = evaluate_fit(view["state"], "sol")
    result = subprocess.run(["node", "tests/attention_pet_ui_check.cjs"],
                            input=json.dumps(view), text=True, capture_output=True,
                            cwd=Path(__file__).resolve().parents[1], timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr


def test_ui_uses_browser_language_for_api_and_dynamic_text():
    import os
    import subprocess
    from pathlib import Path
    view = Store().submit(task("B", 3))
    view["fit"] = evaluate_fit(view["state"], "sol", locale="en")
    environment = {**os.environ, "ATTENTION_PET_TEST_LANG": "en-US"}
    result = subprocess.run(["node", "tests/attention_pet_ui_check.cjs"],
                            input=json.dumps(view), text=True, capture_output=True,
                            cwd=Path(__file__).resolve().parents[1], timeout=15,
                            env=environment)
    assert result.returncode == 0, result.stdout + result.stderr


def test_english_presentation_preserves_evaluation_meaning():
    fit = evaluate_fit(evaluate(task("B", 3)), "luna", locale="en")
    assert fit["modelFit"] == "Underpowered"
    assert fit["presentation"]["petState"] == "Strained"
    assert "capability" in fit["presentation"]["headline"].lower()
    assert all("実験値" not in reason for reason in fit["reasons"])


@pytest.mark.parametrize("model,cost,pet,headline,summary", [
    ("Unknown", "Unknown", "Unknown", "まだ評価できません", "情報が不足"),
    ("Underpowered", "RetryRisk", "Strained", "能力が不足する可能性", "一部を満たしていません"),
    ("Sufficient", "NoLowerCostCandidate", "Balanced", "必要な能力を満たす試算", "候補は確認されていません"),
    ("Sufficient", "LowerCostCandidateAvailable", "Relaxed", "より低い推論コストの候補", "現在のモデルでも必要能力を満たす試算"),
    ("Sufficient", "ReviewNeeded", "Review", "実際の結果", "モデル能力だけを原因とは判断していません"),
    ("Underpowered", "ReviewNeeded", "Review", "実際の結果", "モデル能力だけを原因とは判断していません"),
])
@pytest.mark.parametrize("coverage,confidence", [("partial", "Unknown"), ("reviewed", "Unknown"), ("reviewed", "Low"), ("reviewed", "High")])
def test_presentation_semantics_and_scope(model, cost, pet, headline, summary, coverage, confidence):
    from xrefkit.attention_pet.presentation import present_fit
    result = present_fit(model, cost, coverage, confidence)
    assert result == present_fit(model, cost, coverage, confidence)
    assert result.petState == pet
    assert headline in result.headline
    assert summary in result.summary
    assert confidence in result.confidenceLabel
    if coverage == "partial":
        assert result.scopeNote == "一部の作業のみ評価"
        assert "一部の作業だけ" in result.summary
        if pet != "Unknown":
            assert result.headline.startswith("現在確認できている範囲では")
    elif confidence in {"Unknown", "Low"} and pet != "Unknown":
        assert result.headline.startswith("現在の入力範囲では")
    for forbidden in ("最適", "最安", "ちょうどいい", "過剰", "無駄", "高性能すぎ"):
        assert forbidden not in result.headline + result.shortMessage
    if cost == "NoLowerCostCandidate":
        assert "低コスト適合候補なし" in result.costFitLabel


@pytest.mark.parametrize(("model", "cost", "coverage", "short"), [
    ("Underpowered", "RetryRisk", "partial", "一部の作業では能力不足の可能性"),
    ("Underpowered", "RetryRisk", "reviewed", "能力不足の可能性があります"),
    ("Sufficient", "NoLowerCostCandidate", "partial", "一部の作業では必要能力を満たす試算"),
    ("Sufficient", "NoLowerCostCandidate", "reviewed", "必要能力を満たす試算です"),
    ("Sufficient", "LowerCostCandidateAvailable", "partial", "一部の作業で低コスト比較候補あり"),
    ("Sufficient", "LowerCostCandidateAvailable", "reviewed", "低コスト比較候補があります"),
    ("Sufficient", "ReviewNeeded", "partial", "実結果の確認が必要です"),
    ("Unknown", "Unknown", "partial", "まだ評価できません"),
])
def test_short_message_compresses_the_same_state_as_headline(model, cost, coverage, short):
    from xrefkit.attention_pet.presentation import present_fit

    result = present_fit(model, cost, coverage)
    assert result.shortMessage == short
    if coverage == "partial" and result.petState not in {"Unknown", "Review"}:
        assert "現在確認できている範囲では" in result.headline
        assert "一部の作業" in result.shortMessage
    assert "低コスト比較候補は案内しません" not in result.modelGuide


@pytest.mark.parametrize(("model", "cost", "action"), [
    ("Underpowered", "RetryRisk", "必要能力を満たす候補や、作業の分割・整理を比較してください。"),
    ("Sufficient", "NoLowerCostCandidate", "現在の設定で進めるか、実際の結果を確認してください。"),
    ("Sufficient", "LowerCostCandidateAvailable", "低コスト比較候補の条件を確認してください。"),
    ("Sufficient", "ReviewNeeded", "失敗・修正・再試行の記録を確認してください。"),
    ("Unknown", "Unknown", "作業内容とモデル選択を確認してください。"),
])
def test_action_hint_uses_a_human_next_step(model, cost, action):
    from xrefkit.attention_pet.presentation import present_fit

    assert present_fit(model, cost, "partial").actionHint == action


@pytest.mark.parametrize("field,value", [("relative_inference_cost", -1), ("relative_inference_cost", float("inf"))])
def test_profiles_reject_invalid_costs(field, value):
    data = PROFILES["luna"].model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        ModelProfile.model_validate(data)


def test_api_model_selection_is_read_only_and_invalid_queries_cannot_mutate():
    store = Store()
    before = store.submit(task("B", 3))
    server, launch = make_server(store)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base, token = launch.rstrip("/"), server.write_token

    def request(path, data=None):
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"} if data is not None else {}
        req = Request(base + path, json.dumps(data).encode() if data is not None else None, headers)
        with urlopen(req, timeout=5) as response:
            return json.load(response)

    try:
        for model, expected in zip(PROFILES, ["Underpowered", "Sufficient", "Sufficient", "Sufficient"], strict=True):
            value = request(f"/api/state?model={model}&reasoning=standard")
            assert value["fit"]["modelFit"] == expected
            assert value["state"] == before["state"]
        for query in ["model=absent", "model=luna&model=astra", "reasoning=absent", "unexpected=true"]:
            with pytest.raises(HTTPError) as error:
                request("/api/recover?" + query, {"action": "fix", "expectedObservedAt": before["state"]["observedAt"]})
            assert error.value.code == 400
        assert store.view() == before
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

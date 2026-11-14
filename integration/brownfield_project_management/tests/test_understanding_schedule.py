"""Installed producer -> receiver -> immutable schedule history, no source imports."""
from copy import deepcopy
import json

import pytest

from xrefkit_skills_brownfield import package_root
from xrefkit_skills_brownfield.understanding import analyze_understanding, save_analysis
from xrefkit_skills_project_management.schedule import (
    ScheduleError, assess_impact, calculate, compare_plans, read_history, save,
    validate_impact_notification,
)


def understanding():
    return json.loads((package_root()/"examples/understanding-r001.json").read_text(encoding="utf-8"))


def task(identity, days, predecessors=(), requirement="ABCDEF123456"):
    return {"id": identity, "label": identity, "duration": days,
            "depends_on": [{"task": p, "type": "FS", "lag": 0} for p in predecessors],
            "requirement_xids": [requirement], "evidence_refs": [], "decision_refs": [],
            "hold_refs": [], "work_ref": "work/"+identity}


def plan(kind="execution"):
    return {"schema_version": 1, "plan_id": "migration", "kind": kind, "start": "2026-11-16",
            "calendar": {"working_weekdays": [0,1,2,3,4], "holidays": []}, "rules_ref": "rules/r1",
            "tasks": [task("migrate", 2), task("verify", 1, ["migrate"], "111111111111")]}


def metadata(reason="initial"):
    return {"created_at": "2026-11-14T00:00:00Z", "reason": reason,
            "requirement_xids": ["ABCDEF123456"], "evidence_refs": ["evidence/r1"],
            "decision_refs": ["decision/r1"], "judgment": "owner-selected plan",
            "approval": {"status": "approved", "actor": "project-owner", "record_ref": "approval/r1"}}


def test_producer_contract_and_direct_dependent_impact_without_mutation():
    previous = understanding()
    current = deepcopy(previous)
    current.update(revision=2, reason="Migration inventory changed")
    current["requirements"][0].update(text="Preserve image metadata too", reason="Inventory found metadata")
    notice = analyze_understanding(current, previous)["notification"]
    assert validate_impact_notification(notice) == notice
    original = plan()
    frozen = deepcopy(original)
    impact = assess_impact(original, notice)
    assert impact["direct_tasks"] == ["migrate"]
    assert impact["dependent_tasks"] == ["verify"]
    assert impact["schedule_changed"] is False and impact["readiness"] == "not_evaluated"
    assert impact["decision_activities"][0]["status"] == "proposed"
    assert impact["holds"][0]["status"] == "open"
    assert original == frozen


def test_technical_revision_replan_preserves_old_baseline_and_separate_decision(tmp_path):
    previous = understanding()
    current = deepcopy(previous)
    current.update(revision=2, reason="Measured migration needs longer")
    current["approach"][0].update(text="Increase migration window", reason="PoC result", evidence_refs=["poc/2"])
    analysis_path = save_analysis(tmp_path/"technical", current, previous)
    notice = json.loads(analysis_path.read_text(encoding="utf-8"))["analysis"]["notification"]
    before = plan()
    baseline = save(tmp_path/"plans", before, metadata(), baseline=True)
    frozen = (tmp_path/"plans"/baseline["source"]).read_bytes()
    impact = assess_impact(before, notice)
    assert impact["direct_tasks"] == ["migrate"]
    # The test supplies an explicit owner-approved new estimate; the producer
    # never derives duration from prose or changes an existing authorized plan.
    after = deepcopy(before)
    after["tasks"][0]["duration"] = 5
    after["tasks"][0]["hold_refs"] = [hold["id"] for hold in impact["holds"]]
    revised_metadata = metadata(notice["reason"])
    revised_metadata["evidence_refs"] = notice["evidence_refs"]
    revised_metadata["decision_refs"] = ["decision/2"]
    revised_metadata["approval"]["record_ref"] = "approval/2"
    revision = save(tmp_path/"plans", after, revised_metadata)
    assert (tmp_path/"plans"/baseline["source"]).read_bytes() == frozen
    assert revision["revision"] == 2
    assert calculate(after)["duration"] - calculate(before)["duration"] == 3
    diff = compare_plans(before, after)
    assert diff["finish_delta_calendar_days"] == 5
    assert diff["task_changes"]["migrate"]["duration"] == [2, 5]
    activity = impact["decision_activities"][0]
    decision = plan("decision")
    investigation = task(activity["id"], 1)
    investigation["label"] = activity["question"]
    investigation["work_ref"] = str(analysis_path) + "#" + activity["knowledge_requirement_id"]
    investigation["requirement_xids"] = activity["requirement_xids"]
    investigation["evidence_refs"] = activity["evidence_refs"]
    investigation["decision_refs"] = [activity["decision_ref"]]
    decision["tasks"] = [investigation, task("decide", 0, [activity["id"]])]
    decision_record = save(tmp_path/"plans", decision, metadata("new method investigation"))
    assert decision_record["revision"] == 1
    assert "decision" in decision_record["source"] and "execution" in revision["source"]
    history = read_history(tmp_path/"plans")
    assert history["baselines"]["execution/migration"] == [baseline["source"]]
    assert history["approved"]["execution/migration"] == revision["source"]
    assert history["current"]["execution/migration"] == revision["source"]
    assert revision["previous"] == baseline["source"]
    assert revision["reason"] == notice["reason"]
    assert revision["evidence_refs"] == notice["evidence_refs"]
    saved = json.loads((tmp_path/"plans"/decision_record["source"]).read_text(encoding="utf-8"))
    assert saved["plan"]["tasks"][0]["id"] == activity["id"]
    assert saved["plan"]["tasks"][0]["decision_refs"] == [activity["decision_ref"]]
    assert activity["knowledge_requirement_id"] in saved["plan"]["tasks"][0]["work_ref"]


@pytest.mark.parametrize("mutate", [
    lambda n: n.update(schema="brownfield.change_impact/v999"),
    lambda n: n.update(source_revision=True),
    lambda n: n.update(previous_revision=1),
    lambda n: n["decision_activities"][0].update(status="approved"),
    lambda n: n["holds"][0].update(status="resolved"),
    lambda n: n.update(requirement_xids=["REQ-1"]),
    lambda n: n.update(automatic_schedule_update=True),
])
def test_receiver_rejects_invalid_or_authority_escalating_notifications(mutate):
    notice = analyze_understanding(understanding())["notification"]
    mutate(notice)
    with pytest.raises(ScheduleError):
        assess_impact(plan(), notice)


def test_removed_requirement_keeps_impact_and_unmapped_tasks_explicit():
    before = understanding()
    before["requirements"][0]["affected_task_ids"].append("external-work")
    after = deepcopy(before)
    after.update(revision=2, reason="Explicit scope withdrawal")
    for key in ("requirements", "confirmations", "approach", "artifacts", "knowledge_requirements"):
        after[key] = []
    notice = analyze_understanding(after, before)["notification"]
    impact = assess_impact(plan(), notice)
    assert impact["direct_tasks"] == ["migrate"]
    assert impact["unmapped_task_ids"] == ["external-work"]
    assert all(change["kind"] == "removed" for change in notice["changes"])


def test_unchanged_open_knowledge_still_hands_off_impact():
    previous = understanding()
    current = deepcopy(previous)
    current["revision"] = 2
    notice = analyze_understanding(current, previous)["notification"]
    assert notice["changes"] == []
    impact = assess_impact(plan(), notice)
    assert impact["direct_tasks"] == ["migrate"]
    assert impact["dependent_tasks"] == ["verify"]
    assert impact["holds"][0]["id"] == "knowledge-migration-speed"
    assert impact["readiness"] == "not_evaluated"

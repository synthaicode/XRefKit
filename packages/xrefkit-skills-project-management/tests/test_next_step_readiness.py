import pytest

from xrefkit_skills_project_management.next_step_readiness import ReadinessInput, evaluate, report_lines


def task(id, deps=()):
    return {"id": id, "label": id, "work_ref": "work/" + id, "duration": 1,
            "depends_on": [{"task": dep, "type": "FS", "lag": 0} for dep in deps],
            "requirement_xids": [], "evidence_refs": [], "decision_refs": [], "hold_refs": []}


def records():
    tasks = [task("design"), task("build", ("design",)), task("planning", ("design",)), task("test", ("build",))]
    source = {"schema_version": 1, "current_task": "design", "plan_ref": "schedule", "snapshot_ref": "snapshot",
              "sources": {"schedule": "project", "snapshot": "project", "policy": "project", "trial": "synthetic"},
              "plan": {"schema_version": 1, "plan_id": "Plan", "kind": "execution", "start": "2026-11-16",
                       "calendar": {"working_weekdays": [0, 1, 2, 3, 4], "holidays": []},
                       "rules_ref": "policy", "tasks": tasks},
              "snapshot": {"as_of": "2026-11-17", "tasks": {t["id"]: {"actual_start": None, "actual_finish": None,
                           "remaining": 1, "evidence_refs": []} for t in tasks}},
              "start_contracts": {"build": "policy", "planning": "policy"},
              "conditions": [condition(id, id + "-auth", authority=True, result="SATISFIED")
                             for id in ("build", "planning")]}
    source["snapshot"]["tasks"]["design"] = {"actual_start": "2026-11-16", "actual_finish": "2026-11-17",
                                             "remaining": 0, "evidence_refs": ["done"]}
    return source


def condition(task_id, id="check", **overrides):
    return {"id": id, "task": task_id, "requirement": id, "phase": "pre_start", "blocks_start": True,
            "result": "UNKNOWN", "basis": "current record", "source": "policy", **overrides}


def assess(payload):
    return evaluate(ReadinessInput.model_validate(payload))


@pytest.mark.parametrize(("condition_fields", "status"), [
    ({}, "PENDING_VERIFICATION"),
    ({"result": "UNSATISFIED"}, "NOT_READY"),
    ({"unknown_reason": "human_decision"}, "PENDING_DECISION"),
    ({"result": "SATISFIED"}, "READY"),
    ({"result": "NOT_APPLICABLE"}, "READY"),
])
def test_concurrent_successors_are_independent(condition_fields, status):
    data = records()
    data["conditions"].append(condition("build", **condition_fields))
    result = assess(data)
    assert {s["task"]: s["status"] for s in result["steps"]} == {"build": status, "planning": "READY"}
    assert ("人間に判断してほしいこと" in "\n".join(report_lines(result))) == (status == "PENDING_DECISION")


def test_undefined_and_declaration_gaps():
    missing_plan = assess({"schema_version": 1, "current_task": "candidate"})
    assert missing_plan["status"] == "UNDEFINED" and missing_plan["proposals"]
    data = records()
    data["current_task"] = "test"
    assert assess(data)["status"] == "UNDEFINED"
    data["current_task"] = "design"
    data["plan"]["tasks"][1]["hold_refs"] = ["not-read"]
    build = assess(data)["steps"][0]
    assert build["status"] == "UNDEFINED" and build["missing_refs"] == ["not-read"]


def test_acceptance_check_only_blocks_when_declared_and_cycles_are_detected():
    data = records()
    acceptance = condition("build", phase="acceptance", blocks_start=False, needs_tasks=["test"],
                           unknown_reason="post_implementation_verification")
    data["conditions"].append(acceptance)
    result = assess(data)
    assert result["steps"][0]["status"] == "READY"
    assert "この工程の着手条件外／実装後の受入" in "\n".join(report_lines(result))
    acceptance["blocks_start"] = True
    result = assess(data)
    assert result["steps"][0]["status"] == "NOT_READY"
    assert set(result["steps"][0]["cycle"]) == {"build", "test"}
    assert result["steps"][1]["status"] == "READY"


def test_groups_actions_waiting_unknowns_and_synthetic_cannot_authorize():
    data = records()
    group = {"id": "collect", "work": "collect log", "artifact": "log", "completion": "verified run"}
    data["conditions"].extend([
        condition("build", "one", waiting_source="policy", source="policy", result="SATISFIED", action=group),
        condition("build", "two", source="trial", result="SATISFIED", action=group),
        condition("planning", "three", source="trial", unknown_reason="human_decision", waiting_source="trial",
                  action={**group, "id": "trial", "owner": "mock-owner", "due": "2026-11-22"}),
    ])
    result = assess(data)
    action = next(a for a in result["actions"] if a["id"] == "collect")
    assert action["conditions"] == ["one", "two"] and action["owner"] is None
    assert [step["status"] for step in result["steps"]] == ["PENDING_VERIFICATION", "PENDING_VERIFICATION"]
    prose = "\n".join(report_lines(result))
    assert prose.count("引継ぎ先の対応待ち") == 1 and "担当を決める" in prose
    assert "試験結果のみ" in prose and "人間に判断してほしいこと" not in prose
    assert "mock-owner" not in prose and "2026-11-22" not in prose


def test_gate_disagreement_and_schedule_reuse():
    data = records()
    data["gates"] = {"build": {"result": "denied", "source": "policy"}}
    result = assess(data)
    assert result["steps"][0]["status"] == "READY" and result["steps"][0]["gate_disagreement"]
    assert "実行は保留" in "\n".join(report_lines(result))
    data["plan"]["tasks"][1]["depends_on"][0]["lag"] = 1
    assert assess(data)["steps"][0]["status"] == "NOT_READY"
    data["sources"]["snapshot"] = "synthetic"
    assert assess(data)["steps"][0]["status"] == "PENDING_VERIFICATION"


def test_report_uses_scoped_readiness_from_existing_render_path():
    from test_human_report import facts, render

    data = facts()
    value = records()
    data["evidence"].update({key: {"label": key, "link": "#" + key, "kind": "evidence",
                                  "method": "synthetic" if source == "synthetic" else "design"}
                             for key, source in value["sources"].items()})
    data["readiness"] = value
    output = render(data)
    assert output.index("**現在") < output.index("**次のStep**") < output.index("**誰が何をするか**")
    assert "着手条件が成立" in output and "[schedule](<#schedule>)" in output
    data["evidence"]["snapshot"]["method"] = "synthetic"
    with pytest.raises(ValueError, match="actual project readiness"):
        render(data)

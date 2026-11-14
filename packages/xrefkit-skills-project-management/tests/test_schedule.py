"""Scheduling behavior exercised with small independently calculable networks."""
import copy
import json
from importlib.metadata import version

import pytest

# Core runs this source suite against historical public distributions too.
# Older releases have no scheduler; they retain the compatibility test suite.
if version("xrefkit-skills-project-management") not in ("0.1.0a1", "0.1.0a2"):
    from xrefkit_skills_project_management.schedule import (
        ScheduleError, calculate, compare, compare_plans, mermaid, read_history, save,
    )

    def task(tid, duration, predecessors=()):
        return {"id":tid, "label":tid, "duration":duration,
                "depends_on":[{"task":p,"type":"FS","lag":0} for p in predecessors],
                "requirement_xids":["ABCDEF123456"], "evidence_refs":[], "decision_refs":[], "hold_refs":[], "work_ref":f"work/{tid}"}

    def plan():
        return {"schema_version":1,"plan_id":"P1","kind":"execution","start":"2026-11-16",
                "calendar":{"working_weekdays":[0,1,2,3,4],"holidays":[]},"rules_ref":"rules/r1",
                "tasks":[task("a",2),task("b",4,["a"]),task("c",1,["a"]),task("d",2,["b","c"])]}

    def metadata():
        return {"created_at":"2026-11-14T00:00:00Z","reason":"initial plan","requirement_xids":["ABCDEF123456"],
                "evidence_refs":["evidence/1"],"decision_refs":["decision/1"],"judgment":"proposed duration estimate",
                "approval":{"status":"proposed","actor":None,"record_ref":None}}

    def test_diamond_cpm_and_deterministic_order():
        p=plan(); result=calculate(p)
        assert result["duration"]==8 and result["finish"]=="2026-11-26"
        assert result["critical_tasks"]==["a","b","d"]
        assert result["critical_edges"]==[["a","b"],["b","d"]]
        assert {r["id"]:r["total_float"] for r in result["tasks"]}=={"a":0,"b":0,"c":3,"d":0}
        p["tasks"].reverse()
        assert calculate(p)==result

    def test_multiple_critical_paths_milestone_and_disconnected_work():
        p=plan(); p["tasks"][2]["duration"]=4
        p["tasks"] += [task("end",0,["d"]),task("parallel",1)]
        result=calculate(p)
        assert result["critical_tasks"]==["a","b","c","d","end"]
        assert ["c","d"] in result["critical_edges"]
        assert next(r for r in result["tasks"] if r["id"]=="parallel")["total_float"]==7

    def test_calendar_lag_release_and_mermaid_match_dates():
        p=plan(); p["calendar"]["holidays"]=["2026-11-18"]
        p["tasks"][1]["depends_on"][0]["lag"]=1
        p["tasks"][2]["not_before"]="2026-11-26"
        result=calculate(p)
        assert result["finish"]=="2026-12-01"
        chart=mermaid(p,result)
        assert "2026-12-01" in chart and "excludes" not in chart

    @pytest.mark.parametrize("mutation",[
        lambda p:p["tasks"][0]["depends_on"].append({"task":"d","type":"FS","lag":0}),
        lambda p:p["tasks"][0]["depends_on"].append({"task":"other-plan","type":"FS","lag":0}),
        lambda p:p["tasks"][0].update(duration=-1),
        lambda p:p["tasks"][0].update(duration=True),
        lambda p:p["tasks"][1]["depends_on"][0].update(type="SS"),
        lambda p:p["tasks"].append(copy.deepcopy(p["tasks"][0])),
        lambda p:p["calendar"].update(working_weekdays=[]),
        lambda p:p.update(resource_capacity=2),
        lambda p:p.update(plan_id="../escape"),
    ])
    def test_invalid_and_unsupported_inputs_refused(mutation):
        p=plan();mutation(p)
        with pytest.raises(ScheduleError):calculate(p)

    def test_remaining_forecast_does_not_modify_plan_or_baseline(tmp_path):
        p=plan(); original=copy.deepcopy(p); m=metadata()
        m["approval"]={"status":"approved","actor":"owner","record_ref":"approval/1"}
        baseline=save(tmp_path,p,m,baseline=True)
        before=(tmp_path/baseline["source"]).read_bytes()
        snapshot={"as_of":"2026-11-20","tasks":{
            "a":{"actual_start":"2026-11-16","actual_finish":"2026-11-18","remaining":0,"evidence_refs":["actual/a"]},
            "b":{"actual_start":"2026-11-18","actual_finish":None,"remaining":5,"evidence_refs":["actual/b"]},
            "c":{"actual_start":"2026-11-18","actual_finish":"2026-11-19","remaining":0,"evidence_refs":["actual/c"]},
            "d":{"actual_start":None,"actual_finish":None,"remaining":2,"evidence_refs":[]}}}
        forecast=calculate(p,snapshot)
        assert forecast["finish"]=="2026-12-01" and forecast["critical_tasks"]==["b","d"]
        assert compare(calculate(p),forecast)["finish_delta_calendar_days"]==5
        chart=mermaid(p,forecast)
        assert "section Actual observations" in chart and "section Remaining forecast" in chart
        assert "a observed :done, a0, 2026-11-16, 2026-11-18" in chart
        assert "b observed :active, a1, 2026-11-18, 2026-11-20" in chart
        entry=save(tmp_path,p,metadata(),snapshot=snapshot)
        assert entry["revision"]==1 and entry["type"]=="snapshot"
        assert (tmp_path/baseline["source"]).read_bytes()==before and p==original
        assert read_history(tmp_path)["baselines"]=={"execution/P1":[baseline["source"]]}
        p["tasks"][0]["duration"]=3
        with pytest.raises(ScheduleError,match="cannot change plan"):save(tmp_path,p,metadata(),snapshot=snapshot)

    def test_revision_history_trace_and_kind_separation(tmp_path):
        p=plan(); first=save(tmp_path,p,metadata()); frozen=(tmp_path/first["source"]).read_bytes()
        p["tasks"][1]["duration"]=7
        m=metadata(); m["reason"]="migration investigation changed scope"
        second=save(tmp_path,p,m)
        assert second["revision"]==2 and second["previous"]==first["source"]
        assert second["reason"]==m["reason"]
        assert (tmp_path/first["source"]).read_bytes()==frozen
        p["kind"]="decision"
        assert save(tmp_path,p,metadata())["revision"]==1
        assert len(read_history(tmp_path)["current"])==2

    def test_tamper_collision_lock_and_unapproved_baseline_refuse(tmp_path):
        p=plan();m=metadata()
        with pytest.raises(ScheduleError,match="approved"):save(tmp_path,p,m,baseline=True)
        entry=save(tmp_path,p,m)
        (tmp_path/entry["chart"]).write_text("tampered")
        with pytest.raises(ScheduleError,match="immutable"):save(tmp_path,p,m)
        (tmp_path/".schedule.lock").touch()
        with pytest.raises(ScheduleError,match="locked"):save(tmp_path,p,m)

    def test_index_commit_failure_rolls_back_only_new_files(tmp_path,monkeypatch):
        p=plan();entry=save(tmp_path,p,metadata());before=(tmp_path/"gantt-history.json").read_bytes()
        def fail(*args):raise OSError("injected replace failure")
        monkeypatch.setattr("xrefkit_skills_project_management.schedule.os.replace",fail)
        with pytest.raises(OSError,match="injected"):save(tmp_path,p,metadata())
        assert (tmp_path/"gantt-history.json").read_bytes()==before
        assert (tmp_path/entry["source"]).exists()
        assert not list(tmp_path.rglob("*r002*"))
        assert not (tmp_path/".schedule.lock").exists()

    def test_mermaid_label_injection_is_inert():
        p=plan();p["tasks"][0]["label"]="X : evil\nsection injected<script>```"
        chart=mermaid(p,calculate(p))
        assert chart.count("```")==2
        assert "<script>" not in chart and "\nsection injected" not in chart

    @pytest.mark.parametrize("damage",["reason","approval","baseline","current"])
    def test_index_cannot_rewrite_immutable_meaning(tmp_path,damage):
        save(tmp_path,plan(),metadata())
        path=tmp_path/"gantt-history.json";index=json.loads(path.read_text())
        if damage=="reason":index["entries"][0]["reason"]="invented reason"
        elif damage=="approval":index["entries"][0]["approval"]["status"]="approved"
        elif damage=="baseline":index["baselines"]={"execution/P1":[index["entries"][0]["source"]]}
        else:index["current"]={}
        path.write_text(json.dumps(index))
        with pytest.raises(ScheduleError):read_history(tmp_path)

    def test_recorded_approval_does_not_activate_later_proposal(tmp_path):
        p=plan();m=metadata();m["approval"]={"status":"approved","actor":"owner","record_ref":"approval/1"}
        approved=save(tmp_path,p,m)
        p["tasks"][0]["duration"]=3
        proposed=save(tmp_path,p,metadata())
        history=read_history(tmp_path)
        assert history["approved"]["execution/P1"]==approved["source"]
        assert history["current"]["execution/P1"]==proposed["source"]

    def test_plan_comparison_preserves_non_date_dependency_and_trace_changes():
        p=plan();q=copy.deepcopy(p)
        q["tasks"][3]["depends_on"]=q["tasks"][3]["depends_on"][:1]
        q["tasks"][3]["evidence_refs"]=["new/1"]
        delta=compare_plans(p,q)
        assert delta["finish_delta_calendar_days"]==0
        assert set(delta["task_changes"]["d"])=={"depends_on","evidence_refs"}

    @pytest.mark.parametrize("damage",["preorigin","future","dependency","unproven"])
    def test_inconsistent_observations_refused(damage):
        p=plan();snap={"as_of":"2026-11-20","tasks":{t["id"]:{"actual_start":None,"actual_finish":None,"remaining":t["duration"],"evidence_refs":[]} for t in p["tasks"]}}
        if damage=="preorigin":snap["tasks"]["a"].update(actual_start="2026-11-01")
        elif damage=="future":snap["tasks"]["a"].update(actual_start="2026-12-01")
        elif damage=="dependency":snap["tasks"]["b"].update(actual_start="2026-11-19")
        else:snap["tasks"]["a"].update(remaining=0)
        with pytest.raises(ScheduleError):calculate(p,snap)

    def test_collision_preserves_unindexed_existing_file(tmp_path):
        target=tmp_path/"execution/P1/plan-r001.json";target.parent.mkdir(parents=True);target.write_text("existing")
        with pytest.raises(FileExistsError):save(tmp_path,plan(),metadata())
        assert target.read_text()=="existing" and not (tmp_path/"gantt-history.json").exists()

    def test_later_collision_preserves_prior_index_and_collision_bytes(tmp_path):
        save(tmp_path,plan(),metadata()); before=(tmp_path/"gantt-history.json").read_bytes()
        target=tmp_path/"execution/P1/gantt-r002.md";target.write_text("existing")
        with pytest.raises(FileExistsError):save(tmp_path,plan(),metadata())
        assert target.read_text()=="existing"
        assert (tmp_path/"gantt-history.json").read_bytes()==before
        assert not (target.parent/"plan-r002.json").exists()

    def test_weekend_snapshot_cannot_precede_normalized_start():
        p=plan()
        with pytest.raises(ScheduleError,match="precedes"):
            calculate(p,{"as_of":"2026-11-15","tasks":{}})

    def test_existing_link_cannot_create_directory_outside_root(tmp_path):
        import os
        import subprocess
        root=tmp_path/'history';root.mkdir()
        outside=tmp_path/'outside';outside.mkdir()
        link=root/'execution'
        if os.name=='nt':
            subprocess.run(['cmd','/c','mklink','/J',str(link),str(outside)],check=True,capture_output=True)
        else:
            link.symlink_to(outside,target_is_directory=True)
        with pytest.raises(ScheduleError,match='escaping'):
            save(root,plan(),metadata())
        assert list(outside.iterdir())==[]

    def test_proposed_approval_rejects_nontext_actor(tmp_path):
        value=metadata();value['approval']['actor']=123
        with pytest.raises(ScheduleError,match='actor'):
            save(tmp_path,plan(),value)

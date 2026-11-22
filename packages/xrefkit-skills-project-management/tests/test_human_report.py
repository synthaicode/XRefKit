from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from xrefkit_skills_project_management.human_report import HumanReport, render_report


def facts():
    evidence = {
        key: {"label": label, "kind": kind, "method": method, "link": f"#{key}"}
        for key, (label, kind, method) in {
            "decision": ("設計再評価", "decision", "design"),
            "checklist": ("確認結果", "checklist", "design"),
            "handoff": ("引継ぎ履歴", "handoff", "wheel"),
            "approval": ("承認記録", "approval", "human"),
            "permission": ("工程の着手条件", "permission", "human"),
            "run": ("作業実績", "run", "host"),
            "xid": ("適用設計原則", "xid", "design"),
        }.items()
    }
    return {
        "schema_version": 1, "scope": "#206・#207 設計確認結果",
        "decision": {"status": "CONDITIONAL", "reason": "実環境の証拠が不足しています。", "source": "decision"},
        "evidence": evidence,
        "checks": [
            {"id": f"CHK-{i}", "result": "PASS" if i < 15 else "UNKNOWN", "source": "checklist"}
            for i in range(25)
        ],
        "work": [{"topic": "実Runnerの停止制御", "kind": "evidence", "action": "停止中の起動競合を検証する",
                  "why": "実際の停止制御を示す証拠が不足", "source": "checklist",
                  "checks": ["CHK-15", "CHK-16"]}],
        "handoffs": [{"topic": "検証依頼", "state": "waiting", "environment": "synthetic",
                      "kind": "evidence", "source": "handoff", "recipient": "PM"}],
        "limits": ["実担当者による回答と正式な作業再開は未検証"],
    }


def render(data):
    return render_report(HumanReport.model_validate(data))


def test_complete_progress_and_start_have_separate_evidence():
    data = facts()
    data.pop("decision")
    data.update(progress={"status": "complete", "reason": "対象の確認作業を終えました。", "source": "run"},
                checks=data["checks"][:15], work=[], handoffs=[])
    data["stages"] = {"manufacturing": {"state": "permitted", "source": "permission"},
                      "approval": {"state": "approved", "source": "approval"}}
    report = render(data)
    assert "報告対象の作業が完了" in report
    assert "製造着手は着手可、テスト開始は未確認、正式承認は承認済み" in report
    assert "設計判断の条件は成立" not in report


def test_unknown_group_waiting_scope_and_detail_links():
    report = render(facts())
    assert report.index("設計判断を条件付きで保留") < report.index("25項目中")
    assert "設計書上の確認で15項目" in report and "10項目が未確認" in report
    assert report.count("実Runnerの停止制御") == 1
    assert "依頼先の対応待ち、試験上の依頼先はPM" in report
    assert "対象外の作業には、それぞれの着手条件" in report
    for label, key in (("設計再評価", "decision"), ("適用設計原則", "xid"),
                       ("作業実績", "run"), ("引継ぎ履歴", "handoff"), ("確認結果", "checklist")):
        assert f"[{label}](<#{key}>)" in report
    assert not any(token in report for token in ("CHK-", "CONDITIONAL", "UNKNOWN", "waiting"))


def test_simulated_return_preserves_unresolved_and_hides_mock_owner():
    data = facts()
    data["work"][0].update(owner="Test-only owner", ownership="synthetic")
    data["handoffs"][0].update(state="returned", response="CANNOT_RESOLVE")
    report = render(data)
    assert "模擬回答。回答では問題を解消できませんでした" in report
    assert "10項目が未確認" in report and "設計判断は確定できません" in report
    assert "Test-only owner" not in report and "担当未確定" in report


def test_partial_resolution_keeps_confirmed_and_remaining():
    data = facts()
    data["checks"][-1]["result"] = "PASS"
    report = render(data)
    assert "16項目" in report and "9項目が未確認" in report


def test_authority_request_separate_from_evidence_collection():
    data = facts()
    data["decision"]["status"] = "ESCALATION_REQUIRED"
    data["work"].append({"topic": "リスク受容", "kind": "authority", "action": "適用範囲を判断する",
                         "owner": "方針責任者", "ownership": "actual", "source": "approval"})
    report = render(data)
    assert "証拠の収集" in report and "権限者の判断" in report
    assert "方針責任者" in report and "正式承認は未確認" in report


@pytest.mark.parametrize("failure", ["fabricated_pass", "missing_evidence", "approval_from_trial",
                                      "determined_with_unknown", "trial_ported_as_actual", "wrong_link",
                                      "mock_owner_as_actual", "duplicate_check"])
def test_invalid_or_contradictory_facts_are_rejected(failure):
    data = facts()
    match failure:
        case "fabricated_pass":
            data["evidence"]["checklist"]["method"] = "unverified"
        case "missing_evidence":
            data["evidence"].pop("checklist")
        case "approval_from_trial":
            data["evidence"]["approval"]["method"] = "wheel"
            data["stages"] = {"approval": {"state": "approved", "source": "approval"}}
        case "determined_with_unknown":
            data["decision"]["status"] = "DETERMINED"
        case "trial_ported_as_actual":
            data["handoffs"][0]["environment"] = "actual"
        case "wrong_link":
            data["evidence"]["handoff"]["link"] = "javascript:alert(1)"
        case "mock_owner_as_actual":
            data["work"][0].update(owner="Test-only owner", ownership="actual", source="handoff")
        case "duplicate_check":
            data["checks"].append(deepcopy(data["checks"][0]))
    with pytest.raises(ValueError):
        render(data)


@pytest.mark.parametrize(("status", "meaning"), [
    ("DETERMINED", "成立条件を満たしています"), ("CONDITIONAL", "条件付きで保留"),
    ("BLOCKED", "必要な条件が揃わず"), ("ESCALATION_REQUIRED", "権限者の判断が必要"),
    ("UNKNOWN", "判断の結果は未確認"),
])
def test_status_mapping(status, meaning):
    data = facts()
    data["decision"]["status"] = status
    if status == "DETERMINED":
        data["checks"] = data["checks"][:15]
        data["work"] = []
    assert meaning in render(data)


def test_source_describes_target_risk_and_verification_separately_from_trial():
    data = facts()
    item = data["work"][0]
    item.update(topic="AI APIの送信と外部ツールの起動",
                action="停止後に新しい送信や起動が始まらないことを確認する",
                explanation={
                    "state": "unconfirmed", "problem": "実際の送信処理では停止後の動きを確認できていません",
                    "impact": "停止指示後も外部システムへの操作が始まること",
                    "verification": "停止指示と送信が重なる条件で試験する",
                    "expected_evidence": "送信側と受信側の実行ログ",
                })
    data["work"].append(dict(item, checks=[]))
    text = render(data)
    project, trial = text.split("**機構の検証結果**")
    assert project.index("設計判断は確定できません") < project.index("**問題の内容**")
    assert project.count("実際の送信処理では停止後の動きを確認できていません") == 1
    assert project.count("停止指示と送信が重なる条件で試験する") == 1
    assert "AI APIの送信と外部ツールの起動" in project and "起こり得る影響" in project
    assert "送信側と受信側の実行ログ" in project and "担当未確定" in project
    assert "判断が必要な事項" not in project and "試験上の依頼先" not in project
    assert "試験上の依頼先はPM" in trial


def test_unknown_checks_cannot_be_recast_as_observed_and_method_can_be_pending():
    data = facts()
    data["work"][0]["explanation"] = {"state": "observed", "problem": "外部処理が始まりました"}
    with pytest.raises(ValueError, match="observed problem"):
        render(data)
    data["work"][0]["explanation"].update(state="unconfirmed", problem="外部処理が始まるか未確認")
    result = render(data)
    assert "確認方法を決める必要があります" in result
    assert "起こり得る影響" not in result


def test_cli_emits_the_same_utf8_summary(tmp_path):
    data = facts()
    input_file = tmp_path / "facts.json"
    input_file.write_text(json.dumps(data), encoding="utf-8")
    process = subprocess.run([sys.executable, "-B", "-m", "xrefkit_skills_project_management.human_report",
                              str(input_file)], check=True, capture_output=True,
                             env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert process.stdout.decode("utf-8") == render(data)

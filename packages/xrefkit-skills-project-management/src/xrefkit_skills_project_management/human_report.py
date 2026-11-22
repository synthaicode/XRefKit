"""Render a Japanese PM summary from attributed, scope-specific facts."""

from argparse import ArgumentParser
import json
from pathlib import Path
import re
import sys
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from .issue_projection import _inline, _url
from .next_step_readiness import ReadinessInput, evaluate, report_lines


DECISIONS = {
    "DETERMINED": "設計判断の成立条件を満たしています",
    "CONDITIONAL": "設計判断を条件付きで保留しています",
    "BLOCKED": "必要な条件が揃わず、設計判断を保留しています",
    "ESCALATION_REQUIRED": "設計判断には権限者の判断が必要です",
    "UNKNOWN": "設計判断の結果は未確認です",
}
PROGRESS = {
    "complete": "報告対象の作業が完了しました", "in_progress": "報告対象の作業を進めています",
    "blocked": "報告対象の作業を保留しています", "unknown": "報告対象の進捗は未確認です",
}
METHODS = {
    "design": "設計書上の確認", "static": "静的解析", "synthetic": "合成データによる実行",
    "wheel": "Wheelを導入した試験環境での結合検証", "host": "実ホストでの検証",
    "external": "実際の外部効果を伴う検証", "human": "人間の正式な記録",
    "unverified": "未検証",
}
ACTIONS = {
    "evidence": "証拠の収集", "information": "情報の確認", "design": "設計の再評価",
    "authority": "権限者の判断", "approval": "正式承認",
    "environment": "環境・権限の整備", "knowledge": "設計原則の確認",
}
HANDOFFS = {
    "prepared": "依頼を準備中", "sent": "送付済み、受領待ち", "received": "受領済み",
    "waiting": "依頼先の対応待ち", "returned": "回答を返却済み",
    "acknowledged": "元の担当が回答を受領", "assessed": "元の担当が回答を評価",
    "cancelled": "依頼を取り消し",
}
RESPONSES = {
    "CANNOT_RESOLVE": "回答では問題を解消できませんでした", "REJECTED": "依頼は却下されました",
    "EVIDENCE_PROVIDED": "検証証拠が届きました", "INFORMATION_PROVIDED": "確認情報が届きました",
    "DESIGN_DIRECTION": "設計方針が示されました", "RISK_ACCEPTED": "リスク受容が記録されました",
}
STAGES = {"manufacturing": "製造着手", "test": "テスト開始", "approval": "正式承認"}
PHASES = {"held": "保留", "unknown": "未確認", "permitted": "着手可", "approved": "承認済み"}
BASIS = Literal["decision", "checklist", "run", "xid", "handoff", "approval", "permission", "evidence"]
Method = Literal["design", "static", "synthetic", "wheel", "host", "external", "human", "unverified"]
ActionKind = Literal["evidence", "information", "design", "authority", "approval", "environment", "knowledge"]
Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class Fact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Evidence(Fact):
    label: Short
    link: str
    kind: BASIS
    method: Method

    @model_validator(mode="after")
    def valid_link(self):
        if not re.fullmatch(r"#[A-Za-z0-9_-]+", self.link):
            _url(self.link)
        return self


class Decision(Fact):
    status: Literal["DETERMINED", "CONDITIONAL", "BLOCKED", "ESCALATION_REQUIRED", "UNKNOWN"]
    reason: Short
    source: Short


class Progress(Fact):
    status: Literal["complete", "in_progress", "blocked", "unknown"]
    reason: Short
    source: Short


class Check(Fact):
    id: Short
    result: Literal["PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE"]
    source: Short


class WorkExplanation(Fact):
    """Source-backed description of a finding and how to evaluate it."""

    state: Literal["unconfirmed", "observed"]
    problem: Short
    impact: Short | None = None
    verification: Short | None = None
    expected_evidence: Short | None = None


class Work(Fact):
    topic: Short
    kind: ActionKind
    action: Short
    why: Short | None = None
    owner: Short | None = None
    ownership: Literal["actual", "synthetic"] | None = None
    source: Short
    checks: tuple[Short, ...] = ()
    scope: Literal["project", "mechanism"] = "project"
    explanation: WorkExplanation | None = None

    @model_validator(mode="after")
    def owner_has_provenance(self):
        if (self.owner is None) != (self.ownership is None):
            raise ValueError("an owner requires explicit actual or synthetic provenance")
        return self


class Handoff(Fact):
    topic: Short
    state: Literal["prepared", "sent", "received", "waiting", "returned", "acknowledged", "assessed", "cancelled"]
    environment: Literal["actual", "synthetic"]
    kind: ActionKind
    source: Short
    recipient: Short | None = None
    note: Short | None = None
    response: Literal[
        "CANNOT_RESOLVE", "REJECTED", "EVIDENCE_PROVIDED", "INFORMATION_PROVIDED",
        "DESIGN_DIRECTION", "RISK_ACCEPTED",
    ] | None = None

    @model_validator(mode="after")
    def response_matches_state(self):
        if self.response and self.state not in {"returned", "acknowledged", "assessed"}:
            raise ValueError("a response requires a recorded return")
        return self


class Stage(Fact):
    state: Literal["held", "unknown", "permitted", "approved"]
    source: Short


class HumanReport(Fact):
    schema_version: Literal[1]
    scope: Short
    decision: Decision | None = None
    progress: Progress | None = None
    evidence: dict[Short, Evidence]
    checks: tuple[Check, ...] = ()
    work: tuple[Work, ...] = ()
    handoffs: tuple[Handoff, ...] = ()
    stages: dict[Literal["manufacturing", "test", "approval"], Stage] = {}
    limits: tuple[Short, ...] = ()
    readiness: ReadinessInput | None = None

    def _source(self, key, kind):
        record = self.evidence.get(key)
        if record is None or (kind is not None and record.kind != kind):
            raise ValueError(f"missing or incorrect evidence for {key}")
        return record

    @model_validator(mode="after")
    def consistent_facts(self):
        if self.readiness:
            for key, scope in self.readiness.sources.items():
                record = self._source(key, None)
                if scope == "project" and record.method in {"synthetic", "wheel", "unverified"}:
                    raise ValueError("trial or unverified records cannot establish actual project readiness")
            evaluate(self.readiness)
        if (self.decision is None) == (self.progress is None):
            raise ValueError("a report requires exactly one decision or progress scope")
        check_results = {check.id: check.result for check in self.checks}
        pending = {key for key, result in check_results.items() if result in {"UNKNOWN", "FAIL"}}
        if len({check.id for check in self.checks}) != len(self.checks):
            raise ValueError("duplicate Check ID")
        if self.decision:
            source = self._source(self.decision.source, "decision")
            if self.decision.status == "DETERMINED" and (pending or source.method == "unverified"):
                raise ValueError("a determined decision requires evidence and no pending checks")
        if self.progress:
            source = self._source(self.progress.source, "run")
            if self.progress.status == "complete" and (pending or source.method == "unverified"):
                raise ValueError("completion requires evidence and no pending checks in its scope")
        for check in self.checks:
            source = self._source(check.source, "checklist")
            if check.result == "PASS" and source.method == "unverified":
                raise ValueError("pass requires observed evidence")
        assigned = [check_id for item in self.work for check_id in item.checks]
        if set(assigned) - pending or len(set(assigned)) != len(assigned):
            raise ValueError("grouped work must refer to distinct pending Check IDs")
        for item in self.work:
            source = self._source(item.source, None)
            if item.ownership == "actual" and source.method in {"synthetic", "unverified", "wheel"}:
                raise ValueError("test or unverified evidence cannot confirm an actual owner")
            if item.explanation and item.explanation.state == "observed":
                if source.method == "unverified" or (
                    item.scope == "project" and source.method in {"synthetic", "wheel"}
                ) or (item.checks and all(check_results[key] == "UNKNOWN" for key in item.checks)):
                    raise ValueError("an observed problem needs evidence for this scope")
        for item in self.handoffs:
            source = self._source(item.source, "handoff")
            if item.environment == "actual" and source.method not in {"host", "external", "human"}:
                raise ValueError("test or unverified evidence cannot establish an actual handoff")
        for stage, result in self.stages.items():
            if result.state in {"held", "unknown"}:
                self._source(result.source, None)
                continue
            expected = "approved" if stage == "approval" else "permitted"
            kind = "approval" if stage == "approval" else "permission"
            methods = {"human"} if stage == "approval" else {"human", "host", "external"}
            if result.state != expected or self._source(result.source, kind).method not in methods:
                raise ValueError("authorization requires its own applicable permission or approval record")
        return self


def _links(report, ids):
    return " ".join(
        f"[{_inline(report.evidence[key].label)}](<{report.evidence[key].link}>)"
        for key in dict.fromkeys(ids)
    )


def _sentence(text):
    return _inline(text).rstrip("。") + "。"


def _work_line(item):
    owner = _inline(item.owner) if item.ownership == "actual" else "担当未確定"
    explanation = item.explanation
    if explanation is None:
        why = f"。{_inline(item.why)}" if item.why else ""
        return f"- {_inline(item.topic)} — {ACTIONS[item.kind]}。{_inline(item.action)}（{owner}）{why}"
    details = [item.action]
    if explanation.verification:
        details.append(explanation.verification)
    elif item.kind == "evidence":
        details.append("確認方法を決める必要があります")
    if explanation.expected_evidence:
        details.append("必要な記録は" + explanation.expected_evidence)
    if item.why and item.why.rstrip("。") != explanation.problem.rstrip("。"):
        details.append(item.why)
    return f"- **{_inline(item.topic)}**（{owner}） " + "".join(dict.fromkeys(map(_sentence, details)))


def _handoff_line(item):
    prefix = "試験で確認した引継ぎ" if item.environment == "synthetic" else "引継ぎ"
    recipient = "、依頼先は未確認"
    if item.recipient:
        label = "試験上の依頼先" if item.environment == "synthetic" else "依頼先"
        recipient = f"、{label}は{_inline(item.recipient)}"
    response = f"。{'模擬回答。' if item.environment == 'synthetic' else ''}{RESPONSES[item.response]}" if item.response else ""
    note = " " + _sentence(item.note) if item.note else ""
    return f"- {prefix} — {_inline(item.topic)}（{ACTIONS[item.kind]}）。{HANDOFFS[item.state]}{recipient}{response}。{note}"


def _section(lines, title, rows, limit=None):
    unique = list(dict.fromkeys(rows))
    if unique:
        lines.extend(["", f"**{title}**", "", *unique[:limit]])
        if limit is not None and len(unique) > limit:
            lines.append(f"- 残り{len(unique) - limit}件は末尾の根拠を参照してください。")


def summary_lines(report: HumanReport, *, decision_details=()) -> list[str]:
    """Render only display facts. Canonical IDs and raw records stay at their links."""
    status = report.decision or report.progress
    headline = DECISIONS[status.status] if report.decision else PROGRESS[status.status]
    lines = [
        f"**{_inline(report.scope)}**",
        "",
        f"**現在　{headline}。**",
        _inline(status.reason),
    ]
    stages = "、".join(
        f"{name}は{PHASES[report.stages[key].state] if key in report.stages else '未確認'}"
        for key, name in STAGES.items()
    )
    decision = ""
    if report.decision:
        decision = "設計判断の条件は成立。" if report.decision.status == "DETERMINED" else "設計判断は確定できません。"
    if report.readiness:
        if decision:
            lines.append(decision)
        lines.extend(report_lines(evaluate(report.readiness)))
    else:
        lines += [f"**次に進めるか**　{decision}{stages}。"
                  "対象外の作業には、それぞれの着手条件が適用されます。"]
    stats = {}
    for check in report.checks:
        if check.result == "PASS":
            method = report.evidence[check.source].method
            stats[method] = stats.get(method, 0) + 1
    if report.checks:
        counts = "、".join(f"{METHODS[method]}で{count}項目" for method, count in stats.items())
        confirmed = f"{len(report.checks)}項目中、{counts}を確認しました。" if counts else "合格として記録された項目はありません。"
        lines += ["", f"**確認できたこと**　{confirmed}"]
    unknown = sum(check.result == "UNKNOWN" for check in report.checks)
    failures = sum(check.result == "FAIL" for check in report.checks)
    if unknown or failures:
        outcomes = []
        if unknown:
            outcomes.append(f"{unknown}項目が未確認")
        if failures:
            outcomes.append(f"{failures}項目で条件を満たしていません")
        lines += ["", f"**未解決事項**　{'、'.join(outcomes)}。"]
    project = [item for item in report.work if item.scope == "project"]
    problems = []
    for item in project:
        explanation = item.explanation
        if explanation is None:
            continue
        basis = "未確認" if explanation.state == "unconfirmed" else "確認済み（" + METHODS[report.evidence[item.source].method] + "）"
        impact = f" 起こり得る影響　{_sentence(explanation.impact)}" if explanation.impact else ""
        problems.append(f"- **{_inline(item.topic)}**（{basis}） {_sentence(explanation.problem)}{impact}")
    _section(lines, "問題の内容", problems, 5)
    planned_checks = {check for row in report.readiness.conditions for check in row.check_ids} if report.readiness else set()
    actions = [_work_line(item) for item in project if item.kind not in {"authority", "approval"}
               and (not item.checks or not set(item.checks) <= planned_checks)]
    actions.extend(_handoff_line(item) for item in report.handoffs if item.environment == "actual")
    _section(lines, "対応方法", actions, 5)
    _section(lines, "判断が必要な事項", [_work_line(item) for item in project if item.kind in {"authority", "approval"}])
    lines.extend(decision_details)
    trials = [_work_line(item) for item in report.work if item.scope == "mechanism"]
    trials.extend(_handoff_line(item) for item in report.handoffs if item.environment == "synthetic")
    _section(lines, "機構の検証結果", trials, 3)
    if report.limits:
        lines += ["", "**検証範囲**　" + "。".join(_inline(value).rstrip("。") for value in report.limits) + "。"]
    return lines


def render_report(report: HumanReport) -> str:
    links = _links(report, report.evidence)
    return "\n".join([*summary_lines(report), "", f"**根拠**　{links}", ""])


def main():
    parser = ArgumentParser(description="Render a Japanese PM report from verified report facts.")
    parser.add_argument("facts", type=Path)
    args = parser.parse_args()
    try:
        report = HumanReport.model_validate(json.loads(args.facts.read_text(encoding="utf-8-sig")))
        sys.stdout.buffer.write(render_report(report).encode("utf-8"))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()

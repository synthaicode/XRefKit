"""Read-only PM projection of declared start conditions and schedule dependencies."""

from argparse import ArgumentParser
from datetime import date
from graphlib import CycleError, TopologicalSorter
import json
from pathlib import Path
import sys
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from .issue_projection import _inline
from .schedule import calculate, validate_plan


State = Literal["SATISFIED", "UNSATISFIED", "UNKNOWN", "NOT_APPLICABLE"]
UNKNOWN_MEANINGS = {
    "design_unresolved": "設計未確定",
    "missing_information": "情報不足",
    "implementation_pending": "実装待ち",
    "post_implementation_verification": "実装後の検証待ち",
    "environment_missing": "環境不足",
    "human_decision": "権限者の判断待ち",
}
PHASES = {"design": "設計で確認", "pre_start": "着手前", "trial": "試験用の実装で確認", "acceptance": "実装後の受入"}
STATUS = {"READY": "着手条件が成立", "NOT_READY": "着手条件が未成立", "PENDING_VERIFICATION": "確認待ち",
          "PENDING_DECISION": "権限者の判断待ち", "UNDEFINED": "工程または着手条件が未定"}
CONDITION_STATUS = {"SATISFIED": "成立", "UNSATISFIED": "未成立", "UNKNOWN": "未確認", "NOT_APPLICABLE": "適用外"}


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True, str_min_length=1)


class Action(Record):
    id: str
    work: str
    owner: str | None = None
    artifact: str
    completion: str
    due: date | None = None


class Condition(Record):
    id: str
    task: str
    requirement: str
    result: State
    basis: str
    source: str | None = None
    phase: Literal["design", "pre_start", "trial", "acceptance"]
    blocks_start: StrictBool
    authority: StrictBool = False
    unknown_reason: Literal[
        "design_unresolved", "missing_information", "implementation_pending",
        "post_implementation_verification", "environment_missing", "human_decision",
    ] | None = None
    action: Action | None = None
    covers: tuple[str, ...] = ()
    decision_ids: tuple[str, ...] = ()
    xids: tuple[str, ...] = ()
    check_ids: tuple[str, ...] = ()
    needs_tasks: tuple[str, ...] = ()
    waiting_source: str | None = None


class Gate(Record):
    result: Literal["allowed", "denied", "unknown"]
    source: str


class ReadinessInput(Record):
    schema_version: Literal[1]
    current_task: str
    plan: dict | None = None
    plan_ref: str | None = None
    snapshot: dict | None = None
    snapshot_ref: str | None = None
    sources: dict[str, Literal["project", "synthetic", "proposal"]] = Field(default_factory=dict)
    start_contracts: dict[str, str] = Field(default_factory=dict)
    conditions: tuple[Condition, ...] = ()
    gates: dict[str, Gate] = Field(default_factory=dict)
    proposals: tuple[str, ...] = ()


def _actual(value, source):
    return value.sources.get(source) == "project"


def _cycle(dependencies, task):
    reachable = set()
    pending = [task]
    while pending:
        node = pending.pop()
        if node not in reachable:
            reachable.add(node)
            pending.extend(dependencies[node])
    try:
        TopologicalSorter({node: sorted(dependencies[node]) for node in sorted(reachable)}).prepare()
    except CycleError as exc:
        return exc.args[1]
    return []


def _condition_projection(value, condition):
    result = condition.result
    waiting = condition.waiting_source is not None and _actual(value, condition.waiting_source)
    if not _actual(value, condition.source) or waiting and result == "SATISFIED":
        result = "UNKNOWN"
    projected = condition.model_dump(mode="json")
    action = projected["action"]
    if action and not _actual(value, condition.source) and (action["owner"] or action["due"]):
        projected["action"] = {**action, "id": "unconfirmed:" + action["id"], "owner": None, "due": None}
    return {**projected, "effective_result": result, "waiting": waiting,
            "formal_decision": condition.unknown_reason == "human_decision" and _actual(value, condition.source),
            "trial_only": value.sources.get(condition.source) == "synthetic"}


def _group_actions(conditions):
    groups = {}
    for row in conditions:
        if row["effective_result"] not in {"UNKNOWN", "UNSATISFIED"}:
            continue
        action = row["action"] or {
            "id": "unplanned:" + row["id"], "work": row["requirement"] + "の確認・解消方法を決める",
            "owner": None, "artifact": "確認・解消の計画",
            "completion": "根拠を示せる手順と担当が決まること", "due": None,
        }
        group = groups.setdefault(action["id"], {**action, "conditions": [], "tasks": [], "reasons": []})
        group["conditions"].append(row["id"])
        for key, item in (("tasks", row["task"]), ("reasons", row["basis"])):
            if item not in group[key]:
                group[key].append(item)
    return list(groups.values())


def evaluate(value: ReadinessInput) -> dict:
    """Derive next steps from direct FS successors; never execute or persist transitions."""
    result = {"current_task": value.current_task, "plan_ref": value.plan_ref, "steps": [],
              "sources": value.sources, "proposals": list(value.proposals)}
    if value.plan is None:
        if value.snapshot is not None or value.start_contracts or value.conditions or value.gates:
            raise ValueError("a schedule is required to scope task records")
        result["proposals"].append("次に行う工程と着手条件を計画に記録する。担当未確定。")
        return {**result, "status": "UNDEFINED", "actions": []}

    tasks, order, calendar = validate_plan(value.plan)
    if value.current_task not in tasks or value.plan_ref not in value.sources:
        raise ValueError("current task and plan evidence must identify the schedule being assessed")
    if value.snapshot is not None:
        if value.snapshot_ref not in value.sources:
            raise ValueError("snapshot provenance is required")
        calculate(value.plan, value.snapshot)
    seen, definitions = set(), {}
    for condition in value.conditions:
        if (condition.id in seen or condition.task not in tasks or set(condition.needs_tasks) - tasks.keys()
                or any(ref is not None and ref not in value.sources for ref in (condition.source, condition.waiting_source))):
            raise ValueError("invalid condition identity, task, or source")
        seen.add(condition.id)
        if condition.result != "UNKNOWN" and condition.source is None:
            raise ValueError("condition results require evidence")
        if condition.action:
            prior = definitions.setdefault(condition.action.id, condition.action)
            if prior != condition.action:
                raise ValueError("grouped actions must agree on owner, output and completion evidence")
    if ((set(value.start_contracts) | set(value.gates)) - tasks.keys()
            or (set(value.start_contracts.values()) | {gate.source for gate in value.gates.values()}) - value.sources.keys()):
        raise ValueError("invalid start contract or gate provenance")

    rows = {task: [] for task in tasks}
    dependencies = {task: set() for task in tasks}
    snapshot = value.snapshot if _actual(value, value.snapshot_ref) else None
    as_of = date.fromisoformat(snapshot["as_of"]) if snapshot else None
    for task_id, task in tasks.items():
        for edge in task["depends_on"]:
            predecessor = edge["task"]
            finished = snapshot["tasks"][predecessor]["actual_finish"] if snapshot else None
            satisfied = bool(finished and calendar.add(date.fromisoformat(finished), edge["lag"]) <= as_of)
            if not satisfied:
                dependencies[task_id].add(predecessor)
            status = "SATISFIED" if satisfied else ("UNSATISFIED" if snapshot else "UNKNOWN")
            rows[task_id].append({
                "id": f"schedule:{task_id}:{predecessor}", "task": task_id, "phase": "pre_start",
                "requirement": tasks[predecessor]["label"] + "の完了と計画上の待機期間",
                "effective_result": status, "source": value.snapshot_ref if snapshot else value.plan_ref,
                "basis": "実績記録で先行工程の完了と待機期間を確認" if satisfied else "計画上の先行工程と待機期間の成立を確認できていない",
                "blocks_start": True, "waiting": False, "unknown_reason": None,
                "action": {"id": "schedule:verify-predecessors", "work": "先行工程の実績と待機期間を照合する",
                           "owner": None, "artifact": "工程の実績と日程を照合した記録",
                           "completion": "対象の先行工程の完了日と必要な待機期間を確認できること", "due": None},
            })
        earliest = max(date.fromisoformat(task.get("not_before", value.plan["start"])),
                       date.fromisoformat(value.plan["start"]))
        earliest = calendar.normalize(earliest)
        if _actual(value, value.plan_ref) and (as_of is None or as_of < earliest):
            rows[task_id].append({
                "id": f"schedule:{task_id}:date", "task": task_id, "phase": "pre_start",
                "requirement": "計画上の着手可能日", "effective_result": "UNSATISFIED" if as_of else "UNKNOWN",
                "source": value.snapshot_ref if snapshot else value.plan_ref,
                "basis": f"計画上の着手可能日 {earliest.isoformat()} に到達した実績基準日を確認する必要がある",
                "blocks_start": True, "waiting": False, "action": None, "unknown_reason": None,
            })
    for condition in value.conditions:
        entry = _condition_projection(value, condition)
        rows[condition.task].append(entry)
        if entry["blocks_start"] and entry["effective_result"] in {"UNKNOWN", "UNSATISFIED"}:
            dependencies[condition.task].update(
                task for task in condition.needs_tasks if snapshot is None or not snapshot["tasks"][task]["actual_finish"]
            )

    candidates = [key for key in order if any(edge["task"] == value.current_task for edge in tasks[key]["depends_on"])]
    for key in candidates:
        conditions = rows[key]
        blockers = [row for row in conditions if row["blocks_start"] and row["effective_result"] in {"UNKNOWN", "UNSATISFIED"}]
        governed = [c for c in value.conditions if c.task == key and c.blocks_start]
        expected = {ref for name in ("decision_refs", "hold_refs", "evidence_refs") for ref in tasks[key][name]}
        missing = sorted(expected - {ref for c in governed for ref in c.covers})
        cycle = _cycle(dependencies, key)
        contract_defined = (_actual(value, value.plan_ref) and _actual(value, value.start_contracts.get(key))
                            and any(c.authority for c in governed) and not missing)
        decision = any(row.get("formal_decision") for row in blockers)
        hard_blocker = any(row["effective_result"] == "UNSATISFIED" and not row.get("formal_decision")
                           for row in blockers)
        if cycle or hard_blocker:
            status = "NOT_READY"
        elif not contract_defined:
            status = "UNDEFINED"
        elif decision:
            status = "PENDING_DECISION"
        elif blockers:
            status = "PENDING_VERIFICATION"
        else:
            status = "READY"
        gate = value.gates.get(key)
        gate_result = gate.result if gate and _actual(value, gate.source) else "unknown"
        disagreement = (status == "READY" and gate_result == "denied") or (status != "READY" and gate_result == "allowed")
        next_actions = []
        if cycle:
            next_actions.append("循環した着手条件をBrownfieldへ差し戻し、設計・着手前・試験・受入の条件を再評価する。")
        if not contract_defined:
            next_actions.append("工程の着手条件と権限の根拠を計画管理者と確認する。追加が必要な条件は提案として記録する。")
        result["steps"].append({"task": key, "work_item": tasks[key]["work_ref"], "label": tasks[key]["label"],
                                "status": status, "missing_refs": missing, "cycle": cycle,
                                "cycle_labels": [tasks[node]["label"] for node in cycle],
                                "gate": gate.model_dump() if gate else None, "effective_gate": gate_result,
                                "gate_disagreement": disagreement, "conditions": conditions,
                                "follow_up": next_actions})
    result["status"] = "EVALUATED" if candidates else "UNDEFINED"
    result["plan_proposed"] = not _actual(value, value.plan_ref)
    if not candidates:
        result["proposals"].append("次に行う工程と着手条件を計画に記録する。担当未確定。")
    result["actions"] = _group_actions([row for step in result["steps"] for row in step["conditions"]])
    result["current_label"] = tasks[value.current_task]["label"]
    return result


def report_lines(result):
    lines = ["", "**次のStep**", ""]
    if result.get("plan_proposed"):
        lines.append("- この順序は既存資料から組み立てた工程案です。正式な工程と着手条件は計画管理者の確認が必要です。")
    if result["status"] == "UNDEFINED":
        lines.append("- 次工程未定。計画管理者と後続工程と着手条件を決める必要があります。担当未確定。")
    for step in result["steps"]:
        lines.append(f"- **{_inline(step['label'])}**　{STATUS[step['status']]}。")
    lines += ["", "**次へ進むために必要なこと**", ""]
    for step in result["steps"]:
        for row in step["conditions"]:
            if row["effective_result"] not in {"UNKNOWN", "UNSATISFIED"}:
                continue
            timing = "着手条件" if row["blocks_start"] else "この工程の着手条件外"
            reason = row["unknown_reason"]
            if reason == "human_decision" and not row.get("formal_decision"):
                reason = None
            classification = UNKNOWN_MEANINGS.get(reason, CONDITION_STATUS[row["effective_result"]])
            waiting = "（現在、引継ぎ先の対応待ち）" if row["waiting"] else ""
            basis = "試験結果のみで、実案件の条件成立は未確認" if row.get("trial_only") else row["basis"]
            lines.append(f"- {_inline(step['label'])}　{_inline(row['requirement'])}（{timing}／{PHASES[row['phase']]}／{classification}）{waiting}。"
                         f"{_inline(basis).rstrip('。')}。")
        if step["cycle"]:
            lines.append("- 循環している着手条件　" + " → ".join(map(_inline, step["cycle_labels"])) + "。")
    lines.extend(f"- {_inline(action)}" for action in dict.fromkeys(
        action for step in result["steps"] for action in step["follow_up"]
    ))
    lines.extend(f"- 提案　{_inline(item)}" for item in result["proposals"])
    lines += ["", "**誰が何をするか**", ""]
    task_labels = {step["task"]: step["label"] for step in result["steps"]}
    for action in result["actions"]:
        owner = _inline(action["owner"]) if action["owner"] else "担当未確定。担当を決める"
        due = f"期限　{action['due']}。" if action["due"] else ""
        targets = "、".join(_inline(task_labels[key]) for key in action["tasks"])
        lines.append(f"- {_inline(action['work'])}（{owner}）。{due}"
                     f"成果物　{_inline(action['artifact'])}。完了条件　{_inline(action['completion'])}。対象　{targets}。")
    lines += ["", "**進行範囲**", "",
              "- この評価は工程上の見通しです。実行時は対象ごとのゲートと承認を確認します。"]
    for step in result["steps"]:
        if step["effective_gate"] == "denied":
            lines.append(f"- {_inline(step['label'])}　実行ゲートで拒否。実行は保留です。")
        if step["gate_disagreement"]:
            lines.append(f"- {_inline(step['label'])}　PM評価と実行ゲートの判定に差があるため、根拠を照合する必要があります。")
    lines += ["- 対象外の作業には、それぞれの着手条件が適用されます。"]
    reserved = [step for step in result["steps"] if any(row["blocks_start"] and row.get("formal_decision")
                and row["effective_result"] in {"UNKNOWN", "UNSATISFIED"} for row in step["conditions"])]
    if reserved:
        lines += ["", "**人間に判断してほしいこと**", ""]
        for step in reserved:
            for row in step["conditions"]:
                if row["blocks_start"] and row.get("formal_decision") and row["effective_result"] in {"UNKNOWN", "UNSATISFIED"}:
                    lines.append(f"- {_inline(step['label'])}　{_inline(row['requirement'])}。")
    return lines


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    args = parser.parse_args()
    try:
        value = ReadinessInput.model_validate_json(args.records.read_text(encoding="utf-8-sig"))
        output = json.dumps(evaluate(value), ensure_ascii=False, indent=2) + "\n"
        sys.stdout.buffer.write(output.encode("utf-8"))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()

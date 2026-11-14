"""Deterministic, bounded scheduling and append-only local plan history.

No operation grants project authority or evaluates quality/start conditions.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


class ScheduleError(ValueError):
    """Invalid or unsupported scheduling input; do not guess a schedule."""


def _require(condition, message):
    if not condition:
        raise ScheduleError(message)


def _text(value, name):
    _require(isinstance(value, str) and bool(value.strip()), f"{name}: nonempty text required")
    return value


def _integer(value, name, minimum=0):
    _require(type(value) is int and value >= minimum, f"{name}: integer >= {minimum} required")
    return value


def _date(value):
    _require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), "ISO date required")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ScheduleError(str(exc)) from exc


def _refs(value, name):
    _require(isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value), f"{name}: text list required")
    if name == "requirement_xids":
        _require(all(re.fullmatch(r"[A-F0-9]{12}", x) for x in value), "requirement_xids must be XIDs")


def _fields(value, required, optional=()):
    _require(isinstance(value, dict), "object required")
    _require(set(required) <= value.keys(), f"missing fields: {sorted(set(required)-value.keys())}")
    _require(not value.keys()-set(required)-set(optional), f"unsupported fields: {sorted(value.keys()-set(required)-set(optional))}")


class Calendar:
    def __init__(self, data):
        _fields(data, ("working_weekdays", "holidays"))
        days = data["working_weekdays"]
        _require(isinstance(days, list) and days and all(type(x) is int and 0 <= x <= 6 for x in days), "working_weekdays: nonempty list of 0..6")
        _require(len(set(days)) == len(days), "duplicate working weekdays")
        self.days = set(days)
        _refs(data["holidays"], "holidays")
        self.holidays = {_date(x) for x in data["holidays"]}

    def working(self, day):
        return day.weekday() in self.days and day not in self.holidays

    def normalize(self, day):
        while not self.working(day):
            day += timedelta(days=1)
        return day

    def add(self, day, duration):
        day = self.normalize(day)
        for _ in range(duration):
            day = self.normalize(day + timedelta(days=1))
        return day

    def distance(self, start, end):
        end = self.normalize(end)
        if end < start:
            return -self.distance(end, start)
        count = 0
        while start < end:
            start = self.add(start, 1)
            count += 1
        return count


def validate_plan(plan):
    _fields(plan, ("schema_version", "plan_id", "kind", "start", "calendar", "tasks", "rules_ref"), ("links",))
    _require(type(plan["schema_version"]) is int and plan["schema_version"] == 1, "unsupported schema_version")
    _require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", _text(plan["plan_id"], "plan_id")), "unsafe plan_id")
    _require(plan["kind"] in ("decision", "execution"), "kind must be decision or execution")
    _date(plan["start"])
    calendar = Calendar(plan["calendar"])
    _text(plan["rules_ref"], "rules_ref")
    _require(isinstance(plan["tasks"], list) and plan["tasks"], "tasks must be nonempty")
    tasks = {}
    for task in plan["tasks"]:
        _fields(task, ("id", "label", "duration", "depends_on", "requirement_xids", "evidence_refs", "decision_refs", "hold_refs", "work_ref"), ("not_before",))
        tid = _text(task["id"], "id")
        _require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", tid) and tid not in tasks, "unsafe or duplicate task id")
        _text(task["label"], "label")
        _text(task["work_ref"], "work_ref")
        _integer(task["duration"], "duration")
        for field in ("requirement_xids", "evidence_refs", "decision_refs", "hold_refs"):
            _refs(task[field], field)
        _require(all(re.fullmatch(r"[A-F0-9]{12}", x) for x in task["requirement_xids"]), "requirement_xids must be XIDs")
        if "not_before" in task:
            _date(task["not_before"])
        _require(isinstance(task["depends_on"], list), "depends_on must be a list")
        seen = set()
        for edge in task["depends_on"]:
            _fields(edge, ("task", "type", "lag"))
            _text(edge["task"], "dependency task")
            _require(edge["type"] == "FS", "only finish-to-start dependencies supported")
            _integer(edge["lag"], "lag")
            _require(edge["task"] not in seen, "duplicate dependency")
            seen.add(edge["task"])
        tasks[tid] = task
    for tid, task in tasks.items():
        _require(all(x["task"] in tasks and x["task"] != tid for x in task["depends_on"]), "unknown, cross-plan or self dependency; use links/Hold for cross-plan handoff")
    _require(isinstance(plan.get("links", []), list), "links must be a list")
    for link in plan.get("links", []):
        _fields(link, ("relation", "target_ref", "requirement_xids", "evidence_refs", "decision_refs", "hold_refs"))
        _require(link["relation"] in ("requirement_change", "investigation", "method_decision", "data_migration", "informs", "reopens"), "unsupported trace relation")
        _text(link["target_ref"], "target_ref")
        for field in ("requirement_xids", "evidence_refs", "decision_refs", "hold_refs"):
            _refs(link[field], field)
    order = []
    pending = set(tasks)
    while pending:
        ready = sorted(t for t in pending if all(d["task"] in order for d in tasks[t]["depends_on"]))
        _require(bool(ready), "dependency cycle")
        order.extend(ready)
        pending.difference_update(ready)
    return tasks, order, calendar


def calculate(plan, snapshot=None):
    """CPM in working-day units. Finish dates are exclusive working boundaries.

    Snapshot forecast uses actual finishes and explicit remaining duration;
    percentages never imply completion or acceptance.
    """
    tasks, order, calendar = validate_plan(plan)
    origin = calendar.normalize(_date(plan["start"]))
    observations = {}
    asof = 0
    if snapshot is not None:
        _fields(snapshot, ("as_of", "tasks"))
        _require(_date(snapshot["as_of"]) >= origin, "snapshot precedes plan start")
        asof = calendar.distance(origin, _date(snapshot["as_of"]))
        _require(asof >= 0, "snapshot precedes plan start")
        _require(isinstance(snapshot["tasks"], dict) and set(snapshot["tasks"]) == set(tasks), "snapshot must explicitly cover every task")
        observations = snapshot["tasks"]
        for tid, obs in observations.items():
            _fields(obs, ("actual_start", "actual_finish", "remaining", "evidence_refs"))
            _integer(obs["remaining"], "remaining")
            _refs(obs["evidence_refs"], "evidence_refs")
            start, finish = obs["actual_start"], obs["actual_finish"]
            if start is not None:
                _require(origin <= _date(start) <= _date(snapshot["as_of"]), "actual start outside plan/snapshot range")
            if finish is not None:
                _require(start is not None and _date(start) <= _date(finish) <= _date(snapshot["as_of"]), "invalid actual finish")
                _require(obs["remaining"] == 0 and bool(obs["evidence_refs"]), "completed observation needs zero remaining and evidence")
            else:
                _require(obs["remaining"] > 0 or tasks[tid]["duration"] == 0, "zero remaining is not completion evidence")
        for tid, obs in observations.items():
            if obs["actual_start"] is not None:
                for dep in tasks[tid]["depends_on"]:
                    finish = observations[dep["task"]]["actual_finish"]
                    _require(finish is not None and calendar.add(_date(finish), dep["lag"]) <= _date(obs["actual_start"]),
                             "actual start conflicts with FS dependency; reconcile evidence or revise plan")
    early, duration, finished = {}, {}, set()
    successors = {tid: [] for tid in tasks}
    for tid in order:
        task = tasks[tid]
        obs = observations.get(tid)
        duration[tid] = obs["remaining"] if obs else task["duration"]
        lower = max(0, calendar.distance(origin, _date(task.get("not_before", plan["start"]))))
        if obs:
            lower = max(lower, asof)
        for dep in task["depends_on"]:
            pred = dep["task"]
            successors[pred].append((tid, dep["lag"]))
            lower = max(lower, early[pred] + duration[pred] + dep["lag"])
        if obs and obs["actual_finish"] is not None:
            finished.add(tid)
            early[tid] = calendar.distance(origin, _date(obs["actual_finish"]))
        else:
            early[tid] = lower
    end = max(early[t] + duration[t] for t in tasks)
    late = {}
    for tid in reversed(order):
        late[tid] = min((late[n] - lag for n, lag in successors[tid]), default=end) - duration[tid]
    rows = []
    for tid in order:
        es, ef = early[tid], early[tid] + duration[tid]
        rows.append({"id": tid, "start": calendar.add(origin, es).isoformat(), "finish": calendar.add(origin, ef).isoformat(),
                     "duration": duration[tid], "early_start": es, "early_finish": ef, "late_start": late[tid],
                     "late_finish": late[tid]+duration[tid], "total_float": late[tid]-es,
                     "critical": late[tid] == es and tid not in finished, "observed_complete": tid in finished})
    critical = {row["id"] for row in rows if row["critical"]}
    edges = sorted([p, n] for p in critical for n, lag in successors[p] if n in critical and early[p]+duration[p]+lag == early[n])
    return {"mode": "forecast" if snapshot else "plan", "finish": calendar.add(origin, end).isoformat(), "duration": end,
            "observations": snapshot,
            "tasks": rows, "critical_tasks": sorted(critical), "critical_edges": edges}


def _label(value):
    # User text cannot inject Mermaid directives, HTML, fences or metadata.
    return re.sub(r"[\r\n:;,#`<>%{}]", " ", value).strip()


def mermaid(plan, result):
    tasks = {t["id"]: t for t in plan["tasks"]}
    lines = ["```mermaid", "gantt", f"    title {_label(plan['plan_id'])} / {plan['kind']} / {result['mode']}", "    dateFormat YYYY-MM-DD", "    axisFormat %Y-%m-%d"]
    snapshot = result.get("observations")
    if snapshot:
        lines.append("    section Actual observations")
        for index, (tid, obs) in enumerate(sorted(snapshot["tasks"].items())):
            if obs["actual_start"] is not None:
                end = obs["actual_finish"] or snapshot["as_of"]
                tags = "done" if obs["actual_finish"] else "active"
                if end == obs["actual_start"]:
                    tags += ", milestone"
                    end = "0d"
                lines.append(f"    {_label(tasks[tid]['label'])} observed :{tags}, a{index}, {obs['actual_start']}, {end}")
        lines.append("    section Remaining forecast")
    else:
        lines.append("    section Planned")
    for index, row in enumerate(result["tasks"]):
        if row["observed_complete"]:
            continue
        tags = (["crit"] if row["critical"] else []) + (["milestone"] if row["duration"] == 0 else [])
        metadata = tags + [f"t{index}", row["start"], "0d" if row["duration"] == 0 else row["finish"]]
        lines.append(f"    {_label(tasks[row['id']]['label'])} :{', '.join(metadata)}")
    return "\n".join(lines + ["```", ""])


def compare(before, after):
    """Compare plan/forecast results without implying causality or approval."""
    left = {t["id"]: t for t in before["tasks"]}
    right = {t["id"]: t for t in after["tasks"]}
    return {"finish_delta_calendar_days": (_date(after["finish"]) - _date(before["finish"])).days,
            "added": sorted(right.keys()-left.keys()), "removed": sorted(left.keys()-right.keys()),
            "changed": {t: {k: [left[t][k], right[t][k]] for k in left[t] if left[t][k] != right[t][k]} for t in sorted(left.keys() & right.keys()) if left[t] != right[t]},
            "critical_before": before["critical_tasks"], "critical_after": after["critical_tasks"]}


def compare_plans(before, after):
    """Include semantic task/trace differences even when dates do not move."""
    left = {t["id"]: t for t in before["tasks"]}
    right = {t["id"]: t for t in after["tasks"]}
    result = compare(calculate(before), calculate(after))
    result["task_changes"] = {t: {k: [left[t].get(k), right[t].get(k)] for k in sorted(left[t].keys() | right[t].keys()) if left[t].get(k) != right[t].get(k)} for t in sorted(left.keys() & right.keys()) if left[t] != right[t]}
    result["plan_changes"] = {k:[before.get(k), after.get(k)] for k in sorted(before.keys() | after.keys()) if k != "tasks" and before.get(k) != after.get(k)}
    return result


def validate_impact_notification(value):
    """Receiver-owned Brownfield -> PM wire contract; proposed data only."""
    _fields(value, ("schema", "notification_id", "source_revision", "previous_revision", "reason", "requirement_xids", "evidence_refs", "decision_refs", "approval_refs", "affected_task_ids", "changes", "decision_activities", "holds"))
    _require(value["schema"] == "brownfield.change_impact/v1", "unsupported impact schema")
    for key in ("notification_id", "reason"):
        _text(value[key], key)
    _integer(value["source_revision"], "source_revision", 1)
    if value["previous_revision"] is not None:
        _integer(value["previous_revision"], "previous_revision", 1)
        _require(value["previous_revision"] < value["source_revision"], "revision order invalid")
    for key in ("requirement_xids", "evidence_refs", "decision_refs", "approval_refs", "affected_task_ids"):
        _refs(value[key], key)
    for key in ("changes", "decision_activities", "holds"):
        _require(isinstance(value[key], list), f"{key}: list required")
    for change in value["changes"]:
        _fields(change, ("section", "item_id", "kind", "changed_fields", "before", "after", "reason", "evidence_refs", "decision_refs"))
        _require(change["section"] in ("requirements", "confirmations", "approach"), "invalid impact section")
        _require(change["kind"] in ("added", "modified", "removed"), "invalid change kind")
        for key in ("item_id", "reason"):
            _text(change[key], key)
        for key in ("changed_fields", "evidence_refs", "decision_refs"):
            _refs(change[key], key)
        _require(all(change[k] is None or isinstance(change[k], dict) for k in ("before", "after")), "change payload must be object or null")
        _require((change["kind"] != "added" or change["before"] is None and isinstance(change["after"], dict)) and
                 (change["kind"] != "removed" or isinstance(change["before"], dict) and change["after"] is None) and
                 (change["kind"] != "modified" or isinstance(change["before"], dict) and isinstance(change["after"], dict)), "change payload does not match kind")
    common = ("id", "requirement_xids", "evidence_refs", "decision_refs", "owner", "status")
    for kind, extra, status in (("decision_activities", ("knowledge_requirement_id", "question", "method", "expected_evidence", "decision_ref"), "proposed"),
                                ("holds", ("reason", "next_action", "resolution_point"), "open")):
        for item in value[kind]:
            _fields(item, common + extra)
            _require(item["status"] == status, "notification cannot approve activities or resolve holds")
            for key in ("requirement_xids", "evidence_refs", "decision_refs"):
                _refs(item[key], key)
            for key in ("id", "owner") + extra:
                _text(item[key], key)
    return value


def assess_impact(plan, notification):
    """Report direct and dependent scope; no schedule or readiness mutation."""
    tasks, order, _ = validate_plan(plan)
    validate_impact_notification(notification)
    refs = set(notification["requirement_xids"])
    refs.update(ref for item in notification["decision_activities"] + notification["holds"] for ref in item["requirement_xids"])
    explicit = set(notification["affected_task_ids"])
    direct = {tid for tid,t in tasks.items() if tid in explicit or refs.intersection(t["requirement_xids"])}
    affected = set(direct)
    for tid in order:
        if any(d["task"] in affected for d in tasks[tid]["depends_on"]):
            affected.add(tid)
    matched_refs = {ref for t in tasks.values() for ref in t["requirement_xids"] if ref in refs}
    return {"schema":"project_management.impact_assessment/v1", "notification_id":notification["notification_id"],
            "plan_id":plan["plan_id"], "kind":plan["kind"], "direct_tasks":sorted(direct), "dependent_tasks":sorted(affected-direct),
            "unmapped_task_ids":sorted(explicit-tasks.keys()), "unmapped_requirement_xids":sorted(refs-matched_refs),
            "decision_activities":notification["decision_activities"], "holds":notification["holds"],
            "reason":notification["reason"], "evidence_refs":notification["evidence_refs"], "decision_refs":notification["decision_refs"],
            "approval_refs":notification["approval_refs"], "schedule_changed":False, "readiness":"not_evaluated",
            "next_action":"Route Decision investigation and affected Execution Holds to their owners; approve a plan revision before changing the authorized schedule."}


def _bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+"\n").encode("utf-8")


def _hash(value):
    return hashlib.sha256(value).hexdigest()


@contextmanager
def _lock(root):
    root.mkdir(parents=True, exist_ok=True)
    lock = root / ".schedule.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ScheduleError("history locked; inspect owner before recovering a stale lock") from exc
    os.close(fd)
    try:
        yield
    finally:
        lock.unlink()


def read_history(root):
    root = Path(root).resolve()
    index = root / "gantt-history.json"
    if not index.exists():
        return {"schema_version": 1, "entries": [], "current": {}, "approved": {}, "baselines": {}}
    history = json.loads(index.read_text(encoding="utf-8"))
    _fields(history, ("schema_version", "entries", "current", "approved", "baselines"))
    _require(history["schema_version"] == 1, "unsupported history schema")
    expected_current, expected_approved, expected_baselines = {}, {}, {}
    for entry in history["entries"]:
        for rel, digest in entry["files"].items():
            path = (root / rel).resolve()
            _require(path.is_relative_to(root) and path.is_file(), "missing or escaping history file")
            _require(_hash(path.read_bytes()) == digest, f"immutable history changed: {rel}")
        _require(entry["source"] in entry["files"] and entry["chart"] in entry["files"], "unbound history artifact")
        document = json.loads((root / entry["source"]).read_text(encoding="utf-8"))
        _require(document["record"] == {k:v for k,v in entry.items() if k != "files"}, "history metadata differs from immutable record")
        _require(entry["plan_hash"] == _hash(_bytes(document["plan"])), "history plan hash mismatch")
        key = entry["plan"]
        _require(entry["previous"] == expected_current.get(key), "broken history chain")
        expected_current[key] = entry["source"]
        if entry["type"] == "revision" and entry["approval"]["status"] == "approved":
            expected_approved[key] = entry["source"]
        if entry["baseline"]:
            _require(entry["type"] == "revision" and entry["approval"]["status"] == "approved", "unapproved baseline")
            expected_baselines.setdefault(key, []).append(entry["source"])
    _require(history["current"] == expected_current and history["approved"] == expected_approved and history["baselines"] == expected_baselines, "history pointers differ from immutable records")
    return history


def save(root, plan, metadata, *, snapshot=None, baseline=False):
    """Create immutable revision or observation files; atomically advance one index.

    baseline=True requires recorded approval, never synthesizes it. Cooperating
    writers use an exclusive lock. Filesystem permissions/backup remain external.
    """
    result = calculate(plan, snapshot)
    _fields(metadata, ("created_at", "reason", "requirement_xids", "evidence_refs", "decision_refs", "judgment", "approval"))
    for name in ("created_at", "reason", "judgment"):
        _text(metadata[name], name)
    try:
        timestamp = datetime.fromisoformat(metadata["created_at"])
        _require(timestamp.tzinfo is not None, "created_at requires timezone")
    except ValueError as exc:
        raise ScheduleError("created_at requires ISO timestamp with timezone") from exc
    for name in ("requirement_xids", "evidence_refs", "decision_refs"):
        _refs(metadata[name], name)
    approval = metadata["approval"]
    _fields(approval, ("status", "actor", "record_ref"))
    _require(approval["status"] in ("proposed", "approved", "rejected"), "invalid approval status")
    for key in ("actor", "record_ref"):
        if approval[key] is not None:
            _text(approval[key], f"approval {key}")
    if approval["status"] != "proposed":
        _text(approval["actor"], "approval actor")
        _text(approval["record_ref"], "approval record")
    _require(not baseline or snapshot is None and approval["status"] == "approved", "baseline requires approved plan revision")
    root = Path(root).resolve()
    with _lock(root):
        history = read_history(root)
        key = f"{plan['kind']}/{plan['plan_id']}"
        entries = [e for e in history["entries"] if e["plan"] == key]
        revisions = [e for e in entries if e["type"] == "revision"]
        if snapshot is not None:
            _require(bool(revisions), "save plan revision before observations")
            _require(revisions[-1]["plan_hash"] == _hash(_bytes(plan)), "observation cannot change plan; save a revision first")
        sequence = len(entries) + 1
        revision = len(revisions) if snapshot is not None else len(revisions) + 1
        stem = f"r{revision:03d}" + (f"-s{sequence:03d}" if snapshot is not None else "")
        source = f"{key}/plan-{stem}.json"
        chart = f"{key}/gantt-{stem}.md"
        entry = {"plan": key, "type": "snapshot" if snapshot is not None else "revision", "revision": revision,
                 "sequence": sequence, "source": source, "chart": chart, "previous": entries[-1]["source"] if entries else None,
                 "plan_hash": _hash(_bytes(plan)), "baseline": baseline, **metadata}
        document = {"plan": plan, "snapshot": snapshot, "calculation": result, "record": dict(entry)}
        contents = {source: _bytes(document), chart: (f"# {plan['kind']} {plan['plan_id']} {stem}\n\n"+mermaid(plan,result)).encode("utf-8")}
        entry["files"] = {p:_hash(b) for p,b in contents.items()}
        history["entries"].append(entry)
        history["current"][key] = source
        if snapshot is None and approval["status"] == "approved":
            history["approved"][key] = source
        if baseline:
            history["baselines"].setdefault(key, []).append(source)
        created = []
        temporary = None
        try:
            for relative, body in contents.items():
                path = root / relative
                _require(path.parent.resolve().is_relative_to(root), "escaping history directory")
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as stream:
                    created.append(path)
                    stream.write(body)
                    stream.flush()
                    os.fsync(stream.fileno())
            with tempfile.NamedTemporaryFile(dir=root, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(_bytes(history))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, root / "gantt-history.json")
        except BaseException:
            for path in created:
                path.unlink()
            raise
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        return entry


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="JSON plan input")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--save", type=Path, help="authorized local history destination")
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8")) if args.snapshot else None
        if args.save:
            _require(args.metadata is not None, "--save requires --metadata")
            value = save(args.save, plan, json.loads(args.metadata.read_text(encoding="utf-8")), snapshot=snapshot, baseline=args.baseline)
        else:
            _require(not args.baseline and args.metadata is None, "metadata/baseline require --save")
            value = calculate(plan, snapshot)
        print(_bytes(value).decode("utf-8"), end="")
    except (ScheduleError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"schedule refused: {exc}\n")


if __name__ == "__main__":
    main()

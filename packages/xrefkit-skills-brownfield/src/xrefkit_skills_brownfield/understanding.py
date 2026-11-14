"""Compare explicit understanding records; never infer approval from evidence.

The producer owns technical understanding and proposed investigation activities.
Project Management owns notification acceptance, scheduling, CPM and history.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import re
import tempfile

SCHEMA = "brownfield.understanding/v1"
SECTIONS = {"requirements": "要求事項", "confirmations": "確認事項", "approach": "進め方"}
REFS = ("evidence_refs", "decision_refs", "approval_refs")


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value


def _list(value, field):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise ValueError(f"{field} must be a string list")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} contains duplicates")
    return value


def _rows(value, field):
    if not isinstance(value, list) or any(not isinstance(v, dict) for v in value):
        raise ValueError(f"{field} must be an object list")
    ids = [_text(v.get("id"), field + ".id") for v in value]
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", v) for v in ids):
        raise ValueError(f"{field} ids must be portable identifiers")
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate {field} id")
    return value


def _fields(row, required, optional=()):
    if set(row) - set(required) - set(optional) or set(required) - set(row):
        raise ValueError(f"unexpected or missing fields: {sorted(set(row) ^ set(required))}")


def validate_understanding(document):
    """Validate an explicit snapshot and return a detached normalized copy.

    Knowledge sufficiency is an input judgment with evidence and owner, not a
    conclusion guessed by this deterministic program. Missing scope stays open.
    """
    if not isinstance(document, dict):
        raise ValueError("understanding must be an object")
    doc = deepcopy(document)
    _fields(doc, ("schema", "project_id", "revision", "recorded_at", "reason", *REFS,
                  *SECTIONS, "knowledge_requirements", "artifacts"))
    if doc["schema"] != SCHEMA:
        raise ValueError("unsupported understanding schema")
    _text(doc["project_id"], "project_id")
    _text(doc["reason"], "reason")
    if type(doc["revision"]) is not int or doc["revision"] < 1:
        raise ValueError("revision must be a positive integer")
    try:
        timestamp = datetime.fromisoformat(doc["recorded_at"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("timezone required")
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError("recorded_at must be an ISO timestamp with timezone") from error
    for key in REFS:
        _list(doc[key], key)
    common = ("id", "text", "status", "owner", "reason", "requirement_xids", *REFS,
              "artifact_refs", "affected_task_ids")
    for section in SECTIONS:
        for row in _rows(doc[section], section):
            _fields(row, common)
            for key in ("text", "owner", "reason"):
                _text(row[key], key)
            for key in ("requirement_xids", *REFS, "artifact_refs", "affected_task_ids"):
                _list(row[key], key)
            if not row["requirement_xids"] or any(not re.fullmatch(r"[A-F0-9]{12}", x) for x in row["requirement_xids"]):
                raise ValueError("items require explicit 12-character requirement XIDs")
            allowed = {"requirements": {"candidate", "confirmed", "withdrawn"},
                       "confirmations": {"open", "answered", "conflict"},
                       "approach": {"proposed", "approved", "completed", "hold"}}[section]
            if not isinstance(row["status"], str) or row["status"] not in allowed:
                raise ValueError(f"invalid {section} status")
            if row["status"] in {"confirmed", "approved"} and not row["approval_refs"]:
                raise ValueError("confirmed/approved item needs explicit approval references")
            if row["status"] in {"answered", "completed"} and not row["evidence_refs"]:
                raise ValueError("answered/completed item needs evidence")
    xids = {x for r in doc["requirements"] for x in r["requirement_xids"]}
    for section in ("confirmations", "approach"):
        for row in doc[section]:
            if not set(row["requirement_xids"]) <= xids:
                raise ValueError("orphan requirement link")
    for row in _rows(doc["artifacts"], "artifacts"):
        _fields(row, ("id", "ref", "revision", "requirement_xids", "evidence_refs"))
        for key in ("ref", "revision"):
            _text(row[key], key)
        for key in ("requirement_xids", "evidence_refs"):
            _list(row[key], key)
        if not row["requirement_xids"] or not set(row["requirement_xids"]) <= xids:
            raise ValueError("artifact must trace to an existing requirement")
    artifacts = {row["id"] for row in doc["artifacts"]}
    for section in SECTIONS:
        for row in doc[section]:
            if not set(row["artifact_refs"]) <= artifacts:
                raise ValueError("unknown artifact reference")
            for artifact in doc["artifacts"]:
                if artifact["id"] in row["artifact_refs"] and not set(artifact["requirement_xids"]) & set(row["requirement_xids"]):
                    raise ValueError("artifact and item requirement scopes disagree")
    kr_fields = ("id", "requirement_xids", "question", "query", "needed_for", "status",
                 "knowledge_refs", "evidence_refs", "decision_refs", "owner", "reason",
                 "method", "expected_evidence", "decision_ref", "resolution_point")
    for row in _rows(doc["knowledge_requirements"], "knowledge_requirements"):
        _fields(row, kr_fields)
        for key in ("question", "query", "needed_for", "owner", "reason", "resolution_point"):
            _text(row[key], key)
        for key in ("requirement_xids", "knowledge_refs", "evidence_refs", "decision_refs"):
            _list(row[key], key)
        if not row["requirement_xids"] or not set(row["requirement_xids"]) <= xids:
            raise ValueError("Knowledge Requirement must trace to an existing requirement")
        if not isinstance(row["status"], str) or row["status"] not in {"open", "satisfied", "stale", "conflict"}:
            raise ValueError("invalid Knowledge Requirement status")
        if row["status"] == "satisfied" and not (row["knowledge_refs"] and row["evidence_refs"]):
            raise ValueError("satisfied Knowledge Requirement needs knowledge and evidence references")
        for key in ("method", "expected_evidence", "decision_ref"):
            if row[key] is not None:
                _text(row[key], key)
    return doc


def analyze_knowledge_requirements(document):
    """Expose declared gaps and derive activities only from supplied methods."""
    doc = validate_understanding(document)
    result = {"satisfied": [], "gaps": [], "decision_activities": [], "holds": []}
    for row in sorted(doc["knowledge_requirements"], key=lambda r: r["id"]):
        if row["status"] == "satisfied":
            result["satisfied"].append(deepcopy(row))
            continue
        missing = [key for key in ("method", "expected_evidence", "decision_ref") if row[key] is None]
        result["gaps"].append({**deepcopy(row), "missing_plan_fields": missing})
        if not missing:
            result["decision_activities"].append({
                "id": "investigate-" + row["id"], "knowledge_requirement_id": row["id"],
                "question": row["question"], "method": row["method"],
                "expected_evidence": row["expected_evidence"], "decision_ref": row["decision_ref"],
                "owner": row["owner"], "status": "proposed",
                **{key: deepcopy(row[key]) for key in ("requirement_xids", "evidence_refs", "decision_refs")},
            })
        result["holds"].append({
            "id": "knowledge-" + row["id"], "reason": row["reason"], "owner": row["owner"],
            "next_action": ("Supply " + ", ".join(missing)) if missing else row["method"],
            "resolution_point": row["resolution_point"], "status": "open",
            **{key: deepcopy(row[key]) for key in ("requirement_xids", "evidence_refs", "decision_refs")},
        })
    return result


def _section_rows(doc):
    result = {section: {row["id"]: row for row in doc[section]} for section in SECTIONS}
    # Knowledge Requirement and artifact changes are visible in the same three
    # user-facing groups, without pretending they are approved requirements.
    for row in doc["knowledge_requirements"]:
        result["confirmations"]["knowledge:" + row["id"]] = row
    for row in doc["artifacts"]:
        result["requirements"]["artifact:" + row["id"]] = row
    return result


def compare_understanding(previous, current):
    """Deterministically compare supplied records, including deletion evidence."""
    current = validate_understanding(current)
    previous = validate_understanding(previous) if previous is not None else None
    if previous is not None:
        if previous["project_id"] != current["project_id"]:
            raise ValueError("cannot compare different projects")
        if previous["revision"] >= current["revision"]:
            raise ValueError("new understanding revision must advance")
        if datetime.fromisoformat(previous["recorded_at"].replace("Z", "+00:00")) > datetime.fromisoformat(current["recorded_at"].replace("Z", "+00:00")):
            raise ValueError("new understanding timestamp must not precede previous revision")
    before = _section_rows(previous) if previous else {section: {} for section in SECTIONS}
    after = _section_rows(current)
    changes = []
    for section in SECTIONS:
        for item_id in sorted(before[section].keys() | after[section].keys()):
            old, new = before[section].get(item_id), after[section].get(item_id)
            if old == new:
                continue
            fields = sorted(key for key in (old or {}).keys() | (new or {}).keys()
                            if (old or {}).get(key) != (new or {}).get(key))
            changes.append({"section": section, "item_id": item_id,
                            "kind": "added" if old is None else "removed" if new is None else "modified",
                            "changed_fields": fields, "before": deepcopy(old), "after": deepcopy(new),
                            "reason": new.get("reason", current["reason"]) if new else current["reason"],
                            "evidence_refs": sorted(set(current["evidence_refs"] + (new or old).get("evidence_refs", []))),
                            "decision_refs": sorted(set(current["decision_refs"] + (new or old).get("decision_refs", [])))})
    return changes


def analyze_understanding(current, previous=None):
    """Produce traceable technical findings and a proposed PM notification."""
    current = validate_understanding(current)
    changes = compare_understanding(previous, current)
    knowledge = analyze_knowledge_requirements(current)
    affected_rows = [row for change in changes for row in (change["before"], change["after"]) if row]
    affected_rows += knowledge["gaps"]
    union = lambda key: sorted({value for row in affected_rows for value in row.get(key, [])})
    notification = {
        "schema": "brownfield.change_impact/v1",
        "notification_id": f"{current['project_id']}-understanding-r{current['revision']:03d}",
        "source_revision": current["revision"],
        "previous_revision": previous["revision"] if previous else None,
        "reason": current["reason"], "requirement_xids": union("requirement_xids"),
        "affected_task_ids": union("affected_task_ids"), "changes": changes,
        "decision_activities": knowledge["decision_activities"], "holds": knowledge["holds"],
        **{key: sorted(set(current[key]) | set(union(key))) for key in REFS},
    }
    trace = []
    for requirement in sorted(current["requirements"], key=lambda r: r["id"]):
        xids = set(requirement["requirement_xids"])
        trace.append({"requirement_id": requirement["id"], "requirement_xids": sorted(xids),
                      "artifacts": [deepcopy(a) for a in current["artifacts"] if xids & set(a["requirement_xids"])],
                      "confirmations": [r["id"] for r in current["confirmations"] if xids & set(r["requirement_xids"])],
                      "approach": [r["id"] for r in current["approach"] if xids & set(r["requirement_xids"])],
                      "knowledge_requirements": [r["id"] for r in current["knowledge_requirements"] if xids & set(r["requirement_xids"])]})
    return {"schema": "brownfield.analysis/v1", "project_id": current["project_id"],
            "revision": current["revision"], "sections": {s: deepcopy(current[s]) for s in SECTIONS},
            "changes": changes, "knowledge_requirement_analysis": knowledge,
            "traceability": trace, "notification": notification}


def render_report(analysis):
    """Render exactly three headings while retaining reasons and evidence."""
    def inline(value):
        return str(value).replace("\r", " ").replace("\n", " ")
    lines = []
    for section, label in SECTIONS.items():
        lines += [f"## {label}", ""]
        content_start = len(lines)
        rows = analysis["sections"][section]
        for row in rows:
            lines.append(f"- {inline(row['id'])} [{row['status']}] ({', '.join(row['requirement_xids'])}): {inline(row['text'])}")
            lines.append(f"  - 変更理由: {inline(row['reason'])}／根拠: {', '.join(map(inline, row['evidence_refs'])) or '未記録'}／判断: {', '.join(map(inline, row['decision_refs'])) or '未記録'}／承認: {', '.join(map(inline, row['approval_refs'])) or '未記録'}")
        for change in analysis["changes"]:
            if change["section"] == section:
                xids = sorted({x for row in (change["before"], change["after"]) if row for x in row.get("requirement_xids", [])})
                lines.append(f"- 変更 {inline(change['item_id'])} ({change['kind']}; {', '.join(xids)}): {', '.join(change['changed_fields'])}。理由: {inline(change['reason'])}／根拠: {', '.join(map(inline, change['evidence_refs'])) or '未記録'}")
        if section == "confirmations":
            for gap in analysis["knowledge_requirement_analysis"]["gaps"]:
                lines.append(f"- Knowledge Requirement {inline(gap['id'])} ({', '.join(gap['requirement_xids'])}): {inline(gap['question'])}。状態: {gap['status']}／担当: {inline(gap['owner'])}／解消点: {inline(gap['resolution_point'])}／理由: {inline(gap['reason'])}／根拠: {', '.join(map(inline, gap['evidence_refs'])) or '未記録'}")
                if gap["missing_plan_fields"]:
                    lines.append(f"  - 計画に不足: {', '.join(gap['missing_plan_fields'])}")
        if section == "approach":
            for activity in analysis["knowledge_requirement_analysis"]["decision_activities"]:
                basis = next(g for g in analysis["knowledge_requirement_analysis"]["gaps"] if g["id"] == activity["knowledge_requirement_id"])
                lines.append(f"- 調査・検証案 {inline(activity['id'])} ({', '.join(activity['requirement_xids'])}): {inline(activity['method'])}／必要な証拠: {inline(activity['expected_evidence'])}／判断: {inline(activity['decision_ref'])}／担当: {inline(activity['owner'])}／理由: {inline(basis['reason'])}／根拠: {', '.join(map(inline, basis['evidence_refs'])) or '未記録'}")
        if len(lines) == content_start:
            lines.append("- 記録なし。")
        lines.append("")
    return "\n".join(lines)


def save_analysis(directory, current, previous=None):
    """Persist exact producer input/output as one create-only revision bundle.

    Identical retries return the same file. A reused revision with different
    bytes is rejected. This is technical evidence, not PM plan/history storage.
    """
    current = validate_understanding(current)
    previous = validate_understanding(previous) if previous is not None else None
    result = analyze_understanding(current, previous)
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"understanding-r{current['revision']:03d}.json"
    body = (json.dumps({"current": current, "previous": previous, "analysis": result},
                       ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=".understanding-", dir=root)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            # Same-directory link publishes a completely written inode while
            # refusing an existing destination, including another writer.
            os.link(temporary, target)
        except FileExistsError:
            if target.is_symlink() or target.read_bytes() != body:
                raise ValueError("understanding revision already exists with different content") from None
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target


def _load(path):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("current")
    parser.add_argument("--previous")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable analysis instead of the standard three sections")
    parser.add_argument("--save", help="Explicit project-owned directory for an immutable source/analysis revision")
    args = parser.parse_args(argv)
    try:
        current, previous = _load(args.current), _load(args.previous) if args.previous else None
        result = analyze_understanding(current, previous)
        if args.save:
            save_analysis(args.save, current, previous)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_report(result))
        return 0
    except (ValueError, OSError) as error:
        parser.exit(2, f"understanding rejected: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())

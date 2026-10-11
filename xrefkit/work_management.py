"""Portable local work records. No remote service or workflow transition calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path, PureWindowsPath
from urllib.parse import urlsplit

MAX_BYTES = 1024 * 1024
MAX_RECORDS = 200
MAX_TASKS = 500
WRITER_FIELDS = {"observation_revision", "observation_history", "report_sha256"}
PLAN_KEYS = {"schema_version", "workspace_id", "repository_root", "plan_id", "plan_revision", "title", "source", "approval_status", "approval_evidence", "project", "change", "baseline", "stages", "steps", "pbis", "confirmations", "external_refs", "initial_task_ids", "previous_plan_revision", "knowledge_refs", "report_id", "recorded_at"} | WRITER_FIELDS
TASK_KEYS = {"step_id", "title", "stage_id", "dependencies", "status", "status_evidence", "planned_skill", "agent", "completion_criterion", "outputs", "runs", "pbi_ids", "candidate_version", "revalidation_needed", "revalidation_evidence", "impact_status", "validation_records", "judgment_refs", "concern_refs", "predecessor_step_ids", "artifact_refs"}
PLAN_KEYS.add("work_packages")
PACKAGE_KEYS = {"work_package_id", "title", "pbi_id", "purpose", "expected_output", "step_ids", "completion_criterion", "depends_on", "review_owner", "verification"}


def string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def safe_external_url(value: object) -> bool:
    if not isinstance(value, str) or any(ord(char) < 32 for char in value):
        return False
    try:
        parts = urlsplit(value)
        return parts.scheme in {"http", "https"} and bool(parts.hostname) and parts.username is None and parts.password is None
    except ValueError:
        return False


def confined_directory(root: Path, value: object) -> Path | None:
    if not string(value) or Path(value).is_absolute() or PureWindowsPath(value).drive:
        return None
    try:
        directory = (root.resolve() / value).resolve()
        directory.relative_to(root.resolve())
        return directory if directory.is_dir() else None
    except (OSError, ValueError, RuntimeError):
        return None


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> object:
    with path.open("rb") as stream:
        body = stream.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("1 MiB record limit exceeded")
    return json.loads(body.decode("utf-8-sig"), object_pairs_hook=_unique)


def _object(value, allowed, required, label, issues):
    if not isinstance(value, dict):
        issues.append(f"{label}: object required")
        return False
    unknown = set(value) - allowed
    if unknown:
        issues.append(f"{label}: unsupported fields: {', '.join(sorted(unknown))}")
    for field in required:
        if not string(value.get(field)):
            issues.append(f"{label}.{field}: nonempty string required")
    return True


def _optional_strings(record, fields, label, issues):
    for field in fields:
        if record.get(field) is not None and not string(record[field]):
            issues.append(f"{label}.{field}: string or null required")


def _strings(record, field, label, issues, required=False):
    value = record.get(field)
    if field not in record and not required:
        return []
    if not isinstance(value, list) or not all(string(item) for item in value):
        issues.append(f"{label}.{field}: string array required")
        return []
    if len(value) > MAX_TASKS:
        issues.append(f"{label}.{field}: record limit exceeded")
    return value


def _records(record, field, label, issues, required=False, limit=MAX_RECORDS):
    value = record.get(field)
    if field not in record and not required:
        return []
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        issues.append(f"{label}.{field}: object array required")
        return []
    if len(value) > limit:
        issues.append(f"{label}.{field}: record limit {limit} exceeded")
        return []
    return value


def _time(value, label, issues):
    if value is None:
        return
    try:
        stamp = datetime.fromisoformat(value)
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError("timezone missing")
    except (ValueError, TypeError):
        issues.append(f"{label}: timezone-aware ISO date required")


def _ids(records, field, label, issues):
    values = [item[field] for item in records if string(item.get(field))]
    if len(values) != len(set(values)):
        issues.append(f"{label}: duplicate {field}")
    return set(values)


def _artifact_records(record, field, label, issues):
    for artifact in _records(record, field, label, issues):
        _object(artifact, {"kind", "path", "revision", "source", "recorded_at"}, {"path"}, field, issues)
        _optional_strings(artifact, {"kind", "revision", "source"}, field, issues)
        _time(artifact.get("recorded_at"), field + ".recorded_at", issues)


def validate_workspace(value: object) -> list[str]:
    issues = []
    if _object(value, {"schema_version", "workspace_id", "title", "workspace_root"}, {"workspace_id", "title", "workspace_root"}, "workspace", issues):
        if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
            issues.append("unsupported workspace schema_version")
    return issues


def load_workspaces(root: Path) -> list[dict]:
    rows = []
    directory = root.resolve() / "work/workspaces"
    if not directory.exists():
        return rows
    for path in sorted(directory.glob("*.json"))[:MAX_RECORDS + 1]:
        row = {"file": str(path.relative_to(root.resolve())), "workspace": None, "issues": []}
        try:
            path.resolve().relative_to(root.resolve())
            value = read_json(path)
            row["issues"] = validate_workspace(value)
            if not row["issues"]:
                row["workspace"] = value
                if confined_directory(root, value["workspace_root"]) is None:
                    row["issues"].append("workspace root unavailable inside repository")
        except (OSError, ValueError, UnicodeError, RecursionError) as exc:
            row["issues"] = [str(exc)]
        rows.append(row)
    if len(rows) > MAX_RECORDS:
        return [{"file": "work/workspaces", "workspace": None, "issues": ["workspace record limit exceeded"]}]
    for row in rows:
        value = row["workspace"]
        if value and sum(other["workspace"] is not None and other["workspace"]["workspace_id"] == value["workspace_id"] for other in rows) > 1:
            row["issues"].append("duplicate workspace identity")
        if value and sum(other["workspace"] is not None and confined_directory(root, other["workspace"]["workspace_root"]) == confined_directory(root, value["workspace_root"]) for other in rows) > 1:
            row["issues"].append("ambiguous workspace root")
        if value and not row["issues"]:
            try:
                scope = (confined_directory(root, value["workspace_root"]) / "work/sessions").resolve()
            except (OSError, RuntimeError):
                row["issues"].append("workspace sessions scope cannot be resolved")
                continue
            for other in rows:
                candidate = other["workspace"]
                candidate_root = confined_directory(root, candidate["workspace_root"]) if candidate else None
                if candidate_root is None or other is row:
                    continue
                try:
                    other_scope = (candidate_root / "work/sessions").resolve()
                except (OSError, RuntimeError):
                    continue
                if scope == other_scope or scope in other_scope.parents or other_scope in scope.parents:
                    row["issues"].append("overlapping workspace session scope")
                    break
    return rows


def validate_plan_v2(plan: object, *, stored: bool = False) -> list[str]:
    from xrefkit.plan_observation import validate_plan
    issues = []
    if not _object(plan, PLAN_KEYS, {"workspace_id", "repository_root", "plan_id", "plan_revision", "title", "source", "report_id"}, "plan", issues):
        return issues
    if type(plan.get("schema_version")) is not int or plan["schema_version"] != 2:
        issues.append("unsupported plan schema_version")
    _time(plan.get("recorded_at"), "plan.recorded_at", issues)
    _optional_strings(plan, {"approval_status", "approval_evidence", "previous_plan_revision"}, "plan", issues)
    if plan.get("initial_task_ids") is not None:
        initial = _strings(plan, "initial_task_ids", "plan", issues)
        if len(initial) != len(set(initial)):
            issues.append("initial_task_ids: duplicate identity")
    _strings(plan, "knowledge_refs", "plan", issues)
    definitions = {
        "project": ({"project_id", "title"}, {"project_id", "title"}),
        "change": ({"change_id", "title", "scope_in", "scope_out", "assumptions", "constraints", "exit_criteria", "decision_owner", "review_owner", "acceptance_owner", "quality_conditions"}, {"change_id", "title"}),
        "baseline": ({"baseline_id", "source", "docs_revision", "code_revision", "acquired_at", "mismatches", "artifacts"}, {"baseline_id"}),
    }
    for field, (allowed, required) in definitions.items():
        record = plan.get(field)
        if _object(record, allowed, required, field, issues):
            if field == "baseline":
                _optional_strings(record, {"source", "docs_revision", "code_revision"}, field, issues)
                _time(record.get("acquired_at"), "baseline.acquired_at", issues)
                _strings(record, "mismatches", field, issues)
                _artifact_records(record, "artifacts", field, issues)
            elif field == "change":
                _optional_strings(record, {"scope_in", "scope_out", "assumptions", "constraints", "exit_criteria", "decision_owner", "review_owner", "acceptance_owner"}, field, issues)
                for condition in _records(record, "quality_conditions", field, issues):
                    _object(condition, {"condition_id", "title", "verification_method", "reviewer", "evidence_refs"}, {"condition_id", "title"}, "quality condition", issues)
                    _optional_strings(condition, {"verification_method", "reviewer"}, "quality condition", issues)
                    _strings(condition, "evidence_refs", "quality condition", issues)
    stages = _records(plan, "stages", "plan", issues, required=True)
    pbis = _records(plan, "pbis", "plan", issues, required=True)
    confirmations = _records(plan, "confirmations", "plan", issues, required=True)
    external = _records(plan, "external_refs", "plan", issues, required=True)
    steps = _records(plan, "steps", "plan", issues, required=True, limit=MAX_TASKS)
    for stage in stages:
        _object(stage, {"stage_id", "title"}, {"stage_id", "title"}, "stage", issues)
    stage_ids = _ids(stages, "stage_id", "stages", issues)
    pbi_ids = _ids(pbis, "pbi_id", "pbis", issues)
    step_ids = _ids(steps, "step_id", "steps", issues)
    if "work_packages" in plan:
        _validate_packages(plan, steps, step_ids, pbi_ids, issues)
    external_ids = _ids(external, "external_ref_id", "external refs", issues)
    _ids(confirmations, "confirmation_id", "confirmations", issues)
    for ref in external:
        fields = {"external_ref_id", "service", "organization", "project", "item_id", "url", "revision", "type_mapping", "state_mapping", "ownership_ref", "last_read_at", "last_success_at", "sync_status", "pending_summary"}
        _object(ref, fields, {"external_ref_id", "service", "item_id"}, "external ref", issues)
        _optional_strings(ref, fields - {"last_read_at", "last_success_at"}, "external ref", issues)
        if ref.get("url") is not None and not safe_external_url(ref["url"]):
            issues.append("external ref.url: safe http/https URL without credentials required")
        for field in ("last_read_at", "last_success_at"):
            _time(ref.get(field), field, issues)
    for pbi in pbis:
        fields = {"pbi_id", "title", "purpose", "acceptance_criteria", "priority", "acceptance_status", "acceptance_evidence", "owner", "external_ref_ids"}
        _object(pbi, fields, {"pbi_id", "title"}, "PBI", issues)
        _optional_strings(pbi, fields - {"external_ref_ids"}, "PBI", issues)
        for ref_id in _strings(pbi, "external_ref_ids", "PBI", issues):
            if ref_id not in external_ids:
                issues.append(f"PBI: missing external reference {ref_id}")
    legacy_steps = []
    for step in steps:
        _object(step, TASK_KEYS, {"step_id", "title", "stage_id"}, "task", issues)
        if not string(step.get("stage_id")) or step["stage_id"] not in stage_ids:
            issues.append("task: stage reference unavailable")
        for pbi_id in _strings(step, "pbi_ids", "task", issues):
            if pbi_id not in pbi_ids:
                issues.append(f"task: missing PBI {pbi_id}")
        _optional_strings(step, {"candidate_version", "revalidation_evidence", "impact_status"}, "task", issues)
        if step.get("revalidation_needed") is not None and type(step["revalidation_needed"]) is not bool:
            issues.append("task.revalidation_needed: boolean or null required")
        for field in ("judgment_refs", "concern_refs", "predecessor_step_ids"):
            _strings(step, field, "task", issues)
        _artifact_records(step, "artifact_refs", "task", issues)
        dependencies = _records(step, "dependencies", "task", issues, required=True, limit=MAX_TASKS)
        internal = []
        for dependency in dependencies:
            _object(dependency, {"step_id", "kind", "external_ref_id", "evidence_ref"}, {"kind"}, "dependency", issues)
            _optional_strings(dependency, {"step_id", "external_ref_id", "evidence_ref"}, "dependency", issues)
            if dependency.get("kind") == "external":
                if not string(dependency.get("external_ref_id")) or dependency["external_ref_id"] not in external_ids or dependency.get("step_id") is not None:
                    issues.append("external dependency: explicit external reference only required")
            elif string(dependency.get("kind")) and dependency["kind"] in {"mandatory", "optional"}:
                if not string(dependency.get("step_id")) or dependency["step_id"] not in step_ids or dependency.get("external_ref_id") is not None:
                    issues.append("internal dependency: exact task reference required")
                elif string(dependency.get("step_id")):
                    internal.append(dependency["step_id"])
            else:
                issues.append("dependency: unsupported kind")
        for validation in _records(step, "validation_records", "task", issues):
            fields = {"validation_id", "target_version", "environment", "input_data", "expected_result", "result", "reviewer", "recorded_at", "evidence_refs"}
            _object(validation, fields, {"validation_id", "target_version"}, "validation", issues)
            _optional_strings(validation, fields - {"recorded_at", "evidence_refs"}, "validation", issues)
            _time(validation.get("recorded_at"), "validation.recorded_at", issues)
            _strings(validation, "evidence_refs", "validation", issues)
        legacy = {key: step[key] for key in ("step_id", "title", "status", "status_evidence", "planned_skill", "agent", "completion_criterion", "outputs", "runs") if key in step}
        legacy["depends_on"] = internal
        legacy_steps.append(legacy)
    for confirmation in confirmations:
        fields = {"confirmation_id", "question", "reason", "owner", "resolver", "due_at", "step_ids", "version_refs", "impact", "answer", "application", "judgment_refs"}
        _object(confirmation, fields, {"confirmation_id", "question"}, "confirmation", issues)
        _optional_strings(confirmation, {"reason", "owner", "resolver", "impact"}, "confirmation", issues)
        _time(confirmation.get("due_at"), "confirmation.due_at", issues)
        for step_id in _strings(confirmation, "step_ids", "confirmation", issues):
            if step_id not in step_ids:
                issues.append(f"confirmation: missing task {step_id}")
        for field in ("version_refs", "judgment_refs"):
            _strings(confirmation, field, "confirmation", issues)
        for field, allowed, required in (
            ("answer", {"text", "responder", "recorded_at", "evidence_refs"}, {"text"}),
            ("application", {"target_refs", "verified_by", "recorded_at", "evidence_refs"}, set()),
        ):
            record = confirmation.get(field)
            if record is not None and _object(record, allowed, required, field, issues):
                _optional_strings(record, {"responder", "verified_by"} & allowed, field, issues)
                _time(record.get("recorded_at"), field + ".recorded_at", issues)
                _strings(record, "evidence_refs", field, issues)
                if field == "application":
                    _strings(record, "target_refs", field, issues, required=True)
    legacy_plan = {key: plan[key] for key in ("plan_id", "plan_revision", "repository_root", "title", "source", "approval_status", "approval_evidence") if key in plan}
    legacy_plan.update(schema_version=1, steps=legacy_steps)
    issues.extend(validate_plan(legacy_plan))
    revision = plan.get("observation_revision")
    if stored and not WRITER_FIELDS.issubset(plan):
        issues.append("stored snapshot requires observation revision, report fingerprint and history")
    if stored and (type(revision) is not int or revision < 1 or revision > MAX_RECORDS + 1):
        issues.append("stored observation_revision must be a bounded positive integer")
    if stored and (not string(plan.get("report_sha256")) or len(plan["report_sha256"]) != 64):
        issues.append("stored report_sha256 must be a SHA256 fingerprint")
    if revision is not None and (type(revision) is not int or revision < 1 or revision > MAX_RECORDS + 1):
        issues.append("observation_revision: bounded positive integer required")
    history = _records(plan, "observation_history", "plan", issues)
    history_revisions = []
    reports = [plan.get("report_id")]
    for entry in history:
        _object(entry, {"observation_revision", "report_id", "report_sha256", "payload"}, {"report_id", "report_sha256"}, "history", issues)
        prior = entry.get("observation_revision")
        if type(prior) is not int or prior < 1 or (type(revision) is int and prior >= revision):
            issues.append("history: invalid prior observation_revision")
        history_revisions.append(prior)
        reports.append(entry.get("report_id"))
        payload = entry.get("payload")
        if not isinstance(payload, dict) or submitted_hash(payload) != entry.get("report_sha256"):
            issues.append("history: payload fingerprint mismatch")
        elif payload.get("report_id") != entry.get("report_id") or any(payload.get(key) != plan.get(key) for key in ("workspace_id", "plan_id", "plan_revision")):
            issues.append("history: report or plan identity mismatch")
        elif WRITER_FIELDS.intersection(payload):
            issues.append("history: nested writer fields unsupported")
        else:
            prior_issues = validate_plan_v2(payload)
            if prior_issues:
                issues.append("history: invalid submitted payload")
            elif not issues and plan_definition(payload) != plan_definition(plan):
                issues.append("history: plan definition mismatch")
    if len(history_revisions) != len(set(map(str, history_revisions))) or len(reports) != len(set(map(str, reports))):
        issues.append("history: duplicate report or observation revision")
    if plan.get("report_sha256") is not None and plan["report_sha256"] != submitted_hash(plan):
        issues.append("current report fingerprint mismatch")
    if stored and type(revision) is int and 1 <= revision <= MAX_RECORDS + 1 and sorted(history_revisions, key=str) != sorted(range(1, revision), key=str):
        issues.append("history: non-contiguous observation sequence")
    return issues


def submitted_payload(plan: dict) -> dict:
    return {key: value for key, value in plan.items() if key not in WRITER_FIELDS}


def submitted_hash(plan: dict) -> str:
    body = json.dumps(submitted_payload(plan), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def plan_definition(plan: dict) -> dict:
    static_keys = {"workspace_id", "repository_root", "plan_id", "plan_revision", "title", "source", "project", "change", "baseline", "stages", "initial_task_ids", "previous_plan_revision", "knowledge_refs"}
    result = {key: plan[key] for key in static_keys if key in plan}
    static_task = {"step_id", "title", "stage_id", "dependencies", "completion_criterion", "planned_skill", "pbi_ids", "predecessor_step_ids"}
    result["steps"] = [{key: value for key, value in step.items() if key in static_task} for step in plan["steps"]]
    result["pbis"] = [{key: value for key, value in pbi.items() if key not in {"acceptance_status", "acceptance_evidence"}} for pbi in plan["pbis"]]
    if "work_packages" in plan:
        result["work_packages"] = [{key: value for key, value in package.items() if key != "verification"} for package in plan["work_packages"]]
    return result


def _validate_packages(plan, steps, step_ids, pbi_ids, issues):
    packages = _records(plan, "work_packages", "plan", issues, required=True, limit=MAX_TASKS)
    package_ids = _ids(packages, "work_package_id", "work packages", issues)
    memberships = []
    graph = {}
    tasks = {step["step_id"]: step for step in steps if string(step.get("step_id"))}
    for package in packages:
        _object(package, PACKAGE_KEYS, PACKAGE_KEYS - {"step_ids", "depends_on", "verification"}, "work package", issues)
        if not string(package.get("pbi_id")) or package["pbi_id"] not in pbi_ids:
            issues.append("work package: PBI reference unavailable")
        members = _strings(package, "step_ids", "work package", issues, required=True)
        if not members:
            issues.append("work package.step_ids: nonempty membership required")
        memberships.extend(members)
        for member in members:
            if member not in step_ids:
                issues.append(f"work package: missing task {member}")
            elif isinstance(tasks[member].get("pbi_ids"), list) and tasks[member]["pbi_ids"] and package.get("pbi_id") not in tasks[member]["pbi_ids"]:
                issues.append("work package: task PBI association conflicts with package parent")
        dependencies = _strings(package, "depends_on", "work package", issues, required=True)
        if len(dependencies) != len(set(dependencies)):
            issues.append("work package.depends_on: duplicate dependency")
        for dependency in dependencies:
            if dependency not in package_ids:
                issues.append(f"work package: missing dependency {dependency}")
        if string(package.get("work_package_id")):
            graph[package["work_package_id"]] = dependencies
        verification = package.get("verification")
        if "verification" in package and _object(verification, {"status", "reviewer", "recorded_at", "evidence_refs"}, {"status"}, "package verification", issues):
            _optional_strings(verification, {"reviewer"}, "package verification", issues)
            _time(verification.get("recorded_at"), "package verification.recorded_at", issues)
            evidence = _strings(verification, "evidence_refs", "package verification", issues)
            if not string(verification.get("status")) or verification["status"] not in {"verified", "not_verified", "revalidation_needed"}:
                issues.append("package verification: unsupported status")
            if verification.get("status") == "verified" and (not evidence or not string(verification.get("reviewer")) or verification.get("reviewer") != package.get("review_owner") or verification.get("recorded_at") is None):
                issues.append("package verification: verified requires designated reviewer, timestamp and evidence")
    if len(memberships) != len(set(memberships)):
        issues.append("work packages: task membership must be unique")
    if set(memberships) != step_ids:
        issues.append("work packages: every current task must belong to exactly one package")
    # Iterative traversal keeps validation bounded even at the package limit.
    visiting, visited = set(), set()
    for start in graph:
        stack = [(start, False)]
        while stack:
            node, exiting = stack.pop()
            if exiting:
                visiting.discard(node)
                visited.add(node)
            elif node in visiting:
                issues.append("work packages: dependency cycle")
                return
            elif node not in visited and node in graph:
                visiting.add(node)
                stack.append((node, True))
                stack.extend((dependency, False) for dependency in reversed(graph[node]))


def package_task_counts(plan: dict, package: dict) -> dict:
    """Count member tasks only; no inference of package verification or acceptance."""
    members = set(package["step_ids"])
    subset = {"steps": [step for step in plan["steps"] if step["step_id"] in members]}
    return task_counts(subset)


def task_counts(plan: dict) -> dict:
    tasks = plan["steps"]
    current = {task["step_id"] for task in tasks}
    completed = sum(task.get("status") == "done" and task.get("revalidation_needed") is not True for task in tasks)
    initial = plan.get("initial_task_ids")
    return {"current": len(current), "completed": completed, "remaining": len(current) - completed,
            "initial": len(initial) if initial is not None else None,
            "added": len(current - set(initial)) if initial is not None else None,
            "removed": len(set(initial) - current) if initial is not None else None,
            "revalidation": sum(task.get("revalidation_needed") is True for task in tasks),
            "unrecorded": sum(task.get("status") is None for task in tasks),
            "unrecognized": sum(task.get("status") is not None and task["status"] not in {"pending", "in_progress", "done", "blocked", "unknown", "escalated"} for task in tasks)}


@contextmanager
def writer_lock(path: Path):
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.close(descriptor)
        yield
    finally:
        path.unlink(missing_ok=True)


def _publish(path: Path, payload: dict):
    body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if len(body.encode("utf-8")) > MAX_BYTES:
        raise ValueError("1 MiB snapshot limit exceeded; history was not pruned")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _directory(root: Path, relative: str) -> Path:
    path = root.resolve() / relative
    path.resolve().relative_to(root.resolve())
    path.mkdir(parents=True, exist_ok=True)
    return path


def register_workspace(root: Path, workspace: dict) -> dict:
    issues = validate_workspace(workspace)
    if issues:
        raise ValueError("; ".join(issues))
    if confined_directory(root, workspace["workspace_root"]) is None:
        raise ValueError("workspace root must be an existing repository-contained directory")
    directory = _directory(root, "work/workspaces")
    name = hashlib.sha256(workspace["workspace_id"].encode()).hexdigest()[:24]
    target = directory / (name + ".json")
    with writer_lock(directory / ".registry.lock"):
        rows = load_workspaces(root)
        for row in rows:
            if row["issues"]:
                raise ValueError("workspace registry requires repair: " + "; ".join(row["issues"]))
            existing = row["workspace"]
            if existing["workspace_id"] == workspace["workspace_id"]:
                if existing == workspace:
                    return {"saved": False, "replayed": True, "output": row["file"]}
                raise ValueError("workspace identity conflict; registration is not silently replaced")
            proposed_root = confined_directory(root, workspace["workspace_root"])
            existing_root = confined_directory(root, existing["workspace_root"])
            proposed_scope = (proposed_root / "work/sessions").resolve()
            existing_scope = (existing_root / "work/sessions").resolve()
            if proposed_root == existing_root or proposed_scope == existing_scope or proposed_scope in existing_scope.parents or existing_scope in proposed_scope.parents:
                raise ValueError("workspace root/session scope overlaps an existing registration")
        if len(rows) >= MAX_RECORDS:
            raise ValueError("workspace record limit exceeded")
        if target.exists():
            raise ValueError("workspace output path already belongs to another record; refusing overwrite")
        _publish(target, workspace)
    return {"saved": True, "replayed": False, "output": str(target)}


def record_plan(root: Path, plan: dict, expected_revision: int, *, monitor_base: str | None = None) -> dict:
    if not isinstance(plan, dict):
        raise ValueError("plan object required")
    if any(key in plan for key in WRITER_FIELDS):
        raise ValueError("submitted input must not contain writer-produced observation/history fields")
    issues = validate_plan_v2(plan)
    if issues:
        raise ValueError("; ".join(issues))
    if Path(plan["repository_root"]).resolve() != root.resolve() or not Path(plan["repository_root"]).is_absolute():
        raise ValueError("repository root mismatch")
    registry = [row for row in load_workspaces(root) if row["workspace"] and row["workspace"]["workspace_id"] == plan["workspace_id"]]
    if len(registry) != 1 or registry[0]["issues"]:
        raise ValueError("workspace mapping missing or ambiguous")
    workspace = confined_directory(root, registry[0]["workspace"]["workspace_root"])
    (workspace / "work/plans").resolve().relative_to(workspace)
    directory = _directory(root, str((workspace / "work/plans").relative_to(root.resolve())))
    identity = f'{plan["workspace_id"]}\0{plan["plan_id"]}\0{plan["plan_revision"]}'
    target = directory / (hashlib.sha256(identity.encode()).hexdigest()[:24] + ".json")
    fingerprint = submitted_hash(plan)
    with writer_lock(directory / ".records.lock"):
        existing = None
        candidates = list(directory.glob("*.json"))
        for candidate in candidates:
            candidate.resolve().relative_to(directory.resolve())
            value = read_json(candidate)
            if isinstance(value, dict) and value.get("schema_version") == 2 and tuple(value.get(key) for key in ("workspace_id", "plan_id", "plan_revision")) == tuple(plan[key] for key in ("workspace_id", "plan_id", "plan_revision")):
                if existing is not None:
                    raise ValueError("duplicate plan identity requires repair")
                if validate_plan_v2(value, stored=True):
                    raise ValueError("existing snapshot invalid; refusing overwrite")
                existing = value
                target = candidate
        if existing:
            receipts = [existing] + existing.get("observation_history", [])
            retry = next((item for item in receipts if item.get("report_id") == plan["report_id"]), None)
            if retry:
                if retry.get("report_sha256") == fingerprint:
                    from xrefkit.plan_markdown import publish_projection
                    return {"saved": False, "replayed": True, "observation_revision": existing["observation_revision"], "output": str(target), "projection": publish_projection(root, target, existing, base=monitor_base)}
                raise ValueError("report_id reused with different payload")
            if expected_revision != existing.get("observation_revision"):
                raise ValueError("stale expected observation revision")
            if plan_definition(plan) != plan_definition(existing):
                raise ValueError("plan definition changed; create a new plan_revision")
            history = existing.get("observation_history", []) + [{"observation_revision": existing["observation_revision"], "report_id": existing["report_id"], "report_sha256": existing["report_sha256"], "payload": submitted_payload(existing)}]
        else:
            if target.exists():
                raise ValueError("plan output path already belongs to another record; refusing overwrite")
            if expected_revision != 0:
                raise ValueError("initial observation requires expected revision 0")
            if len(candidates) >= MAX_RECORDS:
                raise ValueError("plan file limit exceeded")
            history = []
        if len(history) > MAX_RECORDS:
            raise ValueError("observation history limit exceeded; history was not pruned")
        snapshot = {**plan, "observation_revision": expected_revision + 1, "report_sha256": fingerprint, "observation_history": history}
        issues = validate_plan_v2(snapshot)
        if issues:
            raise ValueError("; ".join(issues))
        _publish(target, snapshot)
        from xrefkit.plan_markdown import publish_projection
        projection = publish_projection(root, target, snapshot, base=monitor_base)
    return {"saved": True, "replayed": False, "observation_revision": snapshot["observation_revision"], "output": str(target), "projection": projection}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Register a local workspace or atomically record a structured v2 plan")
    parser.add_argument("action", choices=("register", "record", "render"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--expected-observation-revision", type=int)
    parser.add_argument("--monitor-base", help="Explicit optional HTTP/HTTPS monitor deployment base; never inferred")
    args = parser.parse_args(argv)
    try:
        value = read_json(args.input)
        if args.action == "register":
            result = register_workspace(args.root, value)
        elif args.action == "render":
            from xrefkit.plan_markdown import regenerate
            result = regenerate(args.root, args.input, base=args.monitor_base)
        else:
            if args.expected_observation_revision is None or args.expected_observation_revision < 0:
                raise ValueError("record requires a nonnegative --expected-observation-revision")
            result = record_plan(args.root, value, args.expected_observation_revision, monitor_base=args.monitor_base)
        successful = result.get("projection", {}).get("status") != "failed"
        print(json.dumps({"ok": successful, **result}, ensure_ascii=False))
        return 0 if successful else 1
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        print(json.dumps({"ok": False, "issues": [str(exc)]}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Evidence-bearing pre-workflow routing; no model or business-tool execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Text = Annotated[str, Field(min_length=1)]
Count = Annotated[int, Field(ge=0)]
Amount = Annotated[float, Field(ge=0, allow_inf_nan=False)]
AXES = {"constraints", "branch_depth", "dependency_depth", "cross_source_links",
        "scope_changes", "integration_links"}


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Source(Record):
    id: Text
    kind: Literal["instruction", "skill", "profile", "data"]
    path: Text
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    bytes: Count


class Evidence(Record):
    source_id: Text
    locator: Text


class Measurement(Record):
    value: Count | None
    basis: Literal["measured", "estimated", "unknown"]
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent(self):
        if (self.value is None) != (self.basis == "unknown"):
            raise ValueError("unknown measurements require null; known measurements require a value")
        return self


class Step(Record):
    id: Text
    kind: Literal["deterministic", "model"]
    task: Text
    scope: Text
    evidence: list[Evidence] = Field(min_length=1)
    depends_on: list[Text] = Field(default_factory=list)
    capabilities: list[Text] = Field(default_factory=list)
    metrics: dict[str, Measurement] = Field(default_factory=dict)
    tool_ref: Text | None = None

    @model_validator(mode="after")
    def execution_boundary(self):
        if self.kind == "deterministic":
            if not self.tool_ref or self.capabilities or self.metrics:
                raise ValueError("deterministic steps require tool_ref and no model requirements")
        elif self.tool_ref or not self.capabilities or set(self.metrics) != AXES:
            raise ValueError("model steps require capabilities and every complexity axis, with no tool_ref")
        return self


class Assessment(Record):
    version: Literal[1]
    request_id: Text
    revision: Count
    environment: Text
    instruction: Text
    sources: list[Source] = Field(min_length=2)
    # null means not assessed; [] means explicitly assessed with no open issues.
    unresolved: list[Text] | None
    steps: list[Step] = Field(min_length=1)

    @model_validator(mode="after")
    def references(self):
        source_ids = {s.id for s in self.sources}
        if len(source_ids) != len(self.sources):
            raise ValueError("duplicate source IDs")
        kinds = {s.kind for s in self.sources}
        if not {"instruction", "skill"} <= kinds:
            raise ValueError("instruction and skill sources are required")
        seen: set[str] = set()
        for step in self.steps:
            if step.id in seen or not set(step.depends_on) <= seen:
                raise ValueError("steps must have unique IDs and dependencies in execution order")
            seen.add(step.id)
            refs = step.evidence + [e for m in step.metrics.values() for e in m.evidence]
            if any(e.source_id not in source_ids for e in refs):
                raise ValueError("evidence references an unknown source")
        return self


class Candidate(Record):
    id: Text
    cost_tier: Count
    priority: Count
    capabilities: list[Text]
    limits: dict[str, Count]
    evaluation_ref: Text
    max_input_bytes: Count

    @model_validator(mode="after")
    def axes(self):
        if set(self.limits) != AXES:
            raise ValueError("candidate limits must cover every complexity axis")
        return self


class Policy(Record):
    version: Text
    environment: Text
    host: Literal["generic", "vscode_copilot"]
    parent_model_id: Text | None = None
    parent_cost_tier: Count | None = None
    candidates: list[Candidate] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_host(self):
        if self.host == "vscode_copilot" and (
            self.parent_model_id is None or self.parent_cost_tier is None
        ):
            raise ValueError("Copilot policy requires parent_model_id and parent_cost_tier")
        if len({c.id for c in self.candidates}) != len(self.candidates):
            raise ValueError("duplicate model IDs")
        return self


def snapshot(path: Path, kind: str, source_id: str) -> dict:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return {"id": source_id, "kind": kind, "path": str(path.resolve()),
            "sha256": digest.hexdigest(), "bytes": size}


def route(assessment: Assessment, policy: Policy, *, current_sources: list[Source] | None = None) -> dict:
    """Filter by capability, per-axis limits and host tier; never invent scores."""
    issues = list(assessment.unresolved or [])
    if assessment.environment != policy.environment:
        issues.append("assessment and model policy belong to different environments")
    if assessment.unresolved is None:
        issues.append("scope and instruction conflicts have not been assessed")
    if current_sources is not None:
        # Remote MCP source paths belong to the client, never the server.
        expected = {s.id: s.model_dump() for s in assessment.sources}
        current = {s.id: s.model_dump() for s in current_sources}
        if len(current) != len(current_sources) or current != expected:
            issues.append("client source snapshot changed; reassess this revision")
        instruction_bytes = assessment.instruction.encode("utf-8")
        instruction_sources = [s for s in assessment.sources if s.kind == "instruction"]
        if len(instruction_sources) != 1 or any(
            s.sha256 != hashlib.sha256(instruction_bytes).hexdigest()
            or s.bytes != len(instruction_bytes) for s in instruction_sources
        ):
            issues.append("instruction does not match its canonical UTF-8 client snapshot")
    else:
        for source in assessment.sources:
            actual = snapshot(Path(source.path), source.kind, source.id)
            if actual["sha256"] != source.sha256 or actual["bytes"] != source.bytes:
                issues.append(f"source changed: {source.id}; reassess this revision")
            if source.kind == "instruction" and Path(source.path).read_text(encoding="utf-8-sig") != assessment.instruction:
                issues.append(f"instruction does not match source: {source.id}")
    decisions = []
    upgrade_options: dict[str, list[Candidate]] = {}
    model_step_without_route = False
    for step in assessment.steps:
        if step.kind == "deterministic":
            decisions.append({"step_id": step.id, "kind": step.kind, "tool_ref": step.tool_ref})
            continue
        unknown = [axis for axis, metric in step.metrics.items() if metric.value is None]
        rejected = {}
        eligible = []
        blocked_only_by_parent = []
        for candidate in policy.candidates:
            intrinsic_reasons = []
            if sum(s.bytes for s in assessment.sources) > candidate.max_input_bytes:
                intrinsic_reasons.append("exceeds evaluated input byte limit")
            missing = sorted(set(step.capabilities) - set(candidate.capabilities))
            if missing:
                intrinsic_reasons.append("missing capabilities: " + ", ".join(missing))
            if unknown:
                intrinsic_reasons.append("unknown complexity: " + ", ".join(sorted(unknown)))
            for axis, metric in step.metrics.items():
                if metric.value is not None and metric.value > candidate.limits[axis]:
                    intrinsic_reasons.append(f"exceeds {axis}")
            parent_blocked = (
                not intrinsic_reasons
                and policy.host == "vscode_copilot"
                and candidate.cost_tier > policy.parent_cost_tier
            )
            reasons = list(intrinsic_reasons)
            if parent_blocked:
                reasons.append("exceeds Copilot parent cost tier")
                blocked_only_by_parent.append(candidate)
            if reasons:
                rejected[candidate.id] = reasons
            else:
                eligible.append(candidate)
        chosen = min(eligible, key=lambda c: (c.priority, c.id)) if eligible and not issues else None
        if not eligible:
            if blocked_only_by_parent:
                upgrade_options[step.id] = blocked_only_by_parent
            else:
                model_step_without_route = True
        decisions.append({"step_id": step.id, "kind": step.kind,
                          "model": chosen.id if chosen else None,
                          "evaluation_ref": chosen.evaluation_ref if chosen else None,
                          "rejected": rejected})
    upgrade = None
    if not issues and not model_step_without_route and upgrade_options:
        required_tier = max(min(c.cost_tier for c in candidates)
                            for candidates in upgrade_options.values())
        workers = []
        for step_id, candidates in upgrade_options.items():
            callable_at_tier = [c for c in candidates if c.cost_tier <= required_tier]
            selected = min(callable_at_tier, key=lambda c: (c.priority, c.id))
            workers.append({"step_id": step_id, "model": selected.id,
                            "cost_tier": selected.cost_tier,
                            "evaluation_ref": selected.evaluation_ref})
        upgrade = {
            "proposal_only": True,
            "action": "user_selects_conversation_model",
            "current_conversation_model": policy.parent_model_id,
            "current_cost_tier": policy.parent_cost_tier,
            "required_minimum_tier": required_tier,
            "affected_steps": sorted(upgrade_options),
            "workers_callable_after_upgrade": workers,
            "reason": "evaluated workers satisfy task requirements but exceed the current conversation cost tier",
            "resume": {"request_id": assessment.request_id,
                       "revision": assessment.revision,
                       "tool": "route_instruction_gateway",
                       "rule": "select a conversation model at or above required_minimum_tier, refresh source snapshots, update the environment policy, and rerun routing"},
        }
    if issues or model_step_without_route:
        status = "needs_assessment"
    elif upgrade is not None:
        status = "conversation_upgrade_required"
    else:
        status = "ready"
    return {"schema_version": 1, "status": status,
            "request_id": assessment.request_id, "revision": assessment.revision,
            "environment": assessment.environment,
            "policy_version": policy.version, "issues": issues, "decisions": decisions,
            "assessment": assessment.model_dump(), "policy": policy.model_dump(),
            "dispatch_status": "not_dispatched",
            "conversation_upgrade": upgrade,
            "source_verification": "client_reported_snapshot" if current_sources is not None else "local_files",
            "workflow_rule": "Start the existing workflow/Skill envelope before executing any step; preserve all gates."}


class Attempt(Record):
    id: Text
    goal_id: Text
    scope_revision: Count
    model: Text
    route_ref: Text
    retry_of: Text | None = None
    reason: Literal["initial", "instruction_miss", "scope_error", "dissatisfaction",
                    "requirement_change", "unknown"]
    reason_evidence: Text | None = None
    accepted: bool | None = None
    acceptance_evidence: Text | None = None
    cost: Amount | None = None
    elapsed_seconds: Amount | None = None
    user_revision_seconds: Amount | None = None

    @model_validator(mode="after")
    def explicit_feedback(self):
        if (self.retry_of is None) != (self.reason == "initial"):
            raise ValueError("non-initial attempts must link retry_of")
        if self.reason not in {"initial", "unknown"} and not self.reason_evidence:
            raise ValueError("classified feedback requires reason_evidence")
        if self.accepted is not None and not self.acceptance_evidence:
            raise ValueError("acceptance/rejection requires explicit evidence")
        return self


class Feedback(Record):
    version: Literal[1]
    cost_unit: Text
    attempts: list[Attempt] = Field(min_length=1)


def evaluate(feedback: Feedback) -> dict:
    seen = {}
    for attempt in feedback.attempts:
        if attempt.id in seen:
            raise ValueError("duplicate attempt ID")
        if attempt.retry_of:
            parent = seen.get(attempt.retry_of)
            if parent is None or parent.goal_id != attempt.goal_id:
                raise ValueError("retry must refer to an earlier attempt for the same goal")
            changed = parent.scope_revision != attempt.scope_revision
            if attempt.reason == "requirement_change" and not changed:
                raise ValueError("requirement changes require a new scope_revision")
            if changed and attempt.reason not in {"requirement_change", "unknown"}:
                raise ValueError("quality retries must retain the evaluated scope revision")
        seen[attempt.id] = attempt
    initial = [a for a in feedback.attempts if a.reason in {"initial", "requirement_change"}]
    judged = [a for a in initial if a.accepted is not None]
    sums = {}
    for field in ("cost", "elapsed_seconds", "user_revision_seconds"):
        values = [getattr(a, field) for a in feedback.attempts]
        sums[field] = {"total": sum(values) if all(v is not None for v in values) else None,
                       "known_subtotal": sum(v for v in values if v is not None),
                       "missing_count": sum(v is None for v in values)}
    groups = {}
    for attempt in feedback.attempts:
        key = (attempt.goal_id, attempt.scope_revision)
        groups.setdefault(key, []).append(attempt)
    acceptance = []
    for (goal, revision), attempts in groups.items():
        accepted_index = next((i for i, a in enumerate(attempts) if a.accepted is True), None)
        prefix = attempts if accepted_index is None else attempts[:accepted_index + 1]
        totals = {}
        for field in ("cost", "elapsed_seconds", "user_revision_seconds"):
            values = [getattr(a, field) for a in prefix]
            totals[field] = sum(values) if all(v is not None for v in values) else None
        acceptance.append({"goal_id": goal, "scope_revision": revision,
                           "accepted": accepted_index is not None,
                           "attempts_observed": len(prefix),
                           "attempts_to_acceptance": len(prefix) if accepted_index is not None else None,
                           "usage_observed": totals})
    return {"cost_unit": feedback.cost_unit, "attempts": len(seen),
            "quality_retries": sum(a.reason in {"instruction_miss", "scope_error", "dissatisfaction"}
                                   for a in feedback.attempts),
            "requirement_changes": sum(a.reason == "requirement_change" for a in feedback.attempts),
            "unknown_retries": sum(a.reason == "unknown" for a in feedback.attempts),
            "first_acceptance_rate": sum(a.accepted is True for a in judged) / len(judged) if judged else None,
            "first_acceptance_denominator": len(judged),
            "unjudged_initial_attempts": len(initial) - len(judged), "usage": sums,
            "acceptance_by_scope": acceptance, "feedback": feedback.model_dump()}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="xrefkit gateway")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare", help="Snapshot existing files for gateway assessment")
    prepare.add_argument("--request-id", required=True)
    prepare.add_argument("--environment", required=True,
                         help="Host/profile identity, e.g. vscode:work or codex:personal")
    prepare.add_argument("--profile-root", type=Path,
                         help="Existing profile directory supplied by the active host")
    prepare.add_argument("--instruction-file", type=Path, required=True)
    prepare.add_argument("--skill-file", type=Path, required=True)
    prepare.add_argument("--profile-file", type=Path, action="append", default=[])
    prepare.add_argument("--input-file", type=Path, action="append", default=[])
    prepare.add_argument("--revision", type=int, default=0)
    routing = sub.add_parser("route")
    routing.add_argument("--assessment", type=Path, required=True)
    routing.add_argument("--policy", type=Path, required=True)
    feedback = sub.add_parser("evaluate")
    feedback.add_argument("--feedback", type=Path, required=True)
    schema = sub.add_parser("schema", help="Print the strict JSON schema for gateway records")
    schema.add_argument("kind", choices=["assessment", "policy", "feedback"])
    for command in (prepare, routing, feedback):
        command.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "schema":
            print(json.dumps({"assessment": Assessment, "policy": Policy,
                              "feedback": Feedback}[args.kind].model_json_schema(), indent=2))
            return 0
        if args.command == "prepare":
            if args.revision < 0:
                raise ValueError("revision must be nonnegative")
            sources = [snapshot(args.instruction_file, "instruction", "instruction"),
                       snapshot(args.skill_file, "skill", "skill")]
            for kind, paths in (("profile", args.profile_file), ("data", args.input_file)):
                for i, path in enumerate(paths):
                    if kind == "profile" and args.profile_root is not None:
                        root = args.profile_root.resolve(strict=True)
                        if not root.is_dir():
                            raise ValueError("profile-root must be an existing directory")
                        path = (root / path).resolve(strict=True)
                        if not path.is_relative_to(root):
                            raise ValueError("profile file is outside the selected environment profile root")
                    sources.append(snapshot(path, kind, f"{kind}-{i}"))
            result = {"version": 1, "request_id": args.request_id, "revision": args.revision,
                      "environment": args.environment,
                      "instruction": args.instruction_file.read_text(encoding="utf-8-sig"),
                      "sources": sources, "unresolved": None, "steps": []}
        elif args.command == "route":
            result = route(Assessment.model_validate_json(args.assessment.read_bytes()),
                           Policy.model_validate_json(args.policy.read_bytes()))
        else:
            result = evaluate(Feedback.model_validate_json(args.feedback.read_bytes()))
        payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.out:
            with args.out.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
        else:
            print(payload, end="")
        return 1 if result.get("status") in {
            "needs_assessment", "conversation_upgrade_required"
        } else 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

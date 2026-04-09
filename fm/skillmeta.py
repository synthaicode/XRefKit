from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


GUARD_CAPABILITY_REF = "../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11"
GUARD_KNOWLEDGE_REF = "../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601"
VALID_GUARD_POLICIES = {"required", "closed_world"}
VALID_EXECUTION_MODES = {"local_default", "subagent_preferred", "subagent_required"}


@dataclass
class SkillMetaResult:
    meta_path: str
    skill_id: str | None
    guard_policy: str | None
    execution_mode: str | None
    ok: bool
    errors: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "meta_path": self.meta_path,
            "skill_id": self.skill_id,
            "guard_policy": self.guard_policy,
            "execution_mode": self.execution_mode,
            "ok": self.ok,
            "errors": self.errors,
        }


def _parse_meta_lines(text: str) -> dict[str, object]:
    data: dict[str, object] = {}
    current_key: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("- ") and ":" in stripped[2:]:
            key, value = stripped[2:].split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if value:
                data[key] = value.strip("`")
            else:
                data[key] = []
            continue

        if current_key and stripped.startswith("- "):
            value = stripped[2:].strip().strip("`")
            current = data.get(current_key)
            if not isinstance(current, list):
                current = []
                data[current_key] = current
            current.append(value)

    return data


def validate_skill_meta(meta_path: Path) -> SkillMetaResult:
    parsed = _parse_meta_lines(meta_path.read_text(encoding="utf-8"))
    skill_id = parsed.get("skill_id")
    guard_policy = parsed.get("guard_policy")
    execution_mode = parsed.get("execution_mode")
    constraints = str(parsed.get("constraints", ""))
    summary = str(parsed.get("summary", ""))
    tags = str(parsed.get("tags", ""))
    capability_refs = parsed.get("capability_refs", [])
    knowledge_refs = parsed.get("knowledge_refs", [])
    skill_doc = parsed.get("skill_doc")

    if not isinstance(capability_refs, list):
        capability_refs = []
    if not isinstance(knowledge_refs, list):
        knowledge_refs = []

    errors: list[str] = []

    if not skill_id:
        errors.append("missing skill_id")
    if not skill_doc:
        errors.append("missing skill_doc")
    if execution_mode not in VALID_EXECUTION_MODES:
        errors.append("missing or invalid execution_mode")
    if guard_policy not in VALID_GUARD_POLICIES:
        errors.append("missing or invalid guard_policy")
    elif guard_policy == "required":
        if GUARD_CAPABILITY_REF not in capability_refs:
            errors.append("required guard capability ref is missing")
        if GUARD_KNOWLEDGE_REF not in knowledge_refs:
            errors.append("required guard knowledge ref is missing")
    elif guard_policy == "closed_world":
        if "closed-world" not in constraints:
            errors.append("closed_world policy requires explicit closed-world constraint text")

    review_markers = (
        "review" in str(skill_id).lower()
        or " review" in summary.lower()
        or "review" in tags.lower()
        or "self-check" in summary.lower()
        or "self-check" in tags.lower()
    )
    if review_markers and execution_mode == "local_default":
        errors.append("review-oriented skills must use subagent_preferred or subagent_required")

    return SkillMetaResult(
        meta_path=str(meta_path),
        skill_id=str(skill_id) if skill_id else None,
        guard_policy=str(guard_policy) if guard_policy else None,
        execution_mode=str(execution_mode) if execution_mode else None,
        ok=not errors,
        errors=errors,
    )


def _iter_meta_files(root: Path, scope: str) -> Iterable[Path]:
    scopes = ["skills"]
    if scope == "all":
        scopes.append("skills_private")

    for scope_name in scopes:
        base = root / scope_name
        if not base.exists():
            continue
        yield from sorted(base.rglob("meta.md"))


def cmd_skill(args) -> int:
    root = Path(args.root).resolve()
    targets: list[Path] = []

    if args.meta:
        targets.append((root / args.meta).resolve())
    else:
        targets.extend(_iter_meta_files(root, args.scope))

    results = [validate_skill_meta(path) for path in targets]
    failed = [result for result in results if not result.ok]

    if args.json:
        print(json.dumps([result.to_dict() for result in results], ensure_ascii=False, indent=2))
    else:
        for result in results:
            status = "ok" if result.ok else "fail"
            print(f"{status}: {result.meta_path}")
            if result.skill_id:
                print(f"  skill_id: {result.skill_id}")
            if result.execution_mode:
                print(f"  execution_mode: {result.execution_mode}")
            if result.guard_policy:
                print(f"  guard_policy: {result.guard_policy}")
            for error in result.errors:
                print(f"  error: {error}")

    return 1 if failed else 0

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


GUARD_CAPABILITY_REF = "../../capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11"
GUARD_KNOWLEDGE_REF = "../../knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601"
SKILL_RUNTIME_CAPABILITY_REF = "../../capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5"
VALID_GUARD_POLICIES = {"required", "closed_world"}
VALID_EXECUTION_MODES = {"local_default", "subagent_preferred", "subagent_required"}
VALID_MATURITY_LEVELS = {"draft", "trial", "stable", "governed", "deprecated"}
VALID_CHECK_LEVELS = {"auto", "draft", "trial", "stable", "governed"}
LEGACY_DEFAULT_MATURITY = "stable"
TRIAL_DEFAULT_EXECUTION_MODE = "local_default"
TRIAL_DEFAULT_GUARD_POLICY = "required"
REQUIRED_OS_CONTRACT = {
    "version": "1",
    "worklist_policy": "required",
    "execution_role": "required",
    "check_role": "required",
    "logging_policy": "session_required",
    "judgment_log_policy": "required_when_non_trivial",
    "unknown_risk_policy": "explicit",
    "closure_gate": "required",
    "handoff_policy": "explicit",
}


@dataclass
class SkillMetaResult:
    meta_path: str
    skill_id: str | None
    maturity: str | None
    checked_level: str
    guard_policy: str | None
    execution_mode: str | None
    ok: bool
    errors: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "meta_path": self.meta_path,
            "skill_id": self.skill_id,
            "maturity": self.maturity,
            "checked_level": self.checked_level,
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

        if line.startswith("- ") and ":" in stripped[2:]:
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


def _parse_key_value_list(value: object) -> dict[str, str]:
    if not isinstance(value, list):
        return {}

    parsed: dict[str, str] = {}
    for item in value:
        if not isinstance(item, str) or ":" not in item:
            continue
        key, raw_value = item.split(":", 1)
        parsed[key.strip()] = raw_value.strip().strip("`")
    return parsed


def _require_text_field(parsed: dict[str, object], key: str, errors: list[str]) -> None:
    value = parsed.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"missing {key}")


def _resolve_maturity(parsed: dict[str, object]) -> tuple[str | None, str | None]:
    maturity = parsed.get("maturity")
    status = parsed.get("status")

    raw_value = None
    if isinstance(maturity, str) and maturity.strip():
        raw_value = maturity.strip()
    elif isinstance(status, str) and status.strip():
        raw_value = status.strip()

    if raw_value is None:
        return LEGACY_DEFAULT_MATURITY, None
    if raw_value in VALID_MATURITY_LEVELS:
        return raw_value, raw_value
    return None, raw_value


def _resolve_check_level(*, maturity: str | None, check_level: str) -> str:
    if check_level != "auto":
        return check_level
    if maturity == "deprecated":
        return "draft"
    return maturity or LEGACY_DEFAULT_MATURITY


def _check_review_mode(summary: str, tags: str, skill_id: object, execution_mode: object, errors: list[str]) -> None:
    review_markers = (
        "review" in str(skill_id).lower()
        or " review" in summary.lower()
        or "review" in tags.lower()
        or "self-check" in summary.lower()
        or "self-check" in tags.lower()
    )
    if review_markers and execution_mode == "local_default":
        errors.append("review-oriented skills must use subagent_preferred or subagent_required")


def validate_skill_meta(meta_path: Path, *, check_level: str = "auto") -> SkillMetaResult:
    parsed = _parse_meta_lines(meta_path.read_text(encoding="utf-8"))
    skill_id = parsed.get("skill_id")
    summary = str(parsed.get("summary", ""))
    tags = str(parsed.get("tags", ""))
    maturity, explicit_maturity = _resolve_maturity(parsed)
    is_legacy_meta = explicit_maturity is None
    effective_check_level = _resolve_check_level(maturity=maturity, check_level=check_level)
    guard_policy = parsed.get("guard_policy")
    execution_mode = parsed.get("execution_mode")
    constraints = str(parsed.get("constraints", ""))
    capability_refs = parsed.get("capability_refs", [])
    knowledge_refs = parsed.get("knowledge_refs", [])
    observation_refs = parsed.get("observation_refs", [])
    governance_refs = parsed.get("governance_refs", [])
    skill_doc = parsed.get("skill_doc")
    os_contract = _parse_key_value_list(parsed.get("os_contract"))

    if not isinstance(capability_refs, list):
        capability_refs = []
    if not isinstance(knowledge_refs, list):
        knowledge_refs = []
    if not isinstance(observation_refs, list):
        observation_refs = []
    if not isinstance(governance_refs, list):
        governance_refs = []

    errors: list[str] = []

    if check_level not in VALID_CHECK_LEVELS:
        errors.append(f"invalid check level: {check_level}")
    if explicit_maturity and explicit_maturity not in VALID_MATURITY_LEVELS:
        errors.append(f"invalid maturity/status: {explicit_maturity}")

    for key in ("skill_id", "summary", "use_when", "input", "output", "skill_doc"):
        _require_text_field(parsed, key, errors)

    require_observation_refs = effective_check_level in {"trial", "stable", "governed"} and not (
        check_level == "auto" and is_legacy_meta and effective_check_level == "stable"
    )
    if require_observation_refs:
        if not observation_refs:
            errors.append("trial-or-higher skills must include at least one observation_refs entry")
    if effective_check_level == "trial":
        if execution_mode and execution_mode not in VALID_EXECUTION_MODES:
            errors.append("invalid execution_mode")
        if guard_policy and guard_policy not in VALID_GUARD_POLICIES:
            errors.append("invalid guard_policy")

    if effective_check_level in {"stable", "governed"}:
        if execution_mode not in VALID_EXECUTION_MODES:
            errors.append("missing or invalid execution_mode")
        if guard_policy not in VALID_GUARD_POLICIES:
            errors.append("missing or invalid guard_policy")
        elif guard_policy == "required":
            if GUARD_CAPABILITY_REF not in capability_refs:
                errors.append("required guard capability ref is missing")
            if GUARD_KNOWLEDGE_REF not in knowledge_refs:
                errors.append("required guard knowledge ref is missing")
        elif guard_policy == "closed_world" and "closed-world" not in constraints:
            errors.append("closed_world policy requires explicit closed-world constraint text")
        if SKILL_RUNTIME_CAPABILITY_REF not in capability_refs:
            errors.append("required skill runtime envelope capability ref is missing")
        if not constraints.strip():
            errors.append("missing constraints")
        _check_review_mode(summary, tags, skill_id, execution_mode, errors)
        for key, expected_value in REQUIRED_OS_CONTRACT.items():
            actual_value = os_contract.get(key)
            if actual_value != expected_value:
                errors.append(f"os_contract.{key} must be {expected_value}")

    if effective_check_level == "governed":
        if not governance_refs:
            errors.append("governed skills must include at least one governance_refs entry")

    return SkillMetaResult(
        meta_path=str(meta_path),
        skill_id=str(skill_id) if skill_id else None,
        maturity=maturity,
        checked_level=effective_check_level,
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

    results = [validate_skill_meta(path, check_level=args.level) for path in targets]
    failed = [result for result in results if not result.ok]

    if args.json:
        print(json.dumps([result.to_dict() for result in results], ensure_ascii=False, indent=2))
    else:
        for result in results:
            status = "ok" if result.ok else "fail"
            print(f"{status}: {result.meta_path}")
            if result.skill_id:
                print(f"  skill_id: {result.skill_id}")
            if result.maturity:
                print(f"  maturity: {result.maturity}")
            print(f"  checked_level: {result.checked_level}")
            if result.execution_mode:
                print(f"  execution_mode: {result.execution_mode}")
            if result.guard_policy:
                print(f"  guard_policy: {result.guard_policy}")
            for error in result.errors:
                print(f"  error: {error}")

    return 1 if failed else 0

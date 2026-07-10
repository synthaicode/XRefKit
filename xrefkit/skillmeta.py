from __future__ import annotations

import json
import re
import subprocess
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from xrefkit.ownership import content_files, load_optional_ownership


# Canonical repo-relative suffixes. Skill metas reference these with a
# relative prefix whose depth varies by location (skills/<id>/, skills/os/<id>/,
# skills/packs/<pack>/<id>/), so validation matches on the suffix, not on an
# exact relative path.
GUARD_CAPABILITY_REF = "capabilities/management/130_cap_mgt_004_context_direction_guard.md#xid-2F6A3D8C7B11"
GUARD_KNOWLEDGE_REF = "knowledge/organization/160_context_direction_guard_rules.md#xid-7A2F4C8D1601"
SKILL_RUNTIME_CAPABILITY_REF = "capabilities/management/140_cap_mgt_005_skill_runtime_envelope.md#xid-4E6D8C2A19B5"
VALID_GUARD_POLICIES = {"required", "closed_world"}
VALID_CAPABILITY_LAYERING_POLICIES = {"required"}
VALID_WORKFLOW_PROTOCOL_POLICIES = {"required"}
VALID_EXECUTION_MODES = {"local_default", "subagent_preferred", "subagent_required"}
VALID_MATURITY_LEVELS = {"draft", "trial", "stable", "governed", "deprecated"}
VALID_CHECK_LEVELS = {"auto", "draft", "trial", "stable", "governed"}
PROTOCOL_OWNED_ROLE_RESPONSIBILITIES = {"checker", "quality_reviewer", "handoff_owner"}
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
# `os_contract: v1` is the compact declaration of the version-1 operating
# contract above. Both the shorthand and the expanded inline block are valid
# meta forms; run logs always materialize the expanded block.
OS_CONTRACT_SHORTHANDS = {"v1": REQUIRED_OS_CONTRACT}


def resolve_os_contract(value: object) -> dict[str, str]:
    if isinstance(value, str):
        shorthand = OS_CONTRACT_SHORTHANDS.get(value.strip().strip("`"))
        return dict(shorthand) if shorthand else {}
    return _parse_key_value_list(value)


@dataclass
class SkillMetaResult:
    meta_path: str
    skill_id: str | None
    maturity: str | None
    checked_level: str
    guard_policy: str | None
    capability_layering: str | None
    workflow_protocol: str | None
    tuning: str | None
    role_responsibilities: dict[str, str]
    execution_mode: str | None
    ok: bool
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "meta_path": self.meta_path,
            "skill_id": self.skill_id,
            "maturity": self.maturity,
            "checked_level": self.checked_level,
            "guard_policy": self.guard_policy,
            "capability_layering": self.capability_layering,
            "workflow_protocol": self.workflow_protocol,
            "tuning": self.tuning,
            "role_responsibilities": self.role_responsibilities,
            "execution_mode": self.execution_mode,
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
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


def _has_skill_role_responsibilities(value: object) -> bool:
    parsed = _parse_key_value_list(value)
    required = {"executor"}
    return all(parsed.get(role, "").strip() for role in required)


def _protocol_owned_role_responsibilities(value: object) -> list[str]:
    parsed = _parse_key_value_list(value)
    return sorted(PROTOCOL_OWNED_ROLE_RESPONSIBILITIES.intersection(parsed))


def _has_responsibility(parsed: dict[str, object]) -> bool:
    # Skill-centric consolidation (design 083 D1/D3): the triad's
    # `responsibility` is the Skill's business use, replacing the legacy
    # `role_responsibilities.executor` value (which was always a responsibility,
    # not a role). Superset during migration: either form satisfies the check.
    responsibility = parsed.get("responsibility")
    if isinstance(responsibility, str) and responsibility.strip():
        return True
    return _has_skill_role_responsibilities(parsed.get("role_responsibilities"))


_TRACKED_CACHE: dict[str, set[str] | None] = {}


def _git_tracked_files(start: Path) -> tuple[Path, set[str]] | None:
    """Return (repo_root, tracked paths) for the repo containing `start`.

    Returns None when `start` is not inside a git work tree (temp dirs,
    MCP-materialized checkouts without .git), in which case tracked-ness
    cannot and should not be enforced.
    """
    start = start.resolve()
    root = None
    for parent in [start, *start.parents]:
        if (parent / ".git").exists():
            root = parent
            break
    if root is None:
        return None
    key = str(root)
    if key not in _TRACKED_CACHE:
        try:
            out = subprocess.run(
                ["git", "-C", str(root), "ls-files"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            _TRACKED_CACHE[key] = set(out.splitlines())
        except Exception:
            _TRACKED_CACHE[key] = None
    tracked = _TRACKED_CACHE[key]
    return None if tracked is None else (root, tracked)


def _untracked_observation_refs(meta_path: Path, refs: list) -> list[str]:
    """Observation refs whose target is not git-tracked (unresolvable in a clone)."""
    located = _git_tracked_files(meta_path.parent)
    if located is None:
        return []
    root, tracked = located
    bad: list[str] = []
    for ref in refs:
        if not isinstance(ref, str) or not ref.strip():
            continue
        target = (meta_path.parent / ref.split("#")[0]).resolve()
        try:
            rel = target.relative_to(root).as_posix()
        except ValueError:
            bad.append(ref)
            continue
        if rel not in tracked:
            bad.append(ref)
    return bad


def _has_required_ref(refs: list, required_suffix: str) -> bool:
    return any(
        isinstance(ref, str) and ref.replace("\\", "/").endswith(required_suffix)
        for ref in refs
    )


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
    capability_layering = parsed.get("capability_layering")
    workflow_protocol = parsed.get("workflow_protocol")
    tuning = parsed.get("tuning")
    role_responsibilities = _parse_key_value_list(parsed.get("role_responsibilities"))
    execution_mode = parsed.get("execution_mode")
    constraints = str(parsed.get("constraints", ""))
    capability_refs = parsed.get("capability_refs", [])
    knowledge_refs = parsed.get("knowledge_refs", [])
    observation_refs = parsed.get("observation_refs", [])
    governance_refs = parsed.get("governance_refs", [])
    skill_doc = parsed.get("skill_doc")
    raw_os_contract = parsed.get("os_contract")
    os_contract = resolve_os_contract(raw_os_contract)

    if not isinstance(capability_refs, list):
        capability_refs = []
    if not isinstance(knowledge_refs, list):
        knowledge_refs = []
    if not isinstance(observation_refs, list):
        observation_refs = []
    if not isinstance(governance_refs, list):
        governance_refs = []

    errors: list[str] = []
    warnings: list[str] = []

    if is_legacy_meta:
        warnings.append(
            "maturity is not declared; legacy default 'stable' applies. "
            "Declare maturity explicitly (see 059_skill_maturity_governance)."
        )

    skill_body = meta_path.parent / "SKILL.md"
    if skill_body.is_file():
        body = skill_body.read_text(encoding="utf-8")
        generic_calibration = re.compile(
            r"(?im)^\s*[-*]\s+(?:downgrade|remove)\s+"
            r"(?:any\s+)?(?:weakly\s+supported|unsupported|overconfident)\s+"
            r"(?:claims?|conclusions?|inferences?|judgments?)\b"
        )
        if generic_calibration.search(body):
            warnings.append(
                "generic calibration wording candidate in SKILL.md; keep generic "
                "claim-evidence disposition in the base runtime and retain here only "
                "Skill-specific evidence, state, scope, or stop rules"
            )

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
        for ref in observation_refs:
            if isinstance(ref, str) and re.search(r"(^|/)work/", ref.replace("\\", "/")):
                errors.append(
                    f"observation ref points into work/ (local-only): {ref} "
                    "(move the record to observations/ — tracked governance evidence)"
                )
        for ref in _untracked_observation_refs(meta_path, observation_refs):
            errors.append(
                f"observation ref is not git-tracked and cannot resolve in a clone: {ref} "
                "(move the record to observations/ and commit it)"
            )
        if capability_layering not in VALID_CAPABILITY_LAYERING_POLICIES:
            errors.append("missing or invalid capability_layering")
        if workflow_protocol not in VALID_WORKFLOW_PROTOCOL_POLICIES:
            errors.append("missing or invalid workflow_protocol")
        if not isinstance(tuning, str) or not tuning.strip():
            errors.append("missing tuning")
        if not _has_responsibility(parsed):
            errors.append(
                "missing responsibility (declare `responsibility:`; the legacy "
                "role_responsibilities.executor value is still accepted)"
            )
        protocol_roles = _protocol_owned_role_responsibilities(parsed.get("role_responsibilities"))
        if protocol_roles:
            errors.append(
                "role_responsibilities must not define protocol-owned roles: "
                + ", ".join(protocol_roles)
            )
    if effective_check_level == "trial":
        if execution_mode and execution_mode not in VALID_EXECUTION_MODES:
            errors.append("invalid execution_mode")
        if guard_policy and guard_policy not in VALID_GUARD_POLICIES:
            errors.append("invalid guard_policy")
        if capability_layering and capability_layering not in VALID_CAPABILITY_LAYERING_POLICIES:
            errors.append("invalid capability_layering")
        if workflow_protocol and workflow_protocol not in VALID_WORKFLOW_PROTOCOL_POLICIES:
            errors.append("invalid workflow_protocol")

    if effective_check_level in {"stable", "governed"}:
        if execution_mode not in VALID_EXECUTION_MODES:
            errors.append("missing or invalid execution_mode")
        # Skill-centric consolidation (design 083 / 082 D4): the context-direction
        # guard is ambient (startup contract pack + per-response
        # control_reminder), not composed per Skill. guard_policy is no longer a
        # required per-Skill field; validate it only when a legacy meta still
        # declares it.
        if guard_policy is not None and guard_policy not in VALID_GUARD_POLICIES:
            errors.append("invalid guard_policy")
        if capability_layering not in VALID_CAPABILITY_LAYERING_POLICIES:
            errors.append("missing or invalid capability_layering")
        if workflow_protocol not in VALID_WORKFLOW_PROTOCOL_POLICIES:
            errors.append("missing or invalid workflow_protocol")
        if not isinstance(tuning, str) or not tuning.strip():
            errors.append("missing tuning")
        if not _has_responsibility(parsed):
            errors.append(
                "missing responsibility (declare `responsibility:`; the legacy "
                "role_responsibilities.executor value is still accepted)"
            )
        # Guard capability/knowledge refs are no longer required per Skill; the
        # guard is ambient. A legacy meta may still carry them (harmless). The
        # closed_world escape hatch, when explicitly declared, still needs its
        # constraint text.
        if guard_policy == "closed_world" and "closed-world" not in constraints:
            errors.append("closed_world policy requires explicit closed-world constraint text")
        # capability_refs are no longer required per Skill: the runtime envelope
        # is enforced by workflow_protocol / os_contract (the protocol), not a
        # capability-file reference (design 083 D2 — capabilities/ dissolves).
        if not constraints.strip():
            errors.append("missing constraints")
        _check_review_mode(summary, tags, skill_id, execution_mode, errors)
        if (
            isinstance(raw_os_contract, str)
            and raw_os_contract.strip().strip("`") not in OS_CONTRACT_SHORTHANDS
        ):
            errors.append(f"unknown os_contract shorthand: {raw_os_contract}")
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
        capability_layering=str(capability_layering) if capability_layering else None,
        workflow_protocol=str(workflow_protocol) if workflow_protocol else None,
        tuning=str(tuning) if tuning else None,
        role_responsibilities=role_responsibilities,
        execution_mode=str(execution_mode) if execution_mode else None,
        ok=not errors,
        errors=errors,
        warnings=warnings,
    )


# Publication boundary handling for `xrefkit skill list`.
# Boundary truth is the directory: skills/ is public, skills_private/ is
# private. A bare mention of `skills_private/` in public text is a legal
# conceptual reference (authoring rules talk about the boundary itself);
# only a concrete path below it leaks a private skill.
PRIVATE_SCOPE_DIRS = ("skills_private", "knowledge_private", "sources_private")
PUBLIC_TEXT_DIRS = ("skills", "docs", "knowledge", "capabilities", "agent", "flows", "work/retrospectives")
PRIVATE_CONCRETE_REF = re.compile(
    r"(?:skills|knowledge|sources)_private/[\w\-./]+"
)
OWN_XID_RE = re.compile(r"<!--\s*xid:\s*([A-Za-z0-9_-]+)\s*-->")
XID_RE = re.compile(r"(?:<!--\s*xid:\s*([A-Za-z0-9_-]+)\s*-->|#xid-([A-Za-z0-9_-]+))")
LOCAL_MD_REF_RE = re.compile(r"\]\(([^)#]+\.md)(?:#xid-([A-Za-z0-9_-]+))?\)")


def _stable_file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _extract_xids(text: str) -> list[str]:
    xids: list[str] = []
    for match in XID_RE.finditer(text):
        xid = match.group(1) or match.group(2)
        if xid and xid not in xids:
            xids.append(xid)
    return xids


def _extract_own_xids(text: str) -> list[str]:
    xids: list[str] = []
    for match in OWN_XID_RE.finditer(text):
        xid = match.group(1)
        if xid and xid not in xids:
            xids.append(xid)
    return xids


def _read_text_or_empty(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _repo_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _source_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    if not source.exists():
        return []
    return sorted(path for path in source.rglob("*") if path.is_file())


def _find_case_insensitive_file(source: Path, name: str) -> Path | None:
    if source.is_file():
        return source if source.name.lower() == name.lower() else None
    if not source.exists():
        return None
    for path in sorted(source.rglob("*")):
        if path.is_file() and path.name.lower() == name.lower():
            return path
    return None


def _reference_issues(source: Path, files: list[Path]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    text_files = [path for path in files if path.suffix.lower() in {".md", ".yaml", ".yml"}]
    for path in text_files:
        text = _read_text_or_empty(path)
        for match in LOCAL_MD_REF_RE.finditer(text):
            raw_target = match.group(1)
            xid = match.group(2)
            target_path = (path.parent / raw_target).resolve()
            if not xid:
                issues.append(
                    {
                        "kind": "missing_xid_fragment",
                        "file": _repo_rel(path, source),
                        "target": raw_target,
                    }
                )
            if not target_path.exists():
                issues.append(
                    {
                        "kind": "missing_target",
                        "file": _repo_rel(path, source),
                        "target": raw_target,
                    }
                )
    return issues


def _current_skill_candidates(root: Path, source_skill_id: str | None, source_xids: list[str]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    ownership = load_optional_ownership(root)
    for meta_path in content_files(root, "skills", "meta.md", ownership=ownership):
        parsed = _parse_meta_lines(_read_text_or_empty(meta_path))
        skill_id = parsed.get("skill_id")
        skill_dir = meta_path.parent
        current_own_xids: list[str] = []
        for current_file in (meta_path, skill_dir / "SKILL.md"):
            if current_file.exists():
                current_own_xids.extend(
                    x for x in _extract_own_xids(_read_text_or_empty(current_file)) if x not in current_own_xids
                )
        reasons: list[str] = []
        if source_skill_id and skill_id == source_skill_id:
            reasons.append("exact_skill_id")
        overlap = sorted(set(source_xids).intersection(current_own_xids))
        if overlap:
            reasons.append("exact_own_xid")
        if reasons:
            candidates.append(
                {
                    "skill_id": str(skill_id) if skill_id else None,
                    "path": _repo_rel(skill_dir, root),
                    "reasons": reasons,
                    "xid_overlap": overlap,
                }
            )
    return candidates


def _contract_gaps(meta_path: Path | None) -> list[str]:
    if meta_path is None:
        return ["missing meta.md"]
    result = validate_skill_meta(meta_path, check_level="trial")
    return result.errors


def _body_split_indicators(skill_doc: Path | None) -> list[str]:
    if skill_doc is None:
        return []
    text = _read_text_or_empty(skill_doc).lower()
    indicators: list[str] = []
    if "os_contract:" in text or "startup xref routing policy" in text or "uncertainty protocol" in text:
        indicators.append("possible_os_core_rule_copy")
    if "## domain facts" in text or "## factual rules" in text or "## source facts" in text:
        indicators.append("possible_knowledge_in_skill_body")
    return indicators


def build_skill_merge_plan(
    *,
    root: Path,
    source: Path,
    target_skill: str | None = None,
    source_version: str | None = None,
) -> dict[str, object]:
    root = root.resolve()
    source = source.resolve()
    files = _source_files(source)
    meta_path = _find_case_insensitive_file(source, "meta.md")
    skill_doc = _find_case_insensitive_file(source, "SKILL.md")
    parsed_meta = _parse_meta_lines(_read_text_or_empty(meta_path)) if meta_path else {}
    source_skill_id = parsed_meta.get("skill_id")

    source_xids: list[str] = []
    referenced_xids: list[str] = []
    for path in files:
        if path.suffix.lower() in {".md", ".yaml", ".yml"}:
            text = _read_text_or_empty(path)
            source_xids.extend(xid for xid in _extract_own_xids(text) if xid not in source_xids)
            referenced_xids.extend(
                xid for xid in _extract_xids(text) if xid not in source_xids and xid not in referenced_xids
            )

    candidates = _current_skill_candidates(
        root,
        str(source_skill_id) if source_skill_id else target_skill,
        source_xids,
    )
    reference_issues = _reference_issues(source, files)
    contract_gaps = _contract_gaps(meta_path)
    split_indicators = _body_split_indicators(skill_doc)

    safe_transformations: list[str] = []
    if source.exists():
        safe_transformations.append("run xrefkit xref fix after placing accepted files in the repository")
    if meta_path and contract_gaps:
        safe_transformations.append("scaffold missing trial-level metadata fields before promotion")

    judgment_required: list[str] = []
    if candidates:
        judgment_required.append("confirm whether the old Skill and candidate current Skill are semantically the same")
    if split_indicators:
        judgment_required.append("review whether detected Skill body sections must be split into knowledge or core references")
    if reference_issues:
        judgment_required.append("review unmanaged or missing references before promotion")

    if not source.exists():
        proposed = "archive"
        reasons = ["source path does not exist"]
    elif not meta_path and not skill_doc:
        proposed = "archive"
        reasons = ["no meta.md or SKILL.md found"]
    elif split_indicators:
        proposed = "split"
        reasons = split_indicators
    elif candidates:
        proposed = "merge"
        reasons = ["exact structural candidate found"]
    else:
        proposed = "adopt"
        reasons = ["no exact current Skill candidate found"]

    if target_skill and not candidates:
        proposed = "escalate"
        reasons = ["target_skill was supplied but no exact current Skill candidate matched"]
        judgment_required.append("decide whether supplied target_skill is the intended merge target")

    return {
        "source": {
            "path": str(source),
            "source_version": source_version,
            "files": [
                {
                    "path": _repo_rel(path, source),
                    "sha256": _stable_file_hash(path),
                }
                for path in files
            ],
        },
        "identity": {
            "source_skill_id": str(source_skill_id) if source_skill_id else None,
            "source_xids": source_xids,
            "referenced_xids": referenced_xids,
            "candidate_targets": candidates,
        },
        "classification": {
            "proposed": proposed,
            "reasons": reasons,
        },
        "safe_transformations": safe_transformations,
        "judgment_required": sorted(set(judgment_required)),
        "contract_gaps": contract_gaps,
        "reference_issues": reference_issues,
        "ownership_issues": [],
        "validation": {
            "commands": [
                "python -m xrefkit xref fix",
                "python -m xrefkit skill check --scope all",
                "python -m xrefkit pack lint",
                "python tools/run_quality_gate.py xrefkit",
            ]
        },
    }


@dataclass
class SkillListEntry:
    skill_id: str | None
    boundary: str
    path: str
    maturity: str | None
    indexed: bool | None

    def to_dict(self) -> dict[str, object]:
        return {
            "skill_id": self.skill_id,
            "boundary": self.boundary,
            "path": self.path,
            "maturity": self.maturity,
            "indexed": self.indexed,
        }


@dataclass
class SkillIndexEntry:
    skill_id: str
    summary: str
    meta_path: str
    skill_doc: str


def _collect_boundary_entries(root: Path) -> list[SkillListEntry]:
    index_path = root / "skills" / "_index.md"
    index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""

    entries: list[SkillListEntry] = []
    ownership = load_optional_ownership(root)
    for meta_path in content_files(root, "skills", "meta.md", ownership=ownership):
        parsed = _parse_meta_lines(meta_path.read_text(encoding="utf-8"))
        skill_id = parsed.get("skill_id")
        maturity, _ = _resolve_maturity(parsed)
        rel_dir = meta_path.parent.relative_to(root).as_posix()
        indexed = f"{rel_dir}/meta.md" in index_text or f"{rel_dir}/SKILL.md" in index_text
        entries.append(
            SkillListEntry(
                skill_id=str(skill_id) if skill_id else None,
                boundary="public",
                path=rel_dir,
                maturity=maturity,
                indexed=indexed,
            )
        )
    base = root / "skills_private"
    if base.exists():
        for meta_path in sorted(base.rglob("meta.md")):
            parsed = _parse_meta_lines(meta_path.read_text(encoding="utf-8"))
            skill_id = parsed.get("skill_id")
            maturity, _ = _resolve_maturity(parsed)
            rel_dir = meta_path.parent.relative_to(root).as_posix()
            entries.append(
                SkillListEntry(
                    skill_id=str(skill_id) if skill_id else None,
                    boundary="private",
                    path=rel_dir,
                    maturity=maturity,
                    indexed=None,
                )
            )
    return entries


def _skill_doc_path(root: Path, meta_path: Path, parsed: dict[str, object]) -> str:
    value = parsed.get("skill_doc")
    if isinstance(value, str) and value.strip():
        candidate = (meta_path.parent / value.strip().strip("`")).resolve()
    else:
        candidate = meta_path.parent / "SKILL.md"
    try:
        return candidate.relative_to(root).as_posix()
    except ValueError:
        return candidate.as_posix()


def _collect_public_skill_index_entries(root: Path) -> list[SkillIndexEntry]:
    entries: list[SkillIndexEntry] = []
    ownership = load_optional_ownership(root)
    for meta_path in content_files(root, "skills", "meta.md", ownership=ownership):
        parsed = _parse_meta_lines(meta_path.read_text(encoding="utf-8"))
        skill_id = parsed.get("skill_id")
        if not isinstance(skill_id, str) or not skill_id.strip():
            continue
        summary = parsed.get("summary")
        rel_meta = meta_path.relative_to(root).as_posix()
        entries.append(
            SkillIndexEntry(
                skill_id=skill_id.strip(),
                summary=str(summary).strip() if isinstance(summary, str) and summary.strip() else "(summary missing)",
                meta_path=rel_meta,
                skill_doc=_skill_doc_path(root, meta_path, parsed),
            )
        )
    return sorted(entries, key=lambda entry: (entry.meta_path, entry.skill_id))


def build_generated_skill_index(root: Path) -> str:
    index_path = root / "skills" / "_index.md"
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
        prefix = text.split("## Skills (compact)", 1)[0].rstrip()
    else:
        prefix = """<!-- xid: 8D91F66DDBB7 -->
<a id="xid-8D91F66DDBB7"></a>

# Skills Index

This page is the routing entry for skills.
It is intentionally compact for context efficiency.
When asked "what skills are available?", answer from this file."""

    lines = [
        prefix,
        "",
        "## Skills (compact)",
        "",
        "Generated by `python -m xrefkit skill index --write` from catalog-visible `meta.md` files.",
        "",
        "Current family paths:",
        "",
        "- `skills/os/` for OS utility Skills",
        "- `skills/packs/<pack>/` for legacy Business Pack paths during transition",
        "- `packs/<pack>/skills/` for shared pack Skills",
        "- `packs/local/<system>/skills/` for local-instance Skills; these are catalog-visible locally but not distributable",
        "- existing top-level `skills/<skill_id>/` paths remain valid for Skills that have not yet moved",
        "",
    ]
    for entry in _collect_public_skill_index_entries(root):
        lines.extend(
            [
                f"- `{entry.skill_id}`:",
                f"  - summary: {entry.summary}",
                f"  - meta: `{entry.meta_path}`",
                f"  - skill_doc: `{entry.skill_doc}`",
            ]
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Keep this file lightweight; detailed fields belong in `meta.md`.",
            "- Keep behavior/procedure in `SKILL.md`.",
            "- Keep factual domain content in `knowledge/`.",
            "- For the AI Agent OS reorganization view of `skills/`, see:",
            "  - [OS utility and business skill classification design](../docs/designs/064_os_utility_and_business_skill_classification_design.md#xid-ECF29DC3E268)",
            "  - [Business intake pack dependency design](../docs/packs/business-intake/065_business_intake_pack_dependency_design.md#xid-D334C1964342)",
            "",
        ]
    )
    return "\n".join(lines)


def cmd_skill_index(args) -> int:
    root = Path(args.root).resolve()
    rendered = build_generated_skill_index(root)
    out_path = root / "skills" / "_index.md"
    if args.write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        current = out_path.read_text(encoding="utf-8") if out_path.exists() else None
        if current != rendered:
            out_path.write_text(rendered, encoding="utf-8", newline="\n")
        if args.json:
            print(json.dumps({"path": out_path.relative_to(root).as_posix(), "changed": current != rendered}, indent=2))
        else:
            print(f"wrote: {out_path.relative_to(root).as_posix()}")
        return 0
    if args.json:
        entries = [entry.__dict__ for entry in _collect_public_skill_index_entries(root)]
        print(json.dumps({"path": "skills/_index.md", "entries": entries}, ensure_ascii=False, indent=2))
    else:
        print(rendered)
    return 0


def _git_tracked_private_files(root: Path) -> list[str] | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--", *PRIVATE_SCOPE_DIRS],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _private_refs_from_public(root: Path) -> list[str]:
    hits: list[str] = []
    for scope in PUBLIC_TEXT_DIRS:
        base = root / scope
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix.lower() not in {".md", ".yaml", ".yml"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            lines = text.splitlines()
            for match in PRIVATE_CONCRETE_REF.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                # Inline suppression with justification, same idiom as the
                # repo's CA1031 pragmas: a line carrying `private-ref-ok`
                # is a reviewed, deliberate boundary-convention pointer.
                if "private-ref-ok" in lines[line_no - 1]:
                    continue
                rel = path.relative_to(root).as_posix()
                hits.append(f"{rel}:{line_no}: {match.group(0)}")
    return hits


def cmd_skill_list(args) -> int:
    root = Path(args.root).resolve()
    entries = _collect_boundary_entries(root)

    violations: list[str] = []
    warnings: list[str] = []

    tracked_private = _git_tracked_private_files(root)
    if tracked_private is None:
        warnings.append("git unavailable: tracked-private check skipped")
    else:
        for tracked in tracked_private:
            violations.append(f"private file is git-tracked (will be published on push): {tracked}")

    for hit in _private_refs_from_public(root):
        violations.append(f"public asset references a concrete private path: {hit}")

    public_ids = {e.skill_id for e in entries if e.boundary == "public" and e.skill_id}
    for entry in entries:
        if entry.boundary == "public" and entry.indexed is False:
            warnings.append(
                f"public skill not registered in skills/_index.md (misplaced private skill?): {entry.path}"
            )
        if entry.boundary == "private" and entry.skill_id in public_ids:
            warnings.append(
                f"skill_id exists on both sides of the boundary (mid-migration?): {entry.skill_id}"
            )

    payload = {
        "skills": [entry.to_dict() for entry in entries],
        "public_count": sum(1 for e in entries if e.boundary == "public"),
        "private_count": sum(1 for e in entries if e.boundary == "private"),
        "violations": violations,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for boundary in ("public", "private"):
            group = [e for e in entries if e.boundary == boundary]
            print(f"{boundary} ({len(group)}):")
            for entry in group:
                indexed = ""
                if entry.indexed is not None:
                    indexed = " indexed" if entry.indexed else " NOT-INDEXED"
                print(f"  {entry.skill_id or '?':40} {entry.maturity or '?':10}{indexed}  {entry.path}")
        for warning in warnings:
            print(f"warning: {warning}")
        for violation in violations:
            print(f"VIOLATION: {violation}")
        print(f"violations: {len(violations)}")

    return 1 if violations else 0


def cmd_skill_merge_plan(args) -> int:
    root = Path(args.root).resolve()
    source = (root / args.source).resolve() if not Path(args.source).is_absolute() else Path(args.source).resolve()
    payload = build_skill_merge_plan(
        root=root,
        source=source,
        target_skill=args.target_skill,
        source_version=args.source_version,
    )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        classification = payload["classification"]
        identity = payload["identity"]
        print(f"source: {payload['source']['path']}")
        print(f"source_skill_id: {identity['source_skill_id'] or '-'}")
        print(f"proposed: {classification['proposed']}")
        for reason in classification["reasons"]:
            print(f"  reason: {reason}")
        for item in payload["judgment_required"]:
            print(f"judgment_required: {item}")
        for gap in payload["contract_gaps"]:
            print(f"contract_gap: {gap}")

    return 0


def _iter_meta_files(root: Path, scope: str) -> Iterable[Path]:
    ownership = load_optional_ownership(root)
    yield from content_files(root, "skills", "meta.md", ownership=ownership)
    if scope == "all":
        base = root / "skills_private"
        if base.exists():
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
            for warning in result.warnings:
                print(f"  warning: {warning}")

    return 1 if failed else 0

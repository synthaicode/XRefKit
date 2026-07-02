"""flow doctor: static validation of deterministic-control flow definitions.

This is the declaration-time enforcer for the flow definition schema in
docs/018 (xid 6D2E4A9C0B71), realizing the check items in docs/073
(xid 4C7E9A2B1D63). Every check is a pure function of the flow file: no run,
no model.

Legacy flows (still using `sequence` / `control_rules`, not yet migrated to the
deterministic `steps` schema) are reported as `legacy` and pass without detailed
checks, so the doctor is non-breaking during the strangler migration.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


# The flow field is literally named `on`. Under YAML 1.1 (PyYAML's default),
# bare `on` / `off` / `yes` / `no` parse as booleans, so `on:` would silently
# become a boolean key. Use a YAML-1.2-style loader where only true/false are
# booleans, so authors can write `on:` naturally.
class _FlowLoader(yaml.SafeLoader):
    pass


_FlowLoader.yaml_implicit_resolvers = {
    ch: list(resolvers) for ch, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
for _ch in list(_FlowLoader.yaml_implicit_resolvers):
    kept = [
        (tag, regexp)
        for tag, regexp in _FlowLoader.yaml_implicit_resolvers[_ch]
        if tag != "tag:yaml.org,2002:bool"
    ]
    if kept:
        _FlowLoader.yaml_implicit_resolvers[_ch] = kept
    else:
        del _FlowLoader.yaml_implicit_resolvers[_ch]
_FlowLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def _load_flow(path: Path) -> object:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_FlowLoader)


_CAP_ID_RE = re.compile(r"CAP-[A-Z]+-\d+")
_CAP_CACHE: dict[str, set[str]] = {}
# Capability reference paths embed the capability id in the filename
# (`140_cap_qa_006_...md` -> CAP-QA-006), so the binding check stays a pure
# function of file names without resolving relative paths.
_CAP_FILENAME_RE = re.compile(r"_cap_([a-z]+)_(\d+)_")
_SKILL_BINDING_CACHE: dict[str, dict[str, dict]] = {}


def _capability_ids(root: Path) -> set[str]:
    """Collect declared capability ids (CAP-XXX-NNN) from capabilities/."""
    key = str(root)
    if key in _CAP_CACHE:
        return _CAP_CACHE[key]
    ids: set[str] = set()
    capdir = root / "capabilities"
    if capdir.exists():
        for p in capdir.rglob("*.md"):
            ids |= set(_CAP_ID_RE.findall(p.read_text(encoding="utf-8", errors="ignore")))
    _CAP_CACHE[key] = ids
    return ids


def _skill_bindings(root: Path) -> dict[str, dict]:
    """Map skill_id -> {meta, capability_ids} from skills/**/meta.md."""
    key = str(root)
    if key in _SKILL_BINDING_CACHE:
        return _SKILL_BINDING_CACHE[key]
    bindings: dict[str, dict] = {}
    skills_dir = root / "skills"
    if skills_dir.exists():
        from fm.skillmeta import _parse_meta_lines

        for meta in skills_dir.rglob("meta.md"):
            parsed = _parse_meta_lines(meta.read_text(encoding="utf-8", errors="ignore"))
            skill_id = parsed.get("skill_id")
            if not isinstance(skill_id, str) or not skill_id:
                continue
            refs = parsed.get("capability_refs")
            cap_ids: set[str] = set()
            for ref in refs if isinstance(refs, list) else []:
                if not isinstance(ref, str):
                    continue
                m = _CAP_FILENAME_RE.search(ref.replace("\\", "/"))
                if m:
                    cap_ids.add(f"CAP-{m.group(1).upper()}-{m.group(2)}")
            bindings[skill_id] = {
                "meta": meta.relative_to(root).as_posix(),
                "capability_ids": cap_ids,
            }
    _SKILL_BINDING_CACHE[key] = bindings
    return bindings


FLOWS_DIR = "flows"
TERMINALS = {"COMPLETE", "ABORT"}
FALLBACK_LABEL = "_invalid_or_absent"
# Closure outcomes a ③ step may map to exit labels (see 073 result_map / 058).
CLOSURE_OUTCOMES = {"complete", "needs_fix", "escalate", "uncertain", "blocked"}
# Canonical acceptance-gate verdicts (Stage-Gate vocabulary; see 073/018). Each
# verdict constrains the kind of target it may route to.
CANONICAL_VERDICTS = {"Go", "Kill", "Hold", "Recycle"}


def _project_root_for_flow(path: Path) -> Path:
    """Resolve the project root for top-level and pack-owned flow files."""
    resolved = path.resolve()
    for parent in resolved.parents:
        if parent.name == FLOWS_DIR:
            return parent.parent
    return resolved.parent.parent


@dataclass
class FlowDoctorResult:
    flow_path: str
    flow_id: str | None
    schema: str  # "deterministic" | "legacy" | "unknown"
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "flow_path": self.flow_path,
            "flow_id": self.flow_id,
            "schema": self.schema,
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _is_terminal(t: object) -> bool:
    return isinstance(t, str) and t in TERMINALS


def _is_human_edge(t: object) -> bool:
    return isinstance(t, dict) and ("handback" in t or "gate" in t)


def _human_edge_inner(t: dict) -> tuple[str, dict]:
    kind = "handback" if "handback" in t else "gate"
    inner = t.get(kind)
    return kind, inner if isinstance(inner, dict) else {}


def _resume_targets(resume: object) -> list[object]:
    if isinstance(resume, str):
        return [resume]
    if isinstance(resume, dict):
        return list(resume.values())
    return []


def _validate_target(target: object, where: str, steps: set[str], errors: list[str]) -> None:
    """C1 + H1/H2: a target resolves to a step, a terminal, or a valid human edge."""
    if isinstance(target, str):
        if target not in TERMINALS and target not in steps:
            errors.append(f"{where}: target '{target}' is not a known step or terminal")
        return
    if _is_human_edge(target):
        kind, inner = _human_edge_inner(target)
        for required in ("to", "ask", "resume"):
            if not inner.get(required):
                errors.append(f"{where}: {kind} missing '{required}'")
        for rt in _resume_targets(inner.get("resume")):
            if not (isinstance(rt, str) and (rt in TERMINALS or rt in steps)):
                errors.append(f"{where}: {kind} resume target '{rt}' is not a known step or terminal")
        return
    errors.append(f"{where}: target has an unrecognized shape ({type(target).__name__})")


def _step_successors(sdef: dict, steps: set[str]) -> set[str]:
    succs: set[str] = set()
    on = sdef.get("on") or {}
    for t in on.values():
        if isinstance(t, str) and t in steps:
            succs.add(t)
        elif _is_human_edge(t):
            _, inner = _human_edge_inner(t)
            for rt in _resume_targets(inner.get("resume")):
                if isinstance(rt, str) and rt in steps:
                    succs.add(rt)
    for t in (sdef.get("result_map") or {}).values():
        if isinstance(t, str) and t in steps:
            succs.add(t)
    return succs


def _direct_escape(sdef: dict) -> bool:
    """A step escapes directly if any exit is a terminal or a human edge."""
    for t in (sdef.get("on") or {}).values():
        if _is_terminal(t) or _is_human_edge(t):
            return True
    for t in (sdef.get("result_map") or {}).values():
        if _is_terminal(t):
            return True
    return False


def validate_flow(path: Path) -> FlowDoctorResult:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = _load_flow(path)
    except Exception as exc:  # malformed YAML is a hard failure
        return FlowDoctorResult(str(path), None, "unknown", False, [f"yaml parse error: {exc}"])

    if not isinstance(data, dict):
        return FlowDoctorResult(str(path), None, "unknown", False, ["flow file is not a mapping"])

    flow_id = data.get("flow_id")
    flow_id_s = str(flow_id) if flow_id else None
    steps = data.get("steps")

    if not isinstance(steps, dict):
        if "sequence" in data:
            warnings.append(
                "legacy flow (sequence/control_rules); not migrated to the deterministic "
                "schema — flow doctor checks skipped"
            )
            return FlowDoctorResult(str(path), flow_id_s, "legacy", True, errors, warnings)
        errors.append("missing 'steps' map (the deterministic schema requires 'steps')")
        return FlowDoctorResult(str(path), flow_id_s, "unknown", False, errors, warnings)

    step_names = set(steps)
    cap_ids = _capability_ids(_project_root_for_flow(path))

    # C4 — entry exists.
    entry = data.get("entry")
    if not (isinstance(entry, str) and entry in step_names):
        errors.append(f"entry missing or not a known step: {entry!r}")

    # Per-step checks.
    for name, sdef in steps.items():
        where = f"step '{name}'"
        if not isinstance(sdef, dict):
            errors.append(f"{where}: step definition is not a mapping")
            continue

        has_cap = bool(sdef.get("capability"))
        has_result_map = "result_map" in sdef and sdef.get("result_map") is not None

        # G3 — capability references must resolve to a declared capability.
        cap = sdef.get("capability")
        caprefs = [cap] if isinstance(cap, str) else (cap if isinstance(cap, list) else [])
        for c in caprefs:
            if cap_ids and c not in cap_ids:
                errors.append(
                    f"{where}: capability '{c}' does not resolve to a declared capability "
                    "in capabilities/ (G3)"
                )

        # G4 — a declared skill binding must exist and own the step's capability.
        bound_skill = sdef.get("skill")
        if bound_skill is not None:
            if not isinstance(bound_skill, str) or not bound_skill.strip():
                errors.append(f"{where}: 'skill' must be a skill id string (G4)")
            elif not has_cap:
                errors.append(
                    f"{where}: 'skill' binding requires a 'capability' declaration (G4)"
                )
            else:
                binding = _skill_bindings(_project_root_for_flow(path)).get(bound_skill)
                if binding is None:
                    errors.append(
                        f"{where}: bound skill '{bound_skill}' does not resolve to a "
                        "skills/**/meta.md (G4)"
                    )
                else:
                    for c in caprefs:
                        if c not in binding["capability_ids"]:
                            errors.append(
                                f"{where}: bound skill '{bound_skill}' does not declare "
                                f"capability '{c}' in its capability_refs (G4)"
                            )

        # P1 / P2 — declaration completeness (warnings).
        if "facets" not in sdef:
            warnings.append(f"{where}: no 'facets' manifest declared (P1)")
        if "permission" not in sdef:
            warnings.append(f"{where}: no 'permission' envelope declared (P2)")

        # D1 — exit map present.
        on = sdef.get("on")
        if not isinstance(on, dict) or not on:
            errors.append(f"{where}: missing 'on' exit map (D1)")
            on = {}
        else:
            # D2 — the determinism-closing fallback edge.
            if FALLBACK_LABEL not in on:
                errors.append(f"{where}: 'on' has no '{FALLBACK_LABEL}' edge (D2)")
            # C1 / H1 / H2 — every target resolves.
            for label, target in on.items():
                _validate_target(target, f"{where} on.{label}", step_names, errors)

        # K3 / K5 — a point is ② (capability) or ③ (result_map), never both.
        if has_cap and has_result_map:
            errors.append(
                f"{where}: declares both 'capability' (②) and 'result_map' (③); "
                "a point is either consolidation or deterministic execution (K3/K5)"
            )

        # K4 — a self-produced branch needs a declared producer.
        machine_labels = [
            label
            for label, target in on.items()
            if label != FALLBACK_LABEL and not _is_human_edge(target)
        ]
        if len(machine_labels) >= 2 and not has_cap and not has_result_map:
            errors.append(
                f"{where}: branches over {sorted(machine_labels)} but declares no producer "
                "(capability ② or result_map ③): hidden consolidation (K4)"
            )

        # P3 — result_map outcome keys should be closure outcomes (warning).
        if has_result_map and isinstance(sdef.get("result_map"), dict):
            for outcome in sdef["result_map"]:
                if outcome not in CLOSURE_OUTCOMES:
                    warnings.append(
                        f"{where}: result_map outcome '{outcome}' is not a known closure "
                        f"outcome {sorted(CLOSURE_OUTCOMES)} (P3)"
                    )

        # G1 — a declared tool gate must produce its verdict via result_map.
        acceptance = sdef.get("acceptance")
        acc_kinds: set[str] = set()
        if isinstance(acceptance, list):
            for item in acceptance:
                if isinstance(item, dict):
                    acc_kinds |= set(item.keys())
        if "tool" in acc_kinds and not has_result_map:
            warnings.append(
                f"{where}: acceptance declares a tool gate but has no result_map; the tool "
                "gate is not wired to the transition (G1)"
            )

        # G2 — a canonical verdict label must route to a target of the right kind.
        for label, target in on.items():
            if label not in CANONICAL_VERDICTS:
                continue
            if label == "Go":
                ok_target = isinstance(target, str) and (target == "COMPLETE" or target in step_names)
            elif label == "Kill":
                ok_target = target == "ABORT"
            elif label == "Hold":
                ok_target = _is_human_edge(target)
            else:  # Recycle
                ok_target = isinstance(target, str) and target in step_names
            if not ok_target:
                errors.append(
                    f"{where}: verdict '{label}' routes to an inconsistent target "
                    f"({target!r}); Go→step/COMPLETE, Kill→ABORT, Hold→human edge, "
                    "Recycle→step (G2)"
                )

    # H4 — cross-cutting human returns declared once at flow level.
    global_handback = data.get("global_handback")
    if global_handback is not None:
        if not isinstance(global_handback, dict):
            errors.append("global_handback must be a mapping (H4)")
        else:
            for hb_name, hb in global_handback.items():
                where = f"global_handback.{hb_name}"
                if not isinstance(hb, dict):
                    errors.append(f"{where}: not a mapping (H4)")
                    continue
                for required in ("to", "ask", "resume"):
                    if not hb.get(required):
                        errors.append(f"{where}: missing '{required}' (H4)")
                for rt in _resume_targets(hb.get("resume")):
                    if not (isinstance(rt, str) and (rt in TERMINALS or rt in step_names)):
                        errors.append(f"{where}: resume target '{rt}' is not a known step or terminal (H4)")

    # C2 — reachability. Seed with entry and any global_handback resume targets
    # (those re-enter the graph from outside any single step).
    adjacency = {
        name: _step_successors(sdef, step_names)
        for name, sdef in steps.items()
        if isinstance(sdef, dict)
    }
    roots: set[str] = set()
    if isinstance(entry, str) and entry in step_names:
        roots.add(entry)
    if isinstance(global_handback, dict):
        for hb in global_handback.values():
            if isinstance(hb, dict):
                for rt in _resume_targets(hb.get("resume")):
                    if isinstance(rt, str) and rt in step_names:
                        roots.add(rt)
    reachable: set[str] = set()
    stack = list(roots)
    while stack:
        cur = stack.pop()
        if cur in reachable:
            continue
        reachable.add(cur)
        stack.extend(adjacency.get(cur, set()))
    for name in sorted(step_names - reachable):
        errors.append(f"step '{name}' is unreachable from entry (C2)")

    # C3 — every step can reach a terminal or a human edge (no inescapable loop).
    escapes = {
        name
        for name, sdef in steps.items()
        if isinstance(sdef, dict) and _direct_escape(sdef)
    }
    changed = True
    while changed:
        changed = False
        for name in step_names:
            if name in escapes:
                continue
            if adjacency.get(name, set()) & escapes:
                escapes.add(name)
                changed = True
    for name in sorted(step_names - escapes):
        errors.append(f"step '{name}' cannot reach a terminal or human edge: inescapable loop (C3)")

    return FlowDoctorResult(
        str(path),
        flow_id_s,
        "deterministic",
        not errors,
        errors,
        warnings,
    )


def _discover_flows(root: Path) -> list[Path]:
    base = root / FLOWS_DIR
    if not base.exists():
        return []
    return sorted(base.rglob("*.yaml")) + sorted(base.rglob("*.yml"))


def cmd_flow_doctor(args) -> int:
    root = Path(args.root).resolve()

    if args.flow:
        flows = [(root / args.flow).resolve()]
    else:
        flows = _discover_flows(root)

    results = [validate_flow(path) for path in flows]
    failed = [r for r in results if not r.ok]

    if args.json:
        print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))
    else:
        for result in results:
            status = "ok" if result.ok else "fail"
            print(f"{status} [{result.schema}]: {result.flow_path}")
            for warning in result.warnings:
                print(f"  warning: {warning}")
            for error in result.errors:
                print(f"  error: {error}")
        print(f"flows: {len(results)}  failed: {len(failed)}")

    return 1 if failed else 0

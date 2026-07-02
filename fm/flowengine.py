"""flow engine: a minimal deterministic driver for deterministic-control flows.

This is the control kernel from docs/073 (xid 4C7E9A2B1D63). It is deterministic:
given a flow and the sequence of node outcomes (labels) and human answers, the
path it takes is fixed. The non-determinism lives entirely in the node — here the
node is a pluggable input (`labels`) so the engine stays testable and pure.

The engine owns: next-step selection (`on`), per-step facet assembly, terminals,
human edges (`gate` / `handback`) with `resume`, cross-cutting `global_handback`,
and the `_invalid_or_absent` fallback. It does NOT do the business work.

The minimal driver assembles the declared facet manifest (names + permission); it
does not load facet content from disk — that is a later concern.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from fm.flowbridge import resolve_label_arg
from fm.flowdoctor import (
    FALLBACK_LABEL,
    TERMINALS,
    _human_edge_inner,
    _is_human_edge,
    _is_terminal,
    _load_flow,
    validate_flow,
)


@dataclass
class EngineResult:
    flow_id: str | None
    outcome: str | None  # COMPLETE | ABORT | None (engine error)
    ok: bool             # True when the engine reached a terminal cleanly
    steps_executed: int
    trace: list[dict] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "flow_id": self.flow_id,
            "outcome": self.outcome,
            "ok": self.ok,
            "steps_executed": self.steps_executed,
            "trace": self.trace,
            "error": self.error,
        }


def _mode(sdef: dict) -> str:
    if sdef.get("capability"):
        return "capability"  # ② non-deterministic consolidation
    if sdef.get("result_map") is not None:
        return "tool"  # ③ deterministic execution
    return "route"  # ① pure routing / human edge


# --- single-transition core -------------------------------------------------
#
# Both drivers share these pure functions: `run_flow` (one-shot, scripted
# labels/answers) and the resumable state driver in fm/flowstate.py. A
# position is a plain JSON-serializable dict:
#
#   {"kind": "step", "step": <name>}
#   {"kind": "suspended", "suspend": {...}}   awaiting a human answer
#   {"kind": "done", "outcome": COMPLETE|ABORT, "reason": <str>}
#
# `apply_label` / `apply_answer` return (new_position, events, error). On
# error the position is unusable for further progress and the caller decides
# whether to abort (run_flow) or leave persisted state unchanged (flowstate).


def enter_event(steps_map: dict, step: str) -> tuple[dict | None, str | None]:
    sdef = steps_map.get(step)
    if not isinstance(sdef, dict):
        return None, f"step '{step}' is not defined"
    return {
        "event": "enter",
        "step": step,
        "mode": _mode(sdef),
        "facets": sdef.get("facets", []),
        "permission": sdef.get("permission", {}),
    }, None


def initial_position(flow_data: dict) -> tuple[dict | None, str | None]:
    steps_map = flow_data.get("steps") or {}
    entry = flow_data.get("entry")
    if entry not in steps_map:
        return None, f"entry '{entry}' is not a known step"
    return {"kind": "step", "step": entry}, None


def apply_label(flow_data: dict, position: dict, label: str) -> tuple[dict, list[dict], str | None]:
    """Consume one node label at a step position.

    Suspension events (`suspend` / `global_handback`) are emitted when the
    answer is applied, not here, so one-shot and resumable traces agree.
    """
    steps_map = flow_data.get("steps") or {}
    global_handback = flow_data.get("global_handback") or {}
    current = position.get("step")
    sdef = steps_map.get(current)
    if not isinstance(sdef, dict):
        return position, [], f"step '{current}' is not defined"

    # Cross-cutting uncertainty (or any flow-level handback) may fire from any
    # step. It is matched by label name, not declared per step.
    if label in global_handback:
        hb = global_handback[label]
        suspend = {
            "source": "global_handback",
            "name": label,
            "to": hb.get("to"),
            "ask": hb.get("ask"),
            "resume": hb.get("resume"),
            "step": current,
        }
        return {"kind": "suspended", "suspend": suspend}, [], None

    on = sdef.get("on") or {}
    fallback = label not in on
    target = on.get(label, on.get(FALLBACK_LABEL))
    events = [{"event": "emit", "step": current, "label": label, "fallback": fallback}]
    if target is None:
        return position, events, f"step '{current}' has no edge for '{label}' and no fallback"

    if _is_terminal(target):
        events.append({"event": "terminate", "outcome": target, "reason": "transition"})
        return {"kind": "done", "outcome": target, "reason": "transition"}, events, None

    if _is_human_edge(target):
        kind, inner = _human_edge_inner(target)
        suspend = {
            "source": "edge",
            "kind": kind,
            "to": inner.get("to"),
            "ask": inner.get("ask"),
            "resume": inner.get("resume"),
            "step": current,
        }
        return {"kind": "suspended", "suspend": suspend}, events, None

    if target not in steps_map:
        return position, events, f"target '{target}' from step '{current}' is not a known step"
    entered, err = enter_event(steps_map, target)
    if err:
        return position, events, err
    events.append(entered)
    return {"kind": "step", "step": target}, events, None


def apply_answer(flow_data: dict, position: dict, answer: str) -> tuple[dict, list[dict], str | None]:
    """Resolve a suspended position with a human answer."""
    steps_map = flow_data.get("steps") or {}
    suspend = position.get("suspend") or {}
    resume = suspend.get("resume")
    target = resume.get(answer) if isinstance(resume, dict) else resume

    if suspend.get("source") == "global_handback":
        events = [
            {
                "event": "global_handback",
                "name": suspend.get("name"),
                "to": suspend.get("to"),
                "ask": suspend.get("ask"),
                "answer": answer,
                "resume": target,
            }
        ]
        if _is_terminal(target):
            events.append({"event": "terminate", "outcome": target, "reason": "global_handback"})
            return {"kind": "done", "outcome": target, "reason": "global_handback"}, events, None
        if target not in steps_map:
            events.append({"event": "terminate", "outcome": "ABORT", "reason": "invalid_global_resume"})
            return {"kind": "done", "outcome": "ABORT", "reason": "invalid_global_resume"}, events, None
        entered, err = enter_event(steps_map, target)
        if err:
            return position, events, err
        events.append(entered)
        return {"kind": "step", "step": target}, events, None

    events = [
        {
            "event": "suspend",
            "kind": suspend.get("kind"),
            "step": suspend.get("step"),
            "to": suspend.get("to"),
            "ask": suspend.get("ask"),
            "answer": answer,
            "resume": target,
        }
    ]
    if target is None:
        events.append({"event": "terminate", "outcome": "ABORT", "reason": "invalid_resume_answer"})
        return {"kind": "done", "outcome": "ABORT", "reason": "invalid_resume_answer"}, events, None
    if _is_terminal(target):
        events.append({"event": "terminate", "outcome": target, "reason": "resume"})
        return {"kind": "done", "outcome": target, "reason": "resume"}, events, None
    if target not in steps_map:
        events.append({"event": "terminate", "outcome": "ABORT", "reason": "invalid_resume_target"})
        return {"kind": "done", "outcome": "ABORT", "reason": "invalid_resume_target"}, events, None
    entered, err = enter_event(steps_map, target)
    if err:
        return position, events, err
    events.append(entered)
    return {"kind": "step", "step": target}, events, None


def run_flow(flow_data: dict, *, labels, answers, max_steps: int = 100) -> EngineResult:
    """Drive a (validated) deterministic flow with scripted node outcomes.

    `labels` are consumed in visit order (one per step entered); `answers` are
    consumed in order (one per human suspend). Loops are supported, bounded by
    `max_steps`.
    """
    trace: list[dict] = []
    steps_map = flow_data.get("steps") or {}
    flow_id = flow_data.get("flow_id")
    flow_id_s = str(flow_id) if flow_id else None
    label_q = list(labels)
    answer_q = list(answers)
    executed = 0

    def fail(msg: str) -> EngineResult:
        trace.append({"event": "error", "message": msg})
        return EngineResult(flow_id_s, None, False, executed, trace, msg)

    position, err = initial_position(flow_data)
    if err:
        return fail(err)

    while True:
        if position["kind"] == "done":
            return EngineResult(flow_id_s, position["outcome"], True, executed, trace)

        if position["kind"] == "step":
            if executed >= max_steps:
                return fail(f"max_steps ({max_steps}) exceeded")
            entered, err = enter_event(steps_map, position["step"])
            if err:
                return fail(err)
            executed += 1
            trace.append(entered)
            if not label_q:
                return fail(f"no node label available for step '{position['step']}'")
            label = label_q.pop(0)
            position, events, err = apply_label(flow_data, position, label)
            trace.extend(events)
            if err:
                return fail(err)
            # Entering the next step is traced by this loop, not by the core,
            # so the max_steps guard stays in one place.
            if trace and trace[-1].get("event") == "enter":
                trace.pop()
            continue

        # suspended
        suspend = position.get("suspend") or {}
        if not answer_q:
            if suspend.get("source") == "global_handback":
                return fail(f"no human answer for global_handback '{suspend.get('name')}'")
            return fail(f"no human answer for {suspend.get('kind')} at step '{suspend.get('step')}'")
        answer = answer_q.pop(0)
        position, events, err = apply_answer(flow_data, position, answer)
        trace.extend(events)
        if err:
            return fail(err)
        if trace and trace[-1].get("event") == "enter":
            trace.pop()


def _render_trace(result: EngineResult) -> list[str]:
    lines: list[str] = []
    for ev in result.trace:
        kind = ev["event"]
        if kind == "enter":
            lines.append(f"-> {ev['step']} [{ev['mode']}] facets={ev['facets']}")
        elif kind == "emit":
            tail = " (fallback)" if ev["fallback"] else ""
            lines.append(f"   emit '{ev['label']}'{tail}")
        elif kind == "suspend":
            lines.append(f"   {ev['kind']} -> {ev['to']}: ask={ev['ask']!r} answer='{ev['answer']}' resume={ev['resume']}")
        elif kind == "global_handback":
            lines.append(f"   global_handback '{ev['name']}' -> {ev['to']} answer='{ev['answer']}' resume={ev['resume']}")
        elif kind == "terminate":
            lines.append(f"== {ev['outcome']} ({ev['reason']})")
        elif kind == "error":
            lines.append(f"!! error: {ev['message']}")
    return lines


def cmd_flow_run(args) -> int:
    root = Path(args.root).resolve()
    path = (root / args.flow).resolve()

    # The engine only drives flows that statically close.
    vres = validate_flow(path)
    if vres.schema != "deterministic":
        print(f"not a deterministic flow ({vres.schema}): {path}")
        return 1
    if not vres.ok:
        print(f"flow fails flow doctor; refusing to run: {path}")
        for e in vres.errors:
            print(f"  error: {e}")
        return 1

    # Labels may be literal (`Go`) or bridged from a closed skill run log
    # (`log:<run-log-path>`); a run that has not passed the close gate must
    # not drive a transition, so a refused bridge refuses the whole run.
    labels: list[str] = []
    for raw in args.label or []:
        label, bridge = resolve_label_arg(raw, root)
        if label is None:
            print(f"label '{raw}' could not be bridged; refusing to run")
            print(f"  error: {bridge.error}")
            return 1
        if bridge is not None:
            print(f"bridged {bridge.run_log}: closure={bridge.closure} -> label={label}")
        labels.append(label)

    data = _load_flow(path)
    result = run_flow(
        data,
        labels=labels,
        answers=args.answer or [],
        max_steps=args.max_steps,
    )

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        for line in _render_trace(result):
            print(line)
        print(f"outcome: {result.outcome}  ok: {result.ok}  steps: {result.steps_executed}")

    return 0 if result.ok else 1

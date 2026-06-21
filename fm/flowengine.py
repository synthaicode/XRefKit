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


def run_flow(flow_data: dict, *, labels, answers, max_steps: int = 100) -> EngineResult:
    """Drive a (validated) deterministic flow with scripted node outcomes.

    `labels` are consumed in visit order (one per step entered); `answers` are
    consumed in order (one per human suspend). Loops are supported, bounded by
    `max_steps`.
    """
    trace: list[dict] = []
    steps_map = flow_data.get("steps") or {}
    global_handback = flow_data.get("global_handback") or {}
    flow_id = flow_data.get("flow_id")
    flow_id_s = str(flow_id) if flow_id else None
    label_q = list(labels)
    answer_q = list(answers)
    executed = 0

    def fail(msg: str) -> EngineResult:
        trace.append({"event": "error", "message": msg})
        return EngineResult(flow_id_s, None, False, executed, trace, msg)

    def terminate(outcome: str, reason: str) -> EngineResult:
        trace.append({"event": "terminate", "outcome": outcome, "reason": reason})
        return EngineResult(flow_id_s, outcome, True, executed, trace)

    current = flow_data.get("entry")
    if current not in steps_map:
        return fail(f"entry '{current}' is not a known step")

    while True:
        if executed >= max_steps:
            return fail(f"max_steps ({max_steps}) exceeded")
        sdef = steps_map.get(current)
        if not isinstance(sdef, dict):
            return fail(f"step '{current}' is not defined")
        executed += 1
        trace.append(
            {
                "event": "enter",
                "step": current,
                "mode": _mode(sdef),
                "facets": sdef.get("facets", []),
                "permission": sdef.get("permission", {}),
            }
        )

        if not label_q:
            return fail(f"no node label available for step '{current}'")
        label = label_q.pop(0)

        # Cross-cutting uncertainty (or any flow-level handback) may fire from any
        # step. It is matched by label name, not declared per step.
        if label in global_handback:
            hb = global_handback[label]
            if not answer_q:
                return fail(f"no human answer for global_handback '{label}'")
            answer = answer_q.pop(0)
            resume = hb.get("resume")
            target = resume.get(answer) if isinstance(resume, dict) else resume
            trace.append(
                {
                    "event": "global_handback",
                    "name": label,
                    "to": hb.get("to"),
                    "ask": hb.get("ask"),
                    "answer": answer,
                    "resume": target,
                }
            )
            if _is_terminal(target):
                return terminate(target, "global_handback")
            if target not in steps_map:
                return terminate("ABORT", "invalid_global_resume")
            current = target
            continue

        on = sdef.get("on") or {}
        fallback = label not in on
        target = on.get(label, on.get(FALLBACK_LABEL))
        trace.append({"event": "emit", "step": current, "label": label, "fallback": fallback})
        if target is None:
            return fail(f"step '{current}' has no edge for '{label}' and no fallback")

        if _is_terminal(target):
            return terminate(target, "transition")

        if _is_human_edge(target):
            kind, inner = _human_edge_inner(target)
            if not answer_q:
                return fail(f"no human answer for {kind} at step '{current}'")
            answer = answer_q.pop(0)
            resume = inner.get("resume")
            rt = resume.get(answer) if isinstance(resume, dict) else resume
            trace.append(
                {
                    "event": "suspend",
                    "kind": kind,
                    "step": current,
                    "to": inner.get("to"),
                    "ask": inner.get("ask"),
                    "answer": answer,
                    "resume": rt,
                }
            )
            if rt is None:
                return terminate("ABORT", "invalid_resume_answer")
            if _is_terminal(rt):
                return terminate(rt, "resume")
            if rt not in steps_map:
                return terminate("ABORT", "invalid_resume_target")
            current = rt
            continue

        if target not in steps_map:
            return fail(f"target '{target}' from step '{current}' is not a known step")
        current = target


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

    data = _load_flow(path)
    result = run_flow(
        data,
        labels=args.label or [],
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

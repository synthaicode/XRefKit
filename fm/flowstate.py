"""flow state: a resumable, incremental driver for deterministic flows.

`fm flow run` is one-shot: every node label and human answer is scripted up
front. This driver persists the engine position between invocations so a
harness can interleave the probabilistic work:

    fm flow start   --flow flows/<f>.yaml [--state <path>]
    fm flow next    --state <path>          # what the flow needs now
    (harness: fm skill run -> executor subagent -> verify -> close)
    fm flow advance --state <path> --label log:<run-log>   # bridge + move
    fm flow advance --state <path> --answer <answer>       # resolve suspend

The engine core (fm/flowengine.py) stays pure; this module only adds
serialization. The flow file is content-hashed at `start` and every later
command refuses to act if the file changed, so a state never silently drives
a different flow than the one it was started on.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

from fm.flowbridge import resolve_label_arg
from fm.flowdoctor import _load_flow, _skill_bindings, validate_flow
from fm.flowengine import apply_answer, apply_label, enter_event, initial_position

STATE_VERSION = 1
STATES_DIR = "work/flows"


def _flow_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _status_of(position: dict) -> str:
    kind = position.get("kind")
    if kind == "step":
        return "awaiting_label"
    if kind == "suspended":
        return "awaiting_answer"
    outcome = position.get("outcome")
    return "complete" if outcome == "COMPLETE" else "abort"


def _default_state_path(root: Path, flow_id: str) -> Path:
    return root / STATES_DIR / f"{flow_id}.state.json"


def _load_state(state_path: Path) -> tuple[dict | None, str | None]:
    if not state_path.exists():
        return None, f"state file not found: {state_path}"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"state file is not valid JSON: {exc}"
    if state.get("state_version") != STATE_VERSION:
        return None, f"unsupported state_version: {state.get('state_version')}"
    return state, None


def _save_state(state_path: Path, state: dict) -> None:
    state["updated"] = date.today().isoformat()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _load_flow_for_state(root: Path, state: dict) -> tuple[dict | None, str | None]:
    flow_path = root / state["flow"]
    if not flow_path.exists():
        return None, f"flow file not found: {flow_path}"
    if _flow_hash(flow_path) != state["flow_hash"]:
        return None, (
            "flow file changed since `fm flow start`; refusing to act on stale "
            "state. Restart the flow (fm flow start --force) after reviewing the change"
        )
    return _load_flow(flow_path), None


def _step_report(root: Path, flow_data: dict, position: dict) -> dict:
    step = position["step"]
    sdef = (flow_data.get("steps") or {}).get(step) or {}
    bound_skill = sdef.get("skill")
    report = {
        "step": step,
        "capability": sdef.get("capability"),
        "skill": bound_skill,
        "facets": sdef.get("facets", []),
        "permission": sdef.get("permission", {}),
        "labels": sorted(k for k in (sdef.get("on") or {})),
    }
    if isinstance(bound_skill, str):
        binding = _skill_bindings(root).get(bound_skill)
        if binding:
            report["skill_meta"] = binding["meta"]
    return report


def _suspend_report(position: dict) -> dict:
    suspend = position.get("suspend") or {}
    resume = suspend.get("resume")
    return {
        "kind": suspend.get("kind") or suspend.get("source"),
        "step": suspend.get("step"),
        "to": suspend.get("to"),
        "ask": suspend.get("ask"),
        "answers": sorted(resume) if isinstance(resume, dict) else ["<any>"],
    }


def _report(root: Path, flow_data: dict, state: dict) -> dict:
    position = state["position"]
    status = _status_of(position)
    report: dict = {
        "flow_id": state["flow_id"],
        "status": status,
        "executed": state["executed"],
        "max_steps": state["max_steps"],
    }
    if status == "awaiting_label":
        report["current"] = _step_report(root, flow_data, position)
    elif status == "awaiting_answer":
        report["suspended"] = _suspend_report(position)
    else:
        report["outcome"] = position.get("outcome")
        report["reason"] = position.get("reason")
    return report


def _print_report(report: dict) -> None:
    print(f"flow: {report['flow_id']}  status: {report['status']}  steps: {report['executed']}/{report['max_steps']}")
    if "current" in report:
        cur = report["current"]
        print(f"  step: {cur['step']}  capability: {cur['capability']}  skill: {cur['skill']}")
        if cur.get("skill_meta"):
            print(f"  skill_meta: {cur['skill_meta']}")
        print(f"  facets: {cur['facets']}  permission: {cur['permission']}")
        print(f"  labels: {cur['labels']}")
    if "suspended" in report:
        sus = report["suspended"]
        print(f"  suspended[{sus['kind']}] at {sus['step']} -> {sus['to']}")
        print(f"  ask: {sus['ask']}")
        print(f"  answers: {sus['answers']}")
    if "outcome" in report:
        print(f"  outcome: {report['outcome']} ({report['reason']})")


def cmd_flow_start(args) -> int:
    root = Path(args.root).resolve()
    flow_path = (root / args.flow).resolve()

    vres = validate_flow(flow_path)
    if vres.schema != "deterministic":
        print(f"not a deterministic flow ({vres.schema}): {flow_path}")
        return 1
    if not vres.ok:
        print(f"flow fails flow doctor; refusing to start: {flow_path}")
        for e in vres.errors:
            print(f"  error: {e}")
        return 1

    flow_data = _load_flow(flow_path)
    flow_id = str(flow_data.get("flow_id") or flow_path.stem)
    state_path = Path(args.state) if args.state else _default_state_path(root, flow_id)
    if not state_path.is_absolute():
        state_path = root / state_path
    if state_path.exists() and not args.force:
        print(f"state file already exists (use --force to restart): {state_path}")
        return 1

    position, err = initial_position(flow_data)
    if err:
        print(f"error: {err}")
        return 1
    entered, err = enter_event(flow_data.get("steps") or {}, position["step"])
    if err:
        print(f"error: {err}")
        return 1

    state = {
        "state_version": STATE_VERSION,
        "flow": flow_path.relative_to(root).as_posix(),
        "flow_id": flow_id,
        "flow_hash": _flow_hash(flow_path),
        "max_steps": args.max_steps,
        "executed": 1,
        "position": position,
        "trace": [entered],
    }
    _save_state(state_path, state)

    report = _report(root, flow_data, state)
    report["state"] = str(state_path)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"state: {state_path}")
        _print_report(report)
    return 0


def cmd_flow_next(args) -> int:
    root = Path(args.root).resolve()
    state_path = Path(args.state)
    if not state_path.is_absolute():
        state_path = root / state_path
    state, err = _load_state(state_path)
    if err is None:
        flow_data, err = _load_flow_for_state(root, state)
    if err:
        print(f"error: {err}")
        return 1

    report = _report(root, flow_data, state)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_report(report)
    return 0


def cmd_flow_advance(args) -> int:
    root = Path(args.root).resolve()
    state_path = Path(args.state)
    if not state_path.is_absolute():
        state_path = root / state_path
    state, err = _load_state(state_path)
    if err is None:
        flow_data, err = _load_flow_for_state(root, state)
    if err:
        print(f"error: {err}")
        return 1

    position = state["position"]
    status = _status_of(position)
    if status in {"complete", "abort"}:
        print(f"error: flow already terminated ({position.get('outcome')})")
        return 1

    if status == "awaiting_label":
        if not args.label or args.answer:
            print("error: this flow position needs --label (a node label or log:<run-log>)")
            return 1
        label, bridge = resolve_label_arg(args.label, root)
        if label is None:
            print(f"label '{args.label}' could not be bridged; state unchanged")
            print(f"  error: {bridge.error}")
            return 1
        if bridge is not None:
            print(f"bridged {bridge.run_log}: closure={bridge.closure} -> label={label}")
        new_position, events, err = apply_label(flow_data, position, label)
    else:
        if not args.answer or args.label:
            print("error: this flow position needs --answer")
            return 1
        new_position, events, err = apply_answer(flow_data, position, args.answer)

    if err:
        print(f"error: {err} (state unchanged)")
        return 1

    entered_new_step = bool(events) and events[-1].get("event") == "enter"
    if entered_new_step:
        if state["executed"] >= state["max_steps"]:
            print(f"error: max_steps ({state['max_steps']}) exceeded (state unchanged)")
            return 1
        state["executed"] += 1

    state["position"] = new_position
    state["trace"].extend(events)
    _save_state(state_path, state)

    report = _report(root, flow_data, state)
    if args.json:
        report["events"] = events
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for ev in events:
            print(f"  event: {ev}")
        _print_report(report)
    return 0

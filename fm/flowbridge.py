"""flow bridge: deterministic mapping from a closed skill run log to a flow label.

This is the connection point between the two control layers:

- the workflow protocol (`fm skill run ... verify ... close`) controls the
  inside of one Skill run and ends in a deterministic closure gate;
- the deterministic flow kernel (`fm flow run`, docs/073) controls the
  transitions between steps and consumes one node label per step.

The bridge reads the closure gate outcome that `fm skill close` records in the
run log's Phase Events and converts it into the node label the engine
consumes. The mapping is fixed and total over closed runs:

- closure `done`      -> ``Go``
- closure `escalated` -> ``uncertainty`` (routes to the flow's declared
  human edge / ``global_handback``)
- not closed          -> no label; the bridge refuses. A run that has not
  passed the close gate must not drive a flow transition.

Only `fm skill close` writes the ``role=`closure_gate``` phase event, so the
bridge trusts that marker rather than any manually editable status line.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

LABEL_FOR_CLOSURE = {
    "done": "Go",
    "escalated": "uncertainty",
}

_LOAD_GATE_MARKER = "## Skill Load Gate\n\n- status: `opened_by_fm_skill_run`"
_CLOSURE_EVENT_RE = re.compile(
    r"^- \d{4}-\d{2}-\d{2} `closure` -> `(done|escalated)` role=`closure_gate`",
    re.M,
)


@dataclass
class BridgeResult:
    ok: bool
    run_log: str
    closure: str | None = None
    label: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "run_log": self.run_log,
            "closure": self.closure,
            "label": self.label,
            "error": self.error,
        }


def derive_flow_label(log_path: Path) -> BridgeResult:
    log_s = str(log_path)
    if not log_path.exists():
        return BridgeResult(ok=False, run_log=log_s, error=f"run log not found: {log_path}")

    text = log_path.read_text(encoding="utf-8")
    if _LOAD_GATE_MARKER not in text:
        return BridgeResult(
            ok=False,
            run_log=log_s,
            error="run log is missing an opened Skill Load Gate; not an fm skill run log",
        )

    closures = _CLOSURE_EVENT_RE.findall(text)
    if not closures:
        return BridgeResult(
            ok=False,
            run_log=log_s,
            error="run log has no closure_gate phase event; run `fm skill close` first",
        )

    closure = closures[-1]
    return BridgeResult(ok=True, run_log=log_s, closure=closure, label=LABEL_FOR_CLOSURE[closure])


def resolve_label_arg(raw: str, root: Path) -> tuple[str | None, BridgeResult | None]:
    """Resolve one `--label` argument for `fm flow run`.

    A plain value is passed through unchanged. A ``log:<path>`` value is
    resolved through the bridge; the path is taken relative to `root` unless
    absolute. Returns (label, bridge_result); label is None when the bridge
    refused.
    """
    if not raw.startswith("log:"):
        return raw, None
    log_path = Path(raw[len("log:"):])
    if not log_path.is_absolute():
        log_path = root / log_path
    result = derive_flow_label(log_path)
    return (result.label if result.ok else None), result


def cmd_flow_label(args) -> int:
    root = Path(args.root).resolve()
    log_path = Path(args.log)
    if not log_path.is_absolute():
        log_path = root / log_path
    result = derive_flow_label(log_path)

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    elif result.ok:
        print(f"ok: {result.run_log}")
        print(f"  closure: {result.closure}")
        print(f"  label: {result.label}")
    else:
        print("fail: flow label")
        print(f"  error: {result.error}")
    return 0 if result.ok else 1

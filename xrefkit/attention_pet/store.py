"""Transactional local session and bounded history; recovery preserves evidence."""
import json
import os
import threading
import time
import uuid
from pathlib import Path

from .evaluator import Weights, evaluate
from .model import WorkingSet


class Store:
    def __init__(self, path: Path | None = None, weights: Weights = Weights()):
        self.path = path
        self.weights = weights
        self.lock = threading.RLock()
        self.ws = None
        self.history = []
        self.recoveries = []
        if path and path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            self.ws = WorkingSet.model_validate(data["workingSet"])
            # Re-evaluate retained snapshots rather than trusting persisted scores.
            for sample in data["samples"][-100:]:
                ws = WorkingSet.model_validate(sample["workingSet"])
                prev = self.history[-1]["state"] if self.history else None
                self.history.append({"workingSet": ws.model_dump(), "state": evaluate(ws, prev, [h["state"] for h in self.history], weights)})
            if not self.history or self.history[-1]["workingSet"] != self.ws.model_dump():
                raise ValueError("session snapshot/history mismatch")
            self.recoveries = data["recoveries"][-100:]

    def view(self):
        with self.lock:
            return {"workingSet": self.ws.model_dump() if self.ws else None,
                    "state": self.history[-1]["state"] if self.history else None,
                    "history": [h["state"] for h in self.history], "recoveries": list(self.recoveries)}

    def _commit(self, ws, history, recoveries):
        data = {"workingSet": ws.model_dump(), "samples": history[-100:], "recoveries": recoveries[-100:]}
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_name(self.path.name + ".tmp")
            try:
                with temporary.open("w", encoding="utf-8") as stream:
                    json.dump(data, stream, ensure_ascii=False, allow_nan=False)
                    stream.flush()
                    os.fsync(stream.fileno())
                temporary.replace(self.path)
            finally:
                temporary.unlink(missing_ok=True)
        self.ws, self.history, self.recoveries = ws, history[-100:], recoveries[-100:]

    def submit(self, ws: WorkingSet):
        with self.lock:
            prev = self.history[-1]["state"] if self.history else None
            if self.ws and self.ws.taskId == ws.taskId:
                # Replays cannot fabricate trend or overwrite a changed observation.
                if ws == self.ws:
                    return self.view()
            state = evaluate(ws, prev, [h["state"] for h in self.history], self.weights)
            history = self.history if self.ws and self.ws.taskId == ws.taskId else []
            recoveries = self.recoveries if history else []
            self._commit(ws, history + [{"workingSet": ws.model_dump(), "state": state}], recoveries)
            return self.view()

    def recover(self, action: str, expected: float):
        with self.lock:
            if self.ws is None:
                raise ValueError("supply a working set first")
            if self.ws.observedAt != expected:
                raise ValueError("state changed; refresh before recovery")
            if action not in {"fix", "summarize", "split", "externalize", "archive", "resolve", "rebase", "restart"}:
                raise ValueError("unsupported recovery action")
            ws = self.ws.model_copy(deep=True)
            before = ws.model_dump()
            result = {"action": action, "executedAt": time.time(), "contextId": ws.contextId}
            if action in {"externalize", "split", "resolve", "rebase", "restart"}:
                # These actions produce an explicit handoff; they do not manipulate Codex.
                result["handoff"] = {"purpose": action, "workingSet": before,
                    "instruction": {
                        "externalize": "Save this exact evidence-bearing Working Set for later reuse.",
                        "split": "Choose goal boundaries; keep cross-boundary dependencies explicit before starting separate contexts.",
                        "resolve": "Resolve active questions/conflicts with their owner and submit a reviewed snapshot.",
                        "rebase": "Review current goals, constraints and fixed decisions; submit a rebuilt snapshot with evidence.",
                        "restart": "Start a new Codex chat using this bundle; validate the corrected premise before recording fresh trajectory observations.",
                    }[action]}
                result["effect"] = "handoff_created"
                self._commit(ws, self.history, self.recoveries + [result])
                return {**self.view(), "recovery": result}
            if action == "fix":
                changed = [i for i in ws.items if i.kind == "decision" and i.status == "active" and not i.fixed]
                for item in changed:
                    item.fixed = True
            else:
                # Only inactive work or unreferenced historical exploration may leave the active set.
                active_ids = {i.id for i in ws.items if i.status == "active" and i.kind != "history"}
                referenced = set()
                frontier = set(active_ids)
                while frontier:
                    related = {e.target for e in ws.dependencies if e.source in frontier} | {e.source for e in ws.dependencies if e.target in frontier}
                    frontier = related - active_ids - referenced
                    referenced |= related
                changed = [i for i in ws.items if i.status != "archived" and
                           (i.status == "done" or i.kind == "history") and i.id not in referenced]
                for item in changed:
                    item.status = "archived"
            result["affectedIds"] = [i.id for i in changed]
            result["effect"] = "working_set_updated" if changed else "no_eligible_items"
            result["summary"] = [{"id": i.id, "text": i.text, "source": i.source} for i in changed]
            if changed:
                ws.observedAt = max(time.time(), self.ws.observedAt + 0.001)
                state = evaluate(ws, self.history[-1]["state"], [h["state"] for h in self.history], self.weights)
                history = self.history + [{"workingSet": ws.model_dump(), "state": state}]
            else:
                history = self.history
            self._commit(ws, history, self.recoveries + [result])
            return {**self.view(), "recovery": result}

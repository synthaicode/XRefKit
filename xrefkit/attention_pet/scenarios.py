"""Synthetic annotated conversation fixtures, not empirical model outcomes."""
from .model import Conversation, extract


def scenario(name: str, step: int = 1) -> dict:
    if name not in {"A", "B", "C", "D", "E"} or not 1 <= step <= 5:
        raise ValueError("scenario A-E and step 1-5 required")
    turns = []
    if name in {"A", "B", "D"}:
        count = step if name in {"A", "B"} else 5
        for k in range(count):
            turn_id = f"turn-{k}"
            text = (f"Add independent requirement {k + 1}." if name == "A" else
                    f"Add requirement {k + 1}; preserve all earlier constraints and their dependencies.")
            items = [{"id": f"c{k}-{j}", "kind": "constraint", "text": f"Requirement {k + 1}.{j + 1}", "source": turn_id} for j in range(4)]
            items.append({"id": f"d{k}", "kind": "decision", "text": f"Decision {k + 1}", "source": turn_id,
                          "depth": 0 if name == "A" else k + 1})
            edges = []
            if name != "A":
                for item in items:
                    if item["kind"] == "constraint":
                        edges.append({"source": item["id"], "target": f"d{k}", "evidence": turn_id})
                    if k:
                        edges.append({"source": item["id"], "target": f"d{k-1}", "evidence": turn_id})
            if name == "D":
                items += [{"id": f"h{k}-{j}", "kind": "history", "text": f"Completed exploration {k}.{j}", "source": f"turn-{k}"} for j in range(3)]
                if k < 3:
                    items.append({"id": f"q{k}", "kind": "conflict", "text": f"Unresolved design conflict {k}", "source": turn_id})
            turns.append({"id": turn_id, "text": text, "items": items, "dependencies": edges})
        turns[-1]["observations"] = [{"id": "check", "kind": "validated", "context": "context-1", "evidence": "Synthetic reviewer: current constraints were retained."}]
    else:
        turns = [{"id": "turn-0", "text": "Use meters, not feet. The response still uses feet after correction.",
                  "items": [{"id": "units", "kind": "constraint", "text": "Use meters", "source": "turn-0"}],
                  "observations": [{"id": f"error-{k}", "kind": "correction_ignored", "context": "context-1", "evidence": f"Synthetic response {k + 1} still uses feet after explicit correction."} for k in range(step)]}]
    conversation = Conversation.model_validate({"taskId": f"demo-{name}", "contextId": "context-1", "observedAt": float(step * 30), "coverage": "reviewed", "turns": turns})
    ws = extract(conversation)
    if name == "E" and step >= 4:
        from .model import Observation
        ws.contextId = "context-2"
        ws.observations.append(Observation(id="fresh-check", kind="validated", context="context-2",
                                          evidence="Synthetic new-context response checked: units are meters."))
    return {"name": name, "step": step, "synthetic": True, "conversation": conversation.model_dump(), "workingSet": ws.model_dump()}

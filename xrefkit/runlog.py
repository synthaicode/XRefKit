"""JSONL run log writer and reader."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from .models import RunLogAggregate, RunLogEvent


_EVENT_ADAPTER = TypeAdapter(RunLogEvent)
_EVENT_LIST_ADAPTER = TypeAdapter(list[RunLogEvent])


class JsonlRunLogWriter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, event: RunLogEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")


def read_run_log_events(path: str | Path) -> list[RunLogEvent]:
    events: list[RunLogEvent] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at line {line_no}: {exc}") from exc
            events.append(_EVENT_ADAPTER.validate_python(raw))
    return events


def read_run_log_aggregate(path: str | Path, run_id: str) -> RunLogAggregate:
    events = [event for event in read_run_log_events(path) if event.run_id == run_id]
    return RunLogAggregate(run_id=run_id, events=_EVENT_LIST_ADAPTER.validate_python(events))

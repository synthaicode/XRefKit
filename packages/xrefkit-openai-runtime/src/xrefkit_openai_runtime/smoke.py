"""Exercise the CLI delegation path with a fixed, synthetic read-only turn."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from contextlib import closing
from dataclasses import asdict, dataclass
from hashlib import sha256
from http.client import HTTPSConnection, HTTPException
import json
import os
from pathlib import Path
import sqlite3
import sys
from time import monotonic, sleep
from uuid import uuid4

from .contracts import AssignmentRef
from .offline_context import ContextAssembly
from .offline_controller import (
    ControllerBinding, ControllerLimits, CurrentState, JournalEvent,
    OfflineController, OfflineJournal, ProviderReceipt,
)
from .offline_evaluation import ReviewAuthority
from .offline_responses import FakeResponse


MODEL = "gpt-4.1-mini-2025-04-14"
TOOL = "xrefkit_fixture_read"
DOCUMENT = "smoke-doc"
EXPECTED = "XREFKIT_SMOKE_OK"
INSTRUCTIONS = (
    f"Use {TOOL} with document_id {DOCUMENT}. "
    "Read the returned JSON and reply with exactly the value of its text field."
)


def _encode(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


class TurnStore:
    """The local CLI host owns publication; status lookups cannot start work."""

    def __init__(self, database: sqlite3.Connection) -> None:
        self.database = database
        database.executescript("""
            CREATE TABLE IF NOT EXISTS smoke_turn (
                execution TEXT PRIMARY KEY,
                thread TEXT NOT NULL,
                invocation TEXT NOT NULL,
                disposition TEXT NOT NULL,
                result TEXT,
                claimed INTEGER NOT NULL DEFAULT 0,
                UNIQUE (thread, invocation)
            );
            CREATE TABLE IF NOT EXISTS smoke_event (
                execution TEXT NOT NULL,
                event TEXT NOT NULL
            );
        """)

    def start(self, thread: str, invocation: str) -> tuple[str, bool]:
        execution = uuid4().hex
        with self.database:
            started = self.database.execute(
                "INSERT OR IGNORE INTO smoke_turn VALUES (?, ?, ?, 'running', NULL, 0)",
                (execution, thread, invocation),
            ).rowcount == 1
            original, = self.database.execute(
                "SELECT execution FROM smoke_turn WHERE thread = ? AND invocation = ?",
                (thread, invocation),
            ).fetchone()
        return original, started

    def record(self, execution: str, event: object) -> None:
        with self.database:
            self.database.execute(
                "INSERT INTO smoke_event VALUES (?, ?)", (execution, _encode(event).decode())
            )

    def finish(self, execution: str, disposition: str, result: str | None) -> None:
        with self.database:
            self.database.execute(
                "UPDATE smoke_turn SET disposition = ?, result = ? WHERE execution = ?",
                (disposition, result, execution),
            )

    def read(self, thread: str, execution: str, *, claim: bool, invocation: str | None = None) -> dict:
        scope = (
            "invocation NOT LIKE 'codex-turn:%'" if invocation is None else "invocation = ?"
        )
        identity = (execution, thread) if invocation is None else (execution, thread, invocation)
        with self.database:
            claimed_now = claim and self.database.execute(
                "UPDATE smoke_turn SET claimed = 1 "
                f"WHERE execution = ? AND thread = ? AND {scope} AND result IS NOT NULL AND claimed = 0",
                identity,
            ).rowcount == 1
            row = self.database.execute(
                f"SELECT disposition, result, claimed FROM smoke_turn WHERE execution = ? AND thread = ? AND {scope}",
                identity,
            ).fetchone()
        if row is None:
            return {"status": "execution_not_found"}
        disposition, result, presented = row
        payload = {"execution_id": execution, "status": disposition, "result_claimed": bool(presented)}
        if claimed_now:
            payload["result"] = result
        return payload


class StoredJournal(OfflineJournal):
    def __init__(self, store: TurnStore, execution: str) -> None:
        super().__init__()
        self.store = store
        self.execution = execution

    def append(self, event: JournalEvent) -> None:
        try:
            self.store.record(self.execution, asdict(event))
        except sqlite3.Error as exc:
            raise OSError("smoke journal unavailable") from exc
        super().append(event)


def _stub(body: dict, timeout: float, delay: float = 0) -> dict:
    if delay:
        sleep(min(delay, timeout))
    if "tools" in body:
        item = {"type": "function_call", "id": "stub-function", "call_id": "stub-call",
                "name": TOOL, "arguments": json.dumps({"document_id": DOCUMENT})}
        response_id = "stub-initial"
    else:
        tool_result = body["input"][-1]
        assert tool_result["call_id"] == "stub-call"
        item = {"type": "message", "id": "stub-message", "role": "assistant",
                "content": [{"type": "output_text", "text": json.loads(tool_result["output"])["text"]}]}
        response_id = "stub-final"
    return {"id": response_id, "status": "completed", "model": MODEL, "output": [item],
            "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}}


class TransportError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


def _openai(body: dict, timeout: float, *, receipt_timeout: float | None = None) -> dict:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise TransportError(0)
    # A fixed TLS destination, one POST, no redirects, proxies or automatic retries.
    deadline = monotonic() + timeout
    with closing(HTTPSConnection("api.openai.com", timeout=timeout)) as connection:
        connection.connect()
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise TimeoutError("wait expired before sending")
        connection.sock.settimeout(remaining)
        connection.request("POST", "/v1/responses", _encode(body), {
            "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        })
        if receipt_timeout is not None:
            connection.sock.settimeout(receipt_timeout)
        response = connection.getresponse()
        if response.status != 200:
            raise TransportError(response.status)
        raw = response.read(65537)
        if len(raw) > 65536:
            raise ValueError("Responses API result exceeds the smoke limit")
        data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("unexpected Responses API representation")
    return data


def _normalize(data: dict) -> FakeResponse:
    # Adapt the wire structure to the existing #202 parser. Unknown items are
    # retained so that the parser can reject them before any Tool starts.
    output = data.get("output")
    if isinstance(output, list):
        items = []
        for item in output:
            if (isinstance(item, dict) and item.get("type") == "message"
                    and item.get("role") == "assistant" and isinstance(item.get("content"), list)):
                for index, content in enumerate(item["content"]):
                    if not isinstance(content, dict):
                        items.append(content)
                        continue
                    kind = content.get("type")
                    items.append({
                        "type": "text" if kind == "output_text" else kind,
                        "id": f"{item['id']}-{index}" if item.get("id") else None,
                        "text": content.get("refusal") if kind == "refusal" else content.get("text"),
                    })
            else:
                items.append(item)
        output = items
    response = {name: data.get(name) for name in ("id", "status", "model", "usage")}
    return FakeResponse(None, {**response, "http": 200, "output": output})


@dataclass(frozen=True)
class TurnOutcome:
    disposition: str
    result: str | None = None


def _execute(
    store: TurnStore, thread: str, invocation: str, execution: str,
    transport: Callable[[dict, float], dict], wait_seconds: float, clock: Callable[[], float] = monotonic,
    *, deadline: float | None = None, stop_requested: Callable[[], bool] | None = None,
) -> TurnOutcome:
    assignment = AssignmentRef(
        flow_id=execution, run_id=execution, root_run_id=execution, work_item_id="synthetic-api-smoke",
        node_id="api-smoke", route_id="codex-single-turn-smoke", route_revision=1,
        binding_sha256=sha256(_encode([thread, invocation, execution])).hexdigest(),
        owner_generation=1, execution_id=execution,
    )
    payload = _encode({"instructions": [INSTRUCTIONS], "supporting_data": []})
    revision = sha256(payload).hexdigest()
    context = ContextAssembly(payload, _encode({
        "version": 1, "assignment": assignment.model_dump(mode="json"),
        "payload_sha256": revision, "hold_reason": None,
    }), None)
    binding = ControllerBinding(
        assignment, thread, invocation, MODEL, revision, "openai-responses-smoke", TOOL, DOCUMENT,
        "literal-smoke-result", sha256(EXPECTED.encode()).hexdigest(),
        ReviewAuthority("unused-for-exact-smoke", execution),
        ControllerLimits(8, 2, 1, 0, 0, 24576, 8192, 2),
        context, _encode({"status": "ok", "text": EXPECTED}), expected_smoke_text=EXPECTED,
    )
    controller = OfflineController(binding, journal=StoredJournal(store, execution))
    state = CurrentState(assignment, context, revision, binding.recipient, thread, invocation)
    if deadline is None:
        deadline = clock() + wait_seconds

    def waiting_ended() -> bool:
        return clock() >= deadline or (stop_requested is not None and stop_requested())

    def before_entry() -> CurrentState:
        if waiting_ended():
            controller.status(wait_ended=True)
        return state

    def step(tick: int, **kwargs):
        if waiting_ended():
            controller.status(wait_ended=True)
        return controller.step(tick, state, **kwargs)

    previous_call = None
    tick = 0
    consumed_entries = 0
    while tick < binding.limits.deadline_tick_exclusive:
        if waiting_ended():
            status = controller.status(wait_ended=True)
            return TurnOutcome("hold_reconciliation" if status.provider_entries else "wait_expired")
        status = step(tick, start=True, before_entry=before_entry)
        tick += 1
        pending = controller.provider_entries
        if len(pending) > consumed_entries:
            attempt = pending[-1]
            consumed_entries += 1
            body = json.loads(attempt.body)
            body.update(store=False, max_output_tokens=64)
            if "previous_response_id" in body:
                # Carry the original function call alongside its output with storage disabled.
                del body["previous_response_id"]
                if previous_call is None:
                    return TurnOutcome("hold_reconciliation")
                body["input"] = [previous_call, *body["input"]]
            else:
                body["input"] = [{"role": "user", "content": "Run the synthetic read-only turn."}]
                body["tool_choice"] = {"type": "function", "name": TOOL}
            remaining = deadline - clock()
            if waiting_ended():
                controller.status(wait_ended=True)
                return TurnOutcome("hold_reconciliation")
            store.record(execution, {"dispatch": attempt.entry.attempt,
                                     "request_sha256": sha256(_encode(body)).hexdigest()})
            if waiting_ended():
                controller.status(wait_ended=True)
                return TurnOutcome("hold_reconciliation")
            try:
                wire = transport(body, min(20, remaining))
                response = _normalize(wire)
                response_id = response.body["id"]
                if not isinstance(response_id, str) or not response_id:
                    return TurnOutcome("hold_reconciliation")
            except TransportError as exc:
                store.record(execution, {"transport_status": exc.status})
                if exc.status in (401, 403, 429):
                    return TurnOutcome(f"provider_http_{exc.status}")
                return TurnOutcome("hold_reconciliation")
            except (OSError, HTTPException, ValueError):
                return TurnOutcome("hold_reconciliation")
            output = wire.get("output")
            if attempt.entry.operation == "provider" and isinstance(output, list):
                previous_call = next((
                    {key: item.get(key) for key in ("type", "call_id", "name", "arguments")}
                    for item in output if isinstance(item, dict) and item.get("type") == "function_call"
                ), None)
            status = step(tick, observation=ProviderReceipt(
                attempt.entry, response_id, 1, "completed", wire_response=response,
            ))
            tick += 1
        elif status.disposition == "pending" and status.tool_entries:
            status = step(tick, tool_observed=True)
            tick += 1
        if status.candidate is not None:
            return TurnOutcome("candidate", status.candidate.decode())
        if status.disposition != "pending":
            return TurnOutcome(status.disposition)
    return TurnOutcome("hold_reconciliation")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", required=True, type=Path, help="Local SQLite evidence path")
    parser.add_argument("--provider", choices=("stub", "openai"), default="stub")
    parser.add_argument("--invocation-id", help="Stable ID of this particular CLI invocation")
    parser.add_argument("--read-result", metavar="EXECUTION_ID", help="Claim an existing result without running work")
    parser.add_argument("--wait-seconds", type=float, default=30)
    parser.add_argument("--stub-delay", type=float, default=0, help="Delay the stub's final response")
    args = parser.parse_args(argv)
    if not 0 < args.wait_seconds <= 60 or not 0 <= args.stub_delay <= 60:
        parser.error("wait and stub delay must be within the bounded smoke-run range")
    if args.invocation_id and args.invocation_id.startswith("codex-turn:"):
        parser.error("invocation ID is reserved for the Codex host")
    thread = os.environ.get("CODEX_THREAD_ID", "").strip()
    if not thread:
        print('{"status":"initialization_failed","reason":"missing_codex_thread_id"}')
        return 2
    if not args.read_result and args.provider == "openai" and not os.environ.get("OPENAI_API_KEY", "").strip():
        print('{"status":"initialization_failed","reason":"missing_openai_api_key"}')
        return 2
    try:
        with closing(sqlite3.connect(args.journal)) as database:
            store = TurnStore(database)
            if args.read_result:
                payload = store.read(thread, args.read_result, claim=True)
            else:
                invocation = args.invocation_id or uuid4().hex
                execution, started = store.start(thread, invocation)
                if started:
                    def transport(body, timeout):
                        if args.provider == "openai":
                            return _openai(body, timeout)
                        return _stub(body, timeout, args.stub_delay if "tools" not in body else 0)

                    outcome = _execute(store, thread, invocation, execution, transport, args.wait_seconds)
                    store.finish(execution, outcome.disposition, outcome.result)
                payload = store.read(thread, execution, claim=False)
                if started:
                    payload = store.read(thread, execution, claim=True)
    except sqlite3.Error:
        print('{"status":"hold_reconciliation","reason":"journal_unavailable"}')
        return 2
    print(json.dumps(payload))
    return 0 if payload["status"] == "candidate" else 2

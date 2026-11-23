"""Bounded text-only pilot for the Desktop Responses API route."""

import re
from http.client import HTTPException
from time import monotonic, sleep

MODEL = "gpt-4.1-mini-2025-04-14"
CASES = ("normal", "delayed", "stop")
STOP_RETRY = "stop-retry"
STOP_FINAL = "stop-final"
STOP_FOLLOWUPS = (STOP_RETRY, STOP_FINAL)
PILOT_CASES = (*CASES, *STOP_FOLLOWUPS)
FOLLOWUP_AUTHORIZATION = {STOP_RETRY: "XREFKIT_PILOT_STOP_RETRY_AUTHORIZED",
                          STOP_FINAL: "XREFKIT_PILOT_STOP_FINAL_AUTHORIZED"}
STOP_RETRY_INPUT_LIMIT = 1536
INPUT_LIMIT = 2048
OUTPUT_LIMIT = 512
BUDGET_MICRO_USD = 100_000
# Each token is reserved at the approved tariff ceiling of USD 10 per million.
RESERVATION = (INPUT_LIMIT + OUTPUT_LIMIT) * 10
# Standard text tariff ceilings for the pinned model: USD 1/M input and USD 2/M output.
FINAL_RESERVATION = STOP_RETRY_INPUT_LIMIT + OUTPUT_LIMIT * 2
POLL_LIMIT = 12
POLL_INTERVAL = 5
TERMINAL = {"completed", "cancelled", "failed", "incomplete"}
PENDING = {"queued", "in_progress"}
EXPECTED = "XREFKIT_PILOT_OK"
_RESPONSE_ID = re.compile(r"resp_[A-Za-z0-9]{1,128}")


def _usage(payload):
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None
    counts = usage.get("input_tokens"), usage.get("output_tokens")
    if any(type(value) is not int or value < 0 for value in counts):
        return None
    return counts


def inspect_unsettled_response(response_id, recorded_status, retrieve, *, input_limit=INPUT_LIMIT):
    """Check one saved response using read-only transport, without settling its reservation."""
    if not isinstance(response_id, str) or not _RESPONSE_ID.fullmatch(response_id):
        return {"status": "hold_reconciliation", "reason": "response_id_unavailable"}
    try:
        http, payload = retrieve("GET", f"/v1/responses/{response_id}", 5, None)
    except (HTTPException, OSError, ValueError):
        return {"status": "hold_reconciliation", "reason": "retrieve_unavailable"}
    if http != 200 or not isinstance(payload, dict):
        return {"status": "hold_reconciliation", "reason": "retrieve_unavailable"}
    if payload.get("id") != response_id or payload.get("model") != MODEL:
        return {"status": "hold_reconciliation", "reason": "response_mismatch"}
    status = payload.get("status")
    if (not isinstance(status, str) or status not in TERMINAL
            or (recorded_status in TERMINAL and status != recorded_status)):
        return {"status": "hold_reconciliation", "reason": "terminal_state_unverified"}
    usage = _usage(payload)
    if usage is None:
        return {"status": "hold_reconciliation", "reason": "usage_unknown", "provider_status": status}
    inputs, outputs = usage
    if inputs > input_limit or outputs > OUTPUT_LIMIT:
        return {"status": "hold_reconciliation", "reason": "usage_outside_reservation"}
    return {"status": "usage_evidence_ready", "provider_status": status,
            "input_tokens": inputs, "output_tokens": outputs}


def _result(payload):
    output = payload.get("output")
    if not isinstance(output, list) or len(output) != 1:
        return None
    message = output[0]
    if not isinstance(message, dict) or message.get("type") != "message" or message.get("role") != "assistant":
        return None
    content = message.get("content")
    if isinstance(content, list) and len(content) == 1 and isinstance(content[0], dict):
        item = content[0]
        if (item.get("type"), item.get("text"), item.get("annotations")) == ("output_text", EXPECTED, []):
            return EXPECTED
    return None


def execute(store, execution, case, admission, request, deadline):
    """Reserve before create; uncertainty retains the slot and prevents another create."""
    deadline = min(deadline, monotonic() + 120)
    retry = case in STOP_FOLLOWUPS
    input_limit = STOP_RETRY_INPUT_LIMIT if retry else INPUT_LIMIT
    reservation = FINAL_RESERVATION if case == STOP_FINAL else (input_limit + OUTPUT_LIMIT) * 10
    with admission() as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS desktop_pilot_v1 (
            scenario TEXT PRIMARY KEY, execution TEXT NOT NULL UNIQUE,
            reservation INTEGER NOT NULL, settled INTEGER NOT NULL DEFAULT 0,
            response_id TEXT, status TEXT NOT NULL DEFAULT 'unknown',
            input_tokens INTEGER, output_tokens INTEGER, reads INTEGER NOT NULL DEFAULT 0)"""
        )
        if "reads" not in {column[1] for column in db.execute("PRAGMA table_info(desktop_pilot_v1)")}:
            db.execute(f"ALTER TABLE desktop_pilot_v1 ADD COLUMN reads INTEGER NOT NULL DEFAULT {POLL_LIMIT}")
        reserved, pending = db.execute(
            "SELECT coalesce(sum(reservation), 0), count(*) - coalesce(sum(settled), 0) FROM desktop_pilot_v1"
        ).fetchone()
        if (db.execute("SELECT enabled FROM desktop_admission_v1 WHERE id=1").fetchone() == (0,)
                or pending or reserved + reservation > BUDGET_MICRO_USD
                or store.is_origin_closed(execution) or monotonic() >= deadline):
            return "hold_reconciliation", None
        if retry and db.execute(
            "SELECT count(*) FROM desktop_pilot_v1 WHERE scenario IN ('normal','delayed','stop') AND settled=1"
        ).fetchone() != (len(CASES),):
            return "hold_reconciliation", None
        if case == STOP_FINAL:
            prior = db.execute(
                "SELECT scenario,reservation,settled FROM desktop_pilot_v1 ORDER BY scenario"
            ).fetchall()
            if prior != [
                ("delayed", RESERVATION, 1), ("normal", RESERVATION, 1),
                ("stop", RESERVATION, 1), (STOP_RETRY, (STOP_RETRY_INPUT_LIMIT + OUTPUT_LIMIT) * 10, 1),
            ]:
                return "hold_reconciliation", None
        created = db.execute(
            "INSERT OR IGNORE INTO desktop_pilot_v1(scenario,execution,reservation,reads) VALUES(?,?,?,0)",
            (case, execution, reservation),
        ).rowcount
        if not created:
            return "hold_reconciliation", None

    def send(method, path, body=None):
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise TimeoutError("pilot reconciliation deadline reached")
        http, payload = request(method, path, min(5, remaining), body)
        if http != 200:
            raise ValueError("provider outcome uncertain")
        return payload

    def record(status, counts=None, *, settled=False):
        inputs, outputs = counts if counts is not None else (None, None)
        with admission() as db:
            db.execute(
                """UPDATE desktop_pilot_v1 SET response_id=?, status=?, input_tokens=?,
                output_tokens=?, settled=? WHERE execution=?""",
                (response_id, status, inputs, outputs, settled, execution),
            )

    # The fixed ASCII input is far below the input envelope; no caller text or Tools are admitted.
    prompt = f"Reply with exactly {EXPECTED}."
    if retry:
        prompt = (
            "Generate 96 numbered lines. Each line must contain its number followed by "
            "amber river violet garden. Continue in order until the output limit. "
            "Use only these invented words and the line numbers."
        )
    body = {"model": MODEL, "input": prompt, "max_output_tokens": OUTPUT_LIMIT,
            "background": True, "store": False}
    with admission() as db:
        if (db.execute("SELECT enabled FROM desktop_admission_v1 WHERE id=1").fetchone() == (0,)
                or store.is_origin_closed(execution)):
            return "hold_reconciliation", None
        payload = send("POST", "/v1/responses", body)
    response_id = payload.get("id")
    if not isinstance(response_id, str) or not _RESPONSE_ID.fullmatch(response_id):
        raise ValueError("provider response identity unavailable")
    path = f"/v1/responses/{response_id}"
    status = payload.get("status")
    if not isinstance(status, str) or status not in PENDING | TERMINAL:
        raise ValueError("invalid provider status")
    record(status)
    polls, cancel_sent = 0, False
    next_poll = monotonic()
    while status in PENDING:
        remaining = deadline - monotonic()
        if remaining <= 0:
            return "hold_reconciliation", None
        if store.is_origin_closed(execution) and not cancel_sent:
            with admission() as db:
                db.execute(
                    "INSERT INTO desktop_admission_v1 VALUES (1,0) "
                    "ON CONFLICT(id) DO UPDATE SET enabled=0"
                )
            cancel_sent = True
            payload = send("POST", path + "/cancel")
        else:
            if polls >= POLL_LIMIT:
                if not retry or cancel_sent:
                    return "hold_reconciliation", None
                # The read budget is spent; keep the original Stop watcher alive until the deadline.
                sleep(min(0.1, remaining))
                continue
            until_poll = next_poll - monotonic()
            if until_poll > 0:
                sleep(min(0.1, remaining, until_poll))
                continue
            polls += 1
            with admission() as db:
                db.execute("UPDATE desktop_pilot_v1 SET reads=? WHERE execution=?", (polls, execution))
            payload = send("GET", path)
            next_poll = monotonic() + POLL_INTERVAL
        if payload.get("id") != response_id:
            raise ValueError("provider response identity mismatch")
        status = payload.get("status")
        if not isinstance(status, str) or status not in PENDING | TERMINAL:
            raise ValueError("invalid provider status")
        record(status)

    usage = _usage(payload)
    if (usage is None or usage[0] > input_limit or usage[1] > OUTPUT_LIMIT
            or payload.get("model") != MODEL):
        record(status, usage)
        return "hold_reconciliation", None
    if retry and status in {"completed", "incomplete"}:
        record(status, usage, settled=True)
        return "fixture_" + status, None
    result = _result(payload) if status == "completed" else None
    settled = bool(result) or status == "cancelled"
    record(status, usage, settled=settled)
    if result:
        return "candidate", result
    return (status if settled else "hold_reconciliation"), None

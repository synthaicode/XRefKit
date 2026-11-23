"""Owner-bound readback and audit for the Windows Desktop pilot."""

from contextlib import closing
import csv
import ctypes
import os
from pathlib import Path
import re
import sqlite3
import subprocess

from .desktop_pilot import INPUT_LIMIT, OUTPUT_LIMIT, POLL_LIMIT, STOP_FOLLOWUPS, STOP_RETRY_INPUT_LIMIT, TERMINAL, inspect_unsettled_response


def authenticated_owner():
    if os.name != "nt":
        return None
    directory = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetSystemDirectoryW(directory, len(directory))
    if not 0 < length < len(directory):
        return None
    try:
        output = subprocess.run(
            [str(Path(directory.value) / "whoami.exe"), "/user", "/fo", "csv", "/nh"],
            capture_output=True, check=True, timeout=5,
        ).stdout.decode("mbcs")
        identity, = csv.reader(output.splitlines())
        sid = identity[1]
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None
    return sid if re.fullmatch(r"S-1-(?:[0-9]+-)*[0-9]+", sid) else None


def bind_owner(database, journal, execution, project):
    owner = authenticated_owner()
    if owner is None:
        raise ValueError("authenticated pilot owner unavailable")
    with database:
        database.execute(
            "CREATE TABLE IF NOT EXISTS desktop_pilot_owner_v1 "
            "(execution TEXT PRIMARY KEY, owner TEXT NOT NULL, project TEXT NOT NULL, journal TEXT NOT NULL)"
        )
        database.execute("INSERT INTO desktop_pilot_owner_v1 VALUES (?,?,?,?)",
                         (execution, owner, project, str(journal.resolve())))


def _audit_schema(db):
    db.execute(
        """CREATE TABLE IF NOT EXISTS desktop_pilot_reconciliation_v1 (
        execution TEXT NOT NULL, at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        outcome TEXT NOT NULL, response_id TEXT, provider_status TEXT, input_tokens INTEGER, output_tokens INTEGER)"""
    )


def _audit(db, execution, outcome, response_id=None):
    db.execute(
        "INSERT INTO desktop_pilot_reconciliation_v1 "
        "(execution,outcome,response_id,provider_status,input_tokens,output_tokens) VALUES (?,?,?,?,?,?)",
        (execution, outcome.get("reason", outcome["status"]), response_id, outcome.get("provider_status"),
         outcome.get("input_tokens"), outcome.get("output_tokens")),
    )


def reconcile(journal, thread, turn, case, project, admission, request):
    owner = authenticated_owner()
    denied = {"status": "hold_reconciliation", "reason": "owner_or_binding_unverified"}
    if owner is None or not journal.is_file():
        return denied
    journal = journal.resolve()
    with admission() as ledger, closing(sqlite3.connect(journal.as_uri() + "?mode=rw", uri=True)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='desktop_pilot_owner_v1'").fetchone():
            return denied
        binding = db.execute(
            """SELECT s.execution,s.disposition,b.owner,b.project,b.journal
            FROM smoke_turn s JOIN host_job j USING(execution)
            JOIN desktop_pilot_owner_v1 b USING(execution)
            WHERE s.thread=? AND s.invocation=? AND j.provider=?""",
            (thread, f"codex-turn:{turn}", f"pilot:{case}"),
        ).fetchone()
        if not binding or binding[2:] != (owner, project, str(journal)):
            return denied
        execution, disposition = binding[:2]
        if (disposition == "running"
                or ledger.execute("SELECT enabled FROM desktop_admission_v1 WHERE id=1").fetchone() != (0,)):
            return {"status": "hold_reconciliation", "reason": "rollback_required"}
        columns = {column[1] for column in ledger.execute("PRAGMA table_info(desktop_pilot_v1)")}
        if "reads" not in columns:
            return {"status": "hold_reconciliation", "reason": "lookup_history_unverified"}
        row = ledger.execute(
            "SELECT response_id,status,settled,reads FROM desktop_pilot_v1 WHERE execution=? AND scenario=?",
            (execution, case),
        ).fetchone()
        if row is None:
            return denied
        response_id, provider_status, settled, reads = row
        if settled:
            return {"status": "already_settled"}
        with db:
            _audit_schema(db)
            evidence = db.execute(
                "SELECT provider_status,input_tokens,output_tokens FROM desktop_pilot_reconciliation_v1 "
                "WHERE execution=? AND response_id=? AND outcome='usage_evidence_ready' ORDER BY rowid DESC LIMIT 1",
                (execution, response_id),
            ).fetchone()
        input_limit = STOP_RETRY_INPUT_LIMIT if case in STOP_FOLLOWUPS else INPUT_LIMIT
        if evidence:
            status, inputs, outputs = evidence
            if (status not in TERMINAL or (provider_status in TERMINAL and status != provider_status)
                    or type(inputs) is not int or not 0 <= inputs <= input_limit
                    or type(outputs) is not int or not 0 <= outputs <= OUTPUT_LIMIT):
                return {"status": "hold_reconciliation", "reason": "audit_evidence_invalid"}
        else:
            with db:
                lookups = db.execute(
                    "SELECT count(*) FROM desktop_pilot_reconciliation_v1 "
                    "WHERE execution=? AND outcome='lookup_requested'", (execution,),
                ).fetchone()[0]
                if response_id and reads + lookups >= POLL_LIMIT:
                    outcome = {"status": "hold_reconciliation", "reason": "lookup_limit"}
                    _audit(db, execution, outcome, response_id)
                    return outcome
                if response_id:
                    _audit(db, execution, {"status": "lookup_requested"}, response_id)
            outcome = inspect_unsettled_response(response_id, provider_status, request, input_limit=input_limit)
            with db:
                _audit(db, execution, outcome, response_id)
            if outcome["status"] != "usage_evidence_ready":
                return outcome
            status = outcome["provider_status"]
        # The evidence is durable before changing admission accounting. If the
        # second commit fails, the reservation stays held and readback is safe.
        ledger.execute("UPDATE desktop_pilot_v1 SET settled=1 WHERE execution=? AND settled=0", (execution,))
        return {"status": "usage_settled", "provider_status": status}

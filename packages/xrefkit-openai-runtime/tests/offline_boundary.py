from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Literal

from xrefkit_openai_runtime.contracts import AssignmentRef


@dataclass(frozen=True)
class RunnerEvidence:
    runner_id: str
    revision: int
    available: bool


@dataclass(frozen=True)
class DestinationGrant:
    destination: str
    purpose: str
    data_scope: str
    approved: bool = True
    expires_at: int = 10


class FakeBoundary:
    """In-memory counters for one synthetic operation, with no external I/O."""

    def __init__(self, assignment: AssignmentRef, runner: RunnerEvidence) -> None:
        self.assignment = assignment
        self.runner = runner
        self.invocations = 0
        self.sends = 0
        self._claim: tuple[str, str] | None = None
        self._reservation: str | None = None
        self.receipt: str | None = None
        self.settlements = 0
        self._lock = Lock()

    @property
    def reservation(self) -> str | None:
        return self._reservation

    def invoke_tool(
        self, assignment: AssignmentRef, runner: RunnerEvidence | None, *,
        tool: str = "offline.read", knowledge: tuple[str, int] | None = ("A00000000001", 1),
        command: str = "fixture-read", arguments: tuple[str, ...] = ("sample",),
        user_commands: tuple[str, ...] = ("fixture-read",), indirect: bool = False,
    ) -> bool:
        if assignment != self.assignment or runner != self.runner or not self.runner.available:
            return False
        if tool != "offline.read" or knowledge != ("A00000000001", 1):
            return False
        if command != "fixture-read" or command not in user_commands or arguments != ("sample",) or indirect:
            return False
        self.invocations += 1
        return True

    def send(
        self, assignment: AssignmentRef, runner: RunnerEvidence | None,
        destination: str, purpose: str, data_scope: str, grant: DestinationGrant | None, *,
        operation_id: str, attempt_id: str, now: int = 0, pending_reservation: str | None = None,
    ) -> Literal["allowed", "stale", "stale_runner", "missing", "denied", "expired", "mismatch", "duplicate"]:
        with self._lock:
            if assignment != self.assignment:
                return "stale"
            if runner != self.runner or not self.runner.available:
                return "stale_runner"
            if grant is None:
                return "missing"
            if not grant.approved:
                return "denied"
            if grant.expires_at <= now:
                return "expired"
            if (destination, purpose, data_scope) != (grant.destination, grant.purpose, grant.data_scope):
                return "mismatch"
            if self._claim is not None:
                return "duplicate"
            self._claim = operation_id, attempt_id
            self._reservation = pending_reservation
            self.sends += 1
            return "allowed"

    def reconcile(self, operation_id: str, attempt_id: str, receipt: str) -> bool:
        with self._lock:
            if self._claim != (operation_id, attempt_id) or self._reservation is None:
                return False
            self.receipt = receipt
            self._reservation = None
            self.settlements += 1
            return True

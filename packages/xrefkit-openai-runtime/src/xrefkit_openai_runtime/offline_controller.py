"""Single-work Controller for the #206 synthetic execution slice."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import copy
from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
import json
from threading import Lock, RLock
from typing import Literal

from .contracts import AssignmentRef, ExecutionResult
from .offline_budget import (
    Action, Authority, Decision, Grant, LedgerSnapshot, Observation, OfflineBudget, Rate,
    ReceiptRef, ScopeTotals, VerifiedReceipt,
)
from .offline_context import ContextAssembly
from .offline_dispatch import (
    OfflineToolDispatch, ToolContextPin, ToolDecision, ToolDefinition, ToolHost, ToolRequest,
    ToolReturnScope, tool_budget_action,
)
from .offline_evaluation import (
    Evaluation, EvaluationInputs, EvaluationPolicy, ReviewAuthority, controller_tool_criterion,
    evaluate_io, evaluation_digest, evaluation_policy_digest,
)
from .offline_responses import (
    AdapterResult, AttemptDiagnostics, FakeResponse, TextItem, ToolProposal, UsageObservation,
    normalize_controller_response, verified_context,
)


Operation = Literal["provider", "tool", "continuation"]
_OWNER_LOCK = Lock()
_OWNERS: dict[tuple[str, str, str, int], object] = {}
_STOP_PRIORITY = (
    "cancelled", "stop_authority", "hold_reconciliation", "hold_journal", "hold_context",
    "stop_deadline", "stop_attempt_limit", "hold_headroom", "stop_budget", "stop_no_progress",
)


def _encode(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode()


def _digest(content: bytes) -> str:
    return sha256(content).hexdigest()


@dataclass(frozen=True)
class ControllerLimits:
    deadline_tick_exclusive: int
    max_provider_entries: int
    max_tool_entries: int
    max_same_operation_provider_retries: int
    max_delay_ticks: int
    synthetic_budget_units: int
    reservation_units_per_entry: int
    max_consecutive_no_progress_decision_ticks: int

    def __post_init__(self) -> None:
        values = vars(self)
        if any(type(value) is not int or value < 0 for value in values.values()):
            raise ValueError("Controller limits must be nonnegative integers")
        if not self.reservation_units_per_entry or not self.max_consecutive_no_progress_decision_ticks:
            raise ValueError("Reservation and no-progress limits must be positive")


@dataclass(frozen=True)
class ControllerBinding:
    assignment: AssignmentRef
    session_id: str
    invocation_id: str
    selected_model: str
    instruction_revision: str
    recipient: str
    tool_name: str
    document_id: str
    criterion_revision: str
    criterion_sha256: str
    reviewer: ReviewAuthority
    limits: ControllerLimits
    context: ContextAssembly
    synthetic_tool_result: bytes = field(repr=False)
    initial_criterion_evidence_sha256: frozenset[str] = frozenset()
    additional_reviewers: tuple[ReviewAuthority, ...] = ()
    expected_smoke_text: str | None = None


@dataclass(frozen=True)
class CriterionEvidence:
    """Progress already verified by the trusted synthetic host."""

    assignment: AssignmentRef
    session_id: str
    invocation_id: str
    criterion_sha256: str
    observation_sha256: str


@dataclass(frozen=True)
class CurrentState:
    assignment: AssignmentRef
    context: ContextAssembly
    instruction_revision: str
    recipient: str
    session_id: str
    invocation_id: str
    provider_allowed: bool = True
    tool_allowed: bool = True
    egress_allowed: bool = True
    cancelled: bool = False
    guard_proved: bool = True
    headroom_proved: bool = True
    capture_available: bool = True
    intent_available: bool = True
    observation_available: bool = True
    cancellation_acknowledged: bool = False
    retry_evidence: tuple[RetryProof, ...] = ()
    approved_evaluation_sha256: str | None = None
    verified_criterion_evidence: tuple[CriterionEvidence, ...] = ()
    presentation_evidence: tuple[HostPresentation, ...] = ()


@dataclass(frozen=True)
class Entry:
    execution_id: str
    session_id: str
    invocation_id: str
    operation: Operation
    attempt: str
    reservation: str
    admission: str
    call_id: str | None


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: bytes = field(repr=False)


@dataclass(frozen=True)
class ProviderReceipt:
    entry: Entry
    receipt_id: str
    revision: int
    kind: Literal["completed", "refused", "failed", "unknown", "no_submit", "safe_rejection"]
    usage_if_wire_unavailable: UsageObservation = UsageObservation()
    delay_ticks: int = 0
    wire_response: FakeResponse | None = field(default=None, repr=False)

    @property
    def evidence_sha256(self) -> str:
        return _digest(_encode({
            "entry": vars(self.entry), "receipt": self.receipt_id, "revision": self.revision,
            "kind": self.kind, "usage_if_wire_unavailable": vars(self.usage_if_wire_unavailable),
            "delay_ticks": self.delay_ticks,
            "wire_response": (
                (self.wire_response.request_id, self.wire_response.body) if self.wire_response is not None else None
            ),
        }))


@dataclass(frozen=True)
class ReceiptIdentity:
    receipt_id: str
    revision: int
    evidence_sha256: str
    kind: str

    @classmethod
    def from_receipt(cls, receipt: ProviderReceipt) -> ReceiptIdentity:
        return cls(receipt.receipt_id, receipt.revision, receipt.evidence_sha256, receipt.kind)


@dataclass(frozen=True)
class RetryProof:
    """Independent fixture evidence tied to the exact receipt and logical operation."""

    entry: Entry
    receipt_id: str
    revision: int
    kind: Literal["no_submit", "safe_rejection"]
    request_sha256: str
    observation_sha256: str
    evidence_ref: str


@dataclass(frozen=True)
class Assessment:
    """Exact-attempt projection from the trusted #205 evaluator reader."""

    entry: Entry
    receipt_id: str
    observation_sha256: str
    policy: EvaluationPolicy
    inputs: EvaluationInputs


@dataclass(frozen=True)
class ProviderInput:
    entry: Entry
    receipt: ProviderReceipt | None
    proof: RetryProof | None
    assessment: Assessment | None
    evidence_available: bool
    retry_evidence: tuple[RetryProof, ...]


@dataclass(frozen=True)
class HostPresentation:
    """Authoritative observation from the synthetic upper Runtime/#208 host."""

    execution_id: str
    invocation_id: str
    session_id: str
    status: Literal["completed", "not_presented"]
    observed_tick: int
    record_ref: str


@dataclass(frozen=True)
class TickBatch:
    tick: int
    providers: tuple[ProviderInput, ...] = ()
    tool_observed: bool = False
    timeout: bool = False
    cancel: bool = False
    cancel_ack: bool = False
    restrictions: tuple[str, ...] = ()
    tool_evidence_available: bool = True
    presentation: tuple[HostPresentation, ...] = ()


@dataclass(frozen=True)
class ProviderDecision:
    outcome: str
    proposal: ToolProposal | None = None
    evaluation: Evaluation | None = None
    evidence_reason: str | None = None
    exact_smoke_output: bytes | None = None

    @property
    def eligible(self) -> bool:
        return self.outcome in ("tool_proposal", "candidate")


@dataclass(frozen=True)
class LedgerEvidence:
    work: ScopeTotals
    parent: ScopeTotals
    grant: str | None
    reservation: str | None
    reservation_state: str | None
    reservation_units: int | None
    observation_ticks: tuple[int, ...]
    accounting_fact_sha256: str


@dataclass(frozen=True)
class AssignmentEvidence:
    flow_id: str
    run_id: str
    parent_run_id: str | None
    root_run_id: str
    work_item_id: str
    node_id: str
    route_id: str
    route_revision: int
    binding_sha256: str
    owner_generation: int
    execution_id: str


@dataclass(frozen=True)
class JournalEvent:
    tick: int
    stage: str
    reason: str
    entry: Entry | None = None
    evidence_ref: str | None = None
    signals: tuple[str, ...] = ()
    assignment: AssignmentEvidence | None = None
    session_id: str | None = None
    invocation_id: str | None = None
    instruction_revision: str | None = None
    previous_stage: str | None = None
    ledger_before: LedgerEvidence | None = None
    ledger_after: LedgerEvidence | None = None
    progress_before: int = 0
    progress_after: int = 0
    reported_usage: UsageObservation | None = None
    accounting_key: str | None = None
    decision_classification: str | None = None


@dataclass(frozen=True)
class ControllerStatus:
    execution_id: str
    invocation_id: str
    session_id: str
    disposition: str
    provider_entries: int
    tool_entries: int
    outstanding: tuple[Entry, ...]
    last_checkpoint: JournalEvent | None
    last_safe_checkpoint: JournalEvent | None
    owner: str
    cancellation_requested: bool
    cancellation_acknowledged: bool
    checkpoint_gaps: tuple[str, ...]
    committed_tick: int
    no_progress_ticks: int
    candidate: bytes | None = field(default=None, repr=False)
    recorded_candidate_sha256: str | None = None
    presentation: str = "not_applicable"
    presentation_owner: str | None = None
    last_consistent_ledger: LedgerEvidence | None = None


@dataclass(frozen=True)
class FakeProviderEntry:
    entry: Entry
    body: bytes = field(repr=False)


@dataclass(frozen=True)
class Unsent:
    action: Action
    reason: str
    signals: tuple[str, ...]


class OfflineJournal:
    """In-process stage-evidence writer. A write error has no external effects."""

    def __init__(self) -> None:
        self._events: list[JournalEvent] = []

    def append(self, event: JournalEvent) -> None:
        self._events.append(event)

    def committed(self, event: JournalEvent) -> bool:
        return event in self._events

    def fork_fixture(self) -> OfflineJournal:
        branch = OfflineJournal()
        branch._events = self._events.copy()
        return branch


class OfflineController:
    """Own the current assignment, admissions and journal in one in-process lock.

    The transport only records a synthetic entry. A trusted fixture host feeds back
    explicit observations. No adapter performs network, process or durable I/O.
    """

    def __init__(self, binding: ControllerBinding, *, journal: OfflineJournal | None = None) -> None:
        self._binding = binding
        self._lock = RLock()
        self._active = False
        self._tick = -1
        self._committed_tick = -1
        self._batch: TickBatch | None = None
        self._retired = False
        self._recomputing = False
        self._terminal: str | None = None
        self._terminal_signals: tuple[str, ...] = ()
        self._candidate: bytes | None = None
        self._candidate_tick: int | None = None
        self._cancel_tick: int | None = None
        self._deferred_cancel = False
        self._deferred_ack = False
        self._presentation = "not_applicable"
        self._host_presentation: set[HostPresentation] = set()
        self._deferred_presentation: set[HostPresentation] = set()
        self._journal: list[JournalEvent] = []
        self._writer = journal or OfflineJournal()
        self._writing_journal = False
        self._assignment_evidence = AssignmentEvidence(**binding.assignment.model_dump())
        self._owner = object()
        self._provider: list[FakeProviderEntry] = []
        self._tool_count = 0
        self._tool_result: ToolDecision | None = None
        self._tool_entry: Entry | None = None
        self._call: ToolCall | None = None
        self._call_response: str | None = None
        self._pending: dict[Entry, Action] = {}
        self._admitted: dict[Entry, Action] = {}
        self._receipt_ids: dict[str, Entry] = {}
        self._receipts: dict[Entry, ReceiptIdentity] = {}
        self._revisions: dict[tuple[Entry, int], ReceiptIdentity] = {}
        self._disputes: set[Entry] = set()
        self._normalized: dict[Entry, AdapterResult] = {}
        self._unsent: dict[Entry, Unsent] = {}
        self._late_evidence = False
        self._cancel_requested = False
        self._cancel_acknowledged = False
        self._cancel_saved = False
        self._cancel_ack_pending = False
        self._checkpoint_gaps: set[str] = set()
        self._unconfirmed_appends: dict[tuple[object, ...], JournalEvent] = {}
        self._accounting_checkpoints: dict[str, JournalEvent] = {}
        self._unpublished_accounting: set[str] = set()
        self._stalled = 0
        self._criterion_evidence = set(binding.initial_criterion_evidence_sha256)
        self._retry_at = 0
        self._next: Operation = "provider"
        self._ledger_authority = self._authority(0, None, True)
        self._budget = OfflineBudget(self._ledger_authority)

    @property
    def journal(self) -> tuple[JournalEvent, ...]:
        with self._lock:
            return tuple(self._journal)

    @property
    def provider_entries(self) -> tuple[FakeProviderEntry, ...]:
        with self._lock:
            return tuple(self._provider)

    def status(self, *, wait_ended: bool = False) -> ControllerStatus:
        with self._lock:
            if wait_ended and (self._writing_journal or self._retired):
                raise RuntimeError("Host wait expiry requires a current, idle journal owner")
            disposition = self._terminal or "pending"
            if wait_ended and disposition == "pending" and self._admitted:
                self._stop("hold_reconciliation", signals=("host_wait_expired",))
                disposition = self._terminal
            open_cancellation = self._batch is not None and self._batch.cancel
            cancelling = self._cancel_requested or self._deferred_cancel or open_cancellation
            if cancelling and disposition in ("candidate", "cancelled", "hold_reconciliation", "hold_journal"):
                disposition = ("cancelled_with_reconciliation_evidence"
                               if self._late_evidence and not self._checkpoint_gaps else "cancelled")
            elif disposition == "pending" and self._batch is not None:
                disposition = "hold_batch_incomplete"
            binding = self._binding
            unpublished = (
                self._accounting_checkpoints[key].entry for key in sorted(self._unpublished_accounting)
            )
            outstanding = tuple(dict.fromkeys((*self._pending,
                *(entry for entry in self._admitted if entry in self._disputes),
                *(entry for entry in unpublished if entry is not None))))
            applied_events = tuple(event for event in self._journal if event.stage != "gap"
                                   and event.accounting_key not in self._unpublished_accounting)
            checkpoint = next((event for event in reversed(self._journal)
                               if event.stage in (
                                   "prepared", "observation", "evaluation", "not_sent", "cancellation", "reconciliation",
                               )
                               and event.accounting_key not in self._unpublished_accounting
                               and event.reason not in ("submission_unresolved",)), None)
            latest = next((event for event in reversed(self._journal) if event.stage != "batch"), None)
            presentation = self._presentation
            if cancelling and self._candidate is not None and (
                self._deferred_cancel or open_cancellation or not self._cancel_saved
                or "presentation.decision" in self._checkpoint_gaps or presentation == "pending"
            ):
                presentation = "held"
            return ControllerStatus(
                binding.assignment.execution_id, binding.invocation_id, binding.session_id,
                disposition, len(self._provider), self._tool_count, outstanding, latest, checkpoint,
                "#207" if outstanding or any(not gap.startswith("presentation.") for gap in self._checkpoint_gaps)
                or disposition in (
                    "hold_reconciliation", "hold_batch_incomplete",
                ) else "#208" if presentation == "held" else "xrefkit-runtime",
                cancelling, self._cancel_acknowledged,
                tuple(sorted(self._checkpoint_gaps)), self._committed_tick, self._stalled,
                self._candidate if disposition == "candidate" and not cancelling else None,
                _digest(self._candidate) if self._candidate is not None else None, presentation,
                "#208" if presentation == "held" else None,
                applied_events[-1].ledger_after if applied_events else None,
            )

    def reconstruct(self, *, continuity_verified: bool) -> OfflineController:
        """Transfer the in-memory fixture state. Durable reconstruction belongs to #207."""
        with self._lock:
            if self._active or self._writing_journal or self._retired:
                raise RuntimeError("Reconstruction requires a current, idle owner")
            restored = copy(self)
            restored._lock = RLock()
            # Transfer ledger and journal-writer ownership. Freeze the retired owner's local view.
            restored._journal = self._journal.copy()
            restored._provider = self._provider.copy()
            restored._pending = self._pending.copy()
            restored._disputes = self._disputes.copy()
            restored._unpublished_accounting = self._unpublished_accounting.copy()
            restored._checkpoint_gaps = self._checkpoint_gaps.copy()
            self._retired = True
            if continuity_verified and self._committed_tick >= 0:
                checkpoint = next((event for event in reversed(self._journal)
                                   if event.stage == "batch" and event.reason == "tick_closed"
                                   and event.tick == self._committed_tick), None)
                try:
                    continuity_verified = checkpoint is not None and self._writer.committed(checkpoint)
                except Exception:
                    continuity_verified = False
            if not continuity_verified or self._batch is not None or self._tick != self._committed_tick:
                restored._checkpoint_gaps.add("batch.continuity")
                restored._terminal = "hold_reconciliation"
            restored._batch = None
            return restored

    def recomputation(self) -> OfflineController:
        """Reapply the real decision path to an independent in-memory pre-tick snapshot."""
        with self._lock:
            if self._active or self._writing_journal or self._retired:
                raise RuntimeError("Recomputation requires a current, idle owner")
            branch = copy(self)
            branch._lock = RLock()
            branch._recomputing = True
            branch._budget = self._budget.fork_fixture()
            branch._writer = self._writer.fork_fixture()
            for name in (
                "_journal", "_provider", "_pending", "_admitted", "_receipt_ids", "_receipts",
                "_revisions", "_disputes", "_normalized", "_unsent", "_checkpoint_gaps",
                "_unconfirmed_appends", "_accounting_checkpoints", "_unpublished_accounting",
                "_criterion_evidence", "_host_presentation", "_deferred_presentation",
            ):
                setattr(branch, name, getattr(self, name).copy())
            return branch

    def _record(
        self, stage: str, reason: str, entry: Entry | None = None, *,
        ref: str | None = None, signals: tuple[str, ...] = (),
        ledger_before: LedgerSnapshot | None = None, ledger_after: LedgerSnapshot | None = None,
        before_ledger_commit: bool = False,
        progress_after: int | None = None,
        reported_usage: UsageObservation | None = None,
        accounting_key: str | None = None,
        decision_classification: str | None = None,
    ) -> bool:
        if ledger_after is None:
            ledger_after = self._budget.snapshot(self._build_action(entry or self._entry("provider"), b""))
        before = self._ledger_evidence(ledger_before or ledger_after, entry)
        after = self._ledger_evidence(ledger_after, entry)
        binding = self._binding
        event = JournalEvent(
            self._tick, stage, reason, entry, ref, signals, self._assignment_evidence,
            binding.session_id, binding.invocation_id, binding.instruction_revision,
            self._journal[-1].stage if self._journal else None, before, after,
            self._stalled, self._stalled if progress_after is None else progress_after,
            reported_usage,
            accounting_key,
            decision_classification,
        )
        self._writing_journal = True
        try:
            saved = self._append_once(event, before_ledger_commit=before_ledger_commit)
        finally:
            self._writing_journal = False
        if saved is None:
            self._journal.append(replace(event, stage="gap", reason=f"{stage}_write_failed",
                                         ledger_after=before if before_ledger_commit else after,
                                         progress_after=self._stalled))
            return False
        if saved not in self._journal:
            self._journal.append(saved)
        return True

    def _append_once(self, event: JournalEvent, *, before_ledger_commit: bool) -> JournalEvent | None:
        replayable = {"cancellation", "observed", "observation", "not_sent", "reconciliation"}
        key = (("accounting", event.accounting_key) if event.accounting_key else
               (event.stage, event.reason, event.entry, event.evidence_ref,
                None if event.stage in replayable else event.tick))
        previous = self._unconfirmed_appends.get(key)
        if previous is None and event.accounting_key is not None:
            previous = self._accounting_checkpoints.get(event.accounting_key)
        if previous is not None:
            if previous.evidence_ref != event.evidence_ref or previous.reported_usage != event.reported_usage:
                return None
            try:
                committed = self._writer.committed(previous)
            except Exception:
                self._unconfirmed_appends[key] = previous
                self._checkpoint_gaps.add("journal.commit_unknown")
                return None
            if committed and before_ledger_commit and (
                previous.ledger_before.accounting_fact_sha256 != event.ledger_before.accounting_fact_sha256
                or previous.ledger_after.accounting_fact_sha256 != event.ledger_after.accounting_fact_sha256
            ):
                self._unconfirmed_appends[key] = previous
                self._checkpoint_gaps.add("journal.commit_unknown")
                return None
            if not committed and self._accounting_checkpoints.get(event.accounting_key) == previous:
                self._unconfirmed_appends[key] = previous
                self._checkpoint_gaps.add("journal.commit_unknown")
                return None
            self._unconfirmed_appends.pop(key, None)
            self._set_gap("journal.commit_unknown", bool(self._unconfirmed_appends))
            if committed:
                return previous
        try:
            self._writer.append(event)
        except Exception:
            try:
                return event if self._writer.committed(event) else None
            except Exception:
                self._unconfirmed_appends[key] = event
                self._checkpoint_gaps.add("journal.commit_unknown")
                return None
        return event

    @staticmethod
    def _ledger_evidence(snapshot: LedgerSnapshot, entry: Entry | None) -> LedgerEvidence:
        reservation = next((item for item in snapshot.reservations
                            if entry is not None and item.action.reservation_id == entry.reservation), None)
        facts = []
        for item in sorted(snapshot.reservations, key=lambda value: value.action.reservation_id):
            row = asdict(item)
            actions = [row["action"]]
            if row["adapter_link"] is not None:
                actions.append(row["adapter_link"]["action"])
            for action in actions:
                action["canonical_arguments"] = _digest(action["canonical_arguments"])
            facts.append(row)
        return LedgerEvidence(
            snapshot.work, snapshot.parent, reservation.action.authorization_ref if reservation else None,
            entry.reservation if entry else None, reservation.state if reservation else None,
            reservation.original_units if reservation else None,
            reservation.observation_ticks if reservation else (),
            _digest(_encode((snapshot.attempts_consumed, snapshot.fake_effects, facts))),
        )

    def _stop(self, reason: str, *, signals: tuple[str, ...] = ()) -> bool:
        self._terminal_signals = signals or (reason,)
        if not self._record("terminal", reason, signals=signals):
            self._checkpoint_gaps.add("terminal")
            self._terminal = "hold_reconciliation" if self._pending else "hold_journal"
            return False
        self._terminal = reason
        return True

    def _same_owner(self, state: CurrentState) -> bool:
        binding = self._binding
        return (state.assignment, state.session_id, state.invocation_id) == (
            binding.assignment, binding.session_id, binding.invocation_id,
        )

    def _same_invocation(self, state: CurrentState) -> bool:
        binding = self._binding
        return (state.assignment.execution_id, state.session_id, state.invocation_id) == (
            binding.assignment.execution_id, binding.session_id, binding.invocation_id,
        )

    def _input_restrictions(self, state: CurrentState) -> tuple[str, ...]:
        checks = (
            ("assignment", self._same_owner(state)),
            ("guard", state.guard_proved),
            ("provider", state.provider_allowed),
            ("tool", state.tool_allowed),
            ("egress", state.egress_allowed),
            ("recipient", state.recipient == self._binding.recipient),
            ("headroom", state.headroom_proved),
            ("intent", state.intent_available),
            ("capture", state.capture_available),
            ("observation", state.observation_available),
            ("context", self._context(state) is not None),
        )
        return tuple(name for name, allowed in checks if not allowed)

    def _latch_cancellation(self, state: CurrentState, *, correlated_fragment: bool = False) -> None:
        if not correlated_fragment and not self._same_invocation(state):
            return
        if state.cancelled and not self._cancel_requested:
            self._cancel_requested = True
            self._cancel_tick = self._tick
        if self._cancel_requested and not self._cancel_saved:
            self._cancel_saved = self._record("cancellation", "local_request")
            self._set_gap("cancellation.local_request", not self._cancel_saved)
        if state.cancellation_acknowledged and self._cancel_requested:
            self._cancel_ack_pending = True
        if self._cancel_saved and self._cancel_ack_pending and not self._cancel_acknowledged:
            self._cancel_acknowledged = self._record("cancellation", "acknowledged")
            self._set_gap("cancellation.acknowledged", not self._cancel_acknowledged)

    def _process_presentation(self, incoming: tuple[HostPresentation, ...]) -> None:
        """Resolve the delivery fact without reopening the recorded candidate or an effect."""
        binding = self._binding
        for item in incoming:
            if item in self._host_presentation:
                continue
            reference = _digest(_encode(asdict(item)))
            if (
                (item.execution_id, item.invocation_id, item.session_id) != (
                    binding.assignment.execution_id, binding.invocation_id, binding.session_id,
                )
                or not item.record_ref or item.status not in ("completed", "not_presented")
                or type(item.observed_tick) is not int
                or not self._candidate_tick <= item.observed_tick <= self._tick
            ):
                self._record("presentation", "host_presentation_evidence_unattributed", ref=reference)
                continue
            recorded = self._record("presentation", f"host_{item.status}", ref=reference)
            self._set_gap(f"presentation.evidence:{reference}", not recorded)
            if recorded:
                self._host_presentation.add(item)
        if self._cancel_tick is None:
            return
        completions = {item.observed_tick for item in self._host_presentation if item.status == "completed"}
        absences = {item.observed_tick for item in self._host_presentation if item.status == "not_presented"}
        incomplete = any(key.startswith("presentation.evidence:") for key in self._checkpoint_gaps)
        if (not incomplete and len(completions) == 1
                and next(iter(completions)) < self._cancel_tick
                and not any(tick >= next(iter(completions)) for tick in absences)):
            decision = "historical"
        elif not incomplete and not completions and any(tick >= self._cancel_tick for tick in absences):
            decision = "suppressed"
        else:
            decision = "held"
        if decision != self._presentation or "presentation.decision" in self._checkpoint_gaps:
            recorded = self._record("presentation", f"after_cancellation_{decision}")
            self._set_gap("presentation.decision", not recorded)
            if recorded:
                self._presentation = decision

    @staticmethod
    def _presentation_inputs(state: CurrentState) -> tuple[HostPresentation, ...]:
        return tuple(item for item in state.presentation_evidence if isinstance(item, HostPresentation)
                     and type(item.observed_tick) is int and all(isinstance(value, str) for value in (
                         item.execution_id, item.invocation_id, item.session_id, item.status, item.record_ref,
                     )))

    def _set_gap(self, key: str, present: bool) -> None:
        if present:
            self._checkpoint_gaps.add(key)
        else:
            self._checkpoint_gaps.discard(key)

    def _claim_assignment(self) -> bool:
        assignment = self._binding.assignment
        key = (assignment.run_id, assignment.work_item_id, assignment.route_id, assignment.owner_generation)
        with _OWNER_LOCK:
            return _OWNERS.setdefault(key, self._owner) is self._owner

    def _authority(self, tick: int, action: Action | None, headroom: bool) -> Authority:
        limits = self._binding.limits
        commands = frozenset({action.command}) if action else frozenset()
        return Authority(
            tick, self._binding.assignment.owner_generation, self._binding.instruction_revision,
            (Grant(action, limits.deadline_tick_exclusive),) if action else (),
            commands, commands, commands, commands, action.destination if action else "",
            Rate(action.rate_revision, action.model, 1, 0) if action else None,
            limits.synthetic_budget_units, limits.synthetic_budget_units, headroom_proved=headroom,
        )

    def _set_ledger_authority(self, authority: Authority) -> None:
        self._ledger_authority = authority
        self._budget.update_authority(authority)

    def _context(self, state: CurrentState) -> tuple[list[str], list[dict[str, object]]] | None:
        if state.instruction_revision != self._binding.instruction_revision or state.context != self._binding.context:
            return None
        try:
            return verified_context(self._binding.assignment, state.context)
        except (ValueError, RecursionError):
            return None

    def _signals(
        self, state: CurrentState, *, operation: Operation | None, unresolved: bool = False,
        reserved_action: Action | None = None,
        authority_operation: Operation | None = None, progress: int | None = None,
        fragment_restrictions: tuple[str, ...] = (), tool_receipt: bool = False,
    ) -> tuple[str, ...]:
        limits = self._binding.limits
        signals = []
        if self._cancel_requested:
            signals.append("cancelled")
        permitted = operation or authority_operation
        restrictions = set(self._input_restrictions(state)) | set(fragment_restrictions)
        relevant = {"assignment", "guard"}
        if permitted in ("provider", "continuation"):
            relevant.update(("provider", "recipient"))
        if permitted in ("tool", "continuation") or tool_receipt:
            relevant.update(("egress", "recipient"))
        if permitted == "tool" or tool_receipt:
            relevant.add("tool")
        if relevant & restrictions:
            signals.append("stop_authority")
        if unresolved or authority_operation is not None and "observation" in fragment_restrictions:
            signals.append("hold_reconciliation")
        if operation is not None and "intent" in restrictions:
            signals.append("hold_journal")
        if operation is not None and {"capture", "context"} & restrictions:
            signals.append("hold_context")
        if self._tick >= limits.deadline_tick_exclusive:
            signals.append("stop_deadline")
        if operation == "tool" and self._tool_count >= min(1, limits.max_tool_entries):
            signals.append("stop_attempt_limit")
        if operation in ("provider", "continuation") and len(self._provider) >= limits.max_provider_entries:
            signals.append("stop_attempt_limit")
        if "headroom" in restrictions:
            signals.append("hold_headroom")
        elif operation is not None:
            budget_action = reserved_action or self._build_action(self._entry(operation), b"")
            snapshot = self._budget.snapshot(budget_action)
            if snapshot.work.headroom is None or snapshot.parent.headroom is None:
                signals.append("hold_headroom")
            elif min(snapshot.work.headroom, snapshot.parent.headroom) < (
                0 if reserved_action is not None else limits.reservation_units_per_entry
            ):
                signals.append("stop_budget")
        if (self._stalled if progress is None else progress) >= limits.max_consecutive_no_progress_decision_ticks:
            signals.append("stop_no_progress")
        return tuple(signals)

    def step(
        self, tick: int, state: CurrentState, *, start: bool = False,
        observation: ProviderReceipt | None = None, retry_proof: RetryProof | None = None,
        assessment: Assessment | None = None, tool_observed: bool = False, timeout: bool = False,
        evaluate_only: bool = False, before_entry: Callable[[], CurrentState] | None = None,
        batch_closed: bool = True,
    ) -> ControllerStatus:
        """Supply one complete tick or collect receipt fragments until the same tick closes."""
        with self._lock:
            if self._active or self._writing_journal or self._retired or type(tick) is not int or tick < 0:
                raise ValueError("Expected a nonnegative synthetic tick from the current, idle owner")
            if tick <= self._tick:
                if self._same_invocation(state):
                    new_cancel = state.cancelled and not self._cancel_requested
                    new_ack = (state.cancellation_acknowledged and not self._cancel_acknowledged
                               and (state.cancelled or self._cancel_requested or self._deferred_cancel))
                    if new_cancel or new_ack:
                        self._deferred_cancel |= new_cancel
                        self._deferred_ack |= new_ack
                        self._deferred_presentation.update(self._presentation_inputs(state))
                        self._checkpoint_gaps.add("cancellation.awaiting_decision")
                return self.status()
            if self._batch is not None and self._batch.tick != tick:
                return self.status()
            batch = self._batch or TickBatch(tick)
            inputs = batch.providers
            if observation is not None:
                try:
                    captured = self._capture_provider(observation)
                except (ValueError, TypeError, RecursionError):
                    captured = None
                packet = ProviderInput(observation.entry, captured, retry_proof, assessment,
                                       state.capture_available and state.observation_available,
                                       state.retry_evidence)
                same = next((item for item in inputs
                             if replace(item, evidence_available=packet.evidence_available) == packet), None)
                if same is None:
                    inputs += (packet,)
                elif not packet.evidence_available:
                    inputs = tuple(replace(item, evidence_available=False) if item is same else item for item in inputs)
            correlated = self._same_invocation(state)
            presentation = set(batch.presentation) | self._deferred_presentation
            if correlated:
                presentation.update(self._presentation_inputs(state))
            batch = TickBatch(
                tick, tuple(sorted(inputs, key=lambda item: (
                    item.entry.attempt, item.receipt.evidence_sha256 if item.receipt is not None else "",
                ))), batch.tool_observed or tool_observed, batch.timeout or timeout,
                batch.cancel or self._deferred_cancel or correlated and state.cancelled,
                batch.cancel_ack or self._deferred_ack or correlated and state.cancellation_acknowledged,
                tuple(sorted(set(batch.restrictions) | set(self._input_restrictions(state)))),
                batch.tool_evidence_available and (
                    not tool_observed or state.capture_available and state.observation_available
                ),
                tuple(sorted(presentation, key=lambda item: (
                    item.observed_tick, item.execution_id, item.invocation_id, item.session_id,
                    item.status, item.record_ref,
                ))),
            )
            if not batch_closed:
                self._batch = batch
                return self.status()
            self._batch = None
            if self._terminal is not None and self._terminal_duplicate(batch):
                return self.status()
            self._deferred_cancel = False
            self._deferred_ack = False
            self._deferred_presentation.clear()
            self._checkpoint_gaps.discard("cancellation.awaiting_decision")
            self._active = True
            self._tick = tick
            try:
                if batch.cancel or batch.cancel_ack:
                    state = replace(state, cancelled=batch.cancel, cancellation_acknowledged=batch.cancel_ack)
                self._advance(state, batch, start, evaluate_only, before_entry)
                return self.status()
            finally:
                self._active = False

    def _terminal_duplicate(self, batch: TickBatch) -> bool:
        if (self._checkpoint_gaps or self._unsent or batch.timeout
                or batch.cancel and not self._cancel_requested
                or batch.cancel_ack and not self._cancel_acknowledged):
            return False
        if any(item not in self._host_presentation for item in batch.presentation):
            return False
        if batch.tool_observed and (self._tool_entry is None or self._tool_entry in self._pending):
            return False
        for packet in batch.providers:
            receipt = packet.receipt
            if receipt is None:
                return False
            previous = self._revisions.get((packet.entry, receipt.revision), self._receipts.get(packet.entry))
            if previous != ReceiptIdentity.from_receipt(receipt):
                return False
        return bool(batch.providers or batch.tool_observed)

    def _commit_tick(self, progress: int, signals: tuple[str, ...] = (), *, classification: str) -> bool:
        available = self._record("batch", "tick_closed", signals=signals, progress_after=progress,
                                 decision_classification=classification)
        self._set_gap("batch.close", not available)
        if available:
            self._committed_tick = self._tick
            self._stalled = progress
        else:
            self._checkpoint_gaps.add("batch.continuity")
            self._terminal = "hold_reconciliation"
        return available

    def _advance(
        self, state: CurrentState, batch: TickBatch, start: bool, evaluate_only: bool,
        before_entry: Callable[[], CurrentState] | None,
    ) -> None:
        self._set_ledger_authority(replace(self._ledger_authority, now_tick=self._tick,
                                           headroom_proved=state.headroom_proved))
        self._latch_cancellation(state, correlated_fragment=batch.cancel or batch.cancel_ack)
        late = self._terminal is not None
        if not self._record("batch", "tick_open", signals=batch.restrictions):
            self._checkpoint_gaps.add("batch.open")
            self._terminal = "hold_reconciliation"
            return
        packet = batch.providers[0] if len(batch.providers) == 1 else None
        provider_verdict = None
        if len(batch.providers) > 1:
            competing = sorted(
                (item.entry.attempt, item.receipt.evidence_sha256 if item.receipt is not None else "") for item in
                batch.providers
            )
            self._record("gap", "provider_observations_conflict_in_tick", ref=_digest(_encode(competing)))
            provider_verdict = "unresolved"
        elif packet is not None:
            if packet.receipt is None:
                self._record("gap", "invalid_provider_observation", packet.entry)
                provider_verdict = "unresolved"
            else:
                provider_verdict = self._observe_provider(
                    packet.receipt, packet.proof, evidence_available=packet.evidence_available,
                    retry_evidence=packet.retry_evidence, late=late,
                )
        tool_verdict = self._observe_tool(evidence_available=batch.tool_evidence_available,
                                          late=late) if batch.tool_observed else None
        timeout_pending = batch.timeout and bool(self._pending)
        if timeout_pending:
            self._record("gap", "transport_timeout_without_receipt", next(iter(self._pending)))
        unresolved = (timeout_pending or "unresolved" in (provider_verdict, tool_verdict)
                      or bool(self._checkpoint_gaps))
        if late:
            for entry, unsent in tuple(self._unsent.items()):
                if self._release_not_sent(entry, unsent):
                    self._record("reconciliation", "local_no_entry_checkpoint_recovered", entry)
            if not self._commit_tick(self._stalled, classification="terminal_reconciliation"):
                return
            if unresolved and self._terminal == "candidate":
                self._stop("hold_reconciliation", signals=("hold_reconciliation",))
            if self._candidate is not None:
                self._process_presentation(batch.presentation)
            if self._cancel_requested and self._terminal != "cancelled":
                signals = self._signals(
                    state, operation=None, unresolved=unresolved, authority_operation=self._next,
                    fragment_restrictions=batch.restrictions, tool_receipt=batch.tool_observed,
                )
                reasons = tuple(dict.fromkeys((*signals, *self._terminal_signals)))
                ordered = tuple(reason for reason in _STOP_PRIORITY if reason in reasons)
                self._stop("cancelled", signals=ordered + tuple(reason for reason in reasons if reason not in ordered))
            if "settled" in (provider_verdict, tool_verdict):
                self._late_evidence = True
            if (packet is not None and provider_verdict == "settled" and not unresolved
                    and self._terminal_signals == ("host_wait_expired",)
                    and not batch.restrictions and not self._input_restrictions(state)
                    and self._same_invocation(state) and not self._pending
                    and self._binding.expected_smoke_text is not None):
                decision = self._plan_provider(packet.receipt, None, state)
                if decision.exact_smoke_output is not None:
                    self._consume_provider(packet.receipt, None, decision)
            return
        # Settling an already admitted response never opens a fresh admission on its tick.
        receiving = bool(batch.providers) or batch.tool_observed or batch.timeout
        ready = start and not receiving and not self._pending and self._tick >= self._retry_at
        progress = self._stalled
        verdicts = tuple(verdict for verdict in (provider_verdict, tool_verdict) if verdict is not None)
        credited, progress_gap = self._record_progress(state)
        provider_decision = None
        if provider_verdict == "settled" and packet is not None:
            provider_decision = self._plan_provider(packet.receipt, packet.assessment, state)
        requested = self._next if not receiving and not self._pending and (ready or evaluate_only) else None
        blockers = self._signals(
            state, operation=requested, unresolved=unresolved or progress_gap, progress=0,
            authority_operation=self._next if receiving else None,
            fragment_restrictions=batch.restrictions, tool_receipt=batch.tool_observed,
        )
        ready_admission = ready and not evaluate_only and not blockers
        protocol_resolution = (provider_verdict in ("retry", "retry_limit") or tool_verdict == "settled"
                               or provider_decision is not None and provider_decision.eligible)
        transition = ready_admission or protocol_resolution
        active = start or evaluate_only or not receiving or "duplicate" in verdicts
        if credited:
            progress = 0
            classification = "verified_criterion_credit"
        elif active and not transition:
            progress += 1
            classification = "active_no_progress"
        elif protocol_resolution:
            classification = "protocol_resolution"
        elif ready_admission:
            classification = "eligible_admission"
        else:
            classification = "receipt_bookkeeping"
        signals = blockers
        if progress >= self._binding.limits.max_consecutive_no_progress_decision_ticks:
            signals += ("stop_no_progress",)
        if not self._commit_tick(progress, signals, classification=classification):
            return
        if signals:
            reasons = ((provider_decision.outcome,) if provider_decision is not None
                       and not provider_decision.eligible else ())
            self._stop(signals[0], signals=tuple(dict.fromkeys((*signals, *reasons))))
            return
        if provider_verdict == "retry_limit":
            self._stop("stop_retry_limit")
            return
        if provider_decision is not None:
            self._consume_provider(packet.receipt, packet.assessment, provider_decision)
            return
        if receiving:
            return
        if ready and not evaluate_only:
            self._enter(state, requested, before_entry)

    def _record_progress(self, state: CurrentState) -> tuple[bool, bool]:
        if not self._same_owner(state):
            return False, False
        binding = self._binding
        recorded = False
        unavailable = False
        for evidence in state.verified_criterion_evidence:
            reference = evidence.observation_sha256
            if (
                (evidence.assignment, evidence.session_id, evidence.invocation_id, evidence.criterion_sha256)
                != (binding.assignment, binding.session_id, binding.invocation_id, binding.criterion_sha256)
                or len(reference) != 64 or any(char not in "0123456789abcdef" for char in reference)
            ):
                continue
            if reference in self._criterion_evidence:
                if not self._record("evaluation", "unchanged_verified_criterion_evidence", ref=reference):
                    self._checkpoint_gaps.add(f"progress.criterion:{reference}")
                    unavailable = True
                continue
            if self._record("evaluation", "new_verified_criterion_evidence", ref=reference):
                self._criterion_evidence.add(reference)
                recorded = True
            else:
                self._checkpoint_gaps.add(f"progress.criterion:{reference}")
                unavailable = True
        return recorded, unavailable

    def _observe_provider(
        self, receipt: ProviderReceipt, proof: RetryProof | None, *,
        evidence_available: bool, retry_evidence: tuple[RetryProof, ...], late: bool,
    ) -> str:
        entry = receipt.entry
        action = self._admitted.get(entry)
        prior = self._receipts.get(entry)
        identity = ReceiptIdentity.from_receipt(receipt)
        receipt_ref = identity.evidence_sha256
        revision_key = (entry, receipt.revision)
        revised = self._revisions.get(revision_key)
        if prior == identity or revised == identity:
            self._record("reconciliation", "duplicate_receipt", entry)
            return "duplicate"
        if (action is None or entry.operation == "tool" or not receipt.receipt_id
                or type(receipt.revision) is not int or receipt.revision < 1
                or (prior is not None and (prior.revision >= receipt.revision
                    or prior.receipt_id != receipt.receipt_id))
                or self._receipt_ids.get(receipt.receipt_id, entry) != entry
                or revised is not None
                or any(old_entry == entry and old_revision > receipt.revision
                       for old_entry, old_revision in self._revisions)):
            self._record("reconciliation", "receipt_correlation_unproved", ref=receipt_ref)
            return "unresolved"
        if not evidence_available:
            self._record("gap", "required_provider_observation_unavailable", entry)
            if late:
                self._checkpoint_gaps.add(f"reconciliation.provider:{entry.admission}")
            return "unresolved"
        if prior is not None and entry not in self._pending:
            return self._reconcile_revision(action, receipt, identity, prior)
        try:
            normalized = self._normalize_provider(receipt, action)
        except (ValueError, TypeError, RecursionError):
            self._record("gap", "invalid_provider_observation", entry)
            return "unresolved"
        if not self._record("observed", receipt.kind, entry, ref=receipt_ref):
            if late:
                self._checkpoint_gaps.add(f"reconciliation.provider:{entry.admission}")
            return "unresolved"
        positive_no_effect = (
            receipt.kind in ("no_submit", "safe_rejection")
            and proof is not None and proof in retry_evidence and bool(proof.evidence_ref)
            and (proof.entry, proof.receipt_id, proof.revision, proof.kind) ==
                (entry, receipt.receipt_id, receipt.revision, receipt.kind)
            and proof.request_sha256 == _digest(action.canonical_arguments)
            and proof.observation_sha256 == receipt_ref
            and (receipt.kind == "no_submit" and receipt.wire_response is None
                or receipt.kind == "safe_rejection" and normalized is not None
                and normalized.disposition == "controller_retry_advice_only"
                and normalized.reason == "confirmed_transient_rejection")
        )
        submission = (
            "no_submit" if positive_no_effect else
            "confirmed" if receipt.kind in ("completed", "refused", "failed") else "unknown"
        )
        observed_usage = normalized.usage if normalized is not None else receipt.usage_if_wire_unavailable
        if normalized is None and receipt.kind in ("completed", "refused", "failed"):
            submission = "unknown"
        result = self._settle(
            action, receipt.receipt_id, receipt.revision, submission, observed_usage, entry=entry, ref=receipt_ref,
            late_reason="matched_late_receipt" if late else None,
        )
        if result.reason in ("settlement_checkpoint_unavailable", "settlement_publication_unavailable"):
            if late:
                self._checkpoint_gaps.add(f"reconciliation.provider:{entry.admission}")
            return "unresolved"
        self._receipts[entry] = identity
        self._receipt_ids[receipt.receipt_id] = entry
        if normalized is not None:
            self._normalized[entry] = normalized
        if result.disposition not in ("settled", "released"):
            return "unresolved"
        self._checkpoint_gaps.discard(f"reconciliation.provider:{entry.admission}")
        self._pending.pop(entry, None)
        if not positive_no_effect or self._terminal is not None:
            return "settled"
        limits = self._binding.limits
        count = sum(sent.entry.operation == entry.operation for sent in self._provider)
        if (count > limits.max_same_operation_provider_retries
                or type(receipt.delay_ticks) is not int
                or not 0 <= receipt.delay_ticks <= limits.max_delay_ticks
                or self._tick + receipt.delay_ticks >= limits.deadline_tick_exclusive):
            return "retry_limit"
        if not self._record("retry", "same_operation_no_effect_proved", entry, ref=_digest(proof.evidence_ref.encode())):
            return "unresolved"
        self._next = entry.operation
        self._retry_at = self._tick + receipt.delay_ticks
        return "retry"

    def _reconcile_revision(
        self, action: Action, receipt: ProviderReceipt, identity: ReceiptIdentity, prior: ReceiptIdentity,
    ) -> str:
        """Retain the original result and constrain admission on dispute. Never select an action here."""
        entry = receipt.entry
        gap = f"reconciliation.revision:{entry.admission}"
        try:
            normalized = self._normalize_provider(receipt, action)
        except (ValueError, TypeError, RecursionError):
            self._record("gap", "invalid_consumed_receipt_revision", entry, ref=identity.evidence_sha256)
            return "unresolved"
        usage = normalized.usage if normalized else receipt.usage_if_wire_unavailable
        ledger = self._ledger_evidence(self._budget.snapshot(action), entry)
        released = ledger.reservation_state == "released" and prior.kind in ("no_submit", "safe_rejection")
        explicit_usage = usage != UsageObservation()
        same_safe_rejection = (
            prior.kind == receipt.kind == "safe_rejection" and normalized is not None
            and normalized.disposition == "controller_retry_advice_only"
            and normalized.reason == "confirmed_transient_rejection"
        )
        same_no_submit = prior.kind == receipt.kind == "no_submit" and normalized is None
        contrary = released and (explicit_usage or not (same_no_submit or same_safe_rejection))
        if contrary:
            reason = ("consumed_no_submit_usage_reported" if explicit_usage
                      else "consumed_no_submit_usage_absent_disputed")
            result = self._settle(
                action, receipt.receipt_id, receipt.revision, "unknown", usage, entry=entry,
                ref=identity.evidence_sha256, revision_reason=reason,
            )
            saved = result.reason == "conflicting_observation"
            self._set_gap(gap, not saved)
            if saved:
                self._revisions[(entry, receipt.revision)] = identity
                self._disputes.add(entry)
            return "unresolved"
        reason = ("consumed_no_submit_usage_absent_release_preserved" if released
                  else "consumed_provider_receipt_revision")
        saved = self._record("reconciliation", reason, entry, ref=identity.evidence_sha256, reported_usage=usage)
        self._set_gap(gap, not saved)
        if saved:
            self._revisions[(entry, receipt.revision)] = identity
        return "reconciled" if released and saved and entry not in self._disputes else "unresolved"

    @staticmethod
    def _capture_provider(receipt: ProviderReceipt) -> ProviderReceipt:
        """Snapshot caller-owned wire containers before any observer or journal callback."""
        response = receipt.wire_response
        if response is None:
            return receipt
        if not isinstance(response.body, Mapping) or response.request_id is not None and not isinstance(
            response.request_id, str,
        ):
            raise ValueError("Invalid synthetic response envelope")
        return replace(receipt, wire_response=FakeResponse(
            response.request_id, json.loads(_encode(dict(response.body))),
        ))

    def _normalize_provider(self, receipt: ProviderReceipt, action: Action) -> AdapterResult | None:
        if receipt.wire_response is None:
            return None
        wire = receipt.wire_response
        if not isinstance(wire.body, Mapping) or wire.body.get("id") != receipt.receipt_id:
            raise ValueError("response identity mismatch")
        diagnostics = AttemptDiagnostics(
            action.run_id, action.work_item_id, self._binding.assignment.binding_sha256,
            action.attempt_id, action.reservation_id, _digest(action.canonical_arguments),
        )
        observed = normalize_controller_response(
            wire, diagnostics, model=self._binding.selected_model,
            tool_name=self._binding.tool_name, expected_response_id=receipt.receipt_id,
        )
        if observed.diagnostics.response_id != receipt.receipt_id:
            raise ValueError("response identity unavailable")
        return observed

    def _settle(
        self, action: Action, receipt_id: str, revision: int,
        submission: Literal["no_submit", "confirmed", "unknown"], usage: UsageObservation,
        *, entry: Entry | None = None, ref: str | None = None, unsent: Unsent | None = None,
        late_reason: str | None = None, revision_reason: str | None = None,
    ) -> Decision:
        observed = Observation(
            ReceiptRef(action.attempt_id, action.reservation_id, None, None, revision, receipt_id),
            submission, usage, action.rate_revision,
        )
        accounting_key = _digest(_encode((vars(entry), receipt_id, revision))) if entry is not None else None
        pinned = self._accounting_checkpoints.get(accounting_key)
        if pinned is None:
            pinned = self._unconfirmed_appends.get(("accounting", accounting_key))
        verified_checkpoint = False
        def checkpoint(decision: Decision, before: LedgerSnapshot, after: LedgerSnapshot) -> bool:
            nonlocal verified_checkpoint
            stage = "observation"
            reason = decision.reason
            if unsent:
                stage, reason = "not_sent", unsent.reason
            elif revision_reason:
                stage, reason = "reconciliation", revision_reason
            elif late_reason:
                stage = "reconciliation"
                reason = late_reason if decision.disposition in ("settled", "released") else f"late_{decision.reason}"
            saved = self._record(
                stage, reason, entry, ref=ref,
                signals=unsent.signals if unsent else (), ledger_before=before, ledger_after=after,
                before_ledger_commit=True, reported_usage=usage if not unsent else None,
                accounting_key=accounting_key,
            )
            if saved and accounting_key is not None:
                self._accounting_checkpoints[accounting_key] = next(
                    event for event in reversed(self._journal) if event.accounting_key == accounting_key
                    and event.stage != "gap"
                )
                self._unpublished_accounting.add(accounting_key)
                verified_checkpoint = True
            return saved

        result = self._budget.settle(
            action, observed, VerifiedReceipt(action, observed),
            before_commit=checkpoint if entry is not None else None,
            observation_tick=(pinned.ledger_after.observation_ticks[-1]
                              if pinned is not None and pinned.ledger_after.observation_ticks else None),
        )
        if result.reason == "settlement_publication_unavailable" or verified_checkpoint:
            self._set_gap(f"ledger.publication:{action.attempt_id}", result.reason == "settlement_publication_unavailable")
        if verified_checkpoint and result.reason != "settlement_publication_unavailable":
            self._unpublished_accounting.discard(accounting_key)
        return result

    def _plan_provider(
        self, receipt: ProviderReceipt, assessment: Assessment | None, current: CurrentState,
    ) -> ProviderDecision:
        api = self._normalized.get(receipt.entry)
        raw_output = receipt.wire_response.body.get("output") if receipt.wire_response else None
        raw_calls = (sum(isinstance(item, Mapping) and item.get("type") == "function_call"
                         for item in raw_output) if isinstance(raw_output, list) else 0)
        if receipt.kind != "completed" or api is None:
            return ProviderDecision("hold_outcome")
        if raw_calls > 1:
            return ProviderDecision("stop_tool_cardinality")
        if api.disposition != "completed":
            return ProviderDecision("hold_outcome")
        if api.diagnostics.observed_model != self._binding.selected_model:
            return ProviderDecision("hold_model")
        if raw_calls:
            if receipt.entry.operation != "provider" or self._call is not None:
                return ProviderDecision("hold_scope")
            criterion = controller_tool_criterion(
                api, expected_model=self._binding.selected_model,
                tool_name=self._binding.tool_name, document_id=self._binding.document_id,
            )
            if criterion.outcome != "pass":
                return ProviderDecision("hold_evaluation", evidence_reason=criterion.reason)
            proposal = api.items[0]
            if not isinstance(proposal, ToolProposal):
                return ProviderDecision("hold_scope")
            return ProviderDecision("tool_proposal", proposal=proposal, evidence_reason=criterion.reason)
        expected = self._binding.expected_smoke_text
        if expected is not None:
            if receipt.entry.operation != "continuation" or self._tool_count != 1:
                return ProviderDecision("hold_scope")
            if (len(api.items) == 1 and isinstance(api.items[0], TextItem)
                    and api.items[0].kind == "text" and api.items[0].text.strip() == expected):
                return ProviderDecision("candidate", exact_smoke_output=expected.encode())
            return ProviderDecision("hold_evaluation")
        evaluation = self._evaluate(receipt, assessment, current)
        eligible = (evaluation is not None and evaluation.aggregate == "criteria_met"
                    and evaluation.v1_assessment == "review_required" and evaluation.review_state == "reviewed"
                    and bool(evaluation.retained_reviewers))
        return ProviderDecision("candidate" if eligible else "hold_evaluation", evaluation=evaluation)

    def _consume_provider(
        self, receipt: ProviderReceipt, assessment: Assessment | None, decision: ProviderDecision,
    ) -> None:
        proposal, evaluation = decision.proposal, decision.evaluation
        if proposal is not None:
            if not self._record("evaluation", decision.evidence_reason, receipt.entry, ref=receipt.evidence_sha256):
                self._stop("hold_evaluation")
                return
            self._call = ToolCall(proposal.call_id, proposal.name, _encode({"document_id": proposal.query}))
            self._call_response = receipt.receipt_id
            self._next = "tool"
        elif decision.exact_smoke_output is not None:
            if not self._record("evaluation", "exact_smoke_output_matched", receipt.entry, ref=receipt.evidence_sha256):
                self._stop("hold_evaluation")
            elif self._stop("candidate"):
                self._candidate = decision.exact_smoke_output
                self._candidate_tick = self._tick
                self._presentation = "pending"
        elif evaluation is None:
            self._stop(decision.outcome)
        else:
            findings = tuple(criterion.reason for criterion in evaluation.criteria
                             if criterion.outcome in ("fail", "unresolved"))
            reasons = () if decision.eligible else (evaluation.next_proposal, *findings)
            saved = self._record("evaluation", "criteria_met" if decision.eligible else "criteria_unmet",
                                 receipt.entry, ref=evaluation_digest(evaluation), signals=reasons)
            if not saved or not decision.eligible:
                self._stop("hold_evaluation", signals=reasons)
                return
            if self._stop("candidate"):
                self._candidate = assessment.inputs.output_utf8
                self._candidate_tick = self._tick
                self._presentation = "pending"

    def _evaluate(
        self, receipt: ProviderReceipt, assessment: Assessment | None, current: CurrentState,
    ) -> Evaluation | None:
        if assessment is None or (
            assessment.entry, assessment.receipt_id, assessment.observation_sha256
        ) != (receipt.entry, receipt.receipt_id, receipt.evidence_sha256):
            return None
        policy, inputs = assessment.policy, assessment.inputs
        action = self._admitted[receipt.entry]
        continued = receipt.entry.operation == "continuation"
        tool = self._tool_entry
        if continued:
            if (self._tool_count != 1 or tool is None or tool in self._pending
                    or tool.call_id != receipt.entry.call_id):
                return None
        elif self._tool_count or tool is not None or self._call is not None:
            return None
        expected_call = receipt.entry.call_id or "no-tool-call"
        result = inputs.result
        if (
            current.approved_evaluation_sha256 != evaluation_policy_digest(policy)
            or policy.assignment != self._binding.assignment
            or policy.links.criteria_revision != self._binding.criterion_revision
            or policy.links.criteria_sha256 != self._binding.criterion_sha256
            or policy.expected_model != self._binding.selected_model
            or policy.reviewers != (self._binding.reviewer, *self._binding.additional_reviewers)
            or not policy.semantic_required
            or policy.controller_profile != ("continuation" if continued else "provider_only")
            or policy.api_request_sha256 != _digest(action.canonical_arguments)
            or inputs.request.authorization_ref != receipt.entry.admission
            or inputs.request.reservation_ref != receipt.entry.reservation
            or policy.provider_reservation_ref != receipt.entry.reservation
            or policy.links.correlation != (receipt.entry.attempt, receipt.entry.operation, expected_call)
            or not isinstance(result, ExecutionResult) or result.evidence_ref != receipt.evidence_sha256
            or inputs.api != self._normalized[receipt.entry]
            or (continued and (inputs.tool != self._tool_result or inputs.tool_return_utf8 !=
                               self._binding.synthetic_tool_result))
        ):
            return None
        return evaluate_io(policy, inputs)

    def _observe_tool(self, *, evidence_available: bool, late: bool) -> str:
        entries = [entry for entry in self._pending if entry.operation == "tool"]
        if not entries and self._tool_entry is not None:
            self._record("reconciliation", "duplicate_tool_receipt", self._tool_entry)
            return "duplicate"
        if len(entries) != 1 or not evidence_available:
            self._record("gap", "required_tool_observation_unavailable")
            if late and len(entries) == 1:
                self._checkpoint_gaps.add(f"reconciliation.tool:{entries[0].admission}")
            return "unresolved"
        entry = entries[0]
        result = self._tool_result
        if result is None or result.outcome != "executed" or result.receipt is None:
            self._record("gap", "tool_receipt_unresolved", entry)
            return "unresolved"
        action = self._pending[entry]
        tool_receipt_ref = f"tool:{entry.admission}:{result.receipt.result_digest}"
        if not self._record("observed", "tool_receipt", entry, ref=_digest(tool_receipt_ref.encode())):
            if late:
                self._checkpoint_gaps.add(f"reconciliation.tool:{entry.admission}")
            return "unresolved"
        budget = self._settle(
            action, tool_receipt_ref, 1, "confirmed", UsageObservation(action.input_bound, 0, action.input_bound),
            entry=entry, ref=_digest(tool_receipt_ref.encode()),
            late_reason="matched_late_tool_receipt" if late else None,
        )
        if budget.disposition != "settled":
            if late and budget.reason in ("settlement_checkpoint_unavailable", "settlement_publication_unavailable"):
                self._checkpoint_gaps.add(f"reconciliation.tool:{entry.admission}")
            return "unresolved"
        self._checkpoint_gaps.discard(f"reconciliation.tool:{entry.admission}")
        del self._pending[entry]
        self._next = "continuation"
        return "settled"

    def _release_not_sent(self, entry: Entry, unsent: Unsent) -> bool:
        """Consume local proof of no entry only after recording the ledger delta."""
        settled = self._settle(
            unsent.action, f"no-entry:{entry.admission}", 1, "no_submit", UsageObservation(),
            entry=entry, unsent=unsent,
        )
        self._set_gap(f"not_sent:{entry.admission}", settled.disposition != "released")
        if settled.disposition != "released":
            self._pending[entry] = unsent.action
            self._unsent[entry] = unsent
            return False
        self._pending.pop(entry, None)
        self._unsent.pop(entry, None)
        return True

    def _abort_before_entry(
        self, entry: Entry, action: Action, reason: str, terminal: str, signals: tuple[str, ...] = (),
    ) -> None:
        self._admitted.pop(entry, None)
        recorded = self._release_not_sent(entry, Unsent(action, reason, signals))
        self._stop(terminal if recorded else "hold_reconciliation", signals=signals)

    def _entry(self, operation: Operation) -> Entry:
        binding = self._binding
        attempt = f"{operation}-{len(self._admitted) + 1}"
        return Entry(binding.assignment.execution_id, binding.session_id, binding.invocation_id,
                     operation, attempt, f"reserve-{attempt}", f"admit-{attempt}",
                     self._call.call_id if self._call else None)

    def _body(self, state: CurrentState, operation: Operation) -> bytes:
        instructions, inputs = self._context(state)
        body = {
            "model": self._binding.selected_model, "instructions": "\n".join(instructions),
            "input": inputs, "parallel_tool_calls": False,
        }
        if operation == "continuation":
            body["previous_response_id"] = self._call_response
            body["input"] = [*inputs, {
                "type": "function_call_output", "call_id": self._call.call_id,
                "output": _encode({"status": "ok", "text": self._tool_result.value}).decode(),
            }]
        else:
            body["tools"] = [{
                "type": "function", "name": self._binding.tool_name, "parameters": {
                    "type": "object", "properties": {"document_id": {"type": "string"}},
                    "required": ["document_id"], "additionalProperties": False,
                },
            }]
        return _encode(body)

    def _build_action(self, entry: Entry, body: bytes) -> Action:
        binding = self._binding
        return Action(
            binding.assignment.run_id, binding.assignment.work_item_id, entry.attempt, entry.reservation,
            entry.admission, binding.assignment.owner_generation, binding.instruction_revision,
            "controller-synthetic-rate", binding.selected_model, entry.operation, body, "read_only",
            binding.recipient, binding.limits.deadline_tick_exclusive,
            binding.limits.reservation_units_per_entry, 0,
        )

    def _enter(
        self, state: CurrentState, operation: Operation, read_current: Callable[[], CurrentState] | None,
    ) -> None:
        entry = self._entry(operation)
        if self._recomputing:
            self._record("projection", "admission_would_be_requested", entry)
            return
        body = self._call.arguments if operation == "tool" else self._body(state, operation)
        action = self._build_action(entry, body)
        self._set_ledger_authority(self._authority(self._tick, action, state.headroom_proved))
        ledger_before = self._budget.snapshot(action)
        reserved = self._budget.reserve(action)
        if reserved.disposition != "reserved":
            self._stop("stop_budget" if reserved.disposition == "stop" else "hold_headroom")
            return
        if not self._record(
            "prepared", "intent_and_reservation_saved", entry, ref=_digest(body), ledger_before=ledger_before,
            ledger_after=self._budget.snapshot(action),
        ):
            self._abort_before_entry(entry, action, "intent_checkpoint_unavailable", "hold_journal")
            return
        try:
            current = read_current() if read_current else state
        except Exception:
            current = replace(state, guard_proved=False)
        self._latch_cancellation(current)
        signals = self._signals(current, operation=operation, reserved_action=action)
        if not signals:
            if self._terminal is not None:
                signals = (self._terminal,)
            elif not self._claim_assignment():
                signals = ("stop_authority",)
        if signals:
            self._abort_before_entry(entry, action, "entry_gate_denied", signals[0], signals)
            return
        self._admitted[entry] = action
        self._pending[entry] = action
        if operation == "tool":
            self._enter_tool(current, action, entry)
        else:
            self._provider.append(FakeProviderEntry(entry, body))
            if not self._record("entry", "synthetic_transport_entered", entry, ref=_digest(body)):
                self._stop("hold_reconciliation")

    def _enter_tool(self, state: CurrentState, action: Action, entry: Entry) -> None:
        binding = self._binding
        definition = ToolDefinition(binding.tool_name, 1, "e206-document-v1", "read",
                                    "e206-tool-registry", "e206-tool-knowledge", "offline-read", 128, 128)
        request = ToolRequest(
            action.run_id, action.work_item_id, binding.assignment.route_id, action.binding_revision,
            "tool", entry.attempt, entry.call_id, entry.admission, entry.reservation,
            action.policy_revision, binding.tool_name, 1, self._call.arguments,
            binding.document_id, binding.recipient, binding.recipient, action.deadline_tick,
        )
        tool_action = tool_budget_action(definition, request, rate_revision=action.rate_revision, units=action.input_bound)
        if isinstance(tool_action, ToolDecision):
            self._tool_result = tool_action
        else:
            context_pin = ToolContextPin(
                tool_action.work, request.route, request.generation, _digest(state.context.payload),
                state.context.provenance_sha256,
            )
            host = ToolHost(
                request.route, request.generation, "offline-e206-runner", "r2",
                definition.registry_revision, definition.knowledge_revision, frozenset({definition.capability}),
                frozenset({binding.document_id}), state.context, context_pin,
                ToolReturnScope(binding.recipient, state.context),
                self._authority(self._tick, tool_action, state.headroom_proved),
            )
            dispatcher = OfflineToolDispatch(definition, host, units=action.input_bound,
                                             fake_result=binding.synthetic_tool_result)
            prepared = dispatcher.prepare(request)
            if isinstance(prepared, ToolDecision):
                self._tool_result = prepared
            else:
                self._tool_result = dispatcher.reserve_tool(request) or dispatcher.invoke(prepared, request)
            self._tool_count = dispatcher.snapshot(request).entry_count
        if self._tool_count:
            self._tool_entry = entry
            if not self._record("entry", "synthetic_runner_entered", entry, ref=_digest(request.args)):
                self._stop("hold_reconciliation")
        else:
            self._abort_before_entry(entry, action, self._tool_result.reason, "hold_scope")

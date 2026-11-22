"""Single-work Controller for the #206 synthetic execution slice."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
from threading import Lock, RLock
from typing import Literal

from .contracts import AssignmentRef, ExecutionResult
from .offline_budget import (
    Action, Authority, Decision, Grant, Observation, OfflineBudget, Rate, ReceiptRef, VerifiedReceipt,
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
    AdapterResult, AttemptDiagnostics, FakeResponse, ToolProposal, UsageObservation,
    normalize_controller_response, verified_context,
)


Operation = Literal["provider", "tool", "continuation"]
_OWNER_LOCK = Lock()
_OWNERS: dict[tuple[str, str, str, int], object] = {}


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
class JournalEvent:
    tick: int
    stage: str
    reason: str
    entry: Entry | None = None
    evidence_ref: str | None = None
    signals: tuple[str, ...] = ()


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
    candidate: bytes | None = field(default=None, repr=False)


@dataclass(frozen=True)
class FakeProviderEntry:
    entry: Entry
    body: bytes = field(repr=False)


class OfflineJournal:
    """In-process stage-evidence writer. A write error has no external effects."""

    def __init__(self) -> None:
        self._events: list[JournalEvent] = []

    def append(self, event: JournalEvent) -> None:
        self._events.append(event)


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
        self._terminal: str | None = None
        self._candidate: bytes | None = None
        self._journal: list[JournalEvent] = []
        self._writer = journal or OfflineJournal()
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
        self._receipts: dict[Entry, ProviderReceipt] = {}
        self._normalized: dict[Entry, AdapterResult] = {}
        self._late_evidence = False
        self._cancel_requested = False
        self._cancel_acknowledged = False
        self._stalled = 0
        self._retry_at = 0
        self._next: Operation = "provider"
        self._budget = OfflineBudget(self._authority(0, None, True))

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
            disposition = self._terminal or "pending"
            if disposition == "cancelled" and self._late_evidence:
                disposition = "cancelled_with_reconciliation_evidence"
            elif wait_ended and disposition == "pending" and self._admitted:
                self._stop("hold_reconciliation", signals=("host_wait_expired",))
                disposition = "hold_reconciliation"
            binding = self._binding
            checkpoint = next((event for event in reversed(self._journal)
                               if event.stage in ("prepared", "observation", "evaluation")
                               and event.reason not in ("submission_unresolved",)), None)
            return ControllerStatus(
                binding.assignment.execution_id, binding.invocation_id, binding.session_id,
                disposition, len(self._provider), self._tool_count, tuple(self._pending),
                self._journal[-1] if self._journal else None, checkpoint,
                "#207" if self._pending or disposition == "hold_reconciliation" else "xrefkit-runtime",
                self._cancel_requested, self._cancel_acknowledged,
                self._candidate,
            )

    def _record(
        self, stage: str, reason: str, entry: Entry | None = None, *,
        ref: str | None = None, signals: tuple[str, ...] = (),
    ) -> bool:
        event = JournalEvent(self._tick, stage, reason, entry, ref, signals)
        try:
            self._writer.append(event)
        except Exception:
            self._journal.append(JournalEvent(self._tick, "gap", f"{stage}_write_failed", entry))
            return False
        self._journal.append(event)
        return True

    def _stop(self, reason: str, *, signals: tuple[str, ...] = ()) -> None:
        self._terminal = reason
        self._record("terminal", reason, signals=signals)

    def _same_owner(self, state: CurrentState) -> bool:
        binding = self._binding
        return (state.assignment, state.session_id, state.invocation_id) == (
            binding.assignment, binding.session_id, binding.invocation_id,
        )

    def _latch_cancellation(self, state: CurrentState) -> None:
        binding = self._binding
        if (state.assignment.execution_id, state.session_id, state.invocation_id) != (
            binding.assignment.execution_id, binding.session_id, binding.invocation_id,
        ):
            return
        if state.cancelled and not self._cancel_requested:
            self._cancel_requested = True
            self._record("cancellation", "local_request")
        if state.cancellation_acknowledged and self._cancel_requested and not self._cancel_acknowledged:
            self._cancel_acknowledged = True
            self._record("cancellation", "acknowledged")

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
    ) -> tuple[str, ...]:
        limits = self._binding.limits
        signals = []
        if self._cancel_requested:
            signals.append("cancelled")
        if (not self._same_owner(state) or not state.guard_proved
                or (operation == "tool" and not state.tool_allowed)
                or (operation in ("provider", "continuation") and not state.provider_allowed)
                or (operation in ("tool", "continuation")
                    and (not state.egress_allowed or state.recipient != self._binding.recipient))
                or (operation == "provider" and state.recipient != self._binding.recipient)):
            signals.append("stop_authority")
        if unresolved:
            signals.append("hold_reconciliation")
        if operation is not None and not state.intent_available:
            signals.append("hold_journal")
        if operation is not None and (not state.capture_available or self._context(state) is None):
            signals.append("hold_context")
        if self._tick >= limits.deadline_tick_exclusive:
            signals.append("stop_deadline")
        if operation == "tool" and self._tool_count >= min(1, limits.max_tool_entries):
            signals.append("stop_attempt_limit")
        if operation in ("provider", "continuation") and len(self._provider) >= limits.max_provider_entries:
            signals.append("stop_attempt_limit")
        if not state.headroom_proved:
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
        if self._stalled >= limits.max_consecutive_no_progress_decision_ticks:
            signals.append("stop_no_progress")
        return tuple(signals)

    def step(
        self, tick: int, state: CurrentState, *, start: bool = False,
        observation: ProviderReceipt | None = None, retry_proof: RetryProof | None = None,
        assessment: Assessment | None = None, tool_observed: bool = False, timeout: bool = False,
        evaluate_only: bool = False, before_entry: Callable[[], CurrentState] | None = None,
    ) -> ControllerStatus:
        """Advance one synthetic tick and optionally evaluate with admission deferred."""
        with self._lock:
            if self._active or type(tick) is not int or tick <= self._tick:
                raise ValueError("Expected a new synthetic tick outside an active decision")
            self._active = True
            self._tick = tick
            try:
                self._advance(state, start, observation, retry_proof, assessment, tool_observed,
                              timeout, evaluate_only, before_entry)
                return self.status()
            finally:
                self._active = False

    def _advance(
        self, state: CurrentState, start: bool, observation: ProviderReceipt | None,
        retry_proof: RetryProof | None, assessment: Assessment | None, tool_observed: bool,
        timeout: bool, evaluate_only: bool, before_entry: Callable[[], CurrentState] | None,
    ) -> None:
        self._latch_cancellation(state)
        late = self._terminal is not None
        verdict = self._observe_provider(state, observation, retry_proof) if observation else None
        if late:
            if self._cancel_requested and self._terminal == "hold_reconciliation":
                self._stop("cancelled", signals=self._signals(state, operation=None, unresolved=True))
            if verdict == "settled":
                self._late_evidence = True
                self._record("reconciliation", "matched_late_receipt", observation.entry)
            if tool_observed and self._observe_tool(state) == "settled":
                self._late_evidence = True
                self._record("reconciliation", "matched_late_tool_receipt", self._tool_entry)
            return
        ready = start and not self._pending and self._tick >= self._retry_at
        if evaluate_only or (ready and not observation and not tool_observed):
            self._stalled += 1
        if tool_observed:
            verdict = self._observe_tool(state)
        unresolved = (timeout and bool(self._pending)) or verdict == "unresolved"
        # Retain and prioritize every same-tick prohibiting signal before scheduling.
        requested = self._next if ready or evaluate_only else None
        signals = self._signals(state, operation=requested, unresolved=unresolved)
        if signals:
            self._stop(signals[0], signals=signals)
            return
        if verdict == "retry_limit":
            self._stop("stop_retry_limit")
            return
        if verdict == "settled" and observation:
            self._consume_provider(observation, assessment, state)
            return
        if verdict == "retry" or tool_observed or observation:
            return
        if ready and not evaluate_only:
            self._enter(state, requested, before_entry)

    def _observe_provider(
        self, state: CurrentState, receipt: ProviderReceipt, proof: RetryProof | None,
    ) -> str:
        entry = receipt.entry
        action = self._admitted.get(entry)
        prior = self._receipts.get(entry)
        if prior == receipt:
            self._record("reconciliation", "duplicate_receipt", entry)
            return "duplicate"
        if (action is None or entry.operation == "tool" or not receipt.receipt_id
                or type(receipt.revision) is not int or receipt.revision < 1
                or (prior is not None and (prior.revision >= receipt.revision
                    or prior.receipt_id != receipt.receipt_id))
                or self._receipt_ids.get(receipt.receipt_id, entry) != entry):
            self._record("reconciliation", "receipt_correlation_unproved", ref=_digest(receipt.receipt_id.encode()))
            return "unresolved"
        if not state.observation_available or not state.capture_available:
            self._record("gap", "required_provider_observation_unavailable", entry)
            return "unresolved"
        try:
            receipt_ref = receipt.evidence_sha256
            normalized = self._normalize_provider(receipt, action)
        except (ValueError, TypeError, RecursionError):
            self._record("gap", "invalid_provider_observation", entry)
            return "unresolved"
        if not self._record("observed", receipt.kind, entry, ref=receipt_ref):
            return "unresolved"
        positive_no_effect = (
            receipt.kind in ("no_submit", "safe_rejection")
            and proof is not None and proof in state.retry_evidence and bool(proof.evidence_ref)
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
        result = self._settle(action, receipt.receipt_id, receipt.revision, submission, observed_usage)
        self._receipts[entry] = receipt
        self._receipt_ids[receipt.receipt_id] = entry
        if normalized is not None:
            self._normalized[entry] = normalized
        saved_settlement = self._record("observation", result.reason, entry, ref=receipt_ref)
        if result.disposition not in ("settled", "released"):
            return "unresolved"
        self._pending.pop(entry, None)
        if not saved_settlement:
            return "unresolved"
        if not positive_no_effect or self._terminal is not None:
            return "settled"
        limits = self._binding.limits
        count = sum(sent.entry.operation == entry.operation for sent in self._provider)
        if (count > limits.max_same_operation_provider_retries
                or type(receipt.delay_ticks) is not int
                or not 0 <= receipt.delay_ticks <= limits.max_delay_ticks
                or self._tick + receipt.delay_ticks >= limits.deadline_tick_exclusive):
            return "retry_limit"
        self._next = entry.operation
        self._retry_at = self._tick + receipt.delay_ticks
        self._stalled = 0
        self._record("retry", "same_operation_no_effect_proved", entry, ref=_digest(proof.evidence_ref.encode()))
        return "retry"

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
    ) -> Decision:
        observed = Observation(
            ReceiptRef(action.attempt_id, action.reservation_id, None, None, revision, receipt_id),
            submission, usage, action.rate_revision,
        )
        return self._budget.settle(action, observed, VerifiedReceipt(action, observed))

    def _consume_provider(
        self, receipt: ProviderReceipt, assessment: Assessment | None, current: CurrentState,
    ) -> None:
        api = self._normalized.get(receipt.entry)
        raw_output = receipt.wire_response.body.get("output") if receipt.wire_response else None
        raw_calls = (sum(isinstance(item, Mapping) and item.get("type") == "function_call"
                         for item in raw_output) if isinstance(raw_output, list) else 0)
        if receipt.kind != "completed" or api is None:
            self._stop("hold_outcome")
        elif raw_calls > 1:
            self._stop("stop_tool_cardinality")
        elif api.disposition != "completed":
            self._stop("hold_outcome")
        elif api.diagnostics.observed_model != self._binding.selected_model:
            self._stop("hold_model")
        elif raw_calls:
            if receipt.entry.operation != "provider" or self._call is not None:
                self._stop("hold_scope")
                return
            criterion = controller_tool_criterion(
                api, expected_model=self._binding.selected_model,
                tool_name=self._binding.tool_name, document_id=self._binding.document_id,
            )
            if (criterion.outcome != "pass"
                    or not self._record("evaluation", criterion.reason, receipt.entry, ref=receipt.evidence_sha256)):
                self._stop("hold_evaluation")
                return
            proposal = api.items[0]
            if not isinstance(proposal, ToolProposal):
                self._stop("hold_scope")
                return
            self._call = ToolCall(proposal.call_id, proposal.name, _encode({"document_id": proposal.query}))
            self._call_response = receipt.receipt_id
            self._next = "tool"
            self._stalled = 0
        else:
            evaluation = self._evaluate(receipt, assessment, current)
            if evaluation is None or not self._record(
                "evaluation", "criteria_met", receipt.entry, ref=evaluation_digest(evaluation),
            ):
                self._stop("hold_evaluation")
                return
            self._candidate = assessment.inputs.output_utf8
            self._stop("candidate")

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
        expected_call = receipt.entry.call_id or "no-tool-call"
        result = inputs.result
        if (
            current.approved_evaluation_sha256 != evaluation_policy_digest(policy)
            or policy.assignment != self._binding.assignment
            or policy.links.criteria_revision != self._binding.criterion_revision
            or policy.links.criteria_sha256 != self._binding.criterion_sha256
            or policy.expected_model != self._binding.selected_model
            or policy.reviewers != (self._binding.reviewer,) or not policy.semantic_required
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
        evaluation = evaluate_io(policy, inputs)
        if (evaluation.aggregate != "criteria_met" or evaluation.v1_assessment != "review_required"
                or evaluation.review_state != "reviewed" or not evaluation.retained_reviewers):
            return None
        return evaluation

    def _observe_tool(self, state: CurrentState) -> str:
        entries = [entry for entry in self._pending if entry.operation == "tool"]
        if not entries and self._tool_entry is not None:
            self._record("reconciliation", "duplicate_tool_receipt", self._tool_entry)
            return "duplicate"
        if len(entries) != 1 or not state.observation_available or not state.capture_available:
            self._record("gap", "required_tool_observation_unavailable")
            return "unresolved"
        entry = entries[0]
        result = self._tool_result
        if result is None or result.outcome != "executed" or result.receipt is None:
            self._record("gap", "tool_receipt_unresolved", entry)
            return "unresolved"
        action = self._pending[entry]
        tool_receipt_ref = f"tool:{entry.admission}:{result.receipt.result_digest}"
        if not self._record("observed", "tool_receipt", entry, ref=_digest(tool_receipt_ref.encode())):
            return "unresolved"
        budget = self._settle(action, tool_receipt_ref, 1, "confirmed",
                              UsageObservation(action.input_bound, 0, action.input_bound))
        saved_settlement = self._record("observation", budget.reason, entry, ref=_digest(tool_receipt_ref.encode()))
        if budget.disposition != "settled":
            return "unresolved"
        del self._pending[entry]
        if not saved_settlement:
            return "unresolved"
        self._next = "continuation"
        self._stalled = 0
        return "settled"

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
        body = self._call.arguments if operation == "tool" else self._body(state, operation)
        action = self._build_action(entry, body)
        self._budget.update_authority(self._authority(self._tick, action, state.headroom_proved))
        reserved = self._budget.reserve(action)
        if reserved.disposition != "reserved":
            self._stop("stop_budget" if reserved.disposition == "stop" else "hold_headroom")
            return
        if not self._record("prepared", "intent_and_reservation_saved", entry, ref=_digest(body)):
            self._settle(action, f"no-entry:{entry.admission}", 1, "no_submit", UsageObservation())
            self._stop("hold_journal")
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
            self._settle(action, f"no-entry:{entry.admission}", 1, "no_submit", UsageObservation())
            self._record("not_sent", "entry_gate_denied", entry, signals=signals)
            self._stop(signals[0], signals=signals)
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
            del self._pending[entry]
            self._settle(action, f"no-entry:{entry.admission}", 1, "no_submit", UsageObservation())
            self._record("not_sent", self._tool_result.reason, entry)
            self._stop("hold_scope")

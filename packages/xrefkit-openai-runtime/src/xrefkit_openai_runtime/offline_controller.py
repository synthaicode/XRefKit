"""Single-work Controller for the #206 synthetic execution slice."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
from threading import RLock
from typing import Literal

from .contracts import AssignmentRef
from .offline_budget import (
    Action, Authority, Decision, Grant, Observation, OfflineBudget, Rate, ReceiptRef, VerifiedReceipt,
)
from .offline_context import ContextAssembly
from .offline_dispatch import (
    OfflineToolDispatch, ToolContextPin, ToolDecision, ToolDefinition, ToolHost, ToolRequest,
    ToolReturnScope, tool_budget_action,
)
from .offline_evaluation import Evaluation, evaluation_digest
from .offline_responses import UsageObservation, verified_context


Operation = Literal["provider", "tool", "continuation"]


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
    limits: ControllerLimits
    context: ContextAssembly
    synthetic_tool_result: bytes = field(repr=False)


@dataclass(frozen=True)
class CurrentState:
    assignment: AssignmentRef
    context: ContextAssembly
    instruction_revision: str
    recipient: str
    provider_allowed: bool = True
    tool_allowed: bool = True
    egress_allowed: bool = True
    cancelled: bool = False
    guard_proved: bool = True
    headroom_proved: bool = True
    capture_available: bool = True
    intent_available: bool = True
    observation_available: bool = True


@dataclass(frozen=True)
class Entry:
    execution_id: str
    session_id: str
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
    observed_model: str | None = None
    usage: UsageObservation = UsageObservation()
    calls: tuple[ToolCall, ...] = ()
    output: bytes = field(default=b"", repr=False)
    delay_ticks: int = 0

    @property
    def evidence_sha256(self) -> str:
        return _digest(_encode({
            "entry": vars(self.entry), "receipt": self.receipt_id, "revision": self.revision,
            "kind": self.kind, "model": self.observed_model, "usage": vars(self.usage),
            "calls": [(call.call_id, call.name, _digest(call.arguments)) for call in self.calls],
            "output_sha256": _digest(self.output), "delay_ticks": self.delay_ticks,
        }))


@dataclass(frozen=True)
class RetryProof:
    """Independent fixture evidence tied to the exact receipt and logical operation."""

    entry: Entry
    receipt_id: str
    revision: int
    kind: Literal["no_submit", "safe_rejection"]


@dataclass(frozen=True)
class Assessment:
    """Exact-attempt projection from the trusted #205 evaluator reader."""

    entry: Entry
    receipt_id: str
    observation_sha256: str
    evaluation: Evaluation


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
    candidate: bytes | None = field(default=None, repr=False)


@dataclass(frozen=True)
class FakeProviderEntry:
    entry: Entry
    body: bytes = field(repr=False)


class OfflineController:
    """Own the current assignment, admissions and journal in one in-process lock.

    The transport only records a synthetic entry. A trusted fixture host feeds back
    explicit observations. No adapter performs network, process or durable I/O.
    """

    def __init__(self, binding: ControllerBinding) -> None:
        self._binding = binding
        self._lock = RLock()
        self._active = False
        self._tick = -1
        self._terminal: str | None = None
        self._candidate: bytes | None = None
        self._journal: list[JournalEvent] = []
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
        self._late_evidence = False
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
            elif wait_ended and disposition == "pending" and self._pending:
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
                self._candidate,
            )

    def _record(
        self, stage: str, reason: str, entry: Entry | None = None, *,
        ref: str | None = None, signals: tuple[str, ...] = (),
    ) -> None:
        self._journal.append(JournalEvent(self._tick, stage, reason, entry, ref, signals))

    def _stop(self, reason: str, *, signals: tuple[str, ...] = ()) -> None:
        self._terminal = reason
        self._record("terminal", reason, signals=signals)

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
    ) -> tuple[str, ...]:
        limits = self._binding.limits
        signals = []
        if state.cancelled:
            signals.append("cancelled")
        if (state.assignment != self._binding.assignment or not state.guard_proved
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
        if self._stalled >= limits.max_consecutive_no_progress_decision_ticks:
            signals.append("stop_no_progress")
        return tuple(signals)

    def step(
        self, tick: int, state: CurrentState, *, start: bool = False,
        observation: ProviderReceipt | None = None, retry_proof: RetryProof | None = None,
        assessment: Assessment | None = None, tool_observed: bool = False, timeout: bool = False,
        no_progress: bool = False, before_entry: Callable[[], CurrentState] | None = None,
    ) -> ControllerStatus:
        """Advance one synthetic clock tick. Recheck the trusted snapshot at entry."""
        with self._lock:
            if self._active or type(tick) is not int or tick <= self._tick:
                raise ValueError("Expected a new synthetic tick outside an active decision")
            self._active = True
            self._tick = tick
            try:
                self._advance(state, start, observation, retry_proof, assessment, tool_observed,
                              timeout, no_progress, before_entry)
                return self.status()
            finally:
                self._active = False

    def _advance(
        self, state: CurrentState, start: bool, observation: ProviderReceipt | None,
        retry_proof: RetryProof | None, assessment: Assessment | None, tool_observed: bool,
        timeout: bool, no_progress: bool, before_entry: Callable[[], CurrentState] | None,
    ) -> None:
        late = self._terminal is not None
        if late and self._terminal not in ("cancelled", "hold_reconciliation"):
            return
        verdict = self._observe_provider(state, observation, retry_proof) if observation else None
        if late:
            if state.cancelled and self._terminal == "hold_reconciliation":
                self._stop("cancelled", signals=self._signals(state, operation=None, unresolved=True))
            if verdict == "settled":
                self._late_evidence = True
                self._record("reconciliation", "matched_late_receipt", observation.entry)
            if tool_observed and self._observe_tool(state) == "settled":
                self._late_evidence = True
                self._record("reconciliation", "matched_late_tool_receipt", self._tool_entry)
            return
        if no_progress:
            self._stalled += 1
        if tool_observed:
            verdict = self._observe_tool(state)
        unresolved = (timeout and bool(self._pending)) or verdict == "unresolved"
        # Retain and prioritize every same-tick prohibiting signal before scheduling.
        requested = self._next if start and not self._pending else None
        signals = self._signals(state, operation=requested, unresolved=unresolved)
        if signals:
            self._stop(signals[0], signals=signals)
            return
        if verdict == "retry_limit":
            self._stop("stop_retry_limit")
            return
        if verdict == "settled" and observation:
            self._consume_provider(observation, assessment)
            return
        if verdict == "retry" or tool_observed or observation:
            return
        if requested is not None and self._tick >= self._retry_at:
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
        positive_no_effect = (
            receipt.kind in ("no_submit", "safe_rejection")
            and proof == RetryProof(entry, receipt.receipt_id, receipt.revision, receipt.kind)
        )
        submission = (
            "no_submit" if positive_no_effect else
            "confirmed" if receipt.kind in ("completed", "refused", "failed") else "unknown"
        )
        result = self._settle(action, receipt.receipt_id, receipt.revision, submission, receipt.usage)
        self._receipts[entry] = receipt
        self._receipt_ids[receipt.receipt_id] = entry
        self._record("observation", result.reason, entry, ref=receipt.evidence_sha256)
        if result.disposition not in ("settled", "released"):
            return "unresolved"
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
        self._next = entry.operation
        self._retry_at = self._tick + receipt.delay_ticks
        self._record("retry", "same_operation_no_effect_proved", entry)
        return "retry"

    def _settle(
        self, action: Action, receipt_id: str, revision: int,
        submission: Literal["no_submit", "confirmed", "unknown"], usage: UsageObservation,
    ) -> Decision:
        observed = Observation(
            ReceiptRef(action.attempt_id, action.reservation_id, None, None, revision, receipt_id),
            submission, usage, action.rate_revision,
        )
        return self._budget.settle(action, observed, VerifiedReceipt(action, observed))

    def _consume_provider(self, receipt: ProviderReceipt, assessment: Assessment | None) -> None:
        if receipt.kind != "completed":
            self._stop("hold_outcome")
        elif receipt.observed_model != self._binding.selected_model:
            self._stop("hold_model")
        elif len(receipt.calls) > 1:
            self._stop("stop_tool_cardinality")
        elif receipt.calls:
            call = receipt.calls[0]
            if (receipt.entry.operation != "provider" or self._call is not None or not call.call_id
                    or call.name != self._binding.tool_name
                    or call.arguments != _encode({"document_id": self._binding.document_id})):
                self._stop("hold_scope")
                return
            self._call = call
            self._call_response = receipt.receipt_id
            self._next = "tool"
            self._stalled = 0
        elif not self._eligible(receipt, assessment):
            self._stop("hold_evaluation")
        else:
            self._candidate = receipt.output
            self._record("evaluation", "criteria_met", receipt.entry, ref=evaluation_digest(assessment.evaluation))
            self._stop("candidate")

    def _eligible(self, receipt: ProviderReceipt, assessment: Assessment | None) -> bool:
        if assessment is None or (
            assessment.entry, assessment.receipt_id, assessment.observation_sha256
        ) != (receipt.entry, receipt.receipt_id, receipt.evidence_sha256):
            return False
        evaluation = assessment.evaluation
        return (
            evaluation.criteria_revision == self._binding.criterion_revision
            and evaluation.criteria_sha256 == self._binding.criterion_sha256
            and evaluation.output_sha256 == _digest(receipt.output)
            and evaluation.aggregate == "criteria_met"
            and evaluation.api_outcome == "completed"
            and evaluation.usage == receipt.usage
            and evaluation.tool_effect == ("observed" if receipt.entry.operation == "continuation" else "none")
            and evaluation.v1_assessment == "review_required"
            and evaluation.review_state == "reviewed"
            and bool(evaluation.retained_reviewers)
        )

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
        budget = self._settle(action, tool_receipt_ref, 1, "confirmed",
                              UsageObservation(action.input_bound, 0, action.input_bound))
        self._record("observation", budget.reason, entry, ref=_digest(tool_receipt_ref.encode()))
        if budget.disposition != "settled":
            return "unresolved"
        del self._pending[entry]
        self._next = "continuation"
        self._stalled = 0
        return "settled"

    def _entry(self, operation: Operation) -> Entry:
        binding = self._binding
        attempt = f"{operation}-{len(self._admitted) + 1}"
        return Entry(binding.assignment.execution_id, binding.session_id, operation, attempt,
                     f"reserve-{attempt}", f"admit-{attempt}", self._call.call_id if self._call else None)

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

    def _enter(
        self, state: CurrentState, operation: Operation, read_current: Callable[[], CurrentState] | None,
    ) -> None:
        entry = self._entry(operation)
        binding = self._binding
        body = self._call.arguments if operation == "tool" else self._body(state, operation)
        action = Action(
            binding.assignment.run_id, binding.assignment.work_item_id, entry.attempt, entry.reservation,
            entry.admission, binding.assignment.owner_generation, binding.instruction_revision,
            "controller-synthetic-rate", binding.selected_model, operation, body, "read_only",
            binding.recipient, binding.limits.deadline_tick_exclusive,
            binding.limits.reservation_units_per_entry, 0,
        )
        self._budget.update_authority(self._authority(self._tick, action, state.headroom_proved))
        reserved = self._budget.reserve(action)
        if reserved.disposition != "reserved":
            self._stop("stop_budget" if reserved.disposition == "stop" else "hold_headroom")
            return
        self._record("prepared", "intent_and_reservation_saved", entry, ref=_digest(body))
        try:
            current = read_current() if read_current else state
        except Exception:
            current = replace(state, guard_proved=False)
        signals = self._signals(current, operation=operation)
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
            self._record("entry", "synthetic_transport_entered", entry, ref=_digest(body))

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
            self._record("entry", "synthetic_runner_entered", entry, ref=_digest(request.args))
        else:
            del self._pending[entry]
            self._settle(action, f"no-entry:{entry.admission}", 1, "no_submit", UsageObservation())
            self._record("not_sent", self._tool_result.reason, entry)
            self._stop("hold_scope")

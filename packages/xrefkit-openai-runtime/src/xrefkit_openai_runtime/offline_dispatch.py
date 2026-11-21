"""Process-local, synthetic Tool Dispatch for #204."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from hashlib import sha256
import json
import re
from threading import Lock
from typing import Literal

from .offline_budget import Action, Authority, OfflineBudget
from .offline_context import ContextAssembly


@dataclass(frozen=True)
class ToolDefinition:
    tool_id: str
    version: int
    schema: str
    operation: Literal["read"]
    registry_revision: str
    knowledge_revision: str
    capability: str
    argument_bytes: int
    result_bytes: int


@dataclass(frozen=True)
class ToolContextPin:
    """Host-confirmed fixture link from accepted #201 context to the Tool scope."""

    work: tuple[str, str]
    route: str
    generation: int
    payload_sha256: str
    provenance_sha256: str


@dataclass(frozen=True)
class ToolReturnScope:
    """Trusted binding of a #201 assembly decision to its checked recipient."""

    recipient: str
    context: ContextAssembly

    @property
    def pin(self) -> tuple[str, str, str] | None:
        if not self.recipient or self.context.payload is None or self.context.hold_reason is not None:
            return None
        return self.recipient, _digest(self.context.payload), self.context.provenance_sha256


@dataclass(frozen=True)
class ToolHost:
    """Trusted, immutable scope supplied by XRefKit, separate from Tool proposals."""

    route: str
    generation: int
    runner_id: str
    runner_revision: str
    registry_evidence: str | None
    knowledge_revision: str | None
    capabilities: frozenset[str] | None
    permitted_targets: frozenset[str]
    context: ContextAssembly
    context_pin: ToolContextPin
    return_scope: ToolReturnScope
    authority: Authority
    intent_available: bool = True
    listing_approved: bool = True


@dataclass(frozen=True)
class ToolRequest:
    run: str
    work: str
    route: str
    generation: int
    operation_id: str
    attempt: str
    provider_call: str
    grant: str
    reservation: str | None
    policy: str
    tool_id: str
    version: int
    args: bytes
    target: str
    destination: str
    recipient: str
    deadline: int

    @property
    def operation_key(self) -> tuple[str, str, str]:
        return self.run, self.work, self.operation_id


@dataclass(frozen=True)
class PreparedTool:
    request: ToolRequest
    action_digest: str
    runner_id: str
    runner_revision: str
    registry_revision: str
    context_pin: ToolContextPin
    return_pin: tuple[str, str, str] | None


@dataclass(frozen=True)
class ToolCorrelation:
    run_digest: str
    work_digest: str
    route_digest: str
    operation_digest: str
    attempt_digest: str
    call_digest: str
    policy_digest: str
    grant_digest: str
    reservation_digest: str


@dataclass(frozen=True)
class ToolReceipt:
    action_digest: str
    tool_schema: str
    runner_digest: str
    binding_generation: int
    entry_tick: int
    correlation: ToolCorrelation
    outcome: str
    effect: Literal["observed", "unknown"]
    result_digest: str | None


@dataclass(frozen=True)
class ToolAttemptEvidence:
    correlation: ToolCorrelation
    action_digest: str | None
    proposal_digest: str
    arguments_digest: str
    target_digest: str
    destination_digest: str
    effect: Literal["none", "observed", "unknown"]
    workflow_acceptance: Literal["not_evaluated"] = "not_evaluated"


@dataclass(frozen=True)
class ToolDecision:
    outcome: Literal["executed", "deny", "hold", "stop", "in_progress", "replay"]
    reason: str
    receipt: ToolReceipt | None = None
    value: str | None = field(default=None, repr=False)
    evidence: ToolAttemptEvidence | None = None


@dataclass(frozen=True)
class _Intent:
    digest: str
    receipt: ToolReceipt
    context_pin: ToolContextPin
    return_pin: tuple[str, str, str] | None
    value: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class ToolReservationEvidence:
    reservation_digest: str
    action_digest: str
    state: str
    consumed: bool
    units: int


@dataclass(frozen=True)
class ToolSnapshot:
    entry_count: int
    admissions_consumed: int
    reserved_units: int
    headroom: int | None
    parent_headroom: int | None
    reservations: tuple[ToolReservationEvidence, ...]
    intents: tuple[ToolReceipt, ...]


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()


def _digest(value: bytes) -> str:
    return sha256(value).hexdigest()


class _AmbiguousArgument(ValueError):
    pass


def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise _AmbiguousArgument(name)
        result[name] = value
    return result


def _action_bytes(definition: ToolDefinition, request: ToolRequest) -> bytes | ToolDecision:
    if len(request.args) > definition.argument_bytes:
        return ToolDecision("deny", "argument_bytes_exceeded")
    try:
        raw = json.loads(request.args.decode("utf-8"), object_pairs_hook=_unique_fields)
    except _AmbiguousArgument:
        return ToolDecision("deny", "argument_ambiguous")
    except (ValueError, RecursionError):
        return ToolDecision("deny", "argument_schema_invalid")
    if (
        not isinstance(raw, dict) or set(raw) != {"key"} or type(raw["key"]) is not str
        or re.fullmatch(r"[A-Za-z0-9_]{1,16}", raw["key"]) is None
    ):
        return ToolDecision("deny", "argument_schema_invalid")
    return _json_bytes({
        "tool": request.tool_id, "version": request.version, "operation": definition.operation,
        "args": raw, "target": request.target, "destination": request.destination,
    })


def tool_budget_action(
    definition: ToolDefinition, request: ToolRequest, *, rate_revision: str, units: int,
) -> Action | ToolDecision:
    """Bind a Tool-only grant/reservation to an exact validated request."""
    canonical = _action_bytes(definition, request)
    if isinstance(canonical, ToolDecision):
        return canonical
    if request.reservation is None:
        return ToolDecision("hold", "reservation_missing")
    return Action(
        request.run, request.work, request.attempt, request.reservation, request.grant,
        request.generation, request.policy, rate_revision, "fixture-tool-ledger", request.tool_id,
        _json_bytes({
            "route": request.route, "logical_operation": request.operation_id,
            "recipient": request.recipient, "action_sha256": _digest(canonical),
        }),
        "read_only", request.destination, request.deadline, units, 0,
    )


class _FakeRunner:
    """An in-process entry counter with fixed fixture data and no Tool adapter."""

    def __init__(self, result: bytes) -> None:
        self.result = result
        self.entry_count = 0

    def _enter(self) -> bytes:
        self.entry_count += 1
        return self.result


class OfflineToolDispatch:
    """Own host updates, Tool admission, the logical claim and actual fake entry under one lock."""

    def __init__(self, definition: ToolDefinition, host: ToolHost, *, units: int, fake_result: bytes) -> None:
        self._definition = definition
        self._host = host
        self._units = units
        self._lock = Lock()
        self._runner = _FakeRunner(fake_result)
        self._budget = OfflineBudget(host.authority)
        self._intents: dict[tuple[str, str, str], _Intent] = {}

    def update_host(self, host: ToolHost) -> None:
        with self._lock:
            self._host = host
            self._budget.update_authority(host.authority)

    def _definition_check(self, tool_id: str, version: int) -> ToolDecision | None:
        definition = self._definition
        host = self._host
        if tool_id != definition.tool_id or version != definition.version or type(version) is not int:
            return ToolDecision("deny", "unregistered_tool")
        if host.registry_evidence != definition.registry_revision or tool_id not in host.authority.registry:
            return ToolDecision("hold", "registry_unverified")
        if host.knowledge_revision != definition.knowledge_revision:
            return ToolDecision("hold", "required_knowledge_unverified")
        if host.capabilities is None:
            return ToolDecision("hold", "runner_capability_unverified")
        if definition.capability not in host.capabilities or tool_id not in host.authority.available_commands:
            return ToolDecision("deny", "runner_capability_absent")
        if tool_id not in host.authority.user_commands or tool_id not in host.authority.policy_commands:
            return ToolDecision("deny", "command_not_allowed")
        return None

    def discover(self) -> tuple[ToolDefinition, ...]:
        with self._lock:
            definition, host = self._definition, self._host
            if (
                self._definition_check(definition.tool_id, definition.version) is not None
                or not host.listing_approved or not host.permitted_targets
                or not host.authority.confirmed_destination or host.return_scope.pin is None
                or host.authority.cancelled or not self._context_current()
            ):
                return ()
            return (definition,)

    def prepare(self, request: ToolRequest) -> PreparedTool | ToolDecision:
        with self._lock:
            canonical = _action_bytes(self._definition, request)
            failed = self._definition_check(request.tool_id, request.version)
            if failed is not None:
                return self._record_attempt(request, canonical, failed)
            if isinstance(canonical, ToolDecision):
                return self._record_attempt(request, canonical, canonical)
            host = self._host
            if request.target not in host.permitted_targets:
                return self._record_attempt(request, canonical, ToolDecision("deny", "target_outside_scope"))
            return PreparedTool(request, _digest(canonical), host.runner_id, host.runner_revision,
                                self._definition.registry_revision, host.context_pin, host.return_scope.pin)

    def reserve_tool(self, request: ToolRequest) -> ToolDecision | None:
        """Trusted host preparation on the private Tool ledger."""
        with self._lock:
            action = self._budget_action(request)
            if isinstance(action, ToolDecision):
                return action
            decision = self._budget.reserve(action)
            if decision.disposition == "reserved":
                return None
            return self._budget_failure(decision.disposition, decision.reason)

    def _budget_action(self, request: ToolRequest) -> Action | ToolDecision:
        rate = self._host.authority.rate
        return tool_budget_action(self._definition, request,
                                  rate_revision=rate.revision if rate else "", units=self._units)

    @staticmethod
    def _budget_failure(disposition: str, reason: str) -> ToolDecision:
        if disposition == "stop":
            return ToolDecision("stop", "budget_exhausted" if reason == "cap_exhausted" else reason)
        if disposition == "deny":
            return ToolDecision("deny", "reservation_consumed" if reason == "permit_consumed" else reason)
        reasons = {
            "reservation_not_matched": "reservation_mismatch",
            "grant_or_binding_no_longer_current": "grant_revoked",
        }
        return ToolDecision("hold", reasons.get(reason, reason))

    def invoke(
        self, prepared: PreparedTool, request: ToolRequest, *,
        reject_before_entry: bool = False, interruption: Literal["receipt_lost", "paused"] | None = None,
    ) -> ToolDecision:
        with self._lock:
            canonical = _action_bytes(self._definition, request)
            if isinstance(canonical, ToolDecision):
                return self._record_attempt(request, canonical, canonical)
            before = self._runner.entry_count
            decision = self._invoke_locked(prepared, request, _digest(canonical), reject_before_entry, interruption)
            return self._record_attempt(request, canonical, decision, entered=self._runner.entry_count != before)

    def _invoke_locked(
        self, prepared: PreparedTool, request: ToolRequest, digest: str, reject_before_entry: bool,
        interruption: Literal["receipt_lost", "paused"] | None,
    ) -> ToolDecision:
        if prepared.action_digest != digest:
            return ToolDecision("hold", "action_changed")
        if prepared.request != request:
            if request.reservation is None and replace(prepared.request, reservation=None) == request:
                return ToolDecision("hold", "reservation_missing")
            return ToolDecision("hold", "action_changed")
        old = self._intents.get(request.operation_key)
        if old is not None:
            return self._read_receipt(request, digest, old)
        failed = self._check_current(prepared)
        if failed is not None:
            return failed
        if not self._host.intent_available:
            return ToolDecision("hold", "intent_unavailable")
        if reject_before_entry:
            return ToolDecision("deny", "proved_no_entry")
        action = self._budget_action(request)
        if isinstance(action, ToolDecision):
            return action
        pending = self._receipt(request, digest, "pending", "unknown", None)
        admission = self._budget.dispatch_fake(action)
        if admission.disposition != "executed":
            if admission.reason == "reservation_not_matched":
                entries = self._budget.snapshot(action).reservations
                if not any(entry.action.reservation_id == action.reservation_id for entry in entries):
                    return ToolDecision("hold", "reservation_missing")
            return self._budget_failure(admission.disposition, admission.reason)

        # The host lock also protects the intent before a replay or replacement.
        intent = _Intent(digest, pending, self._host.context_pin, self._host.return_scope.pin)
        self._intents[request.operation_key] = intent
        output = self._runner._enter()
        if interruption is not None:
            reason = "admitted_worker_effect_unresolved" if interruption == "paused" else "effect_unknown"
            receipt = self._receipt(request, digest, reason, "unknown", None)
            self._intents[request.operation_key] = replace(intent, receipt=receipt)
            return ToolDecision("hold", reason, receipt)
        value, reason = self._validate_result(output)
        receipt = self._receipt(request, digest, "completed" if value is not None else reason,
                                "observed", _digest(output))
        self._intents[request.operation_key] = replace(intent, receipt=receipt, value=value)
        if value is None:
            return ToolDecision("hold", reason, receipt)
        if not self._may_read(request):
            return ToolDecision("hold", "receipt_reuse_not_authorized")
        return ToolDecision("executed", "bounded_typed_result", receipt, value)

    def _check_current(self, prepared: PreparedTool) -> ToolDecision | None:
        request, host = prepared.request, self._host
        authority = host.authority
        if (
            request.route != host.route or request.generation != host.generation
            or request.generation != authority.binding_revision
        ):
            return ToolDecision("hold", "binding_changed")
        if (
            prepared.runner_id != host.runner_id or prepared.runner_revision != host.runner_revision
            or prepared.registry_revision != host.registry_evidence
        ):
            return ToolDecision("hold", "registry_or_runner_changed")
        failed = self._definition_check(request.tool_id, request.version)
        if failed is not None:
            return failed
        if prepared.context_pin != host.context_pin or not self._context_matches(request):
            return ToolDecision("hold", "context_held")
        if request.target not in host.permitted_targets:
            return ToolDecision("deny", "target_outside_scope")
        if request.destination != authority.confirmed_destination:
            return ToolDecision("hold", "destination_unconfirmed")
        if request.recipient != host.return_scope.recipient:
            return ToolDecision("hold", "recipient_unconfirmed")
        if prepared.return_pin is None or prepared.return_pin != host.return_scope.pin:
            return ToolDecision("hold", "recipient_egress_unapproved")
        return None

    def _context_matches(self, request: ToolRequest) -> bool:
        pin = self._host.context_pin
        return self._context_current() and pin.work == (request.run, request.work)

    def _context_current(self) -> bool:
        host = self._host
        pin = host.context_pin
        context = host.context
        return (
            context.payload is not None and context.hold_reason is None
            and pin.route == host.route and pin.generation == host.generation == host.authority.binding_revision
            and pin.payload_sha256 == _digest(context.payload)
            and pin.provenance_sha256 == context.provenance_sha256
        )

    def _may_read(self, request: ToolRequest) -> bool:
        host = self._host
        authority = host.authority
        action = self._budget_action(request)
        matches = () if isinstance(action, ToolDecision) else tuple(
            grant for grant in authority.grants if grant.action.authorization_ref == request.grant
        )
        return (
            host.return_scope.pin is not None and self._context_matches(request)
            and request.route == host.route and request.generation == host.generation == authority.binding_revision
            and request.policy == authority.policy_revision and request.recipient == host.return_scope.recipient
            and request.target in host.permitted_targets and request.destination == authority.confirmed_destination
            and not authority.cancelled and authority.now_tick < request.deadline
            and len(matches) == 1 and matches[0].action == action and matches[0].status == "allowed"
            and authority.now_tick < matches[0].expires_tick
            and self._definition_check(request.tool_id, request.version) is None
        )

    def _read_receipt(self, request: ToolRequest, digest: str, intent: _Intent) -> ToolDecision:
        if digest != intent.digest:
            return ToolDecision("deny", "operation_digest_conflict")
        if intent.receipt.outcome == "pending":
            return ToolDecision("in_progress", "operation_active")
        can_read = (
            intent.context_pin == self._host.context_pin and intent.return_pin == self._host.return_scope.pin
            and self._may_read(request)
        )
        if intent.receipt.effect == "unknown":
            detail = intent.receipt if can_read else None
            return ToolDecision("hold", intent.receipt.outcome, detail)
        if not can_read:
            return ToolDecision("hold", "receipt_reuse_not_authorized")
        if intent.value is None:
            return ToolDecision("hold", intent.receipt.outcome, intent.receipt)
        return ToolDecision("replay", "receipt_reuse_authorized", intent.receipt, intent.value)

    def _validate_result(self, output: bytes) -> tuple[str | None, str]:
        if len(output) > self._definition.result_bytes:
            return None, "oversize_result"
        try:
            raw = json.loads(output.decode("utf-8"), object_pairs_hook=_unique_fields)
            if isinstance(raw, dict) and set(raw) == {"value"} and type(raw["value"]) is str:
                if 0 < len(raw["value"].encode("utf-8")) <= 64:
                    return raw["value"], "bounded_typed_result"
        except (ValueError, RecursionError):
            pass
        return None, "invalid_result"

    @staticmethod
    def _correlation(request: ToolRequest) -> ToolCorrelation:
        correlation = (request.run, request.work, request.route, request.operation_id, request.attempt,
                       request.provider_call, request.policy, request.grant, request.reservation or "")
        return ToolCorrelation(*(_digest(_json_bytes(value)) for value in correlation))

    def _record_attempt(
        self, request: ToolRequest, canonical: bytes | ToolDecision, decision: ToolDecision,
        *, entered: bool = False,
    ) -> ToolDecision:
        effect: Literal["none", "observed", "unknown"] = "observed" if entered else "none"
        if decision.receipt is not None:
            effect = decision.receipt.effect
        elif decision.reason in {"operation_active", "effect_unknown", "admitted_worker_effect_unresolved"}:
            effect = "unknown"
        arguments_digest = _digest(request.args)
        target_digest = _digest(_json_bytes(request.target))
        destination_digest = _digest(_json_bytes(request.destination))
        proposal_digest = _digest(_json_bytes((
            request.tool_id, request.version, arguments_digest, target_digest, destination_digest,
        )))
        evidence = ToolAttemptEvidence(
            self._correlation(request), _digest(canonical) if isinstance(canonical, bytes) else None,
            proposal_digest, arguments_digest, target_digest, destination_digest, effect,
        )
        return replace(decision, evidence=evidence)

    def _receipt(
        self, request: ToolRequest, digest: str, outcome: str,
        effect: Literal["observed", "unknown"], result_digest: str | None,
    ) -> ToolReceipt:
        return ToolReceipt(digest, self._definition.schema, _digest(_json_bytes(self._host.runner_id)),
                           request.generation, self._host.authority.now_tick,
                           self._correlation(request),
                           outcome, effect, result_digest)

    def snapshot(self, request: ToolRequest) -> ToolSnapshot:
        with self._lock:
            action = self._budget_action(request)
            if isinstance(action, ToolDecision):
                raise ValueError("a valid action is needed to scope the Tool ledger")
            snapshot = self._budget.snapshot(action)
            reservations = tuple(
                ToolReservationEvidence(_digest(_json_bytes(entry.action.reservation_id)),
                                        _digest(entry.action.canonical_arguments), entry.state,
                                        entry.fake_effect_consumed, entry.original_units)
                for entry in snapshot.reservations
            )
            return ToolSnapshot(self._runner.entry_count, snapshot.fake_effects, snapshot.work.reserved,
                                snapshot.work.headroom, snapshot.parent.headroom, reservations,
                                tuple(intent.receipt for intent in self._intents.values()))

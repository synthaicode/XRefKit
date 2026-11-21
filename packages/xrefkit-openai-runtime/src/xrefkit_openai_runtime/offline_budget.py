"""Synthetic, process-local authorization and budget accounting for #203."""

from __future__ import annotations

from dataclasses import dataclass, replace
from threading import Lock
from typing import Literal

from .offline_responses import AdapterResult, AttemptDiagnostics, UsageObservation


@dataclass(frozen=True)
class Action:
    run_id: str
    work_item_id: str
    attempt_id: str
    reservation_id: str
    authorization_ref: str
    binding_revision: int
    policy_revision: str
    rate_revision: str | None
    model: str
    command: str
    canonical_arguments: bytes
    effect_class: str
    destination: str
    deadline_tick: int
    input_bound: int
    output_bound: int

    @property
    def work(self) -> tuple[str, str]:
        return self.run_id, self.work_item_id

    @property
    def attempt(self) -> tuple[str, str, str]:
        return (*self.work, self.attempt_id)


@dataclass(frozen=True)
class Grant:
    action: Action
    expires_tick: int
    status: Literal["allowed", "denied", "revoked"] = "allowed"


@dataclass(frozen=True)
class Rate:
    revision: str
    model: str
    input_units: int
    output_units: int


@dataclass(frozen=True)
class AdapterScope:
    run_id: str | None
    work_item_id: str | None
    binding_sha256: str | None
    attempt_id: str | None
    reservation_ref: str | None

    @classmethod
    def from_diagnostics(cls, diagnostics: AttemptDiagnostics) -> AdapterScope:
        return cls(diagnostics.run_id, diagnostics.work_item_id, diagnostics.binding_sha256,
                   diagnostics.attempt_id, diagnostics.reservation_ref)


@dataclass(frozen=True)
class AdapterLink:
    """A trusted, pre-observation link from one #202 admission to one local action."""

    action: Action
    scope: AdapterScope
    fallback_id: str


@dataclass(frozen=True)
class Authority:
    now_tick: int
    binding_revision: int
    policy_revision: str
    grants: tuple[Grant, ...]
    registry: frozenset[str]
    available_commands: frozenset[str]
    policy_commands: frozenset[str]
    user_commands: frozenset[str]
    confirmed_destination: str
    rate: Rate | None
    work_cap: int | None
    parent_cap: int | None
    cancelled: bool = False
    ledger_available: bool = True
    headroom_proved: bool = True
    adapter_links: tuple[AdapterLink, ...] = ()


@dataclass(frozen=True)
class ReceiptRef:
    attempt_id: str | None
    reservation_id: str | None
    request_id: str | None
    response_id: str | None
    revision: int
    fallback_id: str | None = None

    def identity_keys(self) -> tuple[tuple[str, str], ...]:
        return tuple((kind, value) for kind, value in (
            ("transport_request", self.request_id), ("response", self.response_id),
            ("verified_fallback", self.fallback_id),
        ) if value)


@dataclass(frozen=True)
class Observation:
    receipt: ReceiptRef
    submission: Literal["confirmed", "no_submit", "possible", "unknown"]
    usage: UsageObservation = UsageObservation()
    rate_revision: str | None = None


@dataclass(frozen=True)
class VerifiedReceipt:
    """The synthetic host's independent correlation of an exact observation."""

    action: Action
    observation: Observation


@dataclass(frozen=True)
class Decision:
    disposition: Literal["reserved", "executed", "deny", "hold", "stop", "settled", "released", "duplicate"]
    reason: str
    units: int | None = None


@dataclass(frozen=True)
class Reservation:
    action: Action
    rate: Rate
    original_units: int
    reserved_tick: int
    adapter_link: AdapterLink | None = None
    fake_effect_consumed: bool = False
    state: Literal["reserved", "settled", "released"] = "reserved"
    observations: tuple[Observation, ...] = ()
    observation_ticks: tuple[int, ...] = ()
    synthetic_debit: int | None = None
    actual_bill: None = None
    exposure_uncertain: bool = False


@dataclass(frozen=True)
class ScopeTotals:
    cap: int | None
    reserved: int
    debit: int
    headroom: int | None


@dataclass(frozen=True)
class LedgerSnapshot:
    work: ScopeTotals
    parent: ScopeTotals
    reservations: tuple[Reservation, ...]
    attempts_consumed: int
    fake_effects: int


def _quantity(value: object) -> bool:
    return type(value) is int and value >= 0


class OfflineBudget:
    """One shared lock covers host updates, reservation, and the fake effect itself."""

    def __init__(self, authority: Authority) -> None:
        self._authority = authority
        self._lock = Lock()
        self._entries: dict[str, Reservation] = {}
        self._attempts: set[tuple[str, str, str]] = set()
        self._receipt_owners: dict[tuple[str, str], str] = {}
        self._fake_effects = 0

    def update_authority(self, authority: Authority) -> None:
        with self._lock:
            self._authority = authority

    def _check_action(self, action: Action) -> Decision | None:
        authority = self._authority
        if authority.cancelled or authority.now_tick >= action.deadline_tick:
            return Decision("stop", "cancelled" if authority.cancelled else "deadline_elapsed")
        if (
            action.command not in authority.registry
            or action.command not in authority.available_commands
            or action.command not in authority.policy_commands
            or action.command not in authority.user_commands
            or action.effect_class != "read_only"
        ):
            return Decision("deny", "action_not_allowed")
        grants = tuple(grant for grant in authority.grants
                       if grant.action.authorization_ref == action.authorization_ref)
        if not grants or all(grant.status == "denied" for grant in grants):
            return Decision("deny", "grant_missing_or_denied")
        if len(grants) != 1:
            return Decision("hold", "grant_ambiguous")
        grant = grants[0]
        if (
            grant.action != action
            or grant.status != "allowed"
            or authority.now_tick >= grant.expires_tick
            or authority.binding_revision != action.binding_revision
            or authority.policy_revision != action.policy_revision
        ):
            return Decision("hold", "grant_or_binding_no_longer_current")
        if authority.confirmed_destination != action.destination:
            return Decision("hold", "destination_unconfirmed")
        return None

    def _totals(self, entries: tuple[Reservation, ...], cap: int | None) -> ScopeTotals:
        reserved = sum(entry.original_units for entry in entries if entry.state == "reserved")
        debit = sum(entry.synthetic_debit for entry in entries if entry.synthetic_debit is not None)
        known = (self._authority.ledger_available and self._authority.headroom_proved
                 and _quantity(cap) and not any(entry.exposure_uncertain for entry in entries))
        return ScopeTotals(cap, reserved, debit, cap - reserved - debit if known else None)

    def _scopes(self, action: Action) -> tuple[ScopeTotals, ScopeTotals]:
        entries = tuple(self._entries.values())
        work_entries = tuple(entry for entry in entries if entry.action.work == action.work)
        return (self._totals(work_entries, self._authority.work_cap),
                self._totals(entries, self._authority.parent_cap))

    def snapshot(self, action: Action) -> LedgerSnapshot:
        with self._lock:
            work, parent = self._scopes(action)
            return LedgerSnapshot(work, parent, tuple(self._entries.values()),
                                  len(self._attempts), self._fake_effects)

    def reserve(self, action: Action) -> Decision:
        with self._lock:
            obstruction = self._check_action(action)
            if obstruction:
                return obstruction
            if action.reservation_id in self._entries or action.attempt in self._attempts:
                return Decision("deny", "reservation_or_attempt_reused")
            rate = self._authority.rate
            if (rate is None or rate.revision != action.rate_revision or rate.model != action.model
                    or not all(_quantity(value) for value in (
                        rate.input_units, rate.output_units, action.input_bound, action.output_bound))):
                return Decision("hold", "rate_or_bounds_unproved")
            units = action.input_bound * rate.input_units + action.output_bound * rate.output_units
            work, parent = self._scopes(action)
            if work.headroom is None or parent.headroom is None:
                return Decision("hold", "headroom_unproved")
            if units > min(work.headroom, parent.headroom):
                return Decision("stop", "cap_exhausted")
            links = tuple(link for link in self._authority.adapter_links if link.action == action)
            if len(links) > 1 or any(not link.fallback_id or not all((
                link.scope.run_id, link.scope.work_item_id, link.scope.binding_sha256,
                link.scope.attempt_id, link.scope.reservation_ref,
            )) for link in links):
                return Decision("hold", "adapter_link_unproved")
            self._entries[action.reservation_id] = Reservation(
                action, rate, units, self._authority.now_tick, links[0] if links else None,
            )
            self._attempts.add(action.attempt)
            return Decision("reserved", "reservation_created", units)

    def dispatch_fake(self, action: Action) -> Decision:
        with self._lock:
            obstruction = self._check_action(action)
            if obstruction:
                return obstruction
            entry = self._entries.get(action.reservation_id)
            if entry is None or entry.action != action:
                return Decision("hold", "reservation_not_matched")
            if entry.fake_effect_consumed or entry.state != "reserved" or entry.observations:
                return Decision("deny", "permit_consumed")
            if self._authority.rate != entry.rate:
                return Decision("hold", "rate_changed")
            work, parent = self._scopes(action)
            if work.headroom is None or parent.headroom is None:
                return Decision("hold", "headroom_unproved")
            if min(work.headroom, parent.headroom) < 0:
                return Decision("stop", "cap_exhausted")
            self._entries[action.reservation_id] = replace(entry, fake_effect_consumed=True)
            self._fake_effects += 1
            return Decision("executed", "fake_effect_counted")

    def settle(
        self, action: Action, observation: Observation, verified: VerifiedReceipt | None,
    ) -> Decision:
        with self._lock:
            entry = self._entries.get(action.reservation_id)
            if (
                entry is None or entry.action != action or entry.adapter_link is not None or verified is None
                or verified.action != action or verified.observation != observation
            ):
                return Decision("hold", "correlation_unproved")
            return self._settle_verified(entry, observation)

    def settle_adapter(
        self, action: Action, result: AdapterResult, *, revision: int, settlement_rate: str | None,
        submission_unproved: bool = False,
    ) -> Decision:
        """Consume an authentic synthetic adapter result through its pinned link."""
        with self._lock:
            entry = self._entries.get(action.reservation_id)
            diagnostics = result.diagnostics
            if (
                entry is None or entry.action != action or entry.adapter_link is None
                or AdapterScope.from_diagnostics(diagnostics) != entry.adapter_link.scope
            ):
                return Decision("hold", "adapter_correlation_unproved")
            reference = ReceiptRef(action.attempt_id, action.reservation_id,
                                   diagnostics.transport_request_id, diagnostics.response_id,
                                   revision, entry.adapter_link.fallback_id)
            if submission_unproved:
                submission = "unknown"
            elif result.disposition == "no_submit":
                submission = "no_submit"
            elif (result.disposition in {"completed", "refusal", "incomplete", "provider_failed"}
                  and diagnostics.observed_model in (None, entry.action.model)):
                submission = "confirmed"
            else:
                submission = "possible"
            return self._settle_verified(entry, Observation(reference, submission, result.usage, settlement_rate))

    def _settle_verified(self, entry: Reservation, observation: Observation) -> Decision:
        if not self._authority.ledger_available:
            return Decision("hold", "ledger_unavailable")
        action = entry.action
        reference = observation.receipt
        if (
            reference.attempt_id != action.attempt_id or reference.reservation_id != action.reservation_id
            or not _quantity(reference.revision) or not reference.revision
            or not (reference.fallback_id or (reference.request_id and reference.response_id))
        ):
            return Decision("hold", "correlation_unproved")
        keys = reference.identity_keys()
        if any(self._receipt_owners.get(key, action.reservation_id) != action.reservation_id for key in keys):
            return Decision("hold", "receipt_owned_by_other_reservation")
        if observation in entry.observations:
            return Decision("duplicate", "identical_observation")
        if entry.state != "reserved" or any(
            earlier.receipt.revision >= reference.revision
            or (earlier.receipt.request_id is not None and reference.request_id != earlier.receipt.request_id)
            or (earlier.receipt.response_id is not None and reference.response_id != earlier.receipt.response_id)
            or (earlier.receipt.fallback_id is not None and reference.fallback_id != earlier.receipt.fallback_id)
            for earlier in entry.observations
        ):
            self._entries[action.reservation_id] = replace(entry, exposure_uncertain=True)
            return Decision("hold", "conflicting_observation")

        updated = replace(entry, observations=(*entry.observations, observation),
                          observation_ticks=(*entry.observation_ticks, self._authority.now_tick))
        decision, updated = self._apply_observation(updated, observation)
        for key in keys:
            self._receipt_owners[key] = action.reservation_id
        self._entries[action.reservation_id] = updated
        return decision

    def _apply_observation(
        self, entry: Reservation, observation: Observation,
    ) -> tuple[Decision, Reservation]:
        usage = observation.usage
        if observation.submission == "no_submit":
            if (entry.fake_effect_consumed or usage != UsageObservation()
                    or observation.receipt.response_id is not None
                    or any(earlier.submission == "confirmed" for earlier in entry.observations[:-1])):
                return Decision("hold", "conflicting_no_submit"), entry
            return (Decision("released", "verified_no_submit", entry.original_units),
                    replace(entry, state="released"))
        if observation.submission != "confirmed":
            return Decision("hold", "submission_unresolved"), entry
        if observation.rate_revision != entry.rate.revision:
            return Decision("hold", "settlement_rate_unproved"), entry

        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens
        total_tokens = usage.total_tokens
        if input_tokens is None or output_tokens is None or total_tokens is None:
            return Decision("hold", "usage_incomplete"), entry
        if (not all(_quantity(value) for value in (input_tokens, output_tokens, total_tokens))
                or input_tokens + output_tokens != total_tokens):
            return Decision("hold", "usage_inconsistent"), entry
        debit = input_tokens * entry.rate.input_units + output_tokens * entry.rate.output_units
        if debit > entry.original_units:
            return (Decision("hold", "reported_debit_over_reservation"),
                    replace(entry, exposure_uncertain=True))
        return (Decision("settled", "confirmed_usage", debit),
                replace(entry, state="settled", synthetic_debit=debit, exposure_uncertain=False))

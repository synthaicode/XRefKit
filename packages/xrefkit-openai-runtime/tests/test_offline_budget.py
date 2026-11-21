from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
from threading import Barrier
import unittest

import test_offline_responses

from xrefkit_openai_runtime.offline_budget import (
    Action, Authority, Grant, Observation, OfflineBudget, Rate, ReceiptRef, VerifiedReceipt,
)
from xrefkit_openai_runtime.offline_responses import UsageObservation


_FIXTURES = Path(__file__).parent / "fixtures"
_FROZEN_HASH = "d43147db5ff34e9f3deaaa2a1b17bbf72b2b90e444c3874539bb4100104a6fed"


class OfflineBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = (_FIXTURES / "e203-fixtures-r1" / "cases.json").read_bytes()
        if sha256(raw).hexdigest() != _FROZEN_HASH:
            raise AssertionError("frozen E203 fixture drift")
        cls.spec = json.loads(raw)
        cls.defaults = cls.spec["defaults"]
        cls.adapter_fixture = test_offline_responses.OfflineResponsesTests()
        type(cls.adapter_fixture).setUpClass()
        adapter_raw = (_FIXTURES / "e202-fixtures-r1" / "cases.json").read_bytes()
        if sha256(adapter_raw).hexdigest() != cls.spec["baseline"]["adapter_fixture_sha256"]:
            raise AssertionError("bound upstream E202 fixture drift")

    def synthetic_case(self, changes):
        settings = {**self.defaults, **changes}
        limits = settings["initial_ledger"]
        action = Action(
            settings["run_id"], settings["work_item_id"], settings["attempt_id"],
            settings["reservation_id"], settings["authorization_ref"],
            settings["binding_revision"], settings["policy_revision"],
            settings["rate_revision"], settings["model"], settings["action"],
            self.arguments(settings["arguments"]), settings["effect_class"], settings["destination"],
            settings["deadline_tick"], settings["token_bounds"]["input"], settings["token_bounds"]["output"],
        )
        grant = Grant(action, settings["grant_expires_tick"], settings.get("grant_status", "allowed"))
        rate_revision = settings.get("current_rate_revision", self.defaults["rate_revision"])
        rate = Rate(rate_revision, settings["model"], settings["rate_units"]["input"],
                    settings["rate_units"]["output"])
        authority = Authority(
            settings["now_tick"], settings.get("observed_binding_revision", settings["binding_revision"]),
            settings.get("current_policy_revision", settings["policy_revision"]),
            () if settings.get("grant", True) is None else (grant,),
            frozenset(settings["registry"]), frozenset(settings["available"]),
            frozenset(settings["policy_commands"]), frozenset(settings["user_commands"]),
            settings["confirmed_destination"], rate,
            settings.get("work_cap", limits["work_cap"]), settings.get("parent_cap", limits["parent_cap"]),
            cancelled=settings.get("cancelled", False),
            ledger_available=settings.get("ledger_available", limits["available"]),
            headroom_proved=settings.get("headroom_proved", True),
        )
        return action, authority

    @staticmethod
    def arguments(arguments):
        return json.dumps(arguments, sort_keys=True, separators=(",", ":")).encode()

    @staticmethod
    def evidence(case, variant, expected, decision, before, after, transitions=(), upstream=None):
        def summary(snapshot):
            return {
                "work": asdict(snapshot.work), "parent": asdict(snapshot.parent),
                "attempts_consumed": snapshot.attempts_consumed, "fake_effects": snapshot.fake_effects,
                "reservations": [
                    {"attempt": entry.action.attempt_id, "reservation": entry.action.reservation_id,
                     "state": entry.state, "original_units": entry.original_units,
                     "synthetic_debit": entry.synthetic_debit, "actual_bill": entry.actual_bill,
                     "fake_effect_consumed": entry.fake_effect_consumed,
                     "exposure_uncertain": entry.exposure_uncertain,
                     "observations": [asdict(observation) for observation in entry.observations]}
                    for entry in snapshot.reservations
                ],
            }

        print(json.dumps({
            "case": case, "variant": variant, "fixture_sha256": _FROZEN_HASH, "expected": expected,
            "observed_disposition": decision.disposition, "reason": decision.reason,
            "fake_effects_observed": after.fake_effects - before.fake_effects,
            "ledger_before": summary(before), "ledger_after": summary(after),
            "transitions": [asdict(transition) for transition in transitions],
            "upstream": upstream,
        }))

    def test_E203_01_permissions(self):
        case = "E203-01"
        outcomes = {
            "permit_then_reserve_16_and_one_fake_effect": ("executed", "fake_effect_counted", 1),
            "deny_zero_additional_effect": ("deny", "permit_consumed", 0),
            "stop_zero_fake_effect": ("stop", "cancelled", 0),
        }
        denial = {"grant-missing": "grant_missing_or_denied", "grant-denied": "grant_missing_or_denied",
                  "user-excluded": "action_not_allowed"}
        for variant, changes, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                action, authority = self.synthetic_case(changes)
                ledger = OfflineBudget(authority)
                before = ledger.snapshot(action)
                effective = replace(action, canonical_arguments=self.arguments(changes["effective_arguments"])) \
                    if "effective_arguments" in changes else action
                admission = ledger.reserve(action)
                transitions = [admission]
                if admission.disposition == "reserved":
                    self.assertEqual(admission.units, self.defaults["reservation_units"])
                    if changes.get("revoke_after_preflight"):
                        revoked = replace(authority.grants[0], status="revoked")
                        ledger.update_authority(replace(authority, grants=(revoked,)))
                    if changes.get("permit_consumed"):
                        first = ledger.dispatch_fake(action)
                        self.assertEqual(first.disposition, "executed")
                        transitions.append(first)
                        before = ledger.snapshot(action)
                    decision = ledger.dispatch_fake(effective)
                else:
                    decision = admission
                    self.assertEqual(ledger.dispatch_fake(effective).disposition, admission.disposition)
                after = ledger.snapshot(action)
                if expected == "deny_zero_fake_effect":
                    outcome = ("deny", denial[variant], 0)
                elif expected == "hold_zero_fake_effect":
                    reason = "destination_unconfirmed" if variant == "new-destination" else (
                        "grant_or_binding_no_longer_current")
                    outcome = ("hold", reason, 0)
                else:
                    outcome = outcomes[expected]
                self.assertEqual((decision.disposition, decision.reason,
                                  after.fake_effects - before.fake_effects), outcome)
                self.assertEqual(after.work.reserved, admission.units or 0)
                self.assertEqual(after.parent.reserved, after.work.reserved)
                self.evidence(case, variant, expected, decision, before, after, transitions)

    def test_E203_02_reservations(self):
        case = "E203-02"
        outcomes = {
            "reserve_16": ("reserved", "reservation_created", 16),
            "stop_no_reservation_or_effect": ("stop", "cap_exhausted", 0),
            "stop_no_new_reservation": ("stop", "cap_exhausted", 16),
            "exactly_one_reservation_of_16": ("reserved", "reservation_created", 16),
            "stop": ("stop", "deadline_elapsed", 0),
            "hold_no_cap_reset": ("hold", "headroom_unproved", 0),
        }
        for variant, changes, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                action, authority = self.synthetic_case(changes)
                competitor = None
                if "contenders" in changes:
                    first, second = changes["contenders"]
                    self.assertEqual([action.attempt_id, action.reservation_id], first)
                    competitor = replace(action, attempt_id=second[0], reservation_id=second[1],
                                         authorization_ref="grant-2")
                elif "existing_reserved_units" in changes:
                    competitor = replace(action, attempt_id="existing-attempt", reservation_id="existing-reserve",
                                         authorization_ref="existing-grant")
                if competitor is not None:
                    authority = replace(authority, grants=(*authority.grants,
                                                           replace(authority.grants[0], action=competitor)))
                ledger = OfflineBudget(authority)
                if "existing_reserved_units" in changes:
                    self.assertEqual(ledger.reserve(competitor).units, changes["existing_reserved_units"])
                before = ledger.snapshot(action)
                if "contenders" in changes:
                    transitions = self.reserve_concurrently(ledger, action, competitor)
                    decision = next(result for result in transitions if result.disposition == "reserved")
                    self.assertEqual(ledger.snapshot(action).attempts_consumed, 1)

                    # Both independent work scopes have room; the shared parent still admits only one.
                    separated = replace(competitor, work_item_id="work-203-second-scope")
                    two_scopes = OfflineBudget(replace(authority, grants=(
                        authority.grants[0], replace(authority.grants[1], action=separated),
                    )))
                    self.reserve_concurrently(two_scopes, action, separated)
                    original_scope = two_scopes.snapshot(action)
                    second_scope = two_scopes.snapshot(separated)
                    self.assertEqual(original_scope.work.reserved + second_scope.work.reserved, 16)
                    self.assertEqual(original_scope.parent, second_scope.parent)
                    self.assertEqual(original_scope.parent.headroom, changes["parent_cap"] - 16)
                else:
                    decision = ledger.reserve(action)
                    transitions = (decision,)
                after = ledger.snapshot(action)
                if expected == "hold":
                    reason = {
                        "cap-unknown": "headroom_unproved", "rate-missing": "rate_or_bounds_unproved",
                        "stale-rate": "rate_or_bounds_unproved", "stale-policy": "grant_or_binding_no_longer_current",
                    }[variant]
                    outcome = ("hold", reason, 0)
                else:
                    outcome = outcomes[expected]
                self.assertEqual((decision.disposition, decision.reason, after.work.reserved), outcome)
                self.assertEqual(after.parent.reserved, after.work.reserved)
                self.assertEqual(after.fake_effects, 0)
                if decision.disposition != "reserved":
                    self.assertEqual(before, after)
                    if "ledger_available" in changes:
                        self.assertIsNone(after.parent.headroom)
                        self.assertEqual(after.parent.cap, self.defaults["initial_ledger"]["parent_cap"])
                self.evidence(case, variant, expected, decision, before, after, transitions)

    def reserve_concurrently(self, ledger, first, second):
        start = Barrier(2, timeout=5)

        def contender(action):
            start.wait()
            return ledger.reserve(action)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = tuple(pool.map(contender, (first, second)))
        self.assertCountEqual([(result.disposition, result.units) for result in results],
                              [("reserved", self.defaults["reservation_units"]), ("stop", None)])
        return results

    def upstream_observation(self, fixture_key):
        fixture_case, fixture_variant = fixture_key.split("/")
        row = next(row for row in self.adapter_fixture.spec["cases"][fixture_case] if row[0] == fixture_variant)
        settings, sends, _, invoke = self.adapter_fixture.setup_variant(row[1])
        result = invoke()
        expected_effects = 0 if row[2] == "zero" else 1
        self.assertEqual(len(sends), expected_effects)
        if "transport_observation" in row[1]:
            self.assertEqual(result.reason, row[1]["transport_observation"])
        diagnostics = result.diagnostics
        assignment = self.adapter_fixture.request.assignment
        self.assertEqual((diagnostics.run_id, diagnostics.work_item_id, diagnostics.binding_sha256,
                          diagnostics.attempt_id, diagnostics.reservation_ref), (
                              assignment.run_id, assignment.work_item_id, assignment.binding_sha256,
                              settings["attempt_id"], self.adapter_fixture.request.reservation_ref,
                          ))
        return result, {"fixture": fixture_key, "fake_effects": len(sends),
                        "disposition": result.disposition, "reason": result.reason,
                        "diagnostics": asdict(diagnostics)}

    def settlement_case(self, changes):
        action, authority = self.synthetic_case({})
        ledger = OfflineBudget(authority)
        self.assertEqual(ledger.reserve(action).units, self.defaults["reservation_units"])
        ledger.update_authority(replace(authority, ledger_available=changes.get("ledger_available", True),
                                        headroom_proved=changes.get("headroom_proved", True)))
        default_receipt = self.defaults["receipt"]
        values = changes.get("usage", self.defaults["reported_complete"])
        upstream = None
        if "use_upstream" in changes:
            result, upstream = self.upstream_observation(changes["use_upstream"])
            usage = result.usage
            request_id, response_id = result.diagnostics.transport_request_id, result.diagnostics.response_id
            if request_id is not None:
                self.assertEqual(request_id, default_receipt["request_id"])
            if response_id is not None:
                self.assertEqual(response_id, default_receipt["response_id"])
            if result.disposition == "no_submit":
                self.assertEqual(changes["evidence"], "trusted-matching-no-submit")
                submission = "no_submit"
            elif result.disposition == "unknown_remote_outcome":
                submission = "possible"
            else:
                self.assertEqual(result.disposition, changes.get("outcome", "completed"))
                submission = "confirmed"
        else:
            usage = UsageObservation(*(values.get(key) for key in (
                "input", "output", "total", "cached_input", "reasoning_output",
            )))
            request_id, response_id = default_receipt["request_id"], default_receipt["response_id"]
            submission = "confirmed"
        reference = ReceiptRef(
            changes.get("receipt_attempt_id", default_receipt["attempt_id"]),
            changes.get("receipt_reservation_id", default_receipt["reservation_id"]),
            request_id, response_id, default_receipt["receipt_revision"],
        )
        observation = Observation(reference, changes.get("submission", submission), usage,
                                  changes.get("settlement_rate_revision", action.rate_revision))
        expected_ref = replace(reference, attempt_id=action.attempt_id, reservation_id=action.reservation_id)
        verified = None if changes.get("verified_binding_ref", True) is None else VerifiedReceipt(
            action, replace(observation, receipt=expected_ref),
        )
        return action, ledger, observation, verified, upstream

    def assert_amounts(self, snapshot, reserved, debit):
        self.assertEqual((snapshot.work.reserved, snapshot.work.debit), (reserved, debit))
        self.assertEqual((snapshot.parent.reserved, snapshot.parent.debit), (reserved, debit))
        for scope in (snapshot.work, snapshot.parent):
            if scope.headroom is not None:
                self.assertEqual(scope.headroom, scope.cap - reserved - debit)
        self.assertEqual(len(snapshot.reservations), 1)
        self.assertEqual(snapshot.reservations[0].original_units, self.defaults["reservation_units"])
        self.assertIsNone(snapshot.reservations[0].actual_bill)
        self.assertEqual(snapshot.fake_effects, 0)

    def test_E203_03_known_usage(self):
        case = "E203-03"
        amounts = {"debit_14_release_unused_2": (14, 2), "settle_zero_release_16_once": (0, 16),
                   "debit_8_release_unused_8": (8, 8)}
        for variant, changes, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                action, ledger, observation, verified, upstream = self.settlement_case(changes)
                before = ledger.snapshot(action)
                decision = ledger.settle(action, observation, verified)
                debit, release = amounts[expected]
                after = ledger.snapshot(action)
                self.assertEqual((decision.disposition, decision.reason, decision.units),
                                 ("settled", "confirmed_usage", debit))
                self.assert_amounts(after, 0, debit)
                self.assertEqual(after.work.headroom - before.work.headroom, release)
                self.assertEqual(after.parent.headroom - before.parent.headroom, release)
                self.assertEqual(after.reservations[0].synthetic_debit, debit)
                self.assertEqual(after.reservations[0].observations, (observation,))
                if debit == 0:
                    replay = ledger.settle(action, observation, verified)
                    self.assertEqual(replay.disposition, "duplicate")
                    self.assertEqual(ledger.snapshot(action), after)
                self.evidence(case, variant, expected, decision, before, after, upstream=upstream)

    def test_E203_04_unreliable_usage(self):
        case = "E203-04"
        outcomes = {
            "retain_16_all_usage_unknown": ("usage_incomplete", (None, None, None)),
            "retain_16_keep_reported_input_others_unknown": ("usage_incomplete", (8, None, None)),
            "retain_16_keep_zero_and_unknown_distinct": ("usage_incomplete", (0, None, None)),
            "retain_16_hold_conflict": ("usage_inconsistent", (8, 3, 99)),
            "retain_16_hold_conservative_headroom": ("reported_debit_over_reservation", (8, 5, 13)),
            "retain_16_no_synthetic_debit": ("settlement_rate_unproved", (8, 3, 11)),
            "retain_16_hold_next_admission": ("submission_unresolved", (None, None, None)),
        }
        for variant, changes, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                action, ledger, observation, verified, upstream = self.settlement_case(changes)
                next_action = replace(action, attempt_id="attempt-next", reservation_id="reserve-next",
                                      authorization_ref="grant-next")
                if "headroom_proved" in changes or variant == "over-reserve":
                    _, host = self.synthetic_case({})
                    ledger.update_authority(replace(host, headroom_proved=changes.get("headroom_proved", True),
                                                    grants=(*host.grants, replace(host.grants[0], action=next_action))))
                if "hold_reason" in changes:
                    self.assertEqual(changes["hold_reason"], "unresolved_exposure")
                    observation = replace(observation, submission="possible", usage=UsageObservation())
                    verified = VerifiedReceipt(action, observation)
                before = ledger.snapshot(action)
                decision = ledger.settle(action, observation, verified)
                after = ledger.snapshot(action)
                reason, observed_counts = outcomes[expected]
                self.assertEqual((decision.disposition, decision.reason), ("hold", reason))
                self.assert_amounts(after, 16, 0)
                self.assertIsNone(after.reservations[0].synthetic_debit)
                retained, = after.reservations[0].observations
                self.assertEqual(retained, observation)
                self.assertEqual((retained.usage.input_tokens, retained.usage.output_tokens,
                                  retained.usage.total_tokens), observed_counts)
                transitions = ()
                if "headroom_proved" in changes or variant == "over-reserve":
                    self.assertIsNone(after.work.headroom)
                    self.assertIsNone(after.parent.headroom)
                    next_admission = ledger.reserve(next_action)
                    self.assertEqual((next_admission.disposition, next_admission.reason),
                                     ("hold", "headroom_unproved"))
                    self.assertEqual(ledger.snapshot(action), after)
                    transitions = (next_admission,)
                self.evidence(case, variant, expected, decision, before, after, transitions, upstream)

    def test_E203_05_submission(self):
        case = "E203-05"
        for variant, changes, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                action, ledger, observation, verified, upstream = self.settlement_case(changes)
                before = ledger.snapshot(action)
                decision = ledger.settle(action, observation, verified)
                after = ledger.snapshot(action)
                transitions = ()
                if expected == "release_provider_16_once_keep_attempt_history":
                    self.assertEqual((decision.disposition, decision.reason, decision.units),
                                     ("released", "verified_no_submit", self.defaults["reservation_units"]))
                    self.assert_amounts(after, 0, 0)
                    self.assertEqual(after.attempts_consumed, changes["attempts_consumed"])
                    self.assertEqual(after.parent.headroom - before.parent.headroom, decision.units)
                    duplicate = ledger.settle(action, observation, verified)
                    self.assertEqual(duplicate.disposition, "duplicate")
                    self.assertEqual(ledger.snapshot(action), after)
                    transitions = (duplicate,)
                else:
                    self.assertEqual((decision.disposition, decision.reason), ("hold", "submission_unresolved"))
                    self.assert_amounts(after, 16, 0)
                    if expected == "preserve_all_zeros_keep_reservation_16":
                        self.assertEqual(observation.usage, UsageObservation(0, 0, 0))
                    else:
                        self.assertEqual(expected, "hold_reservation_16_reconcile")
                self.assertIsNone(after.reservations[0].synthetic_debit)
                self.assertEqual(after.reservations[0].observations, (observation,))
                self.evidence(case, variant, expected, decision, before, after, transitions, upstream)

    def test_E203_06_reconciliation(self):
        case = "E203-06"
        for variant, changes, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                action, ledger, observation, verified, upstream = self.settlement_case(changes)
                before = ledger.snapshot(action)
                transitions = []
                if expected == "hold_then_debit_14_once":
                    self.assertEqual(changes["sequence"], ["possible_submit", "matching_complete", "identical_replay"])
                    pending = replace(observation, receipt=replace(observation.receipt, request_id=None,
                                                                  response_id=None),
                                      submission="possible", usage=UsageObservation())
                    pending_decision = ledger.settle(action, pending, VerifiedReceipt(action, pending))
                    self.assertEqual((pending_decision.disposition, pending_decision.reason),
                                     ("hold", "submission_unresolved"))
                    self.assert_amounts(ledger.snapshot(action), 16, 0)
                    observation = replace(observation, receipt=replace(observation.receipt,
                                                                      revision=pending.receipt.revision + 1))
                    verified = VerifiedReceipt(action, observation)
                    transitions.append(pending_decision)
                if expected == "hold_conflict_no_overwrite_or_second_debit":
                    self.assertEqual(changes["sequence"], ["matching_complete", "same_identity_different_usage"])
                    changed = replace(observation, usage=UsageObservation(0, 0, 0))
                    mismatch = ledger.settle(action, changed, verified)
                    self.assertEqual((mismatch.disposition, mismatch.reason), ("hold", "correlation_unproved"))
                    self.assertEqual(ledger.snapshot(action), before)
                    transitions.append(mismatch)

                decision = ledger.settle(action, observation, verified)
                after = ledger.snapshot(action)
                settled_cases = {"one_14_debit_one_release_duplicate_no_op", "hold_then_debit_14_once",
                                 "hold_conflict_no_overwrite_or_second_debit"}
                if expected in settled_cases:
                    self.assertEqual((decision.disposition, decision.reason, decision.units),
                                     ("settled", "confirmed_usage", 14))
                    self.assert_amounts(after, 0, 14)
                    self.assertEqual(after.parent.headroom - before.parent.headroom, 2)
                    self.assertEqual(after.reservations[0].observations[-1], observation)
                    transitions.append(decision)
                    if expected == "hold_conflict_no_overwrite_or_second_debit":
                        conflicting = ledger.settle(action, changed, VerifiedReceipt(action, changed))
                        self.assertEqual((conflicting.disposition, conflicting.reason),
                                         ("hold", "conflicting_observation"))
                        revised = ledger.snapshot(action)
                        self.assert_amounts(revised, 0, 14)
                        self.assertEqual(revised.reservations[0].observations, after.reservations[0].observations)
                        self.assertTrue(revised.reservations[0].exposure_uncertain)
                        self.assertIsNone(revised.parent.headroom)
                        self.assertIsNone(revised.work.headroom)
                        after, decision = revised, conflicting
                    else:
                        self.assertEqual(changes.get("deliveries", 2), 2)
                        duplicate = ledger.settle(action, observation, verified)
                        self.assertEqual(duplicate.disposition, "duplicate")
                        self.assertEqual(ledger.snapshot(action), after)
                        transitions.append(duplicate)
                else:
                    self.assert_amounts(after, 16, 0)
                    self.assertEqual(before, after)
                    if expected == "hold_missing_correlation":
                        self.assertEqual((decision.disposition, decision.reason), ("hold", "correlation_unproved"))
                    else:
                        self.assertEqual(expected, "hold_no_reset_no_fake_retry")
                        self.assertEqual((decision.disposition, decision.reason), ("hold", "ledger_unavailable"))
                        retry = ledger.dispatch_fake(action)
                        self.assertEqual(retry.disposition, "hold")
                        self.assertEqual(ledger.snapshot(action), after)
                        transitions.append(retry)
                self.evidence(case, variant, expected, decision, before, after, transitions, upstream)

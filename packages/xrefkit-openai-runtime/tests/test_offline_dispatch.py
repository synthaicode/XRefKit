from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
from threading import Barrier
import unittest

import test_offline_responses

from xrefkit_openai_runtime.offline_budget import Action, Authority, Grant, OfflineBudget, Rate
from xrefkit_openai_runtime.offline_context import assemble_offline_context
from xrefkit_openai_runtime.offline_dispatch import (
    OfflineToolDispatch, PreparedTool, ToolContextPin, ToolDecision, ToolDefinition,
    ToolHost, ToolRequest, ToolReturnScope, tool_budget_action,
)


_FIXTURES = Path(__file__).parent / "fixtures"
_FROZEN_HASH = "5532f5256a059233cf8c65842cd28f3e5df78413f905f2be6ed941af4e9c7ec6"


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


class OfflineDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (_FIXTURES / "e204-fixtures-r1" / "cases.json").read_bytes()
        if sha256(raw).hexdigest() != _FROZEN_HASH:
            raise AssertionError("frozen #204 fixture drift")
        cls.spec = json.loads(raw)
        cls.defaults = cls.spec["defaults"]
        cls.limits = cls.spec["limits"]
        registry = cls.spec["registry"]
        tool = registry["tool"]
        cls.definition = ToolDefinition(
            tool["id"], tool["version"], tool["schema"], tool["operation"], registry["revision"],
            tool["required_knowledge"], tool["required_capability"],
            cls.limits["argument_bytes"], cls.limits["result_bytes"],
        )
        upstream = test_offline_responses.OfflineResponsesTests
        upstream.setUpClass()
        cls.accepted_context = upstream.context
        cls.context_request = upstream.request
        context_fixture = upstream.spec["baseline"]
        cls.context_root = _FIXTURES / context_fixture["context_revision"]
        cls.context_inventory = (cls.context_root / "fixture-inventory.json").read_bytes()
        cls.context_inventory_digest = context_fixture["inventory_sha256"]
        budget_bytes = (_FIXTURES / "e203-fixtures-r1" / "cases.json").read_bytes()
        expected = cls.spec["baseline"]["budget_fixture_sha256"]
        if sha256(budget_bytes).hexdigest() != expected:
            raise AssertionError("accepted #203 fixture drift")

    def request(self, changes=None):
        row = {**self.defaults, **(changes or {})}
        args = row["raw_args"].encode() if "raw_args" in row else encode(row["args"])
        return ToolRequest(
            row["run"], row["work"], row["route"], row["generation"], row["operation"],
            row["attempt"], row["provider_call"], row["grant"], row["reservation"], row["policy"],
            row["tool"], row["version"], args, row["target"], row["destination"], row["recipient"],
            self.limits["deadline_tick"],
        )

    def assemble_for(self, recipient, *, authorized_recipient, stale_assignment=False):
        assignment = self.context_request.assignment
        if stale_assignment:
            assignment = assignment.model_copy(update={"binding_sha256": "0" * 64})
        return assemble_offline_context(
            self.context_request, current_assignment=assignment, fixture_root=self.context_root,
            inventory_bytes=self.context_inventory, inventory_sha256=self.context_inventory_digest,
            destination=recipient, authorized_destination=authorized_recipient,
        )

    def setup_case(self, changes=None, additional=(), *, reserve_baseline=True):
        changes = changes or {}
        baseline = self.request()
        rate = Rate("fixture-rate-r1", "fixture-tool-ledger", 1, 1)
        units = self.defaults["synthetic_reservation_units"]
        actions = tuple(tool_budget_action(self.definition, request, rate_revision=rate.revision, units=units)
                        for request in (baseline, *additional))
        self.assertTrue(all(isinstance(action, Action) for action in actions))
        granted = frozenset({baseline.tool_id})
        authority = Authority(
            self.limits["prepare_tick"], baseline.generation, baseline.policy,
            tuple(Grant(action, baseline.deadline) for action in actions),
            granted, granted, granted, frozenset(self.defaults["user_commands"]), baseline.destination,
            rate, units * 3, units * 3,
        )
        context = self.accepted_context
        pin = ToolContextPin((baseline.run, baseline.work), baseline.route, baseline.generation,
                             sha256(context.payload).hexdigest(), context.provenance_sha256)
        initial_runner = self.spec["runners"][0]
        host = ToolHost(
            baseline.route, baseline.generation, initial_runner["id"], initial_runner["revision"],
            self.spec["registry"]["revision"], self.spec["knowledge"]["revision"],
            frozenset(initial_runner["capabilities"]), frozenset({baseline.target}), context, pin,
            ToolReturnScope(
                baseline.recipient, self.assemble_for(baseline.recipient, authorized_recipient=baseline.recipient),
            ),
            authority,
        )
        result = encode(changes.get("fake_result", self.defaults["fake_result"]))
        dispatcher = OfflineToolDispatch(self.definition, host, units=units, fake_result=result)
        requests = (baseline, *additional) if reserve_baseline else additional
        for request in requests:
            self.assertIsNone(dispatcher.reserve_tool(request))
        return dispatcher, host, baseline

    def change_host(self, host, row, *, advancing=False):
        authority = host.authority
        tick = self.limits["entry_tick"] if advancing else authority.now_tick
        confirmations = row.get("confirmed_destinations", self.defaults["confirmed_destinations"])
        commands = frozenset(row.get("user_commands", authority.user_commands))
        grants = authority.grants
        if "grant_state" in row:
            grants = tuple(replace(grant, status=row["grant_state"]) for grant in grants)
        caps = authority.parent_cap
        if row.get("budget_status") == "stop":
            caps = self.defaults["synthetic_reservation_units"] + row.get("headroom", -1)
        if row.get("budget_status") == "deny":
            grants = ()
        updated = replace(
            authority, now_tick=row.get("tick", tick), grants=grants, user_commands=commands,
            confirmed_destination=confirmations[0] if confirmations else "",
            cancelled=row.get("cancelled", authority.cancelled), parent_cap=caps,
            binding_revision=row.get("generation", authority.binding_revision),
            headroom_proved=row.get("budget_status") != "hold",
        )
        runner = next(profile for profile in self.spec["runners"]
                      if profile["id"] == row.get("runner", host.runner_id))
        capabilities = frozenset(runner["capabilities"])
        if "runner_capability" in row and row["runner_capability"] is None:
            capabilities = None
        context = host.context
        if row.get("context_status") == "held":
            context = self.assemble_for(self.defaults["recipient"],
                                        authorized_recipient=self.defaults["recipient"], stale_assignment=True)
            self.assertEqual(context.hold_reason, "assignment_not_current")
        return_scope = host.return_scope
        if row.get("return_egress") is False:
            recipient = row.get("recipient", host.return_scope.recipient)
            authorized = host.return_scope.recipient if recipient != host.return_scope.recipient else ""
            held = self.assemble_for(recipient, authorized_recipient=authorized)
            self.assertEqual(held.hold_reason, "unauthorized_destination")
            return_scope = ToolReturnScope(recipient, held)
        return replace(
            host, authority=updated, runner_id=runner["id"],
            runner_revision=row.get("runner_revision", runner["revision"]), capabilities=capabilities,
            registry_evidence=row.get("registry_evidence", row.get("registry_revision", host.registry_evidence)),
            knowledge_revision=row.get("knowledge_revision", host.knowledge_revision),
            generation=row.get("generation", host.generation), context=context,
            intent_available=row.get("intent_store_available", True),
            return_scope=return_scope,
        )

    def invoke(self, dispatcher, request, **options):
        prepared = dispatcher.prepare(request)
        if isinstance(prepared, ToolDecision):
            return prepared
        return dispatcher.invoke(prepared, request, **options)

    @staticmethod
    def summarized(decision):
        return {"outcome": decision.outcome, "reason": decision.reason,
                "receipt": asdict(decision.receipt) if decision.receipt else None,
                "evidence": asdict(decision.evidence) if decision.evidence else None,
                "returned_bounded_value": decision.value is not None}

    def record(self, case, variant, row, expected, actual, before, after, decisions, **extra):
        self.assertEqual(tuple(actual), tuple(expected))
        self.assertEqual(after.entry_count, expected[2])
        self.assertEqual(after.admissions_consumed - before.admissions_consumed, after.entry_count)
        self.assertEqual(before.entry_count, 0)
        self.assertLessEqual(len(after.intents), after.entry_count)
        for decision in decisions:
            self.assertIsNotNone(decision.evidence)
            self.assertEqual(decision.evidence.workflow_acceptance, "not_evaluated")
            self.assertEqual(len(decision.evidence.proposal_digest), 64)
            self.assertEqual(len(decision.evidence.target_digest), 64)
            self.assertEqual(len(decision.evidence.correlation.grant_digest), 64)
            self.assertEqual(len(decision.evidence.correlation.reservation_digest), 64)
        evidence = {
            "case": case, "variant": variant, "fixture_sha256": _FROZEN_HASH,
            "expected": expected, "observed": actual,
            "observed_disposition": actual[0], "reason": actual[1], "fake_entries": after.entry_count,
            "schedule": row["stage"], "before": asdict(before), "after": asdict(after),
            "decisions": [self.summarized(decision) for decision in decisions],
            "entry_site": "offline_dispatch._FakeRunner._enter",
            **extra,
        }
        serialized = json.dumps(evidence)
        for canary in self.spec["canaries"].values():
            self.assertNotIn(canary, serialized)
        print(serialized)

    def test_E204_01_allowlist_and_input(self):
        case = "E204-01"
        for variant, row, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                dispatcher, host, base = self.setup_case(row)
                dispatcher.update_host(self.change_host(host, row))
                before = dispatcher.snapshot(base)
                discovered = dispatcher.discover()
                if row["stage"].startswith("discover"):
                    self.assertEqual(tuple(item.tool_id for item in discovered),
                                     (base.tool_id,) if row["stage"] == "discover_then_invoke"
                                     and variant == "listed-and-permitted" else ())
                decision = self.invoke(dispatcher, self.request(row))
                after = dispatcher.snapshot(base)
                reason = decision.reason
                if decision.outcome == "executed":
                    self.assertEqual(reason, "bounded_typed_result")
                    self.assertIsNotNone(decision.receipt)
                    self.assertEqual(decision.value, self.defaults["fake_result"]["value"])
                    reason = "matched_allowlist"
                self.record(case, variant, row, expected, (decision.outcome, reason, after.entry_count),
                            before, after, [decision], exposed_versions=[item.version for item in discovered])
        dispatcher, host, base = self.setup_case()
        dispatcher.update_host(replace(host, listing_approved=False))
        self.assertEqual(dispatcher.discover(), ())
        dispatcher.update_host(replace(host, context_pin=replace(host.context_pin, generation=0)))
        self.assertEqual(dispatcher.discover(), ())

    def test_E204_02_last_check(self):
        case = "E204-02"
        for variant, row, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                change = row.get("after_prepare", {})
                omit_reservation = ("reservation" in change and change["reservation"] is None
                                    or change.get("reservation_matches") is False)
                dispatcher, host, base = self.setup_case(row, reserve_baseline=not omit_reservation)
                prepared = dispatcher.prepare(base)
                self.assertIsInstance(prepared, PreparedTool)
                if change.get("reservation_matches") is False:
                    self.seed_mismatched_reservation(dispatcher, host, base)
                if change.get("reservation_state") == "consumed":
                    # Seed the real private #203 gate without entering the #204 runner.
                    seeded = dispatcher._budget.dispatch_fake(host.authority.grants[0].action)
                    self.assertEqual(seeded.disposition, "executed")
                before = dispatcher.snapshot(base)
                dispatcher.update_host(self.change_host(host, change, advancing=True))
                at_entry = dispatcher.snapshot(base)
                input_changes = {key: change[key] for key in ("args", "target", "destination") if key in change}
                decision = dispatcher.invoke(prepared, self.request(input_changes))
                after = dispatcher.snapshot(base)
                reason = decision.reason
                if decision.outcome == "executed":
                    self.assertEqual(reason, "bounded_typed_result")
                    self.assertEqual(decision.receipt.entry_tick, self.limits["entry_tick"])
                    reason = "current_at_entry"
                else:
                    self.assertEqual(after.intents, ())
                if variant == "missing-reservation":
                    self.assertEqual(at_entry.reservations, ())
                if variant == "stale-reservation":
                    self.assertEqual(len(at_entry.reservations), 1)
                    self.assertNotEqual(at_entry.reservations[0].action_digest,
                                        sha256(host.authority.grants[0].action.canonical_arguments).hexdigest())
                if variant == "consumed-reservation":
                    self.assertTrue(at_entry.reservations[0].consumed)
                    self.assertEqual(after.admissions_consumed, before.admissions_consumed)
                if variant == "cap-exhausted-after-prepare":
                    self.assertEqual(at_entry.parent_headroom, change["headroom"])
                actual = (decision.outcome, reason, after.entry_count)
                self.record(case, variant, row, expected, actual, before, after, [decision],
                            prepared_binding=prepared.request.generation, prepared_runner=prepared.runner_revision,
                            ledger_at_entry=asdict(at_entry))
        dispatcher, host, base = self.setup_case()
        prepared = dispatcher.prepare(base)
        replaced_context = replace(host.context, provenance=b"other trusted synthetic context")
        repin = replace(host.context_pin, provenance_sha256=replaced_context.provenance_sha256)
        dispatcher.update_host(replace(host, context=replaced_context, context_pin=repin))
        decision = dispatcher.invoke(prepared, base)
        self.assertEqual((decision.outcome, decision.reason), ("hold", "context_held"))
        self.assertEqual(dispatcher.snapshot(base).entry_count, 0)

    def seed_mismatched_reservation(self, dispatcher, host, base):
        stale = replace(base, args=encode({"key": "different"}))
        original_grant = host.authority.grants[0]
        action = tool_budget_action(self.definition, stale, rate_revision=original_grant.action.rate_revision,
                                    units=self.defaults["synthetic_reservation_units"])
        authority = replace(host.authority, grants=(replace(original_grant, action=action),))
        dispatcher.update_host(replace(host, authority=authority))
        self.assertIsNone(dispatcher.reserve_tool(stale))
        dispatcher.update_host(host)

    def test_E204_03_concurrent_and_replayed(self):
        case = "E204-03"
        for variant, row, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                if row["stage"] == "barrier_two_contenders_then_replay":
                    decisions, before, after, observations = self.concurrent_case(row)
                    outcome, reason = "one_execution_then_replays", "single_operation_claim"
                elif row["stage"] == "invoke_then_redeliver":
                    dispatcher, host, base = self.setup_case(row)
                    before = dispatcher.snapshot(base)
                    first = self.invoke(dispatcher, base)
                    second = self.invoke(dispatcher, self.request(row["after"]))
                    self.assertEqual((first.outcome, second.outcome), ("executed", "deny"))
                    self.assertEqual(second.reason, "operation_digest_conflict")
                    after = dispatcher.snapshot(base)
                    decisions, observations = (first, second), {}
                    outcome, reason = "executed_then_deny", second.reason
                else:
                    successor = self.request(row["after"])
                    dispatcher, host, base = self.setup_case(row, additional=(successor,))
                    before = dispatcher.snapshot(base)
                    first = self.invoke(dispatcher, base)
                    second = self.invoke(dispatcher, successor)
                    self.assertEqual((first.outcome, second.outcome), ("executed", "executed"))
                    self.assertEqual(first.receipt.action_digest, second.receipt.action_digest)
                    self.assertNotEqual(first.receipt.correlation, second.receipt.correlation)
                    after = dispatcher.snapshot(base)
                    decisions, observations = (first, second), {}
                    outcome, reason = "executed_twice", "separately_authorized"
                self.assertEqual(after.admissions_consumed, row["tool_reservations_consumed"])
                self.record(case, variant, row, expected, (outcome, reason, after.entry_count),
                            before, after, decisions, **observations)

    def concurrent_case(self, row):
        alternate = self.request({"attempt": row["contenders"][1], "grant": "grant-2",
                                  "reservation": "reservation-2"})
        dispatcher, host, base = self.setup_case(row, additional=(alternate,))
        before = dispatcher.snapshot(base)
        barrier = Barrier(2)

        def compete(request):
            prepared = dispatcher.prepare(request)
            self.assertIsInstance(prepared, PreparedTool)
            barrier.wait(timeout=5)
            return request, dispatcher.invoke(prepared, request)

        with ThreadPoolExecutor(2) as pool:
            raced = tuple(pool.map(compete, (base, alternate)))
        winners = tuple(request for request, result in raced if result.outcome == "executed")
        self.assertEqual(len(winners), 1)
        for request, result in raced:
            if request != winners[0]:
                self.assertIn(result.outcome, row["expected_substeps"]["race"]["allowed_secondary_outcomes"])
        race_snapshot = dispatcher.snapshot(base)
        self.assertEqual(race_snapshot.entry_count, row["expected_substeps"]["race"]["entry_count"])
        same, new = tuple(self.invoke(dispatcher, replace(winners[0], provider_call=call)) for call in row["after"])
        self.assertEqual((same.outcome, new.outcome), ("replay", "replay"))
        self.assertEqual(same.receipt, new.receipt)
        after = dispatcher.snapshot(base)
        self.assertEqual(after.entry_count - race_snapshot.entry_count,
                         row["expected_substeps"]["after_receipt"]["additional_entries"])
        return tuple(result for _, result in raced) + (same, new), before, after, {
            "race_snapshot": asdict(race_snapshot), "contenders": len(raced),
        }

    def test_E204_04_missing_intent_or_effect(self):
        case = "E204-04"
        for variant, row, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                dispatcher, host, base = self.setup_case(row)
                dispatcher.update_host(self.change_host(host, row))
                before = dispatcher.snapshot(base)
                decisions = []
                supplemental = {}
                if "replacement" not in row:
                    decision = self.invoke(dispatcher, base, reject_before_entry="reject_at" in row)
                    decisions.append(decision)
                    outcome, reason = decision.outcome, decision.reason
                    self.assertEqual(dispatcher.snapshot(base), before)
                else:
                    paused = row["stage"] == "enter_then_pause_before_receipt_then_replace"
                    if paused:
                        dispatcher.update_host(self.change_host(host, {"tick": row["old_worker_paused_at_tick"]}))
                    first = self.invoke(dispatcher, base, interruption="paused" if paused else "receipt_lost")
                    self.assertEqual(first.outcome, "hold")
                    self.assertEqual(first.receipt.effect, "unknown")
                    self.assertIsNone(first.receipt.result_digest)
                    decisions.append(first)
                    self.assertEqual(dispatcher.snapshot(base).entry_count, 1)
                    if "redelivery" in row:
                        redelivery = self.invoke(dispatcher, self.request(row["redelivery"]))
                        self.assertEqual((redelivery.outcome, redelivery.reason), ("hold", "effect_unknown"))
                        decisions.append(redelivery)
                    replacement = row["replacement"]
                    self.assertGreater(replacement["tick"], self.limits["lease_end_tick"])
                    dispatcher.update_host(self.change_host(host, replacement))
                    delivered = self.invoke(dispatcher, self.request(replacement))
                    self.assertEqual((delivered.outcome, delivered.reason), ("hold", first.reason))
                    decisions.append(delivered)
                    outcome = "entry_then_replacement_held" if paused else "hold"
                    reason = delivered.reason
                after = dispatcher.snapshot(base)
                self.assertEqual(after.reserved_units, before.reserved_units)
                if variant == "admitted-paused-old-worker":
                    supplemental = self.check_current_replacement(dispatcher, host, row["replacement"], after)
                self.record(case, variant, row, expected, (outcome, reason, after.entry_count),
                            before, after, decisions, **supplemental)

    def check_current_replacement(self, dispatcher, original_host, replacement, after):
        eligible = self.request({**replacement, "grant": "grant-2", "reservation": "reservation-2"})
        current = self.change_host(original_host, replacement)
        action = tool_budget_action(self.definition, eligible, rate_revision=current.authority.rate.revision,
                                    units=self.defaults["synthetic_reservation_units"])
        authority = replace(current.authority, grants=(Grant(action, eligible.deadline),))
        pin = replace(current.context_pin, generation=eligible.generation)
        dispatcher.update_host(replace(current, authority=authority, context_pin=pin))
        self.assertIsNone(dispatcher.reserve_tool(eligible))
        before_eligible = dispatcher.snapshot(eligible)
        self.assertGreater(before_eligible.reserved_units, after.reserved_units)
        held = self.invoke(dispatcher, eligible)
        after_eligible = dispatcher.snapshot(eligible)
        self.assertEqual((held.outcome, held.reason), ("hold", "admitted_worker_effect_unresolved"))
        self.assertEqual(after_eligible, before_eligible)
        return {"approved_replacement_reservation": True, "eligible_replacement": self.summarized(held),
                "eligible_replacement_before": asdict(before_eligible),
                "eligible_replacement_after": asdict(after_eligible)}

    def test_E204_05_result_and_receipt(self):
        case = "E204-05"
        for variant, row, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                canaries = self.spec["canaries"] if "canary_fields" in row else {}
                result = {"value": canaries["raw_result"]} if canaries else row.get("fake_result")
                preferences = {} if result is None else {"fake_result": result}
                dispatcher, host, base = self.setup_case(preferences)
                before = dispatcher.snapshot(base)
                if canaries:
                    context = replace(host.context, provenance=encode({
                        "private_path": canaries["private_path"], "credential": canaries["credentials"],
                        "local_provenance": canaries["local_provenance"],
                    }))
                    pin = replace(host.context_pin, provenance_sha256=context.provenance_sha256)
                    host = replace(host, context=context, context_pin=pin)
                    dispatcher.update_host(host)
                first = self.invoke(dispatcher, base)
                decisions = [first]
                if row["stage"] == "invoke_then_reuse":
                    dispatcher.update_host(self.change_host(host, row["after"]))
                    second = self.invoke(dispatcher, self.request(row["after"]))
                    self.assertEqual(first.outcome, "executed")
                    self.assertEqual(second.receipt, first.receipt if row["return_data"] else None)
                    decisions.append(second)
                    outcome, reason = f"executed_then_{second.outcome}", second.reason
                elif "attempt_registration" in row:
                    second = self.invoke(dispatcher, self.request({"tool": row["attempt_registration"]}))
                    self.assertEqual(first.value, row["fake_result"]["value"])
                    self.assertEqual((second.outcome, second.reason), ("deny", "unregistered_tool"))
                    decisions.append(second)
                    outcome, reason = "executed_then_deny", "untrusted_text_no_authority"
                elif canaries:
                    # Revoke return permission before requesting the saved receipt.
                    self.assertEqual(first.value, canaries["raw_result"])
                    dispatcher.update_host(self.change_host(host, {"return_egress": False}))
                    second = self.invoke(dispatcher, replace(base, provider_call="call-2"))
                    bad_arg = self.invoke(dispatcher, self.request({"args": {"key": canaries["raw_argument"]}}))
                    self.assertEqual((bad_arg.outcome, bad_arg.reason), ("deny", "argument_schema_invalid"))
                    self.assertEqual((second.outcome, second.reason), ("hold", "receipt_reuse_not_authorized"))
                    decisions = [first, second, bad_arg]
                    outcome, reason = "executed_then_hold", "evidence_sanitized"
                else:
                    outcome, reason = first.outcome, first.reason
                relevant = decisions[1] if canaries else decisions[-1]
                if "attempt_registration" in row:
                    relevant = first
                self.assertEqual(relevant.value is not None, row["return_data"])
                if row.get("expected_effect_status"):
                    self.assertEqual(first.receipt.effect, row["expected_effect_status"])
                after = dispatcher.snapshot(base)
                supplemental = {}
                if row["stage"] == "invoke_then_reuse" and not row["return_data"]:
                    denied = self.change_host(host, row["after"]).return_scope.context
                    supplemental = {
                        "upstream_return_hold": denied.hold_reason,
                        "upstream_return_provenance_sha256": denied.provenance_sha256,
                        "fresh_different_recipient": self.check_fresh_recipient(row["after"]["recipient"]),
                    }
                self.record(case, variant, row, expected, (outcome, reason, after.entry_count),
                            before, after, decisions, **supplemental)

    def check_fresh_recipient(self, recipient):
        later = self.request({"recipient": recipient, "attempt": "attempt-2", "provider_call": "call-2",
                              "grant": "grant-2", "reservation": "reservation-2"})
        dispatcher, host, base = self.setup_case(additional=(later,))
        first = self.invoke(dispatcher, base)
        self.assertEqual(first.outcome, "executed")
        fresh_context = self.assemble_for(recipient, authorized_recipient=recipient)
        self.assertIsNone(fresh_context.hold_reason)
        self.assertEqual(fresh_context.payload, host.return_scope.context.payload)
        fresh_scope = ToolReturnScope(recipient, fresh_context)
        self.assertEqual(fresh_scope.pin[1:], host.return_scope.pin[1:])
        self.assertNotEqual(fresh_scope.pin[0], host.return_scope.pin[0])
        dispatcher.update_host(replace(host, return_scope=fresh_scope))
        before = dispatcher.snapshot(later)
        self.assertTrue(dispatcher._may_read(later))
        held = self.invoke(dispatcher, later)
        self.assertEqual((held.outcome, held.reason), ("hold", "receipt_reuse_not_authorized"))
        self.assertIsNone(held.value)
        self.assertIsNone(held.receipt)
        after = dispatcher.snapshot(later)
        self.assertEqual(after, before)
        return {"fresh_context_approved": True, "fresh_grant_current": True,
                "decision": self.summarized(held), "additional_entries": after.entry_count - before.entry_count}

    def provider_ledger(self, host, base):
        units = self.defaults["synthetic_provider_reservation_units"]
        tool = host.authority.grants[0].action
        action = replace(tool, model="fixture-provider-model", reservation_id="provider-reservation",
                         attempt_id="provider-attempt", input_bound=units)
        rate = Rate(tool.rate_revision, action.model, 1, 1)
        provider = OfflineBudget(replace(host.authority, grants=(Grant(action, base.deadline),), rate=rate))
        self.assertEqual(provider.reserve(action).units, units)
        return provider, action

    def test_E204_06_compatibility_and_accounting(self):
        case = "E204-06"
        map_reasons = {
            "headroom_unproved": "budget_unverified", "grant_missing_or_denied": "budget_denied",
            "budget_exhausted": "budget_stopped", "proved_no_entry": "no_tool_effect",
            "effect_unknown": "tool_effect_unknown", "bounded_typed_result": "authorized_tool_entry",
        }
        for variant, row, expected in self.spec["cases"][case]:
            with self.subTest(variant=variant):
                dispatcher, host, base = self.setup_case(row)
                provider, action = self.provider_ledger(host, base)
                before_provider = provider.snapshot(action)
                current = self.change_host(host, row)
                dispatcher.update_host(current)
                before = dispatcher.snapshot(base)
                decision = self.invoke(dispatcher, base, reject_before_entry="reject_at" in row,
                                       interruption="receipt_lost" if "interruption" in row else None)
                after = dispatcher.snapshot(base)
                after_provider = provider.snapshot(action)
                self.assertEqual(after_provider, before_provider)
                self.assertEqual(after_provider.fake_effects, 0)
                self.assertEqual(after_provider.work.reserved,
                                 row.get("provider_reservation_after", self.defaults["synthetic_provider_reservation_units"]))
                if "tool_reservations_consumed" in row:
                    self.assertEqual(after.admissions_consumed, row["tool_reservations_consumed"])
                if "expected_effect_status" in row:
                    effect = decision.receipt.effect if decision.receipt is not None else "none"
                    self.assertEqual(effect, row["expected_effect_status"])
                reason = map_reasons.get(decision.reason, decision.reason)
                self.record(case, variant, row, expected, (decision.outcome, reason, after.entry_count),
                            before, after, [decision], provider_before=asdict(before_provider.work),
                            provider_after=asdict(after_provider.work), provider_effects=after_provider.fake_effects,
                            upstream_hold_reason=current.context.hold_reason,
                            upstream_provenance_sha256=current.context.provenance_sha256)

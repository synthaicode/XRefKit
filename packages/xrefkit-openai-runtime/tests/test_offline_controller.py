"""Exercise the pinned #206 six groups through actual in-process admissions."""

from dataclasses import asdict, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from xrefkit_openai_runtime.contracts import AssignmentRef
from xrefkit_openai_runtime.offline_context import ContextAssembly
from xrefkit_openai_runtime.offline_controller import (
    Assessment, ControllerBinding, ControllerLimits, CurrentState, OfflineController,
    ProviderReceipt, RetryProof, ToolCall,
)
from xrefkit_openai_runtime.offline_evaluation import Criterion, Evaluation
from xrefkit_openai_runtime.offline_responses import UsageObservation


MANIFEST_SHA256 = "213082505029762e2e05458ad3f57f13f02e5204646373a2d9b642441c0d4960"
USAGE = UsageObservation(1, 0, 1)
ZERO = UsageObservation(0, 0, 0)
MISSING = UsageObservation()


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(content):
    return sha256(content).hexdigest()


class OfflineControllerCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = Path(__file__).parent / "fixtures" / "e206-design-fixtures-r2" / "manifest.json"
        cls.manifest = json.loads(fixture.read_bytes())
        if digest(encode(cls.manifest)) != MANIFEST_SHA256:
            raise ValueError("Frozen e206-design-fixtures-r2 differs from the approved Issue")
        cls.fixed = cls.manifest["fixed"]
        cls.limits = ControllerLimits(**cls.manifest["limits"])

    def setUp(self):
        self.setup_controller()

    def setup_controller(self, limits=None):
        fixed = self.fixed
        assignment = AssignmentRef(
            flow_id="flow-206", run_id="run-206", root_run_id="run-206",
            work_item_id=fixed["work_id"], node_id="node-206", route_id="offline-206-r2",
            route_revision=1, binding_sha256=digest(fixed["assignment_id"].encode()),
            owner_generation=1, execution_id="execution-206",
        )
        payload = encode({"instructions": [fixed["instructions"]], "supporting_data": []})
        provenance = encode({
            "version": 1, "assignment": assignment.model_dump(mode="json"),
            "payload_sha256": digest(payload), "hold_reason": None,
        })
        context = ContextAssembly(payload, provenance, None)
        self.binding = ControllerBinding(
            assignment, fixed["session_id"], "invoke-206", fixed["model"], fixed["instruction_revision"],
            fixed["recipient"], fixed["tool_name"], fixed["arguments"]["document_id"], "e206-rubric-r2",
            digest(fixed["criterion"].encode()), limits or self.limits, context, encode(fixed["tool_result"]),
        )
        self.current = CurrentState(assignment, context, fixed["instruction_revision"], fixed["recipient"])
        self.controller = OfflineController(self.binding)
        self.call = ToolCall(fixed["call_id"], fixed["tool_name"], encode(fixed["arguments"]))

    def step(self, tick, *, state=None, **kwargs):
        return self.controller.step(tick, state or self.current, **kwargs)

    def receipt(self, *, kind="completed", calls=(), usage=USAGE):
        entry = self.controller.provider_entries[-1].entry
        return ProviderReceipt(
            entry, f"response-{entry.attempt}", 1, kind, self.fixed["model"], usage, calls,
            self.fixed["criterion"].encode(),
        )

    def assessment(self, receipt, **changes):
        # Frozen synthetic #205 projection. #205's native evaluator and 57 conditions
        # are exercised separately by the package regression run.
        evaluation = Evaluation(
            criteria_revision=self.binding.criterion_revision,
            criteria_sha256=self.binding.criterion_sha256,
            criteria=(Criterion("aggregate", "pass", "all_applicable_criteria_met"),),
            aggregate="criteria_met", next_proposal="report_only", v1_assessment="review_required",
            api_outcome="completed", tool_outcome="executed" if receipt.entry.call_id else "not_applicable",
            tool_effect="observed" if receipt.entry.call_id else "none", entry_observed=True, usage=receipt.usage,
            retained_reviewers=("independent-fixture-reviewer",), review_state="reviewed",
            output_sha256=digest(receipt.output), approved_policy_sha256=digest(encode(self.fixed["review"])),
            source_findings=(),
        )
        return Assessment(receipt.entry, receipt.receipt_id, receipt.evidence_sha256, replace(evaluation, **changes))

    def final(self, tick):
        receipt = self.receipt()
        return self.step(tick, observation=receipt, assessment=self.assessment(receipt))

    def expect(self, result, disposition, provider, tool):
        self.assertEqual((result.disposition, result.provider_entries, result.tool_entries),
                         (disposition, provider, tool))

    def run_fixed(self, case):
        variants = [variant for variant in self.manifest["variants"] if variant["case_id"] == case]
        self.assertTrue(variants)
        for variant in variants:
            for duplicate in ((False, True) if variant["variant"] == "multiple-or-duplicate-tool-calls" else (False,)):
                with self.subTest(variant=variant["variant"], duplicate=duplicate):
                    self.setup_controller()
                    ticks = [record[0] for record in variant["ticks"]]
                    observed = self.execute_variant(variant["variant"], ticks, duplicate)
                    self.expect(observed, **{
                        "disposition": variant["expected"]["terminal"],
                        "provider": variant["expected"]["provider_entries"],
                        "tool": variant["expected"]["tool_entries"],
                    })
                    self.assertEqual(observed.execution_id, self.binding.assignment.execution_id)
                    self.assertEqual(observed.invocation_id, self.binding.invocation_id)
                    if os.environ.get("XREFKIT_E206_EVIDENCE") == "1":
                        print(json.dumps({
                            "case": case, "variant": variant["variant"], "duplicate_call": duplicate,
                            "fixture_sha256": MANIFEST_SHA256,
                            "expected": variant["expected"], "observed": asdict(observed) | {
                                "candidate": digest(observed.candidate) if observed.candidate else None,
                            },
                            "journal": [asdict(record) for record in self.controller.journal],
                        }))

    def execute_variant(self, variant, ticks, duplicate):
        if variant == "held-context":
            return self.step(ticks[0], start=True, state=replace(
                self.current, context=replace(self.current.context, hold_reason="held")))
        if variant == "required-intent-write-fault":
            return self.step(ticks[0], start=True, state=replace(self.current, intent_available=False))
        if variant == "stalled":
            self.step(ticks[0], no_progress=True)
            return self.step(ticks[1], no_progress=True, start=True)
        if variant == "simultaneous-signals":
            self.setup_controller(replace(self.limits, deadline_tick_exclusive=0))
            result = self.step(ticks[0], start=True, state=replace(
                self.current, cancelled=True, provider_allowed=False, headroom_proved=False))
            self.assertEqual(result.last_checkpoint.signals,
                             ("cancelled", "stop_authority", "stop_deadline", "hold_headroom"))
            return result

        self.step(ticks[0], start=True)
        if variant == "provider-only":
            return self.final(ticks[1])
        if variant == "multiple-or-duplicate-tool-calls":
            second = self.call if duplicate else replace(self.call, call_id="call-206-distinct")
            return self.step(ticks[1], observation=self.receipt(calls=(self.call, second)))
        if variant == "timeout":
            self.assertEqual(self.controller.status(wait_ended=True).disposition, "hold_reconciliation")
            result = self.step(ticks[1], timeout=True)
            self.assertEqual(len(result.outstanding), 1)
            return result
        if variant == "required-observation-write-fault":
            return self.step(ticks[1], observation=self.receipt(),
                             state=replace(self.current, observation_available=False))
        if variant == "cancel-then-matched-late":
            receipt = self.receipt()
            cancelled = self.step(ticks[1], state=replace(self.current, cancelled=True))
            self.assertEqual(len(cancelled.outstanding), 1)
            self.step(ticks[2], observation=receipt, start=True)
            duplicate_result = self.step(ticks[3], observation=receipt, start=True)
            self.assertFalse(duplicate_result.outstanding)
            self.assertEqual(duplicate_result.last_checkpoint.reason, "duplicate_receipt")
            return duplicate_result
        if variant == "matched-no-submit":
            receipt = replace(self.receipt(kind="no_submit", usage=MISSING), delay_ticks=2)
            proof = RetryProof(receipt.entry, receipt.receipt_id, receipt.revision, "no_submit")
            released = self.step(ticks[1], observation=receipt, retry_proof=proof)
            self.assertFalse(released.outstanding)
            self.step(ticks[2], start=True)
            self.assertNotEqual(self.controller.provider_entries[-1].entry.attempt, receipt.entry.attempt)
            self.assertNotEqual(self.controller.provider_entries[-1].entry.reservation, receipt.entry.reservation)
            return self.final(ticks[3])

        self.step(ticks[1], observation=self.receipt(calls=(self.call,)))
        if variant == "revoked-before-tool":
            return self.step(ticks[2], start=True, before_entry=lambda: replace(self.current, tool_allowed=False))
        with patch.dict(os.environ, {"OPENAI_API_KEY": "e206-synthetic-secret-marker"}):
            self.step(ticks[2], start=True)
        self.step(ticks[3], tool_observed=True)
        self.step(ticks[4], start=True)
        messages = [json.loads(packet.body) for packet in self.controller.provider_entries]
        self.assertEqual(len(messages), 2)
        for message in messages:
            self.assertEqual(message["instructions"], self.fixed["instructions"])
            self.assertIs(message["parallel_tool_calls"], self.fixed["parallel_tool_calls"])
        self.assertEqual(messages[1]["input"][-1], {
            "type": "function_call_output", "call_id": self.fixed["call_id"],
            "output": encode(self.fixed["tool_result"]).decode(),
        })
        self.assertEqual(messages[1]["previous_response_id"], "response-provider-1")
        self.assertNotIn("e206-synthetic-secret-marker", repr(self.controller.journal) + repr(messages))
        if variant == "tool-after-continuation":
            return self.step(ticks[5], observation=self.receipt(calls=(self.call,)))
        self.assertEqual(variant, "single-tool-success")
        return self.final(ticks[5])

    def test_e206_01_state_sequence(self):
        self.run_fixed("E206-01")

    def test_e206_02_arbitration(self):
        self.run_fixed("E206-02")

    def test_e206_03_retry(self):
        self.run_fixed("E206-03")

    def test_e206_04_stop(self):
        self.run_fixed("E206-04")

    def test_e206_05_cancellation_and_late(self):
        self.run_fixed("E206-05")

    def test_e206_06_journal_failure(self):
        self.run_fixed("E206-06")

    def test_binding_egress_and_completed_evidence_are_rechecked(self):
        for change, reason in (
            ({"egress_allowed": False}, "stop_authority"),
            ({"recipient": "unapproved"}, "stop_authority"),
            ({"instruction_revision": "other"}, "hold_context"),
            ({"capture_available": False}, "hold_context"),
        ):
            with self.subTest(change=change):
                self.setup_controller()
                self.step(0, start=True)
                self.step(1, observation=self.receipt(calls=(self.call,)))
                self.step(2, start=True)
                self.step(3, tool_observed=True)
                stopped = self.step(4, start=True, before_entry=lambda: replace(self.current, **change))
                self.expect(stopped, reason, 1, 1)
                self.assertFalse(stopped.outstanding)

    def test_model_review_and_receipt_mismatches_block_candidate(self):
        for mode, reason in (
            ("missing-model", "hold_model"), ("wrong-model", "hold_model"),
            ("missing-review", "hold_evaluation"), ("other-policy", "hold_evaluation"),
            ("refusal", "hold_outcome"), ("wrong-session", "hold_reconciliation"),
            ("wrong-call", "hold_reconciliation"),
        ):
            with self.subTest(mode=mode):
                self.setup_controller()
                self.step(0, start=True)
                receipt = self.receipt()
                if mode in ("missing-model", "wrong-model"):
                    receipt = replace(receipt, observed_model=None if mode == "missing-model" else "unplanned")
                elif mode == "refusal":
                    receipt = replace(receipt, kind="refused")
                elif mode in ("wrong-session", "wrong-call"):
                    entry = (replace(receipt.entry, session_id="other") if mode == "wrong-session"
                             else replace(receipt.entry, call_id="wrong"))
                    receipt = replace(receipt, entry=entry)
                assessment = self.assessment(
                    receipt,
                    **({"retained_reviewers": (), "review_state": "pending"} if mode == "missing-review"
                       else {"criteria_sha256": digest(b"other")} if mode == "other-policy" else {}),
                )
                self.expect(self.step(1, observation=receipt, assessment=assessment), reason, 1, 0)

    def test_retry_proof_delay_usage_and_cap(self):
        for kind, evidence, usage, delay, expected in (
            ("safe_rejection", True, MISSING, 1, "pending"),
            ("safe_rejection", False, MISSING, 0, "hold_reconciliation"),
            ("safe_rejection", True, ZERO, 0, "hold_reconciliation"),
            ("no_submit", True, MISSING, 3, "stop_retry_limit"),
        ):
            with self.subTest(kind=kind, evidence=evidence, usage=usage, delay=delay):
                self.setup_controller()
                self.step(0, start=True)
                receipt = replace(self.receipt(kind=kind, usage=usage), delay_ticks=delay)
                proof = RetryProof(receipt.entry, receipt.receipt_id, 1, kind) if evidence else None
                self.expect(self.step(1, observation=receipt, retry_proof=proof), expected, 1, 0)
                if expected == "pending":
                    self.step(2, start=True)
                    retry = self.receipt(kind=kind, usage=MISSING)
                    retry_proof = RetryProof(retry.entry, retry.receipt_id, 1, kind)
                    self.expect(self.step(3, observation=retry, retry_proof=retry_proof),
                                "stop_retry_limit", 2, 0)

    def test_no_submit_cannot_release_prior_explicit_zero_or_usage(self):
        for usage in (ZERO, USAGE):
            with self.subTest(usage=usage):
                self.setup_controller()
                self.step(0, start=True)
                first = self.receipt(kind="unknown", usage=usage)
                self.step(1, observation=first)
                later = replace(first, revision=2, kind="no_submit", usage=MISSING)
                proof = RetryProof(later.entry, later.receipt_id, 2, "no_submit")
                outcome = self.step(2, observation=later, retry_proof=proof, start=True)
                self.expect(outcome, "hold_reconciliation", 1, 0)
                self.assertEqual(outcome.outstanding, (first.entry,))
                self.assertIn(outcome.last_checkpoint.reason,
                              {"usage_conflicts_with_prior_observation", "conflicting_no_submit"})

    def test_deadline_counts_budget_and_stale_assignment(self):
        for tick, limits, changes, expected in (
            (8, self.limits, {}, "stop_deadline"),
            (0, replace(self.limits, max_provider_entries=0), {}, "stop_attempt_limit"),
            (0, replace(self.limits, synthetic_budget_units=0), {}, "stop_budget"),
            (0, self.limits, {"headroom_proved": False}, "hold_headroom"),
            (0, self.limits, {"guard_proved": False}, "stop_authority"),
            (0, self.limits, {"assignment": self.binding.assignment.model_copy(update={"owner_generation": 2})},
             "stop_authority"),
        ):
            with self.subTest(expected=expected):
                self.setup_controller(limits)
                self.expect(self.step(tick, start=True, state=replace(self.current, **changes)), expected, 0, 0)

    def test_cancel_before_tool_and_log_gap_after_tool(self):
        for before in (True, False):
            with self.subTest(before=before):
                self.setup_controller()
                self.step(0, start=True)
                self.step(1, observation=self.receipt(calls=(self.call,)))
                if before:
                    blocked = self.step(2, start=True, before_entry=lambda: replace(self.current, cancelled=True))
                    self.expect(blocked, "cancelled", 1, 0)
                else:
                    self.step(2, start=True)
                    blocked = self.step(3, tool_observed=True, state=replace(self.current, capture_available=False))
                    self.expect(blocked, "hold_reconciliation", 1, 1)
                    self.assertEqual(blocked.outstanding[0].call_id, self.fixed["call_id"])

    def test_tool_proposal_cannot_open_a_runner_before_provider(self):
        self.expect(self.step(0, tool_observed=True, start=True), "hold_reconciliation", 0, 0)

    def test_cancelled_tool_receipt_is_reconciled_without_a_continuation(self):
        self.step(0, start=True)
        self.step(1, observation=self.receipt(calls=(self.call,)))
        self.step(2, start=True)
        self.expect(self.step(3, state=replace(self.current, cancelled=True)), "cancelled", 1, 1)
        self.expect(self.step(4, tool_observed=True, start=True), "cancelled_with_reconciliation_evidence", 1, 1)
        duplicate = self.step(5, tool_observed=True, start=True)
        self.expect(duplicate, "cancelled_with_reconciliation_evidence", 1, 1)
        self.assertEqual(duplicate.last_checkpoint.reason, "duplicate_tool_receipt")
        self.assertFalse(duplicate.outstanding)

    def test_delayed_retry_does_not_open_a_second_entry_early(self):
        self.step(0, start=True)
        receipt = replace(self.receipt(kind="no_submit", usage=MISSING), delay_ticks=2)
        proof = RetryProof(receipt.entry, receipt.receipt_id, receipt.revision, "no_submit")
        self.step(1, observation=receipt, retry_proof=proof)
        self.expect(self.step(2, start=True), "pending", 1, 0)
        self.expect(self.step(3, start=True), "pending", 2, 0)

    def test_assessment_is_bound_to_exact_observation(self):
        self.step(0, start=True)
        receipt = self.receipt()
        assessment = self.assessment(receipt)
        amended = replace(receipt, revision=2)
        self.expect(self.step(1, observation=amended, assessment=assessment), "hold_evaluation", 1, 0)

"""Exercise the pinned #206 six groups through actual in-process admissions."""

from dataclasses import asdict, replace
from copy import deepcopy
from hashlib import sha256
from itertools import count
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from xrefkit_openai_runtime.contracts import AssignmentRef, BudgetLimits, ExecutionEvent, ExecutionRequest, ExecutionResult
from xrefkit_openai_runtime.offline_context import ContextAssembly
from xrefkit_openai_runtime.offline_controller import (
    Assessment, ControllerBinding, ControllerLimits, CriterionEvidence, CurrentState, OfflineController, OfflineJournal,
    ProviderReceipt, RetryProof, ToolCall,
)
from xrefkit_openai_runtime.offline_dispatch import OfflineToolDispatch, ToolDecision, _FakeRunner
from xrefkit_openai_runtime.offline_evaluation import (
    EvaluationInputs, EvaluationPolicy, ReviewAuthority, RevisionLinks, SemanticReview,
    api_observation_digest, effective_rules_digest, evaluation_policy_digest, evidence_digest,
    tool_observation_digest, trace_pins,
)
from xrefkit_openai_runtime.offline_responses import (
    AttemptDiagnostics, FakeResponse, UsageObservation, normalize_controller_response,
)


MANIFEST_SHA256 = "213082505029762e2e05458ad3f57f13f02e5204646373a2d9b642441c0d4960"
USAGE = UsageObservation(1, 0, 1)
ZERO = UsageObservation(0, 0, 0)
MISSING = UsageObservation()
RUNS = count(1)


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(content):
    return sha256(content).hexdigest()


class BrokenStage(OfflineJournal):
    def __init__(self, failed, operation=None):
        super().__init__()
        self.failed = failed
        self.operation = operation

    def append(self, event):
        if event.stage == self.failed and (
            self.operation is None or event.entry is not None and event.entry.operation == self.operation
        ):
            self.failed = None
            raise OSError("synthetic append failure")
        super().append(event)


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
        run = f"run-206-{next(RUNS)}"
        assignment = AssignmentRef(
            flow_id="flow-206", run_id=run, root_run_id=run,
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
        self.rubric = encode({"revision": "e206-rubric-r2", "criterion": fixed["criterion"]})
        self.baseline_criterion_sha256 = digest(encode({
            "criterion": fixed["criterion"], "reference": "initial-verified-evidence",
        }))
        reviewer = ReviewAuthority("independent-fixture-reviewer", "independent-fixture-context")
        self.binding = ControllerBinding(
            assignment, fixed["session_id"], "invoke-206", fixed["model"], fixed["instruction_revision"],
            fixed["recipient"], fixed["tool_name"], fixed["arguments"]["document_id"], "e206-rubric-r2",
            digest(self.rubric), reviewer, limits or self.limits, context, encode(fixed["tool_result"]),
            frozenset({self.baseline_criterion_sha256}),
        )
        self.current = CurrentState(assignment, context, fixed["instruction_revision"], fixed["recipient"],
                                    fixed["session_id"], self.binding.invocation_id)
        self.controller = OfflineController(self.binding)
        self.call = ToolCall(fixed["call_id"], fixed["tool_name"], encode(fixed["arguments"]))

    def criterion_evidence(self, observation_sha256):
        binding = self.binding
        return CriterionEvidence(
            binding.assignment, binding.session_id, binding.invocation_id,
            binding.criterion_sha256, observation_sha256,
        )

    def step(self, tick, *, state=None, **kwargs):
        return self.controller.step(tick, state or self.current, **kwargs)

    def receipt(self, *, kind="completed", calls=(), usage=USAGE):
        entry = self.controller.provider_entries[-1].entry
        response_id = f"response-{entry.attempt}"
        output = encode({"objective": self.fixed["criterion"]})
        wire = None
        if kind in ("completed", "refused", "failed", "safe_rejection"):
            items = [{
                "type": "function_call", "id": f"result-{index}", "name": call.name,
                "call_id": call.call_id, "arguments": call.arguments.decode(),
            } for index, call in enumerate(calls)] or [{
                "type": "refusal" if kind == "refused" else "text", "id": "text-1", "text": output.decode(),
            }]
            body = {
                "id": response_id, "http": 200, "status": "failed" if kind == "failed" else "completed",
                "model": self.fixed["model"], "output": items,
                "usage": {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens,
                          "total_tokens": usage.total_tokens},
            }
            if kind == "safe_rejection":
                body.update(http=429, code="rate_limit_exceeded", submission="confirmed_rejected")
            wire = FakeResponse(f"request-{entry.attempt}", body)
        return ProviderReceipt(
            entry, response_id, 1, kind, usage if wire is None else MISSING, wire_response=wire,
        )

    def proof(self, receipt):
        return RetryProof(
            receipt.entry, receipt.receipt_id, receipt.revision, receipt.kind,
            digest(self.controller.provider_entries[-1].body), receipt.evidence_sha256,
            "independent-fixture-no-effect-check",
        )

    def retries(self, tick, receipt, proof):
        return self.step(tick, observation=receipt, retry_proof=proof,
                         state=replace(self.current, retry_evidence=(proof,) if proof else ()))

    def assessment(self, receipt, *, review=True, other_reviewer=False):
        entry = receipt.entry
        binding = self.binding
        assignment = binding.assignment
        request_digest = digest(self.controller.provider_entries[-1].body)
        output = encode({"objective": self.fixed["criterion"]})
        diagnostics = AttemptDiagnostics(
            assignment.run_id, assignment.work_item_id, assignment.binding_sha256,
            entry.attempt, entry.reservation, request_digest,
        )
        api = normalize_controller_response(
            receipt.wire_response, diagnostics, model=binding.selected_model,
            tool_name=binding.tool_name, expected_response_id=receipt.receipt_id,
        )
        evidence = dict(
            version=1, assignment=assignment, attempt_id=entry.attempt,
            operation_id=entry.operation, call_id=entry.call_id or "no-tool-call",
        )
        request = ExecutionRequest(
            version=1, assignment=assignment, criteria_sha256=binding.criterion_sha256,
            reservation_ref=entry.reservation, authorization_ref=entry.admission,
            budget=BudgetLimits(max_attempts=3, max_input_tokens=1, max_output_tokens=1, deadline_ms=8),
            cancelled=False, selected_model=binding.selected_model,
        )
        events = tuple(ExecutionEvent(sequence=i, kind=kind, **evidence)
                       for i, kind in enumerate(("admitted", "dispatched", "receipt"), 1))
        result = ExecutionResult(
            **evidence, outcome="allowed", transport_completed=True,
            observed_model=binding.selected_model, evidence_ref=receipt.evidence_sha256,
        )
        pins = trace_pins(request, events, result)
        links = RevisionLinks(
            "e206-request-r2", "e206-result-r2", "e206-tool-r2", binding.criterion_revision,
            binding.criterion_sha256, "e206-evidence-r2", (entry.attempt, entry.operation, evidence["call_id"]),
        )
        continued = entry.operation == "continuation"
        tool = self.controller._tool_result if continued else ToolDecision("hold", "tool_not_requested")
        tool_return = binding.synthetic_tool_result if continued else b""
        tool_effect = "observed" if continued else "none"
        reviewer = ReviewAuthority("wrong-reviewer", "wrong-context") if other_reviewer else binding.reviewer
        reviews = (SemanticReview(
            reviewer.reviewer_id, "independent_semantic_fixture", True, reviewer.context,
            "producer-context", links, digest(output), "pass", (result.evidence_ref,),
            self.fixed["review"], (pins[2],),
        ),) if review else ()
        inputs = EvaluationInputs(
            request, events, result, links, api, tool, output, tool_return,
            recorded_tool_effect=tool_effect, reviews=reviews,
        )
        policy = EvaluationPolicy(
            assignment, links, request_digest, api_observation_digest(api),
            tool_observation_digest(tool, tool_effect), digest(output), pins, self.rubric,
            "", entry.reservation, (), None, tuple(evidence_digest(item) for item in reviews),
            binding.selected_model, None, 128, "producer", "producer-context", (binding.reviewer,), frozenset(),
            controller_profile="continuation" if continued else "provider_only",
            controller_tool_correlation=tool.receipt.correlation if continued else None,
        )
        policy = replace(policy, approved_rules_sha256=effective_rules_digest(policy))
        return Assessment(entry, receipt.receipt_id, receipt.evidence_sha256, policy, inputs)

    def final(self, tick):
        receipt = self.receipt()
        assessment = self.assessment(receipt)
        state = replace(self.current, approved_evaluation_sha256=evaluation_policy_digest(assessment.policy))
        return self.step(tick, state=state, observation=receipt, assessment=assessment)

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
            same_evidence = self.criterion_evidence(self.baseline_criterion_sha256)
            state = replace(self.current, verified_criterion_evidence=(same_evidence,))
            self.step(ticks[0], state=state, evaluate_only=True)
            outcome = self.step(ticks[1], state=state, evaluate_only=True)
            repeated = [event for event in self.controller.journal
                        if event.reason == "unchanged_verified_criterion_evidence"]
            self.assertEqual([(event.tick, event.evidence_ref) for event in repeated],
                             [(tick, same_evidence.observation_sha256) for tick in ticks])
            return outcome
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
            self.assertEqual(self.controller.status().disposition, "pending")
            result = self.step(ticks[1], timeout=True)
            self.assertEqual(len(result.outstanding), 1)
            self.assertEqual(result.last_checkpoint.tick, ticks[1])
            self.assertEqual(result.last_checkpoint.signals, ("hold_reconciliation",))
            self.assertFalse(any("host_wait_expired" in event.signals for event in self.controller.journal))
            self.assertTrue(any(event.tick == ticks[1] and event.reason == "transport_timeout_without_receipt"
                                for event in self.controller.journal))
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
            proof = self.proof(receipt)
            released = self.retries(ticks[1], receipt, proof)
            self.assertFalse(released.outstanding)
            self.step(ticks[2], start=True)
            self.assertNotEqual(self.controller.provider_entries[-1].entry.attempt, receipt.entry.attempt)
            self.assertNotEqual(self.controller.provider_entries[-1].entry.reservation, receipt.entry.reservation)
            return self.final(ticks[3])

        self.step(ticks[1], observation=self.receipt(calls=(self.call,)))
        if variant == "revoked-before-tool":
            outcome = self.step(ticks[2], start=True, before_entry=lambda: replace(self.current, tool_allowed=False))
            aborted = next(event for event in self.controller.journal if event.stage == "not_sent")
            self.assertEqual(
                (aborted.ledger_before.reservation_state, aborted.ledger_after.reservation_state),
                ("reserved", "released"),
            )
            return outcome
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
            ("wrong-reviewer", "hold_evaluation"),
            ("refusal", "hold_outcome"), ("wrong-session", "hold_reconciliation"),
            ("wrong-call", "hold_reconciliation"),
        ):
            with self.subTest(mode=mode):
                self.setup_controller()
                self.step(0, start=True)
                receipt = self.receipt()
                if mode in ("missing-model", "wrong-model"):
                    wire = receipt.wire_response
                    model = None if mode == "missing-model" else "unplanned"
                    receipt = replace(receipt, wire_response=replace(wire, body=wire.body | {"model": model}))
                elif mode == "refusal":
                    receipt = self.receipt(kind="refused")
                elif mode in ("wrong-session", "wrong-call"):
                    entry = (replace(receipt.entry, session_id="other") if mode == "wrong-session"
                             else replace(receipt.entry, call_id="wrong"))
                    receipt = replace(receipt, entry=entry)
                assessment = self.assessment(receipt, review=mode != "missing-review",
                                             other_reviewer=mode == "wrong-reviewer")
                pin = digest(b"other-policy") if mode == "other-policy" else evaluation_policy_digest(assessment.policy)
                state = replace(self.current, approved_evaluation_sha256=pin)
                self.expect(self.step(1, observation=receipt, assessment=assessment, state=state), reason, 1, 0)

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
                proof = self.proof(receipt) if evidence else None
                self.expect(self.retries(1, receipt, proof), expected, 1, 0)
                if expected == "pending":
                    self.step(2, start=True)
                    retry = self.receipt(kind=kind, usage=MISSING)
                    self.expect(self.retries(3, retry, self.proof(retry)),
                                "stop_retry_limit", 2, 0)

    def test_no_submit_cannot_release_prior_explicit_zero_or_usage(self):
        for usage in (ZERO, USAGE):
            with self.subTest(usage=usage):
                self.setup_controller()
                self.step(0, start=True)
                first = self.receipt(kind="unknown", usage=usage)
                self.step(1, observation=first)
                later = replace(first, revision=2, kind="no_submit", usage_if_wire_unavailable=MISSING)
                outcome = self.retries(2, later, self.proof(later))
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
        self.retries(1, receipt, self.proof(receipt))
        self.expect(self.step(2, start=True), "pending", 1, 0)
        self.expect(self.step(3, start=True), "pending", 2, 0)

    def test_assessment_is_bound_to_exact_observation(self):
        self.step(0, start=True)
        receipt = self.receipt()
        assessment = self.assessment(receipt)
        amended = replace(receipt, revision=2)
        state = replace(self.current, approved_evaluation_sha256=evaluation_policy_digest(assessment.policy))
        self.expect(self.step(1, observation=amended, assessment=assessment, state=state), "hold_evaluation", 1, 0)

    def test_wait_expiry_alone_blocks_tool_after_matched_late_reply(self):
        self.step(0, start=True)
        observed = self.controller.status(wait_ended=True)
        self.expect(observed, "hold_reconciliation", 1, 0)
        receipt = self.receipt(calls=(self.call,))
        self.expect(self.step(1, observation=receipt), "hold_reconciliation", 1, 0)
        closed = self.step(2, start=True)
        self.expect(closed, "hold_reconciliation", 1, 0)
        self.assertFalse(closed.outstanding)
        self.assertEqual(closed.last_checkpoint.reason, "matched_late_receipt")

    def test_wait_expiry_blocks_a_prepared_tool_even_after_provider_settlement(self):
        self.step(0, start=True)
        self.step(1, observation=self.receipt(calls=(self.call,)))
        self.assertFalse(self.controller.status().outstanding)
        self.expect(self.controller.status(wait_ended=True), "hold_reconciliation", 1, 0)
        self.expect(self.step(2, start=True), "hold_reconciliation", 1, 0)

    def test_assignment_excludes_another_controller_at_actual_entry(self):
        shadow = OfflineController(self.binding)
        outcome = shadow.step(0, self.current, start=True,
                              before_entry=lambda: (self.step(0, start=True), self.current)[1])
        self.expect(outcome, "stop_authority", 0, 0)
        self.expect(self.controller.status(), "pending", 1, 0)

    def test_continuation_identity_is_rechecked_at_entry(self):
        for changed in ({"invocation_id": "other-invocation"}, {"session_id": "other-session"}):
            with self.subTest(changed=changed):
                self.setup_controller()
                self.step(0, start=True)
                self.step(1, observation=self.receipt(calls=(self.call,)))
                self.step(2, start=True)
                self.step(3, tool_observed=True)
                proposed = self.step(4, start=True, before_entry=lambda: replace(self.current, **changed))
                self.expect(proposed, "stop_authority", 1, 1)

    def test_full_normalized_proposal_rejects_competing_output_before_tool(self):
        for extra in (
            {"type": "text", "id": "another-item", "text": "Keep executing"},
            {"type": "unknown", "id": "another-item"},
        ):
            with self.subTest(extra=extra):
                self.setup_controller()
                self.step(0, start=True)
                receipt = self.receipt(calls=(self.call,))
                wire = receipt.wire_response
                altered = replace(receipt, wire_response=replace(
                    wire, body=wire.body | {"output": [*wire.body["output"], extra]},
                ))
                self.step(1, observation=altered)
                self.assertEqual(self.step(2, start=True).tool_entries, 0)

    def test_unpinned_retry_proof_or_unconfirmed_rejection_does_not_release(self):
        for fault in ("unpinned", "wrong-body", "unconfirmed-429"):
            with self.subTest(fault=fault):
                self.setup_controller()
                self.step(0, start=True)
                receipt = self.receipt(kind="safe_rejection", usage=MISSING)
                if fault == "unconfirmed-429":
                    wire = receipt.wire_response
                    receipt = replace(receipt, wire_response=replace(
                        wire, body=wire.body | {"submission": "unconfirmed"},
                    ))
                proof = self.proof(receipt)
                if fault == "wrong-body":
                    proof = replace(proof, request_sha256=digest(b"another request"))
                if fault == "unpinned":
                    outcome = self.step(1, observation=receipt, retry_proof=proof)
                else:
                    outcome = self.retries(1, receipt, proof)
                self.expect(outcome, "hold_reconciliation", 1, 0)
                self.assertEqual(outcome.outstanding, (receipt.entry,))

    def test_late_receipt_is_processed_after_known_prohibiting_stop(self):
        for tick, changes, reason in (
            (1, {"invocation_id": "stale-caller"}, "stop_authority"),
            (1, {"headroom_proved": False}, "hold_headroom"),
            (8, {}, "stop_deadline"),
        ):
            with self.subTest(reason=reason):
                self.setup_controller()
                self.step(0, start=True)
                receipt = self.receipt()
                blocked = self.step(tick, state=replace(self.current, **changes))
                self.expect(blocked, reason, 1, 0)
                self.assertEqual(blocked.outstanding, (receipt.entry,))
                reconciled = self.step(tick + 1, observation=receipt, start=True)
                self.expect(reconciled, reason, 1, 0)
                self.assertFalse(reconciled.outstanding)

    def test_cancellation_acknowledgement_does_not_settle_remote_result(self):
        self.step(0, start=True)
        requested = self.step(1, state=replace(self.current, cancelled=True))
        self.assertTrue(requested.cancellation_requested)
        self.assertFalse(requested.cancellation_acknowledged)
        acknowledged = self.step(2, state=replace(self.current, cancellation_acknowledged=True))
        self.assertTrue(acknowledged.cancellation_acknowledged)
        self.assertEqual(requested.outstanding, acknowledged.outstanding)
        late = self.step(3, observation=self.receipt())
        self.expect(late, "cancelled_with_reconciliation_evidence", 1, 0)
        self.assertFalse(late.outstanding)

    def test_budget_precedes_no_progress_at_the_same_gate(self):
        self.setup_controller(replace(self.limits, synthetic_budget_units=0,
                                      max_consecutive_no_progress_decision_ticks=1))
        outcome = self.step(0, evaluate_only=True)
        self.expect(outcome, "stop_budget", 0, 0)
        self.assertEqual(outcome.last_checkpoint.signals, ("stop_budget", "stop_no_progress"))

    def test_required_writer_faults_hold_at_the_real_append_boundary(self):
        for stage in ("prepared", "entry", "observed", "observation"):
            with self.subTest(stage=stage):
                self.setup_controller()
                self.controller = OfflineController(self.binding, journal=BrokenStage(stage))
                status = self.step(0, start=True)
                if stage == "prepared":
                    self.expect(status, "hold_journal", 0, 0)
                    aborted = next(event for event in self.controller.journal if event.stage == "not_sent")
                    self.assertEqual(aborted.reason, "intent_checkpoint_unavailable")
                    self.assertEqual(
                        (aborted.ledger_before.reservation_state, aborted.ledger_after.reservation_state),
                        ("reserved", "released"),
                    )
                else:
                    receipt = self.receipt()
                    if stage in ("observed", "observation"):
                        status = self.step(1, observation=receipt)
                    self.expect(status, "hold_reconciliation", 1, 0)
                    self.assertEqual(status.outstanding, (receipt.entry,))
                    if stage == "observation":
                        gap = next(event for event in self.controller.journal
                                   if event.reason == "observation_write_failed")
                        self.assertEqual(gap.ledger_before, gap.ledger_after)
                        self.assertEqual(gap.ledger_after.reservation_state, "reserved")
                    status = self.step(2, observation=receipt)
                    self.assertFalse(status.outstanding)
                    if stage == "observation":
                        self.assertEqual(status.last_checkpoint.reason, "matched_late_receipt")
                self.assertIn(f"{stage}_write_failed", [event.reason for event in self.controller.journal])

    def test_tool_settlement_checkpoint_failure_preserves_ledger_and_allows_redelivery(self):
        self.controller = OfflineController(self.binding, journal=BrokenStage("observation", "tool"))
        self.step(0, start=True)
        self.step(1, observation=self.receipt(calls=(self.call,)))
        self.step(2, start=True)
        pending = self.step(3, tool_observed=True)
        self.expect(pending, "hold_reconciliation", 1, 1)
        original = pending.outstanding[0]
        self.assertEqual(original.operation, "tool")
        failure = next(event for event in self.controller.journal if event.reason == "observation_write_failed")
        self.assertEqual(failure.ledger_before, failure.ledger_after)
        self.assertEqual(failure.ledger_before.reservation_state, "reserved")
        matched = self.step(4, tool_observed=True, start=True)
        self.expect(matched, "hold_reconciliation", 1, 1)
        self.assertFalse(matched.outstanding)
        self.assertEqual(matched.last_checkpoint.reason, "matched_late_tool_receipt")
        settled = next(event for event in self.controller.journal
                       if event.stage == "observation" and event.entry == original)
        self.assertEqual((settled.ledger_before.work.reserved, settled.ledger_after.work.reserved), (1, 0))
        self.assertEqual((settled.ledger_before.work.debit, settled.ledger_after.work.debit), (1, 2))
        self.assertEqual(settled.ledger_after.observation_ticks, (4,))

    def test_retry_requires_its_checkpoint_and_preserves_progress_count(self):
        for failed_write, terminal in ((True, "hold_reconciliation"), (False, "stop_no_progress")):
            with self.subTest(failed_write=failed_write):
                self.setup_controller()
                if failed_write:
                    self.controller = OfflineController(self.binding, journal=BrokenStage("retry"))
                self.step(0, start=True)
                self.step(1, evaluate_only=True)
                receipt = replace(self.receipt(kind="no_submit", usage=MISSING), delay_ticks=2)
                self.retries(2, receipt, self.proof(receipt))
                stopped = self.step(3, evaluate_only=True)
                self.expect(stopped, terminal, 1, 0)
                retry = self.step(4, start=True)
                self.expect(retry, terminal, 1, 0)
                self.assertFalse(retry.outstanding)
                if failed_write:
                    self.assertIn("retry_write_failed", [event.reason for event in self.controller.journal])

    def test_candidate_at_provider_cap_with_start_signal_still_evaluates(self):
        self.setup_controller(replace(self.limits, max_provider_entries=1))
        self.step(0, start=True)
        receipt = self.receipt()
        assessment = self.assessment(receipt)
        state = replace(self.current, approved_evaluation_sha256=evaluation_policy_digest(assessment.policy))
        result = self.step(1, state=state, start=True, observation=receipt, assessment=assessment)
        self.expect(result, "candidate", 1, 0)
        self.assertIn("criteria_met", [event.reason for event in self.controller.journal])

    def test_wrong_call_on_continuation_cannot_claim_or_settle_its_reservation(self):
        self.step(0, start=True)
        self.step(1, observation=self.receipt(calls=(self.call,)))
        self.step(2, start=True)
        self.step(3, tool_observed=True)
        self.step(4, start=True)
        exact = self.receipt()
        wrong = replace(exact, entry=replace(exact.entry, call_id="wrong-continuation-call"))
        held = self.step(5, observation=wrong, start=True)
        self.expect(held, "hold_reconciliation", 2, 1)
        self.assertEqual(held.outstanding, (exact.entry,))
        matched = self.step(6, observation=exact, start=True)
        self.expect(matched, "hold_reconciliation", 2, 1)
        self.assertFalse(matched.outstanding)

    def test_unique_current_criterion_evidence_resets_count_once(self):
        self.step(0, evaluate_only=True)
        same = self.criterion_evidence(digest(b"new trusted evidence"))
        state = replace(self.current, verified_criterion_evidence=(same,))
        self.expect(self.step(1, state=state, evaluate_only=True), "pending", 0, 0)
        self.expect(self.step(2, state=state, evaluate_only=True), "pending", 0, 0)
        self.expect(self.step(3, state=state, evaluate_only=True), "stop_no_progress", 0, 0)

    def test_journal_records_binding_and_grant_with_reservation_deltas(self):
        self.step(0, start=True)
        self.final(1)
        journal = self.controller.journal
        self.assertTrue(all(event.assignment.binding_sha256 == self.binding.assignment.binding_sha256
                            and event.assignment.work_item_id == self.binding.assignment.work_item_id
                            and event.session_id == self.binding.session_id
                            and event.invocation_id == self.binding.invocation_id for event in journal))
        prepared = next(event for event in journal if event.stage == "prepared")
        self.assertIsNone(prepared.ledger_before.grant)
        self.assertEqual(prepared.ledger_after.grant, prepared.entry.admission)
        self.assertEqual((prepared.ledger_before.work.reserved, prepared.ledger_after.work.reserved), (0, 1))
        settled = next(event for event in journal if event.stage == "observation")
        self.assertEqual(settled.previous_stage, "observed")
        self.assertEqual((settled.ledger_before.work.reserved, settled.ledger_after.work.reserved), (1, 0))
        self.assertEqual((settled.ledger_before.work.debit, settled.ledger_after.work.debit), (0, 1))
        self.assertEqual(settled.ledger_after.observation_ticks, (1,))

    def test_writer_cannot_reenter_controller_and_commit_a_settlement(self):
        class ReenteringWriter(OfflineJournal):
            def append(writer, event):
                if event.stage == "observation":
                    self.controller.status(wait_ended=True)
                super().append(event)

        self.controller = OfflineController(self.binding, journal=ReenteringWriter())
        self.step(0, start=True)
        receipt = self.receipt()
        stopped = self.step(1, observation=receipt)
        self.expect(stopped, "hold_reconciliation", 1, 0)
        self.assertEqual(stopped.outstanding, (receipt.entry,))
        self.assertEqual(stopped.last_checkpoint.ledger_after.work.reserved, 1)

    def test_consumed_initial_receipt_revision_cannot_bypass_tool_continuation(self):
        self.step(0, start=True)
        initial = self.receipt(calls=(self.call,))
        self.step(1, observation=initial)
        self.step(2, start=True)
        self.step(3, tool_observed=True)
        revised = replace(self.receipt(), revision=2)
        assessment = self.assessment(revised)
        state = replace(self.current, approved_evaluation_sha256=evaluation_policy_digest(assessment.policy))
        held = self.step(4, state=state, observation=revised, assessment=assessment, start=True)
        self.expect(held, "hold_reconciliation", 1, 1)
        self.assertIsNone(held.candidate)
        revision = next(event for event in self.controller.journal
                        if event.reason == "consumed_provider_receipt_revision")
        self.assertEqual(revision.evidence_ref, revised.evidence_sha256)
        self.assertEqual(revision.ledger_before, revision.ledger_after)
        self.assertEqual(revision.ledger_after.reservation_state, "settled")
        repeated = self.step(5, observation=initial, start=True)
        self.expect(repeated, "hold_reconciliation", 1, 1)
        self.assertEqual(repeated.last_checkpoint.reason, "duplicate_receipt")

    def test_wire_body_snapshot_is_immune_to_caller_mutation_during_append(self):
        class MutatingWriter(OfflineJournal):
            receipt = None

            def append(writer, event):
                if event.stage == "observed" and writer.receipt is not None:
                    writer.receipt.wire_response.body["output"].clear()
                    writer.receipt = None
                super().append(event)

        writer = MutatingWriter()
        self.controller = OfflineController(self.binding, journal=writer)
        self.step(0, start=True)
        original = self.receipt(calls=(self.call,))
        redelivery = deepcopy(original)
        writer.receipt = original
        self.expect(self.step(1, observation=original), "pending", 1, 0)
        self.assertEqual(original.wire_response.body["output"], [])
        repeated = self.step(2, observation=redelivery)
        self.expect(repeated, "pending", 1, 0)
        self.assertEqual(repeated.last_checkpoint.reason, "duplicate_receipt")
        self.expect(self.step(3, start=True), "pending", 1, 1)

    def test_tool_proposal_and_settlement_do_not_credit_progress_by_themselves(self):
        for stage in ("proposal", "result"):
            with self.subTest(stage=stage):
                self.setup_controller()
                self.step(0, start=True)
                initial = self.receipt(calls=(self.call,))
                if stage == "proposal":
                    self.step(1, evaluate_only=True)
                    self.step(2, observation=initial)
                    self.expect(self.step(3, evaluate_only=True), "stop_no_progress", 1, 0)
                else:
                    self.step(1, observation=initial)
                    self.step(2, start=True)
                    self.step(3, evaluate_only=True)
                    self.step(4, tool_observed=True)
                    self.expect(self.step(5, evaluate_only=True), "stop_no_progress", 1, 1)

    def test_failed_terminal_checkpoint_never_exposes_candidate(self):
        self.controller = OfflineController(self.binding, journal=BrokenStage("terminal"))
        self.step(0, start=True)
        result = self.final(1)
        self.expect(result, "hold_journal", 1, 0)
        self.assertIsNone(result.candidate)
        self.assertEqual(result.last_checkpoint.reason, "terminal_write_failed")
        self.assertEqual(result.last_safe_checkpoint.reason, "criteria_met")
        self.assertIsNone(self.step(2, start=True).candidate)

    def test_not_sent_checkpoint_failure_retains_reservation_until_reconciled(self):
        self.controller = OfflineController(self.binding, journal=BrokenStage("not_sent"))
        outcome = self.step(0, start=True, before_entry=lambda: replace(self.current, provider_allowed=False))
        self.expect(outcome, "hold_reconciliation", 0, 0)
        self.assertEqual(len(outcome.outstanding), 1)
        gap = next(event for event in self.controller.journal if event.reason == "not_sent_write_failed")
        self.assertEqual(gap.ledger_before, gap.ledger_after)
        self.assertEqual(gap.ledger_after.reservation_state, "reserved")
        reconciled = self.step(1, start=True)
        self.expect(reconciled, "hold_reconciliation", 0, 0)
        self.assertFalse(reconciled.outstanding)
        recovered = next(event for event in self.controller.journal if event.stage == "not_sent")
        self.assertEqual((recovered.ledger_before.reservation_state, recovered.ledger_after.reservation_state),
                         ("reserved", "released"))
        self.assertEqual(reconciled.last_checkpoint.reason, "local_no_entry_checkpoint_recovered")

    def test_tool_dispatch_denial_is_recorded_before_reservation_release(self):
        self.step(0, start=True)
        self.step(1, observation=self.receipt(calls=(self.call,)))
        with patch.object(OfflineToolDispatch, "invoke", return_value=ToolDecision("deny", "local_tool_gate")):
            stopped = self.step(2, start=True)
        self.expect(stopped, "hold_scope", 1, 0)
        aborted = next(event for event in self.controller.journal if event.stage == "not_sent")
        self.assertEqual(aborted.reason, "local_tool_gate")
        self.assertEqual((aborted.ledger_before.reservation_state, aborted.ledger_after.reservation_state),
                         ("reserved", "released"))

    def test_api_key_marker_is_absent_at_the_actual_runner_boundary(self):
        original = _FakeRunner._enter
        calls = []
        marker = "e206-only-for-credential-exclusion"

        def inspect_runner(runner):
            calls.append(tuple(vars(runner)))
            self.assertNotIn(marker, repr(vars(runner)))
            self.assertEqual(runner.result, self.binding.synthetic_tool_result)
            return original(runner)

        self.step(0, start=True)
        self.step(1, observation=self.receipt(calls=(self.call,)))
        with patch.dict(os.environ, {"OPENAI_API_KEY": marker}), patch.object(_FakeRunner, "_enter", inspect_runner):
            self.expect(self.step(2, start=True), "pending", 1, 1)
        self.assertEqual(calls, [("result", "entry_count")])
        self.assertNotIn(marker, repr(self.controller.journal))

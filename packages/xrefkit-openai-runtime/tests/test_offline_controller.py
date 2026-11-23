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
from xrefkit_openai_runtime.offline_budget import OfflineBudget
from xrefkit_openai_runtime.offline_context import ContextAssembly
from xrefkit_openai_runtime.offline_controller import (
    Assessment, ControllerBinding, ControllerLimits, CriterionEvidence, CurrentState, HostPresentation,
    OfflineController, OfflineJournal,
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

    def supplemental_evidence(self, case, status):
        if os.environ.get("XREFKIT_E206_EVIDENCE") == "1":
            print(json.dumps({
                "supplemental": case,
                "status": asdict(status) | {"candidate": digest(status.candidate) if status.candidate else None},
                "journal": [asdict(event) for event in self.controller.journal],
            }))

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
            settled = self.step(ticks[2], observation=receipt, start=True)
            journal = self.controller.journal
            duplicate_result = self.step(ticks[3], observation=receipt, start=True)
            self.assertFalse(duplicate_result.outstanding)
            self.assertEqual(duplicate_result, settled)
            self.assertEqual(self.controller.journal, journal)
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
                              {"late_usage_conflicts_with_prior_observation", "late_conflicting_no_submit"})

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
        settled = self.step(4, tool_observed=True, start=True)
        self.expect(settled, "cancelled_with_reconciliation_evidence", 1, 1)
        journal = self.controller.journal
        duplicate = self.step(5, tool_observed=True, start=True)
        self.assertEqual(duplicate, settled)
        self.assertEqual(self.controller.journal, journal)
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
                       if event.reason == "matched_late_tool_receipt" and event.entry == original)
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
        journal = self.controller.journal
        repeated = self.step(5, observation=initial, start=True)
        self.assertEqual(repeated, held)
        self.assertEqual(self.controller.journal, journal)

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

    def pending_tool(self):
        self.step(0, start=True)
        self.step(1, observation=self.receipt(calls=(self.call,)))
        self.step(2, start=True)

    def invalid_provider(self):
        receipt = replace(self.receipt(), revision=2)
        return replace(receipt, wire_response=replace(receipt.wire_response, body=42))

    def test_closed_tick_keeps_provider_gap_and_settles_tool_in_both_fragment_orders(self):
        details = []
        for provider_first in (True, False):
            with self.subTest(provider_first=provider_first):
                self.setup_controller()
                self.pending_tool()
                invalid = self.invalid_provider()
                fragments = ({"observation": invalid}, {"tool_observed": True})
                if not provider_first:
                    fragments = fragments[::-1]
                prior = self.controller.journal
                pending = self.step(3, batch_closed=False, start=True, **fragments[0])
                self.expect(pending, "hold_batch_incomplete", 1, 1)
                wait = self.step(4, start=True)
                self.expect(wait, "hold_batch_incomplete", 1, 1)
                self.assertEqual(self.controller.journal, prior)
                closed = self.step(3, start=True, **fragments[1])
                self.expect(closed, "hold_reconciliation", 1, 1)
                self.assertFalse(closed.outstanding)
                events = [event for event in self.controller.journal if event.tick == 3]
                details.append([(event.stage, event.reason, event.ledger_after.work.debit) for event in events])
                gap = next(event for event in events if event.reason == "invalid_provider_observation")
                observed = next(event for event in events if event.stage == "observation")
                self.assertLess(events.index(gap), events.index(observed))
                self.assertEqual(gap.ledger_before, gap.ledger_after)
                self.assertEqual((observed.ledger_before.work.debit, observed.ledger_after.work.debit), (1, 2))
                self.assertEqual((observed.ledger_before.work.reserved, observed.ledger_after.work.reserved), (1, 0))
                self.controller = self.controller.reconstruct(continuity_verified=True)
                journal = self.controller.journal
                replay = self.step(3, start=True, observation=invalid, tool_observed=True)
                self.assertEqual(replay, closed)
                self.assertEqual(self.controller.journal, journal)
                later = self.step(4, start=True, observation=invalid, tool_observed=True)
                self.expect(later, "hold_reconciliation", 1, 1)
                self.assertEqual(sum(event.stage == "observation" and event.entry.operation == "tool"
                                     for event in self.controller.journal if event.entry is not None), 1)
                self.supplemental_evidence(f"closed-batch-order-{provider_first}", later)
        self.assertEqual(*details)

    def test_cancellation_revocation_and_invalid_provider_gap_remain_visible_at_tick_close(self):
        self.pending_tool()
        state = replace(self.current, cancelled=True, provider_allowed=False)
        cancelled = self.step(3, state=state, start=True, observation=self.invalid_provider(), tool_observed=True)
        self.expect(cancelled, "cancelled", 1, 1)
        self.assertEqual(cancelled.last_checkpoint.signals, ("cancelled", "stop_authority", "hold_reconciliation"))
        self.assertFalse(cancelled.outstanding)
        self.assertEqual(cancelled.last_checkpoint.ledger_after.work.debit, 2)
        self.supplemental_evidence("closed-batch-cancel-revoke-gap", cancelled)

    def test_conflicting_provider_fragments_are_rejected_before_ledger_can_settle(self):
        for first_usage in (ZERO, USAGE):
            with self.subTest(first_usage=first_usage):
                self.setup_controller()
                self.step(0, start=True)
                one = self.receipt(usage=first_usage)
                other = self.receipt(usage=USAGE if first_usage == ZERO else ZERO)
                self.step(1, observation=one, batch_closed=False)
                outcome = self.step(1, observation=other, start=True)
                self.expect(outcome, "hold_reconciliation", 1, 0)
                self.assertEqual(outcome.outstanding, (one.entry,))
                self.assertEqual(outcome.last_checkpoint.ledger_after.work.debit, 0)
                self.assertEqual(outcome.last_checkpoint.ledger_after.work.reserved, 1)

    def test_incomplete_batch_reconstruction_holds_original_execution(self):
        self.pending_tool()
        incomplete = self.step(3, tool_observed=True, batch_closed=False)
        prior = self.controller
        self.controller = prior.reconstruct(continuity_verified=True)
        observed = self.controller.status()
        self.expect(observed, "hold_reconciliation", 1, 1)
        self.assertEqual(observed.execution_id, incomplete.execution_id)
        self.assertIn("batch.continuity", observed.checkpoint_gaps)
        self.assertEqual(observed.outstanding, incomplete.outstanding)
        self.expect(self.step(3, start=True), "hold_reconciliation", 1, 1)
        with self.assertRaises(ValueError):
            prior.step(3, self.current, start=True)

    def test_consumed_no_submit_revisions_distinguish_positive_zero_and_absence(self):
        for label, usage in (("positive", USAGE), ("zero", ZERO),
                             ("absent-conflicting", MISSING), ("absent-no-contrary", MISSING)):
            with self.subTest(label=label):
                self.setup_controller()
                self.step(0, start=True)
                initial = replace(self.receipt(kind="no_submit", usage=MISSING), delay_ticks=2)
                self.retries(1, initial, self.proof(initial))
                if label == "absent-no-contrary":
                    adjusted = replace(initial, revision=2)
                else:
                    adjusted = replace(self.receipt(usage=usage), revision=2)
                    if label == "absent-conflicting":
                        wire = adjusted.wire_response
                        adjusted = replace(adjusted, wire_response=replace(
                            wire, body={key: value for key, value in wire.body.items() if key != "usage"},
                        ))
                result = self.step(2, observation=adjusted, start=True)
                disputed = label != "absent-no-contrary"
                self.expect(result, "hold_reconciliation" if disputed else "pending", 1, 0)
                self.assertEqual(result.outstanding, (initial.entry,) if disputed else ())
                revision = next(event for event in self.controller.journal
                                if event.evidence_ref == adjusted.evidence_sha256)
                self.assertEqual(revision.stage, "reconciliation")
                self.assertEqual(revision.reported_usage.total_tokens, usage.total_tokens)
                self.assertEqual(revision.ledger_before.work.debit, 0)
                self.assertEqual(revision.ledger_after.work.debit, 0)
                self.assertEqual(revision.ledger_before.reservation_state, "released")
                self.assertEqual(revision.ledger_after.reservation_state, "released")
                self.assertEqual(revision.ledger_after.work.headroom,
                                 None if disputed else self.limits.synthetic_budget_units)
                self.controller = self.controller.reconstruct(continuity_verified=True)
                journal = self.controller.journal
                self.assertEqual(self.step(2, observation=adjusted, start=True), result)
                self.assertEqual(self.controller.journal, journal)
                replay = self.step(3, observation=adjusted, start=True)
                if disputed:
                    self.assertEqual(replay, result)
                    self.assertEqual(self.controller.journal, journal)
                else:
                    self.assertEqual(result.no_progress_ticks, 1)
                    self.expect(replay, "stop_no_progress", 1, 0)
                    self.assertEqual(replay.no_progress_ticks, 2)
                    self.assertFalse(replay.outstanding)
                self.supplemental_evidence(f"consumed-no-submit-revision-{label}", replay)

    def test_revision_dispute_publishes_no_ledger_change_before_checkpoint(self):
        self.controller = OfflineController(self.binding, journal=BrokenStage("reconciliation"))
        self.step(0, start=True)
        initial = replace(self.receipt(kind="no_submit", usage=MISSING), delay_ticks=2)
        self.retries(1, initial, self.proof(initial))
        revision = replace(self.receipt(usage=ZERO), revision=2)
        failed = self.step(2, observation=revision, start=True)
        self.expect(failed, "hold_reconciliation", 1, 0)
        self.assertIn(f"reconciliation.revision:{initial.entry.admission}", failed.checkpoint_gaps)
        gap = next(event for event in self.controller.journal if event.reason == "reconciliation_write_failed")
        self.assertEqual(gap.ledger_before, gap.ledger_after)
        self.assertEqual(gap.ledger_after.work.headroom, self.limits.synthetic_budget_units)
        resumed = self.step(3, observation=revision, start=True)
        self.expect(resumed, "hold_reconciliation", 1, 0)
        self.assertEqual(resumed.outstanding, (initial.entry,))
        self.assertEqual(resumed.last_checkpoint.ledger_after.work.headroom, None)
        self.assertFalse(resumed.checkpoint_gaps)

    def test_late_dispute_blocks_redisplay_of_a_previously_checkpointed_candidate(self):
        self.step(0, start=True)
        first_revision = replace(self.receipt(usage=ZERO), revision=2)
        initial = replace(self.receipt(kind="no_submit", usage=MISSING), delay_ticks=2)
        self.retries(1, initial, self.proof(initial))
        self.step(3, start=True)
        self.expect(self.final(4), "candidate", 2, 0)
        held = self.step(5, observation=first_revision)
        self.expect(held, "hold_reconciliation", 2, 0)
        self.assertIsNone(held.candidate)
        self.assertEqual(held.outstanding, (initial.entry,))

    def test_ordinary_advance_in_retry_delay_counts_second_stalled_tick(self):
        self.step(0, start=True)
        self.step(1, evaluate_only=True)
        initial = replace(self.receipt(kind="no_submit", usage=MISSING), delay_ticks=2)
        delayed = self.retries(2, initial, self.proof(initial))
        self.assertEqual(delayed.no_progress_ticks, 1)
        stopped = self.step(3, start=True)
        self.expect(stopped, "stop_no_progress", 1, 0)
        self.assertEqual(stopped.no_progress_ticks, 2)
        self.assertFalse(stopped.outstanding)
        event = next(event for event in self.controller.journal if event.reason == "tick_closed" and event.tick == 3)
        self.assertEqual((event.progress_before, event.progress_after), (1, 2))
        self.supplemental_evidence("ordinary-retry-delay-1-to-2", stopped)

    def test_ordinary_duplicate_ticks_count_once_across_replay_and_reconstruction(self):
        self.step(0, start=True)
        receipt = self.receipt(calls=(self.call,))
        admitted = self.step(1, observation=receipt)
        self.assertEqual(admitted.no_progress_ticks, 0)
        first = self.step(2, observation=receipt)
        self.assertEqual(first.no_progress_ticks, 1)
        self.controller = self.controller.reconstruct(continuity_verified=True)
        journal = self.controller.journal
        self.assertEqual(self.step(2, observation=receipt), first)
        self.assertEqual(self.controller.status(), first)
        self.assertEqual(self.controller.journal, journal)
        second = self.step(3, observation=receipt)
        self.expect(second, "stop_no_progress", 1, 0)
        self.assertEqual(second.no_progress_ticks, 2)
        self.assertEqual(second.last_checkpoint.ledger_after.work, first.last_checkpoint.ledger_after.work)
        transitions = [(event.progress_before, event.progress_after) for event in self.controller.journal
                       if event.reason == "tick_closed" and event.tick in (2, 3)]
        self.assertEqual(transitions, [(0, 1), (1, 2)])
        self.supplemental_evidence("ordinary-duplicate-0-to-1-to-2", second)

    def test_cancel_checkpoint_gap_before_entry_never_allows_dispatch(self):
        self.controller = OfflineController(self.binding, journal=BrokenStage("cancellation"))
        held = self.step(0, start=True, before_entry=lambda: replace(self.current, cancelled=True))
        self.expect(held, "cancelled", 0, 0)
        self.assertTrue(held.cancellation_requested)
        self.assertIn("cancellation.local_request", held.checkpoint_gaps)
        self.assertFalse(held.outstanding)
        self.assertEqual(held.last_safe_checkpoint.reason, "entry_gate_denied")
        self.supplemental_evidence("cancel-before-entry-journal-gap", held)
        recovered = self.step(1, start=True)
        self.expect(recovered, "cancelled", 0, 0)
        self.assertFalse(recovered.checkpoint_gaps)

    def test_missing_cancel_checkpoint_remains_sticky_with_pending_exposure_after_reconstruction(self):
        self.controller = OfflineController(self.binding, journal=BrokenStage("cancellation"))
        self.step(0, start=True)
        receipt = self.receipt()
        stopped = self.step(1, state=replace(self.current, cancelled=True))
        self.expect(stopped, "cancelled", 1, 0)
        self.assertEqual(stopped.outstanding, (receipt.entry,))
        self.assertFalse(stopped.cancellation_acknowledged)
        self.assertIn("cancellation.local_request", stopped.checkpoint_gaps)
        self.assertEqual(stopped.last_safe_checkpoint.reason, "intent_and_reservation_saved")
        self.controller = self.controller.reconstruct(continuity_verified=False)
        recovered = self.controller.status()
        self.expect(recovered, "cancelled", 1, 0)
        self.assertEqual(recovered.execution_id, stopped.execution_id)
        self.assertIn("batch.continuity", recovered.checkpoint_gaps)
        self.assertEqual(recovered.outstanding, stopped.outstanding)
        self.expect(self.step(2, start=True), "cancelled", 1, 0)
        self.supplemental_evidence("cancel-after-entry-reconstruction-gap", recovered)

    def test_late_reconciliation_checkpoint_failure_does_not_publish_or_settle_until_recovery(self):
        self.controller = OfflineController(self.binding, journal=BrokenStage("reconciliation"))
        self.step(0, start=True)
        receipt = self.receipt()
        self.step(1, state=replace(self.current, cancelled=True))
        failed = self.step(2, observation=receipt, start=True)
        self.expect(failed, "cancelled", 1, 0)
        self.assertIn(f"reconciliation.provider:{receipt.entry.admission}", failed.checkpoint_gaps)
        self.assertEqual(failed.outstanding, (receipt.entry,))
        self.assertEqual(failed.last_checkpoint.ledger_after.work.reserved, 1)
        self.assertEqual(failed.last_checkpoint.ledger_after.work.debit, 0)
        self.controller = self.controller.reconstruct(continuity_verified=True)
        reconciled = self.step(3, observation=receipt, start=True)
        self.expect(reconciled, "cancelled_with_reconciliation_evidence", 1, 0)
        self.assertFalse(reconciled.checkpoint_gaps)
        self.assertFalse(reconciled.outstanding)
        self.assertEqual(reconciled.last_checkpoint.ledger_after.work.debit, 1)
        journal = self.controller.journal
        self.assertEqual(sum(event.reason == "matched_late_receipt" for event in journal), 1)
        self.assertEqual(self.step(4, observation=receipt, start=True), reconciled)
        self.assertEqual(self.controller.journal, journal)
        self.supplemental_evidence("late-provider-checkpoint-recovery", reconciled)

    def test_late_checkpoint_acknowledgement_is_checked_before_any_retry(self):
        class UncertainWriter(OfflineJournal):
            def __init__(self, append_first):
                super().__init__()
                self.append_first = append_first
                self.fail = True
                self.readable = False
                self.late_attempts = 0

            def append(self, event):
                if event.reason == "matched_late_receipt":
                    self.late_attempts += 1
                    if self.fail:
                        self.fail = False
                        if self.append_first:
                            super().append(event)
                        raise OSError("synthetic missing write acknowledgement")
                super().append(event)

            def committed(self, event):
                if event.reason == "matched_late_receipt" and not self.readable:
                    raise OSError("synthetic checkpoint lookup unavailable")
                return super().committed(event)

        for append_first in (True, False):
            with self.subTest(append_first=append_first):
                self.setup_controller()
                writer = UncertainWriter(append_first)
                self.controller = OfflineController(self.binding, journal=writer)
                self.step(0, start=True)
                receipt = self.receipt()
                self.step(1, state=replace(self.current, cancelled=True))
                failed = self.step(2, observation=receipt)
                self.expect(failed, "cancelled", 1, 0)
                self.assertIn("journal.commit_unknown", failed.checkpoint_gaps)
                still_unknown = self.step(3, observation=receipt)
                self.assertEqual(still_unknown.outstanding, (receipt.entry,))
                self.assertEqual(writer.late_attempts, 1)
                writer.readable = True
                recovered = self.step(4, observation=receipt)
                self.expect(recovered, "cancelled_with_reconciliation_evidence", 1, 0)
                self.assertFalse(recovered.outstanding)
                self.assertFalse(recovered.checkpoint_gaps)
                self.assertEqual(writer.late_attempts, 1 if append_first else 2)
                committed = [event for event in writer._events if event.reason == "matched_late_receipt"]
                self.assertEqual(len(committed), 1)
                self.assertEqual(committed[0].ledger_after.observation_ticks, (2,))

    def test_cancel_and_no_entry_write_gaps_leave_unsent_reservation_held(self):
        class UnavailableCancellationWriter(OfflineJournal):
            def append(self, event):
                if event.stage in ("cancellation", "not_sent"):
                    raise OSError("synthetic checkpoint unavailable")
                super().append(event)

        self.controller = OfflineController(self.binding, journal=UnavailableCancellationWriter())
        stopped = self.step(0, start=True, before_entry=lambda: replace(self.current, cancelled=True))
        self.expect(stopped, "cancelled", 0, 0)
        admission = stopped.outstanding[0]
        self.assertEqual(stopped.checkpoint_gaps, ("cancellation.local_request", f"not_sent:{admission.admission}"))
        self.assertEqual(stopped.last_checkpoint.ledger_after.work.reserved, 1)
        self.assertEqual(stopped.last_safe_checkpoint.reason, "intent_and_reservation_saved")

    def test_batch_close_failure_prevents_entry_and_retains_continuity_gap(self):
        class BrokenClose(OfflineJournal):
            def append(self, event):
                if event.reason == "tick_closed":
                    raise OSError("synthetic missing batch checkpoint")
                super().append(event)

        self.controller = OfflineController(self.binding, journal=BrokenClose())
        held = self.step(0, start=True)
        self.expect(held, "hold_reconciliation", 0, 0)
        self.assertEqual(held.committed_tick, -1)
        self.controller = self.controller.reconstruct(continuity_verified=True)
        self.assertIn("batch.continuity", self.controller.status().checkpoint_gaps)
        self.expect(self.step(1, start=True), "hold_reconciliation", 0, 0)

    def test_closed_batch_recomputes_the_same_ledger_and_retains_earlier_gate_signals(self):
        self.pending_tool()
        original = self.controller
        initial = original.status()
        before = original.journal
        invalid = self.invalid_provider()
        interrupted = replace(self.current, guard_proved=False, provider_allowed=False)
        projected = []
        for first in ("provider", "tool"):
            with self.subTest(first=first):
                shadow = original.recomputation()
                first_payload = {"observation": invalid} if first == "provider" else {"tool_observed": True}
                second_payload = {"tool_observed": True} if first == "provider" else {"observation": invalid}
                partial = shadow.step(3, interrupted, batch_closed=False, **first_payload)
                self.expect(partial, "hold_batch_incomplete", 1, 1)
                result = shadow.step(3, self.current, start=True, **second_payload)
                self.expect(result, "stop_authority", 1, 1)
                projected.append((result, shadow.journal[len(before):]))
                self.assertEqual(result.last_checkpoint.signals, ("stop_authority", "hold_reconciliation"))
                self.assertFalse(result.outstanding)
        self.assertEqual(projected[0], projected[1])
        self.assertEqual(original.status(), initial)
        self.assertEqual(original.journal, before)
        self.step(3, state=interrupted, observation=invalid, batch_closed=False)
        actual = self.step(3, start=True, tool_observed=True)
        self.assertEqual((actual, original.journal[len(before):]), projected[0])
        opened = next(event for event in original.journal if event.tick == 3 and event.reason == "tick_open")
        self.assertEqual(opened.signals, ("guard", "provider"))
        settled = next(event for event in original.journal if event.tick == 3 and event.stage == "observation")
        self.assertEqual((settled.ledger_before.work.debit, settled.ledger_after.work.debit), (1, 2))
        self.supplemental_evidence("independent-batch-recomputation-with-earlier-revocation", actual)

    def test_recomputation_of_a_ready_admission_does_not_open_an_effect(self):
        shadow = self.controller.recomputation()
        projected = shadow.step(0, self.current, start=True)
        self.expect(projected, "pending", 0, 0)
        self.assertEqual(projected.last_checkpoint.reason, "admission_would_be_requested")
        self.assertEqual(projected.last_checkpoint.ledger_after.work.reserved, 0)
        self.assertEqual(self.controller.journal, ())
        self.expect(self.step(0, start=True), "pending", 1, 0)

    def test_absent_usage_with_changed_submission_evidence_disputes_consumed_release(self):
        self.step(0, start=True)
        initial = replace(self.receipt(kind="no_submit", usage=MISSING), delay_ticks=2)
        self.retries(1, initial, self.proof(initial))
        revision = replace(initial, kind="unknown", revision=2)
        held = self.step(2, observation=revision, start=True)
        self.expect(held, "hold_reconciliation", 1, 0)
        self.assertEqual(held.outstanding, (initial.entry,))
        observed = next(event for event in self.controller.journal
                        if event.reason == "consumed_no_submit_usage_absent_disputed")
        self.assertEqual(observed.reported_usage, MISSING)
        self.assertEqual(observed.ledger_after.reservation_state, "released")
        self.assertIsNone(observed.ledger_after.work.headroom)
        self.assertEqual(observed.ledger_after.work.debit, 0)
        self.supplemental_evidence("consumed-no-submit-revised-to-unknown", held)

    def test_prior_safe_rejection_requires_the_pinned_reason_to_preserve_release(self):
        for exact in (True, False):
            with self.subTest(exact=exact):
                self.setup_controller()
                self.step(0, start=True)
                initial = replace(self.receipt(kind="safe_rejection", usage=MISSING), delay_ticks=2)
                self.retries(1, initial, self.proof(initial))
                normalized = self.controller._normalized[initial.entry]
                if not exact:
                    normalized = replace(normalized, reason="unproved_rejection")
                revision = replace(initial, revision=2)
                with patch.object(OfflineController, "_normalize_provider", return_value=normalized):
                    outcome = self.step(2, observation=revision, start=True)
                self.expect(outcome, "pending" if exact else "hold_reconciliation", 1, 0)
                self.assertEqual(outcome.outstanding, () if exact else (initial.entry,))

    def test_post_append_ledger_failure_holds_and_reuses_the_revision_checkpoint(self):
        self.step(0, start=True)
        initial = replace(self.receipt(kind="no_submit", usage=MISSING), delay_ticks=2)
        self.retries(1, initial, self.proof(initial))
        revision = replace(self.receipt(usage=ZERO), revision=2)
        with patch.object(OfflineBudget, "_publish_settlement", side_effect=OSError("synthetic publication loss")):
            failed = self.step(2, observation=revision, start=True)
        self.expect(failed, "hold_reconciliation", 1, 0)
        self.assertIn(f"ledger.publication:{initial.entry.attempt}", failed.checkpoint_gaps)
        self.assertEqual(failed.last_checkpoint.ledger_after.work.headroom, self.limits.synthetic_budget_units)
        projected = next(event for event in self.controller.journal
                         if event.reason == "consumed_no_submit_usage_reported")
        self.assertIsNone(projected.ledger_after.work.headroom)
        self.controller = self.controller.reconstruct(continuity_verified=True)
        recovered = self.step(3, observation=revision, start=True)
        self.expect(recovered, "hold_reconciliation", 1, 0)
        self.assertEqual(recovered.outstanding, (initial.entry,))
        self.assertFalse(recovered.checkpoint_gaps)
        self.assertEqual(sum(event.accounting_key == projected.accounting_key
                             for event in self.controller.journal), 1)
        handoff = self.controller.journal[-1]
        self.assertEqual(handoff.ledger_after.work.debit, 0)
        self.assertIsNone(handoff.ledger_after.work.headroom)
        prior = self.controller.journal
        self.assertEqual(self.step(4, observation=revision, start=True), recovered)
        self.assertEqual(self.controller.journal, prior)
        self.supplemental_evidence("recorded-dispute-then-ledger-publication-loss", recovered)

    def test_required_progress_evidence_write_failure_holds_before_eligible_entry(self):
        self.controller = OfflineController(self.binding, journal=BrokenStage("evaluation"))
        evidence = self.criterion_evidence(digest(b"new required criterion evidence"))
        state = replace(self.current, verified_criterion_evidence=(evidence,))
        held = self.step(0, state=state, start=True)
        self.expect(held, "hold_reconciliation", 0, 0)
        self.assertIn(f"progress.criterion:{evidence.observation_sha256}", held.checkpoint_gaps)
        self.assertFalse(held.outstanding)
        self.assertEqual(held.last_checkpoint.ledger_after.work.reserved, 0)
        self.supplemental_evidence("required-progress-evidence-append-failure", held)

    def test_first_protocol_receipts_with_explicit_advance_do_not_credit_or_add_stalled_ticks(self):
        self.step(0, start=True)
        self.assertEqual(self.step(1, evaluate_only=True).no_progress_ticks, 1)
        proposal = self.step(2, observation=self.receipt(calls=(self.call,)), start=True)
        self.expect(proposal, "pending", 1, 0)
        self.assertEqual(proposal.no_progress_ticks, 1)
        self.step(3, start=True)
        settled = self.step(4, tool_observed=True, start=True)
        self.expect(settled, "pending", 1, 1)
        self.assertEqual(settled.no_progress_ticks, 1)
        self.assertEqual(settled.last_checkpoint.reason, "confirmed_usage")
        stopped = self.step(5, evaluate_only=True)
        self.expect(stopped, "stop_no_progress", 1, 1)
        self.assertEqual(stopped.no_progress_ticks, 2)
        self.supplemental_evidence("first-protocol-receipts-plus-explicit-advance", stopped)

    def test_active_ambiguous_settlement_uses_same_key_after_transition_to_late(self):
        class UncertainActive(OfflineJournal):
            def __init__(self, append_first):
                super().__init__()
                self.append_first = append_first
                self.readable = False
                self.attempts = 0

            def append(self, event):
                if event.accounting_key is not None:
                    self.attempts += 1
                    if self.attempts == 1:
                        if self.append_first:
                            super().append(event)
                        raise OSError("synthetic missing accounting acknowledgement")
                super().append(event)

            def committed(self, event):
                if event.accounting_key is not None and not self.readable:
                    raise OSError("synthetic accounting checkpoint lookup unavailable")
                return super().committed(event)

        for append_first in (True, False):
            with self.subTest(append_first=append_first):
                self.setup_controller()
                writer = UncertainActive(append_first)
                self.controller = OfflineController(self.binding, journal=writer)
                self.step(0, start=True)
                receipt = self.receipt()
                held = self.step(1, observation=receipt)
                self.expect(held, "hold_reconciliation", 1, 0)
                self.assertEqual(held.outstanding, (receipt.entry,))
                self.assertIn("journal.commit_unknown", held.checkpoint_gaps)
                still_held = self.step(2, observation=receipt)
                self.assertEqual(writer.attempts, 1)
                self.assertEqual(still_held.outstanding, (receipt.entry,))
                writer.readable = True
                recovered = self.step(3, observation=receipt, start=True)
                self.expect(recovered, "hold_reconciliation", 1, 0)
                self.assertFalse(recovered.outstanding)
                self.assertFalse(recovered.checkpoint_gaps)
                accounting = [event for event in writer._events if event.accounting_key is not None]
                self.assertEqual(len(accounting), 1)
                self.assertEqual(accounting[0].stage, "observation" if append_first else "reconciliation")
                self.assertEqual(accounting[0].ledger_after.observation_ticks, (1,))
                self.assertEqual(accounting[0].ledger_after.work.debit, 1)
                self.supplemental_evidence(f"active-to-late-accounting-ack-{append_first}", recovered)

    def test_cancellation_becomes_sticky_primary_after_authority_or_deadline_stop(self):
        for reason in ("stop_authority", "stop_deadline"):
            with self.subTest(reason=reason):
                self.setup_controller()
                self.step(0, start=True)
                receipt = self.receipt()
                at = 1 if reason == "stop_authority" else 8
                state = replace(self.current, guard_proved=False) if reason == "stop_authority" else self.current
                old = self.step(at, state=state)
                self.expect(old, reason, 1, 0)
                cancelled = self.step(at + 1, state=replace(self.current, cancelled=True), start=True)
                self.expect(cancelled, "cancelled", 1, 0)
                self.assertEqual(cancelled.last_checkpoint.signals[:2], ("cancelled", reason))
                self.assertEqual(cancelled.outstanding, (receipt.entry,))
                final = self.step(at + 2, observation=receipt, start=True)
                self.expect(final, "cancelled_with_reconciliation_evidence", 1, 0)
                self.assertFalse(final.outstanding)
                self.supplemental_evidence(f"cancel-after-{reason}", final)

    def test_review_conflict_and_evidence_requests_arbitrate_without_new_effect(self):
        second = ReviewAuthority("second-reviewer", "second-review-context")
        for mode, signal in (
            ("missing-review", "request_independent_review"),
            ("review-disagreement", "independent_review_conflict"),
            ("missing-usage-evidence", "verify_evidence"),
        ):
            with self.subTest(mode=mode):
                self.setup_controller()
                if mode == "review-disagreement":
                    self.binding = replace(self.binding, additional_reviewers=(second,))
                    self.controller = OfflineController(self.binding)
                self.step(0, start=True)
                receipt = self.receipt()
                assessment = self.assessment(receipt, review=mode != "missing-review")
                inputs, policy = assessment.inputs, assessment.policy
                if mode == "review-disagreement":
                    review = replace(inputs.reviews[0], id=second.reviewer_id, context=second.context, verdict="fail")
                    inputs = replace(inputs, reviews=(*inputs.reviews, review))
                    policy = replace(policy, reviewers=(self.binding.reviewer, second),
                                     reviewer_record_pins=tuple(evidence_digest(item) for item in inputs.reviews))
                if mode == "missing-usage-evidence":
                    policy = replace(policy, usage_required_fields=frozenset({"cached_input_tokens"}))
                policy = replace(policy, approved_rules_sha256=effective_rules_digest(policy))
                assessment = replace(assessment, policy=policy, inputs=inputs)
                state = replace(self.current, approved_evaluation_sha256=evaluation_policy_digest(policy))
                held = self.step(1, state=state, observation=receipt, assessment=assessment, start=True)
                self.expect(held, "hold_evaluation", 1, 0)
                self.assertIsNone(held.candidate)
                self.assertIn(signal, held.last_checkpoint.signals)
                self.expect(self.step(2, start=True), "hold_evaluation", 1, 0)
                self.supplemental_evidence(f"evaluation-arbitration-{mode}", held)

    def test_provider_evidence_availability_stays_with_the_fragment_in_both_orders(self):
        for field in ("capture_available", "observation_available"):
            for restricted_first in (True, False):
                with self.subTest(field=field, restricted_first=restricted_first):
                    self.setup_controller()
                    self.step(0, start=True)
                    receipt = self.receipt()
                    assessment = self.assessment(receipt)
                    permitted = replace(self.current, approved_evaluation_sha256=evaluation_policy_digest(assessment.policy))
                    restricted = replace(permitted, **{field: False})
                    fragments = (
                        {"state": restricted, "observation": receipt, "assessment": assessment},
                        {"state": permitted},
                    )
                    first, last = fragments if restricted_first else fragments[::-1]
                    open_batch = self.step(1, batch_closed=False, **first)
                    self.expect(open_batch, "hold_batch_incomplete", 1, 0)
                    held = self.step(1, start=True, **last)
                    self.expect(held, "hold_reconciliation", 1, 0)
                    self.assertEqual(held.outstanding, (receipt.entry,))
                    self.assertEqual(held.last_consistent_ledger.work.reserved, 1)
                    self.assertEqual(held.last_consistent_ledger.work.debit, 0)
                    self.assertIsNone(held.candidate)
                    self.supplemental_evidence(f"provider-evidence-{field}-{restricted_first}", held)

    def test_missing_provider_evidence_does_not_prevent_independent_tool_accounting(self):
        for restricted_first in (True, False):
            with self.subTest(restricted_first=restricted_first):
                self.setup_controller()
                self.step(0, start=True)
                first_receipt = self.receipt(calls=(self.call,))
                self.step(1, observation=first_receipt)
                self.step(2, start=True)
                fragments = (
                    {"state": replace(self.current, capture_available=False),
                     "observation": replace(first_receipt, revision=2)},
                    {"state": self.current, "tool_observed": True},
                )
                first, last = fragments if restricted_first else fragments[::-1]
                self.step(3, batch_closed=False, **first)
                held = self.step(3, start=True, **last)
                self.expect(held, "hold_reconciliation", 1, 1)
                changes = [event for event in self.controller.journal if event.stage == "observation"]
                self.assertEqual([event.entry.operation for event in changes], ["provider", "tool"])
                self.assertEqual(held.last_consistent_ledger.work.debit, 2)
                self.assertFalse(held.outstanding)

    def test_tool_receipt_evidence_is_not_replaced_by_closing_fragment(self):
        for restricted_first in (True, False):
            with self.subTest(restricted_first=restricted_first):
                self.setup_controller()
                self.pending_tool()
                fragments = (
                    {"state": replace(self.current, observation_available=False), "tool_observed": True},
                    {"state": self.current},
                )
                first, last = fragments if restricted_first else fragments[::-1]
                self.step(3, batch_closed=False, **first)
                result = self.step(3, start=True, **last)
                self.expect(result, "hold_reconciliation", 1, 1)
                self.assertEqual(len(result.outstanding), 1)
                self.assertEqual(result.outstanding[0].operation, "tool")
                self.assertEqual(result.last_consistent_ledger.work.debit, 1)
                self.assertEqual(result.last_consistent_ledger.work.reserved, 1)
                self.supplemental_evidence(f"tool-receipt-affine-evidence-{restricted_first}", result)

    def test_unpublished_dispute_reports_original_attempt_and_replays_across_headroom_change(self):
        for initial_headroom in (True, False):
            with self.subTest(initial_headroom=initial_headroom):
                self.setup_controller()
                self.step(0, start=True)
                original = replace(self.receipt(kind="no_submit", usage=MISSING), delay_ticks=2)
                self.retries(1, original, self.proof(original))
                revision = replace(self.receipt(usage=ZERO), revision=2)
                first = replace(self.current, headroom_proved=initial_headroom)
                with patch.object(OfflineBudget, "_publish_settlement", side_effect=OSError("synthetic publication loss")):
                    failed = self.step(2, state=first, observation=revision, start=True)
                self.expect(failed, "hold_reconciliation", 1, 0)
                self.assertEqual(failed.outstanding, (original.entry,))
                self.assertEqual(failed.last_consistent_ledger.work.debit, 0)
                self.assertEqual(failed.last_consistent_ledger.work.headroom,
                                 self.limits.synthetic_budget_units if initial_headroom else None)
                self.assertEqual(failed.last_safe_checkpoint.reason, "verified_no_submit")
                pending = next(event for event in self.controller.journal
                               if event.reason == "consumed_no_submit_usage_reported")
                self.assertEqual(failed.last_consistent_ledger.accounting_fact_sha256,
                                 pending.ledger_before.accounting_fact_sha256)
                self.assertNotEqual(pending.ledger_after.accounting_fact_sha256,
                                    failed.last_consistent_ledger.accounting_fact_sha256)
                self.controller = self.controller.reconstruct(continuity_verified=True)
                new_headroom = replace(self.current, headroom_proved=not initial_headroom)
                recovered = self.step(3, state=new_headroom, observation=revision, start=True)
                self.expect(recovered, "hold_reconciliation", 1, 0)
                self.assertEqual(recovered.outstanding, (original.entry,))
                self.assertFalse(recovered.checkpoint_gaps)
                self.assertEqual(recovered.last_consistent_ledger.work.debit, 0)
                self.assertIsNone(recovered.last_consistent_ledger.work.headroom)
                self.assertEqual(recovered.last_consistent_ledger.accounting_fact_sha256,
                                 pending.ledger_after.accounting_fact_sha256)
                self.assertEqual(sum(event.accounting_key == pending.accounting_key
                                     for event in self.controller.journal), 1)
                stable = self.controller.journal
                self.assertEqual(self.step(4, state=first, observation=revision, start=True), recovered)
                self.assertEqual(self.controller.journal, stable)
                self.supplemental_evidence(f"outstanding-unpublished-dispute-headroom-{initial_headroom}", recovered)

    def test_billable_invalid_output_does_not_satisfy_a_simultaneous_advance(self):
        self.step(0, start=True)
        self.assertEqual(self.step(1, evaluate_only=True).no_progress_ticks, 1)
        receipt = self.receipt()
        malformed = replace(receipt, wire_response=replace(
            receipt.wire_response, body=receipt.wire_response.body | {"output": [{"type": "unsupported"}]},
        ))
        stopped = self.step(2, observation=malformed, start=True)
        self.expect(stopped, "stop_no_progress", 1, 0)
        self.assertEqual(stopped.no_progress_ticks, 2)
        self.assertEqual(stopped.last_checkpoint.signals, ("stop_no_progress", "hold_outcome"))
        self.assertEqual(stopped.last_consistent_ledger.work.debit, 1)
        self.assertIsNone(stopped.candidate)
        self.supplemental_evidence("billable-invalid-output-plus-explicit-advance", stopped)

    def test_required_unchanged_criterion_checkpoint_failure_blocks_ready_entry(self):
        self.controller = OfflineController(self.binding, journal=BrokenStage("evaluation"))
        unchanged = self.criterion_evidence(self.baseline_criterion_sha256)
        state = replace(self.current, verified_criterion_evidence=(unchanged,))
        held = self.step(0, state=state, start=True)
        self.expect(held, "hold_reconciliation", 0, 0)
        self.assertIn(f"progress.criterion:{unchanged.observation_sha256}", held.checkpoint_gaps)
        self.assertTrue(any(event.reason == "evaluation_write_failed" for event in self.controller.journal))
        self.assertEqual(held.last_consistent_ledger.work.reserved, 0)
        self.supplemental_evidence("required-unchanged-evidence-checkpoint-failure", held)

    def host_presentation(self, status, tick, *, execution_id=None):
        binding = self.binding
        return HostPresentation(
            execution_id or binding.assignment.execution_id, binding.invocation_id, binding.session_id,
            status, tick, f"host-{status}-{tick}",
        )

    def test_post_candidate_cancel_applies_all_authoritative_host_presentation_branches(self):
        for mode in ("pending", "delivered", "absent", "contradictory", "unattributed", "unordered"):
            with self.subTest(mode=mode):
                self.setup_controller()
                self.step(0, start=True)
                receipt = self.receipt()
                recorded = self.final(1)
                self.expect(recorded, "candidate", 1, 0)
                candidate_hash = digest(recorded.candidate)
                if mode in ("delivered", "contradictory"):
                    delivered = self.host_presentation("completed", 2)
                    self.step(2, state=replace(self.current, presentation_evidence=(delivered,)))
                if mode in ("pending", "contradictory"):
                    evidence = (self.host_presentation("not_presented", 3),)
                elif mode == "unattributed":
                    evidence = (self.host_presentation("completed", 2, execution_id="wrong-execution"),)
                elif mode == "unordered":
                    evidence = (self.host_presentation("completed", 3),)
                else:
                    evidence = ()
                state = replace(self.current, cancelled=True, presentation_evidence=evidence)
                cancelled = self.step(3, state=state, observation=receipt, start=True)
                self.expect(cancelled, "cancelled", 1, 0)
                expected = {"pending": "suppressed", "delivered": "historical"}.get(mode, "held")
                self.assertEqual(cancelled.presentation, expected)
                self.assertEqual(cancelled.presentation_owner, "#208" if expected == "held" else None)
                self.assertTrue(cancelled.cancellation_requested)
                self.assertIsNone(cancelled.candidate)
                self.assertEqual(cancelled.recorded_candidate_sha256, candidate_hash)
                self.assertEqual(cancelled.last_consistent_ledger.work.debit, 1)
                preserved = self.controller.journal
                self.assertEqual(self.step(4, observation=receipt, start=True), cancelled)
                self.assertEqual(self.controller.journal, preserved)
                self.assertTrue(any(event.reason == "candidate" for event in preserved))
                self.assertTrue(any(event.reason == "local_request" for event in preserved))
                self.supplemental_evidence(f"post-candidate-cancel-presentation-{mode}", cancelled)

    def test_committed_tick_duplicate_keeps_new_cancellation_for_subsequent_decision(self):
        self.step(0, start=True)
        receipt = self.receipt()
        candidate = self.final(1)
        original = self.controller.journal
        foreign = replace(self.current, cancelled=True, invocation_id="unattributed")
        self.assertEqual(self.step(1, observation=receipt, start=True, state=foreign), candidate)
        deferred = self.step(1, observation=receipt, start=True, state=replace(self.current, cancelled=True))
        self.expect(deferred, "cancelled", 1, 0)
        self.assertTrue(deferred.cancellation_requested)
        self.assertIsNone(deferred.candidate)
        self.assertEqual(deferred.committed_tick, 1)
        self.assertEqual(self.controller.journal, original)
        self.assertIn("cancellation.awaiting_decision", deferred.checkpoint_gaps)
        current_host = self.host_presentation("not_presented", 2)
        progressed = self.step(2, state=replace(self.current, presentation_evidence=(current_host,)), start=True)
        self.expect(progressed, "cancelled", 1, 0)
        self.assertEqual(progressed.presentation, "suppressed")
        self.assertEqual(progressed.recorded_candidate_sha256, digest(candidate.candidate))
        self.assertFalse(progressed.checkpoint_gaps)
        self.assertEqual(sum(event.reason == "local_request" for event in self.controller.journal), 1)
        self.supplemental_evidence("new-cancellation-mixed-with-committed-tick-replay", progressed)

    def test_partially_delivered_cancellation_holds_candidate_until_the_batch_closes(self):
        self.step(0, start=True)
        candidate = self.final(1)
        journal = self.controller.journal
        partial = self.step(2, state=replace(self.current, cancelled=True), batch_closed=False)
        self.expect(partial, "cancelled", 1, 0)
        self.assertEqual(partial.presentation, "held")
        self.assertIsNone(partial.candidate)
        self.assertEqual(self.controller.journal, journal)
        confirmed = self.host_presentation("not_presented", 2)
        closed = self.step(2, state=replace(self.current, presentation_evidence=(confirmed,)), start=True)
        self.expect(closed, "cancelled", 1, 0)
        self.assertEqual(closed.presentation, "suppressed")
        self.assertEqual(closed.recorded_candidate_sha256, digest(candidate.candidate))

    def test_presentation_checkpoint_failure_holds_without_erasing_the_candidate(self):
        self.controller = OfflineController(self.binding, journal=BrokenStage("presentation"))
        self.step(0, start=True)
        candidate = self.final(1)
        awaiting = self.host_presentation("not_presented", 2)
        state = replace(self.current, cancelled=True, presentation_evidence=(awaiting,))
        held = self.step(2, state=state, start=True)
        self.expect(held, "cancelled", 1, 0)
        self.assertEqual(held.presentation, "held")
        self.assertEqual(held.presentation_owner, "#208")
        self.assertTrue(any(key.startswith("presentation.evidence:") for key in held.checkpoint_gaps))
        self.assertIsNone(held.candidate)
        self.assertEqual(held.recorded_candidate_sha256, digest(candidate.candidate))
        recovered = self.step(3, state=state, start=True)
        self.expect(recovered, "cancelled", 1, 0)
        self.assertEqual(recovered.presentation, "suppressed")
        self.assertFalse(recovered.checkpoint_gaps)
        self.assertIsNone(recovered.candidate)

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

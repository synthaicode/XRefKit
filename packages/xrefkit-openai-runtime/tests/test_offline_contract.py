from __future__ import annotations

import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from pydantic import ValidationError

from offline_boundary import DestinationGrant, FakeBoundary, RunnerEvidence
from xrefkit_openai_runtime.contracts import (
    ExecutionEvent,
    ExecutionRequest,
    ExecutionResult,
    assess_model_result,
    validate_trace,
)


class OfflineExecutionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.golden = json.loads(
            (Path(__file__).parent / "fixtures" / "execution_v1.json").read_text(encoding="utf-8")
        )
        self.request = ExecutionRequest.model_validate_json(json.dumps(self.golden["request"]))
        self.events = [
            ExecutionEvent.model_validate_json(json.dumps(item)) for item in self.golden["events"]
        ]
        self.result = ExecutionResult.model_validate_json(json.dumps(self.golden["result"]))
        self.runner = RunnerEvidence("synthetic-runner", 1, True)
        self.boundary = FakeBoundary(self.request.assignment, self.runner)

    def test_e200_01_versioned_contract(self) -> None:
        pairs = [
            (self.request, self.golden["request"]),
            *zip(self.events, self.golden["events"], strict=True),
            (self.result, self.golden["result"]),
        ]
        for record, golden in pairs:
            with self.subTest(record=type(record).__name__):
                self.assertEqual(json.loads(record.model_dump_json()), golden)
                for version in (2, True, "1"):
                    with self.assertRaises(ValidationError):
                        type(record).model_validate_json(json.dumps({**golden, "version": version}))
                with self.assertRaises(ValidationError):
                    type(record).model_validate_json(json.dumps({**golden, "unexpected": 0}))
        with self.assertRaises(ValidationError):
            ExecutionRequest.model_validate_json(
                json.dumps({**self.golden["request"], "assignment": {**self.golden["request"]["assignment"], "extra": "synthetic"}})
            )

    def test_e200_02_correlation_and_currentness(self) -> None:
        validate_trace(self.request, self.events, self.result)
        for event_order in (
            [self.events[1], self.events[0], self.events[2]],
            [*self.events[:2], self.events[2].model_copy(update={"call_id": "other-call"})],
            [*self.events, self.events[0].model_copy(update={"sequence": 4, "call_id": "other-call"})],
        ):
            with self.assertRaises(ValueError):
                validate_trace(self.request, event_order, self.result)
        for updates in (
            {"attempt_id": "other-attempt"},
            {"call_id": "other-call"},
            {"assignment": self.request.assignment.model_copy(update={"work_item_id": "other"})},
        ):
            with self.assertRaises(ValueError):
                validate_trace(self.request, self.events, self.result.model_copy(update=updates))
        for updates in ({"binding_sha256": "f" * 64}, {"route_revision": 0}):
            stale = self.request.assignment.model_copy(update=updates)
            self.assertFalse(self.boundary.invoke_tool(stale, self.runner))
        grant = DestinationGrant("approved.endpoint.invalid", "submit", "synthetic")
        for runner in (None, RunnerEvidence(self.runner.runner_id, 2, True)):
            self.assertFalse(self.boundary.invoke_tool(self.request.assignment, runner))
            self.assertEqual(
                self.boundary.send(
                    self.request.assignment, runner, grant.destination, grant.purpose, grant.data_scope, grant,
                    operation_id=self.result.operation_id, attempt_id=self.result.attempt_id,
                ),
                "stale_runner",
            )
        self.assertEqual((self.boundary.invocations, self.boundary.sends), (0, 0))

    def test_e200_03_tool_knowledge_and_command_scope(self) -> None:
        assignment = self.request.assignment
        self.assertTrue(self.boundary.invoke_tool(assignment, self.runner))
        for kwargs in (
            {"tool": "unregistered"},
            {"knowledge": None},
            {"knowledge": ("A00000000001", 0)},
            {"user_commands": ()},
            {"arguments": ("disallowed",)},
            {"command": "outside-policy", "user_commands": ("outside-policy",)},
            {"indirect": True},
        ):
            with self.subTest(options=kwargs):
                self.assertFalse(self.boundary.invoke_tool(assignment, self.runner, **kwargs))
        unavailable = RunnerEvidence("synthetic-unavailable", 1, False)
        other_boundary = FakeBoundary(assignment, unavailable)
        self.assertFalse(other_boundary.invoke_tool(assignment, unavailable))
        self.assertEqual((self.boundary.invocations, other_boundary.invocations), (1, 0))

    def test_e200_04_destination_confirmation(self) -> None:
        assignment = self.request.assignment
        data_scope = "synthetic"
        original = DestinationGrant("approved.endpoint.invalid", "submit", data_scope)
        new_destination = "new.endpoint.invalid"
        denied = DestinationGrant(original.destination, "submit", data_scope, approved=False)
        expired = DestinationGrant(original.destination, "submit", data_scope, expires_at=0)
        for destination, purpose, scope, grant, expected in (
            (new_destination, "submit", data_scope, None, "missing"),
            ("changed.endpoint.invalid", "submit", data_scope, original, "mismatch"),
            ("redirect.endpoint.invalid", "submit", data_scope, original, "mismatch"),
            (original.destination, "probe", data_scope, original, "mismatch"),
            (original.destination, "submit", "out-of-scope", original, "mismatch"),
            ("probe.endpoint.invalid", "probe", data_scope, None, "missing"),
            (original.destination, "submit", data_scope, denied, "denied"),
            (original.destination, "submit", data_scope, expired, "expired"),
        ):
            with self.subTest(destination=destination, purpose=purpose, scope=scope, expected=expected):
                self.assertEqual(
                    self.boundary.send(
                        assignment, self.runner, destination, purpose, scope, grant,
                        operation_id=self.result.operation_id, attempt_id=self.result.attempt_id,
                    ),
                    expected,
                )
        self.assertEqual(self.boundary.sends, 0)
        new_grant = DestinationGrant(new_destination, "submit", data_scope)
        self.assertEqual(
            self.boundary.send(
                assignment, self.runner, new_destination, "submit", data_scope, new_grant,
                operation_id=self.result.operation_id, attempt_id=self.result.attempt_id,
            ),
            "allowed",
        )
        self.assertEqual(self.boundary.sends, 1)

    def test_e200_05_outcome_and_projection_separation(self) -> None:
        self.assertTrue(self.result.transport_completed)
        held = self.events[2].model_copy(update={"kind": "held"})
        with self.assertRaises(ValueError):
            validate_trace(
                self.request, [*self.events[:2], held],
                self.result.model_copy(update={"transport_completed": False}),
            )
        with self.assertRaises(ValueError):
            assess_model_result(self.request, self.events[:2], self.result)
        self.assertEqual(assess_model_result(self.request, self.events, self.result), "review_required")
        cancelled = self.request.model_copy(update={"cancelled": True})
        self.assertEqual(assess_model_result(cancelled, self.events, self.result), "held")
        for model in (None, "different-model"):
            outcome = self.result.model_copy(update={"observed_model": model})
            self.assertEqual(assess_model_result(self.request, self.events, outcome), "held")
        unselected = self.request.model_copy(update={"selected_model": None})
        unobserved = self.result.model_copy(update={"observed_model": None})
        self.assertEqual(assess_model_result(unselected, self.events, unobserved), "held")
        self.assertEqual(assess_model_result(unselected, self.events, self.result), "held")
        for status in ("refused", "held"):
            outcome = self.result.model_copy(update={"outcome": status, "transport_completed": False})
            restored = ExecutionResult.model_validate_json(outcome.model_dump_json())
            self.assertEqual(assess_model_result(self.request, (), restored), status)

    def test_e200_06_duplicate_admission_and_late_receipt(self) -> None:
        assignment = self.request.assignment
        operation_id = self.result.operation_id
        attempt_id = self.result.attempt_id
        reservation = self.request.reservation_ref
        grant = DestinationGrant("approved.endpoint.invalid", "submit", "synthetic")
        send_args = (self.runner, grant.destination, grant.purpose, grant.data_scope, grant)
        attempt = {"operation_id": operation_id, "attempt_id": attempt_id}

        confirmed = FakeBoundary(assignment, self.runner)
        self.assertEqual(confirmed.send(assignment, *send_args, **attempt), "allowed")
        self.assertEqual(confirmed.send(assignment, *send_args, **attempt), "duplicate")
        self.assertEqual(confirmed.sends, 1)

        stale = assignment.model_copy(update={"owner_generation": 0})
        self.assertEqual(
            self.boundary.send(stale, *send_args, **attempt, pending_reservation=reservation),
            "stale",
        )
        self.assertEqual(self.boundary.sends, 0)
        contender = Barrier(2)

        def admit() -> str:
            contender.wait()
            return self.boundary.send(assignment, *send_args, **attempt, pending_reservation=reservation)

        with ThreadPoolExecutor(max_workers=2) as workers:
            outcomes = [workers.submit(admit) for _ in range(2)]
            self.assertCountEqual([result.result() for result in outcomes], ["allowed", "duplicate"])
        self.assertEqual(self.boundary.sends, 1)
        held_event = self.events[2].model_copy(update={"kind": "held"})
        held_events = [*self.events[:2], held_event]
        held_result = self.result.model_copy(update={"outcome": "held", "transport_completed": False})
        self.assertEqual(assess_model_result(self.request, held_events, held_result), "held")
        self.assertEqual(self.boundary.reservation, reservation)
        self.assertEqual(
            self.boundary.send(
                assignment, *send_args, operation_id=operation_id, attempt_id="attempt-2",
                pending_reservation="reserved-2",
            ),
            "duplicate",
        )
        self.assertFalse(self.boundary.reconcile(operation_id, "attempt-2", "wrong-receipt"))
        self.assertEqual(self.boundary.reservation, reservation)
        self.assertTrue(self.boundary.reconcile(operation_id, attempt_id, "receipt-1"))
        self.assertFalse(self.boundary.reconcile(operation_id, attempt_id, "receipt-1"))
        late_receipt = self.events[2].model_copy(update={"sequence": 4})
        self.assertEqual(
            assess_model_result(self.request, [*held_events, late_receipt], self.result),
            "review_required",
        )
        self.assertIsNone(self.boundary.reservation)
        self.assertEqual((self.boundary.sends, self.boundary.settlements), (1, 1))

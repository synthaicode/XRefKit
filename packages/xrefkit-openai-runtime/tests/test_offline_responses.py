from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
from threading import Barrier
import unittest

from xrefkit_openai_runtime.contracts import ExecutionRequest
from xrefkit_openai_runtime.offline_context import ContextAssembly, assemble_offline_context
from xrefkit_openai_runtime.offline_responses import (
    Admission, DispatchState, FakeInvocation, FakeResponse, OfflineResponsesAdapter,
    PossibleSubmission, TextItem, ToolProposal,
)


_FIXTURES = Path(__file__).parent / "fixtures"
_FROZEN_HASH = "c9b09627fda3343d6a67a43f3b0ad3f03af45b51401726b89ee58ab477eed28c"

_EXPECTED_DISPOSITIONS = {
    "stable_order_and_typed_tool_proposal": "completed",
    "observed_totals_with_nested_breakdowns": "completed",
    "zeros_preserved": "completed",
    "usage_unknown": "completed",
    "unreported_fields_unknown": "completed",
    "reported_usage_preserved": "incomplete",
    "same_attempt_and_receipt_identity_no_charge_or_reservation_release": "completed",
    "no_protected_outbound_fields": "local_hold",
    "keep_allowed_ids_status_code_exclude_canaries": "no_retry",
    "no_local_manifest_or_credential_in_provider_input_or_default_diagnostics": "completed",
    "no_second_send": "completed",
}


class OfflineResponsesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = (_FIXTURES / "e202-fixtures-r1" / "cases.json").read_bytes()
        if sha256(raw).hexdigest() != _FROZEN_HASH:
            raise AssertionError("frozen E202 fixture drift")
        cls.spec = json.loads(raw)
        cls.defaults = cls.spec["defaults"]
        upstream = cls.spec["baseline"]
        golden = json.loads((_FIXTURES / "execution_v1.json").read_bytes())
        cls.request = ExecutionRequest.model_validate(golden["request"])
        inventory_path = _FIXTURES / upstream["context_revision"]
        inventory = (inventory_path / "fixture-inventory.json").read_bytes()
        cls.context = assemble_offline_context(
            cls.request, current_assignment=cls.request.assignment, fixture_root=inventory_path,
            inventory_bytes=inventory, inventory_sha256=upstream["inventory_sha256"],
            destination="synthetic-destination-approved",
            authorized_destination="synthetic-destination-approved",
        )
        if (
            cls.context.payload is None or sha256(cls.context.payload).hexdigest() != upstream["context_sha256"]
            or cls.context.provenance_sha256 != upstream["provenance_sha256"]
        ):
            raise AssertionError("accepted #201 context drift")

    def setup_variant(self, changes):
        settings = {**self.defaults, **changes}
        request = self.request.model_copy(update={"cancelled": settings.get("cancelled", False)})
        context = self.context
        if settings["context_state"] == "held":
            context = replace(context, hold_reason="fixture_hold")
        if "restricted_field" in settings:
            payload = json.loads(context.payload)
            payload["supporting_data"][0]["text"] = settings["restricted_field"]
            encoded = json.dumps(payload, separators=(",", ":")).encode()
            provenance = json.loads(context.provenance)
            provenance["payload_sha256"] = sha256(encoded).hexdigest()
            context = ContextAssembly(encoded, json.dumps(provenance).encode(), None)

        admission = Admission(
            request.assignment, settings["attempt_id"], request.authorization_ref, request.reservation_ref,
            settings.get("context_digest", sha256(context.payload).hexdigest()), context.provenance_sha256,
            consumed=settings["admission"] == "consumed",
        )
        current_assignment = request.assignment
        if "current_route_revision" in changes:
            current_assignment = current_assignment.model_copy(
                update={"route_revision": changes["current_route_revision"]},
            )
        if "current_assignment" in changes:
            current_assignment = changes["current_assignment"]
        observation = settings.get("transport_observation")
        current = DispatchState(
            current_assignment, None if settings["admission"] is None else admission,
            cancelled=observation == "cancelled_before_dispatch",
            deadline_expired=observation == "deadline_expired_before_dispatch",
        )

        response = deepcopy(settings["response"])
        for field in ("status", "usage"):
            if field in changes:
                response[field] = changes[field]
        if "tool_arguments" in changes:
            response["output"][1]["arguments"] = changes["tool_arguments"]
        if "tool_name" in changes:
            response["output"][1]["name"] = changes["tool_name"]
        if changes.get("duplicate_call"):
            response["output"].append({**response["output"][1], "id": "e202-duplicate-item"})
        if "append_item_type" in changes:
            response["output"].append({"type": changes["append_item_type"], "id": "e202-unsupported-item"})

        sends: list[FakeInvocation] = []
        screened: list[tuple[str, str, bytes]] = []

        def transport(invocation: FakeInvocation) -> FakeResponse:
            sends.append(invocation)
            if observation == "timeout_after_possible_submission":
                raise PossibleSubmission("timeout")
            if observation == "cancelled_after_possible_submission":
                raise PossibleSubmission("cancelled")
            return FakeResponse(settings["transport_request_id"], response)

        def screen(profile: str, destination: str, body: bytes) -> bool:
            screened.append((profile, destination, body))
            return settings.get("final_body_grant", True)

        adapter = OfflineResponsesAdapter(transport)

        def invoke(
            owner=adapter, screen_body=screen, reader=lambda: current,
            request_override=request, attempt_override=settings["attempt_id"],
        ):
            return owner.invoke(
                request_override, context, attempt_id=attempt_override, profile=settings["profile"],
                destination=settings["destination"], read_current=reader, authorize_body=screen_body,
            )

        return settings, sends, screened, invoke

    def assert_expected(self, settings, expectation, result, sends, screened, invoke):
        semantic = expectation if isinstance(expectation, str) else expectation.get("disposition", "completed")
        self.assertEqual(result.disposition, _EXPECTED_DISPOSITIONS.get(semantic, semantic))
        if isinstance(expectation, dict) and "correlation" in expectation:
            intended = {"attempt_id": settings["attempt_id"], "reservation_ref": self.request.reservation_ref}
            for key in expectation["correlation"]:
                self.assertEqual(getattr(result.diagnostics, key), intended[key])

        if semantic == "completed" and isinstance(expectation, dict):
            body = json.loads(sends[0].body)
            context = json.loads(self.context.payload)
            self.assertEqual(body["instructions"], "\n".join(context["instructions"]))
            self.assertTrue(body["input"])
            self.assertNotIn("embedded_instruction", body["instructions"])
            self.assertEqual(body["model"], self.request.selected_model)
            self.assertEqual(body["max_output_tokens"], self.request.budget.max_output_tokens)
            self.assertEqual(sends[0].deadline_ms, self.request.budget.deadline_ms)
            self.assertNotIn("deadline_ms", body)
            d = result.diagnostics
            self.assertEqual((d.run_id, d.work_item_id, d.binding_sha256, d.attempt_id), (
                self.request.assignment.run_id, self.request.assignment.work_item_id,
                self.request.assignment.binding_sha256, settings["attempt_id"],
            ))
            self.assertEqual(d.transport_request_id, settings["transport_request_id"])
            self.assertEqual(d.response_id, settings["response"]["id"])
            self.assertIsInstance(result.items[1], ToolProposal)
            ids = [d.transport_request_id, d.response_id, result.items[0].item_id,
                   result.items[1].item_id, result.items[1].call_id]
            self.assertEqual(len(set(ids)), 5)
            def check_rerender(profile, destination, rendered):
                self.assertEqual((profile, destination, rendered), screened[0])
                return False

            rerender = invoke(screen_body=check_rerender)
            self.assertEqual(rerender.reason, "final_body_denied")
            self.assertEqual(rerender.diagnostics.request_sha256, d.request_sha256)
        elif semantic == "stable_order_and_typed_tool_proposal":
            self.assertEqual(result.items, (
                TextItem("e202-item-text-001", "text", "synthetic result"),
                ToolProposal("e202-item-call-002", "e202-call-009", "fixture_lookup", "synthetic"),
            ))
        elif semantic == "hold_invalid_proposal":
            self.assertEqual(result.items, ())
        elif semantic == "refusal":
            self.assertTrue(all(isinstance(item, TextItem) for item in result.items))
        elif semantic == "no_second_send":
            replay = invoke()
            self.assertEqual(replay.reason, "attempt_already_consumed")
        elif semantic == "controller_retry_advice_only":
            self.assertEqual(result.retry_after_seconds, 2)
        elif semantic in ("no_fallback", "no_redirect_or_forwarding", "no_retry", "unresolved_no_resend",
                          "unknown_remote_outcome", "no_submit"):
            self.assertIsNone(result.retry_after_seconds)
            observation = settings.get("transport_observation")
            if observation is not None:
                self.assertEqual(result.reason, observation)
        elif semantic == "observed_totals_with_nested_breakdowns":
            self.assertEqual(tuple(asdict(result.usage).values()), (8, 3, 11, 2, 1))
        elif semantic == "zeros_preserved":
            self.assertEqual(tuple(asdict(result.usage).values()), (0, 0, 0, None, None))
        elif semantic == "usage_unknown":
            self.assertEqual(tuple(asdict(result.usage).values()), (None,) * 5)
        elif semantic == "unreported_fields_unknown":
            self.assertEqual(tuple(asdict(result.usage).values()), (8, None, None, None, None))
        elif semantic == "reported_usage_preserved":
            self.assertEqual(tuple(asdict(result.usage).values()), (8, 0, 8, None, None))
        elif semantic == "same_attempt_and_receipt_identity_no_charge_or_reservation_release":
            observations = [result, deepcopy(result)]
            self.assertEqual(
                {item.observation_key for item in observations},
                {(self.request.assignment.run_id, settings["attempt_id"],
                  settings["transport_request_id"], settings["response"]["id"])},
            )
            self.assertEqual(result.diagnostics.reservation_ref, self.request.reservation_ref)
        elif semantic == "no_protected_outbound_fields":
            self.assertIn(b"E202_INPUT_CANARY", screened[0][2])
            self.assertEqual(sends, [])
        elif semantic == "keep_allowed_ids_status_code_exclude_canaries":
            self.assertEqual(result.diagnostics.transport_request_id, settings["transport_request_id"])
            self.assertEqual(result.diagnostics.http_status, 400)
            self.assertEqual(result.diagnostics.error_code, "invalid_request_error")
        elif semantic == "no_local_manifest_or_credential_in_provider_input_or_default_diagnostics":
            self.assertEqual(set(json.loads(sends[0].body)), {
                "instructions", "input", "model", "max_output_tokens", "tools",
            })
            self.assertNotIn(self.context.provenance, sends[0].body)
            self.assertNotIn(b"fixture-reservation", sends[0].body)

        diagnostic_text = json.dumps(asdict(result.diagnostics))
        for marker in ("E202_INPUT_CANARY", "E202_RAW_BODY_CANARY", "E202_HEADER_CANARY",
                       "Synthetic sky rating is clear", "Raw credentials"):
            self.assertNotIn(marker, diagnostic_text)
        if sends:
            self.assertEqual(result.diagnostics.request_sha256, sha256(sends[0].body).hexdigest())
        for sent in sends:
            self.assertIn((settings["profile"], settings["destination"], sent.body), screened)

    def run_case(self, family):
        for variant, changes, sends_expected, expectation in self.spec["cases"][family]:
            with self.subTest(variant=variant):
                settings, sends, screened, invoke = self.setup_variant(changes)
                result = invoke()
                self.assert_expected(settings, expectation, result, sends, screened, invoke)
                self.assertEqual(len(sends), 0 if sends_expected == "zero" else 1)
                print(json.dumps({
                    "case": family, "variant": variant, "fixture_sha256": _FROZEN_HASH,
                    "expected": expectation, "fake_sends_expected": sends_expected,
                    "fake_sends_observed": len(sends),
                    "observed_disposition": result.disposition, "reason": result.reason,
                    "diagnostics": asdict(result.diagnostics), "usage": asdict(result.usage),
                }, sort_keys=True))

    def test_e202_01_request_mapping(self):
        self.run_case("E202-01")

    def test_e202_02_preflight_and_single_attempt(self):
        self.run_case("E202-02")
        _, sends, _, invoke = self.setup_variant({})
        start = Barrier(2)

        def contend():
            start.wait(timeout=5)
            return invoke()

        with ThreadPoolExecutor(max_workers=2) as pool:
            contenders = [pool.submit(contend) for _ in range(2)]
            results = [item.result(timeout=5) for item in contenders]
        self.assertCountEqual([item.disposition for item in results], ("completed", "local_hold"))
        self.assertEqual(len(sends), 1)

        _, sends, _, invoke = self.setup_variant({})
        events = []

        def screen_after_revocation(*_):
            events.append("screened")
            return True

        def current_after_screening():
            events.append("rechecked")
            return DispatchState(None, None)

        held = invoke(screen_body=screen_after_revocation, reader=current_after_screening)
        self.assertEqual(events, ["screened", "rechecked"])
        self.assertEqual(held.reason, "missing_or_stale_admission")
        self.assertEqual(sends, [])

    def test_e202_03_response_and_proposals(self):
        self.run_case("E202-03")
        for status in ("incomplete", "failed"):
            _, _, _, invoke = self.setup_variant({"status": status})
            self.assertFalse(any(isinstance(item, ToolProposal) for item in invoke().items))
        _, _, _, invoke = self.setup_variant({"response": {"http": 200, "status": "completed"}})
        self.assertEqual(invoke().disposition, "unsupported_output")
        _, _, _, invoke = self.setup_variant({})
        invalid = OfflineResponsesAdapter(lambda _: FakeResponse("e202-fake-http", []))
        malformed = invoke(invalid)
        self.assertEqual(malformed.disposition, "unknown_remote_outcome")
        self.assertEqual(malformed.diagnostics.transport_request_id, "e202-fake-http")
        self.assertEqual(malformed.diagnostics.attempt_id, "e202-attempt-001")
        self.assertEqual(malformed.diagnostics.reservation_ref, self.request.reservation_ref)
        self.assertEqual(malformed.observation_key[2], "e202-fake-http")
        self.assertIsNone(malformed.diagnostics.response_id)

    def test_e202_04_errors_and_uncertainty(self):
        self.run_case("E202-04")
        _, _, _, invoke = self.setup_variant({})

        def unknown_transport_failure(_):
            raise RuntimeError("E202_RAW_BODY_CANARY")

        result = invoke(OfflineResponsesAdapter(unknown_transport_failure))
        self.assertEqual(result.disposition, "unknown_remote_outcome")
        self.assertEqual(result.reason, "fake_transport_raised")
        self.assertNotIn("E202_RAW_BODY_CANARY", repr(result))

    def test_e202_05_usage(self):
        self.run_case("E202-05")

    def test_e202_06_data_and_diagnostics(self):
        self.run_case("E202-06")

        canary = "E202_HEADER_CANARY"
        _, _, _, invoke = self.setup_variant({})
        response = deepcopy(self.defaults["response"])
        response.update(id=canary, model=canary)
        rejected = OfflineResponsesAdapter(lambda _: FakeResponse(canary, response))
        result = invoke(rejected)
        correlation = "sha256:" + sha256(canary.encode()).hexdigest()
        self.assertNotIn(canary, json.dumps(asdict(result.diagnostics)))
        self.assertEqual(result.diagnostics.transport_request_id, correlation)
        self.assertEqual(result.diagnostics.response_id, correlation)
        self.assertEqual(result.diagnostics.observed_model, correlation)

        _, sends, _, invoke = self.setup_variant({})
        caller_canary = "E202_CALLER_METADATA!"
        untrusted_assignment = self.request.assignment.model_copy(
            update={"run_id": caller_canary, "work_item_id": caller_canary},
        )
        untrusted_request = self.request.model_copy(
            update={"assignment": untrusted_assignment, "reservation_ref": caller_canary},
        )
        result = invoke(request_override=untrusted_request, attempt_override=caller_canary)
        self.assertEqual(result.disposition, "local_hold")
        self.assertEqual(sends, [])
        diagnostic = asdict(result.diagnostics)
        self.assertNotIn(caller_canary, json.dumps(diagnostic))
        expected = "sha256:" + sha256(caller_canary.encode()).hexdigest()
        for key in ("run_id", "work_item_id", "attempt_id", "reservation_ref"):
            self.assertEqual(diagnostic[key], expected)

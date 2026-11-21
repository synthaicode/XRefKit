"""Fixed #205 evidence cases; exercises only the deterministic evaluator."""

from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import unittest

import test_offline_dispatch
import test_offline_responses

from xrefkit_openai_runtime.contracts import AssignmentRef, ExecutionEvent, ExecutionRequest, ExecutionResult
from xrefkit_openai_runtime.offline_dispatch import ToolAttemptEvidence, ToolCorrelation, ToolDecision, ToolReceipt
from xrefkit_openai_runtime.offline_evaluation import (
    EffectObservation, EvaluationInputs, EvaluationPolicy, ReevaluationLink,
    ReplayAuthorization, RevisionLinks, ReviewAuthority, SemanticReview, api_observation_digest, effective_rules_digest,
    evaluate_io, evaluation_digest, evidence_digest, project_interaction, reevaluate_io,
    tool_observation_digest, trace_pins,
)
from xrefkit_openai_runtime.offline_responses import AdapterResult, AttemptDiagnostics, TextItem, UsageObservation


_FIXTURE_SHA256 = "59e4aa50166dd059ff9852cac8c269a7ad135eca48dc703a4bddcedac15e02c1"


def _sha(content: bytes) -> str:
    return sha256(content).hexdigest()


def _encode(value: object, *, ascii_only: bool = False) -> bytes:
    return json.dumps(value, ensure_ascii=ascii_only, sort_keys=True, separators=(",", ":")).encode()


def _refs(record: dict) -> RevisionLinks:
    keys = ("request_revision", "result_revision", "tool_receipt_revision", "criteria_revision",
            "criteria_sha256", "evidence_revision")
    correlation = record["correlation"]
    return RevisionLinks(*(record[key] for key in keys), (
        correlation["attempt_id"], correlation["operation_id"], correlation["call_id"],
    ))


def _replace_at(document: dict, path: str, value: object) -> None:
    target = document
    *parts, leaf = path.removeprefix("/").split("/")
    for part in parts:
        target = target[int(part)] if isinstance(target, list) else target[part]
    if isinstance(target, list):
        index = int(leaf)
        if index == len(target):
            target.append(value)
        else:
            target[index] = value
    else:
        target[leaf] = value


class OfflineEvaluationCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = Path(__file__).parent / "fixtures" / "e205-fixtures-r1" / "cases.json"
        raw = fixture.read_bytes()
        if _sha(raw) != _FIXTURE_SHA256:
            raise ValueError("e205-fixtures-r1 bytes changed")
        cls.fixture = json.loads(raw)
        if cls.fixture["revision"] != "e205-fixtures-r1":
            raise ValueError("unexpected fixture revision")
        for name, body in cls.fixture["rubrics"].items():
            if _sha(_encode(body)) != cls.fixture["rubric_sha256"][name]:
                raise ValueError(f"rubric pin changed: {name}")

    def resolve(self, value, document=None):
        if isinstance(value, dict):
            return {key: self.resolve(item, document) for key, item in value.items()}
        if isinstance(value, list):
            return [self.resolve(item, document) for item in value]
        if not isinstance(value, str) or not value.startswith("@"):
            return value
        marker, _, name = value.partition(":")
        if marker == "@sha":
            return _sha(name.encode())
        if marker == "@jsonsha":
            return _sha(_encode(name, ascii_only=True))
        if marker == "@rubric":
            return self.fixture["rubric_sha256"][name]
        if marker == "@record" and document is not None:
            record = document[name]
            return _sha(record.encode() if isinstance(record, str) else _encode(record))
        if marker == "@record":
            return value
        raise ValueError(f"Unknown fixture marker {marker}")

    def records(self, replacements=()):
        document = deepcopy(self.fixture["defaults"])
        for path, value in replacements:
            _replace_at(document, path, value)
        expanded = self.resolve(document)
        return self.resolve(expanded, expanded)

    def run_case(self, changes, *, rubric_version="rubric-r1", original_changes=(),
                 evaluation_ref="evaluation-205-r1", previous=None):
        original = self.records(original_changes)
        observed = self.records(tuple(original_changes) + tuple(changes))
        api, tool = observed["api"], observed["tool"]
        receipt, frozen_receipt = tool["receipt"], original["tool"]["receipt"]
        typed_receipt = (ToolReceipt(**{**receipt, "correlation": ToolCorrelation(**receipt["correlation"])})
                         if receipt is not None else None)
        attempt_effect = tool["evidence"]["effect"]
        attempt_evidence = ToolAttemptEvidence(
            ToolCorrelation(**frozen_receipt["correlation"]), frozen_receipt["action_digest"],
            _sha(b"synthetic-proposal"), _sha(b"synthetic-arguments"), _sha(b"synthetic-target"),
            _sha(b"synthetic-destination"), attempt_effect,
        )
        interaction = observed["interaction"]
        reference = project_interaction(interaction) if interaction is not None else None
        request = ExecutionRequest.model_validate(observed["request"])
        events = tuple(ExecutionEvent.model_validate(event) for event in observed["events"])
        # The fixture host seals the received V1 records under the declared current authority.
        # An unsupported version is passed raw for evaluator rejection; it cannot become a V1 pin.
        trace_record = observed["result"] if observed["result"]["version"] == 1 else original["result"]
        v1_pins = trace_pins(request, events, ExecutionResult.model_validate(trace_record))
        postconditions = tuple(EffectObservation(**proof) for proof in observed["postconditions"])

        original_result = ExecutionResult.model_validate(original["result"])
        review_basis = {original_result.evidence_ref: _sha(_encode(original_result.model_dump(mode="json")))}
        review_basis.update((proof["ref"], evidence_digest(EffectObservation(**proof)))
                            for proof in original["postconditions"])
        if original["interaction"] is not None:
            original_ref = project_interaction(original["interaction"])
            review_basis[original_ref.ref] = evidence_digest(original_ref)
        reviews = tuple(SemanticReview(
            data["id"], data["role"], data["authorized"], data["context"], data["author_context"],
            _refs(data), data["output_sha256"], data["verdict"], tuple(data["basis_refs"]), data["rationale"],
            tuple(review_basis.get(ref, "") for ref in data["basis_refs"]),
        ) for data in observed["reviewers"])
        output = observed["output_utf8"].encode()
        items = (TextItem("output-205", "text", observed["output_utf8"]),) if api["disposition"] == "completed" else ()
        inputs = EvaluationInputs(
            request=request, events=events, result=observed["result"], links=_refs(observed["revision_links"]),
            api=AdapterResult(api["disposition"], api["reason"], AttemptDiagnostics(**api["diagnostics"]),
                              UsageObservation(**(api["usage"] or {})), items),
            tool=ToolDecision(tool["outcome"], tool["reason"], typed_receipt, tool["value"], attempt_evidence),
            output_utf8=output, tool_return_utf8=observed["tool_return_utf8"].encode(),
            recorded_tool_effect=attempt_effect, postconditions=postconditions, interaction=interaction,
            reviews=reviews, reevaluation=ReevaluationLink(**observed["reevaluation"]) if observed["reevaluation"] else None,
        )
        rubric = self.fixture["rubrics"][rubric_version]
        authorities = (ReviewAuthority("reviewer-a", "review-context-a"), ReviewAuthority("reviewer-b", "review-context-b"))
        policy = EvaluationPolicy(
            assignment=AssignmentRef.model_validate(observed["active_assignment"]),
            links=_refs(original["revision_links"]),
            api_request_sha256=_sha(_encode(observed["request"])),
            api_observation_sha256=api_observation_digest(inputs.api),
            tool_observation_sha256=tool_observation_digest(inputs.tool, inputs.recorded_tool_effect),
            output_sha256=_sha(output), trace_pins=v1_pins, rubric_utf8=_encode(rubric), approved_rules_sha256="",
            provider_reservation_ref=original["request"]["reservation_ref"],
            effect_observation_pins=tuple(evidence_digest(proof) for proof in postconditions),
            interaction_pin=evidence_digest(reference) if reference is not None else None,
            reviewer_record_pins=tuple(evidence_digest(review) for review in reviews),
            expected_model=original["request"]["selected_model"],
            expected_postcondition=rubric["expected_postcondition"] if observed["postcondition_required"] else None,
            output_byte_limit=96,
            producer=original["producer"], producer_context="producer-context", reviewers=authorities,
            trusted_readback_origins=frozenset({"independent-fixture-readback", "independent-fixture-readback-b"}),
            usage_required_fields=frozenset(observed["usage_required_fields"]),
            interaction_required=observed["interaction_required"], semantic_required=observed["semantic_required"],
            rubric_successor=("rubric-r2", self.fixture["rubric_sha256"]["rubric-r2"]),
            prior_evaluation_ref="evaluation-205-r1", evaluation_ref=evaluation_ref,
            previous_evaluation_pin=evaluation_digest(previous) if previous is not None else None,
            tool_authorization_digests=tuple(frozen_receipt["correlation"][field]
                for field in ("policy_digest", "grant_digest", "reservation_digest")),
        )
        policy = replace(policy, approved_rules_sha256=effective_rules_digest(policy))
        return evaluate_io(policy, inputs), observed, inputs, policy

    def run_group(self, case: str):
        for variant, changes, expected, assertions in self.fixture["cases"][case]:
            with self.subTest(variant=variant):
                result, raw, inputs, policy = self.run_case(changes)
                checks = {check.id: check for check in result.criteria}
                check = checks[assertions["criterion"]]
                actual = [check.outcome, check.reason]
                self.assertEqual(actual, expected)
                if check.reason in ("review_rubric_mismatch", "review_result_mismatch", "review_evidence_mismatch"):
                    self.assertNotEqual(*check.comparison_sha256)
                known = asdict(result.usage)
                optional = {
                    "aggregate": result.aggregate, "v1": result.v1_assessment,
                    "structure": checks["structure"].outcome if "structure" in checks else None,
                    "review_state": result.review_state, "api_outcome": result.api_outcome,
                    "tool_outcome": result.tool_outcome, "entry_observed": result.entry_observed,
                    "next": result.next_proposal if check.id == "aggregate" else check.next_check,
                    "human_acceptance": result.human_acceptance,
                    "allow_repeat": result.allow_repeat, "handoff": list(result.handoff_targets),
                }
                for key in assertions.keys() & optional.keys():
                    self.assertEqual(optional[key], assertions[key], key)
                if "retained_usage" in assertions:
                    self.assertEqual({key: known[key] for key in assertions["retained_usage"]},
                                     assertions["retained_usage"])
                if "evidence_refs" in assertions:
                    self.assertEqual(check.evidence_refs,
                                     tuple(_sha(_encode(ref, ascii_only=True)) for ref in assertions["evidence_refs"]))
                if "retained_reviewers" in assertions:
                    self.assertEqual(result.retained_reviewers,
                                     tuple(_sha(_encode(ref, ascii_only=True)) for ref in assertions["retained_reviewers"]))
                if "semantic_review_input" in assertions:
                    self.assertEqual(inputs.reviews[0].verdict, assertions["semantic_review_input"])
                if "old_evaluation_unchanged" in assertions:
                    self.assertEqual((result.criteria_revision, result.criteria_sha256),
                                     (policy.links.criteria_revision, policy.links.criteria_sha256))
                if "old_revision" in assertions:
                    self.assertEqual(result.criteria_revision, assertions["old_revision"])
                    self.assertEqual(inputs.reevaluation.new_criteria_revision, assertions["new_revision"])
                self.assertIsNone(result.human_acceptance)
                self.assertEqual(result.output_sha256, _sha(inputs.output_utf8))
                proof = {
                    "case": case, "variant": variant, "expected": expected, "observed": actual,
                    "fixture_sha256": _FIXTURE_SHA256, "evaluation": asdict(result),
                    "source_correlation_sha256": _sha(_encode(raw["revision_links"])),
                    "approved_policy_sha256": result.approved_policy_sha256,
                    "api_observation_sha256": policy.api_observation_sha256,
                    "tool_observation_sha256": policy.tool_observation_sha256,
                    "evaluator_side_effects": "none",
                }
                if variant == "wrong-tool-call":
                    self.assertEqual((result.api_outcome, result.tool_outcome), ("completed", "unverified"))
                    self.assertEqual(result.usage, inputs.api.usage)
                if variant == "wrong-api-attempt":
                    self.assertEqual((result.api_outcome, result.tool_outcome), ("unverified", "executed"))
                    self.assertTrue(result.entry_observed)
                if inputs.reevaluation is not None:
                    proof["verified_successor"] = self.check_reevaluation(inputs.reevaluation)
                if variant == "exact-trace":
                    proof["upstream_controls"] = self.verify_native_observations()
                serialized = json.dumps(proof)
                for canary in assertions.get("ordinary_output_excludes", []):
                    self.assertEqual(inputs.interaction["fixture_forbidden_content"], canary)
                    self.assertNotIn(canary, json.dumps(asdict(project_interaction(inputs.interaction))))
                    self.assertNotIn(canary, serialized)
                print(serialized)

    def test_E205_01_identity(self):
        self.run_group("E205-01")
        _, _, inputs, policy = self.run_case(())
        # A payload or source observation replaced after trusted intake is not a current artifact.
        substituted = evaluate_io(policy, replace(inputs, output_utf8=b'{"objective":"other"}'))
        self.assertEqual(substituted.criteria[0].reason, "api_output_unlinked")
        modified = evaluate_io(policy, replace(inputs, api=replace(inputs.api, disposition="refusal")))
        self.assertEqual(modified.criteria[0].reason, "api_observation_digest_mismatch")

        receipt = inputs.tool.receipt
        digest = "f" * 64
        evidence = ToolAttemptEvidence(receipt.correlation, receipt.action_digest,
                                       digest, digest, digest, digest, "none")
        denied = replace(inputs.tool, outcome="deny", reason="command_not_allowed",
                         receipt=None, evidence=evidence, value=None)
        denied_input = replace(inputs, tool=denied, recorded_tool_effect="none")
        denied_policy = replace(policy, tool_observation_sha256=tool_observation_digest(denied, "none"))
        self.assertEqual(evaluate_io(denied_policy, denied_input).criteria[0].outcome, "pass")

        unrelated = replace(denied, evidence=replace(evidence, correlation=replace(
            evidence.correlation, operation_digest=digest,
        )))
        unrelated_policy = replace(policy, tool_observation_sha256=tool_observation_digest(unrelated, "none"))
        result = evaluate_io(unrelated_policy, replace(denied_input, tool=unrelated))
        self.assertEqual((result.criteria[0].outcome, result.criteria[0].reason),
                         ("unresolved", "operation_uncorrelated"))

        contradictory = replace(inputs.tool, evidence=evidence)
        contradictory_policy = replace(
            policy, tool_observation_sha256=tool_observation_digest(contradictory, None),
        )
        result = evaluate_io(contradictory_policy, replace(inputs, tool=contradictory, recorded_tool_effect=None))
        self.assertEqual(result.criteria[0].reason, "tool_attempt_receipt_conflict")
        self.assertEqual(result.next_proposal, "reconcile")

        # The immutable pins cover record contents, not merely their revision labels.
        modified_request = replace(inputs, request=inputs.request.model_copy(update={"authorization_ref": "other"}))
        changed_events = replace(inputs, events=(inputs.events[0].model_copy(update={"kind": "held"}), *inputs.events[1:]))
        changed_result = replace(inputs, result={**inputs.result, "evidence_ref": "different-v1-ref"})
        for candidate in (modified_request, changed_events, changed_result):
            checked = evaluate_io(policy, candidate)
            self.assertEqual(checked.criteria[0].reason, "trace_content_unpinned")
            self.assertEqual(checked.aggregate, "criteria_unresolved")
        changed_scope = evaluate_io(replace(policy, output_byte_limit=512), inputs)
        self.assertEqual(changed_scope.criteria[0].reason, "effective_rubric_unpinned")
        self.assertEqual(changed_scope.aggregate, "criteria_unresolved")

        # Unlinked Tool records do not erase separately verified API usage.
        result = evaluate_io(unrelated_policy, replace(denied_input, tool=unrelated))
        self.assertEqual((result.api_outcome, result.tool_outcome), ("completed", "unverified"))
        self.assertEqual(result.usage, inputs.api.usage)
        # Neither an absent receipt nor an absent attempt can substantiate a trusted denial.
        missing = replace(denied, evidence=None)
        missing_policy = replace(policy, tool_observation_sha256=tool_observation_digest(missing, "none"))
        result = evaluate_io(missing_policy, replace(denied_input, tool=missing))
        self.assertEqual(result.criteria[0].reason, "tool_attempt_evidence_missing")
        self.assertEqual(result.aggregate, "criteria_unresolved")
        # Unlinked API records must not erase the accepted Tool's possible-effect hold.
        possible = replace(receipt, outcome="effect_unknown", effect="unknown", result_digest=None)
        held = replace(inputs.tool, outcome="hold", receipt=possible, value=None,
                       evidence=replace(evidence, effect="unknown"))
        held_policy = replace(policy, tool_observation_sha256=tool_observation_digest(held, "unknown"))
        bad_api = replace(inputs.api, diagnostics=replace(inputs.api.diagnostics, attempt_id="wrong"))
        result = evaluate_io(held_policy, replace(inputs, api=bad_api, tool=held, recorded_tool_effect="unknown"))
        self.assertEqual((result.api_outcome, result.tool_outcome, result.tool_effect), ("unverified", "hold", "unknown"))
        self.assertEqual(result.usage, UsageObservation())
        self.assertEqual(result.next_proposal, "reconcile")

    def test_E205_02_structure_and_outcomes(self):
        self.run_group("E205-02")
        failure, _, _, _ = self.run_case((
            ("/output_utf8", '{"objective":'),
            ("/tool/receipt/correlation/call_digest", "@jsonsha:other-call"),
        ))
        checks = {check.id: check for check in failure.criteria}
        self.assertEqual((checks["structure"].outcome, checks["structure"].reason), ("fail", "invalid_json"))
        self.assertEqual(failure.aggregate, "criteria_failed")

        failure, _, _, _ = self.run_case((
            ("/api/diagnostics/attempt_id", "attempt-other"),
            ("/tool/outcome", "deny"),
            ("/tool/receipt", None),
            ("/tool/evidence/effect", "none"),
        ))
        checks = {check.id: check for check in failure.criteria}
        self.assertEqual(checks["outcome"].reason, "tool_denied")
        self.assertEqual(failure.aggregate, "criteria_failed")

        failure, _, _, _ = self.run_case((
            ("/active_assignment/route_revision", 2),
            ("/api/diagnostics/attempt_id", "attempt-other"),
            ("/tool/receipt/correlation/call_digest", "@jsonsha:other-call"),
        ))
        self.assertEqual({item.id: item.reason for item in failure.source_findings}, {
            "v1_identity": "assignment_not_current", "api_identity": "attempt_uncorrelated",
            "tool_identity": "call_uncorrelated",
        })
        self.assertTrue(all(item.comparison_sha256[0] != item.comparison_sha256[1]
                            for item in failure.source_findings))

    def test_E205_03_effect_evidence(self):
        self.run_group("E205-03")

    def test_E205_04_usage_and_references(self):
        self.run_group("E205-04")

    def test_E205_05_independent_review(self):
        self.run_group("E205-05")
        result, _, inputs, policy = self.run_case((("/postconditions/0/observed", "synthetic-absent"),))
        criteria = {check.id: check for check in result.criteria}
        self.assertEqual(criteria["semantic"].reason, "review_basis_changed")
        self.assertEqual(criteria["effect"].outcome, "fail")
        self.assertEqual(result.aggregate, "criteria_failed")
        self.assertEqual(result.review_state, "pending")
        _, _, inputs, policy = self.run_case((("/interaction_required", True),))
        reference = project_interaction(inputs.interaction)
        for changed in (
            replace(reference, ref="substituted"), replace(reference, access="blocked"),
            replace(reference, status="redacted_insufficient"), replace(reference, revision="evidence-r0"),
        ):
            result = evaluate_io(policy, replace(inputs, interaction=changed))
            criteria = {check.id: check for check in result.criteria}
            self.assertEqual(criteria["interaction"].reason, "interaction_snapshot_unpinned")
            self.assertEqual(result.usage, inputs.api.usage)
        reviewer = replace(inputs.reviews[0], rationale="substituted under the same reviewer identity")
        result = evaluate_io(policy, replace(inputs, reviews=(reviewer,)))
        self.assertEqual({check.id: check for check in result.criteria}["semantic"].reason,
                         "review_record_unpinned")

    def test_E205_06_aggregation_and_handoff(self):
        self.run_group("E205-06")

    def check_reevaluation(self, link):
        prior, _, _, _ = self.run_case(())
        prior_digest = evaluation_digest(prior)
        revisions = (
            ("/request/criteria_sha256", "@rubric:rubric-r2"),
            ("/revision_links/criteria_revision", "rubric-r2"),
            ("/revision_links/criteria_sha256", "@rubric:rubric-r2"),
            ("/reviewers/0/criteria_revision", "rubric-r2"),
            ("/reviewers/0/criteria_sha256", "@rubric:rubric-r2"),
            ("/postconditions/0/observed", "synthetic-revised"),
            ("/output_utf8", '{"objective":"synthetic-revised"}'),
        )
        _, _, inputs, policy = self.run_case(
            (), rubric_version="rubric-r2", original_changes=revisions,
            evaluation_ref="evaluation-205-r2", previous=prior,
        )
        direct = evaluate_io(policy, inputs)
        self.assertEqual(direct.criteria[0].reason, "reevaluation_link_required")
        self.assertEqual(direct.aggregate, "criteria_unresolved")
        without_previous_pin = evaluate_io(replace(policy, previous_evaluation_pin=None), inputs)
        self.assertEqual(without_previous_pin.aggregate, "criteria_unresolved")
        latest = reevaluate_io(prior, link, policy, inputs)
        self.assertEqual(latest.aggregate, "criteria_met")
        self.assertEqual(latest.criteria_revision, "rubric-r2")
        self.assertEqual(latest.reevaluation_from, prior.evaluation_ref)
        self.assertEqual(latest.evaluation_ref, "evaluation-205-r2")
        self.assertNotEqual(latest.output_sha256, prior.output_sha256)
        self.assertEqual(prior.criteria_revision, "rubric-r1")
        self.assertEqual(evaluation_digest(prior), prior_digest)
        with self.assertRaises(ValueError):
            reevaluate_io(prior, replace(link, new_evaluation_ref="unapproved"), policy, inputs)
        return {
            "prior_sha256": prior_digest, "prior_unchanged": True,
            "successor_sha256": evaluation_digest(latest), "successor_criteria_sha256": latest.criteria_sha256,
            "successor_aggregate": latest.aggregate, "successor_human_acceptance": latest.human_acceptance,
            "direct_aggregate": direct.aggregate, "direct_reason": direct.criteria[0].reason,
        }

    def verify_native_observations(self):
        _, _, inputs, policy = self.run_case(())
        api_harness = test_offline_responses.OfflineResponsesTests()
        api_harness.setUpClass()
        settings, sends, _, invoke = api_harness.setup_variant({})
        api = invoke()
        self.assertEqual((api.disposition, len(sends)), ("completed", 1))
        output = "".join(item.text for item in api.items if isinstance(item, TextItem) and item.kind == "text").encode()
        self.assertTrue(output)
        wire_digest = _sha(sends[0].body)
        self.assertEqual(api.diagnostics.request_sha256, wire_digest)
        attempt, operation, call = policy.links.correlation
        api_policy = replace(
            policy, assignment=api_harness.request.assignment,
            links=replace(policy.links, correlation=(settings["attempt_id"], operation, call)),
            provider_reservation_ref=api_harness.request.reservation_ref, api_request_sha256=wire_digest,
            api_observation_sha256=api_observation_digest(api), output_sha256=_sha(output),
        )
        checked = evaluate_io(api_policy, replace(inputs, api=api, output_utf8=output))
        self.assertEqual(checked.source_findings[1].outcome, "pass")
        self.assertEqual(checked.usage, api.usage)

        dispatch = test_offline_dispatch.OfflineDispatchTests()
        dispatch.setUpClass()
        later = dispatch.request({"attempt": "attempt-2", "provider_call": "call-2",
                                  "grant": "grant-2", "reservation": "reservation-2"})
        dispatcher, host, base = dispatch.setup_case(additional=(later,))
        first = dispatch.invoke(dispatcher, base)
        replay = dispatch.invoke(dispatcher, later)
        self.assertEqual((first.outcome, replay.outcome, dispatcher.snapshot(later).entry_count),
                         ("executed", "replay", 1))
        self.assertEqual(first.receipt, replay.receipt)
        authorized_action = next(grant.action for grant in host.authority.grants
                                 if grant.action.authorization_ref == later.grant)
        digests = tuple(_sha(_encode(ref, ascii_only=True)) for ref in (
            authorized_action.policy_revision, authorized_action.authorization_ref, authorized_action.reservation_id,
        ))
        scope = _sha(_encode(host.return_scope.pin))
        seal = ReplayAuthorization(first.receipt.correlation, replay.evidence.correlation, scope)
        tool_assignment = policy.assignment.model_copy(update={
            "run_id": later.run, "work_item_id": later.work, "route_id": later.route,
            "owner_generation": later.generation,
        })
        tool_policy = replace(
            policy, assignment=tool_assignment, links=replace(
                policy.links, correlation=(later.attempt, later.operation_id, later.provider_call),
            ), tool_observation_sha256=tool_observation_digest(replay, "observed"),
            tool_authorization_digests=digests, replay_authorization=seal,
        )
        native_return_bytes = test_offline_dispatch.encode(dispatch.defaults["fake_result"])
        tool_inputs = replace(inputs, tool=replay, tool_return_utf8=native_return_bytes,
                              recorded_tool_effect="observed", tool_return_scope_sha256=scope)
        checked_tool = evaluate_io(tool_policy, tool_inputs)
        self.assertEqual((checked_tool.source_findings[2].outcome, checked_tool.tool_outcome), ("pass", "replay"))
        invalid_scope = evaluate_io(tool_policy, replace(tool_inputs, tool_return_scope_sha256="a" * 64))
        self.assertEqual(invalid_scope.source_findings[2].reason, "tool_replay_authorization_unverified")
        for key in ("policy_digest", "grant_digest", "reservation_digest"):
            amended = replace(replay.evidence.correlation, **{key: "0" * 64})
            wrong = replace(replay, evidence=replace(replay.evidence, correlation=amended))
            wrong_policy = replace(tool_policy, tool_observation_sha256=tool_observation_digest(wrong, "observed"))
            rejected = evaluate_io(wrong_policy, replace(tool_inputs, tool=wrong))
            self.assertEqual(rejected.source_findings[2].reason, "tool_replay_authorization_unverified")
        return {
            "adapter_wire_sha256": wire_digest, "adapter_evaluation": checked.source_findings[1].outcome,
            "dispatch_entries": dispatcher.snapshot(later).entry_count,
            "replay_evaluation": checked_tool.source_findings[2].outcome,
            "replay_scope_sha256": scope, "changed_replay_scope": invalid_scope.source_findings[2].reason,
        }

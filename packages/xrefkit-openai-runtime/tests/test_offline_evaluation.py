"""Fixed #205 evidence cases; exercises only the deterministic evaluator."""

from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import unittest

from xrefkit_openai_runtime.contracts import AssignmentRef, ExecutionEvent, ExecutionRequest
from xrefkit_openai_runtime.offline_dispatch import ToolAttemptEvidence, ToolCorrelation, ToolDecision, ToolReceipt
from xrefkit_openai_runtime.offline_evaluation import (
    EffectObservation, EvaluationInputs, EvaluationPolicy, InteractionReference, ReevaluationLink,
    RevisionLinks, ReviewAuthority, SemanticReview, api_observation_digest, evaluate_io, tool_observation_digest,
)
from xrefkit_openai_runtime.offline_responses import AdapterResult, AttemptDiagnostics, UsageObservation


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

    def run_case(self, changes):
        original = self.records()
        observed = self.records(changes)
        api = observed["api"]
        tool = observed["tool"]
        receipt = tool["receipt"]
        typed_receipt = (ToolReceipt(**{**receipt, "correlation": ToolCorrelation(**receipt["correlation"])})
                         if receipt is not None else None)
        external_ref = observed["interaction"]
        reference = (InteractionReference(*(external_ref[key] for key in
                     ("ref", "revision", "attempt_id", "access", "status", "origin")))
                     if external_ref is not None else None)
        reviews = tuple(SemanticReview(
            data["id"], data["role"], data["authorized"], data["context"], data["author_context"],
            _refs(data), data["output_sha256"], data["verdict"], tuple(data["basis_refs"]), data["rationale"],
        ) for data in observed["reviewers"])
        output = observed["output_utf8"].encode()
        inputs = EvaluationInputs(
            request=ExecutionRequest.model_validate(observed["request"]),
            events=tuple(ExecutionEvent.model_validate(event) for event in observed["events"]),
            result=observed["result"],
            links=_refs(observed["revision_links"]),
            api=AdapterResult(api["disposition"], api["reason"], AttemptDiagnostics(**api["diagnostics"]),
                              UsageObservation(**(api["usage"] or {}))),
            tool=ToolDecision(tool["outcome"], tool["reason"], typed_receipt, tool["value"]),
            output_utf8=output,
            tool_return_utf8=observed["tool_return_utf8"].encode(),
            recorded_tool_effect=tool["evidence"]["effect"],
            postconditions=tuple(EffectObservation(**proof) for proof in observed["postconditions"]),
            interaction=reference,
            reviews=reviews,
            reevaluation=ReevaluationLink(**observed["reevaluation"]) if observed["reevaluation"] else None,
        )
        rubric = self.fixture["rubrics"]["rubric-r1"]
        # Test host supplies an independent policy record. Only declared scope switches are case inputs.
        # The host pins the exact received request and artifact bytes independently of claimed source digests.
        authorities = (ReviewAuthority("reviewer-a", "review-context-a"), ReviewAuthority("reviewer-b", "review-context-b"))
        policy = EvaluationPolicy(
            assignment=AssignmentRef.model_validate(observed["active_assignment"]),
            links=_refs(original["revision_links"]),
            api_request_sha256=_sha(_encode(observed["request"])),
            api_observation_sha256=api_observation_digest(inputs.api),
            tool_observation_sha256=tool_observation_digest(inputs.tool, inputs.recorded_tool_effect),
            output_sha256=_sha(output),
            expected_model=original["request"]["selected_model"],
            expected_postcondition=rubric["expected_postcondition"] if observed["postcondition_required"] else None,
            output_byte_limit=96,
            producer=original["producer"],
            producer_context="producer-context",
            reviewers=authorities,
            trusted_readback_origins=frozenset({"independent-fixture-readback", "independent-fixture-readback-b"}),
            usage_required_fields=frozenset(observed["usage_required_fields"]),
            interaction_required=observed["interaction_required"],
            semantic_required=observed["semantic_required"],
            rubric_successor=("rubric-r2", self.fixture["rubric_sha256"]["rubric-r2"]),
            prior_evaluation_ref="evaluation-205-r1",
        )
        evaluation = evaluate_io(policy, inputs)
        return evaluation, observed, inputs, policy

    def run_group(self, case: str):
        for variant, changes, expected, assertions in self.fixture["cases"][case]:
            with self.subTest(variant=variant):
                result, raw, inputs, policy = self.run_case(changes)
                checks = {check.id: check for check in result.criteria}
                check = checks[assertions["criterion"]]
                actual = [check.outcome, check.reason]
                self.assertEqual(actual, expected)
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
                    "approved_policy_sha256": _sha(_encode(asdict(policy.links))),
                    "api_observation_sha256": policy.api_observation_sha256,
                    "tool_observation_sha256": policy.tool_observation_sha256,
                    "evaluator_side_effects": "none",
                }
                serialized = json.dumps(proof)
                for canary in assertions.get("ordinary_output_excludes", []):
                    self.assertNotIn(canary, serialized)
                print(serialized)

    def test_E205_01_identity(self):
        self.run_group("E205-01")
        _, _, inputs, policy = self.run_case(())
        # A payload or source observation replaced after trusted intake is not a current artifact.
        substituted = evaluate_io(policy, replace(inputs, output_utf8=b'{"objective":"other"}'))
        self.assertEqual(substituted.criteria[0].reason, "result_digest_mismatch")
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

        prior = replace(receipt, correlation=replace(
            receipt.correlation, call_digest=_sha(_encode("call-prior", ascii_only=True)),
        ))
        replay = replace(inputs.tool, outcome="replay", receipt=prior, evidence=replace(evidence, effect="observed"))
        replay_input = replace(inputs, tool=replay)
        replay_policy = replace(policy, tool_observation_sha256=tool_observation_digest(replay, "observed"))
        self.assertEqual(evaluate_io(replay_policy, replay_input).criteria[0].reason, "call_uncorrelated")
        linked = replace(replay_policy, replay_receipt_refs=("attempt-205", "call-prior"))
        self.assertEqual(evaluate_io(linked, replay_input).criteria[0].outcome, "pass")

    def test_E205_02_structure_and_outcomes(self):
        self.run_group("E205-02")

    def test_E205_03_effect_evidence(self):
        self.run_group("E205-03")

    def test_E205_04_usage_and_references(self):
        self.run_group("E205-04")

    def test_E205_05_independent_review(self):
        self.run_group("E205-05")

    def test_E205_06_aggregation_and_handoff(self):
        self.run_group("E205-06")

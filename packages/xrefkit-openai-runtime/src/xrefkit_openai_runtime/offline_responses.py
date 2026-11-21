"""A Responses-style adapter for the synthetic in-process execution slice."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from hashlib import sha256
import json
import re
from threading import Lock
from typing import Literal

from .contracts import AssignmentRef, ExecutionRequest
from .offline_context import ContextAssembly


FIXTURE_PROFILE = "e202-fake-only"
FIXTURE_DESTINATION = "https://e202-provider.invalid/v1/responses"
FIXTURE_MODEL = "synthetic-model"
FIXTURE_TOOL = "fixture_lookup"

_IDENTIFIER = re.compile(r"[a-zA-Z0-9_-]{1,128}")
_BINDING_DIGEST = re.compile(r"[a-f0-9]{64}")
_TRANSPORT_REQUEST_IDS = ("e202-http-request-001", "e202-fake-http")
_RESPONSE_IDS = ("e202-response-001",)
_ERROR_CODES = frozenset({
    "invalid_request_error", "invalid_api_key", "insufficient_quota",
    "rate_limit_exceeded", "model_not_found",
})
_TOOL_CONTEXT_FIELDS = frozenset({"source", "observation", "embedded_instruction"})


@dataclass(frozen=True)
class Admission:
    assignment: AssignmentRef
    attempt_id: str
    authorization_ref: str
    reservation_ref: str
    context_sha256: str
    provenance_sha256: str
    consumed: bool = False


@dataclass(frozen=True)
class DispatchState:
    assignment: AssignmentRef | None
    admission: Admission | None
    cancelled: bool = False
    deadline_expired: bool = False


@dataclass(frozen=True)
class FakeInvocation:
    """Only data for the injected in-process fake reaches this boundary."""

    body: bytes
    deadline_ms: int


@dataclass(frozen=True)
class FakeResponse:
    request_id: str | None
    body: Mapping[str, object]


class PossibleSubmission(Exception):
    """A synthetic observation with no proof that the originating call had no effect."""

    def __init__(self, kind: Literal["timeout", "cancelled"]) -> None:
        super().__init__(kind)
        self.kind = kind


@dataclass(frozen=True)
class UsageObservation:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cached_input_tokens: int | None = None
    reasoning_output_tokens: int | None = None


@dataclass(frozen=True)
class TextItem:
    item_id: str
    kind: Literal["text", "refusal"]
    text: str


@dataclass(frozen=True)
class ToolProposal:
    item_id: str
    call_id: str
    name: str
    query: str


@dataclass(frozen=True)
class AttemptDiagnostics:
    """Closed field set for retained attempt evidence; no response/request content."""

    run_id: str | None
    work_item_id: str | None
    binding_sha256: str | None
    attempt_id: str | None
    reservation_ref: str | None
    request_sha256: str | None = None
    transport_request_id: str | None = None
    response_id: str | None = None
    http_status: int | None = None
    error_code: str | None = None
    observed_model: str | None = None


@dataclass(frozen=True)
class AdapterResult:
    disposition: Literal[
        "local_hold", "no_submit", "no_redirect_or_forwarding", "no_fallback",
        "no_retry", "controller_retry_advice_only", "unresolved_no_resend",
        "unknown_remote_outcome", "completed", "refusal", "incomplete",
        "provider_failed", "hold_invalid_proposal", "unsupported_output",
    ]
    reason: str
    diagnostics: AttemptDiagnostics
    usage: UsageObservation = UsageObservation()
    items: tuple[TextItem | ToolProposal, ...] = ()
    retry_after_seconds: int | None = None

    @property
    def observation_key(self) -> tuple[str | None, str | None, str | None, str | None]:
        diagnostic = self.diagnostics
        return (diagnostic.run_id, diagnostic.attempt_id,
                diagnostic.transport_request_id, diagnostic.response_id)


def _json_object(raw: bytes | str) -> dict:
    def unique(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result

    value = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    return value


def _serialize_request(request: ExecutionRequest, context: ContextAssembly) -> bytes:
    if context.hold_reason is not None or context.payload is None:
        raise ValueError("context hold")
    payload = _json_object(context.payload)
    manifest = _json_object(context.provenance)
    if (
        manifest.get("payload_sha256") != sha256(context.payload).hexdigest()
        or manifest.get("assignment") != request.assignment.model_dump(mode="json")
        or type(manifest.get("version")) is not int
        or manifest["version"] != 1
        or "hold_reason" not in manifest
        or manifest["hold_reason"] is not None
    ):
        raise ValueError("context provenance does not match the assignment")
    if set(payload) != {"instructions", "supporting_data"}:
        raise ValueError("unexpected context structure")
    instructions = payload["instructions"]
    supporting_data = payload["supporting_data"]
    if (
        not isinstance(instructions, list)
        or not instructions
        or any(not isinstance(item, str) or not item.strip() for item in instructions)
        or not isinstance(supporting_data, list)
    ):
        raise ValueError("invalid instruction or supporting data")

    inputs = []
    for item in supporting_data:
        if not isinstance(item, dict):
            raise ValueError("invalid supporting item")
        if set(item) == {"xid", "text"} and all(isinstance(v, str) for v in item.values()):
            inputs.append({"type": "supporting_document", **item})
        elif set(item) == {"tool_result"}:
            tool = item["tool_result"]
            if (
                not isinstance(tool, dict)
                or not {"source", "observation"} <= tool.keys() <= _TOOL_CONTEXT_FIELDS
                or any(not isinstance(value, str) for value in tool.values())
            ):
                raise ValueError("invalid tool context")
            inputs.append({"type": "supporting_tool_data", "data": tool})
        else:
            raise ValueError("unexpected supporting item")

    body = {
        "model": request.selected_model,
        "max_output_tokens": request.budget.max_output_tokens,
        "instructions": "\n".join(instructions),
        "input": inputs,
        "tools": [{
            "type": "function",
            "name": FIXTURE_TOOL,
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        }],
    }
    return json.dumps(body, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _identifier(value: object) -> str | None:
    return value if isinstance(value, str) and _IDENTIFIER.fullmatch(value) else None


def _diagnostic_id(value: object, approved: tuple[str, ...]) -> str | None:
    """Preserve known synthetic IDs; retain only an opaque key for other IDs."""
    if not isinstance(value, str) or not 0 < len(value) <= 128:
        return None
    if value in approved:
        return value
    try:
        raw = value.encode("utf-8")
    except UnicodeEncodeError:
        return None
    return "sha256:" + sha256(raw).hexdigest()


def _count(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _usage(value: object) -> UsageObservation:
    if not isinstance(value, Mapping):
        return UsageObservation()
    input_details = value.get("input_tokens_details")
    output_details = value.get("output_tokens_details")
    return UsageObservation(
        input_tokens=_count(value.get("input_tokens")),
        output_tokens=_count(value.get("output_tokens")),
        total_tokens=_count(value.get("total_tokens")),
        cached_input_tokens=(
            _count(input_details.get("cached_tokens")) if isinstance(input_details, Mapping) else None
        ),
        reasoning_output_tokens=(
            _count(output_details.get("reasoning_tokens")) if isinstance(output_details, Mapping) else None
        ),
    )


class _OutputError(ValueError):
    def __init__(self, invalid_proposal: bool = False) -> None:
        self.invalid_proposal = invalid_proposal


def _ordered_items(output: object) -> tuple[TextItem | ToolProposal, ...]:
    if not isinstance(output, list):
        raise _OutputError()
    items: list[TextItem | ToolProposal] = []
    item_ids: set[str] = set()
    call_ids: set[str] = set()
    for row in output:
        if not isinstance(row, Mapping):
            raise _OutputError()
        kind = row.get("type")
        item_id = _identifier(row.get("id"))
        if item_id is None or item_id in item_ids:
            raise _OutputError(kind == "function_call")
        item_ids.add(item_id)
        if kind == "text" or kind == "refusal":
            value = row.get("text")
            if not isinstance(value, str):
                raise _OutputError()
            items.append(TextItem(item_id, kind, value))
        elif kind == "function_call":
            call_id = _identifier(row.get("call_id"))
            arguments = row.get("arguments")
            if (
                call_id is None or call_id in call_ids or row.get("name") != FIXTURE_TOOL
                or not isinstance(arguments, str)
            ):
                raise _OutputError(True)
            try:
                values = _json_object(arguments)
            except (ValueError, RecursionError) as exc:
                raise _OutputError(True) from exc
            if set(values) != {"query"} or not isinstance(values["query"], str):
                raise _OutputError(True)
            call_ids.add(call_id)
            items.append(ToolProposal(item_id, call_id, FIXTURE_TOOL, values["query"]))
        else:
            raise _OutputError()
    return tuple(items)


def _normalize(response: FakeResponse, diagnostics: AttemptDiagnostics) -> AdapterResult:
    if not isinstance(response, FakeResponse):
        return AdapterResult("unknown_remote_outcome", "invalid_fake_response", diagnostics)
    diagnostics = replace(
        diagnostics, transport_request_id=_diagnostic_id(response.request_id, _TRANSPORT_REQUEST_IDS),
    )
    if not isinstance(response.body, Mapping):
        return AdapterResult("unknown_remote_outcome", "invalid_fake_response", diagnostics)
    body = response.body
    status = body.get("http")
    status = status if type(status) is int and 100 <= status <= 599 else None
    error = body.get("code")
    error = error if isinstance(error, str) and error in _ERROR_CODES else None
    diagnostics = replace(
        diagnostics, response_id=_diagnostic_id(body.get("id"), _RESPONSE_IDS),
        http_status=status, error_code=error,
        observed_model=_diagnostic_id(body.get("model"), (FIXTURE_MODEL,)),
    )
    usage = _usage(body.get("usage"))
    if status is None:
        return AdapterResult("unknown_remote_outcome", "invalid_http_status", diagnostics, usage)
    if 300 <= status < 400:
        return AdapterResult("no_redirect_or_forwarding", "redirect_refused", diagnostics, usage)
    if status == 429:
        if error == "insufficient_quota":
            return AdapterResult("no_retry", "quota_rejected", diagnostics, usage)
        if error == "rate_limit_exceeded" and body.get("submission") == "confirmed_rejected":
            return AdapterResult(
                "controller_retry_advice_only", "confirmed_transient_rejection", diagnostics, usage,
                retry_after_seconds=_count(body.get("retry_after_seconds")),
            )
        return AdapterResult("unresolved_no_resend", "ambiguous_rate_limit", diagnostics, usage)
    if status >= 500 or status in (408, 409):
        return AdapterResult("unknown_remote_outcome", "submission_unresolved", diagnostics, usage)
    if 400 <= status < 500:
        if error == "model_not_found":
            return AdapterResult("no_fallback", "selected_model_unavailable", diagnostics, usage)
        if status in (401, 403):
            return AdapterResult("no_retry", "authentication_or_permission_rejected", diagnostics, usage)
        reason = "invalid_request_rejected" if error == "invalid_request_error" else "request_rejected"
        return AdapterResult("no_retry", reason, diagnostics, usage)
    if status < 200:
        return AdapterResult("unknown_remote_outcome", "unexpected_http_status", diagnostics, usage)

    outcome = body.get("status")
    if outcome not in ("completed", "incomplete", "failed"):
        return AdapterResult("unsupported_output", "unsupported_response_status", diagnostics, usage)
    if outcome == "completed" and not body.get("output"):
        return AdapterResult("unsupported_output", "missing_completed_output", diagnostics, usage)
    try:
        items = _ordered_items(body.get("output", []))
    except _OutputError as exc:
        if exc.invalid_proposal:
            return AdapterResult("hold_invalid_proposal", "invalid_tool_proposal", diagnostics, usage)
        return AdapterResult("unsupported_output", "unsupported_response_item", diagnostics, usage)
    # A non-completed or refused response cannot advance tool proposals.
    text_items = tuple(item for item in items if isinstance(item, TextItem))
    if outcome == "incomplete":
        return AdapterResult("incomplete", "provider_incomplete", diagnostics, usage, text_items)
    if outcome == "failed":
        return AdapterResult("provider_failed", "provider_failed", diagnostics, usage, text_items)
    if any(item.kind == "refusal" for item in text_items):
        return AdapterResult("refusal", "provider_refusal", diagnostics, usage, text_items)
    return AdapterResult("completed", "provider_completed", diagnostics, usage, items)


class OfflineResponsesAdapter:
    """One synthetic attempt, with an in-process admission ledger per adapter.

    The owner supplies a trusted current state and a final-body authorization check.
    The adapter cannot provide durable admission or transport-side replay proof.
    """

    def __init__(self, transport: Callable[[FakeInvocation], FakeResponse]) -> None:
        self._transport = transport
        self._lock = Lock()
        self._consumed_attempts: set[str] = set()

    def invoke(
        self,
        request: ExecutionRequest,
        context: ContextAssembly,
        *,
        attempt_id: str,
        profile: str,
        destination: str,
        read_current: Callable[[], DispatchState],
        authorize_body: Callable[[str, str, bytes], bool],
    ) -> AdapterResult:
        binding = request.assignment.binding_sha256
        diagnostics = AttemptDiagnostics(
            run_id=_diagnostic_id(request.assignment.run_id, ("fixture-run",)),
            work_item_id=_diagnostic_id(request.assignment.work_item_id, ("fixture-item",)),
            binding_sha256=binding if isinstance(binding, str) and _BINDING_DIGEST.fullmatch(binding) else None,
            attempt_id=_diagnostic_id(attempt_id, ("e202-attempt-001",)),
            reservation_ref=_diagnostic_id(request.reservation_ref, ("fixture-reservation",)),
        )

        def hold(reason: str) -> AdapterResult:
            return AdapterResult("local_hold", reason, diagnostics)

        if request.cancelled:
            return hold("request_cancelled")
        if (
            profile != FIXTURE_PROFILE or destination != FIXTURE_DESTINATION
            or request.selected_model != FIXTURE_MODEL
            or _identifier(attempt_id) is None
            or request.budget.max_output_tokens <= 0
        ):
            return hold("outside_fixture_profile")
        try:
            body = _serialize_request(request, context)
        except (ValueError, RecursionError):
            return hold("invalid_context")
        diagnostics = replace(diagnostics, request_sha256=sha256(body).hexdigest())
        try:
            approved = authorize_body(profile, destination, body)
        except Exception:
            return hold("final_body_check_unavailable")
        if approved is not True:
            return hold("final_body_denied")

        with self._lock:
            try:
                current = read_current()
            except Exception:
                return hold("current_state_unavailable")
            if not isinstance(current, DispatchState):
                return hold("current_state_unavailable")
            if current.cancelled:
                return AdapterResult("no_submit", "cancelled_before_dispatch", diagnostics)
            if current.deadline_expired:
                return AdapterResult("no_submit", "deadline_expired_before_dispatch", diagnostics)
            admission = current.admission
            if current.assignment != request.assignment or admission is None:
                return hold("missing_or_stale_admission")
            if admission.consumed or attempt_id in self._consumed_attempts:
                return hold("attempt_already_consumed")
            if (
                admission.assignment != request.assignment or admission.attempt_id != attempt_id
                or admission.authorization_ref != request.authorization_ref
                or admission.reservation_ref != request.reservation_ref
                or admission.context_sha256 != sha256(context.payload).hexdigest()
                or admission.provenance_sha256 != context.provenance_sha256
            ):
                return hold("admission_binding_mismatch")
            self._consumed_attempts.add(attempt_id)

        try:
            response = self._transport(FakeInvocation(body, request.budget.deadline_ms))
        except PossibleSubmission as exc:
            reason = {
                "timeout": "timeout_after_possible_submission",
                "cancelled": "cancelled_after_possible_submission",
            }.get(exc.kind, "fake_transport_raised")
            return AdapterResult("unknown_remote_outcome", reason, diagnostics)
        except Exception:
            return AdapterResult("unknown_remote_outcome", "fake_transport_raised", diagnostics)
        return _normalize(response, diagnostics)

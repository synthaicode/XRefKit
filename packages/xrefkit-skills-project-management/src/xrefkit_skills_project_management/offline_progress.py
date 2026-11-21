"""Evaluate a transition against current, independently verified project records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Transition = Literal["start", "review", "accept", "handoff"]
Check = Literal["readiness", "verification", "independent_review", "acceptance"]
Outcome = Literal["proceed", "await_evidence", "human_decision"]

_REQUIRED_CHECKS: dict[Transition, tuple[Check, ...]] = {
    "start": ("readiness",),
    "review": ("verification",),
    "accept": ("verification", "independent_review"),
    "handoff": ("acceptance",),
}


@dataclass(frozen=True)
class OfflinePolicy:
    """Current standing human authorization, resolved by the host's trusted reader."""

    project: str
    revision: str
    approval_ref: str
    scope: str
    transitions: tuple[Transition, ...]


@dataclass(frozen=True)
class TransitionRequest:
    project: str
    scope: str
    work_id: str
    work_revision: str
    transition: Transition
    offline: bool | None
    candidate: str | None = None
    human_decision_refs: tuple[str, ...] | None = None


@dataclass(frozen=True)
class TransitionEvidence:
    """An owner's current, verified result, bound to work and candidate revisions."""

    check: Check
    project: str
    scope: str
    work_id: str
    work_revision: str
    record_ref: str
    passed: bool
    candidate: str | None = None
    independent: bool | None = None


@dataclass(frozen=True)
class TransitionResult:
    outcome: Outcome
    reason: str
    request: TransitionRequest
    policy_revision: str | None = None
    approval_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()


def evaluate_offline_transition(
    request: TransitionRequest,
    policy: OfflinePolicy | None,
    evidence: tuple[TransitionEvidence, ...],
) -> TransitionResult:
    """Match verified records. The caller must resolve current authority and holds first.

    A proceed result relies on the standing approval and cannot itself grant
    authority, issue a quality verdict, or change project state.
    """
    if request.human_decision_refs is None:
        return TransitionResult("await_evidence", "applicable_holds_unverified", request)
    if request.human_decision_refs:
        return TransitionResult(
            "human_decision", "reserved_or_held_decision", request,
            unresolved=request.human_decision_refs,
        )
    if request.offline is None:
        return TransitionResult("await_evidence", "offline_scope_unverified", request)
    if request.offline is not True:
        return TransitionResult("human_decision", "outside_offline_scope", request)
    if (
        policy is None
        or not policy.revision.strip()
        or not policy.approval_ref.strip()
        or not request.project.strip()
        or not request.scope.strip()
        or policy.project != request.project
        or policy.scope != request.scope
        or request.transition not in policy.transitions
        or request.transition not in _REQUIRED_CHECKS
    ):
        return TransitionResult("human_decision", "no_applicable_standing_approval", request)

    if not request.work_id.strip() or not request.work_revision.strip():
        return TransitionResult("await_evidence", "work_identity_unverified", request)
    if request.transition != "start" and not (request.candidate or "").strip():
        return TransitionResult("await_evidence", "candidate_unverified", request)

    accepted: list[str] = []
    unresolved: list[str] = []
    for check in _REQUIRED_CHECKS[request.transition]:
        matches = [
            item for item in evidence
            if item.check == check
            and item.project == request.project
            and item.scope == request.scope
            and item.work_id == request.work_id
            and item.work_revision == request.work_revision
            and item.candidate == request.candidate
        ]
        if (
            len(matches) != 1
            or matches[0].passed is not True
            or not matches[0].record_ref.strip()
            or check == "independent_review" and matches[0].independent is not True
        ):
            unresolved.append(check)
        else:
            accepted.append(matches[0].record_ref)

    if unresolved:
        return TransitionResult(
            "await_evidence", "required_evidence_unresolved", request, policy.revision,
            policy.approval_ref, tuple(accepted), tuple(unresolved),
        )
    return TransitionResult(
        "proceed", "standing_approval_conditions_met", request, policy.revision,
        policy.approval_ref, tuple(accepted),
    )

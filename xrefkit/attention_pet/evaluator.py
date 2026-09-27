"""Explainable heuristic v1. Thresholds are hypotheses, not calibrated probabilities."""
from dataclasses import dataclass, asdict

from .model import AttentionState, WorkingSet, Capability, FitCandidate, FitEvaluation, ModelProfile, ReasoningDepth
from .profiles import PROFILES, DEPTHS
from .presentation import present_fit


@dataclass(frozen=True)
class Weights:
    working_set: float = 30
    dependency_complexity: float = 25
    constraint_density: float = 10
    decision_depth: float = 10
    conflict_pressure: float = 15
    context_dispersion: float = 10

    def __post_init__(self):
        import math
        if any(not math.isfinite(v) or v < 0 for v in asdict(self).values()):
            raise ValueError("weights must be finite and nonnegative")
        if abs(sum(asdict(self).values()) - 100) > 1e-6:
            raise ValueError("weights must sum to 100")


def features(ws: WorkingSet) -> dict:
    active = [i for i in ws.items if i.status == "active"]
    ids = {i.id for i in active}
    edges = [e for e in ws.dependencies if e.source in ids and e.target in ids]
    n = len(active)
    counts = {kind: sum(i.kind == kind for i in active) for kind in
              ("goal", "constraint", "decision", "question", "exception", "history", "conflict")}
    constraint_ids = {i.id for i in active if i.kind == "constraint"}
    constraint_edges = sum(e.source in constraint_ids or e.target in constraint_ids for e in edges)
    return {
        **counts, "active_items": n, "dependency_edges": len(edges),
        "sources": len({i.source for i in active}),
        "max_decision_depth": max((i.depth for i in active if i.kind == "decision"), default=0),
        "constraint_edges": constraint_edges,
    }


def evaluate(ws: WorkingSet, previous: dict | None = None, history: list[dict] | None = None,
             weights: Weights = Weights()) -> dict:
    f = features(ws)
    n = f["active_items"]
    relational_n = max(1, n - f["history"])
    severity = {
        "working_set": min(1, n / 40),
        "dependency_complexity": min(1, f["dependency_edges"] / relational_n / 2),
        "constraint_density": min(1, f["constraint_edges"] / relational_n),
        "decision_depth": min(1, f["max_decision_depth"] / 6),
        "conflict_pressure": min(1, (f["conflict"] * 3 + f["question"] + f["exception"]) / 12),
        "context_dispersion": min(1, max(0, f["sources"] - 1) / 8),
    }
    contributions = {k: v * asdict(weights)[k] for k, v in severity.items()}
    ral = round(sum(contributions.values()))
    observations = [o for o in ws.observations if o.context == ws.contextId]
    penalties = {"repeated_error": 18, "correction_ignored": 22, "misread_explanation": 18,
                 "decision_contradiction": 15, "intent_drift": 18, "no_improvement": 15,
                 "repeated_failure": 20}
    failures = [o for o in observations if o.kind != "validated"]
    validated = sum(o.kind == "validated" for o in observations)
    trajectory = (max(0, min(95, 85 + min(validated, 2) * 5 - sum(penalties[o.kind] for o in failures)))
                  if observations else None)
    comparable = previous is not None and previous["taskId"] == ws.taskId
    delta = ral - previous["ral"] if comparable else None
    elapsed = ws.observedAt - previous["observedAt"] if comparable else None
    if comparable and elapsed <= 0:
        raise ValueError("observation timestamps must increase for a task")
    recent = [s for s in (history or []) if s["taskId"] == ws.taskId
              and 0 < ws.observedAt - s["observedAt"] <= 300]
    trend_delta = ral - recent[0]["ral"] if recent else delta
    rapid = trend_delta is not None and trend_delta >= 15 and ((recent != []) or elapsed <= 300)
    high = ral >= 75
    wrong = trajectory is not None and trajectory < 50
    state = ("CRITICAL" if high else "WRONG TRAJECTORY") if wrong else (
        "UNKNOWN" if trajectory is None or ws.coverage == "partial" else ("HIGH LOAD" if high else "NORMAL"))
    band = ("stable" if ral < 40 else "loaded" if ral < 60 else "strained" if ral < 75
            else "high_pressure" if ral < 90 else "unstable")
    expression = "wrong_trajectory" if wrong and not high else "unstable" if wrong else band
    # Missing trajectory evidence is not evidence of load or distress. Keep
    # the observed load expression; reserve unknown for absent structure.
    if not n and ws.coverage == "partial" and not wrong:
        expression = "unknown"
    actions = ["rebase", "restart", "resolve"] if wrong else (
        ["split", "summarize", "externalize", "fix"] if high or rapid else ["fix", "summarize", "externalize", "archive"])
    if f["conflict"] or f["question"]:
        actions = list(dict.fromkeys(["resolve"] + actions))
    changes = []
    if comparable:
        for key, value in f.items():
            difference = value - previous["features"][key]
            if difference:
                changes.append({"feature": key, "delta": difference})
    result = {
        "schemaVersion": 1, "evaluatorVersion": "heuristic-v1", "weights": asdict(weights),
        "measurement": "task-structure-based estimated load",
        "taskId": ws.taskId, "contextId": ws.contextId, "observedAt": ws.observedAt,
        "coverage": ws.coverage, "ral": ral, "deltaRal": delta,
        "deltaSeconds": elapsed, "trajectoryStability": trajectory,
        "trajectoryEvidence": [o.model_dump() for o in observations],
        "state": state, "loadBand": band, "expression": expression,
        "trend": "rapid_rise" if rapid else "rising" if (delta or 0) > 0 else "falling" if (delta or 0) < 0 else "steady" if comparable else "unknown",
        "windowDeltaRal": trend_delta, "features": f, "changes": changes,
        "causes": [{"type": k, "severity": round(severity[k], 3), "points": round(v, 1)}
                   for k, v in sorted(contributions.items(), key=lambda kv: -kv[1]) if v > 0],
        "recommendedActions": actions,
    }
    return AttentionState.model_validate(result).model_dump()


def fit_candidate(state: dict, profile: ModelProfile, depth: ReasoningDepth) -> FitCandidate:
    """Model-generated expansion is a projection, never added to actual input/history."""
    base = state["ral"]
    severity = {c["type"]: c["severity"] for c in state["causes"]}
    dependency = severity.get("dependency_complexity", 0)
    constraints = severity.get("constraint_density", 0)
    unresolved = severity.get("conflict_pressure", 0)
    decisions = severity.get("decision_depth", 0)
    evidence = severity.get("context_dispersion", 0)
    b = profile.behavior
    exploration = (.10 * b.exploration + .10 * b.dependency_expansion * dependency
                   + .08 * b.constraint_discovery * constraints
                   + .08 * b.uncertainty_discovery * unresolved
                   + .08 * b.alternative_generation * decisions)
    expansion = round(min(30, max(0, base * exploration * depth.exploration_modifier
                                 - base * .06 * b.compression)), 1)
    effective = round(base + expansion, 1)
    # Effective complexity is deliberately not clamped to 100: expansion can
    # make a high-complexity task exceed every available profile's capabilities.
    required = Capability(
        reasoning=min(100, round(.65 * effective + 20 * decisions + 15 * dependency, 1)),
        constraint_tracking=min(100, round(.65 * effective + 25 * constraints + 10 * unresolved, 1)),
        evidence_handling=min(100, round(.65 * effective + 35 * evidence, 1)),
    )
    capability = Capability(**{k: min(100, max(0, v + depth.capability_modifier))
                               for k, v in profile.capability.model_dump().items()})
    shortfalls = [k for k, need in required.model_dump().items() if capability.model_dump()[k] < need]
    return FitCandidate(model=profile.id, reasoning=depth.id, expansion=expansion,
                        effectiveRal=effective, capability=capability, requiredCapability=required,
                        shortfalls=shortfalls, meetsRequirements=not shortfalls,
                        relativeInferenceCost=round(profile.relative_inference_cost * depth.cost_modifier, 2))


def evaluate_fit(state: dict | None, model: str = "", reasoning: str = "standard") -> dict:
    """Relative quality/cost allocation hypothesis; never a routing decision."""
    if model and model not in PROFILES:
        raise ValueError("unknown model profile")
    if reasoning not in DEPTHS:
        raise ValueError("unknown reasoning depth")
    if not model or state is None or not state["features"]["active_items"]:
        reason = "比較するモデルを選んでください。" if not model else "判定に使う作業内容がありません。"
        cost_fit = "ReviewNeeded" if state and any(o["kind"] != "validated" for o in state["trajectoryEvidence"]) else "Unknown"
        reasons = [reason]
        if cost_fit == "ReviewNeeded":
            reasons.append("失敗・修正の記録があり、総コストの確認が必要です。能力不足が原因とは断定しません。")
        return FitEvaluation(modelFit="Unknown", costFit=cost_fit, reasons=reasons,
                             coverage=state["coverage"] if state else None,
                             presentation=present_fit("Unknown", cost_fit, state["coverage"] if state else None),
                             baseRal=state["ral"] if state else None).model_dump()
    profile, depth = PROFILES[model], DEPTHS[reasoning]
    selected = fit_candidate(state, profile, depth)
    candidates = [fit_candidate(state, p, depth) for p in PROFILES.values() if p.id != model]
    cheaper = [c for c in candidates if c.meetsRequirements
               and c.relativeInferenceCost < selected.relativeInferenceCost]
    lowest_sufficient = min(cheaper, key=lambda c: c.relativeInferenceCost, default=None)
    axes = {"reasoning": "推論", "constraint_tracking": "制約の保持", "evidence_handling": "根拠の扱い"}
    # Capability adequacy never depends on candidate prices or comparisons.
    model_fit = "Sufficient" if selected.meetsRequirements else "Underpowered"
    if model_fit == "Underpowered":
        cost_fit = "RetryRisk"
        reasons = ["仮の必要能力に届かない項目：" + "、".join(axes[k] for k in selected.shortfalls) + "。",
                   "再試行や修正が増える可能性があります。回数・損失は未推定です。"]
    elif cheaper:
        cost_fit = "LowerCostCandidateAvailable"
        labels = " / ".join(PROFILES[c.model].label for c in cheaper)
        reasons = ["選択モデルは仮の必要能力3軸を満たしています。",
                   f"同じ考える深さで、{labels} も必要能力を満たし、より低い相対推論コストとなる試算です。",
                   "再試行・修正・失敗損失はまだ比較していません。実品質の同等性、総コストの低下、モデル変更の必要性を示すものではありません。"]
    else:
        cost_fit = "NoLowerCostCandidate"
        reasons = ["仮の必要能力を全項目で満たしています。",
                   "同じ考える深さの登録候補には、より低い相対推論コストで必要能力を満たすものがありません。実品質や総コストの優位性は未確認です。"]
    if any(o["kind"] != "validated" for o in state["trajectoryEvidence"]):
        cost_fit = "ReviewNeeded"
        reasons.append("失敗・修正に関する記録があります。能力試算とは別に再試行や修正を含む総コストの確認が必要です。")
    if state["coverage"] == "partial":
        reasons.append("入力は作業の一部です。未入力の条件により評価は変わります。")
    reasons.append("実験値・未校正。実際の能力、成功率、費用を計測した結果ではありません。")
    return FitEvaluation(modelFit=model_fit, costFit=cost_fit, baseRal=state["ral"],
                         coverage=state["coverage"],
                         presentation=present_fit(model_fit, cost_fit, state["coverage"],
                                                  selected=selected, lowest_sufficient=lowest_sufficient),
                         lowerCostCandidates=cheaper, inferenceCostIndex=selected.relativeInferenceCost,
                         selected=selected, profile=profile, depth=depth,
                         alternatives=candidates, reasons=reasons).model_dump()

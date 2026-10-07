"""Presentation policy, independent of capability and cost calculations."""
from .model import FitCandidate, Presentation


def _present_fit_en(state: str, model_fit: str, cost_fit: str, coverage: str | None,
                    confidence: str, selected: FitCandidate | None,
                    lowest_sufficient: FitCandidate | None) -> Presentation:
    messages = {
        "Unknown": ("Not enough information to evaluate yet.",
                    "Information required for this evaluation is missing.",
                    "Evaluation is not available yet", "Model fit has not been determined.",
                    "Check the work information and selected model."),
        "Strained": ("This work may exceed the model's capability.",
                     "Some estimated capability requirements are not met. This does not prove that model capability caused an actual failure.",
                     "Capability may be insufficient", "Some of the three estimated capability requirements are not met.",
                     "Compare a model that meets the requirements, or split and clarify the work."),
        "Balanced": ("The estimated capability requirements are met.",
                     "Under the current assumptions, no compatible execution profile meets the requirements at a lower estimated inference-cost index.",
                     "Estimated capability requirements are met", "All three estimated requirements are met; this is not a quality guarantee.",
                     "Continue with the current settings or check the actual result."),
        "Relaxed": ("A lower inference-cost candidate may meet the requirements.",
                    "The current execution profile meets the estimated requirements, and another compatible profile has a lower estimated inference-cost index.",
                    "Lower-cost comparison candidate available", "Retries, correction time, failure losses, and equivalent actual quality remain unverified.",
                    "Review the conditions for the lower-cost candidate."),
        "Review": ("Review the allocation using the actual results.",
                   "There are records of failures, retries, or corrections. Model capability alone is not identified as the cause.",
                   "Actual results need review", "Review the outcome records and total cost separately from capability fit.",
                   "Review the failure, correction, and retry records."),
    }
    headline, summary, short, detail, action = messages[state]
    if state != "Unknown":
        if coverage == "partial":
            headline = "For the work currently visible, " + headline[0].lower() + headline[1:]
            short = {"Strained": "Some visible work may exceed capability",
                     "Balanced": "Visible work meets estimated requirements",
                     "Relaxed": "Lower-cost candidate for some visible work"}.get(state, short)
        elif confidence in {"Unknown", "Low"}:
            headline = "For the current input, " + headline[0].lower() + headline[1:]
    if coverage == "partial":
        summary += " Only part of the work is included."
    confidence_labels = {"Unknown": "Not evaluated / Unknown", "Low": "Low",
                         "Medium": "Medium", "High": "High"}
    confidence_note = ("Evaluation confidence has not been assessed." if confidence == "Unknown" else
                       "Evaluation confidence is low." if confidence == "Low" else
                       "Evaluation confidence is separate from capability fit.")
    if cost_fit == "ReviewNeeded":
        guide_status, guide = "HoldForReview", "Review the actual result before comparing lower-cost candidates."
        guide_detail = "Failure or correction records are present, so candidate guidance based only on relative inference cost is paused."
    elif model_fit == "Unknown":
        guide_status, guide = "Unknown", "Provide work information and select a model to estimate lower-cost candidates."
        guide_detail = "A candidate cannot be shown until the required capability is known."
    elif model_fit == "Underpowered":
        guide_status, guide = "Underpowered", "First compare candidates that meet the capability requirements."
        guide_detail = "Lower-cost comparison is paused until a model is estimated to meet the requirements."
    elif cost_fit == "LowerCostCandidateAvailable" and selected and lowest_sufficient:
        guide_status = "Available"
        guide = f"Lower-cost candidate: {lowest_sufficient.model.capitalize()} / {lowest_sufficient.reasoning} (estimated)"
        guide_detail = (f"Under the current assumptions, {lowest_sufficient.model.capitalize()} / {lowest_sufficient.reasoning} also meets all three estimated requirements after its own work expansion. Relative inference-cost index: current {selected.model.capitalize()} {selected.relativeInferenceCost}; candidate {lowest_sufficient.model.capitalize()} {lowest_sufficient.relativeInferenceCost}. Actual quality and total cost including retries, corrections, and failures have not been compared.")
    else:
        guide_status, guide = "NoLowerCandidate", "No lower relative inference-cost candidate is currently estimated to meet the requirements."
        guide_detail = "This compares registered model and reasoning combinations. It does not establish an advantage in quality or total cost."
    if coverage == "partial" and guide_status == "Available":
        guide_detail += " This estimate uses only the supplied part of the work."
    guide_short = (f"Lower-cost candidate: {lowest_sufficient.model.capitalize()} / {lowest_sufficient.reasoning}"
                   if guide_status == "Available" and selected and lowest_sufficient else
                   "No lower-cost candidate (estimate)" if guide_status == "NoLowerCandidate" else "")
    return Presentation(
        petState=state, headline=headline, summary=summary, shortMessage=short,
        detailReason=detail, actionHint=action,
        scopeNote="Partial work only" if coverage == "partial" else "",
        confidenceNote=confidence_note,
        modelFitLabel={"Unknown": "Cannot determine / Unknown", "Underpowered": "Below estimated requirements / Underpowered",
                       "Sufficient": "Meets estimated requirements / Sufficient"}[model_fit],
        costFitLabel={"Unknown": "Not determined / Unknown", "RetryRisk": "Retries or corrections may increase",
                      "NoLowerCostCandidate": "No lower-cost fit candidate",
                      "LowerCostCandidateAvailable": "Lower inference-cost fit candidate available",
                      "ReviewNeeded": "Review outcome records and total cost"}[cost_fit],
        coverageLabel={None: "No input", "partial": "Partial", "reviewed": "Input scope reviewed / Reviewed"}[coverage],
        confidenceLabel=confidence_labels[confidence], modelGuide=guide,
        modelGuideShort=guide_short, modelGuideDetail=guide_detail,
        modelGuideStatus=guide_status,
    )


def present_fit(model_fit: str, cost_fit: str, coverage: str | None = None,
                confidence: str = "Unknown", selected: FitCandidate | None = None,
                lowest_sufficient: FitCandidate | None = None,
                locale: str = "ja") -> Presentation:
    # Outcome evidence takes priority over an otherwise comfortable face.
    if cost_fit == "ReviewNeeded":
        state = "Review"
    elif model_fit == "Unknown":
        state = "Unknown"
    elif model_fit == "Underpowered":
        state = "Strained"
    elif model_fit == "Sufficient" and cost_fit == "NoLowerCostCandidate":
        state = "Balanced"
    elif model_fit == "Sufficient" and cost_fit == "LowerCostCandidateAvailable":
        state = "Relaxed"
    else:
        state = "Unknown"
    if locale == "en":
        return _present_fit_en(state, model_fit, cost_fit, coverage, confidence,
                               selected, lowest_sufficient)
    messages = {
        "Unknown": (
            "まだ評価できません。", "評価に必要な情報が不足しています。",
            "まだ評価できません", "能力の適合は判定していません。",
            "作業内容とモデル選択を確認してください。"),
        "Strained": (
            "この作業には、能力が不足する可能性があります。",
            "仮の必要能力の一部を満たしていません。モデル能力が実際の失敗原因だとは判断していません。",
            "能力不足の可能性があります", "必要能力3軸のうち、一部に届かない試算です。",
            "必要能力を満たす候補や、作業の分割・整理を比較してください。"),
        "Balanced": (
            "必要な能力を満たす試算です。",
            "現在の仮定では、登録された組合せに、より低い推論コストで必要能力を満たす候補は確認されていません。",
            "必要能力を満たす試算です", "仮の必要能力3軸を満たしています。実務での品質保証ではありません。",
            "現在の設定で進めるか、実際の結果を確認してください。"),
        "Relaxed": (
            "必要能力を満たす、より低い推論コストの候補があります。",
            "現在の実行プロファイルでも必要能力を満たす試算ですが、より低い推論コスト指数の候補があります。",
            "低コスト比較候補があります",
            "再試行、修正時間、失敗損失はまだ総コスト比較に含まれていません。候補の実品質の同等性も未検証です。",
            "低コスト比較候補の条件を確認してください。"),
        "Review": (
            "実際の結果を含めて、配分を見直す必要があります。",
            "失敗、再試行、修正などに関する記録があります。モデル能力だけを原因とは判断していません。",
            "実結果の確認が必要です", "能力条件上の判定とは別に、結果の記録と総コストの確認が必要です。",
            "失敗・修正・再試行の記録を確認してください。"),
    }
    headline, summary, short, detail, action = messages[state]
    scope = "一部の作業のみ評価" if coverage == "partial" else ""
    if state != "Unknown":
        if coverage == "partial":
            headline = "現在確認できている範囲では、" + headline
            short = {
                "Strained": "一部の作業では能力不足の可能性",
                "Balanced": "一部の作業では必要能力を満たす試算",
                "Relaxed": "一部の作業で低コスト比較候補あり",
            }.get(state, short)
        elif confidence in {"Unknown", "Low"}:
            headline = "現在の入力範囲では、" + headline
    confidence_labels = {"Unknown": "未評価 / Unknown", "Low": "低い / Low",
                         "Medium": "中程度 / Medium", "High": "高い / High"}
    confidence_note = ("評価の確からしさは未評価です。" if confidence == "Unknown" else
                       "評価の確からしさは低い状態です。" if confidence == "Low" else
                       "評価の確からしさは能力条件上の判定とは別です。")
    if coverage == "partial":
        summary += " 一部の作業だけを評価しています。"
    if cost_fit == "ReviewNeeded":
        guide_status = "HoldForReview"
        guide = "低コスト候補の比較前に、実際の結果を確認してください。"
        guide_detail = "失敗・修正の記録があるため、推論コスト指数だけによる候補案内は保留しています。"
    elif model_fit == "Unknown":
        guide_status = "Unknown"
        guide = "作業内容と比較するモデルを選ぶと、低コスト比較候補を試算します。"
        guide_detail = "必要能力が未判定のため、低コスト比較候補は示せません。"
    elif model_fit == "Underpowered":
        guide_status = "Underpowered"
        guide = "まず必要能力を満たす候補を比較してください。"
        guide_detail = "必要能力を満たせるかが未確定のため、低コスト比較は保留しています。"
    elif cost_fit == "LowerCostCandidateAvailable" and selected and lowest_sufficient:
        guide_status = "Available"
        guide = (f"低コスト比較候補: {lowest_sufficient.model.capitalize()} /"
                 f" {lowest_sufficient.reasoning}（試算）")
        guide_detail = (f"現在の仮定では、{lowest_sufficient.model.capitalize()} /"
                        f" {lowest_sufficient.reasoning} も、その候補自身の作業展開を含めた"
                        "仮の必要能力3軸を満たす試算です。相対推論コスト指数: "
                        f"現在 {selected.model.capitalize()} {selected.relativeInferenceCost}、"
                        f"候補 {lowest_sufficient.model.capitalize()} {lowest_sufficient.relativeInferenceCost}。"
                        "実品質、再試行・修正時間・失敗損失を含む総コストは未比較です。")
    else:
        guide_status = "NoLowerCandidate"
        guide = "現在の比較条件では、より低い相対推論コストで仮の必要能力を満たす候補は確認されていません。"
        guide_detail = "登録されたモデルと考える深さの組合せを比較した結果です。品質や総コストの優位性は確認していません。"
    if coverage == "partial" and guide_status == "Available":
        guide_detail += "入力された一部の作業だけに基づく試算です。"
    guide_short = (f"低コスト比較候補: {lowest_sufficient.model.capitalize()} / {lowest_sufficient.reasoning}"
                   if guide_status == "Available" and selected and lowest_sufficient else
                   "低コスト比較候補なし（試算）" if guide_status == "NoLowerCandidate" else "")
    return Presentation(
        petState=state, headline=headline, summary=summary, shortMessage=short,
        detailReason=detail, actionHint=action, scopeNote=scope, confidenceNote=confidence_note,
        modelFitLabel={"Unknown": "判定できません / Unknown", "Underpowered": "必要能力に届かない試算 / Underpowered",
                       "Sufficient": "必要能力を満たす試算 / Sufficient"}[model_fit],
        costFitLabel={"Unknown": "未判定 / Unknown", "RetryRisk": "再試行・修正に注意",
                      "NoLowerCostCandidate": "低コスト適合候補なし / No lower-cost candidate",
                      "LowerCostCandidateAvailable": "より低い推論コストの適合候補あり",
                      "ReviewNeeded": "結果の記録と総コストを要確認"}[cost_fit],
        coverageLabel={None: "入力なし", "partial": "一部のみ / Partial", "reviewed": "入力範囲を確認済み / Reviewed"}[coverage],
        confidenceLabel=confidence_labels[confidence],
        modelGuide=guide, modelGuideShort=guide_short,
        modelGuideDetail=guide_detail, modelGuideStatus=guide_status,
    )

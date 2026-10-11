"""Read-only, source-faithful plan/task presentation."""
from __future__ import annotations

import hashlib
import html
from pathlib import Path

from xrefkit.plan_observation import _artifact_link as _local_artifact_link, _display, _repository_matches, _status_label
from xrefkit.work_management import safe_external_url, task_counts


def _artifact_link(root: Path | None, value: object) -> str:
    return _local_artifact_link(root, value) if root is not None else _display(value) + "（対応未確認・リンク利用不可）"


def _attributes(plan: dict, step: dict | None = None) -> str:
    fields = {key: plan[key] for key in ("workspace_id", "plan_id", "plan_revision")}
    if step is not None:
        fields["step_id"] = step["step_id"]
    return " ".join(f'data-{key.replace("_", "-")}="{html.escape(value, quote=True)}"' for key, value in fields.items())


def _class(step: dict) -> str:
    if step.get("revalidation_needed") is True:
        return "revalidation"
    return {"done": "done", "in_progress": "active"}.get(step.get("status"), "pending")


def _refs(root: Path, values: list | None) -> str:
    return "、".join(_artifact_link(root, value) for value in values) if values else "未記録"


def _external(ref: dict) -> str:
    label = f'{_display(ref["service"])} / {_display(ref["item_id"])}'
    if safe_external_url(ref.get("url")):
        label = f'<a href="{html.escape(ref["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{label}</a>'
    return f'<li>{label}（記録された外部参照・未照合）<br>外部版: {_display(ref.get("revision"))} | 反映状態: {_display(ref.get("sync_status"))}<br>最終取得: {_display(ref.get("last_read_at"))} / 最終反映成功: {_display(ref.get("last_success_at"))}<br>更新責任: {_display(ref.get("ownership_ref"))} | 反映待ち: {_display(ref.get("pending_summary"))}</li>'


def _confirmation(root: Path, confirmation: dict) -> str:
    answer = confirmation.get("answer")
    application = confirmation.get("application")
    state = "回答待ち（回答未記録）" if answer is None else "回答記録あり・反映未記録" if application is None else "回答と反映の記録あり（受入は別）"
    if answer is None and application is not None:
        state = "反映記録あり・回答未記録（対応不完全）"
    answer_html = "未記録" if answer is None else f'{_display(answer["text"])} | 回答者: {_display(answer.get("responder"))} | 日時: {_display(answer.get("recorded_at"))} | 根拠: {_refs(root, answer.get("evidence_refs"))}'
    application_html = "未記録" if application is None else f'反映先: {_refs(root, application.get("target_refs"))} | 確認者: {_display(application.get("verified_by"))} | 日時: {_display(application.get("recorded_at"))} | 検証根拠: {_refs(root, application.get("evidence_refs"))}'
    return f'<li><strong>{_display(confirmation["question"])}</strong> <small>{_display(confirmation["confirmation_id"])}</small><p>{state}</p><p>理由: {_display(confirmation.get("reason"))} | owner: {_display(confirmation.get("owner"))} | 解決担当: {_display(confirmation.get("resolver"))} | 必要時期: {_display(confirmation.get("due_at"))}</p><p>影響: {_display(confirmation.get("impact"))} | 対象版: {_display(confirmation.get("version_refs"))}</p><p>回答: {answer_html}</p><p>反映確認: {application_html}</p><p>判断・変更履歴参照: {_refs(root, confirmation.get("judgment_refs"))}</p></li>'


def _graph(plan: dict) -> str:
    positions = {}
    widths = 210
    row_counts = {}
    stages = {stage["stage_id"]: index for index, stage in enumerate(plan["stages"])}
    for step in plan["steps"]:
        column = stages[step["stage_id"]]
        row = row_counts.get(column, 0)
        row_counts[column] = row + 1
        positions[step["step_id"]] = (column * widths + 20, row * 115 + 45)
    width = max(1, len(stages)) * widths + 20
    height = max(row_counts.values(), default=0) * 115 + 50
    marker = "wm-arrow-" + hashlib.sha256((plan["workspace_id"] + plan["plan_id"] + plan["plan_revision"]).encode()).hexdigest()[:12]
    edges = []
    nodes = []
    same_column_lanes = {}
    for step in plan["steps"]:
        x, y = positions[step["step_id"]]
        for dependency in step["dependencies"]:
            if dependency["kind"] == "external":
                continue
            before_x, before_y = positions[dependency["step_id"]]
            if before_x == x:
                lane = same_column_lanes.get(x, 0)
                same_column_lanes[x] = lane + 1
                edge_x = x + 184 + (lane % 4) * 5
                path = f'M {before_x + 175} {before_y + 36} H {edge_x} V {y + 36} H {x + 180}'
            elif before_x < x:
                path = f'M {before_x + 175} {before_y + 36} C {before_x + 192} {before_y + 36}, {x - 15} {y + 36}, {x - 5} {y + 36}'
            else:
                path = f'M {before_x + 80} {before_y} V 16 H {x + 80} V {y - 5}'
            dash = ' stroke-dasharray="5 4"' if dependency["kind"] == "optional" else ""
            edges.append(f'<path d="{path}" fill="none" stroke="currentColor" stroke-width="1.3"{dash} marker-end="url(#{marker})"/>')
        title = _display(step["title"])
        state = "再確認対象" if step.get("revalidation_needed") is True else _status_label(step.get("status"))
        nodes.append(f'<button type="button" class="plan-step wm-node {_class(step)}" {_attributes(plan, step)} style="left:{x}px;top:{y}px" aria-label="{html.escape(step["title"] + " " + state, quote=True)}"><small>{_display(step["step_id"])} · {state}</small><strong>{title}</strong></button>')
    headers = "".join(f'<text x="{index * widths + 20}" y="30" fill="currentColor" font-size="12">{_display(stage["title"][:14])}</text>' for index, stage in enumerate(plan["stages"]))
    return f'<div class="wm-graph-scroll"><div class="wm-graph" style="width:{width}px;height:{height}px"><svg width="{width}" height="{height}" aria-hidden="true"><defs><marker id="{marker}" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0 0 L6 3 L0 6" fill="currentColor"/></marker></defs>{headers}{"".join(edges)}</svg>{"".join(nodes)}</div></div>'


def plan_v2_card(root: Path, row: dict) -> str:
    plan = row["plan"]
    matches_root = _repository_matches(root, plan)
    if not matches_root or row["issues"]:
        root = None
    attributes = _attributes(plan)
    counts = task_counts(plan)
    stages = []
    details = []
    for stage in plan["stages"]:
        tasks = [task for task in plan["steps"] if task["stage_id"] == stage["stage_id"]]
        countable = sum(task.get("status") == "done" and task.get("revalidation_needed") is not True for task in tasks)
        marks = "".join(f'<button type="button" class="plan-step wm-mark {_class(task)}" {_attributes(plan, task)} title="{html.escape(task["title"], quote=True)}" aria-label="{html.escape(task["title"] + " " + _status_label(task.get("status")), quote=True)}"></button>' for task in tasks)
        titles = "".join(f'<button type="button" class="plan-step wm-task-title" {_attributes(plan, task)}>{_display(task["title"])}</button>' for task in tasks)
        stages.append(f'<section class="wm-stage"><div><strong>{_display(stage["title"])}</strong><small>予定 {len(tasks)} · 記録上完了 {countable}</small></div><div class="wm-marks">{marks}</div><strong>残り {len(tasks) - countable}</strong><div class="wm-task-titles">{titles or "作業なし"}</div></section>')
    external = {ref["external_ref_id"]: ref for ref in plan["external_refs"]}
    for step in plan["steps"]:
        dependency_items = []
        for dependency in step["dependencies"]:
            label = {"mandatory": "必須", "optional": "任意", "external": "外部"}[dependency["kind"]]
            target = external[dependency["external_ref_id"]]["item_id"] if dependency["kind"] == "external" else dependency["step_id"]
            dependency_items.append(f'<li>{label}: {_display(target)} | 根拠: {_artifact_link(root, dependency.get("evidence_ref"))}</li>')
        history = []
        for mapping in step["run_observations"]:
            link = f'<a class="monitor-link" {_attributes(plan, step)} data-run-id="{html.escape(mapping["run_id"], quote=True)}" href="{html.escape(mapping["monitor_url"], quote=True)}">実行モニタを見る</a>' if mapping["available"] else f'<span aria-disabled="true">モニタ利用不可: {_display(mapping["reason"])}</span>'
            history.append(f'<li><code>{_display(mapping.get("run_id"))}</code> | 記録日時: {_display(mapping.get("recorded_at"))}<br>プロセス: {_display(mapping.get("process_status"))} / Closure: {_display(mapping.get("closure_status"))} / 品質: {_display(mapping.get("quality_status"))}<br>{link}</li>')
        validations = []
        for validation in step.get("validation_records", []):
            applicability = "現在の候補版の記録" if validation["target_version"] == step.get("candidate_version") else "別対象版の記録（有効性を引き継ぎません）"
            validations.append(f'<li>{_display(validation["validation_id"])} · 対象版: {_display(validation["target_version"])} · {applicability}<br>結果: {_display(validation.get("result"))} | 確認担当: {_display(validation.get("reviewer"))}<br>環境: {_display(validation.get("environment"))} | 入力: {_display(validation.get("input_data"))} | 期待値: {_display(validation.get("expected_result"))}<br>根拠: {_refs(root, validation.get("evidence_refs"))}</li>')
        confirmations = [_confirmation(root, confirmation) for confirmation in plan["confirmations"] if step["step_id"] in confirmation.get("step_ids", [])]
        artifacts = "".join(f'<li>{_display(artifact.get("kind"))} | 版: {_display(artifact.get("revision"))} | {_artifact_link(root, artifact["path"])}</li>' for artifact in step.get("artifact_refs", []))
        details.append(f'''<section class="plan-step-detail wm-detail" {_attributes(plan, step)} hidden>
          <h4>{_display(step["title"])} <small>{_display(step["step_id"])}</small></h4>
          <p>記録状態: {_display(step.get("status"))} | 完了根拠: {_artifact_link(root, step.get("status_evidence"))}</p>
          <p>再確認の必要性（記録値）: {_display(step.get("revalidation_needed"))} | 影響確認: {_display(step.get("impact_status"))} | 根拠: {_artifact_link(root, step.get("revalidation_evidence"))}</p>
          <p>担当Skill: {_display(step.get("planned_skill"))} | Agent: {_display(step.get("agent"))}</p>
          <p>完了条件: {_display(step.get("completion_criterion"))} | 候補成果物の版: {_display(step.get("candidate_version"))}</p>
          <p>PBI参照: {_display(step.get("pbi_ids"))} | 前版作業参照: {_display(step.get("predecessor_step_ids"))}</p>
          <h5>依存関係</h5><ul>{"".join(dependency_items) or "<li>依存なし</li>"}</ul><p>依存先の完了から着手許可を推測しません。</p>
          <h5>変更前後の資料・成果物</h5><p>出力: {_refs(root, step.get("outputs"))}</p><ul>{artifacts or "<li>版付き資料は未記録</li>"}</ul>
          <h5>版ごとの検証記録</h5><ul>{"".join(validations) or "<li>未記録</li>"}</ul>
          <h5>確認事項</h5><ul>{"".join(confirmations) or "<li>関連記録なし</li>"}</ul>
          <p>判断・変更履歴: {_refs(root, step.get("judgment_refs"))} | 懸念・対策の参照: {_refs(root, step.get("concern_refs"))}</p>
          <h5>実行履歴（再試行は作業数に加算しません）</h5><ul>{"".join(history) or "<li>未実行（Run対応なし）</li>"}</ul>
        </section>''')
    pbi_html = "".join(f'<li><strong>{_display(pbi["title"])}</strong> {_display(pbi["pbi_id"])} | 受入状態（記録値）: {_display(pbi.get("acceptance_status"))} | 受入担当: {_display(pbi.get("owner"))}<p>目的: {_display(pbi.get("purpose"))} | 受入条件: {_display(pbi.get("acceptance_criteria"))}</p><p>受入根拠: {_artifact_link(root, pbi.get("acceptance_evidence"))}</p></li>' for pbi in plan["pbis"])
    issues = "".join(f'<p class="wm-issue">{_display(issue)}</p>' for issue in row["issues"])
    if not matches_root:
        issues += '<p class="wm-issue">別リポジトリの計画です。モニタは利用不可。</p>'
    return f'''<article class="plan-card wm-plan" {attributes}>
      <h3>{_display(plan["title"])}</h3><p class="wm-sub">{_display(plan["project"]["title"])} / {_display(plan["change"]["title"])} · 計画版 {_display(plan["plan_revision"])} · 状態観測版 {_display(plan.get("observation_revision"))} · 基準版 {_display(plan["baseline"]["baseline_id"])}</p>
      {issues}<div class="wm-metrics"><div><small>現在の予定</small><strong>{counts["current"]}<small>作業</small></strong></div><div><small>記録上の完了</small><strong>{counts["completed"]}<small>作業</small></strong></div><div><small>残り</small><strong>{counts["remaining"]}<small>作業</small></strong></div></div>
      <p class="wm-sub">当初予定: {_display(counts["initial"])} · 追加: {_display(counts["added"])} · 削除: {_display(counts["removed"])} · 再確認対象: {counts["revalidation"]} · 状態未記録: {counts["unrecorded"]} · 未認識の状態: {counts["unrecognized"]}</p>
      <p class="wm-sub">件数は工数・残日数・品質承認ではありません。記録済みdoneのうち明示的な再確認対象を完了数から除外します。根拠や版の検証は別に表示します。</p>
      <div class="wm-segmented" aria-label="計画の表示"><button type="button" class="wm-view-switch" data-view="stages" aria-pressed="false">工程別の残り</button><button type="button" class="wm-view-switch" data-view="network" aria-pressed="true">依存関係の図</button></div>
      <p class="wm-legend">緑: 記録上完了 · 黄: 進行中 · 青破線: 再確認対象 · 実線: 必須依存 / 破線: 任意依存 · 外部依存は作業詳細に表示</p>
      <div data-wm-view="stages" hidden>{"".join(stages) or "工程・作業がありません"}</div><div data-wm-view="network">{_graph(plan)}</div>
      <p>図の作業を選択して詳細へ。工程別の一覧でもすべての作業を選べます。</p>{"".join(details)}
      <details><summary>PBIの受入（作業完了とは別）</summary><ul>{pbi_html or "<li>記録なし</li>"}</ul></details>
      <details><summary>確認事項台帳（{len(plan["confirmations"])}件・作業数とは別）</summary><ul>{"".join(_confirmation(root, confirmation) for confirmation in plan["confirmations"]) or "<li>記録なし</li>"}</ul></details>
      <details><summary>計画の根拠・基準版・案件の条件</summary><p>計画: {_artifact_link(root, plan["source"])} | snapshot・全観測履歴: {_artifact_link(root, row["file"])} | 承認記録: {_display(plan.get("approval_status"))} / {_artifact_link(root, plan.get("approval_evidence"))}</p><p>文書基準版: {_display(plan["baseline"].get("docs_revision"))} | コード基準版: {_display(plan["baseline"].get("code_revision"))} | 取得日時: {_display(plan["baseline"].get("acquired_at"))} | 不一致: {_display(plan["baseline"].get("mismatches"))}</p><ul>{"".join(f'<li>{_display(artifact.get("kind"))} · 版 {_display(artifact.get("revision"))} · {_artifact_link(root, artifact["path"])}</li>' for artifact in plan["baseline"].get("artifacts", []))}</ul><p>案件条件: {_display(plan["change"])}</p><p>参照Skill・知識の版: {_display(plan.get("knowledge_refs"))} | 前計画版: {_display(plan.get("previous_plan_revision"))}</p></details>
      <details><summary>外部への参照・反映記録（通信しません）</summary><ul>{"".join(_external(ref) for ref in plan["external_refs"]) or "<li>記録なし</li>"}</ul></details>
      <details><summary>保持された過去の状態観測（{len(plan.get("observation_history", []))}件）</summary><ul>{"".join(f'<li>観測版 {_display(entry["observation_revision"])} · report {_display(entry["report_id"])} · 完了状態/版/確認事項は元のsnapshot内に保持</li>' for entry in plan.get("observation_history", [])) or "<li>過去観測なし</li>"}</ul></details>
    </article>'''

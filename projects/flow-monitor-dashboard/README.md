# Flow Monitor Dashboard

`projects/` 配下のブラウンフィールド案件に後付けできる、Flow 実行モニタリング用の軽量ダッシュボードです。

このツールは、人間が AI の動作ログを見るための監視面です。
OS 再編や周辺構造の変更があっても、この可視化機能は壊さない前提で扱います。

## 目的

- どの Flow が通ったか
- 各 Flow でどの `steps` ステップが観測されたか
- 判断イベントが記録されたか
- チェックリストが使われたか
- Flow に紐づく各 Skill の runtime log がどう閉じられたか
- 未観測ステップが残っていないか
- AI の実行、判断、証跡、closure の状態が人間から追えるか

を一覧できるようにします。

## 起動

```powershell
cd projects/flow-monitor-dashboard
npm start
```

既定の URL は `http://127.0.0.1:3087` です。

## 品質チェック

```powershell
cd projects/flow-monitor-dashboard
npm run check
```

現在の最小基準:

- JavaScript 構文チェック
- 監視用 JSON ファイルの parse 検証
- ダッシュボード集計が実データから Flow run と Skill runtime log を検出できること

## 配置前提

このアプリ自身も `projects/` 配下にありますが、自己ディレクトリはスキャン対象から除外します。

監視対象は次のルートです。

```text
<repo>/projects/*
```

## 推奨トレース配置

既存成果物を壊さないため、各 Flow 成果物の横に `monitoring` ディレクトリを追加し、その中へ JSONL を書きます。

```text
projects/
  customer-a/
    flows/
      investigation_workflow/
        findings.md
        monitoring/
          flow-events.jsonl
      manufacturing_workflow/
        patch.diff
        checklist.md
        monitoring/
          flow-events.jsonl
```

## 推奨イベント形式

1 行 1 JSON の JSONL です。

```json
{"timestamp":"2026-04-05T09:00:00Z","project":"customer-a","flow_name":"investigation_workflow","run_id":"INV-20260405-01","type":"step","step":"service_catalog_analysis","status":"completed"}
{"timestamp":"2026-04-05T09:04:00Z","project":"customer-a","flow_name":"investigation_workflow","run_id":"INV-20260405-01","type":"path","path":"out_of_scope_to_coordinator","status":"raised"}
{"timestamp":"2026-04-05T09:07:00Z","project":"customer-a","flow_name":"investigation_workflow","run_id":"INV-20260405-01","type":"decision","decision":"coverage_assessment","decision_result":"needs_follow_up"}
{"timestamp":"2026-04-05T09:09:00Z","project":"customer-a","flow_name":"manufacturing_workflow","run_id":"MFG-20260405-02","type":"checklist","checklist":"manufacturing_self_check","completed_items":7,"total_items":8,"checklist_used":true}
```

## 読み取りルール

- `flows/*.yaml` を基準定義として読みます
- ステップ系列は決定論的制御スキーマの `steps:` マップのキーから取得します（旧 `sequence:` リストは未移行 Flow の fallback としてのみ読みます）
- 推奨 path は `handoff.escalation`（旧 `monitoring.paths` も併用）から取得します
- 推奨 decision / checklist はスキーマで表現されないため `flow-log-presets.json` から取得します
- `projects/` 配下の `flow-events.jsonl`, `trace.jsonl`, `events.jsonl`, `flow-monitor.json`, `flow-monitoring.json` を収集します
- `work/sessions/*_skill_run_*.md` を収集し、Skill runtime log の phase / artifact / concern / closure 状態を表示します
- `flow_id` または `flow_name` が一致すれば該当 Flow に紐づけます
- `step`, `path`, `decision`, `checklist` 系フィールドから集計します
- Skill runtime log は `flow-skill-map.json` と `flow-step-skill-map.json` を使って Flow 上の Skill 定義に紐づけます

## ブラウンフィールド導入の最小運用

既存ツールに大きく手を入れず、まずは次だけ記録すれば可視化できます。

1. Flow 開始時に `run_id` を発番する
2. `sequence` を通過したら `type: "step"` を書く
3. 分岐やエスカレーションが発生したら `type: "path"` を書く
4. 判断をしたら `type: "decision"` を書く
5. チェックリストを使ったら `type: "checklist"` を書く

この 5 種だけで、ダッシュボード上の主な監視項目は埋まります。

## Flow ごとの追加ログ

必要に応じて、各 Flow に次の種類のログを足す前提で設計しています。

- `decision`: その Flow 固有の判断点
- `checklist`: 実行時に確認したチェックリスト
- `path`: 分岐、エスカレーション、handoff

ダッシュボード上で表示する decision / checklist / path キーは、観測済みログがある場合はそのキーを優先します。

未観測時の表示候補は、種類ごとに次の正本から取得します。

- path: `flows/*.yaml` の `handoff.escalation`（決定論的制御スキーマのエスカレーション経路）
- decision / checklist: `flow-log-presets.json`（決定論的スキーマがドメインの判断・チェックリストラベルを表現しないため、これらの正本として残す）

```yaml
handoff:
  escalation:
    - out_of_scope_to_coordinator
    - quality_feedback_tradeoff_or_scope_conflict_to_coordinator
```

表示優先順位は次のとおりです。

1. プロジェクト側の観測トレースに含まれるキー
2. Flow YAML 由来（path は `handoff.escalation`）
3. `flow-log-presets.json`（decision / checklist の正本、path は fallback）

例:

- `investigation_workflow`: `coverage_assessment`, `unknown_classification`, `investigation_coverage_checklist`
- `planning_workflow`: `test_tool_selection`, `planning_policy_completeness_check`
- `manufacturing_workflow`: `implementation_boundary_review`, `quality_feedback_classification`, `manufacturing_self_check`, `quality_feedback_tradeoff_or_scope_conflict_to_coordinator`
- `release_planning_workflow`: `operational_readiness_gate`, `monitoring_design_review`

## Skill runtime log 表示

定義ビューでは、Flow に紐づく各 Skill について次を確認できます。

- 最新の `work/sessions/*_skill_run_*.md`
- `Execution Role` / `Check Role` / `Closure Gate` / `Handoff` の状態
- `output` / `evidence` / `handoff` artifact 数
- judgment を含む concern と open の unknown / risk
- 元の session log / `meta.md` / `SKILL.md` へのリンク

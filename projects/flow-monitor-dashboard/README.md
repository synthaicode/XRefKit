# Flow Monitor Dashboard

`projects/` 配下のブラウンフィールド案件に後付けできる、Flow 実行モニタリング用の軽量ダッシュボードです。

## 目的

- どの Flow が通ったか
- 各 Flow でどの `sequence` ステップが観測されたか
- 判断イベントが記録されたか
- チェックリストが使われたか
- 未観測ステップが残っていないか

を一覧できるようにします。

## 起動

```powershell
cd projects/flow-monitor-dashboard
npm start
```

既定の URL は `http://127.0.0.1:3087` です。

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
- `projects/` 配下の `flow-events.jsonl`, `trace.jsonl`, `events.jsonl`, `flow-monitor.json`, `flow-monitoring.json` を収集します
- `flow_id` または `flow_name` が一致すれば該当 Flow に紐づけます
- `step`, `path`, `decision`, `checklist` 系フィールドから集計します

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

定義値としては `flows/*.yaml` の `monitoring:` セクションを正本とし、未観測時の表示候補として扱います。

```yaml
monitoring:
  decisions:
    - implementation_boundary_review
  checklists:
    - manufacturing_self_check
  paths:
    - handoff_to_quality_review
```

移行中は `flow-log-presets.json` を fallback として読みます。

例:

- `investigation_workflow`: `coverage_assessment`, `unknown_classification`, `investigation_coverage_checklist`
- `planning_workflow`: `test_tool_selection`, `planning_policy_completeness_check`
- `manufacturing_workflow`: `implementation_boundary_review`, `manufacturing_self_check`
- `release_planning_workflow`: `operational_readiness_gate`, `monitoring_design_review`

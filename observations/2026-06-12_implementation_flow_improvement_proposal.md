# 改善提案 — implementation_flow Skill（2026-06-12 MailKit.Pooling 修正ランからの観測）

<!-- type: retro candidate / promotion via skill_flow_authoring -->
<!-- source run: work/sessions/2026-06-12_skill_run_implementation_flow_2.md -->

対象: `skills/implementation_flow/meta.md` / `SKILL.md`（maturity: trial）

## 観測された問題と提案

### P-1: レビュー所見起点の修正ランに入力プロファイルが合わない

- **観測**: 必須入力（test plan / test design / test design basis policy reference / test-item requirement traceability reference / manufacturing test review result）は SIer 型の承認済み設計パッケージを前提としており、csharp_review の findings doc を起点とする修正ランでは一つも存在しない。UNK-001 として記録し「findings doc = スコープ兼テスト基準」と読み替えて回避した。
- **提案**: SKILL.md の Inputs / Startup に **「review-findings remediation プロファイル」** を明文化する。レビューSkillの findings doc（所見ID・改善方向・証拠つき）を approved scope + test design の複合入力として認め、その場合の必須要素を「所見IDへのトレース」「所見ごとのテスト対応（既存修正 or 新規追加）」に置き換える。毎回 unknown を起票して読み替える運用は、ラン間で読み替え方がぶれるリスクがある。

### P-2: 上流所見が反証されたときの分類と帰還経路がない

- **観測**: F-002（MailKit SmtpClient が IAsyncDisposable 実装という前提）はコンパイラ証拠（CS1061）で反証された。implementation assumption gap の4分類（clarification_needed / evidence_missing / scope_conflict / local_choice_allowed)のどれにも該当せず、JDG-001 として judgment 起票で代用した。また、反証情報をクローズ済みの csharp_review ランの findings doc へ正式に戻す経路がなく、実装ノート内の補正記録に留まった。
- **提案**:
  1. assumption gap 分類に **`basis_refuted`**（実装時の機械的証拠が上流基準を反証）を追加する。
  2. Handoff 節に「反証は発生元レビューSkillへの handoff artifact として記録し、findings doc に補正注記を入れる」往復経路を定義する。レビューSkill側（csharp_review）にも「サードパーティAPIの表面（メンバー有無）を主張する所見は、参照パッケージの実バージョンに対する検証（コンパイルチェック等）を remediation 確定の前提とする」規則を追加するとP-2の発生自体が減る。

### P-3: TRACE-TEMP 規則が単一セッション自律ランと整合しない

- **観測**: SKILL.md は「コードレビュー完了宣言後に TRACE-TEMP を除去」、knowledge/151 は「クローズ前に除去、残存していたら正常完了扱いにしない」とする。人間レビューの窓が存在しない単一セッションの自律修正ランでは「付けて即剥がす」だけの作業になるため、151 の triviality 例外を適用して未使用とし、判断を planning note に記録して回避した。
- **提案**: knowledge/151 または SKILL.md に適用条件を明文化する: 「人間レビュー工程がラン外に存在する場合は TRACE-TEMP を既定とする / レビューSkill所見IDへのトレースが外部成果物で完結する単一ラン修正では省略を既定とする」。現在は例外条項の解釈に依存しており、チェッカーがランごとに異なる判定をしうる。

### P-4（軽微): 既存ランログとの命名衝突

- **観測**: `fm skill run` は同日2回目のランで `_2` サフィックスを自動付与して回避した（問題なし）が、meta.md の observation_refs は無印の同日ログを指しており、どのランを観測対象としているか曖昧になる。
- **提案**: observation_refs の追記運用（新しいランログを追加する／しないの基準）を skill_flow_authoring 側のチェックリストに含める。

## 昇格手順

- P-1〜P-3 の SKILL.md / knowledge 反映は `skill_flow_authoring` Skill のランとして実施する（本ドキュメントはその入力）。
- P-2 のレビューSkill側規則は `skills/csharp_review/SKILL.md` の Execution 節（attribute/remediation 検証）への追記として同ランで扱える。

## 採否と反映結果（2026-06-12 更新）

| 提案 | 採否 | 反映先 |
|---|---|---|
| P-1 | **見送り**（ユーザー判断） | — |
| P-2 | 採用 | `knowledge/organization/150`（`basis_refuted` 分類・許容応答・管理表規則）、`skills/implementation_flow/SKILL.md`（分類追加・Handoff帰還経路）、`skills/csharp_review/SKILL.md`（サードパーティAPI表面の実バージョン検証規則） |
| P-3 | 採用 | `knowledge/organization/151`（Applicability 節: 人間レビュー工程の有無で既定ON/OFF、クローズ越え残存はhandoff必須）、`skills/implementation_flow/SKILL.md`（文言整合） |
| P-4 | 採用 | `skills/os/skill_flow_authoring/references/authoring_checklist.md`（observation_refs 追記/剪定基準）、`skills/implementation_flow/meta.md`（observation_refs を実ラン `_2`/`_3`/本提案に更新） |

反映ラン: `work/sessions/2026-06-12_skill_run_skill_flow_authoring_3.md`。
検証: `fm skill check` 合格（implementation_flow trial / csharp_review stable / skill_flow_authoring trial）。`fm xref fix` 実行済み（残存248件は capabilities/ がインデックス include 外であることによる既存検出で、本反映の起因ではない）。

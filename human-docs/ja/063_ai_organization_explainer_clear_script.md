# AI 組織説明動画 改訂シナリオ

この資料は、AI の出力速度を組織の継続可能な業務実行へ変えるための
XRefKit の現行モデルを説明する。

## 対象者とゴール

- 対象者: AI を個人利用しているが、品質、手戻り、引き継ぎに課題を感じる人。
- ゴール: AI が途中で止まっても未完了を完了扱いにせず、責務を限定した
  作業を継続できる仕組みを理解してもらう。
- 中心メッセージ: AI の効率は出力速度だけでは決まらない。Goal、routing、
  Skill、Knowledge、workflow protocol を分けることで、再説明、再調査、
  作業漏れ、引き継ぎ漏れを減らす。

## 用語の境界

| 要素 | 説明 |
| --- | --- |
| Goal | 最終状態、受入条件、複数 Skill をまたぐ継続を管理する。 |
| semantic routing | Goal と現在状態から、次に必要な Skill を選ぶ。 |
| Skill | 限定した責務、判断方法、入出力、必要な Knowledge、handoff 境界を持つ。 |
| Knowledge | 判断に必要なドメイン規則と根拠。候補一覧から必要な XID だけを読む。 |
| workflow protocol | 各 Skill Run の work item、根拠、unknown、verify、handoff、close を管理する。 |

`verify` は作業記録の完全性を検査する。成果物の内容を受け入れるかどうかは、
必要に応じて quality review と人間の承認で判断する。

## スライド構成とナレーション

1. AI は個人作業を速くする。しかし、確認、判断、引き継ぎまで終わったとは限らない。
2. AI が途中で止まると、未了の作業、未確認点、根拠、次の担当が会話に埋もれる。
3. プロンプトだけでは、人が毎回説明し、何が終わったかを判断する必要がある。
4. Goal は最終状態と受入条件を固定し、Skill は途中で担う責務を限定する。
5. Skill は capability、tuning、responsibility、入出力、判断方法、handoff 境界を持つ。
6. semantic routing は Goal と現在状態から次の Skill を選ぶ。人が毎回一覧から手選びしない。
7. Skill は方法を持ち、Knowledge は判断材料を持つ。必要な XID だけを選んで読む。
8. workflow protocol は work item、成果物、根拠、unknown、risk、judgment、handoff を run log に残す。
9. `verify` は作業漏れを検査する。成果物の品質受入れとは別の軸である。
10. 中断時は記録から再開または handoff する。Goal は受入条件が満たされるまで続く。
11. 人間は Goal、受入れ、承認、例外を担い、すべてを会話履歴から監視しない。
12. AI 活用を、単発の会話から継続可能で監査可能な業務実行へ変える。

## 結びの文

AI を止めないための仕組みではありません。AI が途中で止まっても、仕事を失わず、
未確認の仕事を完了扱いにしないための仕組みです。

責務を限定した Skill が判断と成果物に集中し、workflow protocol が漏れを検査し、
Goal が最終状態までの継続を管理します。これにより、AI の速さを手戻り削減と
継続性へ変えます。

## 関連

- [AIの作業を途中で終わらせないための仕組み](071_ai_workflow_completion_and_skill_scope_material.md#xid-F6C3A9E12B47)
- [Workflow Protocol Sequence For Humans](../../docs/guides/087_workflow_protocol_sequence_for_humans.md#xid-E8B4D2F19A63)
- [Skill and Knowledge Operating Model](../../docs/core/models/052_flow_capability_skill_knowledge_model.md#xid-91C4B7E2D5A8)

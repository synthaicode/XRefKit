# 図インデックス

このフォルダには、XRefKit の概念図と、その図だけで最低限説明できる正本メモを置きます。
詳細説明、対象読者別の言い換え、導入向けの話し方は、利用者の AI にこの図と対応する `.md` を参照させて行います。

## 何から読むか

- XRefKit の全体像から入りたい: [01 XRefKitは、AIに業務を依頼するための基盤](01_xrefkit_as_ai_agent_os.md)
- Business Pack の意味を知りたい: [02 Business Pack Explained](02_business_pack_explained.md)
- 基礎概念から入りたい: [03 Skill / Knowledge / Handoff と進行制御](03_flow_skill_knowledge_handoff.md)
- Skill 分割の具体例を見たい: [04 Code Review as Split Checks](04_code_review_as_split_checks.md)
- 実行すると何が出力されるかを知りたい: [05 AIを実行すると、何が出力されるのか](05_execution_outputs_and_followup_work.md)
- 実行ログと Dashboard の関係を知りたい: [06 Skill Run Observation Dashboard](06_skill_run_observation_dashboard.md)
- Business Pack の再利用と単一 Skill/Knowledge との違いを知りたい: [09 Business Packはどう再利用するか](09_business_pack_reuse.md)

## 疑問ごとの入口

- XRefKit は何か: [01](01_xrefkit_as_ai_agent_os.md)
- Skill / Knowledge / Handoff と進行制御は何を分けているか: [03](03_flow_skill_knowledge_handoff.md)
- Business Pack とは何か: [02](02_business_pack_explained.md)
- Business Pack は再利用可能か: [09](09_business_pack_reuse.md)
- Business Pack と単一 Skill / Knowledge の違いは何か: [09](09_business_pack_reuse.md)
- Skill 分割の具体例を見たい: [04](04_code_review_as_split_checks.md)
- コード作成時に AI をどう制御するか: [04](04_code_review_as_split_checks.md)
- 実行すると何が出力されるか: [05](05_execution_outputs_and_followup_work.md)
- Dashboard で何を見てどう改善につなげるか: [06](06_skill_run_observation_dashboard.md), [07](07_dashboard_observation_and_improvement.md), [08](08_human_direction_ai_modification_loop.md)

## 推奨読順

1. [01 XRefKitは、AIに業務を依頼するための基盤](01_xrefkit_as_ai_agent_os.md)
2. [02 Business Pack Explained](02_business_pack_explained.md)
3. [03 Skill / Knowledge / Handoff と進行制御](03_flow_skill_knowledge_handoff.md)
4. [04 Code Review as Split Checks](04_code_review_as_split_checks.md)
`03` と `04` は `02` の詳細説明
5. [05 AIを実行すると、何が出力されるのか](05_execution_outputs_and_followup_work.md)
6. [06 Skill Run Observation Dashboard](06_skill_run_observation_dashboard.md)
`06` は `05` の詳細説明
7. [07 Dashboardから改善につなげる](07_dashboard_observation_and_improvement.md)
8. [08 人間が方向を決め、AIが修正する](08_human_direction_ai_modification_loop.md)
`08` は `04` の詳細説明
9. [09 Business Packはどう再利用するか](09_business_pack_reuse.md)

## 利用者 AI への渡し方

- 図だけを見せず、対応する `.md` も一緒に参照させる
- 詳細説明は AI に行わせるが、用語定義はこの `.md` の定義を優先させる
- 対象読者別の説明を作るときは、非対象の節も同時に参照させる

## プロンプト例

- [利用者 AI 向けプロンプト例](prompt_examples.md)

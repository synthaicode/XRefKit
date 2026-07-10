<!-- xid: D7C3A9E15B42 -->
<a id="xid-D7C3A9E15B42"></a>

# AI活用を継続可能な業務実行に変える

- 想定時間: 8-12 分
- 想定読者: AI 活用を個人の会話から、継続可能な業務実行へ進めたい組織
- 目的: AI活用を、Goalから完了まで継続・検証・改善できる業務実行へ変える仕組みを説明する
- 構成: 状態が残らない問題 -> Goalと作業分割 -> 接続と記録 -> Knowledge、受入れ、改善
- 形式: 画像ベース

---
![AI活用を継続可能な業務実行に変える](assets/055_why_ai_organization_needed/00_intro.png)

AI活用を、途中で止まっても再開でき、検証・受入れ・改善できる業務実行へ変えることが、この資料の主題です。

---
![毎回のプロンプト主体の利用方法では、業務の状態が残らない](assets/055_why_ai_organization_needed/01_title.png)

判断材料、未確認点、次作業、受入れ条件が会話ごとに埋もれます。担当者や実行環境が変わると、次の実行者は状態を再構成しなければなりません。

---
![AIは、途中で作業を終えても完了として扱いやすい](assets/055_why_ai_organization_needed/02_individual_limit.png)

AIは要求への応答を終えられますが、業務全体の未了項目や受入れ条件を自律的に保持し続けるわけではありません。出力終了と業務完了を混同しやすくなります。

---
![Goal が、業務の完了を定義する](assets/055_why_ai_organization_needed/03_input_organization.png)

Goalはdesired stateとacceptance conditionsを持ちます。個々の作業やAIの停止ではなく、Goalが満たされて初めて業務完了となります。Goalを達成するには、AIが扱える責務単位へ作業を分ける必要があります。

---
![AIには、限定した責務を担当させる](assets/055_why_ai_organization_needed/04_scattered_controls.png)

分割した各作業をSkillとして持ちます。Skillは担当範囲、判断方法、入出力、必要なKnowledge、handoff境界を明確にし、AIを必要な判断へ集中させます。

---
![semantic routing が、分割した作業をGoalへつなぐ](assets/055_why_ai_organization_needed/05_organization_role.png)

Goalと現在状態から、次に必要なSkillを選びます。作業が分割されていても、個別Skillの完了をGoal達成と取り違えず、全体の終点へ進めます。

---
![workflow protocol が、未完了の仕事を残す](assets/055_why_ai_organization_needed/06_organization_value.png)

Skill Runごとにwork item、artifact、evidence、unknown、risk、judgment、handoffを記録します。AIが途中で止まっても、次のSkillまたは人間が状態から続けられます。

---
![AI活用には、組織固有のKnowledgeが必要](assets/055_why_ai_organization_needed/07_human_control_unit.png)

AIが持つのは一般化された学習知識です。実務判断には、組織固有のルール、対象情報、例外、過去の判断、責任境界が必要になります。必要なKnowledgeをXIDで選び、段階的に参照します。

---
![作業漏れの検証と、成果物の受入れを分ける](assets/055_why_ai_organization_needed/08_ai_control_unit.png)

`xrefkit skill verify` は作業記録の完全性を検査します。成果物を採用するか、Goalを受け入れるか、例外を認めるかはquality reviewと人間が判断します。

---
![ログから、次の業務実行を改善する](assets/055_why_ai_organization_needed/09_conclusion.png)

Skill RunとMCPのログから、Skillの選択とXIDの選択・解決・ロード・適用を観測します。得られた証拠でrouting、Skill、Knowledgeを改善し、次のGoal実行へ戻します。

## 関連

- [AIの業務実行構造をどう持たせるか](056_structure_for_ai_organization_presentation.md#xid-C8E2B4D19A65)
- [AI組織説明動画 改訂シナリオ](063_ai_organization_explainer_clear_script.md)
- [XID利用状況を確認し、SkillとKnowledgeを改善する](072_xid_usage_observability_and_improvement_presentation.md#xid-E5B0D94A71C3)

<!-- xid: C8E2B4D19A65 -->
<a id="xid-C8E2B4D19A65"></a>

# AI の業務実行構造をどう持たせるか

- 想定読者: AI を用いた仕事を、組織で継続・再開・改善できる形に設計したい人
- 目的: Goal、semantic routing、Skill、Knowledge、workflow protocol、品質受入れを混同せず、それぞれの役割と接続を説明する
- 構成: 終点 -> 選択 -> 実行 -> 知識 -> 検証 -> 人間の受入れ -> 改善

---
![はじめに](assets/056_structure_for_ai_organization/00_intro.png)

AI の業務実行構造とは、AI を並べる組織図ではありません。目標から完了まで、どの責務が何をし、どの情報と記録を使うかを分ける構造です。

---
![タイトル](assets/056_structure_for_ai_organization/01_title.png)

必要なのは、Goal、routing、Skill、Knowledge、workflow protocol、品質受入れを一つのものとして混ぜず、相互に接続することです。

---
![Goal](assets/056_structure_for_ai_organization/02_four_elements.png)

Goal は最終状態と受入れ条件を持ちます。複数の Skill Run があっても、同じ終点へ継続して進めます。

---
![semantic routing](assets/056_structure_for_ai_organization/03_skill.png)

semantic routing は Goal と現在状態から、次の責務を持つ Skill を選びます。Skill の手順を実行するものではありません。

---
![Skill](assets/056_structure_for_ai_organization/04_domain_knowledge.png)

Skill は限定された責務、判断方法、入出力、必要な Knowledge、handoff 境界を持ちます。責務を狭くすることで、AI が判断へ集中できます。

---
![Knowledge](assets/056_structure_for_ai_organization/05_flow.png)

Knowledge は判断材料です。カタログから対象を見つけ、必要な XID だけを解決・ロードし、どの判断に適用したかを記録します。

---
![workflow protocol](assets/056_structure_for_ai_organization/06_group.png)

workflow protocol は Skill Run の work item、artifact、evidence、unknown、risk、judgment、handoff、close を記録し、作業漏れを検査可能にします。

---
![検証と受入れ](assets/056_structure_for_ai_organization/07_mapping.png)

`xrefkit skill verify` は workflow の進行記録を検査します。品質の受入れは、必要な quality review と人間の承認で別に判断します。

---
![結論](assets/056_structure_for_ai_organization/08_conclusion.png)

AI の業務実行構造は、Goalを中心に、routing、責務を限定したSkill、選択的Knowledge、workflow protocol、人間の受入れを接続し、ログから改善を回す仕組みです。
